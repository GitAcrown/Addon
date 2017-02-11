import discord
from discord.ext import commands
from .utils import checks
import asyncio
import os
import operator
import random
from cogs.utils.dataIO import fileIO, dataIO
from __main__ import send_cmd_help, settings
import time

default = {"PRSROLE": None}

class Justice:
    """Outils de modération avancés."""

    def __init__(self, bot):
        self.bot = bot
        self.sys = dataIO.load_json("data/justice/sys.json")
        self.case = dataIO.load_json("data/justice/case.json")

    @commands.group(pass_context=True)
    async def prs(self, ctx):
        """Commandes de gestion Prison."""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @prs.command(pass_context=True)
    @checks.mod_or_permissions(administrator=True)
    async def setrole(self, ctx, role: discord.Role):
        """Réglage du rôle Prison."""
        channel = ctx.message.channel
        author = ctx.message.author
        if self.sys["PRSROLE"] is None:
            self.sys["PRSROLE"] = role.name
            if role.hoist is False:
                await self.bot.say("Je vous conseille de régler ce rôle pour les afficher dans une liste à part.")
            fileIO("data/justice/sys.json", "save", self.sys)
            await self.bot.say("Rôle enregistré.")
        else:
            await self.bot.say(
                "Le rôle {} est déja renseigné. Voulez-vous l'enlver ? (O/N)".format(self.sys["PRSROLE"]))
            rep = await self.bot.wait_for_message(author=author, channel=channel)
            rep = rep.content.lower()
            if rep == "o":
                await self.bot.say("Le rôle à été retiré.")
                self.sys["PRSROLE"] = None
                fileIO("data/justice/sys.json", "save", self.sys)
            elif rep == "n":
                await self.bot.say("Le rôle est conservé.")
            else:
                await self.bot.say("Réponse invalide, le rôle est conservé.")

    @prs.command(pass_context=True, no_pm=True)
    @checks.mod_or_permissions(kick_members=True)
    async def apply(self, ctx, user: discord.Member, temps: int = 5, mute: bool = False):
        """Ajoute ou retire une personne de prison.
        > Paramètres :
        - user : Utilisateur visé (Mention ou Pseudo exact)
        - temps : Temps en prison, par défaut 5 minutes.
        - mute : True/False, indique si la personne doit être mutée vocalement, par défaut False.
        """
        server = ctx.message.server
        id = user.id
        role = self.sys["PRSROLE"]
        r = discord.utils.get(ctx.message.server.roles, name = role)
        if id not in self.case:
            self.case[user.id] = {"EXACT" : str(user),
                                  "VISITE" : False,
                                  "SORTIE_PRS": None}
            fileIO("data/justice/case.json", "save", self.case)
        if temps >= 1:
            sec = temps * 60 #Nous voulons un temps en secondes
            now = int(time.time())
            sortie = now + sec
            if role not in [r.name for r in user.roles]:
                await self.bot.add_roles(user, r)
                if mute is True:
                    try:
                        self.bot.server_voice_state(user, mute=True)
                    except:
                        pass
                else:
                    pass
                await self.bot.say("{} est désormais en prison pour {} minute(s).".format(user.mention, temps))
                await self.bot.send_message(user, "__Vous êtes désormais en prison pour {} minute(s).__\nVous avez désormais accès au salon *Goulag* pour toute contestation.".format(temps))
                self.case[user.id]["SORTIE_PRS"] = sortie
                self.case[user.id]["VISITE"] = False
                fileIO("data/justice/case.json", "save", self.case)
                await asyncio.sleep(sec) #Attente ~~~~~~~~
                if role in [r.name for r in user.roles]:
                    try:
                        await self.bot.remove_roles(user, r)
                        if mute is True:
                            try:
                                self.bot.server_voice_state(user, mute=False)
                            except:
                                pass
                        else:
                            pass
                        await self.bot.say("{} est désormais libre.".format(user.mention))
                        await self.bot.send_message(user, "__Vous êtes désormais libre.__")
                        self.case[user.id]["SORTIE_PRS"] = None
                        fileIO("data/justice/case.json", "save", self.case)
                    except:
                        await self.bot.whisper("*L'utilisateur {} emprisonné n'est plus sur le serveur.*".format(user.name))
                        self.case[user.id]["SORTIE_PRS"] = None
                        fileIO("data/justice/case.json", "save", self.case)
                else:
                    return
            else:
                try:
                    await self.bot.remove_roles(user, r)
                    if mute is True:
                        try:
                            self.bot.server_voice_state(user, mute=False)
                        except:
                            pass
                    else:
                        pass
                    await self.bot.say("{} à été libéré.".format(user.mention))
                    await self.bot.send_message(user, "__Vous avez été libéré plus tôt que prévu.__")
                    self.case[user.id]["SORTIE_PRS"] = None
                    fileIO("data/justice/case.json", "save", self.case)
                except:
                    await self.bot.whisper("*L'utilisateur {} emprisonné n'est plus sur le serveur.*".format(user.name))
                    self.case[user.id]["SORTIE_PRS"] = None
                    fileIO("data/justice/case.json", "save", self.case)
        else:
            await self.bot.say("Le temps doit être égal ou supérieur à une minute.")

    @prs.command(pass_context=True, no_pm=True)
    async def visite(self, ctx, user: discord.Member = None):
        """Permet la visite de la prison durant un temps illimité.

        Faîtes de nouveau la commande pour vous libérer."""
        if user == None:
            user = ctx.message.author
        server = ctx.message.server
        id = user.id
        role = self.sys["PRSROLE"]
        r = discord.utils.get(ctx.message.server.roles, name=role)
        if id not in self.case:
            self.case[user.id] = {"EXACT": str(user),
                                  "VISITE" : False,
                                  "SORTIE_PRS": None}
            fileIO("data/justice/case.json", "save", self.case)
        if role not in [r.name for r in user.roles]:
            await self.bot.add_roles(user, r)
            await self.bot.say("{} est désormais en prison (Visite)".format(user.mention))
            await asyncio.sleep(0.5)
            await self.bot.send_message(user,
                                        "__Vous visitez la prison.__\nVous avez désormais accès au salon *Goulag*.\nVous pouvez utiliser la commande de nouveau pour arrêter la visite.")

            self.case[user.id]["VISITE"] = True
            fileIO("data/justice/case.json", "save", self.case)
        else:
            if self.case[user.id]["VISITE"] is True:
                try:
                    await self.bot.remove_roles(user, r)
                    await self.bot.say("{} à été libéré (Visite).".format(user.mention))
                    await asyncio.sleep(0.5)
                    await self.bot.send_message(user, "__Au revoir__ :wave:")
                    self.case[user.id]["VISITE"] = False
                    fileIO("data/justice/case.json", "save", self.case)
                except:
                    await self.bot.whisper("*Erreur, {} n'est plus sur le serveur.*".format(user.name))
                    self.case[user.id]["VISITE"] = False
                    fileIO("data/justice/case.json", "save", self.case)
            else:
                await self.bot.say("Hey ! Vous n'êtes pas en visite !")

    @prs.command(pass_context=True)
    async def rest(self, ctx, user: discord.Member = None):
        """Estimation sur la sortie de Prison."""
        role = self.sys["PRSROLE"]
        r = discord.utils.get(ctx.message.server.roles, name=role)
        if user == None:
            user = ctx.message.author
        if user.id in self.case:
            if self.case[user.id]["VISITE"] is False:
                if role in [r.name for r in user.roles]:
                    reste = self.case[user.id]["SORTIE_PRS"] - int(time.time())
                    reste /= 60
                    reste = int(reste)
                    sortie = time.localtime(self.case[user.id]["SORTIE_PRS"])
                    sortie = time.strftime("%H:%M", sortie)
                    await self.bot.say("{} Vous sortirez approximativement vers *{}*.".format(user.mention, sortie))
                else:
                    await self.bot.say("Vous n'êtes pas en Prison")
            else:
                await self.bot.say("Vous êtes en visite, vous pouvez sortir à tout moment en réutilisant la commande de visite.")
        else:
            await self.bot.say("Vous n'avez jamais été en prison.")

def check_folders():
    folders = ("data", "data/justice/")
    for folder in folders:
        if not os.path.exists(folder):
            print("Création du fichier " + folder)
            os.makedirs(folder)

def check_files():
    if not os.path.isfile("data/justice/case.json"):
        print("Création du fichier de stockage de données JUSTICE...")
        fileIO("data/justice/case.json", "save", {})

    if not os.path.isfile("data/justice/sys.json"):
        print("Création du fichier système JUSTICE...")
        fileIO("data/justice/sys.json", "save", default)

def setup(bot):
    check_folders()
    check_files()
    n = Justice(bot)
    bot.add_cog(n)