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
        self.good = random.choice(["Oui !", "Exact !", "C'est ça !", "Bien joué !", "Absolument !"])
        self.neutre = random.choice(["Désolé !", "Oups...", "Euh ouais ?", "???"])
        self.bad = random.choice(["Loupé !", "Non !", "Dommage !", "C'est pas ça !", "Absolument...pas"])

    def bye(self):
        heure = int(time.strftime("%H", time.localtime()))
        if 6 <= heure <= 12:
            return "Bonne matinée !"
        elif 13 <= heure <= 17:
            return "Bonne après-midi !"
        elif 18 <= heure <= 22:
            return "Bonne soirée !"
        else:
            return "Bonne nuit !"

    def dessinpendu(self, etape):
        tp = ["──\n"
              "     |\n"
              "    |\n"
              "    |\n"
              "    |\n"
              "    |\n"
              "    |\n"
              "    |\n"
              "    |\n"
              "#####################\n",
              "──\n"
              "    |\n"
              "    |\n"
              "    |\n"
              "    |\n"
              "    |\n"
              "    |\n"
              "   [|\n"
              "  [ |\n"
              "#####################\n",
              "──\n"
              "    |\n"
              "    |\n"
              "    |\n"
              "    |\n"
              "    |\n"
              "    |\n"
              "   [|]\n"
              "  [ | ]\n"
              "#####################\n",
              "────────\n"
              "    |\n"
              "    |\n"
              "    |\n"
              "    |\n"
              "    |\n"
              "    |\n"
              "   [|]\n"
              "  [ | ]\n"
              "#####################\n",
              "────────\n"
              "    |  /\n"
              "    |/\n"
              "    |\n"
              "    |\n"
              "    |\n"
              "    |\n"
              "   [|]\n"
              "  [ | ]\n"
              "#####################\n",
              "────────\n"
              "    |  //\n"
              "    |//\n"
              "    |/\n"
              "    |\n"
              "    |\n"
              "    |\n"
              "   [|]\n"
              "  [ | ]\n"
              "#####################\n",
              "────────\n"
              "    |  //     |\n"
              "    |//       |\n"
              "    |/       (_)\n"
              "    |\n"
              "    |\n"
              "    |\n"
              "   [|]\n"
              "  [ | ]\n"
              "#####################\n",
              "────────\n"
              "    |  //     |\n"
              "    |//       |\n"
              "    |/       (_)\n"
              "    |           |\n"
              "    |\n"
              "    |\n"
              "   [|]\n"
              "  [ | ]\n"
              "#####################\n",
              "────────\n"
              "    |  //     |\n"
              "    |//       |\n"
              "    |/       (_)\n"
              "    |         /|\n"
              "    |           |\n"
              "    |\n"
              "   [|]\n"
              "  [ | ]\n"
              "#####################\n",
              "────────\n"
              "    |  //     |\n"
              "    |//       |\n"
              "    |/       (_)\n"
              "    |         /|\\\n"
              "    |           |\n"
              "    |\n"
              "   [|]\n"
              "  [ | ]\n"
              "#####################\n",
              "────────\n"
              "    |  //     |\n"
              "    |//       |\n"
              "    |/       (_)\n"
              "    |         /|\\\n"
              "    |           |\n"
              "    |         /\n"
              "   [|]\n"
              "  [ | ]\n"
              "#####################\n",
              "────────\n"
              "    |  //     |\n"
              "    |//       |\n"
              "    |/       (_)\n"
              "    |         /|\\\n"
              "    |           |\n"
              "    |         / \\\n"
              "   [|]\n"
              "  [ | ]\n"
              "#####################\n",
              "────────\n"
              "    |  //     |\n"
              "    |//       |\n"
              "    |/       (X)\n"
              "    |         /|\\\n"
              "    |           |\n"
              "    |         / \\\n"
              "   [|]\n"
              "  [ | ]\n"
              "#####################\n"
              ]
        return tp[etape]

    def choose(self, rub, mini):
        div = "data/pendu/{}.txt".format(rub)
        if os.path.isfile(div):
            with open(div, "r", encoding="UTF-8") as f:
                liste = f.readlines()
            deflist = []
            for i in liste:
                if len(i) >= mini:
                    if i.lower() != "stop": # On s'assure que ça ne défonce pas la sécurité
                        deflist.append(i)
            mot = random.choice(deflist)
            mot = mot.replace("\n", "")
            mot = mot.replace(" ", "")
            lettres = [r.upper() for r in mot]
            encode = [n for n in "─" * len(mot)]
            return [mot, lettres, encode]
        else:
            return False
        
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

    def list_exist(self, rub):
        div = "data/pendu/{}.txt".format(rub)
        return os.path.isfile(div)

    def check(self, msg: discord.Message):
        if msg.author == self.bot.user:
            return False
        ct = msg.content.lower()
        if ct.startswith("&") or ct.startswith(":") or ct.startswith(";;") or ct.startswith("\\") or ct.startswith("!"):
            return False
        elif len(ct.split(" ")) > 1:
            return False
        else:
            return True
        
    def indexplus(self, mot, l):
        tr = []
        n = 0
        for e in mot:
            if e == l:
                tr.append(n)
                n += 1
            else:
                n += 1
        return tr

    @commands.command(pass_context=True, no_pm=True)
    async def pendu(self, ctx, liste: str = "general", niveau: int = 1):
        """Démarre une partie de pendu

        Liste: Liste de mots chargée (Par défaut 'General')
        Niveau (1-3): Niveau de difficulé (1- Facile, 2- Normale, 3- Difficile)
        1) 12 vies + Aide + Aucun minimum de longueur
        2) 6 vies + Aide + Mots généralement 33% plus long
        3) 3 vies (sans aide) + Mots 33% plus long que 2)"""
        server = ctx.message.server
        bit = self.bot.get_cog('Mirage').api
        if self.data["PENDU_ON"] is False:
            if self.list_exist(liste):
                if 0 < niveau < 4:
                    gain = True
                    joueurs = {}
                    mini = 12 / (4-niveau)
                    l = self.choose(liste, mini)
                    if l is False:
                        await self.bot.say("Le fichier /data/pendu/**{}.txt** est absent !".format(liste))
                        return
                    if server.id != "204585334925819904":
                        await self.bot.say("**Vous êtes sur le Serveur Alpha**\n*Vous n'êtes donc pas éligible aux "
                                           "gains/pertes et aux succès*")
                        gain = False
                        await asyncio.sleep(2)
                    if niveau is 1:
                        nivtxt = "Facile"
                        aide = True
                    elif niveau is 2:
                        nivtxt = "Moyen"
                        aide = True
                    else:
                        nivtxt = "Difficile"
                        aide = False
                    lettres_as = []
                    vies = int(12 / niveau)
                    encode = l[2]
                    mot = l[1]
                    points = len(l[1]) * niveau
                    soluce = l[0]
                    self.data["PENDU_ON"] = True
                    fileIO("data/pendu/data.json", "save", self.data)
                    while vies > 0 and "".join(encode) != soluce and \
                                    self.data["PENDU_ON"] is True:
                        msg = "{}\n**Vies restantes: *{}***\n\n{}".format(self.dessinpendu(12-vies), vies,
                                                                        " ".join(encode))
                        em = discord.Embed(title="PENDU | {}".format(nivtxt), description=msg, color=0x58598D)
                        em.set_footer(text="Proposé: {}".format(", ".join(lettres_as)if lettres_as else "Aucune"))
                        menu = await self.bot.say(embed=em)
                        rep = await self.bot.wait_for_message(channel=ctx.message.channel, timeout=120,
                                                              check=self.check)
                        if rep is None:
                            em.set_footer(text="Partie arrêtée pour cause d'inactivité")
                            await self.bot.edit_message(menu, embed=em)
                            self.data["PENDU_ON"] = False
                            fileIO("data/pendu/data.json", "save", self.data)
                            return
                        if rep.author != self.bot.user:
                            user = rep.author
                            content = rep.content.upper()
                            if user.id not in joueurs:
                                joueurs[user.id] = {"TROUVE": [],
                                                    "SOMMEPLUS": 0,
                                                    "SOMMEMOINS": 0}
                            if content.lower() == "stop":
                                await self.bot.say("Arrêt d'urgence... (Vos comptes ne sont pas affectés)")
                                return
                            if len(content) < 2:
                                if content in mot:
                                    if content not in encode:
                                        if content not in lettres_as:
                                            places = self.indexplus(mot, content)
                                            for i in places:
                                                encode[i] = content
                                                joueurs[user.id]["SOMMEPLUS"] += points / len(mot)
                                                points -= points / len(mot)
                                            joueurs[user.id]["TROUVE"].append(content)
                                            lettres_as.append(content)
                                            em.set_footer(text="{} | {} lettre(s) trouvée(s) !".format(self.good.upper(), len(places)))
                                            await self.bot.edit_message(menu, embed=em)
                                            await asyncio.sleep(0.5)
                                        else:
                                            em.set_footer(text="{} | Vous avez déjà proposé cette lettre !".format(self.neutre.upper()))
                                            await self.bot.edit_message(menu, embed=em)
                                            await asyncio.sleep(0.5)
                                    else:
                                        em.set_footer(
                                            text="{} | Vous avez déjà trouvé cette lettre !".format(self.neutre.upper()))
                                        await self.bot.edit_message(menu, embed=em)
                                        await asyncio.sleep(0.5)
                                else:
                                    vies -= 1
                                    joueurs[user.id]["SOMMEMOINS"] += points / len(mot)
                                    em.set_footer(
                                        text="{} | C'est pas ça...".format(self.bad.upper()))
                                    lettres_as.append(content)
                                    await self.bot.edit_message(menu, embed=em)
                                    await asyncio.sleep(0.5)
                            else:
                                if content == "".join(mot):
                                    encode = mot
                                    joueurs[user.id]["SOMMEPLUS"] += points
                                    joueurs[user.id]["TROUVE"].append(content)
                                else:
                                    lettres_as.append(content)
                                    vies -= 1
                                    joueurs[user.id]["SOMMEMOINS"] += points / len(mot)
                                    fdp = "C'est pas ça"
                                    if aide:
                                        if self.leven("".join(mot), content) == 1:
                                            fdp = "Presque... mais c'est pas ça"
                                    em.set_footer(
                                        text="{} | {}".format(self.bad, fdp))
                                    await self.bot.edit_message(menu, embed=em)
                                    await asyncio.sleep(1)
                    if vies == 0:
                        msg = "{}\nLe mot était **{}**".format(self.dessinpendu(12 - vies), soluce.upper())
                        prt = ""
                        unord = []
                        for p in joueurs:
                            u = server.get_member(p)
                            unord.append([joueurs[p]["SOMMEMOINS"], u.name])
                        ord = sorted(unord, key=operator.itemgetter(0), reverse=True)
                        for l in ord:
                            prt += "**{}** (*-{}* BK)\n".format(l[1], l[0])
                        em = discord.Embed(title="PENDU | ECHEC", description=msg, color=0x58598D)
                        em.add_field(name="Perdants", value=prt)
                        polit = self.bye()
                        em.set_footer(text="{}".format(
                            polit if gain else "{} | Pertes non-appliquées (Serveur Alpha)".format(polit)))
                        menu = await self.bot.say(embed=em)
                        if gain: # Ou plutôt pertes :aah:
                            for j in joueurs:
                                user = server.get_member(j)
                                som = int(joueurs[j]["SOMMEMOINS"])
                                if bit._sub(user, som, "Défaite au pendu"):
                                    await self.bot.send_message(user, "Vous perdez **{}** BK.".format(som))
                                else:
                                    bit._set(user, 0, "Défaite au pendu")
                                    await self.bot.send_message(user, "Votre compte bancaire est désormais **vide**.")
                                bit.success(user, "Triplé", "Avoir réussi 3 parties de pendu consécutives", 0, 3)
                                bit.success(user, "Seulement 10 ?", "Avoir réussi 10 parties de pendu d'affilé", 0, 10)
                        self.data["PENDU_ON"] = False
                        fileIO("data/pendu/data.json", "save", self.data)
                        return
                    elif "".join(encode) == soluce:
                        msg = "{}\nLe mot est **{}**".format(self.dessinpendu(12 - vies),
                                                               soluce.upper())
                        prt = ""
                        unord = []
                        for p in joueurs:
                            u = server.get_member(p)
                            unord.append([joueurs[p]["SOMMEPLUS"], u.name])
                        ord = sorted(unord, key=operator.itemgetter(0), reverse=True)
                        for l in ord:
                            prt += "**{}** (*+{}* BK)\n".format(l[1], l[0])
                        em = discord.Embed(title="PENDU | VICTOIRE", description=msg, color=0x58598D)
                        em.add_field(name="Gagnants", value=prt)
                        polit = self.bye()
                        em.set_footer(text="{}".format(
                            polit if gain else "{} | Gains non-appliquées (Serveur Alpha)".format(polit)))
                        menu = await self.bot.say(embed=em)
                        if gain:
                            for j in joueurs:
                                user = server.get_member(j)
                                som = int(joueurs[j]["SOMMEPLUS"])
                                if bit._add(user, som, "Victoire au pendu"):
                                    await self.bot.send_message(user, "Vous gagnez **{}** BK.".format(som))
                                else:
                                    await self.bot.send_message(user, "Il semblerait que vous n'ayez pas de compte "
                                                                      "bancaire... Je garde l'argent du coup.")
                                suc = bit.success(user, "Triplé", "Avoir réussi 3 parties de pendu consécutives", 1, 3)
                                if suc:
                                    await self.bot.say(
                                        "{} **Succès débloqué** | **{}** - *{}*".format(user.mention, suc[0],
                                                                                        suc[1]))
                                suc = bit.success(user, "Seulement 10 ?", "Avoir réussi 10 parties de pendu d'affilé",
                                                  1, 10)
                                if suc:
                                    await self.bot.say(
                                        "{} **Succès débloqué** | **{}** - *{}*".format(user.mention, suc[0],
                                                                                        suc[1]))
                        self.data["PENDU_ON"] = False
                        fileIO("data/pendu/data.json", "save", self.data)
                        return
                    else:
                        em.set_footer(text="Partie arrêtée")
                        await self.bot.edit_message(menu, embed=em)
                        return
                else:
                    await self.bot.say("Le niveau de difficulté doit être compris entre 1 (Facile) et 3 (Difficile)")
            else:
                txtlist = "**Listes:**\n"
                liste = os.listdir("data/pendu/")
                for i in liste:
                    if i.endswith(".txt"):
                        txtlist += "- {}\n".format(i.replace(".txt", ""))
                await self.bot.say("Cette liste n'existe pas !\n\n{}".format(txtlist))
        else:
            await self.bot.say("Une partie est en cours sur **{}**".format(server.name))

    @commands.command(pass_context=True, hidden=True)
    async def resetpendu(self, ctx):
        """Permet de reset le pendu en cas de blocage"""
        self.data["PENDU_ON"] = False
        fileIO("data/pendu/data.json", "save", self.data)
        await self.bot.say("Reset effectué avec succès.")

def check_folders():
    if not os.path.exists("data/pendu/"):
        print("Creation du dossier Jeu du pendu...")
        os.makedirs("data/pendu")

def check_files():
    default = {"PENDU_ON" : False}
    if not os.path.isfile("data/pendu/data.json"):
        print("Création du fichier Jeu du pendu")
        fileIO("data/pendu/data.json", "save", default)

def setup(bot):
    check_folders()
    check_files()
    n = Pendu(bot)
    bot.add_cog(n)