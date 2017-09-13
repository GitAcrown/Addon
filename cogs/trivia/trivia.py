import discord
from discord.ext import commands
from .utils.dataIO import dataIO, fileIO
from .utils import checks
import time
import random
import os
import aiohttp
import asyncio
import operator

class Trivia:
    """Trivia | Refonte 2017 du jeu de questions/réponses (Compatible Bitkhey)"""
    def __init__(self, bot):
        self.bot = bot
        self.data = dataIO.load_json("data/trivia/data.json")
        self.trv = dataIO.load_json("data/trivia/trv.json")
        self.sys = dataIO.load_json("data/trivia/sys.json")

    def charge(self, liste):
        titre = liste.upper()
        div = "data/trivia/listes/{}.txt".format(liste)
        if titre in self.data:
            if os.path.isfile(div):
                with open(div, "r", encoding="UTF-8") as f:
                    liste = f.readlines()
                if liste:
                    self.trv = {}
                    n = 0
                    for qr in liste:
                        if "?" in qr:
                            n += 1
                            qr = qr.replace("\n", "")
                            lqr = qr.split("?")
                            question = lqr[0] + "?"
                            reponses = [r[:-1] if r.endswith(" ") else r for r in lqr[1].split(";")]
                            reponses = [r[1:] if r.startswith(" ") else r for r in reponses]
                            reponses = [self.normal(r).lower() for r in reponses]
                            self.trv[n] = {"QUESTION": question,
                                           "REPONSES": reponses}
                    fileIO("data/trivia/trv.json", "save", self.trv)
                    f.close()
                    return True
        return False

    def normal(self, txt):
        ch1 = "àâçéèêëîïôùûüÿ"
        ch2 = "aaceeeeiiouuuy"
        s = ""
        for c in txt:
            i = ch1.find(c)
            if i >= 0:
                s += ch2[i]
            else:
                s += c
        return s

    def leven(self, s1, s2):
        if len(s1) < len(s2):
            m = s1
            s1 = s2
            s2 = m
        if len(s2) == 0:
            return len(s1)
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[
                                 j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]

    def positif(self):
        r = ["Bien joué", "Excellent", "Génial", "Bravo", "GG"]
        return random.choice(r)

    def list_exist(self, rub):
        if not rub:
            return False
        if rub.upper() not in self.data:
            return False
        div = "data/trivia/listes/{}.txt".format(rub)
        return os.path.isfile(div)

    def check(self, msg: discord.Message):
        if msg.author == self.bot.user:
            return False
        self.sys["INACTIF"] = time.time() + 60
        ch = self.sys["NOMBRE"]
        if self.normal(msg.content.lower()) in [self.normal(r.lower()) for r in self.trv[ch]["REPONSES"]]:
            return True
        else:
            return False

    def reset(self):
        self.trv = {}
        self.sys["ON"] = False
        self.sys["CHANNELID"] = None
        fileIO("data/trivia/trv.json", "save", self.trv)
        fileIO("data/trivia/sys.json", "save", self.sys)
        fileIO("data/trivia/data.json", "save", self.data)
        return True

    def top_gg(self, joueurs):
        l = [[r, joueurs[r]["POINTS"]] for r in joueurs]
        sort = sorted(l, key=operator.itemgetter(1), reverse=True)
        return sort

    def classlist(self):
        md = []
        for l in self.data:
            if "LIKES" not in self.data[l]:
                self.data[l]["LIKES"] = 0
            md.append([l.capitalize(), self.data[l]["LIKES"]])
        result = sorted(md, key=operator.itemgetter(1), reverse=True)
        return result

    @commands.command(pass_context=True)
    async def triviareset(self, ctx):
        """Permet de reset le trivia en cas de problèmes"""
        if self.reset():
            await self.bot.say("Reset effectué")
        else:
            await self.bot.say("Impossible d'effectuer un reset, les fichiers sont corrompus...")

    @commands.command(pass_context=True)
    async def triviasup(self, ctx, nom):
        """Permet de supprimer une liste"""
        nomt = nom.upper()
        if nomt in self.data:
            del self.data[nomt]
        div = "data/trivia/listes/{}.txt".format(nom)
        if os.path.exists(div):
            os.remove(div)
        await self.bot.say("Liste supprimée avec succès !")
        fileIO("data/trivia/data.json", "save", self.data)

    @commands.command(pass_context=True, hidden=True)
    async def triviaadd(self, ctx, *descr: str):
        """Permet d'ajouter une liste Trivia"""
        descr = " ".join(descr)
        attach = ctx.message.attachments
        if len(attach) > 1:
            await self.bot.say("Vous ne pouvez ajouter qu'une seule liste à la fois.")
            return
        if attach:
            a = attach[0]
            url = a["url"]
            filename = a["filename"]
            nom = filename.replace(".txt", "")
            auteur = ctx.message.author.name
        else:
            await self.bot.say("Uploadez le fichier en même temps que vous faîtes la commande.")
            return
        filepath = os.path.join("data/trivia/listes/", filename)
        if not ".txt" in filepath:
            await self.bot.say("Le format du fichier n'est pas correct. Utilisez un .txt")
            return
        if os.path.splitext(filename)[0] in os.listdir("data/trivia/listes"):
            await self.bot.reply("Une liste avec ce nom est déjà disponible.")
            return

        async with aiohttp.get(url) as new:
            f = open(filepath, "wb")
            f.write(await new.read())
            f.close()
        self.data[nom.upper()] = {"NOM": nom,
                                  "AUTEUR": auteur,
                                  "DESCR": descr,
                                  "LIKES": 0}
        fileIO("data/trivia/data.json", "save", self.data)
        await self.bot.say("Liste ajoutée avec succès !")

    @commands.command(pass_context=True, no_pm=True)
    async def trivia(self, ctx, liste: str = None, maxpts: int = 5):
        """Démarre un trivia avec la liste spécifiée"""
        server = ctx.message.server
        bit = self.bot.get_cog('Mirage').api
        if server.id != "328632789836496897":
            await self.bot.say("**JEU EN BETA** | Vous ne pouvez y jouer que sur le serveur AlphaTest ! (MP Acrown pour y accéder)")
            return
        if self.list_exist(liste):
            nom = liste.upper()
            if not self.trv and self.sys["ON"] is False:
                if 5 <= maxpts <= 30:
                    gain = True if server.id == "328632789836496897" else False
                    if gain is False:
                        await self.bot.say("**Vous êtes sur AlphaTest, vous n'êtes donc pas éligible aux gains**")
                        await asyncio.sleep(1)
                    joueurs = {}
                    joueurs[ctx.message.author.id] = {"POINTS": 0,
                                                      "REPONSES": []}
                    if self.charge(liste) is False:
                        await self.bot.say("Impossible de charger la liste...")
                        return
                    self.sys["ON"] = True
                    self.sys["CHANNELID"] = ctx.message.channel.id
                    self.sys["NOMBRE"] = None
                    param = self.data[nom]
                    fileIO("data/trivia/sys.json", "save", self.sys)
                    self.sys["INACTIF"] = time.time() + 90
                    while self.top_gg(joueurs)[0][1] < maxpts and time.time() <= self.sys["INACTIF"]:
                        ch = random.choice([r for r in self.trv])
                        self.sys["NOMBRE"] = ch
                        msg = "**{}**".format(self.trv[ch]["QUESTION"])
                        em = discord.Embed(title="TRIVIA | {}".format(param["NOM"].capitalize()), description=msg, color=0x38e39a)
                        em.set_footer(text="Liste par {} | {}".format(param["AUTEUR"], param["DESCR"]))
                        menu = await self.bot.say(embed=em)
                        rep = await self.bot.wait_for_message(channel=ctx.message.channel, timeout=20,
                                                              check=self.check)
                        if rep == None:
                            bef = random.choice(["Vraiment ? C'est","Facile ! C'était", "Sérieusement ? C'était"
                                                 , "Aucune idée ? C'est", "Pas trouvé ? Tout le monde sait que c'est"
                                                 , "Décevant... C'était"])
                            aft = random.choice(["évidemment...", "!", "enfin !", "!!!1!", "..."])
                            msg = "{} **{}** {}".format(bef, self.trv[ch]["REPONSES"][0].title(), aft)
                            em = discord.Embed(title="TRIVIA | {}".format(param["NOM"].capitalize()), description=msg,
                                               color=0xe33838)
                            em.set_footer(text="Liste par {} | {}".format(param["AUTEUR"], param["DESCR"]))
                            menu = await self.bot.say(embed=em)
                            del self.trv[ch]
                            await asyncio.sleep(3)
                        elif self.normal(rep.content.lower()) in [self.normal(r.lower()) for r in self.trv[ch][
                            "REPONSES"]]:
                            # On note l'auteur et on lui attribue un point
                            gagn = rep.author
                            win = random.choice(["Bien joué **{}** !", "Bien évidemment **{}** !", "GG **{}** !", "C'est exact **{}** !",
                                                 "C'est ça **{}** !", "Ouais ouais ouais **{}** !"])
                            await self.bot.say("{} C'était bien *{}* !".format(win.format(gagn.name), self.trv[ch]["REPONSES"][0].title()))
                            if gagn.id not in joueurs:
                                joueurs[gagn.id] = {"POINTS" : 1,
                                                    "REPONSES" : [rep.content]}
                            else:
                                joueurs[gagn.id]["POINTS"] += 1
                                joueurs[gagn.id]["REPONSES"].append(rep.content)
                            del self.trv[ch]
                            await asyncio.sleep(2)
                        else:
                            await self.bot.say("Problème WHILE /!\\")
                            pass
                    if self.top_gg(joueurs)[0][1] == maxpts:
                        top = self.top_gg(joueurs)
                        msg = ""
                        for p in top:
                            msg += "**{}** - *{}*\n".format(server.get_member(p[0]).name, p[1])
                        msg += "\n**Gagnant:** {}".format(server.get_member(top[0][0]).name)
                        em = discord.Embed(title="TRIVIA | TERMINÉ", description=msg, color=0x3b84b1)
                        em.set_footer(text="Vous aimez cette liste ? Laissez un Like !")
                        fin = await self.bot.say(embed=em)
                        await self.bot.add_reaction(fin, "👍")
                        await asyncio.sleep(1)
                        timeout = time.time() + 20
                        while time.time() <= timeout:
                            like = await self.bot.wait_for_message("👍", channel=ctx.message.channel, timeout=20)
                            if like:
                                if "LIKES" in self.data[nom]:
                                    self.data[nom]["LIKES"] += 1
                                else:
                                    self.data[nom]["LIKES"] = 1
                        em.set_footer(text="Merci d'avoir participé à cette Beta !")
                        await self.bot.edit_message(fin, embed=em)
                        self.reset()
                        return
                    elif time.time() >= self.sys["INACTIF"]:
                        await self.bot.say("Allo ? Il semblerait qu'il n'y ai plus personne...\n**Arrêt de la partie**")
                        self.reset()
                        return
                    else:
                        await self.bot.say("**[Haxx]** Un problème à eu lieu. Arrêt automatique de la partie... :(")
                        self.reset()
                        return
                else:
                    await self.bot.say("Le nombre de points nécéssaire pour gagner doit être compris entre 5 et 30.")
            else:
                await self.bot.say("Il semblerait qu'une partie soit déjà en cours")
        else:
            msg = ""
            l = self.classlist()
            for r in l:
                msg += "**{}** - {}\n".format(r[0], r[1])
            em = discord.Embed(title="TRIVIA | LISTES", description=msg, color=0x202020)
            em.set_footer(text="Classées par ordre de préférence")
            await self.bot.say(embed=em)

def check_folders():
    if not os.path.exists("data/trivia/"):
        print("Creation du dossier Trivia...")
        os.makedirs("data/trivia")
    if not os.path.exists("data/trivia/listes/"):
        print("Creation du dossier Trivia/Listes...")
        os.makedirs("data/trivia/listes/")


def check_files():
    default = {}
    if not os.path.isfile("data/trivia/data.json"):
        print("Création du fichier Trivia/Data")
        fileIO("data/trivia/data.json", "save", {})
    if not os.path.isfile("data/trivia/trv.json"):
        print("Création du fichier Trivia/Trv)")
        fileIO("data/trivia/trv.json", "save", {})
    if not os.path.isfile("data/trivia/sys.json"):
        print("Création du fichier Trivia/Sys")
        fileIO("data/trivia/sys.json", "save", {})


def setup(bot):
    check_folders()
    check_files()
    n = Trivia(bot)
    bot.add_cog(n)