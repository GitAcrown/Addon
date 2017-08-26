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

class Just:
    """Ajoute des fonctionnalités supplémentaires à la modération"""

    def __init__(self, bot):
        self.bot = bot
        self.sys = dataIO.load_json("data/just/sys.json")
        self.reg = dataIO.load_json("data/just/reg.json")

    def save(self):
        fileIO("data/just/sys.json", "save", self.sys)
        fileIO("data/just/reg.json", "save", self.reg)
        return True

    def new_event(self, classe, destination, auteur, temps="?"):
        today = time.strftime("%d/%m/%Y", time.localtime())
        if not "HISTORIQUE" in self.sys:
            self.sys["HISTORIQUE"] = []
        self.sys["HISTORIQUE"].append([today, classe, destination, auteur, temps])
        self.save()
        return True

    def convert_sec(self, form: str, val: int):
        if form == "j":
            return val * 86400
        elif form == "h":
            return val * 3600
        elif form == "m":
            return val * 60
        else:
            return val #On considère alors que c'est déjà en secondes

    @commands.command(aliases=["p", "jail"], pass_context=True)
    @checks.admin_or_permissions(manage_messages=True)
    async def prison(self, ctx, user: discord.Member, temps: str = "5m"):
        """Mettre un membre en prison pendant un certain temps (Par défaut 5m).
        
        user = Utilisateur à mettre en prison
        temps = Temps pendant lequel l'utilisateur est en prison (Minimum 60s)
        Format de temps:
        's' pour seconde(s)
        'm' pour minute(s)
        'h' pour heure(s)
        'j' pour jour(s)
        Exemple : &p @membre 5h
        
        Note - Il est possible d'ajouter ou retirer du temps avec '+' et '-' avant le chiffre
        Exemple : &p @membre +10m"""
        server = ctx.message.server
        if temps.isdigit():
            await self.bot.whisper("**N'oubliez pas le format !**\n"
                                   "Formats disponibles : m (minutes), h (heures), j (jours)\n"
                                   "Exemple: &p @membre 5h")
            return
        role = self.sys["ROLE_PRISON"]
        apply = discord.utils.get(ctx.message.server.roles, name=role)
        form = temps[-1:]
        if form not in ["s", "m", "h", "j"]:
            await self.bot.say("Ce format n'existe pas (s, m, h ou j)")
            return
        save = user.name
        if temps.startswith("+") or temps.startswith("-"): #Ajouter ou retirer du temps de prison
            val = temps.replace(form, "")
            val = int(val.replace(temps[0], ""))
            if user.id in self.reg:
                if role in [r.name for r in user.roles]:
                    modif = self.convert_sec(form, val)
                    if temps[0] == "+":
                        self.reg[user.id]["FIN_PEINE"] += modif
                        self.new_event("add", user.id, ctx.message.author.id, modif)
                        estim = time.strftime("%H:%M", time.localtime(self.reg[user.id]["FIN_PEINE"]))
                        await self.bot.say("**Ajout de *{}{}* pour *{}* réalisé avec succès.**".format(val, form, user.name))
                        await self.bot.send_message(user, "*{}{}* ont été ajoutés à ta peine par *{}*\nSortie désormais prévue à: `{}`".format(val, form, ctx.message.author.name, estim))
                    elif temps[0] == "-":
                        self.reg[user.id]["FIN_PEINE"] -= modif
                        self.new_event("sub", user.id, ctx.message.author.id, modif)
                        estim = time.strftime("%H:%M", time.localtime(self.reg[user.id]["FIN_PEINE"]))
                        await self.bot.say(
                            "**Retrait de *{}{}* pour *{}* réalisé avec succès.**".format(val, form, user.name))
                        await self.bot.send_message(user,
                                                    "*{}{}* ont été retirés de ta peine par *{}*\nSortie désormais prévue à: `{}`".format(
                                                        val, form, ctx.message.author.name, estim))
                    else:
                        await self.bot.say("Symbole non reconnu. Ajoutez du temps avec '+' et retirez-en avec '-'.")
                        return
                else:
                    await self.bot.say("L'utilisateur n'est pas en prison. Vous ne pouvez donc pas lui ajouter ni retirer du temps de peine.")
                    return
            else:
                await self.bot.say("L'utilisateur n'a jamais été en prison. Vous ne pouvez donc pas lui ajouter ni retirer du temps de peine.")
                return
        else:
            val = int(temps.replace(form, ""))
            sec = self.convert_sec(form, val)
            if sec >= 60: #Au moins une minute
                if sec > 86400:
                    await self.bot.whisper("Il est déconseillé d'utiliser la prison pour une peine dépassant 24h (1j) à cause des instabilités de Discord pouvant causer une peine infinie.")
                if user.id not in self.reg:
                    self.reg[user.id] = {"FIN_PEINE": None,
                                         "DEB_PEINE": None,
                                         "BANG": 0,
                                         "ROLES": [r.name for r in user.roles],
                                         "D_PSEUDO": user.display_name,
                                         "TRACKER": []}
                    self.save()
                if role not in [r.name for r in user.roles]:
                    b_peine = time.time()
                    estim = time.strftime("%H:%M", time.localtime(b_peine + sec))
                    self.reg[user.id]["DEB_PEINE"] = b_peine
                    self.reg[user.id]["FIN_PEINE"] = b_peine + sec
                    self.new_event("in", user.id, ctx.message.author.id, temps)
                    await self.bot.add_roles(user, apply)
                    await self.bot.say("{} **a été mis(e) en prison pendant *{}* par *{}***".format(user.mention, temps, ctx.message.author.name))
                    await self.bot.send_message(user, "**Tu as été mis(e) en prison pendant {}**\nSortie prévue à: `{}`\n"
                                                      "Un salon textuel écrit est disponible sur le serveur afin de contester cette punition ou afin d'obtenir plus d'informations.".format(temps, estim))
                    self.save()
                    while time.time() < self.reg[user.id]["FIN_PEINE"] or self.reg[user.id]["FIN_PEINE"] != None:
                        await asyncio.sleep(1)
                    if user in server.members:
                        if role in [r.name for r in user.roles]:
                            self.reg[user.id]["DEB_PEINE"] = self.reg[user.id]["FIN_PEINE"] = 0
                            self.new_event("out", user.id, "auto")
                            await self.bot.remove_roles(user, apply)
                            await self.bot.say("{} **est libre**".format(user.mention))
                            await asyncio.sleep(1)
                            self.reg[user.id]["DEB_PEINE"] = self.reg[user.id]["FIN_PEINE"] = None
                            self.save()
                        else:
                            return
                    else:
                        await self.bot.say("{} ne peut être sorti de prison car il n'est plus sur le serveur.".format(save))
                else:
                    self.reg[user.id]["DEB_PEINE"] = self.reg[user.id]["FIN_PEINE"] = 0
                    self.new_event("out", user.id, ctx.message.author.id)
                    await self.bot.remove_roles(user, apply)
                    await self.bot.say("{} **a été libéré par *{}***".format(user.mention, ctx.message.author.name))
                    await asyncio.sleep(1)
                    self.reg[user.id]["DEB_PEINE"] = self.reg[user.id]["FIN_PEINE"] = None
                    self.save()
            else:
                await self.bot.say("Le temps minimum est de 1m")

    async def renew(self, user):
        server = user.server
        chanp = self.bot.get_channel("204585334925819904")
        role = self.sys["ROLE_PRISON"]
        save = user.name
        apply = discord.utils.get(server.roles, name=role)
        if user.id in self.reg:
            if role not in [r.name for r in user.roles]:
                if self.reg[user.id]["FIN_PEINE"] != None:
                    if self.reg[user.id]["FIN_PEINE"] > time.time():
                        await self.bot.add_roles(user, apply)
                        estim = time.strftime("%H:%M", time.localtime(self.reg[user.id]["FIN_PEINE"]))
                        await self.bot.send_message(chanp, "**{} retourne automatiquement en prison pour finir sa peine**".format(user.name))
                        await self.bot.send_message("**Rappel: Vous aviez été mis en prison et votre peine n'est pas terminée.**\nSortie prévue à: `{}`".format(estim))
                        while time.time() < self.reg[user.id]["FIN_PEINE"] or self.reg[user.id]["FIN_PEINE"] != None:
                            await asyncio.sleep(1)
                        if user in server.members:
                            if role in [r.name for r in user.roles]:
                                self.reg[user.id]["DEB_PEINE"] = self.reg[user.id]["FIN_PEINE"] = None
                                self.new_event("out", user.id, "auto")
                                await self.bot.remove_roles(user, apply)
                                await self.bot.send_message(chanp, "{} **est libre**".format(user.mention))
                                self.save()
                            else:
                                return
                        else:
                            await self.bot.send_message(chanp, "{} ne peut être libéré de prison car il n'est plus sur ce serveur.".format(save))

def check_folders():
    folders = ("data", "data/just/")
    for folder in folders:
        if not os.path.exists(folder):
            print("Création du fichier " + folder)
            os.makedirs(folder)

def check_files():
    default = {"ROLE_PRISON": "Prison"}
    if not os.path.isfile("data/just/reg.json"):
        fileIO("data/just/reg.json", "save", {})
    if not os.path.isfile("data/just/sys.json"):
        fileIO("data/just/sys.json", "save", default)

def setup(bot):
    check_folders()
    check_files()
    n = Just(bot)
    bot.add_listener(n.renew, "on_member_join")
    bot.add_cog(n)