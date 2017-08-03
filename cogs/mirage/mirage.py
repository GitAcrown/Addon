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

class MirageAPI:
    """Système monétaire & gestionnaire de succès"""
    def __init__(self, bot, path):
        self.bot = bot
        self.bank = dataIO.load_json(path)
        self.cycle_task = bot.loop.create_task(self.regul())
        self.acc_type = [["Silver", 0],
                         ["Gold", 500],
                         ["Diamond", 2000],
                         ["Black", 5000]]

    async def regul(self):
        await self.bot.wait_until_ready()
        try:
            await asyncio.sleep(20)
            while True:
                for p in self.bot.get_all_members():
                    if p.id in self.bank:
                        if p.status != discord.Status.offline:
                            self.bank[p.id]["SOLDE"] += 2
                self.save()
                await asyncio.sleep(3600)  # Toutes les 24h
        except asyncio.CancelledError:
            pass

    def save(self):
        fileIO("data/mirage/bank.json", "save", self.bank)
        return True

    def open(self, user):
        """Retourne les informations du compte de l'utilisateur.

        Ouvre un compte si l'utilisateur n'en possède pas."""
        if user.id not in self.bank:
            clef = ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(6))
            self.bank[user.id] = {"CLEF_SECU": clef,
                                  "SOLDE": 20,
                                  "HISTORY": [],
                                  "TYPE": "Silver",
                                  "SUCCESS": [],
                                  "PLUS": {}}
            self.save()
        Bank = namedtuple('Bank', ['id', 'clef', "solde", "history", "type", "success", "plus"])
        id = user.id
        clef = self.bank[user.id]["CLEF_SECU"]
        solde = self.bank[user.id]["SOLDE"]
        hist = self.bank[user.id]["HISTORY"]
        acc = self.bank[user.id]["TYPE"]
        succ = self.bank[user.id]["SUCCESS"]
        plus = self.bank[user.id]["PLUS"]
        return Bank(id, clef, solde, hist, acc, succ, plus)

    def limit(self, user):
        """Renvoie une liste concernant le type de compte contenant:
        [0] Nom
        [1] Valeur minimale (en négatif)"""
        acc = self.open(user)
        for a in self.acc_type:
            if acc.type == a[0]:
                return a

    def enough(self, user, somme):
        """Renvoie un bool pour déterminer si l'opération peut se faire"""
        solde = self.open(user).solde
        min = 0 - self.limit(user)[1]
        if (solde - somme) >= min:
            return True
        else:
            return False

    def top(self, user, top: int = 10):
        liste = []
        for p in self.bank:
            liste.append([self.bank[p]["SOLDE"], p])
            if p == user.id:
                k = [self.bank[p]["SOLDE"], p]
        sort = sorted(liste, key=operator.itemgetter(0), reverse=True)
        place = sort.index(k)
        sort = sort[:top]
        return [sort, place]

    def _add(self, user, somme: int, raison=None):
        """Ajoute du solde à un utilisateur"""
        acc = self.open(user)
        acc.solde += somme
        acc.history.append(["+", somme, raison])
        self.save()
        return True

    def _sub(self, user, somme: int, raison=None):
        """Retire du solde à un utilisateur"""
        acc = self.open(user)
        if self.enough(user, somme):
            acc.solde -= somme
            acc.history.append(["-", somme, raison])
            self.save()
            return True
        else:
            return False

    def _set(self, user, somme: int, raison=None):
        """Règle le solde de l'utilisateur à une valeur précise"""
        acc = self.open(user)
        if somme >= (0 - self.limit(user)[1]):
            acc.solde = somme
            acc.history.append(["!", somme, raison])
            self.save()
            return True
        else:
            return False

class Mirage:
    """Mirage | Système monétaire et Gestionnaire de succès"""
    def __init__(self, bot):
        self.bot = bot
        self.api = MirageAPI(bot, "data/mirage/bank.json")

    @commands.command(pass_context=True)
    async def compte(self, ctx, user: discord.Member = None):
        """Permet de voir le compte BitKhey d'un membre."""
        if user is None:
            user = ctx.message.author
        acc = self.api.open(user)
        em = discord.Embed(color=user.color)
        em.set_author(name="BitKhey | {}".format("Votre compte" if user == ctx.message.author else user.name),
                      icon_url=user.avatar_url)  # Cimer Lord pour le nom de la monnaie
        em.add_field(name="Solde", value="**{}** BK".format(acc.solde))
        met = acc.history[-3:]
        if met != []:
            msg = ""
            met.reverse()
            for e in met:
                msg += "**{}*{}*** {}".format(e[0], e[1], e[2] if len(e[2]) < 30 else e[2][:29] + "...")
        else:
            msg = "Aucune action"
        em.add_field(name="Actions", value=msg)
        stamp = time.strftime("Le %d/%m/%Y à %H:%M", time.localtime())
        em.set_footer(text=stamp)
        await self.bot.say(embed=em)

    @commands.command(aliases=["lb"], pass_context=True, no_pm=True)
    async def leaderboard(self, ctx, top:int = 10):
        """Affiche un top X des personnes les plus riches et affiche votre place."""
        if top <= 0:
            await self.bot.say("**Erreur** | Le top doit être positif et supérieur à 0.")
            return
        author = ctx.message.author
        server = ctx.message.server
        sort = self.api.top(author, top)
        place = sort[1]
        em = discord.Embed(color=author.color, title="BitKhey | Les plus riches")
        msg = ""
        n = 1
        for p in sort[0]:
            user = server.get_member(p[1])
            msg += "{} | *{}*\n".format(n, user.name)
            n += 1
        if len(msg) > 1960:
            await self.bot.say("**Erreur** | Top trop elevé.")
            return
        em.add_field(name="Top {}".format(top), value=msg)
        em.add_field(name="Votre place", value="{}e".format(place + 1)) # On ajoute 1 parce qu'il compte à partir de 0
        await self.bot.say(embed=em)

    @commands.command(pass_context=True, no_pm=True)
    async def don(self, ctx, user: discord.Member, somme: int, *raison: str):
        """Permet de donner une certaine somme à un membre.

        La raison est obligatoire."""
        if somme < 1:
            await self.bot.say("**Erreur** | La somme transférée doit être positive et supérieure à 0")
            return
        author = ctx.message.author
        raison = " ".join(raison)
        if self.api._sub(author, somme, "Don à {}".format(user.name)):
            self.api._add(user, somme, raison)
            await self.bot.say("**Transfert réalisé avec succès.**")
        else:
            await self.bot.say("**Erreur** | Vous n'avez pas assez de fonds pour ce transfert.")

    @commands.command(aliases=["be"] ,pass_context=True, no_pm=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def bitedit(self, ctx, user: discord.Member, mode: str, somme: int, raison=None):
        """Permet d'éditer le solde d'une personne.
        Si la raison est composée de plusieurs mots, utilisez des guillemets.
        Modes:
        '+' = Ajouter une somme
        '-' = Retirer une somme
        '!' = Régler le solde à cette somme"""
        self.api.open(user)
        if raison is None:
            raison = "Edition par staff"
        if mode == "+":
            self.api._add(user, somme, raison)
            await self.bot.say("**Réalisé avec succès.**")
        elif mode == "-":
            if self.api._sub(user, somme, raison):
                await self.bot.say("**Réalisé avec succès.**")
            else:
                await self.bot.say("**Impossible**, c'est inférieur au seuil minimum de son compte (Découvert compris).")
        elif mode == "!":
            if self.api._set(user, somme, raison):
                await self.bot.say("**Réalisé avec succès.**")
            else:
                await self.bot.say("**Impossible**, c'est inférieur au seuil minimum de son compte (Découvert compris).")
        else:
            await self.bot.say(
                "**Mode non reconnu.**\n**Rappel:**\n'+' = Ajouter une somme\n'-' = Retirer une somme\n'!' = Régler le solde à cette somme")

def check_folders():
    if not os.path.exists("data/mirage"):
        print("Creation du dossier Mirage...")
        os.makedirs("data/mirage")

def check_files():
    if not os.path.isfile("data/mirage/bank.json"):
        print("Creation du fichier de Comptes Bancaires...")
        fileIO("data/mirage/bank.json", "save", {})

def setup(bot):
    check_folders()
    check_files()
    n = Mirage(bot)
    bot.add_cog(n)