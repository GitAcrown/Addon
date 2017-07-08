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

default = {"PRSROLE": "Prison", "PRSCHAN": "212928957337567242", "2EGEN": False}

class Justice:
    """Outils de modération avancés."""

    def __init__(self, bot):
        self.bot = bot
        self.sys = dataIO.load_json("data/justice/sys.json")
        self.case = dataIO.load_json("data/justice/case.json")
        if "2EGEN" not in self.sys or self.sys["2EGEN"] is False:
            self.case = {}
            self.sys = default
            self.sys["2EGEN"] = True
            fileIO("data/justice/sys.json", "save", self.sys)
            fileIO("data/justice/case.json", "save", self.case)

    @commands.command(aliases=["p", "jail"], pass_context=True, no_pm=True)
    @checks.admin_or_permissions(manage_messages=True)
    async def prison(self, ctx, user: discord.Member, temps: int = 5, *raison: str):
        """Permet de mettre quelqu'un en Prison pendant un certain temps.
        
        user > Utilisateur visé (Mention ou Pseudo absolu)
        temps > Temps en minutes de la mise en prison (Optionnel, par défaut 5m)
        raison > Raison à la mise en prison (Optionnel)"""
        if raison == "":
            raison = None
        else:
            raison = " ".join(raison)
        role = self.sys["PRSROLE"]
        chan = self.bot.get_channel(self.sys["PRSCHAN"])
        mrole = discord.utils.get(ctx.message.server.roles, name=role)
        if temps >= 1:
            sec = temps * 60  # Temps en secondes
            if user.id not in self.case:
                self.case[user.id] = {"ID": user.id,
                                      "SOMA": 0,
                                      "HISTO": [],
                                      "TEMPS" : None,
                                      "KARMA" : 0}
                self.case[user.id]["KARMA"] -= 1
                fileIO("data/justice/case.json", "save", self.case)
            if role not in [r.name for r in user.roles]:
                self.case[user.id]["TEMPS"] = time.time() + sec
                t = time.strftime("%d/%m - %H:%M", time.localtime())
                if raison == None:
                    raison = "Aucune raison"
                    msgp = "**{}** à été envoyé en prison pendant {}m.\nRaison: *{}*".format(user.name, temps, raison)
                else:
                    msgp = "**{}** à été envoyé en prison pour {} minutes.".format(user.name, temps)
                self.case[user.id]["HISTO"].append("{} | **+** Prison pour {} minute(s).\nRaison: *{}*".format(t, temps, raison))
                fileIO("data/justice/case.json", "save", self.case)
                await self.bot.add_roles(user, mrole)
                await self.bot.say(msgp)
                await self.bot.send_message(chan, "{} | Vous avez été mis en prison pour {}m.\nUtilisez *{}sortie* pour demander à en sortir lorsque votre peine sera effectuée.".format(user.mention, temps, ctx.prefix))
            else:
                t = time.strftime("%d/%m - %H:%M", time.localtime())
                await self.bot.remove_roles(user, mrole)
                await self.bot.say("**{}** à été libéré.".format(user.name))
                await self.bot.send_message(user, "Vous avez été libéré de la prison plus tôt que prévu par {}.".format(ctx.message.author.
                                                                                                                        name))
                self.case[user.id]["HISTO"].append("{} | **!** Libéré par {} plus tôt que prévu.".format(t, ctx.message.author.name))
                self.case[user.id]["TEMPS"] = None
                fileIO("data/justice/case.json", "save", self.case)
        else:
            await self.bot.say("Le temps spécifié doit être supérieur à une minute.")

    @commands.command(alises= ["s", "quit"], pass_context=True, no_pm=True)
    async def sortie(self, ctx):
        """Demander la sortie de prison et donne le temps restant le cas échéant."""
        author = ctx.message.author
        role = self.sys["PRSROLE"]
        mrole = discord.utils.get(ctx.message.server.roles, name=role)
        if author.id in self.case and role in [r.name for r in author.roles]:
            if time.time() >= self.case[author.id]["TEMPS"]:
                await self.bot.say("**Sortie autorisée**\n*Patientez s'il vous plaît...*")
                await asyncio.sleep(1.5)
                await self.bot.remove_roles(author, mrole)
                t = time.strftime("%d/%m - %H:%M", time.localtime())
                self.case[author.id]["HISTO"].append("{} | **-** Sortie autonome autorisée de prison.".format(t))
                self.case[author.id]["TEMPS"] = None
                fileIO("data/justice/case.json", "save", self.case)
            else:
                restant = round((self.case[author.id]["TEMPS"] - time.time()) / 60, 1)
                if restant < 1:
                    msg = "{}s".format(int(restant * 100))
                else:
                    msg = "{}m".format(int(restant))
                await self.bot.say("Il vous reste approximativement {} de prison.".format(msg))
        else:
            await self.bot.say("Vous n'êtes pas en prison.")

    @commands.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(manage_messages=True)
    async def niv(self, ctx, membre:discord.Member, niveau:int = None):
        """Permet de modifier le niveau de Sommation d'un membre (0-3) ou affiche le niveau si non précisé.
        Rappels:
        0 = Absence de sommation (reset)
        1 = Prison 5m
        2 = Prison 30m
        3 = Prison 24h
        4 = Kick
        Attention, le niveau monte de un cran à chaque blâme.
        Exemple : Mettre un membre en sommation 3 signifie qu'au prochain blâme il sera kick."""
        if membre.id in self.case:
            if niveau is None:
                if "SOMA" in self.case[membre.id]:
                    await self.bot.say("*{}* est au niveau **{}** de sommation.".format(membre.name, self.case[membre.id]["SOMA"]))
                    return
            if niveau < 4:
                self.case[membre.id]["SOMA"] = niveau
                fileIO("data/justice/case.json", "save", self.case)
                await self.bot.say("Niveau de sommation modifié avec succès.")
            else:
                await self.bot.say("Le niveau doit être compris entre 0 et 3.")
        else:
            if niveau < 4:
                self.case[user.id] = {"ID": user.id,
                                      "SOMA": 0,
                                      "HISTO": [],
                                      "TEMPS": None,
                                      "KARMA": 0}
                fileIO("data/justice/case.json", "save", self.case)
            else:
                await self.bot.say("Le niveau doit être compris entre 0 et 3.")


    async def slash(self, user):
        """Détecte et remet le rôle prison si échappé"""
        server = user.server
        role = self.sys["PRSROLE"]
        mrole = discord.utils.get(server.roles, name=role)
        if user.id in self.case:
            if self.case[user.id]["TEMPS"] != None:
                if role not in [r.name for r in user.roles]:
                    await self.bot.add_roles(user, mrole)
                    await self.bot.send_message(user, "**Rappel:** Vous êtes en prison. Utilisez &sortie sur le channel approprié pour en sortir ou obtenir, dans le cas échant, le temps restant.")

    async def semiauto(self, reaction, author):
        user = reaction.message.author
        role = self.sys["PRSROLE"]
        chan = self.bot.get_channel(self.sys["PRSCHAN"])
        mrole = discord.utils.get(reaction.message.server.roles, name=role)
        temps = 5
        raison = None
        if reaction.emoji == "‼":
            if author.server_permissions.manage_messages is True:
                if role not in [r.name for r in user.roles]:
                    if user.id not in self.case:
                        self.case[user.id] = {"ID": user.id,
                                              "SOMA": 0,
                                              "HISTO": [],
                                              "TEMPS": None,
                                              "KARMA": 0}
                        self.case[user.id]["KARMA"] -= 1
                        fileIO("data/justice/case.json", "save", self.case)
                    if "SOMA" not in self.case[user.id]:
                        self.case[user.id]["SOMA"] = 0
                    self.case[user.id]["SOMA"] += 1
                    if self.case[user.id]["SOMA"] == 1:
                        temps = 5
                        raison = "Première sommation Auto"
                    elif self.case[user.id]["SOMA"] == 2:
                        temps = 30
                        raison = "Deuxième sommation Auto"
                    elif self.case[user.id]["SOMA"] == 3:
                        temps = 1440 #24h
                        raison = "Troisième sommation Auto"
                    elif self.case[user.id]["SOMA"] == 4:
                        self.case[user.id]["SOMA"] = 0
                        await self.bot.kick(user)
                        return
                    else:
                        self.case[user.id]["SOMA"] = 0
                    sec = temps * 60
                    self.case[user.id]["TEMPS"] = time.time() + sec
                    t = time.strftime("%d/%m - %H:%M", time.localtime())
                    msgp = "**{}** à été envoyé en prison pendant **{}m** par **{}**.\nRaison: *{}*".format(user.name, temps, author.name, raison)
                    self.case[user.id]["HISTO"].append(
                        "{} | **+** Prison pour {} minute(s).\nRaison: *{}*".format(t, temps, raison))
                    fileIO("data/justice/case.json", "save", self.case)
                    await self.bot.add_roles(user, mrole)
                    await self.bot.send_message(reaction.message.channel, msgp)
                    await self.bot.send_message(chan,
                                                "{} | Vous avez été mis en prison pour **{}m** par **{}**.\nUtilisez *&sortie* pour demander à en sortir lorsque votre peine sera effectuée.".format(
                                                    user.mention, temps, author.name))

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
    bot.add_listener(n.slash, "on_member_join")
    bot.add_listener(n.semiauto, "on_reaction_add")
    bot.add_cog(n)