import discord
from discord.ext import commands
from cogs.utils import checks
from __main__ import set_cog, send_cmd_help, settings
from .utils.dataIO import dataIO
from .utils.chat_formatting import pagify, box

import importlib
import traceback
import logging
import asyncio
import threading
import datetime
import glob
import os
import time
import aiohttp

log = logging.getLogger("red.owner")


class CogNotFoundError(Exception):
    pass


class CogLoadError(Exception):
    pass


class NoSetupError(CogLoadError):
    pass


class CogUnloadError(Exception):
    pass


class OwnerUnloadWithoutReloadError(CogUnloadError):
    pass


class Owner:
    """Operations réservés à l'utilisateur.
    """

    def __init__(self, bot):
        self.bot = bot
        self.setowner_lock = False
        self.file_path = "data/red/disabled_commands.json"
        self.disabled_commands = dataIO.load_json(self.file_path)
        self.session = aiohttp.ClientSession(loop=self.bot.loop)

    def __unload(self):
        self.session.close()

    @commands.command()
    @checks.mod_or_permissions(administrator=True)
    async def load(self, *, module: str):
        """Charge un module"""
        module = module.strip()
        if "cogs." not in module:
            module = "cogs." + module
        try:
            self._load_cog(module)
        except CogNotFoundError:
            await self.bot.say("Module introuvable.")
        except CogLoadError as e:
            log.exception(e)
            traceback.print_exc()
            await self.bot.say("Impossible de charger le module. Plus d'infos sur le terminal.\n"
                               "Erreur: `{}`".format(e.args[0]))
        except Exception as e:
            log.exception(e)
            traceback.print_exc()
            await self.bot.say('Module chargé mais une chose cloche. Regardez le terminal pour plus d\'infos.\n'
                               'Erreur: `{}`'.format(e.args[0]))
        else:
            set_cog(module, True)
            await self.disable_commands()
            await self.bot.say("Module activé.")

    @commands.group(invoke_without_command=True)
    @checks.mod_or_permissions(administrator=True)
    async def unload(self, *, module: str):
        """Décharge un module"""
        module = module.strip()
        if "cogs." not in module:
            module = "cogs." + module
        if not self._does_cogfile_exist(module):
            await self.bot.say("Ce module est introuvable.")
        else:
            set_cog(module, False)
        try:  # No matter what we should try to unload it
            self._unload_cog(module)
        except OwnerUnloadWithoutReloadError:
            await self.bot.say("*Je ne peux pas vous autoriser à faire ça...*\n*C'est une très mauvaise idée...*\n*Ne faîtes pas ça...*\nJe vous en prie...*")
        except CogUnloadError as e:
            log.exception(e)
            traceback.print_exc()
            await self.bot.say('Module non désactivable.')
        else:
            await self.bot.say("Module désactivé.")

    @unload.command(name="all")
    @checks.is_owner()
    async def unload_all(self):
        """Décharge l'ensemble des modules (Sauf Owner)"""
        cogs = self._list_cogs()
        still_loaded = []
        for cog in cogs:
            set_cog(cog, False)
            try:
                self._unload_cog(cog)
            except OwnerUnloadWithoutReloadError:
                pass
            except CogUnloadError as e:
                log.exception(e)
                traceback.print_exc()
                still_loaded.append(cog)
        if still_loaded:
            still_loaded = ", ".join(still_loaded)
            await self.bot.say("Quelques modules n'ont pas été déchargés: "
                "{}".format(still_loaded))
        else:
            await self.bot.say("Déchargés...")

    @checks.mod_or_permissions(administrator=True)
    @commands.command(name="reload")
    async def _reload(self, module):
        """Recharge un module"""
        if "cogs." not in module:
            module = "cogs." + module

        try:
            self._unload_cog(module, reloading=True)
        except:
            pass

        try:
            self._load_cog(module)
        except CogNotFoundError:
            await self.bot.say("Introuvable.")
        except NoSetupError:
            await self.bot.say("Le module n'a pas de fonction de paramétrages.")
        except CogLoadError as e:
            log.exception(e)
            traceback.print_exc()
            await self.bot.say("Impossible de le recharger.\n"
                               "Erreur: `{}`".format(e.args[0]))
        else:
            set_cog(module, True)
            await self.disable_commands()
            await self.bot.say("Module rechargé.")

    @commands.command(pass_context=True, hidden=True)
    @checks.mod_or_permissions(administrator=True)
    async def debug(self, ctx, *, code):
        """Evalue un code"""
        code = code.strip('` ')
        result = None

        global_vars = globals().copy()
        global_vars['bot'] = self.bot
        global_vars['ctx'] = ctx
        global_vars['message'] = ctx.message
        global_vars['author'] = ctx.message.author
        global_vars['channel'] = ctx.message.channel
        global_vars['server'] = ctx.message.server

        try:
            result = eval(code, global_vars, locals())
        except Exception as e:
            await self.bot.say(box('{}: {}'.format(type(e).__name__, str(e)),
                                   lang="py"))
            return

        if asyncio.iscoroutine(result):
            result = await result

        result = str(result)

        if not ctx.message.channel.is_private:
            censor = (settings.email, settings.password)
            r = "[EXPUNGED]"
            for w in censor:
                if w != "":
                    result = result.replace(w, r)
                    result = result.replace(w.lower(), r)
                    result = result.replace(w.upper(), r)
        for page in pagify(result, shorten_by=12):
            await self.bot.say(box(page, lang="py"))

    @commands.group(name="set", pass_context=True)
    async def _set(self, ctx):
        """Change les réglages de Plume."""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)
            return

    @_set.command(pass_context=True)
    async def owner(self, ctx):
        """Sets owner"""
        if self.setowner_lock:
            await self.bot.say("Propriétaire déjà reglé.")
            return

        if settings.owner != "id_here":
            await self.bot.say(
            "Il y a déjà un propriétaire. Rapellez-vous que mettre quelqu'un d'autre propriétaire que l'hébergeur pose de réels problèmes au niveau du bot."
            )
            await asyncio.sleep(3)

        await self.bot.say("Confirmez dans le terminal que vous êtes le propriétaire.")
        self.setowner_lock = True
        t = threading.Thread(target=self._wait_for_answer,
                             args=(ctx.message.author,))
        t.start()

    @_set.command(pass_context=True)
    @checks.is_owner()
    async def prefix(self, ctx, *prefixes):
        """Change le(s) préfixe(s) utilisé(s) pour appeller le bot"""
        if prefixes == ():
            await send_cmd_help(ctx)
            return

        self.bot.command_prefix = sorted(prefixes, reverse=True)
        settings.prefixes = sorted(prefixes, reverse=True)
        log.debug("Changés en:\n\t{}".format(settings.prefixes))

        if len(prefixes) > 1:
            await self.bot.say("Changé")
        else:
            await self.bot.say("Changé")

    @_set.command(pass_context=True)
    @checks.is_owner()
    async def name(self, ctx, *, name):
        """Change le nom d'Plume"""
        name = name.strip()
        if name != "":
            try:
                await self.bot.edit_profile(settings.password, username=name)
            except:
                await self.bot.say("Impossible de changer le nom. Vous l'avez peut être fait trop souvent.\nUtilisez plutôt {}set nickname.".format(ctx.prefix))
            else:
                await self.bot.say("Fait.")
        else:
            await send_cmd_help(ctx)

    @_set.command(pass_context=True, no_pm=True)
    @checks.is_owner()
    async def nickname(self, ctx, *, nickname=""):
        """Change le surnom du bot."""
        nickname = nickname.strip()
        if nickname == "":
            nickname = None
        try:
            await self.bot.change_nickname(ctx.message.server.me, nickname)
            await self.bot.say("Fait.")
        except discord.Forbidden:
            await self.bot.say("Je n'ai pas les permissions pour le faire.")

    @_set.command(pass_context=True)
    @checks.is_owner()
    async def game(self, ctx, *, game=None):
        """Change le nom du jeu joué par le bot."""

        server = ctx.message.server

        current_status = server.me.status if server is not None else None

        if game:
            game = game.strip()
            await self.bot.change_presence(game=discord.Game(name=game),
                                           status=current_status)
            log.debug('Status changé en "{}"'.format(game))
        else:
            await self.bot.change_presence(game=None, status=current_status)
            log.debug('Status reset')
        await self.bot.say("Fait.")

    @_set.command(pass_context=True)
    @checks.is_owner()
    async def status(self, ctx, *, status=None):
        """Change le status du bot

        Status disponibles:
            online
            idle
            dnd
            invisible"""

        statuses = {
                    "online"    : discord.Status.online,
                    "idle"      : discord.Status.idle,
                    "dnd"       : discord.Status.dnd,
                    "invisible" : discord.Status.invisible
                   }

        server = ctx.message.server

        current_game = server.me.game if server is not None else None

        if status is None:
            await self.bot.change_presence(status=discord.Status.online,
                                           game=current_game)
            await self.bot.say("Status reset.")
        else:
            status = statuses.get(status.lower(), None)
            if status:
                await self.bot.change_presence(status=status,
                                               game=current_game)
                await self.bot.say("Status changé.")
            else:
                await send_cmd_help(ctx)

    @_set.command(pass_context=True)
    @checks.is_owner()
    async def stream(self, ctx, streamer=None, *, stream_title=None):
        """Change le status du stream du bot

        Laisser les champs vide désactive cette fonction."""

        server = ctx.message.server

        current_status = server.me.status if server is not None else None

        if stream_title:
            stream_title = stream_title.strip()
            if "twitch.tv/" not in streamer:
                streamer = "https://www.twitch.tv/" + streamer
            game = discord.Game(type=1, url=streamer, name=stream_title)
            await self.bot.change_presence(game=game, status=current_status)
            log.debug('Le propriétaire a reglé un stream pour "{}" et {}'.format(stream_title, streamer))
        elif streamer is not None:
            await send_cmd_help(ctx)
            return
        else:
            await self.bot.change_presence(game=None, status=current_status)
            log.debug('Stream Vidé')
        await self.bot.say("Fait.")

    @_set.command()
    @checks.is_owner()
    async def avatar(self, url):
        """Change l'avatat du bot."""
        try:
            async with self.session.get(url) as r:
                data = await r.read()
            await self.bot.edit_profile(settings.password, avatar=data)
            await self.bot.say("Fait.")
            log.debug("avatar changé")
        except Exception as e:
            await self.bot.say("Erreur, regardez le terminal...")
            log.exception(e)
            traceback.print_exc()

    @_set.command(name="token")
    @checks.mod_or_permissions(administrator=True)
    async def _token(self, token):
        """Change le token de connexion"""
        if len(token) < 50:
            await self.bot.say("Token invalide.")
        else:
            settings.login_type = "token"
            settings.email = token
            settings.password = ""
            await self.bot.say("Token changé, rechargez-moi.")
            log.debug("Token changé.")

    @commands.command()
    @checks.mod_or_permissions(administrator=True)
    async def shutdown(self):
        """Redémarre le bot"""
        await self.bot.logout()

    @commands.group(name="command", pass_context=True)
    @checks.mod_or_permissions(administrator=True)
    async def command_disabler(self, ctx):
        """Désactive une commande"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)
            if self.disabled_commands:
                msg = "Commandes désactivés:\n```xl\n"
                for cmd in self.disabled_commands:
                    msg += "{}, ".format(cmd)
                msg = msg.strip(", ")
                await self.bot.whisper("{}```".format(msg))

    @command_disabler.command()
    async def disable(self, *, command):
        """Désactiver une commande."""
        comm_obj = await self.get_command(command)
        if comm_obj is KeyError:
            await self.bot.say("Cette commande n'existe pas.")
        elif comm_obj is False:
            await self.bot.say("Vous ne pouvez pas vous bloquer vous-même.")
        else:
            comm_obj.enabled = False
            comm_obj.hidden = True
            self.disabled_commands.append(command)
            dataIO.save_json(self.file_path, self.disabled_commands)
            await self.bot.say("Commande désactivée.")

    @command_disabler.command()
    async def enable(self, *, command):
        """Active une commande"""
        if command in self.disabled_commands:
            self.disabled_commands.remove(command)
            dataIO.save_json(self.file_path, self.disabled_commands)
            await self.bot.say("Commande activée.")
        else:
            await self.bot.say("Cette commande n'est pas désactivée.")
            return
        try:
            comm_obj = await self.get_command(command)
            comm_obj.enabled = True
            comm_obj.hidden = False
        except:  # In case it was in the disabled list but not currently loaded
            pass # No point in even checking what returns

    async def get_command(self, command):
        command = command.split()
        try:
            comm_obj = self.bot.commands[command[0]]
            if len(command) > 1:
                command.pop(0)
                for cmd in command:
                    comm_obj = comm_obj.commands[cmd]
        except KeyError:
            return KeyError
        for check in comm_obj.checks:
            if hasattr(check, "__name__") and check.__name__ == "is_owner_check":
                return False
        return comm_obj

    async def disable_commands(self): # runs at boot
        for cmd in self.disabled_commands:
            cmd_obj = await self.get_command(cmd)
            try:
                cmd_obj.enabled = False
                cmd_obj.hidden = True
            except:
                pass

    @commands.command()
    @checks.is_owner()
    async def join(self, invite_url: discord.Invite=None):
        """Permet de rejoindre un nouveau serveur."""
        if hasattr(self.bot.user, 'bot') and self.bot.user.bot is True:
            # Check to ensure they're using updated discord.py
            msg = ("J'ai un tag 'BOT', qui m'oblige à utiliser OAuth2."
                   "\nPour plus d'infos: "
                   "https://twentysix26.github.io/"
                   "Red-Docs/red_guide_bot_accounts/#bot-invites")
            await self.bot.say(msg)
            if hasattr(self.bot, 'oauth_url'):
                await self.bot.whisper("Voilà mon lien OAuth2:\n{}".format(
                    self.bot.oauth_url))
            return

        if invite_url is None:
            await self.bot.say("J'ai besoin d'une invitation Discord...")
            return

        try:
            await self.bot.accept_invite(invite_url)
            await self.bot.say("Server rejoint.")
            log.debug("J'ai rejoint {}".format(invite_url))
        except discord.NotFound:
            await self.bot.say("Invitation expirée.")
        except discord.HTTPException:
            await self.bot.say("Je n'ai pas pu accepter l'invitation.")

    @commands.command(pass_context=True, no_pm=True)
    @checks.is_owner()
    async def leave(self, ctx):
        """Quitte le serveur"""
        message = ctx.message

        await self.bot.say("Êtes-vous sur de vouloir me faire quitter le serveur ? Tapez 'yes' pour me faire partir.")
        response = await self.bot.wait_for_message(author=message.author)

        if response.content.lower().strip() == "yes":
            await self.bot.say("Okay. Bye :wave:")
            log.debug('Quitte "{}"'.format(message.server.name))
            await self.bot.leave_server(message.server)
        else:
            await self.bot.say("D'accord, je reste.")

    @commands.command(pass_context=True)
    @checks.is_owner()
    async def servers(self, ctx):
        """Liste des serveurs connectés"""
        owner = ctx.message.author
        servers = sorted(list(self.bot.servers),
                         key=lambda s: s.name.lower())
        msg = ""
        for i, server in enumerate(servers):
            msg += "{}: {}\n".format(i, server.name)
        msg += "\nPour quitter un serveur tapez son chiffre."

        for page in pagify(msg, ['\n']):
            await self.bot.say(page)

        while msg is not None:
            msg = await self.bot.wait_for_message(author=owner, timeout=15)
            try:
                msg = int(msg.content)
                await self.leave_confirmation(servers[msg], owner, ctx)
                break
            except (IndexError, ValueError, AttributeError):
                pass

    async def leave_confirmation(self, server, owner, ctx):
        await self.bot.say("Êtes-vous sûr de vouloir quitter le serveur {}? (yes/no)".format(server.name))

        msg = await self.bot.wait_for_message(author=owner, timeout=15)

        if msg is None:
            await self.bot.say("Je ne crois pas.")
        elif msg.content.lower().strip() in ("yes", "y"):
            await self.bot.leave_server(server)
            if server != ctx.message.server:
                await self.bot.say("Fait.")
        else:
            await self.bot.say("Ok :wave:.")

    @commands.command(pass_context=True)
    async def contact(self, ctx, *, message : str):
        """Permet l'envoie d'un MP au propriétaire"""
        if settings.owner == "id_here":
            await self.bot.say("Aucun propriétaire reglé.")
            return
        owner = discord.utils.get(self.bot.get_all_members(), id=settings.owner)
        author = ctx.message.author
        if ctx.message.channel.is_private is False:
            server = ctx.message.server
            source = ", serveur **{}** ({})".format(server.name, server.id)
        else:
            source = ", message privé"
        sender = "De **{}** ({}){}:\n\n".format(author, author.id, source)
        message = sender + message
        try:
            await self.bot.send_message(owner, message)
        except discord.errors.InvalidArgument:
            await self.bot.say("Je n'ai pas pu trouver mon propriétaire *hum*")
        except discord.errors.HTTPException:
            await self.bot.say("Message trop long.")
        except:
            await self.bot.say("Votre message ne passe pas dans la boite aux lettres...")
        else:
            await self.bot.say("Message envoyé.")

    @commands.command()
    async def info(self):
        """Montre des informations à propos du bot"""
        author_repo = "https://github.com/GitAcrown"
        red_repo = author_repo + "/Plume"
        server_url = "https://discord.gg/veqrFX8"
        dpy_repo = "https://github.com/Rapptz/discord.py"
        python_url = "https://www.python.org/"
        since = datetime.datetime(2016, 4, 26, 0, 0)
        days_since = (datetime.datetime.now() - since).days
        dpy_version = "[{}]({})".format(discord.__version__, dpy_repo)
        py_version = "[{}.{}.{}]({})".format(*os.sys.version_info[:3],
                                             python_url)

        owner = settings.owner if settings.owner != "id_here" else None
        if owner:
            owner = discord.utils.get(self.bot.get_all_members(), id=owner)
            if not owner:
                try:
                    owner = await self.bot.get_user_info(settings.owner)
                except:
                    owner = None
        if not owner:
            owner = "Inconnu"

        about = (
            "Session de [Plume, un bot pour Discord]({}) "
            "créé par [Acrown]({}) et adapté partiellement de Red.\n\n"
            "Ce bot a été originellement créé pour un serveur en particulier. [Rejoignez-nous !]({})\n"
            "".format(red_repo, author_repo, server_url))

        embed = discord.Embed(colour=discord.Colour.blue())
        embed.add_field(name="Session par", value=str(owner))
        embed.add_field(name="Python", value=py_version)
        embed.add_field(name="discord.py", value=dpy_version)
        embed.add_field(name="A propos de Plume", value=about, inline=False)
        embed.set_footer(text="Apporte de la joie depuis le 26 Avril 2016 ("
                         "{} jours d'existence!)".format(days_since))

        try:
            await self.bot.say(embed=embed)
        except discord.HTTPException:
            await self.bot.say("J'ai besoin des liens intrégrés pour poster ça.")

    @commands.command()
    async def uptime(self):
        """Montre le nombre d'heures depuis le lancement de la session."""
        now = datetime.datetime.now()
        uptime = (now - self.bot.uptime).seconds
        uptime = datetime.timedelta(seconds=uptime)
        await self.bot.say("`Uptime: {}`".format(uptime))

    @commands.command()
    async def version(self):
        """Montre la dernière version du bot."""
        response = self.bot.loop.run_in_executor(None, self._get_version)
        result = await asyncio.wait_for(response, timeout=10)
        try:
            await self.bot.say(embed=result)
        except discord.HTTPException:
            await self.bot.say("J'ai besoin d'avoir l'accès aux liens.")

    def _load_cog(self, cogname):
        if not self._does_cogfile_exist(cogname):
            raise CogNotFoundError(cogname)
        try:
            mod_obj = importlib.import_module(cogname)
            importlib.reload(mod_obj)
            self.bot.load_extension(mod_obj.__name__)
        except SyntaxError as e:
            raise CogLoadError(*e.args)
        except:
            raise

    def _unload_cog(self, cogname, reloading=False):
        if not reloading and cogname == "cogs.owner":
            raise OwnerUnloadWithoutReloadError(
                "Impossible de décharger le module Owner")
        try:
            self.bot.unload_extension(cogname)
        except:
            raise CogUnloadError

    def _list_cogs(self):
        cogs = [os.path.basename(f) for f in glob.glob("cogs/*.py")]
        return ["cogs." + os.path.splitext(f)[0] for f in cogs]

    def _does_cogfile_exist(self, module):
        if "cogs." not in module:
            module = "cogs." + module
        if module not in self._list_cogs():
            return False
        return True

    def _wait_for_answer(self, author):
        print(author.name + " a demandé à être propriétaire. Si c'est vous, "
              "tapez 'yes'. Sinon appuyez sur Entrer.")

        choice = "None"
        while choice.lower() != "yes" and choice == "None":
            choice = input("> ")

        if choice == "yes":
            settings.owner = author.id
            print(author.name + " est maintenant propriétaire.")
            self.setowner_lock = False
            self.owner.hidden = True
        else:
            print("Requête ignorée.")
            self.setowner_lock = False

    def _get_version(self):
        url = os.popen(r'git config --get remote.origin.url')
        url = url.read().strip()[:-4]
        repo_name = url.split("/")[-1]
        commits = os.popen(r'git show -s -n 3 HEAD --format="%cr|%s|%H"')
        ncommits = os.popen(r'git rev-list --count HEAD').read()

        lines = commits.read().split('\n')
        embed = discord.Embed(title="Mise à jour " + repo_name,
                              description="Dernières MAJ ",
                              colour=discord.Colour.red(),
                              url=url)
        for line in lines:
            if not line:
                continue
            when, commit, chash = line.split("|")
            commit_url = url + "/commit/" + chash
            content = "[{}]({}) - {} ".format(chash[:6], commit_url, commit)
            embed.add_field(name=when, value=content, inline=False)
        embed.set_footer(text="Total de MAJ: " + ncommits)

        return embed

def check_files():
    if not os.path.isfile("data/red/disabled_commands.json"):
        print("Creating empty disabled_commands.json...")
        dataIO.save_json("data/red/disabled_commands.json", [])


def setup(bot):
    check_files()
    n = Owner(bot)
    bot.add_cog(n)
