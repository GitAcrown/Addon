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

    def poss_jeu(self, jeu):
        verif = self.jeux_verif()
        total = []
        nom = None
        for j in verif:
            if jeu in j:
                if nom == None:
                    nom = j
                for p in self.user:
                    if "JEUX" in self.user[p]["PERSO"]:
                        if j in self.user[p]["PERSO"]["JEUX"]:
                            total.append(self.user[p]["ID"])
        if total != []:
            return [total, nom]
        else:
            return False

    def jeux_verif(self):
        verif = []
        dispo = []
        for p in self.user:
            if "JEUX" in self.user[p]["PERSO"]:
                for g in self.user[p]["PERSO"]["JEUX"]:
                    if g not in verif:
                        verif.append(g)
                    else:
                        if g not in dispo:
                            dispo.append(g)
        return dispo

    def biblio(self, user):
        ego = self.log(user)
        verif = self.jeux_verif()
        if "JEUX" in ego.perso:
            poss = []
            for g in ego.perso["JEUX"]:
                if g in verif:
                    poss.append(g)
            if poss != []:
                return poss
            else:
                return False
        else:
            return False

    def is_fantome(self, user):
        ego = self.log(user)
        if "CONFIDENCE" in ego.perso:
            if "FANTOME" in ego.perso["CONFIDENCE"]:
                return ego.perso["CONFIDENCE"]["FANTOME"]
            else:
                return False
        else:
            return False

    def aff_auto(self, user, section):
        ego = self.log(user)
        if "CONFIDENCE" in ego.perso:
            if self.is_fantome(user) is False:
                if section in ego.perso["CONFIDENCE"]:
                    return ego.perso["CONFIDENCE"][section]
                else:
                    return True
            else:
                return False
        else:
            return True

    def suspens(self, user, mode:bool):
        ego = self.log(user)
        if mode == True:
            self.user[user.id]["STATS"] = {}
            self.user[user.id]["HISTO"] = []
            self.user[user.id]["SAVED"] = []
            self.user[user.id]["PERSO"]["CONFIDENCE"]["FANTOME"] = True
            self.save()
        else:
            self.user[user.id]["PERSO"]["CONFIDENCE"]["FANTOME"] = False
            self.event(user, "autre", "?", "Est sorti(e) du mode fantôme")
            self.save()
        return True

    def trad_day(self, input):
        if input.lower() == "monday":
            return "Lundi"
        elif input.lower() == "tuesday":
            return "Mardi"
        elif input.lower() == "wednesday":
            return "Mercredi"
        elif input.lower() == "thursday":
            return "Jeudi"
        elif input.lower() == "friday":
            return "Vendredi"
        elif input.lower() == "saturday":
            return "Samedi"
        else:
            return "Dimanche"

    def find_pseudo(self, term: str, strict = False):
        possible = []
        for p in self.user:
            if "PSEUDOS" in self.user[p]["STATS"]:
                for i in self.user[p]["STATS"]["PSEUDOS"]:
                    if term.lower() in i.lower():
                        possible.append([self.user[p]["ID"], i])
            if strict is False:
                if "N_PSEUDOS" in self.user[p]["STATS"]:
                    for i in self.user[p]["STATS"]["N_PSEUDOS"]:
                        if term.lower() in i.lower():
                            if self.user[p]["ID"] not in possible:
                                possible.append([self.user[p]["ID"], i])
        if possible != []:
            return possible
        else:
            return False

    def pop_class(self, user, top=5):
        liste = []
        for p in self.user:
            n = 0
            for u in self.user:
                if "MENTION" in self.user[u]["STATS"]:
                    if p in self.user[u]["STATS"]["MENTION"]:
                        n += self.user[u]["STATS"]["MENTION"][p]
            t = self.user[p]["BORN"] / (60*60*24)
            mn = n/t
            if self.user[p]["ID"] == user.id:
                k = [mn, self.user[p]["ID"]]
            liste.append([mn, self.user[p]["ID"]])
        sort = sorted(liste, key=operator.itemgetter(0))
        sort.reverse()
        place = sort.index(k)
        sort = sort[:top]
        return [sort, place]

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

#,Commandes >>>>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<<<<<<<

    @commands.command(name="logs", pass_context=True)
    async def changelog(self, ctx):
        """Informations sur la dernière MAJ Majeure de EGO."""
        em = discord.Embed(color=0x5184a5)
        c1 = "[BETA] Ajout des paramètres perso (&options)\n" \
             "[BETA] Ajout du mode 'fantôme'\n" \
             "Ajout de l'affichage du site\n" \
             "Nouveau suivi de la bibliothèque de jeux\n" \
             "Changements mineurs d'affichage\n" \
             "Affichage de la bibliothèque de jeux\n" \
             "Ajout comparaison de bibliothèques\n" \
             "Nouvel algorithme de détection + rapide\n" \
             "Nouvel affichage &logs\n" \
             "Ajout de &find\n" \
             "Améliorations de l'affichage de &jeu\n" \
             "Réajout temporaire de &epop (ancien algorithme adapté)"
        em.add_field(name="Version 2.2", value=c1)
        c2 = "Ajout des statistiques serveur détaillés\n" \
             "Réorganisation des commandes, rassemblées sous &ego (sauf &card et &scard)"
        em.add_field(name="Version 2.3", value=c2)
        bt = "Notifications (Anniversaire...)\n" \
             "Retour des relations\n" \
             "Historique complet"
        em.add_field(name="Bientôt", value=bt, inline=False)
        em.set_footer(text="Dernière MAJ publiée le 05/07", icon_url="http://i.imgur.com/DsBEbBw.png")
        await self.bot.say(embed=em)

    @commands.group(name="ego", pass_context=True)
    async def _ego(self, ctx):
        """Commandes EGO"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @_ego.command(pass_context=True, no_pm=True)
    async def stats(self, ctx):
        """Affiche les détails des statistiques sur le serveur."""
        server = ctx.message.server
        today = time.strftime("%d/%m/%Y", time.localtime())
        saut = 0
        day = menu = None
        retour = False
        while retour is False:
            if saut == 0:
                day = today
            elif saut > 0:
                day = time.strftime("%d/%m/%Y", time.localtime(time.mktime(time.strptime(today, "%d/%m/%Y")) - (86400 * saut)))
            else:
                await self.bot.say("**Erreur** | Impossible d'aller dans le futur, ça risquerait de détruire l'Espace-Temps...")
                return
            em = discord.Embed(title="EGO Stats | {} - *{}*".format(server.name, day), color=ctx.message.author.color)
            em.set_thumbnail(url=server.icon_url)
            if day in self.glob["NB_MSG"]:
                tot = ""
                total = 0
                try:
                    for c in self.glob["NB_MSG"][day]:
                        if not self.bot.get_channel(c).is_private:
                            if self.bot.get_channel(c).server.id == server.id:
                                nom = self.bot.get_channel(c).name.title()
                                tot += "**{}** {}\n".format(nom, self.glob["NB_MSG"][day][c])
                                total += self.glob["NB_MSG"][day][c]
                except:
                    total = 0
                    for c in self.glob["NB_MSG"][day]:
                        total += self.glob["NB_MSG"][day][c]
                tot += "\n**Total** {}\n".format(total)
                if day in self.glob["BOT_MSG"]:
                    tobot = 0
                    for b in self.glob["BOT_MSG"][day]:
                        tobot += self.glob["BOT_MSG"][day][b]
                    tot += "**Sans bot** {}".format(total - tobot)
                em.add_field(name="Messages", value="{}".format(tot))
            if day in self.glob["NB_JOIN"] and self.glob["NB_QUIT"]:
                if day in self.glob["NB_RETURN"]:
                    msg = "**Immigrés (Dont revenus):** {} ({})\n" \
                          "**Emigrés:** {}\n" \
                          "**Solde:** {}".format(self.glob["NB_JOIN"][day], self.glob["NB_RETURN"][day], self.glob["NB_QUIT"][day], (self.glob["NB_JOIN"][day] - self.glob["NB_QUIT"][day]))
                else:
                    msg = "**Immigrés:** {}\n" \
                          "**Emigrés:** {}\n" \
                          "**Solde:** {}".format(self.glob["NB_JOIN"][day],
                                                 self.glob["NB_QUIT"][day],
                                                 (self.glob["NB_JOIN"][day] - self.glob["NB_QUIT"][day]))
                em.add_field(name="Flux migratoire", value="{}".format(msg))
            em.set_footer(text="Données issues de EGO | V2.3 (&logs)", icon_url="http://i.imgur.com/DsBEbBw.png")
            if menu == None:
                menu = await self.bot.say(embed=em)
            else:
                await self.bot.clear_reactions(menu)
                menu = await self.bot.edit_message(menu, embed=em)
            await self.bot.add_reaction(menu, "⏪")
            if saut > 0:
                await self.bot.add_reaction(menu, "⏩")
            await asyncio.sleep(1)
            act = await self.bot.wait_for_reaction(["⏪","⏩"], message=menu, timeout=60)
            if act == None:
                em.set_footer(text="---- Session expiré ----")
                await self.bot.edit_message(menu, embed=em)
                return
            elif act.reaction.emoji == "⏪":
                saut += 1
            elif act.reaction.emoji == "⏩":
                saut -= 1
            else:
                pass

    @_ego.command(pass_context=True, no_pm=True)
    async def epop(self, ctx, top=5):
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
        em.add_field(name="Top {}".format(top), value=msg)
        em.add_field(name="Votre place", value="{}e".format(place + 1))
        em.set_footer(text="Ces informations sont issues du système Ego | V2.3 (&logs)", icon_url="http://i.imgur.com/DsBEbBw.png")
        await self.bot.say(embed=em)

    @_ego.command(pass_context=True)
    async def jeu(self, ctx, opt: str=None):
        """Permet de voir qui possède le jeu auquel vous jouez.
        
        Si un jeu est précisé, il sera recherché au lieu de celui que vous êtes en train de jouer."""
        author = ctx.message.author
        if opt is None:
            if author.game != None:
                opt = author.game.name.lower()
            else:
                await self.bot.say("Vous ne jouez à aucun jeu.")
                return
        else:
            opt = opt.lower()
        server = ctx.message.server
        for m in server.members:
            if m.game != None:
                ego = self.ego.log(m)
                if "JEUX" in ego.perso:
                    if m.game.name.lower() not in ego.perso["JEUX"]:
                        ego.perso["JEUX"].append(m.game.name.lower())
                else:
                    ego.perso["JEUX"] = [m.game.name.lower()]
        if self.ego.poss_jeu(opt) == False:
            await self.bot.say("Je n'ai pas assez de données pour ce jeu, je suis pour le moment incapable de vous dire si d'autres personnes le possède.\nRéssayez une prochaine fois !")
            return
        liste = self.ego.poss_jeu(opt)[0]
        nom = self.ego.poss_jeu(opt)[1]
        msg = ""
        n = 1
        for p in liste:
            msg += "- *{}*\n".format(server.get_member(p))
            if len(msg) >= 1950 * n:
                n += 1
                msg += "!!"
        else:
            lmsg = msg.split("!!")
            try:
                if "!!" not in lmsg:
                    em = discord.Embed(color=author.color)
                    em.add_field(name="Propriétaires de {}*".format(nom.title()), value=msg)
                    em.set_footer(text="* ou version similaire")
                    await self.bot.say(embed=em)
                else:
                    await self.bot.say("Propriétaires de {} *ou version similaire*\n\n")
                    for m in lmsg:
                        await self.bot.say(m)
            except:
                await self.bot.say("Le nombre de joueurs est trop important. Discord n'autorise pas l'affichage d'un tel pavé...")

    @_ego.command(pass_context=True, no_pm=True)
    async def find(self, ctx, recherche, strict:bool = False):
        """Permet de retrouver à qui appartient un pseudo ou un surnom.
        Si le pseudo est composé, utilisez des guillemets pour l'entrer.
        
        Prend en compte les anciens pseudos enregistrés par EGO."""
        liste = self.ego.find_pseudo(recherche, strict)
        if liste is False:
            await self.bot.say("Aucun résultat trouvé. Essayez d'être moins précis et/ou vérifiez l'orthographe.")
            return
        server = ctx.message.server
        msg = ""
        for p in liste:
            try:
                mp = server.get_member(p[0])
                msg += "**{}** ({})\n".format(str(mp), p[1])
            except:
                msg += "*{}* ({})\n".format(p[0], p[1])
        em = discord.Embed(color=ctx.message.author.color)
        em.add_field(name="Résultats de votre recherche", value=msg)
        em.set_footer(text="Informations issues de EGO | V2.3 (&logs)", icon_url="http://i.imgur.com/DsBEbBw.png")
        await self.bot.say(embed=em)

    @_ego.command(aliases=["opt"], pass_context=True, no_pm=True)
    async def options(self, ctx):
        """Permet de modifier vos options EGO."""
        author = ctx.message.author
        user = author
        ego = self.ego.log(author)
        if not user.bot:
            ec = self.ego.stat_color(user)
        else:
            ec = 0x2e6cc9
        if self.ego.is_fantome(user) is False:
            retour = False
            while retour is False:
                em = discord.Embed(color=ec, title="EGO | Vos paramètres")
                liste = "**1** | Informations personnelles\n" \
                        "**2** | Confidentialité\n" \
                        "**3** | Notifications\n" \
                        "**Q** | Quitter"
                em.add_field(name="Menu", value=liste)
                em.set_footer(text="Saisissez le chiffre correspondant au sous-menu désiré",
                              icon_url="http://i.imgur.com/DsBEbBw.png")
                menu = await self.bot.whisper(embed=em)
                verif = False
                while verif != True:
                    rep = await self.bot.wait_for_message(timeout=30, author=ctx.message.author, channel=menu.channel)
                    if rep == None:
                        await self.bot.whisper("*Absence de réponse* | Bye :wave:")
                        return
                    elif rep.content == "1":
                        verif = True
                        fini = False
                        while fini != True:
                            em = discord.Embed(color=ec, title="EGO | Informations perso.")
                            liste = "**A** | Anniversaire\n" \
                                    "**B** | Bibliothèque de jeux\n" \
                                    "**S** | Site personnel\n" \
                                    "**R** | Retour au menu\n" \
                                    "**Q** | Quitter"
                            em.add_field(name="Options", value=liste)
                            em.set_footer(text="Saisissez la lettre correspondant à l'option désirée",
                                          icon_url="http://i.imgur.com/DsBEbBw.png")
                            sub_menu = await self.bot.whisper(embed=em)
                            verif2 = False
                            while verif2 != True:
                                rep2 = await self.bot.wait_for_message(timeout=30, author=ctx.message.author,
                                                                       channel=menu.channel)
                                if rep2 == None:
                                    await self.bot.whisper("*Absence de réponse* | Bye :wave:")
                                    return
                                elif rep2.content.lower() == "a":
                                    verif2 = True
                                    if "ANNIV" not in ego.perso:
                                        notif = "**Saisir votre anniversaire**\n" \
                                                "*Il est possible de saisir la date d'anniversaire afin de proposer divers services supplémentaires*\n" \
                                                "*comme notifier d'autres membres proches de vous que c'est votre anniversaire afin que personne ne l'oublie.*\n" \
                                                "Utilisez le format 'dd/mm' pour saisir votre anniversaire. \nPour annuler, saisissez 'non'."
                                    else:
                                        if ego.perso["ANNIV"] is None:
                                            notif = "**Saisir votre anniversaire**\n" \
                                                    "*Il est possible de saisir la date d'anniversaire afin de proposer divers services supplémentaires*\n" \
                                                    "*comme notifier d'autres membres proches de vous que c'est votre anniversaire afin que personne ne l'oublie.*\n" \
                                                    "Utilisez le format 'dd/mm' pour saisir votre anniversaire. \nPour annuler, saisissez 'non'."
                                        else:
                                            notif = "**Modifier votre anniversaire**\n" \
                                                    "*Il est possible de saisir la date d'anniversaire afin de proposer divers services supplémentaires*\n" \
                                                    "*comme notifier d'autres membres proches de vous que c'est votre anniversaire afin que personne ne l'oublie.*\n" \
                                                    "Utilisez le format 'dd/mm' pour saisir votre anniversaire. \nPour annuler, saisissez 'non'. \nPour le retirer, saisissez 'stop'."
                                    await self.bot.whisper(notif)
                                    verif3 = False
                                    while verif3 != True:
                                        rep3 = await self.bot.wait_for_message(timeout=30, author=ctx.message.author,
                                                                               channel=menu.channel)
                                        if rep3 == None:
                                            await self.bot.whisper("*Absence de réponse* | Retour au menu")
                                            verif3 = True
                                        elif len(rep3.content.lower()) == 5:
                                            try:
                                                node = time.strptime(rep3.content, "%d/%m")
                                                cont = True
                                            except:
                                                await self.bot.whisper("*Format invalide* | Réessayez")
                                                cont = False
                                            if cont != False:
                                                verif3 = True
                                                await self.bot.whisper(
                                                    "*Vous fêterez votre prochain anniversaire le {}/{}.*\nEst-ce exact ? (O/N)".format(
                                                        node.tm_mday, node.tm_mon))
                                                att = await self.bot.wait_for_message(timeout=30,
                                                                                      author=ctx.message.author,
                                                                                      channel=menu.channel)
                                                if att == None:
                                                    await self.bot.whisper("*Absence de réponse* | Retour au menu")
                                                elif att.content.lower() == "o" or "oui":
                                                    await self.bot.whisper("**Enregistré !**")
                                                    ego.perso["ANNIV"] = rep3.content.lower()
                                                    self.ego.save()
                                                else:
                                                    await self.bot.whisper("*Annulation* | Retour au menu")
                                        elif rep3.content.lower() in ["non", "annuler"]:
                                            await self.bot.whisper("*Annulation* | Retour au menu")
                                            verif3 = True
                                        elif rep3.content.lower() == "stop":
                                            await self.bot.whisper(
                                                "*Votre anniversaire à été effacé de mes données* | Retour au menu")
                                            ego.perso["ANNIV"] = None
                                            self.ego.save()
                                            verif3 = True
                                        else:
                                            await self.bot.whisper("*Format invalide* | Réessayez")
                                elif rep2.content.lower() == "b":
                                    verif2 = True
                                    biblio = self.ego.biblio(user)
                                    if biblio != False:
                                        if biblio != []:
                                            msg = "**Voici vos jeux possédés**:\n"
                                            for g in biblio:
                                                msg += "*{}*\n".format(g.title())
                                            msg += "\nCes jeux sont vérifiés automatiquement par EGO. Cependant certains 'faux-jeux' (Status modifiés pour le fun) outrepassent cette sécurité\n" \
                                                   "Il est donc possible de retirer un jeu détecté comme valide.\n" \
                                                   "__Pour en retirer un, saisissez son nom complet__ sinon tapez 'annuler'."
                                            await self.bot.whisper(msg)
                                            verif3 = False
                                            while verif3 != True:
                                                rep3 = await self.bot.wait_for_message(timeout=60,
                                                                                       author=ctx.message.author,
                                                                                       channel=menu.channel)
                                                if rep3 == None:
                                                    await self.bot.whisper("*Absence de réponse* | Retour au menu")
                                                    verif3 = True
                                                elif rep3.content.lower() in [k.lower() for k in biblio]:
                                                    ego.perso["JEUX"].remove(rep3.content.lower())
                                                    self.ego.save()
                                                    msg = "**Liste actualisée**:\n"
                                                    biblio = self.ego.biblio(user)
                                                    if biblio != []:
                                                        for g in biblio:
                                                            msg += "*{}*\n".format(g.title())
                                                    else:
                                                        msg += "Votre bibliothèque est vide."
                                                    await self.bot.whisper(
                                                        "{}\n\n**{} retiré.**\n*Pour continuer, saisissez un autre jeu, sinon tapez 'annuler'.*".format(
                                                            rep3.content.title()))
                                                elif rep3.content.lower() in ["non", "annuler"]:
                                                    await self.bot.whisper("*Action annulée* | Retour au menu")
                                                    verif3 = True
                                                else:
                                                    await self.bot.whisper(
                                                        "*Absent de votre bibliothèque* | Réessayez (Tapez 'annuler' pour retourner au menu)")
                                        else:
                                            await self.bot.whisper(
                                                "*Votre bibliothèque détectée semble vide* | Retour menu")
                                    else:
                                        await self.bot.whisper(
                                            "*Vous n'avez pas de bibliothèque détectée* | Retour menu")
                                elif rep2.content.lower() == "s":
                                    verif2 = True
                                    notif = "**Saisir son site internet**\n" \
                                            "*Il est possible de saisir l'URL de son site internet afin de l'afficher sur votre carte*\n" \
                                            "*Celui-ci sera accessible en cliquant sur votre pseudo dans &card*\n" \
                                            "Pour l'ajouter, entrez l'URL du site. Sinon, tapez 'annuler'"
                                    await self.bot.whisper(notif)
                                    verif3 = False
                                    while verif3 != True:
                                        rep3 = await self.bot.wait_for_message(timeout=30, author=ctx.message.author,
                                                                               channel=menu.channel)
                                        if rep3 == None:
                                            await self.bot.whisper("*Absence de réponse* | Retour au menu")
                                            verif3 = True
                                        elif "http://" in rep3.content.lower():
                                            verif3 = True
                                            if "SITE" not in ego.perso:
                                                ego.perso["SITE"] = rep3.content.lower()
                                                await self.bot.whisper("*Site ajouté !* | Retour au menu")
                                            else:
                                                ego.perso["SITE"] = rep3.content.lower()
                                                await self.bot.whisper("*Site modifié !* | Retour au menu")
                                        elif rep3.content.lower() in ["non", "annuler"]:
                                            await self.bot.whisper("*Annulation* | Retour au menu")
                                            verif3 = True
                                        else:
                                            await self.bot.whisper(
                                                "*Format invalide* | Réessayez (Ou tapez 'annuler' pour retourner au menu)")
                                elif rep2.content.lower() == "r":
                                    fini = True
                                    verif2 = True
                                    await self.bot.whisper("*Retour au menu*")
                                elif rep2.content.lower() == "q":
                                    await self.bot.whisper("**Bye** :wave:")
                                    return
                                else:
                                    await self.bot.whisper(
                                        "Non reconnu. Tapez la lettre correspondant à l'option désirée.")
                    elif rep.content == "2":
                        verif = True
                        if "CONFIDENCE" not in ego.perso:
                            ego.perso["CONFIDENCE"] = {}
                        base = ["RATIO", "JEUX", "RELATIONS", "PROFIL", "HISTO", "FANTOME"]
                        for e in base:
                            if e not in ego.perso["CONFIDENCE"]:
                                if e != "FANTOME":
                                    ego.perso["CONFIDENCE"][e] = True
                                else:
                                    ego.perso["CONFIDENCE"][e] = False
                        fini = False
                        while fini != True:
                            em = discord.Embed(color=ec, title="EGO | Confidentialité")
                            liste = "**M** | Ratio de message ({})\n" \
                                    "**B** | Bibliothèque de jeux ({})\n" \
                                    "**S** | Relations ({})\n" \
                                    "**H** | Historique ({})\n" \
                                    "**P** | Profil personnel ({})\n" \
                                    "**F** | Mode fantôme ({})\n" \
                                    "**R** | Retour au menu\n" \
                                    "**Q** | Quitter".format(ego.perso["CONFIDENCE"]["RATIO"],
                                                             ego.perso["CONFIDENCE"]["JEUX"],
                                                             ego.perso["CONFIDENCE"]["RELATIONS"],
                                                             ego.perso["CONFIDENCE"]["HISTO"],
                                                             ego.perso["CONFIDENCE"]["PROFIL"],
                                                             ego.perso["CONFIDENCE"]["FANTOME"])
                            em.add_field(name="Options", value=liste)
                            em.set_footer(text="Saisissez la lettre correspondant à l'option désirée",
                                          icon_url="http://i.imgur.com/DsBEbBw.png")
                            sub_menu = await self.bot.whisper(embed=em)
                            verif2 = False
                            while verif2 != True:
                                rep2 = await self.bot.wait_for_message(timeout=30, author=ctx.message.author,
                                                                       channel=menu.channel)
                                if rep2 == None:
                                    await self.bot.whisper("*Absence de réponse* | Bye :wave:")
                                    return
                                elif rep2.content.lower() == "m":
                                    verif2 = True
                                    if ego.perso["CONFIDENCE"]["RATIO"] is True:
                                        await self.bot.whisper(
                                            "*Le ratio de message ne sera plus affiché sur votre carte EGO* | Retour Menu")
                                        ego.perso["CONFIDENCE"]["RATIO"] = False
                                        self.ego.save()
                                    else:
                                        if ego.perso["CONFIDENCE"]["RATIO"] is False:
                                            await self.bot.whisper(
                                                "*Le ratio de message sera affiché sur votre carte EGO* | Retour Menu")
                                            ego.perso["CONFIDENCE"]["RATIO"] = True
                                            self.ego.save()
                                elif rep2.content.lower() == "b":
                                    verif2 = True
                                    if ego.perso["CONFIDENCE"]["JEUX"] is True:
                                        await self.bot.whisper(
                                            "*Vos jeux ne seront plus affichés sur votre carte EGO* | Retour Menu")
                                        ego.perso["CONFIDENCE"]["JEUX"] = False
                                        self.ego.save()
                                    else:
                                        if ego.perso["CONFIDENCE"]["JEUX"] is False:
                                            await self.bot.whisper(
                                                "*Vos jeux seront affichés sur votre carte EGO* | Retour Menu")
                                            ego.perso["CONFIDENCE"]["JEUX"] = True
                                            self.ego.save()
                                elif rep2.content.lower() == "s":
                                    verif2 = True
                                    if ego.perso["CONFIDENCE"]["RELATIONS"] is True:
                                        await self.bot.whisper(
                                            "*Vos relations ne seront plus affichés sur votre carte EGO* | Retour Menu")
                                        ego.perso["CONFIDENCE"]["RELATIONS"] = False
                                        self.ego.save()
                                    else:
                                        if ego.perso["CONFIDENCE"]["RELATIONS"] is False:
                                            await self.bot.whisper(
                                                "*Vos relations seront affichés sur votre carte EGO* | Retour Menu")
                                            ego.perso["CONFIDENCE"]["RELATIONS"] = True
                                            self.ego.save()
                                elif rep2.content.lower() == "h":
                                    verif2 = True
                                    if ego.perso["CONFIDENCE"]["HISTO"] is True:
                                        await self.bot.whisper(
                                            "*Votre historique ne sera plus affiché sur votre carte EGO* | Retour Menu")
                                        ego.perso["CONFIDENCE"]["HISTO"] = False
                                        self.ego.save()
                                    else:
                                        if ego.perso["CONFIDENCE"]["HISTO"] is False:
                                            await self.bot.whisper(
                                                "*Votre historique sera affiché sur votre carte EGO* | Retour Menu")
                                            ego.perso["CONFIDENCE"]["HISTO"] = True
                                            self.ego.save()
                                elif rep2.content.lower() == "p":
                                    verif2 = True
                                    if ego.perso["CONFIDENCE"]["PROFIL"] is True:
                                        await self.bot.whisper(
                                            "*Vos informations perso. ne seront plus communiqués par EGO* | Retour Menu")
                                        ego.perso["CONFIDENCE"]["PROFIL"] = False
                                        self.ego.save()
                                    else:
                                        if ego.perso["CONFIDENCE"]["PROFIL"] is False:
                                            await self.bot.whisper(
                                                "*Vos informations perso. seront communiqués par EGO* | Retour Menu")
                                            ego.perso["CONFIDENCE"]["PROFIL"] = True
                                            self.ego.save()
                                elif rep2.content.lower() == "f":
                                    verif2 = True
                                    warning = "**Mode Fantôme**\n" \
                                              "Activer ce mode effacera toute information détenue par EGO jusqu'à ce jour et mettra votre profil 'en suspens'.\n" \
                                              "Cela signifie qu'aucune nouvelle donnée ne sera récoltée de vous jusqu'a que vous sortiez de ce mode.\n" \
                                              "En outre, votre carte EGO n'affichera que le stricte nécéssaire fourni par les serveurs Discord (Arrivée sur le serveur etc)\n" \
                                              "*Note: Certaines données tels que le suivi du changement de pseudo ne sont pas seulement gérés par EGO et ne pourraient être supprimées*\n\n" \
                                              "_Êtes-vous certain d'activer ce mode ?_ (O/N)"
                                    await self.bot.whisper(warning)
                                    verif3 = False
                                    while verif3 is False:
                                        rep3 = await self.bot.wait_for_message(timeout=60, author=ctx.message.author,
                                                                               channel=menu.channel)
                                        if rep3 == None:
                                            await self.bot.whisper("*Absence de réponse* | Retour au menu")
                                            verif3 = True
                                        elif rep3.content.lower() in ["oui", "o"]:
                                            if self.ego.suspens(ctx.message.author, True) == True:
                                                await self.bot.whisper(
                                                    "**Mode fantôme activé**\nPour en sortir, allez dans vos options et confirmez la sortie du mode.\n**Bye** :wave:")
                                            else:
                                                await self.bot.whisper("Il y a eu une erreur lors du changement de mode. Contactez Acrown#4424...")
                                            return
                                        else:
                                            await self.bot.whisper("*Annulation* | Retour au menu")
                                            verif3 = True
                                elif rep2.content.lower() == "r":
                                    await self.bot.whisper("*Retour au menu*")
                                    verif2 = True
                                    fini = True
                                elif rep2.content.lower() == "q":
                                    await self.bot.whisper("**Bye** :wave:")
                                    return
                                else:
                                    await self.bot.whisper("*Réponse invalide* | Réessayez")
                    elif rep.content == "3":
                        verif = True
                        await self.bot.whisper("*Page en construction* | Retour au menu")
                    elif rep.content.lower() == "q":
                        await self.bot.whisper("**Bye** :wave:")
                        return
                    else:
                        await self.bot.whisper("*Réponse invalide* | Réessayez")
        else:
            menu = await self.bot.whisper(
                "**Voulez-vous sortir du mode fantôme et réautoriser le suivi par EGO ?** (O/N)")
            verifs = False
            while verifs is False:
                rep = await self.bot.wait_for_message(timeout=30, author=ctx.message.author, channel=menu.channel)
                if rep is None:
                    await self.bot.whisper("*Absence de réponse* | Bye :wave:")
                    return
                elif rep.content.lower() in ["o", "oui"]:
                    await self.bot.whisper("**Sortie du mode fantôme**\n"
                                           "Votre profil n'est plus suspendu !")
                    self.ego.suspens(ctx.message.author, False)
                    return
                else:
                    await self.bot.whisper("Bye :wave:")
                    return

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
        msg = "{} jours"
        if self.ego.is_fantome(user) is False:
            egodate = self.ego.since(user, "jour")
            if egodate < 1:
                egodate = 1
            if passed < egodate:
                msg = "+{} jours"
        em.add_field(name="Nb de jours", value=msg.format(passed))
        if self.ego.aff_auto(user, "RATIO") is True:
            em.add_field(name="Ratio de messages", value="{}/jour".format(str(
                round(ego.stats["NB_MSG"] / egodate, 2))))
        rolelist = [r.name for r in user.roles]
        rolelist.remove('@everyone')
        em.add_field(name="Rôles", value=rolelist)
        if self.ego.aff_auto(user, "HISTO") is True:
            liste = ego.histo[-3:]
            liste.reverse()
            hist = ""
            if liste != []:
                for i in liste:
                    hist += "**{}** *{}*\n".format(i[2], i[3])
            else:
                hist = "Aucun historique"
            em.add_field(name="Historique", value="{}".format(hist))
        if self.ego.is_fantome(user) is True:
            fantome = "Cette personne n'est pas suivie par le système EGO"
        else:
            fantome = "Certaines informations proviennent du système EGO"
        em.set_footer(
            text="{} | V2.3 (&logs)".format(fantome), icon_url="http://i.imgur.com/DsBEbBw.png")
        msg = await self.bot.say(embed=em)

        await self.bot.add_reaction(msg, "🎮")
        await asyncio.sleep(1)
        rap = await self.bot.wait_for_reaction("🎮", message=msg, timeout=20)
        if rap == None:
            pass
        elif rap.reaction.emoji == "🎮":
            if self.ego.aff_auto(user, "JEUX") is True:
                if user != ctx.message.author:
                    em = discord.Embed(title="Jeux de {}".format(str(user)), color=ec)
                    biblio = self.ego.biblio(user)
                    selfbib = self.ego.biblio(ctx.message.author)
                    verif = []
                    msg = ""
                    if biblio != False:
                        if biblio != []:
                            for g in biblio:
                                if g.lower() not in verif:
                                    if selfbib != False:
                                        if selfbib != []:
                                            if g in selfbib:
                                                msg += "***{}***\n".format(g.title())
                                                verif.append(g.lower())
                                            else:
                                                msg += "*{}*\n".format(g.title())
                                                verif.append(g.lower())
                                        else:
                                            msg += "*{}*\n".format(g.title())
                                            verif.append(g.lower())
                                    else:
                                        msg += "*{}*\n".format(g.title())
                                        verif.append(g.lower())
                                else:
                                    pass
                        else:
                            msg = "Bibliothèque vide."
                    else:
                        msg = "Bibliothèque vide."
                    em.add_field(name="Bibliothèque", value=msg)
                    em.set_footer(text="Les jeux en commun sont affichés en gras", icon_url="http://i.imgur.com/DsBEbBw.png")
                else:
                    em = discord.Embed(title="Vos jeux", color=ec)
                    biblio = self.ego.biblio(user)
                    verif = []
                    msg = ""
                    if biblio != False:
                        if biblio != []:
                            for g in biblio:
                                if g.lower() not in verif:
                                    verif.append(g.lower())
                                    msg += "*{}*\n".format(g.title())
                                else:
                                    pass
                        else:
                            msg = "Bibliothèque vide."
                    else:
                        msg = "Bibliothèque vide."
                    em.add_field(name="Bibliothèque", value=msg)
                    em.set_footer(text="Certains jeux possédés peuvent ne pas avoir été vérifiés", icon_url="http://i.imgur.com/DsBEbBw.png")
                await self.bot.say(embed=em)
            else:
                await self.bot.say("L'utilisateur ne souhaite pas partager sa bibliothèque.")
        else:
            return

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
            if auj in self.glob["NB_JOIN"]:
                if auj in self.glob["NB_QUIT"]:
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
        else:
            var = "?"
        em.add_field(name="Nb membres", value="**{}**/{} (*{}*)".format(online, total_users, var))
        passed = (ctx.message.timestamp - server.created_at).days
        em.add_field(name="Age", value="{} jours".format(passed))
        em.set_thumbnail(url=server.icon_url)
        em.set_footer(text="Certaines informations proviennent du système Ego | V2.3 (&logs)", icon_url="http://i.imgur.com/DsBEbBw.png")
        msg = await self.bot.say(embed=em)

        await self.bot.add_reaction(msg, "📊")
        await asyncio.sleep(1)
        rap = await self.bot.wait_for_reaction("📊", message=msg, timeout=20)
        if rap == None:
            pass
        elif rap.reaction.emoji == "📊":
            em = discord.Embed(title="Statistiques {}".format(server.name), color=ctx.message.author.color)
            aff = True
            if "NB_JOIN" and "NB_QUIT" in self.glob:
                if auj in self.glob["NB_JOIN"]:
                    todayj = self.glob["NB_JOIN"][auj]
                    if auj in self.glob["NB_QUIT"]:
                        todayq = self.glob["NB_QUIT"][auj]
                        if hier in self.glob["NB_JOIN"]:
                            laj = self.glob["NB_JOIN"][hier]
                            if hier in self.glob["NB_QUIT"]:
                                laq = self.glob["NB_QUIT"][hier]
                            else:
                                aff = False
                        else:
                            aff = False
                    else:
                        aff = False
                else:
                    aff = False
            else:
                aff = False
            if aff != False:
                to = "Arrivées : **{}**\n" \
                     "Sorties : **{}**"
                em.add_field(name="Aujourd'hui ({})".format(auj), value=to.format(todayj, todayq))
                em.add_field(name="Hier ({})".format(hier), value=to.format(laj, laq))
            else:
                em.add_field(name="Erreur", value="Données trop minces pour afficher des statistiques")
            em.set_footer(
                text="Informations issues de EGO | Pour obtenir des détails, utilisez '&ego servstats' | V2.3 (&logs)",
                icon_url="http://i.imgur.com/DsBEbBw.png")
            await self.bot.say(embed=em)
        else:
            return

    @commands.command(name="egologs", pass_context=True, hidden=True)
    @checks.admin_or_permissions(kick_members=True)
    async def debug(self, ctx):
        """Upload les fichiers de débug EGO."""
        channel = ctx.message.channel
        chemin = 'data/ego/profil.json'
        chemin2 = 'data/ego/glob.json'
        await self.bot.say("Upload en cours...")
        await asyncio.sleep(0.25)
        try:
            await self.bot.send_file(channel, chemin)
            await asyncio.sleep(1)
            await self.bot.send_file(channel, chemin2)
        except:
            await self.bot.say("Impossible d'upload le fichier.")

#LISTENERS

    async def l_msg(self, message):
        author = message.author
        channel = message.channel
        server = message.server
        if author.bot is True:
            if "BOT_MSG" in self.glob:
                if server:
                    today = time.strftime("%d/%m/%Y", time.localtime())
                    if today in self.glob["BOT_MSG"]:
                        if channel.id in self.glob["BOT_MSG"][today]:
                            self.glob["BOT_MSG"][today][channel.id] += 1
                        else:
                            self.glob["BOT_MSG"][today][channel.id] = 1
                    else:
                        self.glob["BOT_MSG"][today] = {} #Ngb
            else:
                self.glob["BOT_MSG"] = {} #Ngb
        if "NB_MSG" in self.glob:
            if server:
                today = time.strftime("%d/%m/%Y", time.localtime())
                if today in self.glob["NB_MSG"]:
                    if channel.id in self.glob["NB_MSG"][today]:
                        self.glob["NB_MSG"][today][channel.id] += 1
                    else:
                        self.glob["NB_MSG"][today][channel.id] = 1
                else:
                    self.glob["NB_MSG"][today] = {} #Ngb
            else:
                pass
        else:
            self.glob["NB_MSG"] = {} #Ngb
        fileIO("data/ego/glob.json", "save", self.glob)

        ego = self.ego.log(author)
        if self.ego.is_fantome(author) is True:
            return
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
            if today not in self.glob["NB_RETURN"]:
                self.glob["NB_RETURN"][today] = 0
        else:
            self.glob["NB_JOIN"] = {} #Ngb

        ego = self.ego.log(user)
        if self.ego.is_fantome(user) is True:
            return
        if ego.born < (time.time() - 500):
            if "NB_RETURN" in self.glob:
                if today in self.glob["NB_RETURN"]:
                    self.glob["NB_RETURN"][today] += 1
                else:
                    self.glob["NB_RETURN"][today] = 1
            else:
                self.glob["NB_RETURN"] = {} #Ngb

        if "ENTREES" in ego.stats:
            ego.stats["ENTREES"] += 1
        else:
            ego.stats["ENTREES"] = 1
        self.ego.event(user, "presence", ">", "Est arrivé sur le serveur")
        fileIO("data/ego/glob.json", "save", self.glob)
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
            if today not in self.glob["NB_RETURN"]:
                self.glob["NB_RETURN"][today] = 0
        else:
            self.glob["NB_QUIT"] = {} #Ngb
        fileIO("data/ego/glob.json", "save", self.glob)

        ego = self.ego.log(user)
        if self.ego.is_fantome(user) is True:
            return
        if "SORTIES" in ego.stats:
            ego.stats["SORTIES"] += 1
        else:
            ego.stats["SORTIES"] = 1
        self.ego.event(user, "presence", "<", "A quitté le serveur")
        self.ego.save()

    async def l_react(self, reaction, user):
        if "REACTS" in self.glob:
            today = time.strftime("%d/%m/%Y", time.localtime())
            if reaction.custom_emoji is True:
                if today in self.glob["REACTS"]:
                    if reaction.emoji.name in self.glob["REACTS"][today]:
                        self.glob["REACTS"][today][reaction.emoji.name] += 1
                    else:
                        self.glob["REACTS"][today][reaction.emoji.name] = 1
                else:
                    self.glob["REACTS"][today] = {}
                    self.glob["REACTS"][today][reaction.emoji.name] = 1
        else:
            self.glob["REACTS"] = {} #Ngb
        fileIO("data/ego/glob.json", "save", self.glob)

    async def l_profil(self, b, a): #On cherche un changement dans le profil
        ego = self.ego.log(a)
        if self.ego.is_fantome(a) is True:
            return
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
        if a.game != None:
            if "JEUX" in ego.perso:
                if a.game.name != None:
                    if a.game.name.lower() not in ego.perso["JEUX"]:
                        ego.perso["JEUX"].append(a.game.name.lower())
            else:
                ego.perso["JEUX"] = [] #Ngb
        self.ego.save()

        #TODO Ajouter VoiceState dans le cadre du calcul d'Activité

    async def l_ban(self, user):
        ego = self.ego.log(user)
        if self.ego.is_fantome(user) is True:
            return
        if "BANS" in ego.stats:
            ego.stats["BANS"] += 1
        else:
            ego.stats["BANS"] = 1
        self.ego.event(user, "presence", "#", "A été banni(e)")
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
    bot.add_listener(n.l_react, "on_reaction_add")
    bot.add_listener(n.l_join, "on_member_join") #A chaque membre qui rejoint
    bot.add_listener(n.l_quit, "on_member_remove") #A chaque membre qui part
    bot.add_listener(n.l_profil, "on_member_update") #Lorsqu'un membre modifie son profil (avatar, pseudo...)
    bot.add_listener(n.l_ban, "on_member_ban") #Lorsqu'un membre est banni
    bot.add_cog(n)