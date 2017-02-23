from typing import List
import discord
from discord.ext import commands
from .utils import checks
from .utils.dataIO import dataIO, fileIO
from .utils import checks, chat_formatting as cf
from __main__ import send_cmd_help
import os
import time
import datetime
import asyncio
import operator

default_settings = {
    "join_message": "{0.mention} has joined the server.",
    "leave_message": "{0.mention} has left the server.",
    "ban_message": "{0.mention} has been banned.",
    "unban_message": "{0.mention} has been unbanned.",
    "join_mp": "Salut {0.mention}, bienvenue sur EK !",
    "on": False,
    "channel": None
}

class Tools:
    """Ensemble d'outils."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.settings_path = "data/membership/settings.json"
        self.settings = dataIO.load_json(self.settings_path)
        self.live = dataIO.load_json("data/gen/live.json")

    def compare_role(self, user, rolelist):
        for role in rolelist:
            if role in user.roles:
                return True
        else:
            return False

    def log_update(self, server, change: str):
        temps = time.strftime("%d/%m/%Y %H:%M:%S", time.localtime())
        if server.id in self.live:
            self.live[server.id]["UPDATE"].append([temps, change])
            fileIO("data/gen/live.json", "save", self.live)
            return True
        else:
            self.live[server.id] = {"NOM" : server.name,
                                  "UPDATE" : []}
            self.live[server.id]["UPDATE"].append([temps, change])
            fileIO("data/gen/live.json", "save", self.live)
            return True

    @commands.command(pass_context=True)
    async def jp(self, ctx, nb: int=10):
        """Affiche les X derniers changements de pseudo du serveur.

        Par défaut les 10 derniers."""
        server = ctx.message.server
        clsm = []
        msg = "**Derniers changements**\n"
        if server.id in self.live:
            for e in self.live[server.id]["UPDATE"]:
                clsm.append([e[0],e[1]])
            clsm = sorted(clsm, key=operator.itemgetter(0))
            clsm.reverse()
            if len(clsm) <= nb:
                nb = len(clsm)
            a = 0
            while a < nb:
                rang = clsm[a]
                temps = rang[0]
                update = rang[1]
                msg += "__{}__ > {}\n".format(temps, update)
                a += 1
            await self.bot.say(msg)
        else:
            self.live[server.id] = {"NOM": server.name,
                                    "UPDATE": []}
            fileIO("data/gen/live.json", "save", self.live)
            await self.bot.say("Aucun changement enregistré pour ce serveur.")

    @commands.command(pass_context=True, no_pm=True)
    async def easter(self, ctx):
        """Ceci n'est pas un easter egg."""
        # Pour les gens qui cherchent des easter-eggs dans les codes :jpp:
        await self.bot.say("```css\nCeci n'est en aucun cas un easter-egg.```")

# AUTRE ------------------------------------------------------------

    @commands.command(pass_context=True)
    async def membernb(self, ctx):
        """Renvoie le nombre de membres présents sur le serveur."""
        server = ctx.message.server
        a = 0
        await self.bot.say("Il y a" + str(len(server.members)) + " membres sur le serveur.")
        for member in server.members:
            if member.status is discord.Status.online:
                a += 1
        else:
            await self.bot.say("Dont {} actifs.".format(a))
                
    @commands.command(pass_context=True)
    async def bans(self, ctx):
        """Retrouve les bannis du serveur."""
        server = ctx.message.server
        a = 0
        for member in await self.bot.get_bans(server):
            a +=1
        await self.bot.say("Il y a {} bannis sur ce serveur.".format(a))

    @commands.command(pass_context=True)
    async def region(self, ctx):
        """Affiche la région du serveur."""
        await self.bot.say(ctx.message.server.region)

    @commands.command(pass_context=True)
    async def time(self, ctx, temps:int):
        """Permet d'attendre pendant x secondes."""
        now = int(time.time())
        await self.bot.say("Now : {}".format(now))
        vise = now + temps
        while int(time.time()) != vise:
            pass
        else:
            await self.bot.say("Terminé : {}".format(int(time.time())))

    @commands.command(pass_context=True)
    async def urole(self, ctx):
        """Affiche l'ensemble des rôles liés aux utilisateurs du serveur."""
        server = ctx.message.server
        msg = "**Serveur {}:**\n".format(server.name)
        n = 1
        for member in server.members:
                clean = []
                for role in member.roles:
                    clean.append(role.name)
                if clean != ["@everyone"]:
                    msg += "{} | {}\n".format(member.mention, clean)
                if len(msg) > 1900 * n:
                    msg += "!!"
                    n += 1
        else:
            listmsg = msg.split("!!")
            for msg in listmsg:
                await self.bot.say(msg)

    @commands.command(pass_context=True)
    async def ancien(self, ctx, jours: int):
        """Recherche les gens qui ont + de X jours sur le serveur."""
        server = ctx.message.server
        msg = "**Anciens (+{} jours):**\n".format(jours)
        n = 1
        for member in server.members:
            passed = (ctx.message.timestamp - member.joined_at).days
            if passed >= jours:
                clean = []
                for role in member.roles:
                    clean.append(role.name)
                if "Habitué" in clean:
                    msg += "{}\n".format(member.mention)
                    if len(msg) > 1900 * n:
                        msg += "!!"
                        n += 1
        else:
            listmsg = msg.split("!!")
            for msg in listmsg:
                await self.bot.whisper(msg)
                      
    @commands.command(pass_context=True)
    async def suser(self, ctx, *snom):
        """Recherche un utilisateur."""
        server = ctx.message.server
        nom = " ".join(snom).lower()
        nb = 0
        for member in server.members: #On cherche le nombre de résultats [RECHERCHE ALL]
            if nom in member.name or nom in member.display_name:
                nb += 1
        if nb > 0:
            await self.bot.say("**{} Résultat(s)**".format(nb))
            await asyncio.sleep(0.25)
            msg = "**Quel mode voulez-vous utiliser ?**\n"
            msg += "*ALL* - Affiche l'ensemble des résultats\n"
            msg += "*DEB* - Affiche les résultats commençant par votre recherche\n"
            msg += "*FIN* - Affiche les résultats finissant par votre recherche\n"
            msg += "-----------------------\n"
            msg += "*ACTIF* - Affiche seulement les membres actifs\n"
            msg += "*INACT* - Affiche seulement les membres inactifs\n"
            msg += "*ROLE* - Affiche seulement les membres possédant le rôle visé\n"
            msg += "*STR* - Recherche stricte, la case est prise en compte\n"
            msg += "\n" + "**Assemblez les mots clefs ci-dessus pour lancer la recherche...**\n*Note : N'oubliez pas qu'il faut au moins 'ALL','DEB' ou 'FIN' pour démarrer la recherche !*"
            await self.bot.say(msg)
            verif = False
            while verif != True:
                rps = await self.bot.wait_for_message(author = ctx.message.author, channel = ctx.message.channel)
                rps = rps.content.lower()
                if rps != "":
                    
                    if "role" in rps:
                        verif2 = False
                        await self.bot.say("**Mentionne le(s) rôle(s) que tu veux rechercher:**")
                        while verif2 != True:
                            rmsg = await self.bot.wait_for_message(author = ctx.message.author, channel = ctx.message.channel)
                            if rmsg.content != "":
                                rlist = rmsg.role_mentions
                                verif2 = True
                            else:
                                await self.bot.say("Invalide, réessaye !")
                                continue
                                
                    if "str" in rps:
                            nom = " ".join(snom)
                    
                    if "actif" and "inactif" in rps:
                        await self.bot.say("Certains mots clefs ne sont pas compatibles entre eux ! ('ACTIF' et 'INACT' reviennent à 'ALL' !)\nRéessayez.")
                        continue
                    
                    #RECHERCHE
                    verif = True
                    if "all" in rps: #MODE FULL
                        if "actif" in rps: #FULL ACTIF
                            res = "**Voici ce que j'ai trouvé pour [ALL, ACTIF]:**\n"
                            for member in server.members:
                                if nom in member.name or nom in member.display_name:
                                    if member.status is discord.Status.online:
                                        res += "*{}* | {}\n".format(member.display_name, member.mention)
                        elif "inact" in rps: #FULL INACTIF
                            res = "**Voici ce que j'ai trouvé pour [ALL, INACT]:**\n"
                            for member in server.members:
                                if nom in member.name or nom in member.display_name:
                                    if member.status is discord.Status.offline:
                                        res += "*{}* | {}\n".format(member.display_name, member.mention)
                        elif "role" in rps: #FULL ROLE
                            res = "**Voici ce que j'ai trouvé pour [ALL, ROLE] (Avec les rôles spécifiés):**\n"
                            for member in server.members:
                                if nom in member.name or nom in member.display_name:
                                    if self.compare_role(member, rlist):
                                        res += "*{}* | {}\n".format(member.display_name, member.mention)
                        else: #FULL SIMPLE
                            res = "**Voici ce que j'ai trouvé pour [ALL]:**\n"
                            for member in server.members:
                                if nom in member.name or nom in member.display_name:
                                    res += "*{}* | {}\n".format(member.display_name, member.mention)
                        await self.bot.say(res)
                    elif "deb" in rps: #MODE DEBUT
                        r = len(nom)
                        if "actif" in rps: #DEBUT ACTIF
                            res = "**Voici ce que j'ai trouvé pour [DEB, ACTIF]:**\n"
                            for member in server.members:
                                if nom in member.name[:r] or nom in member.display_name[:r]:
                                    if member.status is discord.Status.online:
                                        res += "*{}* | {}\n".format(member.display_name, member.mention)
                        elif "inact" in rps: #DEBUT INACT
                            res = "**Voici ce que j'ai trouvé pour [DEB, INACT]:**\n"
                            for member in server.members:
                                if nom in member.name[:r] or nom in member.display_name[:r]:
                                    if member.status is discord.Status.offline:
                                        res += "*{}* | {}\n".format(member.display_name, member.mention)
                        elif "role" in rps: #DEBUT ROLE
                            res = "**Voici ce que j'ai trouvé pour [DEB, ROLE] (Avec les rôles spécifiés):**\n"
                            for member in server.members:
                                if nom in member.name[:r] or nom in member.display_name[:r]:
                                    if self.compare_role(member, rlist):
                                        res += "*{}* | {}\n".format(member.display_name, member.mention)
                        else: #DEBUT SIMPLE
                            res = "**Voici ce que j'ai trouvé pour [DEB]:**\n"
                            for member in server.members:
                                if nom in member.name[:r] or nom in member.display_name[:r]:
                                    res += "*{}* | {}\n".format(member.display_name, member.mention)
                        await self.bot.say(res)
                    elif "fin" in rps: #MODE FIN
                        r = len(nom)
                        if "actif" in rps: #FIN ACTIF
                            res = "**Voici ce que j'ai trouvé pour [FIN, ACTIF]:**\n"
                            for member in server.members:
                                if nom in member.name[-r:] or nom in member.display_name[-r:]:
                                    if member.status is discord.Status.online:
                                        res += "*{}* | {}\n".format(member.display_name, member.mention)
                        elif "inact" in rps: #FIN INACT
                            res = "**Voici ce que j'ai trouvé pour [FIN, INACT]:**\n"
                            for member in server.members:
                                if nom in member.name[-r:] or nom in member.display_name[-r:]:
                                    if member.status is discord.Status.offline:
                                        res += "*{}* | {}\n".format(member.display_name, member.mention)
                        elif "role" in rps: #FIN ROLE
                            res = "**Voici ce que j'ai trouvé pour [FIN, ROLE] (Avec les rôles spécifiés):**\n"
                            for member in server.members:
                                if nom in member.name[-r:] or nom in member.display_name[-r:]:
                                    if self.compare_role(member, rlist):
                                        res += "*{}* | {}\n".format(member.display_name, member.mention)
                        else: #FIN SIMPLE
                            res = "**Voici ce que j'ai trouvé pour [FIN]:**\n"
                            for member in server.members:
                                if nom in member.name[-r:] or nom in member.display_name[-r:]:
                                    res += "*{}* | {}\n".format(member.display_name, member.mention)
                        await self.bot.say(res)
                    else:
                        await self.bot.say("Votre recherche ne donne aucun résultat. Vérifiez vos mots-clefs.")
                        continue
                else:
                    await self.bot.say("Mettez des mots clefs pour commencer une recherche.")
                    continue

    @commands.command(pass_context=True)
    @checks.mod_or_permissions(ban_members=True)
    async def unban(self, ctx, user : discord.Member):
        """Permet le déban d'un utilisateur."""
        server = ctx.message.server
        if user in server.members:
            self.bot.unban(server, user)
            await self.bot.say("L'utilisateur a été débanni.")
        else:
            await self.bot.say("L'utilisateur n'est pas sur le serveur.")

# MASSDM -----------------------------------------------------------

    def _member_has_role(self, member: discord.Member, role: discord.Role):
        return role in member.roles

    def _get_users_with_role(self, server: discord.Server,
                             role: discord.Role) -> List[discord.User]:
        roled = []
        for member in server.members:
            if self._member_has_role(member, role):
                roled.append(member)
        return roled

    @commands.command(no_pm=True, pass_context=True, name="mdm", aliases=["massdm"])
    @checks.mod_or_permissions(ban_members=True)
    async def _mdm(self, ctx: commands.Context, role: discord.Role, *, message: str):
        """Envoie un MP à toutes les personnes possédant un certain rôle.
        Permet certaines customisations:
        {0} est le membre recevant le message.
        {1} est le rôle au travers duquel ils sont MP.
        {2} est la personne envoyant le message.
        Exemple: Message provenant de {2}: Salut {0} du rôle {1} ! ..."""
        server = ctx.message.server
        sender = ctx.message.author
        await self.bot.delete_message(ctx.message)
        dm_these = self._get_users_with_role(server, role)
        for user in dm_these:
            await self.bot.send_message(user,message.format(user, role, sender))

#MEMBERSHIP ---------------------------------------------------------

    @commands.group(pass_context=True, no_pm=True, name="trigset")
    @checks.admin_or_permissions(manage_server=True)
    async def _membershipset(self, ctx: commands.Context):
        """Changement des paramétrages des triggers."""
        server = ctx.message.server
        if server.id not in self.settings:
            self.settings[server.id] = default_settings
            self.settings[server.id]["channel"] = server.default_channel.id
            dataIO.save_json(self.settings_path, self.settings)
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @_membershipset.command(pass_context=True, no_pm=True, name="join",aliases=["greeting", "bienvenue"])
    async def _join(self, ctx: commands.Context, *,
                    format_str: str):
        """Change le message d'arrivée du serveur.
        {0} est le membre
        {1} est le serveur
        """
        await self.bot.type()
        server = ctx.message.server
        self.settings[server.id]["join_message"] = format_str
        dataIO.save_json(self.settings_path, self.settings)
        await self.bot.say("Message réglé.")

    @_membershipset.command(pass_context=True, no_pm=True, name="mp")
    async def _mp(self, ctx: commands.Context, *,
                    format_str: str):
        """Change le MP d'arrivée du serveur.
        {0} est le membre
        {1} est le serveur
        """
        await self.bot.type()
        server = ctx.message.server
        self.settings[server.id]["join_mp"] = format_str
        dataIO.save_json(self.settings_path, self.settings)
        await self.bot.say("Message réglé.")

    @_membershipset.command(pass_context=True, no_pm=True, name="leave",aliases=["adieu"])
    async def _leave(self, ctx: commands.Context, *,
                     format_str: str):
        """Change le message de départ du serveur.
        {0} est le membre
        {1} est le serveur
        """
        await self.bot.type()
        server = ctx.message.server
        self.settings[server.id]["leave_message"] = format_str
        dataIO.save_json(self.settings_path, self.settings)
        await self.bot.say("Message reglé.")

    @_membershipset.command(pass_context=True, no_pm=True, name="ban")
    async def _ban(self, ctx: commands.Context, *, format_str: str):
        """Change le message de ban du serveur.
        {0} est le membre
        {1} est le serveur
        """
        await self.bot.type()
        server = ctx.message.server
        self.settings[server.id]["ban_message"] = format_str
        dataIO.save_json(self.settings_path, self.settings)
        await self.bot.say("Message reglé.")

    @_membershipset.command(pass_context=True, no_pm=True, name="unban")
    async def _unban(self, ctx: commands.Context, *, format_str: str):
        """Change le message de débanissement du serveur.
        {0} est le membre
        {1} est le serveur
        """
        await self.bot.type()
        server = ctx.message.server
        self.settings[server.id]["unban_message"] = format_str
        dataIO.save_json(self.settings_path, self.settings)
        await self.bot.say("Message reglé.")

    @_membershipset.command(pass_context=True, no_pm=True, name="toggle")
    async def _toggle(self, ctx: commands.Context):
        """Active ou désactive les triggers serveur."""

        await self.bot.type()
        server = ctx.message.server
        self.settings[server.id]["on"] = not self.settings[server.id]["on"]
        if self.settings[server.id]["on"]:
            await self.bot.say("Les events du trigger seront annoncés.")
        else:
            await self.bot.say("Les events du trigger ne seront plus annoncés.")
        dataIO.save_json(self.settings_path, self.settings)

    @_membershipset.command(pass_context=True, no_pm=True, name="channel")
    async def _channel(self, ctx: commands.Context,
                       channel: discord.Channel=None):
        """Change le channel où doit être envoyé les messages d'activation de trigger.

        Par défaut le présent."""

        await self.bot.type()
        server = ctx.message.server

        if not channel:
            channel = server.default_channel

        if not self.speak_permissions(server, channel):
            await self.bot.say(
                "Je n'ai pas les permissions d'envoyer de message sur {0.mention}.".format(channel))
            return

        self.settings[server.id]["channel"] = channel.id
        dataIO.save_json(self.settings_path, self.settings)
        channel = self.get_welcome_channel(server)
        await self.bot.send_message(channel,"{0.mention}, " + "Je vais maintenant envoyer les messages d'annonce" + "sur {1.mention}.".format(ctx.message.author, channel))

    @commands.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(manage_server=True)
    async def upchan(self, ctx, channel: discord.Channel):
        """Permet de mettre un serveur de publication des update profil."""
        server = ctx.message.server
        self.settings[server.id]["upchan"] = channel.id
        dataIO.save_json(self.settings_path, self.settings)
        await self.bot.say("Channel réglé.")

    async def member_join(self, member: discord.Member):
        server = member.server
        if server.id not in self.settings:
            self.settings[server.id] = default_settings
            self.settings[server.id]["channel"] = server.default_channel.id
            dataIO.save_json(self.settings_path, self.settings)

        if not self.settings[server.id]["on"]:
            return

        await self.bot.send_typing(
            self.bot.get_channel(self.settings[member.server.id]["channel"]))

        if server is None:
            print("Le serveur était considéré NONE, Erreur inconnue."
                  "L'utilisateur était {}.".format(
                      member.name))
            return

        channel = self.get_welcome_channel(server)
        if self.speak_permissions(server, channel):
            await self.bot.send_message(channel,
                                        self.settings[server.id][
                                            "join_message"]
                                        .format(member, server))
            await asyncio.sleep(0.25)
            await self.bot.send_message(member, self.settings[server.id][
                                            "join_mp"])
        else:
            print("Je n'ai pas eu les autorisations pour envoyer un message. L'utilisateur était {}.".format(member.name))

    async def member_leave(self, member: discord.Member):
        server = member.server
        if server.id not in self.settings:
            self.settings[server.id] = default_settings
            self.settings[server.id]["channel"] = server.default_channel.id
            dataIO.save_json(self.settings_path, self.settings)

        if not self.settings[server.id]["on"]:
            return

        await self.bot.send_typing(
            self.bot.get_channel(self.settings[member.server.id]["channel"]))

        if server is None:
            print("Le serveur était NONE, c'était peut-être un MP. L'utilisateur était {}.".format(member.name))
            return

        channel = self.get_welcome_channel(server)
        if self.speak_permissions(server, channel):
            await self.bot.send_message(channel,
                                        self.settings[server.id][
                                            "leave_message"]
                                        .format(member, server))
        else:
            print("J'ai essayé d'envoyer un message mais je n'ai pas pu, l'utilisateur était {}.".format(member.name))

    async def member_ban(self, member: discord.Member):
        server = member.server
        if server.id not in self.settings:
            self.settings[server.id] = default_settings
            self.settings[server.id]["channel"] = server.default_channel.id
            dataIO.save_json(self.settings_path, self.settings)

        if not self.settings[server.id]["on"]:
            return

        await self.bot.send_typing(
            self.bot.get_channel(self.settings[member.server.id]["channel"]))

        if server is None:
            print("Le serveur était NONE, c'était peut-être un MP. L'utilisateur était {}.".format(member.name))
            return

        channel = self.get_welcome_channel(server)
        if self.speak_permissions(server, channel):
            await self.bot.send_message(channel,
                                        self.settings[server.id]["ban_message"]
                                        .format(member, server))
        else:
            print("J'ai essayé d'envoyer un message mais je n'ai pas pu, l'utilisateur était {}.".format(member.name))

    async def member_unban(self, member: discord.Member):
        server = member.server
        if server.id not in self.settings:
            self.settings[server.id] = default_settings
            self.settings[server.id]["channel"] = server.default_channel.id
            dataIO.save_json(self.settings_path, self.settings)

        if not self.settings[server.id]["on"]:
            return

        await self.bot.send_typing(
            self.bot.get_channel(self.settings[member.server.id]["channel"]))

        if server is None:
            print("Le serveur était NONE, c'était peut-être un MP. L'utilisateur était {}.".format(
                      member.name))
            return

        channel = self.get_welcome_channel(server)
        if self.speak_permissions(server, channel):
            await self.bot.send_message(channel,
                                        self.settings[server.id][
                                            "unban_message"]
                                        .format(member, server))
        else:
            print("J'ai essayé d'envoyer un message mais je n'ai pas pu, l'utilisateur était {}.".format(member.name))

    async def member_update(self, before: discord.Member, after: discord.Member):
        server = after.server
        if server.id in self.settings:
            if before.nick != after.nick:
                if after.nick != None:
                    if before.nick == None:
                        self.log_update(server,
                                        "**{}** a changé son surnom en **{}** (Pseudo *{}*)".format(before.name,
                                                                                                      after.nick,
                                                                                                      after.name))
                        return
                    self.log_update(server, "**{}** a changé son surnom en **{}** (Pseudo *{}*)".format(before.nick,
                                                                                                         after.nick,
                                                                                                         after.name))
                else:
                    self.log_update(server, "**{}** a retiré son surnom (Pseudo *{}*)".format(before.name,after.name))
            elif before.name != after.name:
                self.log_update(server,
                                "**{}** a changé son pseudo en **{}** (Pseudo *{}*)".format(before.name, after.name,
                                                                                              after.nick))
            else:
                pass
        else:
            pass

    def get_welcome_channel(self, server: discord.Server):
        return server.get_channel(self.settings[server.id]["channel"])

    def speak_permissions(self, server: discord.Server,
                          channel: discord.Channel=None):
        if not channel:
            channel = self.get_welcome_channel(server)
        return server.get_member(
            self.bot.user.id).permissions_in(channel).send_messages

    
    #DEMARRAGE =================================================================

def check_folders():
    if not os.path.exists("data/membership"):
        print("Création de data/membership directory...")
        os.makedirs("data/membership")


def check_files():
    f = "data/membership/settings.json"
    if not dataIO.is_valid_json(f):
        print("Création de data/membership/settings.json...")
        dataIO.save_json(f, {})

    f = "data/gen/sondage.json"
    if not dataIO.is_valid_json(f):
        print("Création du fichier de Sondages...")
        dataIO.save_json(f, {})

    f = "data/gen/live.json"
    if not dataIO.is_valid_json(f):
        print("Création du fichier Live...")
        dataIO.save_json(f, {})

def setup(bot: commands.Bot):
    check_folders()
    check_files()
    n = Tools(bot)
    bot.add_listener(n.member_join, "on_member_join")
    bot.add_listener(n.member_leave, "on_member_remove")
    bot.add_listener(n.member_ban, "on_member_ban")
    bot.add_listener(n.member_unban, "on_member_unban")
    bot.add_listener(n.member_update, "on_member_update")
    bot.add_cog(n)
