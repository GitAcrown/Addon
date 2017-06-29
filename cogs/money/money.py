import asyncio
import os
from .utils import checks
import discord
from collections import namedtuple
from __main__ import send_cmd_help
from discord.ext import commands
import time
import operator
from .utils.dataIO import fileIO, dataIO

class MoneyAPI:
    """Système monétaire du serveur"""
    def __init__(self, bot, path):
        self.bot = bot
        self.bank = dataIO.load_json(path)
        self.account_type = [["C", 0, "Classique"],
                             ["B", 250, "Plus"],
                             ["A", 1000, "Premium"]]

    def save(self): # Sauvegarde l'ensemble des données bancaires
        fileIO("data/money/bank.json", "save", self.bank)
        return True

# GESTION COMPTE <<<<<<<<<<<<<<<

    def log(self, user):
        if user.id in self.bank:
            return self.convert(user)
        else:
            self.bank[user.id] = {"ID": user.id,
                                  "SOLDE": 0,
                                  "CARTE": "C", # Classique
                                  "HISTORY": []}
            self.save()
            return self.convert(user)

    def convert(self, user):
        Compte = namedtuple('Compte', ['id', 'solde', "carte", "history"])
        id = user.id
        solde = self.bank[user.id]["SOLDE"]
        carte = self.bank[user.id]["CARTE"]
        hist = self.bank[user.id]["HISTORY"]
        return Compte(id, solde, carte, hist)

    def histmaker(self, user, top=3):
        acc = self.log(user)
        met = acc.history[-top:]
        met.reverse()
        return met

    def cartetype(self, user):
        acc = self.log(user)
        for a in self.account_type:
            if acc.carte == a[0]:
                return a

    def enough(self, user, somme): #MR. MEESEEKS - LOOK AT ME !
        solde = self.log(user).solde
        autorise = 0 - self.cartetype(user)[1]
        if (solde - somme) >= autorise:
            return True
        else:
            return False

    def top(self, user, top: int = 10):
        liste = []
        for p in self.bank:
            liste.append([self.bank[p]["SOLDE"], self.bank[p]["ID"]])
            if self.bank[p]["ID"] == user.id:
                k = [self.bank[p]["SOLDE"], self.bank[p]["ID"]]
        sort = sorted(liste, key=operator.itemgetter(0), reverse=True)
        place = sort.index(k)
        sort = sort[:top]
        return [sort, place]

# TRANSACTIONS <<<<<<<<<<<

    def add_solde(self, user, somme:int, raison:str=None):
        self.log(user)
        self.bank[user.id]["SOLDE"] += somme
        if raison != None:
            self.bank[user.id]["HISTORY"].append(["+", somme, raison])
        self.save()
        return True

    def sub_solde(self, user, somme:int, raison:str=None):
        self.log(user)
        if self.enough(user, somme):
            self.bank[user.id]["SOLDE"] -= somme
            if raison != None:
                self.bank[user.id]["HISTORY"].append(["-", somme, raison])
            self.save()
            return True
        else:
            return False

    def set_solde(self, user, somme:int, raison:str=None):
        self.log(user)
        if somme > (0 - self.cartetype(user)[1]):
            self.bank[user.id]["SOLDE"] = somme
            if raison != None:
                self.bank[user.id]["HISTORY"].append(["!", somme, raison])
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
        if self.sub_solde(emmeteur, somme, message1) is True:
            self.add_solde(receveur, somme, message2)
            return True
        else:
            return False

class Money:
    """MoneyAPI | Système monétaire et suivi de l'économie"""
    def __init__(self, bot):
        self.bot = bot
        self.api = MoneyAPI(bot, "data/money/bank.json")

    @commands.command(pass_context=True)
    async def compte(self, ctx, user: discord.Member = None):
        """Permet de voir votre compte monétaire où celui d'un autre membre."""
        if user is None:
            user = ctx.message.author
            qui = "Votre Compte"
        else:
            qui = "Compte de {}".format(user.name)
        acc = self.api.log(user)
        em = discord.Embed(color=user.color)
        em.set_author(name="BitKhey | {}".format(qui),
                      icon_url="http://i.imgur.com/nJJjoPG.png")  # Cimer Lord pour le nom de la monnaie
        em.set_thumbnail(url=user.avatar_url)
        em.add_field(name="Solde", value="**{}** BK".format(acc.solde))
        type = self.api.cartetype(user)
        em.add_field(name="Type de compte", value="*{}* ({})".format(type[2], type[0]))
        hist = ""
        liste = self.api.histmaker(user)
        if liste != []:
            for i in liste:
                hist += "**{} {}** | *{}*\n".format(i[0], i[1], i[2])
        else:
            hist = "Aucun historique"
        em.add_field(name="Historique", value="{}".format(hist))
        stamp = time.strftime("Généré le %d/%m/%Y à %H:%M", time.localtime())
        em.set_footer(text=stamp)
        await self.bot.say(embed=em)

    @commands.command(aliases=["lb"], pass_context=True)
    async def leaderboard(self, ctx, top: int = 10):
        """Affiche un top des membres les plus riches"""
        author = ctx.message.author
        server = ctx.message.server
        sort = self.api.top(author, top)
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
        await self.bot.say(embed=em)

#OPERATIONS >>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<

    @commands.group(name="bit", aliases=["b"], pass_context=True)
    async def _bit(self, ctx):
        """Opérations bancaires BitKhey"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @_bit.command(aliases=["t"], pass_context=True, no_pm=True)
    async def transfert(self, ctx, user: discord.Member, somme: int, raison: str = None):
        """Permet de transférer une certaine somme d'argent à un membre.

        Il est possible de donner une raison à ce don en spécifiant après <somme>."""
        author = ctx.message.author
        solde = self.api.log(author).solde
        if somme <= (solde / 3):
            self.api.trans_solde(author, user, somme, raison)
            await self.bot.say("**Transfert réalisé avec succès**")
        else:
            max = solde / 3
            await self.bot.say("Impossible de faire cette transaction.\n"
                               "{} Vous ne pouvez transférer qu'un tiers de votre solde au maximum. ({} BK)".format(
                author.mention, max))

    @_bit.command(aliases=["e"], pass_context=True, no_pm=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def edit(self, ctx, user: discord.Member, mode: str, somme: int, raison=None):
        """Permet d'éditer le solde d'une personne.
        Si la raison est composée de plusieurs mots, utilisez des guillemets.
        Modes:
        '+' = Ajouter une somme
        '-' = Retirer une somme
        '!' = Régler le solde à cette somme"""
        acc = self.api.log(user)
        if raison != None:
            raison = " ".join(raison)
        else:
            raison = "Edition par autorité"
        if mode == "+":
            self.api.add_solde(user, somme, raison)
            await self.bot.say("Réalisé avec succès.")
        elif mode == "-":
            if self.api.sub_solde(user, somme, raison):
                await self.bot.say("Réalisé avec succès.")
            else:
                await self.bot.say("Impossible, c'est inférieur au seuil minimum de son compte (Découvert compris).")
        elif mode == "!":
            if self.api.set_solde(user, somme, raison):
                await self.bot.say("Réalisé avec succès.")
            else:
                await self.bot.say("Impossible, c'est inférieur au seuil minimum de son compte (Découvert compris).")
        else:
            await self.bot.say(
                "Mode non reconnu.\n**Rappel:**\n'+' = Ajouter une somme\n'-' = Retirer une somme\n'!' = Régler le solde à cette somme")

def check_folders():
    if not os.path.exists("data/money"):
        print("Creation du dossier Money...")
        os.makedirs("data/money")

def check_files():
    if not os.path.isfile("data/money/bank.json"):
        print("Creation du fichier de comptes bancaires...")
        fileIO("data/money/bank.json", "save", {})

def setup(bot):
    check_folders()
    check_files()
    n = Money(bot)
    bot.add_cog(n)
