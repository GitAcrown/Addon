import asyncio
import os
from .utils import checks
from copy import deepcopy
import discord
from collections import namedtuple
from __main__ import send_cmd_help
from discord.ext import commands
import time
import operator
from .utils.dataIO import fileIO, dataIO

class EgoAPI:
    """API Ego | Suivi de statistiques et services liés (Service)"""
    def __init__(self, bot, path):
        self.bot = bot
        self.user = dataIO.load_json(path)

    def save(self): #Sauvegarde l'ensemble des données utilisateur
        fileIO("data/ego/profil.json", "save", self.user)
        return True

    def log(self, user):
        if user.id in self.user:
            return self.convert(user)
        else:
            creat = time.time()
            self.user[user.id] = {"ID": user.id,
                                     "BORN" : creat,
                                     "HISTO" : [], #Historique du membre
                                     "SAVED": [], #Sauvegardes (Messages, Memo...)
                                     "PERSO" : {}, #Informations perso (A venir)
                                     "STATS" : {}} #Statistiques sur le membre
            self.save()
            return self.convert(user)

    def convert(self, user):
        Profil = namedtuple('Profil', ['id', 'born', 'histo', 'saved', 'perso', 'stats'])
        id = user.id
        b = self.user[user.id]["BORN"]
        h = self.user[user.id]["HISTO"]
        sa = self.user[user.id]["SAVED"]
        p = self.user[user.id]["PERSO"]
        st = self.user[user.id]["STATS"]
        return Profil(id, b, h, sa, p ,st)

    def event(self, user, rubrique:str, symb:str, descr:str):
        ego = self.log(user)
        date = time.strftime("%d/%m/%Y", time.localtime())
        ego.histo.append([date, rubrique, symb, descr])
        self.save()

    def since(self, user, format=None):
        ego = self.log(user)
        s = time.time() - ego.born
        sm = s / 60  # en minutes
        sh = sm / 60  # en heures
        sj = sh / 24  # en jours
        sa = sj / 364.25  # en années
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

    def stat_color(self, user):
        s = user.status
        if s == discord.Status.online:
            return 0x43B581
        elif s == discord.Status.idle:
            return 0xFAA61A
        elif s == discord.Status.dnd:
            return 0xF04747
        else:
            return 0x9ea0a3

class Ego:
    """Système Ego | Assistant personnel et suivi de statistiques"""
    def __init__(self, bot):
        self.bot = bot
        self.ego = EgoAPI(bot, "data/ego/profil.json")
        self.glob = dataIO.load_json("data/ego/glob.json") #Stats globaux

    def solde_img(self, rewind=0): #Remonte de X jours (rewind) afin de calculer le solde migratoire
        nb_join = nb_quit = 0
        today = time.strftime("%d/%m/%Y", time.localtime())
        if today in self.glob["NB_JOIN"]:
            nb_join += self.glob["NB_JOIN"][today]
        else:
            return False
        if today in self.glob["NB_QUIT"]:
            nb_quit += self.glob["NB_QUIT"][today]
        else:
            return False
        if rewind > 0:
            yst = today
            while rewind > 0:
                yst = time.strftime("%d/%m/%Y", time.localtime(time.mktime(time.strptime(yst, "%d/%m/%Y")) - 86400))
                if yst in self.glob["NB_JOIN"]:
                    nb_join += self.glob["NB_JOIN"][yst]
                else:
                    return False
                if yst in self.glob["NB_QUIT"]:
                    nb_quit += self.glob["NB_QUIT"][yst]
                else:
                    return False
                rewind -= 1
        solde = nb_join - nb_quit
        return [nb_join, nb_quit, solde]

    @commands.command(name="logs", pass_context=True)
    async def changelog(self, ctx):
        """Informations sur la dernière MAJ Majeure de EGO."""
        em = discord.Embed(color=0x5184a5)
        cl = "- Remise à 0 des données sauvegardées\n" \
             "- Ajout de l'Historique\n" \
             "- Nouveaux suivis (Pseudos, rôles...)\n" \
             "- Changement affichage &card\n" \
             "- Ajout de &server\n" \
             "[Bientôt] Retour des commandes &epop et &compat\n" \
             "[Bientôt] Mode fantôme\n" \
             "[Bientôt] Ajout des informations perso\n" \
             "[Bientôt] Historique détaillé\n"
        em.add_field(name="Version 2.0.5", value=cl)
        em.set_footer(text="MAJ publiée le 28/06")
        await self.bot.say(embed=em)

    @commands.command(aliases=["c"], pass_context=True)
    async def card(self, ctx, user: discord.Member = None):
        """Affiche une carte de membre détaillée.
        
        Si le pseudo n'est pas spécifié, c'est une carte de votre compte."""
        if user is None:
            user = ctx.message.author
        ego = self.ego.log(user)
        if not user.bot:
            ec = self.ego.stat_color(user)
        else:
            ec = 0x2e6cc9
        em = discord.Embed(title="{}".format(str(user)), color=ec, url=ego.perso["SITE"] if "SITE" in ego.perso else None)
        em.set_thumbnail(url=user.avatar_url)
        em.add_field(name="Surnom", value=user.display_name)
        em.add_field(name="ID", value=str(user.id))
        passed = (ctx.message.timestamp - user.created_at).days
        em.add_field(name="Age du compte", value=str(passed) + " jours")
        passed = (ctx.message.timestamp - user.joined_at).days
        egodate = self.ego.since(user, "jour")
        if passed < egodate:
            msg = "+{} jours"
        else:
            msg = "{} jours"
        em.add_field(name="Nb de jours", value=msg.format(passed))
        if egodate == 0:
            egodate = 1
        em.add_field(name="Ratio de messages", value="{}/jour".format(str(
            round(ego.stats["NB_MSG"] / egodate, 2))))
        rolelist = [r.name for r in user.roles]
        rolelist.remove('@everyone')
        em.add_field(name="Rôles", value=rolelist)
        liste = ego.histo[-3:]
        liste.reverse()
        hist = ""
        if liste != []:
            for i in liste:
                hist += "**{}** *{}*\n".format(i[2], i[3])
        else:
            hist = "Aucun historique"
        em.add_field(name="Historique", value="{}".format(hist))
        em.set_footer(
            text="Certaines informations proviennent du système Ego | V2.0.5 (&logs)", icon_url="http://i.imgur.com/DsBEbBw.png")
        #TODO Changer de version à chaque MAJ
        await self.bot.say(embed=em)

    @commands.command(aliases=["s"], pass_context=True)
    async def scard(self, ctx):
        """Affiche des informations sur le serveur."""
        server = ctx.message.server
        online = str(len([m.status for m in server.members if str(m.status) == "online" or str(m.status) == "idle" or str(m.status) == "dnd"]))
        total_users = str(len(server.members))
        auj = time.strftime("%d/%m/%Y", time.localtime())
        hier = time.strftime("%d/%m/%Y", time.localtime(time.mktime(time.strptime(auj, "%d/%m/%Y")) - 86400))
        em = discord.Embed(title= "{}".format(server.name), color=ctx.message.author.color)
        em.add_field(name="ID", value="{}".format(server.id))
        em.add_field(name="Region", value="{}".format(server.region))
        em.add_field(name="Propriétaire", value="{}".format(server.owner))
        if "NB_JOIN" and "NB_QUIT" in self.glob:
            if auj in self.glob["NB_JOIN"] and auj in self.glob["NB_QUIT"]:
                if (self.glob["NB_JOIN"][auj] - self.glob["NB_QUIT"][auj]) > (self.glob["NB_JOIN"][hier] - self.glob["NB_QUIT"][hier]):
                    var = "+"
                elif (self.glob["NB_JOIN"][auj] - self.glob["NB_QUIT"][auj]) == (self.glob["NB_JOIN"][hier] - self.glob["NB_QUIT"][hier]):
                    var = "="
                else:
                    var = "-"
            else:
                var = "?"
        else:
            var = "?"
        em.add_field(name="Nb membres", value="**{}**/{} (*{}*)".format(online, total_users, var))
        passed = (ctx.message.timestamp - server.created_at).days
        em.add_field(name="Age", value="{} jours".format(passed))
        em.set_thumbnail(url=server.icon_url)
        em.set_footer(text="Certaines informations proviennent du système Ego | V2.0.5 (&logs)")
        await self.bot.say(embed=em)

#LISTENERS

    async def l_msg(self, message):
        author = message.author
        channel = message.channel
        if "NB_MSG" in self.glob:
            today = time.strftime("%d/%m/%Y", time.localtime())
            if today in self.glob["NB_MSG"]:
                if channel.id in self.glob["NB_MSG"][today]:
                    self.glob["NB_MSG"][today][channel.id] += 1
                else:
                    self.glob["NB_MSG"][today][channel.id] = 1
            else:
                self.glob["NB_MSG"][today] = {} #Ngb
        else:
            self.glob["NB_MSG"] = {} #Ngb

        ego = self.ego.log(author)
        ego.stats["NB_MSG"] = ego.stats["NB_MSG"] + 1 if "NB_MSG" in ego.stats else 1
        if message.mentions != []:
            if "MENTION" in ego.stats:
                for u in message.mentions:
                    if u.id in ego.stats["MENTION"]:
                        ego.stats["MENTION"][u.id] += 1
                    else:
                        ego.stats["MENTION"][u.id] = 1
                    egb = self.ego.log(u)
                    if "MENTION_BY" in egb.stats:
                        if author.id in egb.stats["MENTION_BY"]:
                            egb.stats["MENTION_BY"][author.id] += 1
                        else:
                            egb.stats["MENTION_BY"][author.id] = 1
                    else:
                        egb.stats["MENTION_BY"] = {} #Ngb
            else:
                ego.stats["MENTION"] = {} #Ngb
        self.ego.save()

    async def l_join(self, user):
        if "NB_JOIN" in self.glob:
            today = time.strftime("%d/%m/%Y", time.localtime())
            if today in self.glob["NB_JOIN"]:
                self.glob["NB_JOIN"][today] += 1
            else:
                self.glob["NB_JOIN"][today] = 1
            if today not in self.glob["NB_QUIT"]:
                self.glob["NB_QUIT"][today] = 0
        else:
            self.glob["NB_JOIN"] = {} #Ngb

        ego = self.ego.log(user)
        if "ENTREES" in ego.stats:
            ego.stats["ENTREES"] += 1
        else:
            ego.stats["ENTREES"] = 1
        self.ego.event(user, "presence", ">", "Est arrivé sur le serveur")
        self.ego.save()

    async def l_quit(self, user):
        if "NB_QUIT" in self.glob:
            today = time.strftime("%d/%m/%Y", time.localtime())
            if today in self.glob["NB_QUIT"]:
                self.glob["NB_QUIT"][today] += 1
            else:
                self.glob["NB_QUIT"][today] = 1
            if today not in self.glob["NB_JOIN"]:
                self.glob["NB_JOIN"][today] = 0
        else:
            self.glob["NB_QUIT"] = {} #Ngb

        ego = self.ego.log(user)
        if "SORTIES" in ego.stats:
            ego.stats["SORTIES"] += 1
        else:
            ego.stats["SORTIES"] = 1
        self.ego.event(user, "presence", "<", "A quitté le serveur")
        self.ego.save()

    async def l_profil(self, b, a): #On cherche un changement dans le profil
        ego = self.ego.log(a)
        if a.name != b.name: #Pseudo ?
            if "PSEUDOS" in ego.stats:
                ego.stats["PSEUDOS"].append(a.name)
            else:
                ego.stats["PSEUDOS"] = [b.name, a.name]
            self.ego.event(a, "pseudo", "@", "A changé son pseudo en {}".format(a.name))
        if a.display_name != b.display_name: #Surnom ?
            if "N_PSEUDOS" in ego.stats:
                ego.stats["N_PSEUDOS"].append(a.display_name)
            else:
                ego.stats["N_PSEUDOS"] = [b.display_name, a.display_name]
            self.ego.event(a, "n_pseudo", "@", "Désormais surnommé(e) {}".format(a.display_name))
        if a.avatar_url != b.avatar_url: #Avatar ?
            self.ego.event(a, "avatar", "×", "A changé son avatar")
        if a.top_role != b.top_role: #Rôle affiché ?
            if not a.top_role.name == "@everyone":
                if a.top_role > b.top_role:
                    self.ego.event(a, "role", "+", "A été promu {}".format(a.top_role.name))
                else:
                    self.ego.event(a, "role", "-", "A été rétrogradé {}".format(a.top_role.name))
            else:
                self.ego.event(a, "role", "!", "Ne possède plus de rôles")
        #TODO Ajouter VoiceState dans le cadre du calcul d'Activité

    async def l_ban(self, user):
        ego = self.ego.log(user)
        if "BANS" in ego.stats:
            ego.stats["BANS"] += 1
        else:
            ego.stats["BANS"] = 1
        self.ego.event(a, "presence", "#", "A été banni(e)")
        self.ego.save()

def check_folders():
    if not os.path.exists("data/ego"):
        print("Creation du dossier EGO...")
        os.makedirs("data/ego")

def check_files():
    if not os.path.isfile("data/ego/profil.json"):
        print("Creation du fichier de comptes EGO...")
        fileIO("data/ego/profil.json", "save", {})
    if not os.path.isfile("data/ego/glob.json"):
        print("Creation du fichier global EGO...")
        fileIO("data/ego/glob.json", "save", {})

def setup(bot):
    check_folders()
    check_files()
    n = Ego(bot)
    #Listeners (Suivi de l'écrit)
    bot.add_listener(n.l_msg, "on_message") #A chaque message
    bot.add_listener(n.l_join, "on_member_join") #A chaque membre qui rejoint
    bot.add_listener(n.l_quit, "on_member_remove") #A chaque membre qui part
    bot.add_listener(n.l_profil, "on_member_update") #Lorsqu'un membre modifie son profil (avatar, pseudo...)
    bot.add_listener(n.l_ban, "on_member_ban") #Lorsqu'un membre est banni
    bot.add_cog(n)