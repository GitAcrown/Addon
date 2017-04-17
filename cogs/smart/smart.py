import discord
from discord.ext import commands
from .utils import checks
import asyncio
import os
import operator
import random
import time
import datetime
from .utils.chat_formatting import *
from cogs.utils.dataIO import fileIO, dataIO
from __main__ import send_cmd_help, settings

default = {"ACTIVE" : True}

class Smart:
    """Détecte et execute des commandes de manière contextuelle."""
    def __init__(self, bot):
        self.bot = bot
        self.sys = dataIO.load_json("data/smart/sys.json")
        self.ball = ["A ce que je vois, oui.", "C'est certain.", "J'hésite.", "Plutôt oui.", "Il semble que oui.",
                     "Les esprits penchent pour un oui.", "Sans aucun doute.", "Oui.", "Oui - C'est sûr.",
                     "Tu peux compter dessus.", "Je ne sais pas.",
                     "Ta question n'est pas très interessante...", "Je ne vais pas te le dire.","N'y comptes pas.", "Ma réponse est non.",
                     "Des sources fiables assurent que oui.", "J'en doute.","Non, clairement."]

    @commands.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(ban_members=True)
    async def togglesmart(self, val:bool = None):
        """Active ou désactive le système Smart"""
        if val == None:
            if self.sys["ACTIVE"] is True:
                self.sys["ACTIVE"] = False
                fileIO("data/smart/sys.json", "save", self.sys)
                await self.bot.say("Système Smart désactivé")
            else:
                self.sys["ACTIVE"] = True
                fileIO("data/smart/sys.json", "save", self.sys)
                await self.bot.say("Système Smart activé")
        else:
            self.sys["ACTIVE"] = val
            fileIO("data/smart/sys.json", "save", self.sys)
            await self.bot.say("Système Smart modifié")

    def appro(self, content:str, liste):
        for e in liste:
            if e in content:
                pass
            else:
                return False
        else:
            return True

    async def listen(self, message):
        mentions = message.mentions
        ct = message.content.lower()
        chan = message.channel
        if self.sys["ACTIVE"] is True:
            if len(mentions) == 1:
                if mentions[0].id == self.bot.user.id:
                    hors = ct.split()
                    hors.remove(hors[0])
                    if hors == []:
                        await self.bot.send_typing(chan)
                        await self.bot.send_message(chan, str(random.choice(["Oui ? Besoin d'un truc ?","Tu sais que tu va me saouler rapidement avec tes mentions toi.","MAIS QUOI BON SANG ?! :reee:", "Quoi ?","Oui je suis là","Que puis-je faire pour vous ?", "QUOI ENCORE ?!?", "Pourquoi vous me mentionnez ? Je suis pas votre ami.", "Vous avez besoin d'attention ou quoi ?", "Arrêtez de me mentionner svp; j'ai pas que ça à faire."])))
                    else:
                        question = " ".join(ct)
                        if question.endswith("?") and question != "?":
                            await self.bot.send_typing(chan)
                            await self.bot.send_message(chan, random.choice(self.ball))
                        else:
                            pass
            await asyncio.sleep(0.25)
            if self.appro(ct, ["what", "my", "purpose", "?"]):
                await self.bot.send_message(chan, "You pass butter.")
            elif self.appro(ct, ["oh", "my", "god"]):
                await self.bot.send_message(chan, "Yeah, welcome to the club, pal.")
            elif self.appro(ct, ["wubba","lubba","dub"]):
                await self.bot.send_message(chan, str(random.choice(["GRAAAAAASSSSSSS.... tastes bad.", "No jumping in the sewer!", "Wubbalubbadubdub!","Lick, lickity, lick my balls!"])))
            elif self.appro(ct, ["combien", "schmeckles", "dollars"]):
                wl = ct.split(" ")
                for w in wl:
                    if w.isdigit():
                        nb = int(w) * 148
                        await self.bot.send_message(chan, "Il semblerait que ça fasse environ {}$.".format(round(nb, 2)))
            elif self.appro(ct, ["combien", "schmeckles", "euros"]):
                wl = ct.split(" ")
                for w in wl:
                    if w.isdigit():
                        nb = (int(w) * 148) * 0.94
                        await self.bot.send_message(chan ,"Il semblerait que ça fasse environ {}€.".format(round(nb, 2)))
            elif self.appro(ct, ["combien", "dollars", "euros"]):
                wl = ct.split(" ")
                for w in wl:
                    if w.isdigit():
                        usd_to_eur = int(w)* 0.94
                        eur_to_usd = int(w)/ 0.94
                        await self.bot.send_message(chan ,"{}$ = {}€ | {}€ = {}$ (Environ)".format(int(w), round(usd_to_eur, 2), int(w), round(eur_to_usd, 2)))
            elif self.appro(ct, ["quel", "est", "id"]) or self.appro(ct, ["quoi", "id"]):
                if mentions != []:
                    if len(mentions) == 1:
                        await self.bot.send_message(chan, "L'ID de ce membre est {}".format(mentions[0].id))
            elif self.appro(ct, ["quoi","url", "avatar"]) or self.appro(ct, ["quel","url", "avatar"]):
                if mentions != []:
                    if len(mentions) == 1:
                        await self.bot.send_message(chan, "L'avatar de ce membre est disponible à cet URL : {}".format(mentions[0].avatar_url))
            elif self.appro(ct, ["quel", "jeu", "joue"]):
                if mentions != []:
                    if len(mentions) == 1:
                        if mentions[0].game is None:
                            await self.bot.send_message(chan, "Cet utilisateur ne joue pas")
                        else:
                            await self.bot.send_message(chan, "Il joue à *{}*".format(mentions[0].game))
            else:
                pass



def check_folders():
    folders = ("data", "data/smart/")
    for folder in folders:
        if not os.path.exists(folder):
            print("Création du fichier " + folder)
            os.makedirs(folder)

def check_files():
    if not os.path.isfile("data/smart/sys.json"):
        print("Création du fichier systeme Smart...")
        fileIO("data/smart/sys.json", "save", default)

def setup(bot):
    check_folders()
    check_files()
    n = Smart(bot)
    bot.add_listener(n.listen, "on_message")
    bot.add_cog(n)
