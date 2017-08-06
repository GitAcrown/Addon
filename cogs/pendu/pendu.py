import asyncio
import os
from .utils import checks
import discord
from collections import namedtuple
from __main__ import send_cmd_help
from discord.ext import commands
import time
import operator
import random
import string
from .utils.dataIO import fileIO, dataIO

class Pendu:
    """Simple jeu du pendu (Compatible BitKhey V1)"""
    def __init__(self, bot):
        self.bot = bot
        self.data = dataIO.load_json("data/pendu/data.json")

    def choose(self, difficile = False):
        div = "data/pendu/dico.txt"
        if difficile is True:
            min = 6
        else:
            min = 4
        if os.path.isfile(div):
            with open(div, "r", encoding="UTF-8") as f:
                liste = f.readlines()
            deflist = []
            for i in liste:
                if len(i) >= min:
                    deflist.append(i)
            mot = random.choice(deflist)
            mot = mot.replace("\n", "")
            mot = mot.replace(" ", "")
            lettres = [r.upper() for r in mot]
            encode = [n for n in "-" * len(mot)]
            return [mot, lettres, encode]
        else:
            return False

    @commands.command(pass_context=True)
    async def pendu(self, ctx, hard: bool=False):
        """Démarre un jeu du pendu"""
        server = ctx.message.server
        bit = self.bot.get_cog('Mirage').api
        if self.data["PENDU_ON"] is False:
            await self.bot.say("**Génération du mot...**")
            await asyncio.sleep(1)
            self.data["JOUEURS"] = {}
            l = self.choose()
            if l is False:
                await self.bot.say("Le fichier /data/pendu/**dico.txt** est absent !")
                return
            self.data["VIES"] = 10 if hard is False else 5
            self.data["ENCODE"] = l[2]
            self.data["MOT"] = l[1]
            self.data["POINTS"] = len(l[1]) * 2
            soluce = l[0]
            self.data["PENDU_CHAN"] = ctx.message.channel.id
            self.data["PENDU_ON"] = True
            self.data["TIMEOUT"] = time.time() + 120
            await self.bot.say("**{}**\n*Vies restantes: {}*".format("".join(self.data["ENCODE"]), self.data["VIES"]))
            fileIO("data/pendu/data.json", "save", self.data)
            while self.data["VIES"] > 0 and "".join(self.data["ENCODE"]) != soluce and time.time() < self.data["TIMEOUT"] and self.data["PENDU_ON"] is True:
                await asyncio.sleep(1)
            if self.data["TIMEOUT"] < time.time():
                await self.bot.say("Eh, il y a quelqu'un ?\nJ'arrête la partie...")
                self.data["PENDU_ON"] = False
                fileIO("data/pendu/data.json", "save", self.data)
                return
            elif self.data["VIES"] == 0:
                await self.bot.say("**Echec** | Vous avez perdu\nLe mot était *{}*".format(soluce))
                for j in self.data["JOUEURS"]:
                    user = server.get_member(j)
                    som = self.data["JOUEURS"][j]["SOMMEMOINS"]
                    if bit._sub(user, som, "Prix de la défaite (Pendu)"):
                        await self.bot.send_message(user, "Vous perdez **{}** BK.".format(som))
                    else:
                        bit._set(user, 0, "Prix de la défaite (Pendu)")
                        await self.bot.send_message(user, "Votre compte bancaire est désormais **vide**.")
                self.data["PENDU_ON"] = False
                fileIO("data/pendu/data.json", "save", self.data)
                return
            elif "".join(self.data["ENCODE"]) == soluce:
                await self.bot.say("**Bien joué !** | C'était bien *{}*".format(soluce))
                for j in self.data["JOUEURS"]:
                    user = server.get_member(j)
                    som = self.data["JOUEURS"][j]["SOMMEPLUS"]
                    if bit._add(user, som, "Victoire (Pendu)"):
                        await self.bot.send_message(user, "Vous remportez **{}** BK.".format(som))
                    else:
                        await self.bot.send_message(user, "Vous n'avez pas de compte bancaire en 2017 !?\n"
                                                          "Je n'ai pas pu vous donner votre argent...")
                self.data["PENDU_ON"] = False
                fileIO("data/pendu/data.json", "save", self.data)
            else:
                print("PENDU > Erreur, la partie s'est terminée trop tôt.")
                await self.bot.say("*[Haxx]* Un **problème** dans mes **systèmes** m'a fait **arrêter** la partie "
                                   "**plus tôt** que prévu :(")
                self.data["PENDU_ON"] = False
                fileIO("data/pendu/data.json", "save", self.data)
                return
        else:
            await self.bot.say("Une partie est déjà en cours, je le sais...")

    def indexplus(self, mot, l):
        nb = mot.count(l)
        tr = []
        n = 0
        for e in mot:
            if e == l:
                tr.append(n)
                n += 1
            else:
                n += 1
        return tr

    async def l_msg(self, message):
        chan = self.bot.get_channel(self.data["PENDU_CHAN"])
        if self.data["PENDU_ON"] is True:
            if message.channel == chan:
                author = message.author
                if message.content.startswith("&") or message.content.startswith("!") or message.content.startswith(";;") or message.content.startswith("\\"):
                    return
                if message.content.lower() == "stop":
                    if author.server_permissions.manage_messages:
                        self.data["PENDU_ON"] = False
                        await self.bot.send_message(chan, "Arrêt...")
                        fileIO("data/pendu/data.json", "save", self.data)
                        return
                if author.id != self.bot.user.id:
                    if author.id not in self.data["JOUEURS"]:
                        self.data["JOUEURS"][author.id] = {"TROUVE": [],
                                                           "SOMMEPLUS": 0,
                                                           "SOMMEMOINS": 0}
                        fileIO("data/pendu/data.json", "save", self.data)
                    content = message.content.upper()
                    if len(content) < 2: # C'est une seule lettre
                        if content in self.data["MOT"]:
                            if content not in self.data["ENCODE"]: # Si on l'a déjà trouvée
                                places = self.indexplus(self.data["MOT"], content)
                                for i in places:
                                    self.data["ENCODE"][i] = content
                                    self.data["JOUEURS"][author.id]["SOMMEPLUS"] += 2
                                    self.data["POINTS"] -= 2
                                    self.data["JOUEURS"][author.id]["TROUVE"].append(content)
                                fileIO("data/pendu/data.json", "save", self.data)
                                await self.bot.send_message(chan, "+{} lettre(s) trouvé(es) !".format(len(places)))
                                self.data["TIMEOUT"] = time.time() + 120
                                if self.data["VIES"] > 0:
                                    await self.bot.send_message(chan, "**{}**\n*Vies restantes: {}*".format("".join(self.data["ENCODE"]),
                                                                                                            self.data["VIES"]))
                                else:
                                    return
                            else:
                                await self.bot.send_message(chan, "Vous avez déjà trouvé cette lettre !")
                                self.data["TIMEOUT"] = time.time() + 120
                                if self.data["VIES"] > 0:
                                    await self.bot.send_message(chan, "**{}**\n*Vies restantes: {}*".format("".join(self.data["ENCODE"]),
                                                                                                            self.data["VIES"]))
                                else:
                                    return
                        else:
                            self.data["JOUEURS"][author.id]["SOMMEMOINS"] += 1
                            self.data["VIES"] -= 1
                            await self.bot.send_message(chan, "**Loupé !**\n`-1 vie`")
                            fileIO("data/pendu/data.json", "save", self.data)
                            self.data["TIMEOUT"] = time.time() + 120
                            if self.data["VIES"] > 0:
                                await self.bot.send_message(chan, "**{}**\n*Vies restantes: {}*".format(
                                    "".join(self.data["ENCODE"]),
                                    self.data["VIES"]))
                            else:
                                return
                    else: # C'est un mot
                        if content == "".join(self.data["MOT"]):
                            self.data["ENCODE"] = self.data["MOT"]
                            self.data["JOUEURS"][author.id]["SOMMEPLUS"] += self.data["POINTS"]
                            self.data["JOUEURS"][author.id]["TROUVE"].append(content)
                            fileIO("data/pendu/data.json", "save", self.data)
                            return
                        else:
                            self.data["JOUEURS"][author.id]["SOMMEMOINS"] += 2
                            self.data["VIES"] -= 1
                            await self.bot.send_message(chan, "**Loupé !**\n`-1 vie`")
                            fileIO("data/pendu/data.json", "save", self.data)
                            self.data["TIMEOUT"] = time.time() + 120
                            await self.bot.send_message(chan, "**{}**\n*Vies restantes: {}*".format("".join(self.data["ENCODE"]),
                                                                                                    self.data["VIES"]))

def check_folders():
    if not os.path.exists("data/pendu/"):
        print("Creation du dossier Jeu du pendu...")
        os.makedirs("data/pendu")

def check_files():
    default = {"PENDU_CHAN": None,"POINTS": 0, "PENDU_ON" : False, "JOUEURS" : {}, "ENCODE": None, "MOT": None, "VIES": 10}
    if not os.path.isfile("data/pendu/data.json"):
        print("Création du fichier Jeu du pendu")
        fileIO("data/pendu/data.json", "save", default)

def setup(bot):
    check_folders()
    check_files()
    n = Pendu(bot)
    bot.add_cog(n)
    bot.add_listener(n.l_msg, "on_message")