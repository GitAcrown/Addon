import discord
from discord.ext import commands
from .utils import checks
import asyncio
import os
import operator
from collections import namedtuple
import random
import time
import datetime
from copy import deepcopy
from .utils.chat_formatting import *
from cogs.utils.dataIO import fileIO, dataIO
from __main__ import send_cmd_help, settings

class Arc:
    """Fonctions Arcade"""
    def __init__(self, bot, path):
        self.prf = dataIO.load_json(path)
        self.bot = bot

    def new_prf(self, user):
        if user.id not in self.prf:
            self.prf[user.id] = {"PSEUDO": user.name,
                                   "ID": user.id,
                                   "SUC": [],
                                   "CONVOC": True,
                                   "CREDITS": 0}
            dataIO.save_json("data/arcade/profil.json", self.prf)
            return True
        else:
            return False

    def user_in(self, user):
        if user.id in self.prf:
            return True
        else:
            return False

    def get_profil(self, user):
        if user.id in self.prf:
            Profil = namedtuple('Profil', ['pseudo', 'id', 'succes', 'convoc', "credits"])
            pseudo = self.prf[user.id]["PSEUDO"]
            id = self.prf[user.id]["ID"]
            suc = self.prf[user.id]["SUC"]
            convoc = self.prf[user.id]["CONVOC"]
            credits = self.prf[user.id]["CREDITS"]
            return Profil(pseudo, id, suc, convoc, credits)
        else:
            self.new_prf(user)
            Profil = namedtuple('Profil', ['pseudo', 'id', 'succes', 'convoc', "credits"])
            pseudo = self.prf[user.id]["PSEUDO"]
            id = self.prf[user.id]["ID"]
            suc = self.prf[user.id]["SUC"]
            convoc = self.prf[user.id]["CONVOC"]
            credits = self.prf[user.id]["CREDITS"]
            return Profil(pseudo, id, suc, convoc, credits)

    def set_credits(self, user, sum: int):
        if user.id in self.prf:
            self.prf[user.id]["CREDITS"] = sum
            dataIO.save_json("data/arcade/profil.json", self.prf)
        else:
            return False

    def add_credits(self, user, sum: int):
        if user.id in self.prf:
            self.prf[user.id]["CREDITS"] += sum
            dataIO.save_json("data/arcade/profil.json", self.prf)
        else:
            return False

    def sub_credits(self, user, sum: int):
        if user.id in self.prf:
            self.prf[user.id]["CREDITS"] -= sum
            dataIO.save_json("data/arcade/profil.json", self.prf)
        else:
            return False

    def set_convoc(self, user, val: bool):
        if user.id in self.prf:
            self.prf[user.id]["CONVOC"] = val
            dataIO.save_json("data/arcade/profil.json", self.prf)
        else:
            return False

    def find_adv(self, server, exc = []):
        liste = []
        for member in server.members:
            if member.id in self.prf:
                if not member.id in exc:
                    if self.prf[member.id]["CONVOC"] == True:
                        liste.append(member.id)
        else:
            rand = random.choice(liste)
            return rand

class Arcade:
    """Regroupe les jeux du serveur."""
    def __init__(self, bot):
        self.bot = bot
        self.arc = Arc(bot, "data/arcade/profil.json")

    @commands.command(aliases= ["mini"],pass_context=True, no_pm=True)
    async def vg(self, ctx):
        """Regroupe les jeux compatibles Arc."""
        author = ctx.message.author
        if not self.arc.user_in(author):
            self.arc.new_prf(author)
            await self.bot.whisper(
                "**Vous autorisez désormais le bot à vous convoquer pour un jeu**\nCette option est désactivable dans les paramètres.")

        main = False
        while main is False:
            em = discord.Embed(title="Arc", color=0xDDDDDD)
            msg = "GW = Guess Who ?\n"
            msg += "----------------\n"
            msg += "S = Succès\n"
            msg += "P = Paramètres\n"
            msg += "Q = Quitter"
            em.add_field(name="Menu", value=msg)
            em.set_footer(text="Vous avez {} crédits.".format(self.arc.get_profil(author).credits))
            menu = await self.bot.whisper(embed=em)
            verif1 = False
            while verif1 != True:
                rep = await self.bot.wait_for_message(author=author, channel=menu.channel, timeout=45)
                if rep == None:
                    return

                elif rep.content.lower() == "gw":
                    verif1 = True
                    em = discord.Embed(title="Guess Who ?", color=0xDC3737)
                    em.add_field(name="But",
                                 value="Votre but est de retrouver le pseudo de votre correspondant secret en 3 essais grâce à 3 indices qu'il vous donne sur lui.\n")
                    em.add_field(name="Nb de joueurs", value="2")
                    em.set_thumbnail(url="http://i.imgur.com/ttYSoBw.png")
                    sousmenu = await self.bot.whisper(embed=em)
                    await self.bot.add_reaction(sousmenu, "✔")
                    await self.bot.add_reaction(sousmenu, "✖")
                    await asyncio.sleep(0.25)
                    rap = await self.bot.wait_for_reaction(["✔", "✖"], message=sousmenu, user=author, timeout=60)
                    if rap == None:
                        await self.bot.whisper("*Retour au menu*")
                    elif rap.reaction.emoji == "✔":
                        await asyncio.sleep(0.5)
                        new_message = deepcopy(ctx.message)
                        new_message.content = ctx.prefix + "guess"
                        await self.bot.process_commands(new_message)
                        return
                    else:
                        pass

                elif rep.content.lower() == "s":
                    verif1 = True
                    em = discord.Embed(title="Arc", color=0xDDDDD)
                    msg = ""
                    for m in self.arc.get_profil(author).succes:
                        msg += "*{}* - {}\n".format(m[0].title(), m[1])
                    if msg != "":
                        em.add_field(name="Vos succès", value=msg)
                    else:
                        em.add_field(name="Vos succès", value="Vous n'avez pas encore de succès.")
                    em.set_footer(text="Vous gagnez des succès lors des parties des jeux compatibles Arcade.")
                    await self.bot.whisper(embed=em)
                    await asyncio.sleep(2)

                elif rep.content.lower() == "p":
                    verif1 = True
                    param = False
                    while param is False:
                        em = discord.Embed(title="Arc", color=0xDDDDD)
                        msg = "C = Convocation pour jouer\n"
                        msg += "N = Rôle @Play\n"
                        msg += "----------------\n"
                        msg += "R = Retour menu"
                        em.add_field(name="Paramètres", value=msg)
                        em.set_footer(text="Tapez le tag correspondant à votre choix pour continuer...")
                        submenu = await self.bot.whisper(embed=em)
                        verif2 = False
                        while verif2 != True:
                            rep = await self.bot.wait_for_message(author=author, channel=submenu.channel, timeout=45)
                            if rep == None:
                                return
                            elif rep.content.lower() == "c":
                                verif2 = True
                                await self.bot.whisper("Voulez-vous être convoqué pour jouer à des jeux que les autres memrbes ont lancés ? (O/N)")
                                need = False
                                while need == False:
                                    ans = await self.bot.wait_for_message(author=author, channel=submenu.channel, timeout=30)
                                    if ans == None:
                                        await self.bot.whisper("*Retour paramètres*")
                                        need = True
                                    elif ans.content.lower() == "o":
                                        await self.bot.whisper("Vous pourrez être convoqué pour jouer.")
                                        self.arc.set_convoc(author, True)
                                        need = True
                                    elif ans.content.lower() == "n":
                                        await self.bot.whisper("Vous ne serez plus convoqué pour jouer.")
                                        self.arc.set_convoc(author, False)
                                        need = True
                                    else:
                                        await self.bot.whisper("Réponse invalide, réessayez.")
                            elif rep.content.lower() == "n":
                                verif2 = True
                                await asyncio.sleep(0.5)
                                new_message = deepcopy(ctx.message)
                                new_message.content = ctx.prefix + "playrole"
                                await self.bot.process_commands(new_message)
                                return

                            elif rep.content.lower() == "r":
                                verif2 = True
                                await self.bot.whisper("*Retour menu*")
                                param = True

                elif rep.content.lower() == "q":
                    await self.bot.whisper("Bye :wave:")
                    return

                else:
                    await self.bot.whisper("**Tag invalide.** Réessayez.")

    @commands.command(pass_context=True, no_pm=True)
    async def guess(self, ctx):
        """Arcade - Guess who ?

        Devinez votre correspondant secret !"""
        author = ctx.message.author
        server = ctx.message.server
        if not self.arc.user_in(author):
            await self.bot.whisper("Je vais vous créer un compte **Arc**...")
            self.arc.new_prf(author)
            await asyncio.sleep(1)
        msg = "**JEU** - *Guess who ?*\n"
        msg += "Ton but est de retrouver le pseudo de ton correspondant secret.\nIl va te donner 3 indices sur lui.\nEnsuite, tu devra deviner son pseudo."
        await self.bot.whisper(msg)
        reset = False
        while reset == False:
            okay = False
            while okay != True:
                ident = random.randint(1000, 9999)
                adv = server.get_member(self.arc.find_adv(server, [author.id]))
                await asyncio.sleep(1)
                await self.bot.whisper("**Connexion en cours avec un candidat potentiel...**")
                await asyncio.sleep(1)
                msg2 = "**JEU** - *Guess who ?*\n"
                msg2 += "Un correspondant secret doit deviner ton pseudo.\nTu va devoir lui donner 3 indices pour qu'il puisse te retrouver.\nVous gagnez si il le devine (Il est impératif de ne pas donner son pseudo dans ses messages)."
                try:
                    await self.bot.send_message(adv, msg2)
                    okay = True
                except:
                    await self.bot.whisper(
                        "**Votre correspondant semble m'avoir bloqué.**\nRecherche d'un nouveau correspondant...")
                    await asyncio.sleep(1)
            await asyncio.sleep(1.25)
            await self.bot.send_message(adv, "**Connexion en cours avec votre correspondant...**")
            await asyncio.sleep(2)
            bab = await self.bot.whisper(
                "**Correspondant connecté. (Partie #{})**\n*Il va vous donner 3 indices, à vous de retrouver son pseudo. Bonne chance !*".format(
                    ident))
            beb = await self.bot.send_message(adv,
                                              "**Correspondant connecté. (Partie #{})**\nTapez dès à présent votre premier indice.".format(
                                                  ident))
            nb = 0
            while nb < 3:
                rep = await self.bot.wait_for_message(author=adv, channel=beb.channel, timeout=180)
                if rep == None:
                    await self.bot.send_message(adv,
                                                "Vous n'avez pas répondu à temps. Partie annulée...")
                    back = await self.bot.whisper(
                        "**Le correspondant ({}) ne réponds pas.**\n*Voulez-vous un nouveau correspondant ? (o/n)*".format(
                            adv.name))
                    nep = await self.bot.wait_for_message(author=author, channel=back.channel,
                                                          timeout=60)
                    if nep == None:
                        await self.bot.whisper("Okay, bye :wave:")
                        return
                    elif nep.content.lower() == "o":
                        await self.bot.whisper("**Recherche d'un nouveau correspondant...**")
                        await asyncio.sleep(1)
                        nb = 3
                    else:
                        await self.bot.whisper("Okay, bye :wave:")
                        return
                elif adv.name.lower() in rep.content.lower():
                    await self.bot.whisper("Le correspondant à tenté de tricher. Partie annulée...")
                    await self.bot.send_message(adv,
                                                "Vous avez tenté de tricher. Partie annulée...")
                    return
                elif len(rep.content) > 3:
                    nb += 1
                    await self.bot.whisper("**Indice {}** - *{}*".format(nb, rep.content))
                    if nb < 3:
                        await self.bot.send_message(adv,
                                                    "**Indice {} transmis.**\nVous pouvez taper le prochain.".format(
                                                        nb))
                    else:
                        await asyncio.sleep(1)
                        await self.bot.send_message(adv,
                                                    "**Indice {} transmis.**\nLe correspondant doit désormais deviner votre identitée...".format(
                                                        nb))
                        await self.bot.whisper(
                            "Voilà, vous devez désormais deviner le pseudo de votre correspondant secret.(3 chances).\n"
                            "*Marquez simplement son pseudo (ou surnom) - Sachez qu'il ne peut être qu'Habitué, Oldfag ou Malsain.*")
                        chance = 0
                        while chance < 3:
                            ess = await self.bot.wait_for_message(author=author,
                                                                  channel=bab.channel, timeout=300)
                            if ess == None:
                                await self.bot.whisper(
                                    "Vous avez mis trop de temps à répondre. Partie annulée...")
                                await self.bot.send_message(adv,
                                                            "Votre correspondant est absent. Partie annulée...")
                                return
                            elif adv.name.lower() == ess.content.lower():
                                await self.bot.whisper(
                                    "**Bravo !** Votre correspondant était bien {} !".format(
                                        adv.name))
                                self.arc.add_credits(author, 1)
                                self.arc.add_credits(adv, 1)
                                await self.bot.send_message(adv,
                                                            "**Bien joué !** Votre correspondant ({}) vous a retrouvé !".format(
                                                                author.name))
                                return
                            elif adv.display_name.lower() == ess.content.lower():
                                await self.bot.whisper(
                                    "**Bravo !** Votre correspondant était bien {} !".format(
                                        adv.display_name))
                                await self.bot.send_message(adv,
                                                            "**Bien joué !** Votre correspondant ({}) vous a retrouvé !".format(
                                                                author.name))
                                return
                            else:
                                chance += 1
                                reste = 3 - chance
                                await self.bot.whisper(
                                    "Mauvaise réponse ! Vous avez encore {} chances.".format(reste))
                        await self.bot.whisper(
                            "**Perdu !** Votre correspondant était {}.".format(adv.name))
                        await self.bot.send_message(adv,
                                                    "**Dommage !** Votre correspondant était {}.".format(
                                                        author.name))
                        return
                else:
                    await self.bot.send_message(adv,
                                                "Vous devez saisir plus de 3 caractères pour envoyer un indice valide.")

def check_folders():
    folders = ("data", "data/arcade/")
    for folder in folders:
        if not os.path.exists(folder):
            print("Création du fichier " + folder)
            os.makedirs(folder)

def check_files():
    if not os.path.isfile("data/arcade/profil.json"):
        print("Création du fichier arcade/profil.json...")
        fileIO("data/arcade/profil.json", "save", {})

def setup(bot):
    check_folders()
    check_files()
    n = Arcade(bot)
    bot.add_cog(n)