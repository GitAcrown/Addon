import discord
from discord.ext import commands
import threading
import os
from random import shuffle, choice
from cogs.utils.dataIO import dataIO
from cogs.utils import checks
from cogs.utils.chat_formatting import pagify
from urllib.parse import urlparse
from __main__ import send_cmd_help, settings
from json import JSONDecodeError
import re
import logging
import collections
import copy
import asyncio
import math
import time
import inspect
import subprocess

__author__ = "tekulvw"
__version__ = "0.1.1"

log = logging.getLogger("red.audio")

try:
    import youtube_dl
except:
    youtube_dl = None

try:
    if not discord.opus.is_loaded():
        discord.opus.load_opus('libopus-0.dll')
except OSError:  # Incorrect bitness
    opus = False
except:  # Missing opus
    opus = None
else:
    opus = True

youtube_dl_options = {
    'source_address': '0.0.0.0',
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': "mp3",
    'outtmpl': '%(id)s',
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'quiet': True,
    'no_warnings': True,
    'outtmpl': "data/audio/cache/%(id)s",
    'default_search': 'auto'
}


class MaximumLength(Exception):
    def __init__(self, m):
        self.message = m

    def __str__(self):
        return self.message


class NotConnected(Exception):
    pass


class AuthorNotConnected(NotConnected):
    pass


class VoiceNotConnected(NotConnected):
    pass


class UnauthorizedConnect(Exception):
    pass


class UnauthorizedSpeak(Exception):
    pass


class ChannelUserLimit(Exception):
    pass


class UnauthorizedSave(Exception):
    pass


class ConnectTimeout(NotConnected):
    pass


class InvalidURL(Exception):
    pass


class InvalidSong(InvalidURL):
    pass


class InvalidPlaylist(InvalidSong):
    pass


class deque(collections.deque):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def peek(self):
        ret = self.pop()
        self.append(ret)
        return copy.deepcopy(ret)

    def peekleft(self):
        ret = self.popleft()
        self.appendleft(ret)
        return copy.deepcopy(ret)


class Song:
    def __init__(self, **kwargs):
        self.__dict__ = kwargs
        self.title = kwargs.pop('title', None)
        self.id = kwargs.pop('id', None)
        self.url = kwargs.pop('url', None)
        self.webpage_url = kwargs.pop('webpage_url', "")
        self.duration = kwargs.pop('duration', 60)


class Playlist:
    def __init__(self, server=None, sid=None, name=None, author=None, url=None,
                 playlist=None, path=None, main_class=None, **kwargs):
        # when is this used? idk
        # what is server when it's global? None? idk
        self.server = server
        self._sid = sid
        self.name = name
        # this is an id......
        self.author = author
        self.url = url
        self.main_class = main_class  # reference to Audio
        self.path = path

        if url is None and "link" in kwargs:
            self.url = kwargs.get('link')
        self.playlist = playlist

    @property
    def filename(self):
        f = "data/audio/playlists"
        f = os.path.join(f, self.sid, self.name + ".txt")
        return f

    def to_json(self):
        ret = {"author": self.author, "playlist": self.playlist,
               "link": self.url}
        return ret

    def is_author(self, user):
        """checks if the user is the author of this playlist
        Returns True/False"""
        return user.id == self.author

    def can_edit(self, user):
        """right now checks if user is mod or higher including server owner
        global playlists are uneditable atm

        dev notes:
        should probably be defined elsewhere later or be dynamic"""

        # I don't know how global playlists are handled.
        # Not sure if the framework is there for them to be editable.
        # Don't know how they are handled by Playlist
        # Don't know how they are handled by Audio
        # so let's make sure it's not global at all.
        if self.main_class._playlist_exists_global(self.name):
            return False

        admin_role = settings.get_server_admin(self.server)
        mod_role = settings.get_server_mod(self.server)

        is_playlist_author = self.is_author(user)
        is_bot_owner = user.id == settings.owner
        is_server_owner = self.server.owner.id == self.author
        is_admin = discord.utils.get(user.roles, name=admin_role) is not None
        is_mod = discord.utils.get(user.roles, name=mod_role) is not None

        return any((is_playlist_author,
                    is_bot_owner,
                    is_server_owner,
                    is_admin,
                    is_mod))


    # def __del__() ?

    def append_song(self, author, url):
        if not self.can_edit(author):
            raise UnauthorizedSave
        elif not self.main_class._valid_playable_url(url):
            raise InvalidURL
        else:
            self.playlist.append(url)
            self.save()

    def save(self):
        dataIO.save_json(self.path, self.to_json())

    @property
    def sid(self):
        if self._sid:
            return self._sid
        elif self.server:
            return self.server.id
        else:
            return None


class Downloader(threading.Thread):
    def __init__(self, url, max_duration=None, download=False,
                 cache_path="data/audio/cache", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = url
        self.max_duration = max_duration
        self.done = threading.Event()
        self.song = None
        self.failed = False
        self._download = download
        self.hit_max_length = threading.Event()
        self._yt = None

    def run(self):
        try:
            self.get_info()
            if self._download:
                self.download()
        except MaximumLength:
            self.hit_max_length.set()
        except:
            self.failed = True
        self.done.set()

    def download(self):
        self.duration_check()

        if not os.path.isfile('data/audio/cache' + self.song.id):
            video = self._yt.extract_info(self.url)
            self.song = Song(**video)

    def duration_check(self):
        log.debug("duration {} for songid {}".format(self.song.duration,
                                                     self.song.id))
        if self.max_duration and self.song.duration > self.max_duration:
            log.debug("songid {} too long".format(self.song.id))
            raise MaximumLength("songid {} has duration {} > {}".format(
                self.song.id, self.song.duration, self.max_duration))

    def get_info(self):
        if self._yt is None:
            self._yt = youtube_dl.YoutubeDL(youtube_dl_options)
        if "[SEARCH:]" not in self.url:
            video = self._yt.extract_info(self.url, download=False,
                                          process=False)
        else:
            self.url = self.url[9:]
            yt_id = self._yt.extract_info(
                self.url, download=False)["entries"][0]["id"]
            # Should handle errors here ^
            self.url = "https://youtube.com/watch?v={}".format(yt_id)
            video = self._yt.extract_info(self.url, download=False,
                                          process=False)

        self.song = Song(**video)


class Audio:
    """Streaming de musique."""

    def __init__(self, bot, player):
        self.bot = bot
        self.queue = {}  # add deque's, repeat
        self.downloaders = {}  # sid: object
        self.settings = dataIO.load_json("data/audio/settings.json")
        self.surv = dataIO.load_json("data/audio/surv.json")
        self.server_specific_setting_keys = ["VOLUME", "VOTE_ENABLED",
                                             "VOTE_THRESHOLD", "NOPPL_DISCONNECT"]
        self.cache_path = "data/audio/cache"
        self.local_playlist_path = "data/audio/localtracks"
        self._old_game = False

        self.skip_votes = {}

        self.connect_timers = {}

        if player == "ffmpeg":
            self.settings["AVCONV"] = False
        elif player == "avconv":
            self.settings["AVCONV"] = True
        self.save_settings()

    async def surv_acc(self, user):
        if user.id not in self.surv["USERS"]:
            self.surv["USERS"][user.id] = {"ID": user.id,
                                           "TICKETS": self.surv["SYS"]["MAX_TICKETS"],
                                           "INTERDIT": False,
                                           "SONGLIST": []}
            dataIO.save_json('data/audio/surv.json', self.surv)
            return True
        else:
            pass

    async def surv_autorise(self, user, sub = 1):
        await self.surv_acc(user)
        if self.surv["USERS"][user.id]["INTERDIT"] is False:
            if self.surv["SYS"]["LIBERE_ROLE"] not in [r.name for r in user.roles]:
                if self.surv["USERS"][user.id]["TICKETS"] - sub > 0:
                    self.surv["USERS"][user.id]["TICKETS"] -= sub
                    dataIO.save_json('data/audio/surv.json', self.surv)
                    return True
                else:
                    return False
            else:
                return True
        else:
            return False

    async def _add_song_status(self, song):
        if self._old_game is False:
            self._old_game = list(self.bot.servers)[0].me.game
        status = list(self.bot.servers)[0].me.status
        game = discord.Game(name=song.title)
        await self.bot.change_presence(status=status, game=game)
        log.debug('Status du bot changé en: ' + song.title)

    def _add_to_queue(self, server, url):
        if server.id not in self.queue:
            self._setup_queue(server)
        self.queue[server.id]["QUEUE"].append(url)

    def _add_to_temp_queue(self, server, url):
        if server.id not in self.queue:
            self._setup_queue(server)
        self.queue[server.id]["TEMP_QUEUE"].append(url)

    def _addleft_to_queue(self, server, url):
        if server.id not in self.queue:
            self._setup_queue()
        self.queue[server.id]["QUEUE"].appendleft(url)

    def _cache_desired_files(self):
        filelist = []
        for server in self.downloaders:
            song = self.downloaders[server].song
            try:
                filelist.append(song.id)
            except AttributeError:
                pass
        shuffle(filelist)
        return filelist

    def _cache_max(self):
        setting_max = self.settings["MAX_CACHE"]
        return max([setting_max, self._cache_min()])  # enforcing hard limit

    def _cache_min(self):
        x = self._server_count()
        return max([60, 48 * math.log(x) * x**0.3])  # log is not log10

    def _cache_required_files(self):
        queue = copy.deepcopy(self.queue)
        filelist = []
        for server in queue:
            now_playing = queue[server].get("NOW_PLAYING")
            try:
                filelist.append(now_playing.id)
            except AttributeError:
                pass
        return filelist

    def _cache_size(self):
        songs = os.listdir(self.cache_path)
        size = sum(map(lambda s: os.path.getsize(
            os.path.join(self.cache_path, s)) / 10**6, songs))
        return size

    def _cache_too_large(self):
        if self._cache_size() > self._cache_max():
            return True
        return False

    def _clear_queue(self, server):
        if server.id not in self.queue:
            return
        self.queue[server.id]["QUEUE"] = deque()
        self.queue[server.id]["TEMP_QUEUE"] = deque()

    async def _create_ffmpeg_player(self, server, filename, local=False):
        """This function will guarantee we have a valid voice client,
            even if one doesn't exist previously."""
        voice_channel_id = self.queue[server.id]["VOICE_CHANNEL_ID"]
        voice_client = self.voice_client(server)

        if voice_client is None:
            log.debug("not connected when we should be in sid {}".format(
                server.id))
            to_connect = self.bot.get_channel(voice_channel_id)
            if to_connect is None:
                raise VoiceNotConnected("Aucun channel disponible")
            log.debug("valid reconnect channel for sid"
                      " {}, reconnexion...".format(server.id))
            await self._join_voice_channel(to_connect)  # SHIT
        elif voice_client.channel.id != voice_channel_id:
            # This was decided at 3:45 EST in #advanced-testing by 26
            self.queue[server.id]["VOICE_CHANNEL_ID"] = voice_client.channel.id
            log.debug("reconnexion chan id for sid {} is wrong, fixing".format(
                server.id))

        # Okay if we reach here we definitively have a working voice_client

        if local:
            song_filename = os.path.join(self.local_playlist_path, filename)
        else:
            song_filename = os.path.join(self.cache_path, filename)

        use_avconv = self.settings["AVCONV"]
        options = '-b:a 64k -bufsize 64k'

        try:
            voice_client.audio_player.process.kill()
            log.debug("killed old player")
        except AttributeError:
            pass
        except ProcessLookupError:
            pass

        log.debug("making player on sid {}".format(server.id))

        voice_client.audio_player = voice_client.create_ffmpeg_player(
            song_filename, use_avconv=use_avconv, options=options)

        # Set initial volume
        vol = self.get_server_settings(server)['VOLUME'] / 100
        voice_client.audio_player.volume = vol

        return voice_client  # Just for ease of use, it's modified in-place

    # TODO: _current_playlist

    # TODO: _current_song

    def _delete_playlist(self, server, name):
        if not name.endswith('.txt'):
            name = name + ".txt"
        try:
            os.remove(os.path.join('data/audio/playlists', server.id, name))
        except OSError:
            pass
        except WindowsError:
            pass

    # TODO: _disable_controls()

    async def _disconnect_voice_client(self, server):
        if not self.voice_connected(server):
            return

        voice_client = self.voice_client(server)

        await voice_client.disconnect()

    async def _download_all(self, url_list):
        """
        Doesn't actually download, just get's info for uses like queue_list
        """
        downloaders = []
        for url in url_list:
            d = Downloader(url)
            d.start()
            downloaders.append(d)

        while any([d.is_alive() for d in downloaders]):
            await asyncio.sleep(0.1)

        songs = [d.song for d in downloaders if d.song is not None]
        return songs

    async def _download_next(self, server, curr_dl, next_dl):
        """Checks to see if we need to download the next, and does.

        Both curr_dl and next_dl should already be started."""
        if curr_dl.song is None:
            # Only happens when the downloader thread hasn't initialized fully
            #   There's no reason to wait if we can't compare
            return

        max_length = self.settings["MAX_LENGTH"]

        while next_dl.is_alive():
            await asyncio.sleep(0.5)

        if curr_dl.song.id != next_dl.song.id:
            log.debug("downloader ID's mismatch on sid {}".format(server.id) +
                      " gonna start dl-ing the next thing on the queue"
                      " id {}".format(next_dl.song.id))
            try:
                next_dl.duration_check()
            except MaximumLength:
                return
            self.downloaders[server.id] = Downloader(next_dl.url, max_length,
                                                     download=True)
            self.downloaders[server.id].start()

    def _dump_cache(self, ignore_desired=False):
        reqd = self._cache_required_files()
        log.debug("required cache files:\n\t{}".format(reqd))

        opt = self._cache_desired_files()
        log.debug("desired cache files:\n\t{}".format(opt))

        prev_size = self._cache_size()

        for file in os.listdir(self.cache_path):
            if file not in reqd:
                if ignore_desired or file not in opt:
                    try:
                        os.remove(os.path.join(self.cache_path, file))
                    except OSError:
                        # A directory got in the cache?
                        pass
                    except WindowsError:
                        # Removing a file in use, reqd failed
                        pass

        post_size = self._cache_size()
        dumped = prev_size - post_size

        if not ignore_desired and self._cache_too_large():
            log.debug("must dump desired files")
            return dumped + self._dump_cache(ignore_desired=True)

        log.debug("dumped {} MB of audio files".format(dumped))

        return dumped

    # TODO: _enable_controls()

    # returns list of active voice channels
    # assuming list does not change during the execution of this function
    # if that happens, blame asyncio.
    def _get_active_voice_clients(self):
        avcs = []
        for vc in self.bot.voice_clients:
            if hasattr(vc, 'audio_player') and not vc.audio_player.is_done():
                avcs.append(vc)
        return avcs

    def _get_queue(self, server, limit):
        if server.id not in self.queue:
            return []

        ret = []
        for i in range(limit):
            try:
                ret.append(self.queue[server.id]["QUEUE"][i])
            except IndexError:
                pass

        return ret

    def _get_queue_nowplaying(self, server):
        if server.id not in self.queue:
            return None

        return self.queue[server.id]["NOW_PLAYING"]

    def _get_queue_playlist(self, server):
        if server.id not in self.queue:
            return None

        return self.queue[server.id]["PLAYLIST"]

    def _get_queue_repeat(self, server):
        if server.id not in self.queue:
            return None

        return self.queue[server.id]["REPEAT"]

    def _get_queue_tempqueue(self, server, limit):
        if server.id not in self.queue:
            return []

        ret = []
        for i in range(limit):
            try:
                ret.append(self.queue[server.id]["TEMP_QUEUE"][i])
            except IndexError:
                pass
        return ret

    async def _guarantee_downloaded(self, server, url):
        max_length = self.settings["MAX_LENGTH"]
        if server.id not in self.downloaders:  # We don't have a downloader
            log.debug("sid {} not in downloaders, making one".format(
                server.id))
            self.downloaders[server.id] = Downloader(url, max_length)

        if self.downloaders[server.id].url != url:  # Our downloader is old
            # I'm praying to Jeezus that we don't accidentally lose a running
            #   Downloader
            log.debug("sid {} in downloaders but wrong url".format(server.id))
            self.downloaders[server.id] = Downloader(url, max_length)

        try:
            # We're assuming we have the right thing in our downloader object
            self.downloaders[server.id].start()
            log.debug("starting our downloader for sid {}".format(server.id))
        except RuntimeError:
            # Queue manager already started it for us, isn't that nice?
            pass

        # Getting info w/o download
        self.downloaders[server.id].done.wait()

        # This will throw a maxlength exception if required
        self.downloaders[server.id].duration_check()
        song = self.downloaders[server.id].song

        log.debug("sid {} wants to play songid {}".format(server.id, song.id))

        # Now we check to see if we have a cache hit
        cache_location = os.path.join(self.cache_path, song.id)
        if not os.path.exists(cache_location):
            log.debug("cache miss on song id {}".format(song.id))
            self.downloaders[server.id] = Downloader(url, max_length,
                                                     download=True)
            self.downloaders[server.id].start()

            while self.downloaders[server.id].is_alive():
                await asyncio.sleep(0.5)

            song = self.downloaders[server.id].song
        else:
            log.debug("cache hit on song id {}".format(song.id))

        return song

    def _is_queue_playlist(self, server):
        if server.id not in self.queue:
            return False

        return self.queue[server.id]["PLAYLIST"]

    async def _join_voice_channel(self, channel):
        server = channel.server
        connect_time = self.connect_timers.get(server.id, 0)
        if time.time() < connect_time:
            diff = int(connect_time - time.time())
            raise ConnectTimeout("Impossible de se connecter. Attendez {}"
                                 " secondes.".format(diff))
        if server.id in self.queue:
            self.queue[server.id]["VOICE_CHANNEL_ID"] = channel.id
        try:
            await asyncio.wait_for(self.bot.join_voice_channel(channel),
                                   timeout=5, loop=self.bot.loop)
        except asyncio.futures.TimeoutError as e:
            log.exception(e)
            self.connect_timers[server.id] = time.time() + 300
            raise ConnectTimeout("Impossible de se connecter. Réessayez dans 10 minutes.")

    def _list_local_playlists(self):
        ret = []
        for thing in os.listdir(self.local_playlist_path):
            if os.path.isdir(os.path.join(self.local_playlist_path, thing)):
                ret.append(thing)
        log.debug("local playlists:\n\t{}".format(ret))
        return ret

    def _list_playlists(self, server):
        try:
            server = server.id
        except:
            pass
        path = "data/audio/playlists"
        old_playlists = [f[:-4] for f in os.listdir(path)
                         if f.endswith(".txt")]
        path = os.path.join(path, server)
        if os.path.exists(path):
            new_playlists = [f[:-4] for f in os.listdir(path)
                             if f.endswith(".txt")]
        else:
            new_playlists = []
        return list(set(old_playlists + new_playlists))

    def _load_playlist(self, server, name, local=True):
        try:
            server = server.id
        except:
            pass

        f = "data/audio/playlists"
        if local:
            f = os.path.join(f, server, name + ".txt")
        else:
            f = os.path.join(f, name + ".txt")
        kwargs = dataIO.load_json(f)

        kwargs['path'] = f
        kwargs['main_class'] = self
        kwargs['name'] = name
        kwargs['sid'] = server
        kwargs['server'] = self.bot.get_server(server)

        return Playlist(**kwargs)

    def _local_playlist_songlist(self, name):
        dirpath = os.path.join(self.local_playlist_path, name)
        return sorted(os.listdir(dirpath))

    def _make_local_song(self, filename):
        # filename should be playlist_folder/file_name
        folder, song = os.path.split(filename)
        return Song(name=song, id=filename, title=song, url=filename,
                    webpage_url=filename)

    def _make_playlist(self, author, url, songlist):
        try:
            author = author.id
        except:
            pass

        return Playlist(author=author, url=url, playlist=songlist)

    def _match_sc_playlist(self, url):
        return self._match_sc_url(url)

    def _match_yt_playlist(self, url):
        if not self._match_yt_url(url):
            return False
        yt_playlist = re.compile(
            r'^(https?\:\/\/)?(www\.)?(youtube\.com|youtu\.?be)'
            r'((\/playlist\?)|\/watch\?).*(list=)(.*)(&|$)')
        # Group 6 should be the list ID
        if yt_playlist.match(url):
            return True
        return False

    def _match_sc_url(self, url):
        sc_url = re.compile(
            r'^(https?\:\/\/)?(www\.)?(soundcloud\.com\/)')
        if sc_url.match(url):
            return True
        return False

    def _match_yt_url(self, url):
        yt_link = re.compile(
            r'^(https?\:\/\/)?(www\.|m\.)?(youtube\.com|youtu\.?be)\/.+$')
        if yt_link.match(url):
            return True
        return False

    def _match_any_url(self, url):
        url = urlparse(url)
        if url.scheme and url.netloc and url.path:
            return True
        return False

    # TODO: _next_songs_in_queue

    async def _parse_playlist(self, url):
        if self._match_sc_playlist(url):
            return await self._parse_sc_playlist(url)
        elif self._match_yt_playlist(url):
            return await self._parse_yt_playlist(url)
        raise InvalidPlaylist("L'URL donné ne provient ni de Youtube ni de Soundcloud")

    async def _parse_sc_playlist(self, url):
        playlist = []
        d = Downloader(url)
        d.start()

        while d.is_alive():
            await asyncio.sleep(0.5)

        for entry in d.song.entries:
            if entry["url"][4] != "s":
                song_url = "https{}".format(entry["url"][4:])
                playlist.append(song_url)
            else:
                playlist.append(entry.url)

        return playlist

    async def _parse_yt_playlist(self, url):
        d = Downloader(url)
        d.start()
        playlist = []

        while d.is_alive():
            await asyncio.sleep(0.5)

        for entry in d.song.entries:
            try:
                song_url = "https://www.youtube.com/watch?v={}".format(
                    entry['id'])
                playlist.append(song_url)
            except AttributeError:
                pass
            except TypeError:
                pass

        log.debug("song list:\n\t{}".format(playlist))

        return playlist

    async def _play(self, sid, url):
        """Returns the song object of what's playing"""
        if type(sid) is not discord.Server:
            server = self.bot.get_server(sid)
        else:
            server = sid

        assert type(server) is discord.Server
        log.debug('starting to play on "{}"'.format(server.name))

        if self._valid_playable_url(url) or "[SEARCH:]" in url:
            try:
                song = await self._guarantee_downloaded(server, url)
            except MaximumLength:
                log.warning("I can't play URL below because it is too long."
                            " Use [p]audioset maxlength to change this.\n\n"
                            "{}".format(url))
                raise
            local = False
        else:  # Assume local
            try:
                song = self._make_local_song(url)
                local = True
            except FileNotFoundError:
                raise

        voice_client = await self._create_ffmpeg_player(server, song.id,
                                                        local=local)
        # That ^ creates the audio_player property

        voice_client.audio_player.start()
        log.debug("starting player on sid {}".format(server.id))

        return song

    def _play_playlist(self, server, playlist):
        try:
            songlist = playlist.playlist
            name = playlist.name
        except AttributeError:
            songlist = playlist
            name = True

        log.debug("setting up playlist {} on sid {}".format(name, server.id))

        self._stop_player(server)
        self._stop_downloader(server)
        self._clear_queue(server)

        log.debug("finished resetting state on sid {}".format(server.id))

        self._setup_queue(server)
        self._set_queue_playlist(server, name)
        self._set_queue_repeat(server, True)
        self._set_queue(server, songlist)

    def _play_local_playlist(self, server, name):
        songlist = self._local_playlist_songlist(name)

        ret = []
        for song in songlist:
            ret.append(os.path.join(name, song))

        ret_playlist = Playlist(server=server, name=name, playlist=ret)
        self._play_playlist(server, ret_playlist)

    def _player_count(self):
        count = 0
        queue = copy.deepcopy(self.queue)
        for sid in queue:
            server = self.bot.get_server(sid)
            try:
                vc = self.voice_client(server)
                if vc.audio_player.is_playing():
                    count += 1
            except:
                pass
        return count

    def _playlist_exists(self, server, name):
        return self._playlist_exists_local(server, name) or \
            self._playlist_exists_global(name)

    def _playlist_exists_global(self, name):
        f = "data/audio/playlists"
        f = os.path.join(f, name + ".txt")
        log.debug('checking for {}'.format(f))

        return dataIO.is_valid_json(f)

    def _playlist_exists_local(self, server, name):
        try:
            server = server.id
        except AttributeError:
            pass

        f = "data/audio/playlists"
        f = os.path.join(f, server, name + ".txt")
        log.debug('checking for {}'.format(f))

        return dataIO.is_valid_json(f)

    def _remove_queue(self, server):
        if server.id in self.queue:
            del self.queue[server.id]

    async def _remove_song_status(self):
        if self._old_game is not False:
            status = list(self.bot.servers)[0].me.status
            await self.bot.change_presence(game=self._old_game,
                                           status=status)
            log.debug('Bot status returned to ' + str(self._old_game))
            self._old_game = False

    def _save_playlist(self, server, name, playlist):
        sid = server.id
        try:
            f = playlist.filename
            playlist = playlist.to_json()
            log.debug("got playlist object")
        except AttributeError:
            f = os.path.join("data/audio/playlists", sid, name + ".txt")

        head, _ = os.path.split(f)
        if not os.path.exists(head):
            os.makedirs(head)

        log.debug("saving playlist '{}' to {}:\n\t{}".format(name, f,
                                                             playlist))
        dataIO.save_json(f, playlist)

    def _shuffle_queue(self, server):
        shuffle(self.queue[server.id]["QUEUE"])

    def _shuffle_temp_queue(self, server):
        shuffle(self.queue[server.id]["TEMP_QUEUE"])

    def _server_count(self):
        return max([1, len(self.bot.servers)])

    def _set_queue(self, server, songlist):
        if server.id in self.queue:
            self._clear_queue(server)
        else:
            self._setup_queue(server)
        self.queue[server.id]["QUEUE"].extend(songlist)

    def _set_queue_channel(self, server, channel):
        if server.id not in self.queue:
            return

        try:
            channel = channel.id
        except AttributeError:
            pass

        self.queue[server.id]["VOICE_CHANNEL_ID"] = channel

    def _set_queue_nowplaying(self, server, song):
        if server.id not in self.queue:
            return

        self.queue[server.id]["NOW_PLAYING"] = song

    def _set_queue_playlist(self, server, name=True):
        if server.id not in self.queue:
            self._setup_queue(server)

        self.queue[server.id]["PLAYLIST"] = name

    def _set_queue_repeat(self, server, value):
        if server.id not in self.queue:
            self._setup_queue(server)

        self.queue[server.id]["REPEAT"] = value

    def _setup_queue(self, server):
        self.queue[server.id] = {"REPEAT": False, "PLAYLIST": False,
                                 "VOICE_CHANNEL_ID": None,
                                 "QUEUE": deque(), "TEMP_QUEUE": deque(),
                                 "NOW_PLAYING": None}

    def _stop(self, server):
        self._setup_queue(server)
        self._stop_player(server)
        self._stop_downloader(server)
        self.bot.loop.create_task(self._update_bot_status())

    async def _stop_and_disconnect(self, server):
        self._stop(server)
        await self._disconnect_voice_client(server)

    def _stop_downloader(self, server):
        if server.id not in self.downloaders:
            return

        del self.downloaders[server.id]

    def _stop_player(self, server):
        if not self.voice_connected(server):
            return

        voice_client = self.voice_client(server)

        if hasattr(voice_client, 'audio_player'):
            voice_client.audio_player.stop()

    # no return. they can check themselves.
    async def _update_bot_status(self):
        if self.settings["TITLE_STATUS"]:
            song = None
            try:
                active_servers = self._get_active_voice_clients()
            except:
                log.debug("Voice client changed while trying to update bot's"
                          " song status")
                return
            if len(active_servers) == 1:
                server = active_servers[0].server
                song = self.queue[server.id]["NOW_PLAYING"]
            if song:
                await self._add_song_status(song)
            else:
                await self._remove_song_status()

    def _valid_playlist_name(self, name):
        for char in name:
            if char.isdigit() or char.isalpha() or char == "_":
                pass
            else:
                return False
        return True

    def _valid_playable_url(self, url):
        yt = self._match_yt_url(url)
        sc = self._match_sc_url(url)
        if yt or sc:  # TODO: Add sc check
            return True
        return False

    @commands.group(pass_context=True)
    async def audioset(self, ctx):
        """Réglages audio."""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)
            return

    @audioset.command(name="cachemax")
    async def audioset_cachemax(self, size: int):
        """Taille du cache"""
        if size < self._cache_min():
            await self.bot.say("Le minimum de cache, compte tenu du nombre de serveurs où je suis connecté, est de {} MB.".format(
                                   self._cache_min()))
            return

        self.settings["MAX_CACHE"] = size
        await self.bot.say("Max cache size set to {} MB.".format(size))
        self.save_settings()

    @audioset.command(name="emptydisconnect", pass_context=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def audioset_emptydisconnect(self, ctx):
        """Active la déconnexion automatique lorsqu'il n'y a plus personne sur le channel."""
        server = ctx.message.server
        settings = self.get_server_settings(server.id)
        noppl_disconnect = settings.get("NOPPL_DISCONNECT", True)
        self.set_server_setting(server, "NOPPL_DISCONNECT",
                                not noppl_disconnect)
        if not noppl_disconnect:
            await self.bot.say("Déconnexion automatique activée.")
        else:
            await self.bot.say("Déconnexion automatique désactivée.")
        self.save_settings()

    @audioset.command(name="maxlength")
    @checks.is_owner()
    async def audioset_maxlength(self, length: int):
        """Longueur maximale des vidéos (en secondes)"""
        if length <= 0:
            await self.bot.say("La valeur doit être positive...")
            return
        self.settings["MAX_LENGTH"] = length
        await self.bot.say("La longueur maximale est maintenant de {} secondes.".format(length))
        self.save_settings()

    @audioset.command(name="player")
    @checks.is_owner()
    async def audioset_player(self):
        """Change la bibliothèque audio (AvConv/Ffmpeg)"""
        self.settings["AVCONV"] = not self.settings["AVCONV"]
        if self.settings["AVCONV"]:
            await self.bot.say("Vous utilisez maintenant AVCONV.")
        else:
            await self.bot.say("Vous utilisez maintenant FFMPEG.")
        self.save_settings()

    @audioset.command(name="status")
    @checks.is_owner()  # cause effect is cross-server
    async def audioset_status(self):
        """Active/Désactive le changement de statut à chaque musique."""
        self.settings["TITLE_STATUS"] = not self.settings["TITLE_STATUS"]
        if self.settings["TITLE_STATUS"]:
            await self.bot.say("Activé")
            # not updating on disable if we say disable
            #   means don't mess with it.
            await self._update_bot_status()
        else:
            await self.bot.say("Désactivé")
        self.save_settings()

    @audioset.command(pass_context=True, name="volume", no_pm=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def audioset_volume(self, ctx, percent: int=None):
        """Change le volume audio (0 - 100%)
        Il est possible d'aller jusqu'a 200% mais il pourrait y avoir des glitchs."""
        server = ctx.message.server
        if percent is None:
            vol = self.get_server_settings(server)['VOLUME']
            msg = "Le volume est désormais à %d%%" % vol
        elif percent >= 0 and percent <= 200:
            self.set_server_setting(server, "VOLUME", percent)
            msg = "Le volume est maintenant à %d." % percent
            if percent > 100:
                msg += ("\nAttention: Les volumes supérieur à 100 peuvent causer des glitchs audio.")

            # Set volume of playing audio
            vc = self.voice_client(server)
            if vc:
                vc.audio_player.volume = percent / 100

            self.save_settings()
        else:
            msg = "Le volume doit être entre 0 et 200."
        await self.bot.say(msg)

    @audioset.command(pass_context=True, name="vote", no_pm=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def audioset_vote(self, ctx, percent: int):
        """Pourcentage de vote nécéssaire afin de passer la musique. (Pour les non-staff)"""
        server = ctx.message.server

        if percent < 0:
            await self.bot.say("Supérieur à 0 ?")
            return
        elif percent > 100:
            percent = 100

        if percent == 0:
            enabled = False
            await self.bot.say("Le vote est désactivé. Tous les utilisateurs peuvent skip et stop.")
        else:
            enabled = True
            await self.bot.say("Pourcentage réglé à {}%".format(percent))

        self.set_server_setting(server, "VOTE_THRESHOLD", percent)
        self.set_server_setting(server, "VOTE_ENABLED", enabled)
        self.save_settings()

    @commands.group(name = "surv", pass_context=True, no_pm=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def surv_sys(self, ctx):
        """Contrôle de la surveillance"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @surv_sys.command(pass_context=True, no_pm=True)
    async def role(self, ctx, role: discord.Role):
        """Définit un rôle nécéssaire afin d'être libéré de la surveillance."""
        self.surv["SYS"]["LIBERE_ROLE"] = role.name
        dataIO.save_json('data/audio/surv.json', self.surv)
        await self.bot.say("Rôle réglé.")

    @surv_sys.command(pass_context=True, no_pm=True)
    async def playtick(self, ctx, nombre: int):
        """Définit le nombre de tickets nécéssaire pour lancer un seul morceau."""
        self.surv["SYS"]["PLAY_TICKETS"] = nombre
        dataIO.save_json('data/audio/surv.json', self.surv)
        await self.bot.say("Il faut désormais {} tickets aux sans-rôles pour passer un morceau.".format(nombre))

    @surv_sys.command(pass_context=True, no_pm=True)
    async def playlisttick(self, ctx, nombre: int):
        """Définit le nombre de tickets nécéssaire pour lancer une playlist entière."""
        self.surv["SYS"]["PLAYLIST_TICKETS"] = nombre
        dataIO.save_json('data/audio/surv.json', self.surv)
        await self.bot.say("Il faut désormais {} tickets aux sans-rôles pour passer une playlist.".format(nombre))

    @surv_sys.command(pass_context=True, no_pm=True)
    async def defaut(self, ctx, nombre: int):
        """Définit le nombre de tickets disponible chaque jour pour les sans-rôles."""
        self.surv["SYS"]["MAX_TICKETS"] = nombre
        dataIO.save_json('data/audio/surv.json', self.surv)
        await self.bot.say("Il faut désormais {} tickets aux sans-rôles pour passer un morceau.".format(nombre))

    @commands.group(pass_context=True)
    async def audiostat(self, ctx):
        """Statistiques sur l'audio."""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)
            return

    @audiostat.command(name="servers")
    async def audiostat_servers(self):
        """Nombre de serveurs où le bot joue."""

        count = self._player_count()

        await self.bot.say("Je joue de la musique dans {} servers.".format(
            count))

    @commands.group(pass_context=True)
    async def cache(self, ctx):
        """Réglages du cache."""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)
            return

    @cache.command(name="dump")
    @checks.is_owner()
    async def cache_dump(self):
        """Efface le cache."""
        dumped = self._dump_cache()
        await self.bot.say("Suppression de {:.3f} MB de fichiers audios.".format(dumped))

    @cache.command(name="minimum")
    async def cache_minimum(self):
        """Taille minimale du cache."""
        await self.bot.say("Le cache sera au minimum de {:.3f} MB".format(
            self._cache_min()))

    @cache.command(name="size")
    async def cache_size(self):
        """Taille du cache."""
        await self.bot.say("Le cache fait {:.3f} MB.".format(
            self._cache_size()))

    @commands.group(pass_context=True, hidden=True, no_pm=True)
    @checks.is_owner()
    async def disconnect(self, ctx):
        """Déconnecte le bot sur le serveur vocal."""
        if ctx.invoked_subcommand is None:
            server = ctx.message.server
            await self._stop_and_disconnect(server)

    @disconnect.command(name="all", hidden=True, no_pm=True)
    async def disconnect_all(self):
        """Déconnecte le bot de tous les serveurs vocaux."""
        while len(list(self.bot.voice_clients)) != 0:
            vc = list(self.bot.voice_clients)[0]
            await self._stop_and_disconnect(vc.server)
        await self.bot.say("Fait.")

    @commands.command(hidden=True, pass_context=True, no_pm=True)
    @checks.is_owner()
    async def joinvoice(self, ctx):
        """Rejoindre votre channel audio."""
        author = ctx.message.author
        server = ctx.message.server
        voice_channel = author.voice_channel

        if voice_channel is not None:
            self._stop(server)

        await self._join_voice_channel(voice_channel)

    @commands.group(pass_context=True, no_pm=True)
    async def local(self, ctx):
        """Commandes de playlists locales"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @local.command(name="start", pass_context=True, no_pm=True)
    async def play_local(self, ctx, *, name):
        """Joue une playlist"""
        server = ctx.message.server
        author = ctx.message.author
        self.surv_acc(author)
        min = self.surv["SYS"]["PLAYLIST_TICKETS"]
        if not await self.surv_autorise(author, min):
            await self.bot.say("Vous avez besoin de {} tickets pour jouer une playlist. Vous n'en avez pas assez ({}).".format(min,
                                                                                                          self.surv[
                                                                                                              "USERS"][
                                                                                                              author.id][
                                                                                                              "TICKETS"]))
            return

        voice_channel = author.voice_channel

        # Checking already connected, will join if not

        if not self.voice_connected(server):
            try:
                self.has_connect_perm(author, server)
            except AuthorNotConnected:
                await self.bot.say("Vous devez rejoindre un salon vocal d'abord.")
                return
            except UnauthorizedConnect:
                await self.bot.say("Je ne peux pas vous rejoindre sur ce salon.")
                return
            except UnauthorizedSpeak:
                await self.bot.say("Je n'ai pas le droit de parler sur ce salon.")
                return
            except ChannelUserLimit:
                await self.bot.say("Ce channel est plein.")
                return
            else:
                await self._join_voice_channel(voice_channel)
        else:  # We are connected but not to the right channel
            if self.voice_client(server).channel != voice_channel:
                pass  # TODO: Perms

        # Checking if playing in current server

        if self.is_playing(server):
            await self.bot.say("Je joue déjà cette musique !")
            return  # TODO: Possibly execute queue?

        # If not playing, spawn a downloader if it doesn't exist and begin
        #   downloading the next song

        if self.currently_downloading(server):
            await self.bot.say("Je télécharge un fichier. Patientez et recommencez...")
            return

        lists = self._list_local_playlists()

        if not any(map(lambda l: os.path.split(l)[1] == name, lists)):
            await self.bot.say("Cette playlist n'existe pas.")
            return

        self._play_local_playlist(server, name)

    @local.command(name="list", no_pm=True)
    async def list_local(self):
        """Listes des playlists locales"""
        playlists = ", ".join(self._list_local_playlists())
        if playlists:
            playlists = "Playlists disponibles :\n\n" + playlists
            for page in pagify(playlists, delims=[" "]):
                await self.bot.say(page)
        else:
            await self.bot.say("Aucune playlist disponible.")

    @commands.command(pass_context=True, no_pm=True)
    async def pause(self, ctx):
        """Met en pause la musique en cours."""
        server = ctx.message.server
        if not self.voice_connected(server):
            await self.bot.say("Je ne suis pas connecté.")
            return

        # We are connected somewhere
        voice_client = self.voice_client(server)

        if not hasattr(voice_client, 'audio_player'):
            await self.bot.say("Rien ne joue.")
        elif voice_client.audio_player.is_playing():
            voice_client.audio_player.pause()
            await self.bot.say("**Pause**\n*Utilisez {}resume pour rejouer*".format(ctx.prefix))
        else:
            await self.bot.say("Rien ne joue.")

    @commands.command(pass_context=True, no_pm=True)
    async def play(self, ctx, *, url_or_search_terms):
        """Passe une musique/Recherche et passe la musique"""
        url = url_or_search_terms
        server = ctx.message.server
        author = ctx.message.author
        self.surv_acc(author)
        min = self.surv["SYS"]["PLAY_TICKETS"]
        if not await self.surv_autorise(author, min):
            await self.bot.say(
                "Vous avez besoin de {} tickets pour jouer un morceau. Vous n'en avez pas assez ({}).".format(min, self.surv["USERS"][author.id]["TICKETS"]))
            return
        voice_channel = author.voice_channel

        # Checking if playing in current server

        if self.is_playing(server):
            await ctx.invoke(self._queue, url=url)
            return  # Default to queue

        # Checking already connected, will join if not

        try:
            self.has_connect_perm(author, server)
        except AuthorNotConnected:
            await self.bot.say("Rejoignez d'abord un salon vocal.")
            return
        except UnauthorizedConnect:
            await self.bot.say("Je n'ai pas la permission de vous rejoindre.")
            return
        except UnauthorizedSpeak:
            await self.bot.say("Je n'ai pas le droit de parler sur ce channel.")
            return
        except ChannelUserLimit:
            await self.bot.say("Ce salon est plein.")
            return

        if not self.voice_connected(server):
            await self._join_voice_channel(voice_channel)
        else:  # We are connected but not to the right channel
            if self.voice_client(server).channel != voice_channel:
                await self._stop_and_disconnect(server)
                await self._join_voice_channel(voice_channel)

        # If not playing, spawn a downloader if it doesn't exist and begin
        #   downloading the next song

        if self.currently_downloading(server):
            await self.bot.say("Je télécharge un fichier. Réessayez d'ici quelques secondes...")
            return

        url = url.strip("<>")

        if self._match_any_url(url):
            if not self._valid_playable_url(url):
                await self.bot.say("URL invalide.")
                return
        else:
            url = url.replace("/", "&#47")
            url = "[SEARCH:]" + url

        if "[SEARCH:]" not in url and "youtube" in url:
            url = url.split("&")[0]  # Temp fix for the &list issue

        self._stop_player(server)
        self._clear_queue(server)
        self._add_to_queue(server, url)

    @commands.command(pass_context=True, no_pm=True)
    async def prev(self, ctx):
        """Retourne à la musique précédente."""
        # Current song is in NOW_PLAYING
        server = ctx.message.server

        if self.is_playing(server):
            curr_url = self._get_queue_nowplaying(server).webpage_url
            last_url = None
            if self._is_queue_playlist(server):
                # need to reorder queue
                try:
                    last_url = self.queue[server.id]["QUEUE"].pop()
                except IndexError:
                    pass

            log.debug("prev on sid {}, curr_url {}".format(server.id,
                                                           curr_url))

            self._addleft_to_queue(server, curr_url)
            if last_url:
                self._addleft_to_queue(server, last_url)
            self._set_queue_nowplaying(server, None)

            self.voice_client(server).audio_player.stop()

            await self.bot.say("**RETOUR EN ARRIEEEEEERE**")
        else:
            await self.bot.say("Je ne joue rien.")

    @commands.group(pass_context=True, no_pm=True)
    async def playlist(self, ctx):
        """Contrôle des playlists"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @playlist.command(pass_context=True, no_pm=True, name="create")
    async def playlist_create(self, ctx, name):
        """Créer une playlist vide"""
        server = ctx.message.server
        author = ctx.message.author
        if not self._valid_playlist_name(name) or len(name) > 25:
            await self.bot.say("Le nom de la playlist est invalide.")
            return

        # Returns a Playlist object
        url = None
        songlist = []
        playlist = self._make_playlist(author, url, songlist)

        playlist.name = name
        playlist.server = server

        self._save_playlist(server, name, playlist)
        await self.bot.say("Playlist '{}' créée.".format(name))

    @playlist.command(pass_context=True, no_pm=True, name="add")
    async def playlist_add(self, ctx, name, url):
        """Ajoute une playlist Youtube ou Soundcloud."""
        server = ctx.message.server
        author = ctx.message.author
        if not self._valid_playlist_name(name) or len(name) > 25:
            await self.bot.say("Le nom de la playlist est invalide.")
            return

        if self._valid_playable_url(url):
            try:
                await self.bot.say("Enumération des liens. Patientez un moment...")
                await asyncio.sleep(0.25)
                songlist = await self._parse_playlist(url)
            except InvalidPlaylist:
                await self.bot.say("URL invalide.")
                return

            playlist = self._make_playlist(author, url, songlist)
            # Returns a Playlist object

            playlist.name = name
            playlist.server = server

            self._save_playlist(server, name, playlist)
            await self.bot.say("La playlist '{}' est désormais disponible.\n*Composée de {} morceaux*".format(
                name, len(songlist)))
        else:
            await self.bot.say("URL Invalide. Faîtes attention à donner un lien de playlist (regardez l'URL), et non un lien de compte.")

    @playlist.command(pass_context=True, no_pm=True, name="append")
    async def playlist_append(self, ctx, name, url):
        """Ajoute un morceau à une playlist."""
        author = ctx.message.author
        server = ctx.message.server
        if name not in self._list_playlists(server):
            await self.bot.say("Aucune playlist avec ce nom.")
            return
        playlist = self._load_playlist(
            server, name, local=self._playlist_exists_local(server, name))
        try:
            playlist.append_song(author, url)
        except UnauthorizedSave:
            await self.bot.say("Vous n'êtes pas l'auteur de cette playlist.")
        except InvalidURL:
            await self.bot.say("Lien invalide.")
        else:
            await self.bot.say("Réalisé avec succès.")

    @playlist.command(pass_context=True, no_pm=True, name="extend", hidden=True)
    async def playlist_extend(self, ctx, playlist_url_or_name):
        """Permet d'etendre une playlist avec une autre playlist."""
        # Need better wording ^
        await self.bot.say("Indisponible pour le moment.")

    @playlist.command(pass_context=True, no_pm=True, name="list")
    async def playlist_list(self, ctx):
        """Liste toutes les playlists disponibles."""
        server = ctx.message.server
        playlists = ", ".join(self._list_playlists(server))
        if playlists:
            playlists = "Playlists disponibles :\n\n" + playlists
            for page in pagify(playlists, delims=[" "]):
                await self.bot.say(page)
        else:
            await self.bot.say("Aucune playlist n'est disponible.")

    @playlist.command(pass_context=True, no_pm=True, name="queue")
    async def playlist_queue(self, ctx, url):
        """Ajoute un morceau dans la liste d'attente d'une playlist sans l'ajouter dans celle-ci.

        Cet ajout est temporaire dans la playlist et il sera retiré après son passage."""
        author = ctx.message.author
        self.surv_acc(author)
        min = self.surv["SYS"]["PLAYLIST_TICKETS"]
        if not await self.surv_autorise(author, min):
            await self.bot.say(
                "Vous avez besoin de {} tickets pour jouer un morceau. Vous n'en avez pas assez ({}).".format(min,
                                                                                                              self.surv[
                                                                                                                  "USERS"][
                                                                                                                  author.id][
                                                                                                                  "TICKETS"]))
            return
        server = ctx.message.server
        if not self.voice_connected(server):
            await self.bot.say("Non connecté à un channel vocal.")
            return

        # We are connected somewhere
        if server.id not in self.queue:
            log.debug("Impossible d'ajouter cette musique")
            raise VoiceNotConnected("Impossible d'ajouter ce morceau  la liste d'attente.")

        # We have a queue to modify
        self._add_to_queue(server, url)

        await self.bot.say("**Ajouté**")

    @playlist.command(pass_context=True, no_pm=True, name="remove")
    async def playlist_remove(self, ctx, name):
        """Supprime une playlist."""
        author = ctx.message.author
        server = ctx.message.server

        if not self._valid_playlist_name(name):
            await self.bot.say("Ce nom contient des caractères non acceptés.")
            return

        if not self._playlist_exists(server, name):
            await self.bot.say("Introuvable.")
            return

        playlist = self._load_playlist(
            server, name, local=self._playlist_exists_local(server, name))

        if not playlist.can_edit(author):
            await self.bot.say("Vous n'avez pas l'autorisation de supprimer cette playlist.")
            return

        self._delete_playlist(server, name)
        await self.bot.say("Playlist supprimée avec succès.")

    @commands.command(pass_context=True, no_pm=True, name="dispo")
    async def tick_restant(self, ctx):
        """Affiche vos tickets restant"""
        author = ctx.message.author
        if self.surv["SYS"]["LIBERE_ROLE"] not in [r.name for r in author.roles]:
            await self.bot.say("Il vous reste {} tickets pour aujourd'hui.\nIl vous en faut {} pour un morceau et {} pour une playlist.".format(self.surv["USERS"][author.id]["TICKETS"], self.surv["SYS"]["PLAY_TICKETS"], self.surv["SYS"]["PLAYLIST_TICKETS"]))
        else:
            await self.bot.say("Vous n'avez pas besoin de tickets pour jouer de la musique.")

    @playlist.command(pass_context=True, no_pm=True, name="start")
    async def playlist_start(self, ctx, name):
        """Joue une playlist."""
        server = ctx.message.server
        author = ctx.message.author
        voice_channel = ctx.message.author.voice_channel
        self.surv_acc(author)
        min = self.surv["SYS"]["PLAYLIST_TICKETS"]
        if not await self.surv_autorise(author, min):
            await self.bot.say(
                "Vous avez besoin de {} tickets pour jouer une playlist. Vous n'en avez pas assez ({}).".format(min,
                                                                                                              self.surv[
                                                                                                                  "USERS"][
                                                                                                                  author.id][
                                                                                                                  "TICKETS"]))
            return

        caller = inspect.currentframe().f_back.f_code.co_name

        if voice_channel is None:
            await self.bot.say("Vous devez être connecté en vocal d'abord.")
            return

        if self._playlist_exists(server, name):
            if not self.voice_connected(server):
                try:
                    self.has_connect_perm(author, server)
                except AuthorNotConnected:
                    await self.bot.say("Rejoignez un channel audio avant...")
                    return
                except UnauthorizedConnect:
                    await self.bot.say("Je n'ai pas le droit de vous rejoindre sur ce channel.")
                    return
                except UnauthorizedSpeak:
                    await self.bot.say("Je n'ai pas le droit de parler sur ce channel.")
                    return
                except ChannelUserLimit:
                    await self.bot.say("Channel plein.")
                    return
                else:
                    await self._join_voice_channel(voice_channel)
            self._clear_queue(server)
            playlist = self._load_playlist(server, name,
                                           local=self._playlist_exists_local(
                                               server, name))
            if caller == "playlist_start_mix":
                shuffle(playlist.playlist)

            self._play_playlist(server, playlist)
            await self.bot.say("Playlist ajoutée à la liste d'attente.")
        else:
            await self.bot.say("Playlist inexistante.")

    @playlist.command(pass_context=True, no_pm=True, name="mix")
    async def playlist_start_mix(self, ctx, name):
        """Ajoute et mélange une playlist."""
        await self.playlist_start.callback(self, ctx, name)

    @commands.command(pass_context=True, no_pm=True, name="queue")
    async def _queue(self, ctx, *, url=None):
        """Ajoute un morceau à la liste d'attente avec une URL

        Si vous utilisez la commande sans URL, elle renvoie la liste des morceaux qui vont être joués."""
        author = ctx.message.author
        self.surv_acc(author)
        min = self.surv["SYS"]["PLAY_TICKETS"]
        if url != None:
            if not await self.surv_autorise(author, min):
                await self.bot.say(
                    "Vous avez besoin de {} tickets pour jouer un morceau. Vous n'en avez pas assez ({}).".format(min,
                                                                                                                  self.surv[
                                                                                                                      "USERS"][
                                                                                                                      author.id][
                                                                                                                      "TICKETS"]))
                return
        if url is None:
            return await self._queue_list(ctx)
        server = ctx.message.server
        if not self.voice_connected(server):
            await ctx.invoke(self.play, url_or_search_terms=url)
            return

        # We are connected somewhere
        if server.id not in self.queue:
            log.debug("Something went wrong, we're connected but have no"
                      " queue entry.")
            raise VoiceNotConnected("Impossible de rajouter ce morceau.")

        url = url.strip("<>")

        if self._match_any_url(url):
            if not self._valid_playable_url(url):
                await self.bot.say("URL invalide. J'accepte les liens Youtube et Soundcloud seulement.")
                return
        else:
            url = "[SEARCH:]" + url

        if "[SEARCH:]" not in url and "youtube" in url:
            url = url.split("&")[0]  # Temp fix for the &list issue

        # We have a queue to modify
        if self.queue[server.id]["PLAYLIST"]:
            log.debug("queueing to the temp_queue for sid {}".format(
                server.id))
            self._add_to_temp_queue(server, url)
        else:
            log.debug("queueing to the actual queue for sid {}".format(
                server.id))
            self._add_to_queue(server, url)
        await self.bot.say("**Ajouté**")

    async def _queue_list(self, ctx):
        """Ce n'est pas une commande, c'est un morceau de commande :smart:"""
        server = ctx.message.server
        if server.id not in self.queue:
            await self.bot.say("Rien ne joue sur ce serveur.")
            return
        elif len(self.queue[server.id]["QUEUE"]) == 0:
            await self.bot.say("Rien ne joue sur ce serveur.")
            return

        msg = ""

        now_playing = self._get_queue_nowplaying(server)

        if now_playing is not None:
            msg += "\n***En ce moment:***\n{}\n".format(now_playing.title)

        queue_url_list = self._get_queue(server, 5)
        tempqueue_url_list = self._get_queue_tempqueue(server, 5)

        await self.bot.say("*Recherche...*")

        queue_song_list = await self._download_all(queue_url_list)
        tempqueue_song_list = await self._download_all(tempqueue_url_list)

        song_info = []
        for num, song in enumerate(tempqueue_song_list, 1):
            try:
                song_info.append("{}. {.title}".format(num, song))
            except AttributeError:
                song_info.append("{}. {.webpage_url}".format(num, song))

        for num, song in enumerate(queue_song_list, len(song_info) + 1):
            if num > 5:
                break
            try:
                song_info.append("{}. {.title}".format(num, song))
            except AttributeError:
                song_info.append("{}. {.webpage_url}".format(num, song))
        msg += "\n***Prochainement:***\n" + "\n".join(song_info)

        await self.bot.say(msg)

    @commands.group(pass_context=True, no_pm=True)
    async def repeat(self, ctx):
        """Active la lecture en boucle de la liste d'attente."""
        server = ctx.message.server
        if ctx.invoked_subcommand is None:
            if self.is_playing(server):
                if self.queue[server.id]["REPEAT"]:
                    msg = "La file d'attente sera jouée en boucle."
                else:
                    msg = "Elle ne sera plus jouée en boucle."
                await self.bot.say(msg)
                await self.bot.say(
                    "Faîtes `{}repeat toggle` pour changer.".format(ctx.prefix))
            else:
                await self.bot.say("Jouez quelque chose pour voir ce paramètre.")

    @repeat.command(pass_context=True, no_pm=True, name="toggle")
    async def repeat_toggle(self, ctx):
        """Change le paramètre de mise en boucle."""
        server = ctx.message.server
        if not self.is_playing(server):
            await self.bot.say("Jouez quelque chose d'abord.")
            return

        self._set_queue_repeat(server, not self.queue[server.id]["REPEAT"])
        repeat = self.queue[server.id]["REPEAT"]
        if repeat:
            await self.bot.say("Activé.")
        else:
            await self.bot.say("Désactivé.")

    @commands.command(pass_context=True, no_pm=True)
    async def resume(self, ctx):
        """Relance un morceau mis en pause"""
        server = ctx.message.server
        if not self.voice_connected(server):
            await self.bot.say("Je ne suis pas connecté en vocal.")
            return

        # We are connected somewhere
        voice_client = self.voice_client(server)

        if not hasattr(voice_client, 'audio_player'):
            await self.bot.say("Rien n'est en pause.")
        elif not voice_client.audio_player.is_done() and \
                not voice_client.audio_player.is_playing():
            voice_client.audio_player.resume()
            await self.bot.say("**Relance**")
        else:
            await self.bot.say("Rien n'est en pause...")

    @commands.command(pass_context=True, no_pm=True, name="shuffle")
    async def _shuffle(self, ctx):
        """Mélange la liste d'attente"""
        server = ctx.message.server
        if server.id not in self.queue:
            await self.bot.say("Je n'ai rien dans la liste d'attente.")
            return

        self._shuffle_queue(server)
        self._shuffle_temp_queue(server)

        await self.bot.say("File d'attente mélangée.")

    @commands.command(pass_context=True, aliases=["next"], no_pm=True)
    async def skip(self, ctx):
        """Permet de sauter un morceau.
        Si l'utilisateur n'est pas un membre du staff, déclenche le vote."""
        msg = ctx.message
        server = ctx.message.server
        if self.is_playing(server):
            vchan = server.me.voice_channel
            vc = self.voice_client(server)
            if msg.author.voice_channel == vchan:
                if self.can_instaskip(msg.author):
                    vc.audio_player.stop()
                    if self._get_queue_repeat(server) is False:
                        self._set_queue_nowplaying(server, None)
                    await self.bot.say("Passe...")
                else:
                    if msg.author.id in self.skip_votes[server.id]:
                        self.skip_votes[server.id].remove(msg.author.id)
                        reply = "J'ai retiré votre vote."
                    else:
                        self.skip_votes[server.id].append(msg.author.id)
                        reply = "Vous avez voté pour passer ce morceau."

                    num_votes = len(self.skip_votes[server.id])
                    # Exclude bots and non-plebs
                    num_members = sum(not (m.bot or self.can_instaskip(m))
                                      for m in vchan.voice_members)
                    vote = int(100 * num_votes / num_members)
                    thresh = self.get_server_settings(server)["VOTE_THRESHOLD"]

                    if vote >= thresh:
                        vc.audio_player.stop()
                        if self._get_queue_repeat(server) is False:
                            self._set_queue_nowplaying(server, None)
                        self.skip_votes[server.id] = []
                        await self.bot.say("Vote threshold met. Skipping...")
                        return
                    else:
                        reply += " Votes: %d/%d" % (num_votes, num_members)
                        reply += " (%d%% sur %d%% nécéssaire)" % (vote, thresh)
                    await self.bot.reply(reply)
            else:
                await self.bot.say("Vous avez besoin d'être dans le canal audio pour sauter cette musique.")
        else:
            await self.bot.say("Impossible, je ne joue rien.")

    def can_instaskip(self, member):
        server = member.server

        if not self.get_server_settings(server)["VOTE_ENABLED"]:
            return True

        admin_role = settings.get_server_admin(server)
        mod_role = settings.get_server_mod(server)

        is_owner = member.id == settings.owner
        is_server_owner = member == server.owner
        is_admin = discord.utils.get(member.roles, name=admin_role) is not None
        is_mod = discord.utils.get(member.roles, name=mod_role) is not None


        nonbots = sum(not m.bot for m in member.voice_channel.voice_members)
        alone = nonbots <= 1

        return is_owner or is_server_owner or is_admin or is_mod or alone

    @commands.command(pass_context=True, no_pm=True, hidden=True)
    async def sing(self, ctx):
        """Faîtes chanter le bot"""
        ids = ("zGTkAVsrfg8", "cGMWL8cOeAU", "vFrjMq4aL-g", "WROI5WYBU_A",
               "41tIUr_ex3g", "f9O2Rjn1azc")
        url = "https://www.youtube.com/watch?v={}".format(choice(ids))
        await ctx.invoke(self.play, url_or_search_terms=url)

    @commands.command(pass_context=True, no_pm=True)
    async def song(self, ctx):
        """Affiche des informations sur le morceau en cours."""
        server = ctx.message.server
        if not self.is_playing(server):
            await self.bot.say("Je ne joue rien en ce moment.")
            return

        song = self._get_queue_nowplaying(server)
        if song:
            if not hasattr(song, 'creator'):
                song.creator = None
            if not hasattr(song, 'view_count'):
                song.view_count = None
            if not hasattr(song, 'uploader'):
                song.uploader = None
            if hasattr(song, 'duration'):
                m, s = divmod(song.duration, 60)
                h, m = divmod(m, 60)
                if h:
                    dur = "{0}:{1:0>2}:{2:0>2}".format(h, m, s)
                else:
                    dur = "{0}:{1:0>2}".format(m, s)
            else:
                dur = None
            em = discord.Embed(title=song.title, description= song.creator,color=user.color)
            em.add_field(name="Uploadé par", value=song.uploader)
            em.add_field(name="Vues", value=str(song.view_count))
            em.add_field(name="Durée", value=str(dur))
            em.set_footer(text=song.webpage_url)
            await self.bot.say(embed=em)
        else:
            await self.bot.say("Darude - Sandstorm.")

    @commands.command(pass_context=True, no_pm=True)
    async def stop(self, ctx):
        """Arrête toute musique en vocal."""
        server = ctx.message.server
        if self.is_playing(server):
            if ctx.message.author.voice_channel == server.me.voice_channel:
                if self.can_instaskip(ctx.message.author):
                    await self.bot.say('Arrêt...')
                    self._stop(server)
                else:
                    await self.bot.say("Impossible d'arrêter la musique si d'autres personnes sont sur le canal. Utilisez plutôt 'skip'")
            else:
                await self.bot.say("Vous avez besoin d'être sur le salon pour arrêter la musique.")
        else:
            await self.bot.say("Je ne joue rien.")

    @commands.command(name="yt", pass_context=True, no_pm=True)
    async def yt_search(self, ctx, *, search_terms: str):
        """Cherche et joue une musique depuis Youtube"""
        await self.bot.say("*Recherche...*")
        await ctx.invoke(self.play, url_or_search_terms=search_terms)

    async def reload_tickets(self):
        while self == self.bot.get_cog('Audio'):
            for u in self.surv["USERS"]:
                self.surv["USERS"][u]["TICKETS"] = self.surv["SYS"]["MAX_TICKETS"]
            dataIO.save_json('data/audio/surv.json', self.surv)
            await asyncio.sleep(60)

    def is_playing(self, server):
        if not self.voice_connected(server):
            return False
        if self.voice_client(server) is None:
            return False
        if not hasattr(self.voice_client(server), 'audio_player'):
            return False
        if self.voice_client(server).audio_player.is_done():
            return False
        return True

    async def cache_manager(self):
        while self == self.bot.get_cog("Audio"):
            if self._cache_too_large():
                # Our cache is too big, dumping
                log.debug("cache too large ({} > {}), dumping".format(
                    self._cache_size(), self._cache_max()))
                self._dump_cache()
            await asyncio.sleep(5)  # No need to run this every half second

    async def cache_scheduler(self):
        await asyncio.sleep(30)  # Extra careful

        self.bot.loop.create_task(self.cache_manager())

    def currently_downloading(self, server):
        if server.id in self.downloaders:
            if self.downloaders[server.id].is_alive():
                return True
        return False

    async def disconnect_timer(self):
        stop_times = {}
        while self == self.bot.get_cog('Audio'):
            for vc in self.bot.voice_clients:
                server = vc.server
                if not hasattr(vc, 'audio_player') and \
                        (server not in stop_times or
                         stop_times[server] is None):
                    log.debug("putting sid {} in stop loop, no player".format(
                        server.id))
                    stop_times[server] = int(time.time())

                if hasattr(vc, 'audio_player'):
                    if vc.audio_player.is_done():
                        if server not in stop_times or stop_times[server] is None:
                            log.debug("putting sid {} in stop loop".format(server.id))
                            stop_times[server] = int(time.time())

                    noppl_disconnect = self.get_server_settings(server)
                    noppl_disconnect = noppl_disconnect.get("NOPPL_DISCONNECT", True)
                    if noppl_disconnect and len(vc.channel.voice_members) == 1:
                        if server not in stop_times or stop_times[server] is None:
                            log.debug("putting sid {} in stop loop".format(server.id))
                            stop_times[server] = int(time.time())
                    elif not vc.audio_player.is_done():
                        stop_times[server] = None

            for server in stop_times:
                if stop_times[server] and \
                        int(time.time()) - stop_times[server] > 300:
                    # 5 min not playing to d/c
                    log.debug("dcing from sid {} after 300s".format(server.id))
                    self._clear_queue(server)
                    await self._stop_and_disconnect(server)
                    stop_times[server] = None
            await asyncio.sleep(5)

    def get_server_settings(self, server):
        try:
            sid = server.id
        except:
            sid = server

        if sid not in self.settings["SERVERS"]:
            self.settings["SERVERS"][sid] = {}
        ret = self.settings["SERVERS"][sid]

        # Not the cleanest way. Some refactoring is suggested if more settings
        # have to be added
        if "NOPPL_DISCONNECT" not in ret:
            ret["NOPPL_DISCONNECT"] = True

        for setting in self.server_specific_setting_keys:
            if setting not in ret:
                # Add the default
                ret[setting] = self.settings[setting]
                if setting.lower() == "volume" and ret[setting] <= 1:
                    ret[setting] *= 100
        # ^This will make it so that only users with an outdated config will
        # have their volume set * 100. In theory.
        self.save_settings()

        return ret

    def has_connect_perm(self, author, server):
        channel = author.voice_channel

        if channel:
            is_admin = channel.permissions_for(server.me).administrator
            if channel.user_limit == 0:
                is_full = False
            else:
                is_full = len(channel.voice_members) >= channel.user_limit

        if channel is None:
            raise AuthorNotConnected
        elif channel.permissions_for(server.me).connect is False:
            raise UnauthorizedConnect
        elif channel.permissions_for(server.me).speak is False:
            raise UnauthorizedSpeak
        elif is_full and not is_admin:
            raise ChannelUserLimit
        else:
            return True
        return False

    async def queue_manager(self, sid):
        """This function assumes that there's something in the queue for us to
            play"""
        server = self.bot.get_server(sid)
        max_length = self.settings["MAX_LENGTH"]

        # This is a reference, or should be at least
        temp_queue = self.queue[server.id]["TEMP_QUEUE"]
        queue = self.queue[server.id]["QUEUE"]
        repeat = self.queue[server.id]["REPEAT"]
        last_song = self.queue[server.id]["NOW_PLAYING"]

        assert temp_queue is self.queue[server.id]["TEMP_QUEUE"]
        assert queue is self.queue[server.id]["QUEUE"]

        # _play handles creating the voice_client and player for us

        if not self.is_playing(server):
            log.debug("not playing anything on sid {}".format(server.id) +
                      ", attempting to start a new song.")
            self.skip_votes[server.id] = []
            # Reset skip votes for each new song
            if len(temp_queue) > 0:
                # Fake queue for irdumb's temp playlist songs
                log.debug("calling _play because temp_queue is non-empty")
                try:
                    song = await self._play(sid, temp_queue.popleft())
                except MaximumLength:
                    return
            elif len(queue) > 0:  # We're in the normal queue
                url = queue.popleft()
                log.debug("calling _play on the normal queue")
                try:
                    song = await self._play(sid, url)
                except MaximumLength:
                    return
                if repeat and last_song:
                    queue.append(last_song.webpage_url)
            else:
                song = None
            self.queue[server.id]["NOW_PLAYING"] = song
            log.debug("set now_playing for sid {}".format(server.id))
            self.bot.loop.create_task(self._update_bot_status())

        elif server.id in self.downloaders:
            # We're playing but we might be able to download a new song
            curr_dl = self.downloaders.get(server.id)
            if len(temp_queue) > 0:
                next_dl = Downloader(temp_queue.peekleft(),
                                     max_length)
            elif len(queue) > 0:
                next_dl = Downloader(queue.peekleft(), max_length)
            else:
                next_dl = None

            if next_dl is not None:
                # Download next song
                next_dl.start()
                await self._download_next(server, curr_dl, next_dl)

    async def queue_scheduler(self):
        while self == self.bot.get_cog('Audio'):
            tasks = []
            queue = copy.deepcopy(self.queue)
            for sid in queue:
                if len(queue[sid]["QUEUE"]) == 0 and \
                        len(queue[sid]["TEMP_QUEUE"]) == 0:
                    continue
                # log.debug("scheduler found a non-empty queue"
                #           " for sid: {}".format(sid))
                tasks.append(
                    self.bot.loop.create_task(self.queue_manager(sid)))
            completed = [t.done() for t in tasks]
            while not all(completed):
                completed = [t.done() for t in tasks]
                await asyncio.sleep(0.5)
            await asyncio.sleep(1)

    async def reload_monitor(self):
        while self == self.bot.get_cog('Audio'):
            await asyncio.sleep(0.5)

        for vc in self.bot.voice_clients:
            try:
                vc.audio_player.stop()
            except:
                pass

    def save_settings(self):
        dataIO.save_json('data/audio/settings.json', self.settings)

    def set_server_setting(self, server, key, value):
        if server.id not in self.settings["SERVERS"]:
            self.settings["SERVERS"][server.id] = {}
        self.settings["SERVERS"][server.id][key] = value

    def voice_client(self, server):
        return self.bot.voice_client_in(server)

    def voice_connected(self, server):
        if self.bot.is_voice_connected(server):
            return True
        return False

    async def voice_state_update(self, before, after):
        server = after.server
        # Member objects
        if after.voice_channel != before.voice_channel:
            try:
                self.skip_votes[server.id].remove(after.id)
            except (ValueError, KeyError):
                pass
                # Either the server ID or member ID already isn't in there
        if after is None:
            return
        if server.id not in self.queue:
            return
        if after != server.me:
            return

        # Member is the bot

        if before.voice_channel != after.voice_channel:
            self._set_queue_channel(after.server, after.voice_channel)

        if before.mute != after.mute:
            vc = self.voice_client(server)
            if after.mute and vc.audio_player.is_playing():
                log.debug("Just got muted, pausing")
                vc.audio_player.pause()
            elif not after.mute and \
                    (not vc.audio_player.is_playing() and
                     not vc.audio_player.is_done()):
                log.debug("just got unmuted, resuming")
                vc.audio_player.resume()

    def __unload(self):
        for vc in self.bot.voice_clients:
            self.bot.loop.create_task(vc.disconnect())


def check_folders():
    folders = ("data/audio", "data/audio/cache", "data/audio/playlists",
               "data/audio/localtracks", "data/audio/sfx")
    for folder in folders:
        if not os.path.exists(folder):
            print("Creating " + folder + " folder...")
            os.makedirs(folder)


def check_files():
    default = {"VOLUME": 50, "MAX_LENGTH": 3700, "VOTE_ENABLED": True,
               "MAX_CACHE": 0, "SOUNDCLOUD_CLIENT_ID": None,
               "TITLE_STATUS": True, "AVCONV": False, "VOTE_THRESHOLD": 50,
               "SERVERS": {}}
    surv_def = {"SYS": {"MAX_TICKETS": 10, "PLAY_TICKETS": 1, "PLAYLIST_TICKETS": 5, "LIBERE_ROLE": "Habitué"}, "USERS": {}}
    settings_path = "data/audio/settings.json"
    user_path = "data/audio/surv.json"

    if not os.path.isfile(settings_path):
        print("Creating default audio settings.json...")
        dataIO.save_json(settings_path, default)
    else:  # consistency check
        try:
            current = dataIO.load_json(settings_path)
        except JSONDecodeError:
            # settings.json keeps getting corrupted for unknown reasons. Let's
            # try to keep it from making the cog load fail.
            dataIO.save_json(settings_path, default)
            current = dataIO.load_json(settings_path)
        if current.keys() != default.keys():
            for key in default.keys():
                if key not in current.keys():
                    current[key] = default[key]
                    print(
                        "Adding " + str(key) + " field to audio settings.json")
            dataIO.save_json(settings_path, current)

    if not os.path.isfile(user_path):
        print("Création des réglages utilisateur...")
        dataIO.save_json(user_path, surv_def)

def verify_ffmpeg_avconv():
    try:
        subprocess.call(["ffmpeg", "-version"], stdout=subprocess.DEVNULL)
    except FileNotFoundError:
        pass
    else:
        return "ffmpeg"

    try:
        subprocess.call(["avconv", "-version"], stdout=subprocess.DEVNULL)
    except FileNotFoundError:
        return False
    else:
        return "avconv"

def setup(bot):
    check_folders()
    check_files()

    if youtube_dl is None:
        raise RuntimeError("You need to run `pip3 install youtube_dl`")
    if opus is False:
        raise RuntimeError(
            "Your opus library's bitness must match your python installation's"
            " bitness. They both must be either 32bit or 64bit.")
    elif opus is None:
        raise RuntimeError(
            "You need to install ffmpeg and opus. See \"https://github.com/"
            "Twentysix26/Red-DiscordBot/wiki/Requirements\"")

    player = verify_ffmpeg_avconv()

    if not player:
        if os.name == "nt":
            msg = "ffmpeg isn't installed"
        else:
            msg = "Neither ffmpeg nor avconv are installed"
        raise RuntimeError(
          "{}.\nConsult the guide for your operating system "
          "and do ALL the steps in order.\n"
          "https://twentysix26.github.io/Red-Docs/\n"
          "".format(msg))

    n = Audio(bot, player=player)  # Praise 26
    bot.add_cog(n)
    bot.add_listener(n.voice_state_update, 'on_voice_state_update')
    bot.loop.create_task(n.queue_scheduler())
    bot.loop.create_task(n.disconnect_timer())
    bot.loop.create_task(n.reload_monitor())
    bot.loop.create_task(n.cache_scheduler())
    bot.loop.create_task(n.reload_tickets())