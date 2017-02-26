import asyncio
import glob
import os
import os.path
import re
from copy import deepcopy
from typing import List

import aiohttp
import discord
from discord.ext import commands

from .utils.dataIO import dataIO
from .utils import checks, chat_formatting as cf

default_volume = 25

class Horn:
    """Comme pour les stickers mais en plus bruyant..."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.audio_players = {}
        self.sound_base = "data/playsound"
        self.sys = dataIO.load_json("data/playsound/sys.json")

        self.settings_path = "data/playsound/settings.json"
        self.settings = dataIO.load_json(self.settings_path)

    async def lecture(self, message):
        server = message.server
        channel = message.channel
        if self.sys["ACTIVE"] == True:
            if ":" in message.content:
                output = re.compile(':(.*?):', re.DOTALL |  re.IGNORECASE).findall(message.content)
                if output:
                    for cast in output:
                        if cast in self.settings[server.id]:
                            soundname = cast #Conversion TYPIQUE DU BORDELIQUE
                            if "volume" in self.settings[server.id][cast]:
                                vol = self.settings[server.id][soundname]["volume"]
                            else:
                                vol = default_volume
                                self.settings[server.id][soundname]["volume"] = vol
                                dataIO.save_json(self.settings_path, self.settings)

                            prefix = self.sys["PREFIX"]
                            new_message = deepcopy(message)
                            new_message.content = prefix + "cast" + " " + soundname
                            await self.bot.process_commands(new_message)
                            return


    def voice_channel_full(self, voice_channel: discord.Channel) -> bool:
        return (voice_channel.user_limit != 0 and
                len(voice_channel.voice_members) >= voice_channel.user_limit)

    def list_sounds(self, server_id: str) -> List[str]:
        return sorted(
            [os.path.splitext(s)[0] for s in os.listdir(os.path.join(
                self.sound_base, server_id))],
            key=lambda s: s.lower())

    def voice_connected(self, server: discord.Server) -> bool:
        return self.bot.is_voice_connected(server)

    def voice_client(self, server: discord.Server) -> discord.VoiceClient:
        return self.bot.voice_client_in(server)

    async def _join_voice_channel(self, ctx: commands.Context):
        channel = ctx.message.author.voice_channel
        if channel:
            await self.bot.join_voice_channel(channel)

    async def _leave_voice_channel(self, server: discord.Server):
        if not self.voice_connected(server):
            return
        voice_client = self.voice_client(server)

        if server.id in self.audio_players:
            self.audio_players[server.id].stop()
        await voice_client.disconnect()

    async def wait_for_disconnect(self, server: discord.Server):
        while not self.audio_players[server.id].is_done():
            await asyncio.sleep(0.01)
        await self._leave_voice_channel(server)

    async def sound_init(self, ctx: commands.Context, path: str, vol: int):
        server = ctx.message.server
        options = "-filter \"volume=volume={}\"".format(str(vol/100))
        voice_client = self.voice_client(server)
        self.audio_players[server.id] = voice_client.create_ffmpeg_player(
            path, options=options)

    async def sound_play(self, ctx: commands.Context, p: str, vol: int):
        server = ctx.message.server
        if not ctx.message.author.voice_channel:
            await self.bot.reply(
                "Vous avez besoin de rejoindre un channel audio.")
            return

        if self.voice_channel_full(ctx.message.author.voice_channel):
            return

        if not ctx.message.channel.is_private:
            if self.voice_connected(server):
                if server.id not in self.audio_players:
                    await self.sound_init(ctx, p, vol)
                    self.audio_players[server.id].start()
                    await self.wait_for_disconnect(server)
                else:
                    if self.audio_players[server.id].is_playing():
                        self.audio_players[server.id].stop()
                    await self.sound_init(ctx, p, vol)
                    self.audio_players[server.id].start()
                    await self.wait_for_disconnect(server)
            else:
                await self._join_voice_channel(ctx)
                if server.id not in self.audio_players:
                    await self.sound_init(ctx, p, vol)
                    self.audio_players[server.id].start()
                    await self.wait_for_disconnect(server)
                else:
                    if self.audio_players[server.id].is_playing():
                        self.audio_players[server.id].stop()
                    await self.sound_init(ctx, p, vol)
                    self.audio_players[server.id].start()
                    await self.wait_for_disconnect(server)

    @commands.command(pass_context=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def castactive(self, ctx):
        """Permet d'activer/désactiver les casts auto."""
        if "ACTIVE" not in self.sys:
            self.sys = {"PREFIX": ctx.prefix, "ACTIVE": False}
            dataIO.save_json("data/playsound/sys.json", self.sys)
        if self.sys["ACTIVE"] is True:
            self.sys["ACTIVE"] = False
            dataIO.save_json("data/playsound/sys.json", self.sys)
            await self.bot.say("Désactivé")
        else:
            self.sys["ACTIVE"] = True
            dataIO.save_json("data/playsound/sys.json", self.sys)
            await self.bot.say("Activé")

    @commands.command(no_pm=True, pass_context=True, name="cast")
    async def _cast(self, ctx: commands.Context, soundname: str):
        """Joue un fichier audio local."""

        server = ctx.message.server
        self.sys["PREFIX"] = ctx.prefix

        if server.id not in os.listdir(self.sound_base):
            os.makedirs(os.path.join(self.sound_base, server.id))

        if server.id not in self.settings:
            self.settings[server.id] = {}
            dataIO.save_json(self.settings_path, self.settings)

        f = glob.glob(os.path.join(
            self.sound_base, server.id, soundname + ".*"))
        if len(f) < 1:
            await self.bot.reply(
                "Fichier introuvable. Essayez `{}allcast` pour une liste.".format(
                    ctx.prefix))
            return
        elif len(f) > 1:
            await self.bot.reply(
                "Il y a {} fichiers avec le même nom. Faîtes en sorte que ce ne soit pas le cas".format(len(f)))
            return

        soundname = os.path.splitext(os.path.basename(f[0]))[0]
        if soundname in self.settings[server.id]:
            if "volume" in self.settings[server.id][soundname]:
                vol = self.settings[server.id][soundname]["volume"]
            else:
                vol = default_volume
                self.settings[server.id][soundname]["volume"] = vol
                dataIO.save_json(self.settings_path, self.settings)
        else:
            vol = default_volume
            self.settings[server.id][soundname] = {"volume": vol}
            dataIO.save_json(self.settings_path, self.settings)

        await self.sound_play(ctx, f[0], vol)

    @commands.command(pass_context=True, name="allcast")
    async def _allcast(self, ctx: commands.Context):
        """Envoie une liste de tous les sons en MP."""

        await self.bot.type()

        server = ctx.message.server
        self.sys["PREFIX"] = ctx.prefix

        if server.id not in os.listdir(self.sound_base):
            os.makedirs(os.path.join(self.sound_base, server.id))

        if server.id not in self.settings:
            self.settings[server.id] = {}
            dataIO.save_json(self.settings_path, self.settings)

        strbuffer = self.list_sounds(server.id)

        if len(strbuffer) == 0:
            await self.bot.reply(
                "Aucun cast trouvé. Utilisez `{}addcast` pour en ajouter un.".format(
                    ctx.prefix))
            return

        mess = "```"
        for line in strbuffer:
            if len(mess) + len(line) + 4 < 2000:
                mess += "\n" + line
            else:
                mess += "```"
                await self.bot.whisper(mess)
                mess = "```" + line
        if mess != "":
            mess += "```"
            await self.bot.whisper(mess)

    @commands.command(no_pm=True, pass_context=True, name="addcast")
    @checks.mod_or_permissions(administrator=True)
    async def _addcast(self, ctx: commands.Context, link: str=None):
        """Ajoute un nouveau son

        Uploadez un document et mettez en commentaire [p]addsound ou utilisez un URL direct
        """

        await self.bot.type()

        server = ctx.message.server
        self.sys["PREFIX"] = ctx.prefix

        if server.id not in os.listdir(self.sound_base):
            os.makedirs(os.path.join(self.sound_base, server.id))

        if server.id not in self.settings:
            self.settings[server.id] = {}
            dataIO.save_json(self.settings_path, self.settings)

        attach = ctx.message.attachments
        if len(attach) > 1 or (attach and link):
            await self.bot.reply("Ajoutez qu'un seul cast en même temps.")
            return

        url = ""
        filename = ""
        if attach:
            a = attach[0]
            url = a["url"]
            filename = a["filename"]
        elif link:
            url = "".join(link)
            filename = os.path.basename(
                "_".join(url.split()).replace("%20", "_"))
        else:
            await self.bot.reply("Vous devez fournir un fichier ou un URL direct.")
            return

        filepath = os.path.join(self.sound_base, server.id, filename)

        if os.path.splitext(filename)[0] in self.list_sounds(server.id):
            await self.bot.reply("Un cast sous ce nom existe déjà"
                         " Changez le nom du fichier et reessayez...")
            return

        async with aiohttp.get(url) as new_sound:
            f = open(filepath, "wb")
            f.write(await new_sound.read())
            f.close()

        self.settings[server.id][
            os.path.splitext(filename)[0]] = {"volume": default_volume}
        dataIO.save_json(self.settings_path, self.settings)

        await self.bot.reply(
            "Cast {} ajouté.".format(os.path.splitext(filename)[0]))

    @commands.command(no_pm=True, pass_context=True, name="castvol")
    @checks.mod_or_permissions(administrator=True)
    async def _soundvol(self, ctx: commands.Context, soundname: str,
                        percent: int=None):
        """Change le volume pour le cast spécifié.

        Si aucun pourcentage n'est donné, renvoie sa valeur présente.
        """

        await self.bot.type()

        server = ctx.message.server

        if server.id not in os.listdir(self.sound_base):
            os.makedirs(os.path.join(self.sound_base, server.id))

        if server.id not in self.settings:
            self.settings[server.id] = {}
            dataIO.save_json(self.settings_path, self.settings)

        f = glob.glob(os.path.join(self.sound_base, server.id,
                                   soundname + ".*"))
        if len(f) < 1:
            await self.bot.say(
                "Fichier non trouvé. Essayez `{}allcast` pour une liste.".format(
                    ctx.prefix))
            return
        elif len(f) > 1:
            await self.bot.say(
                "Plusieurs fichiers ont le même nom ({}), faîtes en sorte que ce ne soit plus le cas".format(len(f)))
            return

        if soundname not in self.settings[server.id]:
            self.settings[server.id][soundname] = {"volume": default_volume}
            dataIO.save_json(self.settings_path, self.settings)

        if percent is None:
            await self.bot.reply("Le volume pour {} est {}.".format(
                soundname, self.settings[server.id][soundname]["volume"]))
            return

        self.settings[server.id][soundname]["volume"] = percent
        dataIO.save_json(self.settings_path, self.settings)

        await self.bot.reply("Volume pour {} reglé à {}.".format(soundname,
                                                               percent))

    @commands.command(no_pm=True, pass_context=True, name="delcast")
    @checks.mod_or_permissions(administrator=True)
    async def _delsound(self, ctx: commands.Context, soundname: str):
        """Supprime un cast"""

        await self.bot.type()

        server = ctx.message.server

        if server.id not in os.listdir(self.sound_base):
            os.makedirs(os.path.join(self.sound_base, server.id))

        f = glob.glob(os.path.join(self.sound_base, server.id,
                                   soundname + ".*"))
        if len(f) < 1:
            await self.bot.say(
                "Fichier non trouvé. Essayez `{}allcast` pour une liste.".format(
                    ctx.prefix))
            return
        elif len(f) > 1:
            await self.bot.say(
                "Plusieurs fichiers ont le même nom ({}), faîtes en sorte que ce ne soit plus le cas".format(len(f)))
            return

        os.remove(f[0])

        if soundname in self.settings[server.id]:
            del self.settings[server.id][soundname]
            dataIO.save_json(self.settings_path, self.settings)

        await self.bot.reply("Cast {} supprimé.".format(soundname))

    @commands.command(no_pm=True, pass_context=True, name="getcast")
    async def _getsound(self, ctx: commands.Context, soundname: str):
        """Renvoie le cast spécifié."""

        await self.bot.type()

        server = ctx.message.server

        if server.id not in os.listdir(self.sound_base):
            os.makedirs(os.path.join(self.sound_base, server.id))

        f = glob.glob(os.path.join(self.sound_base, server.id,
                                   soundname + ".*"))

        if len(f) < 1:
            await self.bot.say(
                "Fichier introuvable. Essayez `{}allcast` pour une liste.".format(
                    ctx.prefix))
            return
        elif len(f) > 1:
            await self.bot.say(
                "Plusieurs fichiers ont le même nom ({}), faîtes en sorte que ce ne soit plus le cas".format(len(f)))
            return

        await self.bot.upload(f[0])


def check_folders():
    if not os.path.exists("data/playsound"):
        print("Creating data/playsound directory...")
        os.makedirs("data/playsound")

    if not os.path.exists("data/horn"):
        print("Création de data/horn...")
        os.makedirs("data/horn")

def check_files():
    f = "data/playsound/settings.json"
    if not dataIO.is_valid_json(f):
        print("Creating data/playsound/settings.json...")
        dataIO.save_json(f, {})

    f = "data/playsound/sys.json"
    if not dataIO.is_valid_json(f):
        print("Création de playsound/sys.json...")
        dataIO.save_json(f, {})

def setup(bot: commands.Bot):
    check_folders()
    check_files()
    bot.add_listener(Horn(bot).lecture, "on_message")
    bot.add_cog(Horn(bot))