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
                        ident = self.user[p]["STATS"]["MENTIONS"][search.id]["ID"]
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

class Ego:
    """Système EGO : Assistant personnel [EN CONSTRUCTION]"""

    def __init__(self, bot):
        self.bot = bot
        self.ego = EgoAPI(bot, "data/ego/user.json")

    @commands.group(name= "ego", pass_context=True)
    async def ego_sys(self, ctx):
        """Commandes Systeme EGO - Assistant personnel"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @commands.command(pass_context=True)
    async def card(self, ctx, user: discord.Member = None):
        """Permet de recevoir une carte affichant des informations complètes à propos d'un utilisateur."""
        server = ctx.message.server
        channel = ctx.message.channel
        if user is None:
            user = ctx.message.author
        ego = self.ego.logged(user)
        epoch = self.ego.epoch(user, "jour")
        em = discord.Embed(title="{}".format(str(user)), color=user.color)
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
        try:
            most = "Paillasson de {}".format(server.get_member(self.ego.plus_smth(user, "MENTIONS")[0]))
        except:
            pass
        try:
            pail = "Paillassonné par {}".format(server.get_member(self.ego.paille(user)[0]))
        except:
            pass
        em.add_field(name="Relations", value="- *{}*\n- *{}*".format(str(most), str(pail)))
        try:
            mostchan = server.get_channel(self.ego.plus_smth(user, "CHANNELS")[0])
            em.add_field(name="Channel favoris", value="#{}".format(mostchan.name))
        except:
            pass
        em.set_footer(text="Certaines informations proviennent du Système Ego | V1.13")
        msg = await self.bot.say(embed=em)

        await self.bot.add_reaction(msg, "➕")
        await asyncio.sleep(0.25)
        rap = await self.bot.wait_for_reaction("➕", message=msg, timeout=10)
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
            total = 0
            for e in ego.stats["MENTIONS"]:
                total += 1
            em.add_field(name="Nb mentions", value="{}".format(total))
            em.set_footer(text="Informations relatives à l'inscription Ego. Ces informations ne sont pas protégées et relèvent du public.")
            await self.bot.say(embed=em)
        else:
            pass

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
    bot.add_cog(n)