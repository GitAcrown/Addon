import asyncio
import os
import random
from .utils import checks
from copy import deepcopy
import discord
from collections import namedtuple
from __main__ import send_cmd_help
from discord.ext import commands
import time
import operator
from .utils.dataIO import fileIO, dataIO

#Enregistrement depuis le

class EgoAPI:
    """API Ego | Utilisable sur toutes les extensions compatibles"""

    def __init__(self, bot, path):
        self.bot = bot
        self.user = dataIO.load_json(path)

    def save(self): #Sauvegarde l'ensemble des données utilisateur
        fileIO("data/ego/user.json", "save", self.user)
        return True

    def create(self, user): #Créer un compte vierge
        self.user[user.id] = {"ID": user.id,
                              "LEVEL" : 0,
                              "STATS" : {}}
        self.user[user.id]["STATS"]["CREATION"] = time.time()
        self.save()
        return self.personnal(user)

    def personnal(self, user):
        Profil = namedtuple('Profil', ['id', 'level', "stats"])
        id = user.id
        level = self.user[user.id]["LEVEL"]
        stats = self.user[user.id]["STATS"]
        return Profil(id, level, stats)

    def logged(self, user):
        if user.id in self.user:
            return self.personnal(user)
        else:
            return False

    def edit(self, user, champ, line, val):
        """Editer une valeur EGO"""
        if self.logged(user):
            self.user[user.id][champ][line] = val
            self.save()
            return True
        else:
            return None

    def get(self, user, champ, line, defaut):
        """Recevoir une valeur EGO"""
        if self.logged(user):
            if line != None:
                if line not in self.user[user.id][champ]:
                    self.user[user.id][champ][line] = defaut
                    self.save()
                return self.user[user.id][champ][line]
            else:
                return self.user[user.id][champ]
        else:
            return None

    def discard(self, user, champ, line):
        """Supprimer une valeur EGO"""
        if self.logged(user):
            del self.user[user.id][champ][line]
            self.save()
        else:
            return None

    def plus_smth(self, user, line):
        ego = self.logged(user)
        if ego != None:
            post = 0
            ident = None
            for p in ego.stats[line]:
                if ego.stats[line][p]["NB"] > post:
                    post = ego.stats[line][p]["NB"]
                    ident = ego.stats[line][p]["ID"]
            else:
                return [ident, post]

    def paille(self, search):
        post = 0
        ident = None
        for p in self.user:
            if "MENTIONS" in self.user[p]["STATS"]:
                if search.id in self.user[p]["STATS"]["MENTIONS"]:
                    if self.user[p]["STATS"]["MENTIONS"][search.id]["NB"] > post:
                        post = self.user[p]["STATS"]["MENTIONS"][search.id]["NB"]
                        ident = self.user[p]["ID"]
        else:
            return [ident, post]

    def epoch(self, user, format=None):
        ego = self.logged(user)
        if ego != None:
            s = time.time() - ego.stats["CREATION"]
            sm = s/60 #en minutes
            sh = sm/60 #en heures
            sj = sh/24 #en jours
            sa = sj/364.25 #en années
            if format == "année":
                return int(sa)
            elif format == "jour":
                return int(sj)
            elif format == "heure":
                return int(sh)
            elif format == "minute":
                return int(sm)
            else:
                return int(s)

    def pop_class(self, user, top=5):
        liste = []
        for p in self.user:
            n = 0
            for u in self.user:
                if "MENTIONS" in self.user[u]["STATS"]:
                    if p in self.user[u]["STATS"]["MENTIONS"]:
                        n += self.user[u]["STATS"]["MENTIONS"][p]["NB"]
            t = self.user[p]["STATS"]["CREATION"] / (60*60*24)
            mn = n/t
            if self.user[p]["ID"] == user.id:
                k = [mn, self.user[p]["ID"]]
            liste.append([mn, self.user[p]["ID"]])
        sort = sorted(liste, key=operator.itemgetter(0))
        sort.reverse()
        place = sort.index(k)
        sort = sort[:top]
        return [sort, place]

    def set_site(self, user, url:str):
        if user.id in self.user:
            self.user[user.id]["STATS"]["SITE"] = url
            self.save()
            return True
        else:
            return False

    def total_ment(self, user):
        if user.id in self.user:
            nb = 0
            for m in self.user[user.id]["STATS"]["MENTIONS"]:
                nb += self.user[user.id]["STATS"]["MENTIONS"][m]["NB"]
            return nb
        else:
            return False

    def nb_ment(self, user, search):
        if user.id in self.user:
            if search.id in self.user[user.id]["STATS"]["MENTIONS"]:
                return self.user[user.id]["STATS"]["MENTIONS"][search.id]["NB"]
            else:
                return False
        else:
            return False

class Ego:
    """Système EGO : Assistant personnel [EN CONSTRUCTION]"""

    def __init__(self, bot):
        self.bot = bot
        self.ego = EgoAPI(bot, "data/ego/user.json")

    @commands.command(name="logs", pass_context=True)
    async def changelog(self, ctx):
        """Informations sur la dernière MAJ Majeure de EGO."""
        em = discord.Embed(color=0x5184a5)
        cl = "- Ajout de 'InstantEgo'"
        em.add_field(name="Version 1.3", value=cl)
        em.set_footer(text="MAJ faite le 05/06/17")
        await self.bot.say(embed=em)

    @commands.command(pass_context=True)
    async def site(self, ctx, url):
        """Permet de rajouter un site personnel à sa Carte Ego."""
        author = ctx.message.author
        if "http" in url:
            if self.ego.set_site(author, url):
                await self.bot.say("Site enregistré.")
            else:
                await self.bot.say("Une erreur s'est produite. Essayez plus tard.")
        else:
            await self.bot.say("Ce n'est pas une URL valide.")

    @commands.command(pass_context=True)
    async def card(self, ctx, user: discord.Member = None):
        """Permet de recevoir une carte affichant des informations complètes à propos d'un utilisateur."""
        server = ctx.message.server
        channel = ctx.message.channel
        if user is None:
            user = ctx.message.author
        ego = self.ego.logged(user)
        epoch = self.ego.epoch(user, "jour")
        site = ego.stats["SITE"] if "SITE" in ego.stats else None
        em = discord.Embed(title="{}".format(str(user)), color=user.color, url=site)
        em.set_thumbnail(url=user.avatar_url)
        em.add_field(name= "ID", value=str(user.id))
        em.add_field(name= "Surnommé", value=user.display_name)
        em.add_field(name= "Type de compte", value="Utilisateur" if user.bot is False else "Bot")
        passed = (ctx.message.timestamp - user.created_at).days
        em.add_field(name= "Age du compte", value= str(passed) + " jours")
        passed = (ctx.message.timestamp - user.joined_at).days
        em.add_field(name= "Nb de Jours", value= "{} jours (Ego/{})".format(passed, epoch))
        rolelist = [r.name for r in user.roles]
        rolelist.remove('@everyone')
        em.add_field(name= "Roles", value= rolelist)

        if epoch == 0:
            epoch = 1
        em.add_field(name="Ratio de messages", value="{}/jour".format(str(
            round(ego.stats["MESSAGES"] / epoch, 2))))
        most = "Paillasson de (?)"
        pail = "Paillassonné par (?)"
        cuck = "Cuck par (?)"
        try:
            most = "Paillasson de {}".format(server.get_member(self.ego.plus_smth(user, "MENTIONS")[0]))
            pp = server.get_member(self.ego.plus_smth(user, "MENTIONS")[0])
            cuck = "Cuck par {}".format(server.get_member(self.ego.plus_smth(pp, "MENTIONS")[0]))
        except:
            pass
        try:
            pail = "Paillassonné par {}".format(server.get_member(self.ego.paille(user)[0]))
        except:
            pass
        em.add_field(name="Relations", value="- *{}*\n- *{}*\n- *{}*".format(str(most), str(pail), str(cuck)))
        em.set_footer(text="Certaines informations proviennent du Système Ego | V1.31 (&logs)")
        msg = await self.bot.say(embed=em)

        await self.bot.add_reaction(msg, "➕")
        await self.bot.add_reaction(msg, "💳")
        await self.bot.add_reaction(msg, "❔")
        await asyncio.sleep(1.25)
        rap = await self.bot.wait_for_reaction(["➕","💳","❔"], message=msg, timeout=20)
        if rap == None:
            pass
        elif rap.reaction.emoji == "➕":
            em = discord.Embed(title="Plus sur {}".format(str(user)), color=user.color)
            if "ENTREES" in ego.stats:
                em.add_field(name="Entrées", value=ego.stats["ENTREES"])
            else:
                em.add_field(name="Entrées", value=0)
            if "SORTIES" in ego.stats:
                em.add_field(name="Sorties", value=ego.stats["SORTIES"])
            else:
                em.add_field(name="Sorties", value=0)
            em.add_field(name="Nb messages", value="{}".format(ego.stats["MESSAGES"]))
            place = self.ego.pop_class(user)[1]
            em.add_field(name="Classement Epop", value="{}".format(place))
            total = 0
            for e in ego.stats["MENTIONS"]:
                total += 1
            em.add_field(name="Nb mentions", value="{}".format(total))
            em.set_footer(text="Informations relatives à l'inscription Ego. Ces informations ne sont pas protégées et relèvent du public.")
            await self.bot.say(embed=em)
        elif rap.reaction.emoji == "💳":
            money = self.bot.get_cog('Money').money
            acc = money.log(user)
            solde = acc.solde
            typecompte = acc.type
            num = user.id[8:]
            em = discord.Embed(title="Compte BitKhey", color= user.color)
            em.add_field(name="Solde", value="**{}** BK".format(solde))
            em.add_field(name="Type de compte", value=typecompte)
            em.add_field(name="Numéro de compte", value=num)
            em.set_footer(text="Informations tirées de BitKhey | '&compte' pour en savoir plus.")
            await self.bot.say(embed=em)
        elif rap.reaction.emoji == "❔":
            em = discord.Embed(color = user.color)
            aide = "**Ego** est un système integré au bot qui permet de récolter des statistiques sur le serveur. Il n'enregistre pas vos messages.\n" \
                   "- ID représente votre Identifiant Discord. C'est ce qui permet de savoir qui vous êtes pour Ego.\n" \
                   "- L'Age du compte correspond au nombre de jours depuis lequel votre compte a été crée.\n" \
                   "- Le Nombre de jour est celui qui compte depuis combien de jours vous êtes sur le serveur (Reset à chaque départ)\n" \
                   "- 'Ego/' est le nombre de jours depuis lequel le système vous piste. Plus ce nombre est elevé, plus les statistiques sont exactes.\n" \
                   "- Vos relations proviennent d'un calcul effectué par un algorithme grace aux données récoltés. Elles ne sont pas à prendre au sérieux.\n" \
                   "L'Emoji *+* vous permet d'avoir plus d'informations sur votre profil (Entrées et sorties du serveur par exemple)."
            em.add_field(name="Aide", value=aide)
            em.set_footer(text="Pour avoir plus d'informations sur la dernière MAJ, utilisez &logs.")
            await asyncio.sleep(0.5)
            await self.bot.send_message(rap.user, embed=em)
        else:
            pass

    @commands.command(pass_context=True, no_pm=True)
    async def epop(self, ctx, top = 5):
        """Affiche le top X des personnes les plus populaires du serveur et votre place sur ce top.
        
        Par défaut le top 5."""
        author = ctx.message.author
        server = ctx.message.server
        sort = self.ego.pop_class(author, top)
        place = sort[1]
        em = discord.Embed(color=author.color, title="EGO | Les E-Pop du serveur")
        msg = ""
        n = 1
        for p in sort[0]:
            user = server.get_member(p[1])
            msg += "{} | *{}*\n".format(n, str(user))
            n += 1
        em.add_field(name = "Top {}".format(top), value=msg)
        em.add_field(name = "Votre place", value="{}e".format(place + 1))
        em.set_footer(text="Ces informations sont issues du système Ego")
        await self.bot.say(embed=em)

    @commands.command(pass_context=True, no_pm=True)
    async def compat(self, ctx, p1: discord.Member, p2: discord.Member = None):
        """Calcul de la compatibilité de deux personnes.
        
        Si P2 n'est pas précisé, c'est par défaut VOUS."""
        if p2 == None:
            p2 = ctx.message.author
        nbp1_p2 = self.ego.nb_ment(p1, p2)
        pour1 = (nbp1_p2 / self.ego.total_ment(p1))*100
        nbp2_p1 = self.ego.nb_ment(p2, p1)
        pour2 = (nbp2_p1 / self.ego.total_ment(p2))*100
        moy = round((pour1 + pour2) / 2, 2)
        await self.bot.say("La compatibilité entre **{}** et **{}** est de *{}%* !".format(p1.name, p2.name, moy))

# LISTENERS & SYSTEME =============================================
    async def stats_listener(self, message):
        author = message.author
        channel = message.channel
        if not self.ego.logged(author):
            self.ego.create(author)
            await asyncio.sleep(0.25)

        #Nb de messages
        out = self.ego.get(author, "STATS", "MESSAGES", 0) + 1
        self.ego.edit(author, "STATS", "MESSAGES", out)

        #Channel favoris
        ego = self.ego.get(author, "STATS", "CHANNELS", {})
        liste = []
        for c in ego:
            liste.append(ego[c]["ID"])
        if channel.id in liste:
            ego[channel.id]["NB"] += 1
        else:
            ego[channel.id] = {"ID" : channel.id, "NB" : 1}
        self.ego.edit(author, "STATS", "CHANNELS", ego)

        #Mentions
        if message.mentions != []:
            for u in message.mentions:
                ego = self.ego.get(author, "STATS", "MENTIONS", {})
                liste = []
                for c in ego:
                    liste.append(ego[c]["ID"])
                if not u.id in liste:
                    ego[u.id] = {"ID" : u.id, "NB": 1}
                else:
                    ego[u.id]["NB"] += 1
                self.ego.edit(author, "STATS", "MENTIONS", ego)

    async def entree_listen(self, user):
        if not self.ego.logged(user):
            self.ego.create(user)
            await asyncio.sleep(0.25)
        out = self.ego.get(user, "STATS", "ENTREES", 0) + 1
        self.ego.edit(user, "STATS", "ENTREES", out)

    async def sortie_listen(self, user):
        if not self.ego.logged(user):
            self.ego.create(user)
            await asyncio.sleep(0.25)
        out = self.ego.get(user, "STATS", "SORTIES", 0) + 1
        self.ego.edit(user, "STATS", "SORTIES", out)

    async def instant_ego(self, reaction, author):
        if reaction.emoji == "🔍":
            user = reaction.message.author
            message = reaction.message

            roles = [x.name for x in user.roles if x.name != "@everyone"]
            if not roles: roles = ["None"]
            ego = self.ego.logged(user)
            epoch = self.ego.epoch(user, "jour")
            site = ego.stats["SITE"] if "SITE" in ego.stats else None
            em = discord.Embed(color=user.color, url=site)
            em.set_author(name="InstantEgo | {}".format(str(user)), icon_url=user.avatar_url)
            em.add_field(name="Surnommé", value=user.display_name)
            em.add_field(name="Type de compte", value="Utilisateur" if user.bot is False else "Bot")
            passed = (message.timestamp - user.created_at).days
            em.add_field(name="Age du compte", value=str(passed) + " jours")
            passed = (message.timestamp - user.joined_at).days
            em.add_field(name="Nb de Jours", value="{} jours (Ego/{})".format(passed, epoch))
            rolelist = [r.name for r in user.roles]
            rolelist.remove('@everyone')
            em.add_field(name="Roles", value=rolelist)
            em.set_footer(text="Données issues en partie de Ego | '&card {}' pour en savoir plus".format(user.name))

            if epoch == 0:
                epoch = 1
            em.add_field(name="Ratio de messages", value="{}/jour".format(str(
                round(ego.stats["MESSAGES"] / epoch, 2))))
            await self.bot.send_message(author, embed=em)

def check_folders():
    if not os.path.exists("data/ego"):
        print("Creation du dossier EGO...")
        os.makedirs("data/ego")

def check_files():
    if not os.path.isfile("data/ego/user.json"):
        print("Creation du fichier de comptes EGO...")
        fileIO("data/ego/user.json", "save", {})

def setup(bot):
    check_folders()
    check_files()
    n = Ego(bot)
    bot.add_listener(n.stats_listener, "on_message")
    bot.add_listener(n.entree_listen, "on_member_join")
    bot.add_listener(n.sortie_listen, "on_member_remove")
    bot.add_listener(n.instant_ego, "on_reaction_add")
    bot.add_cog(n)