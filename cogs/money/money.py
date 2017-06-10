import asyncio
import os
import random
from .utils import checks
from copy import deepcopy
import discord
import time
from collections import namedtuple
from __main__ import send_cmd_help
from discord.ext import commands
import time
import operator
from .utils.dataIO import fileIO, dataIO

class MoneyAPI:
    """API Money / Système monétaire du serveur"""
    def __init__(self, bot, path):
        self.bot = bot
        self.account = dataIO.load_json(path)
        self.account_type = [["Classique", 0], ["Plus", 250], ["Premium", 1000]]

    def save(self): #Sauvegarde l'ensemble des données bancaires
        fileIO("data/money/account.json", "save", self.account)
        return True

    def log(self, user):
        if user.id in self.account:
            return self.convert(user)
        else:
            self.account[user.id] = {"ID": user.id,
                                     "SOLDE": 0,
                                     "TYPE": "Classique",
                                     "SPECS": {}}
            self.save()
            return self.convert(user)

    def convert(self, user):
        Profil = namedtuple('Profil', ['id', 'solde', "type", "specs"])
        id = user.id
        solde = self.account[user.id]["SOLDE"]
        specs = self.account[user.id]["SPECS"]
        type = self.account[user.id]["TYPE"]
        return Profil(id, solde, type, specs)

    def historique(self, user, top=3):
        acc = self.log(user)
        if "HISTORIQUE" not in acc.specs:
            self.account[user.id]["SPECS"]["HISTORIQUE"] = []
        hist = self.account[user.id]["SPECS"]["HISTORIQUE"]
        met = hist[-top:]
        met.reverse()
        return met

    def type(self, user):
        acc = self.log(user)
        for a in self.account_type:
            if acc.type == a[0]:
                return a

    def reset_minage(self, user):
        self.log(user)
        self.account[user.id]["SPECS"]["MINAGE"]["DAY"] = time.strftime("%d", time.gmtime())
        self.account[user.id]["SPECS"]["MINAGE"]["NB"] = 0
        self.save()

    def gen_top(self, user, top:int =10):
        liste = []
        for p in self.account:
            liste.append([self.account[p]["SOLDE"], self.account[p]["ID"]])
            if self.account[p]["ID"] == user.id:
                k = [self.account[p]["SOLDE"], self.account[p]["ID"]]
        sort = sorted(liste, key=operator.itemgetter(0), reverse=True)
        place = sort.index(k)
        sort = sort[:top]
        return [sort, place]

#TRANSACTIONS

    def can_do(self, user, somme): #MR. MEESEEKS - LOOK AT ME !
        solde = self.log(user).solde
        autorise = 0 - self.type(user)[1]
        if (solde - somme) >= autorise:
            return True
        else:
            return False

    def add_solde(self, user, somme:int, raison:str=None):
        self.log(user)
        self.account[user.id]["SOLDE"] += somme
        if raison != None:
            if "HISTORIQUE" not in self.account[user.id]["SPECS"]:
                self.account[user.id]["SPECS"]["HISTORIQUE"] = []
            self.account[user.id]["SPECS"]["HISTORIQUE"].append(["+", somme, raison])
        self.save()
        return True

    def sub_solde(self, user, somme:int, raison:str=None):
        self.log(user)
        if self.can_do(user, somme):
            self.account[user.id]["SOLDE"] -= somme
            if raison != None:
                if "HISTORIQUE" not in self.account[user.id]["SPECS"]:
                    self.account[user.id]["SPECS"]["HISTORIQUE"] = []
                self.account[user.id]["SPECS"]["HISTORIQUE"].append(["-", somme, raison])
            self.save()
            return True
        else:
            return False

    def set_solde(self, user, somme:int, raison:str=None):
        self.log(user)
        if somme > (0 - self.type(user)[1]):
            self.account[user.id]["SOLDE"] = somme
            if raison != None:
                if "HISTORIQUE" not in self.account[user.id]["SPECS"]:
                    self.account[user.id]["SPECS"]["HISTORIQUE"] = []
                self.account[user.id]["SPECS"]["HISTORIQUE"].append(["!", somme, raison])
            self.save()
            return True
        else:
            return False

    def trans_solde(self, emmeteur, receveur, somme:int, raison:str=None):
        self.log(receveur)
        self.log(emmeteur)
        message1 = "Transfert à {}".format(receveur.name)
        message2 = "Reçu de {}".format(emmeteur.name)
        if raison != None:
            message1 += " ({})".format(raison)
            message2 += " ({})".format(raison)
        if self.sub_solde(emmeteur, somme, message1) != False:
            self.add_solde(receveur, somme, message2)
            return True
        else:
            return False

class Money:
    """Money : Système monétaire"""

    def __init__(self, bot):
        self.bot = bot
        self.money = MoneyAPI(bot, "data/money/account.json")

    @commands.command(pass_context=True)
    async def compte(self, ctx, user:discord.Member = None):
        """Permet de voir votre compte monétaire où celui d'un autre membre."""
        if user is None:
            user = ctx.message.author
            qui = "Votre Compte"
        else:
            qui = "Compte de {}".format(user.name)
        acc = self.money.log(user)
        em = discord.Embed(color=user.color)
        em.set_author(name="BitKhey | {}".format(qui), icon_url="http://i.imgur.com/nJJjoPG.png") #Cimer Lord pour le nom de la monnaie
        em.set_thumbnail(url=user.avatar_url)
        em.add_field(name="Solde", value="**{}** BK".format(acc.solde))
        type = self.money.type(user)
        em.add_field(name="Type de compte", value="{}".format(type[0]))
        hist = ""
        liste = self.money.historique(user)
        if liste != []:
            for i in liste:
                hist += "{}**{}** | *{}*\n".format(i[0], i[1], i[2])
        else:
            hist = "Aucune action enregistrée"
        em.add_field(name="Historique", value="{}".format(hist))
        stamp = time.strftime("Le %d/%m/%Y à %H:%M", time.localtime())
        em.set_footer(text=stamp)
        await self.bot.say(embed=em)

    @commands.command(aliases = ["lb"], pass_context=True)
    async def leaderboard(self, ctx, top:int = 10):
        """Affiche un top des membres les plus riches"""
        author = ctx.message.author
        server = ctx.message.server
        sort = self.money.gen_top(author, top)
        place = sort[1]
        em = discord.Embed(color=author.color, title="BitKhey | Les plus riches")
        msg = ""
        n = 1
        for p in sort[0]:
            user = server.get_member(p[1])
            msg += "{} | *{}*\n".format(n, str(user))
            n += 1
        em.add_field(name="Top {}".format(top), value=msg)
        em.add_field(name="Votre place", value="{}e".format(place + 1))
        stamp = time.strftime("Au %d/%m/%Y à %H:%M", time.localtime())
        em.set_footer(text=stamp)
        await self.bot.say(embed=em)

    @commands.group(name="bit", pass_context=True)
    async def _bit(self, ctx):
        """Opérations bancaires BitKhey"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @_bit.command(aliases = ["t"], pass_context=True, no_pm=True)
    async def transfert(self, ctx, user: discord.Member, somme:int, raison:str = None):
        """Permet de transférer une certaine somme d'argent à un membre.
        
        Il est possible de donner une raison à ce don en spécifiant après <somme>."""
        author = ctx.message.author
        solde = self.money.log(author).solde
        if somme <= (solde / 3):
            self.money.trans_solde(author, user, somme, raison)
            await self.bot.say("**Transfert réalisé avec succès**")
            if raison:
                if raison.lower() == "anniversaire":
                    await asyncio.sleep(3)
                    await self.bot.say("Et bon anniversaire {} !".format(user.mention))
        else:
            max = solde / 3
            await self.bot.say("Impossible de faire cet transaction.\n"
                               "{} Vous ne pouvez transférer qu'un tiers de votre solde au maximum. ({} BK)".format(author.mention, max))

    @_bit.command(aliases = ["r"], pass_context=True, no_pm=True)
    async def recolte(self, ctx):
        """Permet de récupérer les BitKhey minés aujourd'hui.
        
        Attention : Si vous ne récupérez pas tous les jours vos fragments, ils sont perdus."""
        author = ctx.message.author
        specs = self.money.log(author).specs["MINAGE"]
        if specs["DAY"] == time.strftime("%d", time.gmtime()):
            somme = int(round(specs["NB"] / 6, 0))
            frag = specs["NB"]
            self.money.add_solde(author, somme, "Récolte minage")
            self.money.reset_minage(author)
            await self.bot.say("Vous avez {} fragments.\nVous récoltez **{}** BK".format(frag, somme))
        else:
            await self.bot.say("**Récolte d'hier** (Malus -75% pour récolte tardive)\nVous avez {} fragments. Vous avez donc **{}** BK".format(frag, somme))
            somme = int(round(specs["NB"] / 10, 0))
            frag = specs["NB"]
            self.money.add_solde(author, somme, "Récolte minage")
            self.money.reset_minage(author)

    @_bit.command(pass_context=True, no_pm=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def edit(self, ctx, user: discord.Member, mode:str, somme:int, raison:str = None):
        """Permet d'éditer le solde d'une personne.
        Modes:
        '+' = Ajouter une somme
        '-' = Retirer une somme
        '!' = Régler le solde à cette somme"""
        acc = self.money.log(user)
        if raison == None:
            raison = "Edition par le Staff"
        if mode == "+":
            self.money.add_solde(user, somme, raison)
            await self.bot.say("Réalisé avec succès.")
        elif mode == "-":
            if self.money.sub_solde(user, somme, raison):
                await self.bot.say("Réalisé avec succès.")
            else:
                await self.bot.say("Impossible, c'est inférieur au seuil minimum de son compte (Découvert compris).")
        elif mode == "!":
            if self.money.set_solde(user, somme, raison):
                await self.bot.say("Réalisé avec succès.")
            else:
                await self.bot.say("Impossible, c'est inférieur au seuil minimum de son compte (Découvert compris).")
        else:
            await self.bot.say("Mode non reconnu.\n**Rappel:**\n'+' = Ajouter une somme\n'-' = Retirer une somme\n'!' = Régler le solde à cette somme")

    async def minage(self):
        while self == self.bot.get_cog('Money'):
            s = self.bot.get_server("204585334925819904")
            for m in s.members:
                if m.status != discord.Status.offline:
                    acc = self.money.log(m)
                    if "MINAGE" not in acc.specs:
                        acc.specs["MINAGE"] = {"DAY": time.strftime("%d", time.gmtime()), "NB": 0}
                    if acc.specs["MINAGE"]["DAY"] != time.strftime("%d", time.gmtime()):
                        acc.specs["MINAGE"]["DAY"] = time.strftime("%d", time.gmtime())
                        acc.specs["MINAGE"]["NB"] = 0
                    acc.specs["MINAGE"]["NB"] += 1
                    self.money.save()
            await asyncio.sleep(300)

def check_folders():
    if not os.path.exists("data/money"):
        print("Creation du dossier Money...")
        os.makedirs("data/money")

def check_files():
    if not os.path.isfile("data/money/account.json"):
        print("Creation du fichier de comptes bancaires...")
        fileIO("data/money/account.json", "save", {})

def setup(bot):
    check_folders()
    check_files()
    n = Money(bot)
    bot.loop.create_task(n.minage())
    bot.add_cog(n)