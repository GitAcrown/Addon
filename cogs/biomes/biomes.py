import os
import asyncio
import random
import time
import datetime
import discord
from operator import itemgetter
from discord.ext import commands
from .utils.dataIO import fileIO, dataIO
from random import randint
from .utils import checks
from __main__ import send_cmd_help
try:   # Check Tabulate (Si activé)
    from tabulate import tabulate
    tabulateAvailable = True
except:
    tabulateAvailable = False

#Version 1.0

    #TODO:
    #- Niveaux de difficultés (Normal/Difficile//Hardcore)
    #- Son Audio à la mort de personnes ?
    #- Possibilité de créer directement des extensions
    #- Ajout d'actions
    #- Ajout dialogues
    #- Classement

# DIALOGUES UNIVERSEL
etats = ["Sain","Malade","Blessé","Empoisonné"]
d_repos = ["**{0}** se repose dans **{1}**","**{0}** trouve **{1}** et décide de s'y reposer","**{0}** tombe et découvre **{1}**","**{0}** décide de s'abriter dans **{1}**", "**{0}** s'abrite d'urgence dans **{1}**"]
d_chasse = ["**{0}** se décide à chasser **{1}** passant à proximité","**{0}** se met à courser **{1}**","**{0}** dévore **{1}** chassé juste avant","**{0}** mange **{1}**","**{0}** descend **{1}**"]
d_cueil = ["**{0}** récolte **{1}**","**{0}** trouve **{1}**","**{0}** ramasse **{1}**","**{0}** arrache **{1}**"]
d_trouve = ["**{0}** trouve **{1}** et s'en équippe (*{2}*)","**{0}** trébuche sur **{1}** et le ramasse (*{2}*)","**{0}** trouve **{1}** accroché (*{2}*)","**{0}** vole **{1}** dans un sac (*{2}*)","**{0}** trouve **{1}** sur le sol (*{2}*)"]
d_reposgrp = ["**{0}**, **{1}** et **{2}** décident de se reposer dans **{3}**","**{1}** se rassemble avec **{0}** et **{2}** dans **{3}** pour discuter autour d'un feu.","**{1}** se regroupe avec **{0}** et **{2}** dans **{3}** pour se poser tranquillement."]
d_combat = ["**{0}** et **{1}** se provoquent en duel","**{1}** attaque **{0}** par surprise","**{0}**, frappé par **{1}**, réplique","**{1}** se met à poursuivre **{0}**"]
d_combat2 = ["**{0}** et **{1}** prennent par surprise **{2}** et **{3}** qui étaient tranquillement en train de camper","**{2}** et **{3}** prennent en chasse **{1}** et **{0}** !"]
d_piege = ["**{0}** s'est fait piéger par **{1}** !", "**{0}** est tombé dans le piège de **{1}**", "**{1}** vient de remarquer que **{0}** est tombé dans son piège !", "**{0}** s'est pris le piège de **{1}** !"]

class Biomes:
    """Puisse le sort vous être favorable !"""

    def __init__(self, bot):
        self.bot = bot
        self.player = dataIO.load_json("data/biomes/player.json")
        self.system = dataIO.load_json("data/biomes/system.json")
        self.charge = dataIO.load_json("data/biomes/charge.json")
        self.sponsor = dataIO.load_json("data/biomes/sponsor.json")
        defpar = {"SPONSOR_NB": 0, "STOP" : False, "EXT" : None,"OPEN" : False, "PLAYING" : False,"PLAYERS" : 0,"MAX_PLAYERS" : 12, "SAISON" : 1}
        extdiv = "data/biomes/ext/{}.txt"

    @commands.group(pass_context=True)
    @checks.admin_or_permissions(kick_members=True)
    async def setbms(self, ctx):
        """Commandes de Gestion Biomes"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @setbms.command(pass_context=True)
    async def resetbms(self, ctx):
        """Permet de reset le module en cas d'urgence."""
        self.reset()
        await self.bot.say("Reset effectué avec succès.")

    @setbms.command(pass_context=True)
    async def maxp(self, ctx, val:int):
        """Change le maximum de joueurs dans une session.

        Minimum 8 - Maximum 64"""
        if val >= 2 and val <= 64:
            self.system["MAX_PLAYERS"] = val
            self.save("system")
            await self.bot.say("Il y aura maintenant {} joueurs par partie.".format(val))
        else:
            await self.bot.say("Au minimum 8 et maximum 64 joueurs.")

    @setbms.command(pass_context=True)
    async def saison(self, ctx, val:int):
        """Change la saison de la prochaine session."""
        if val >= 1:
            self.system["SAISON"] = val
            self.save("system")
            await self.bot.say("Nous sommes désormais à la saison {}".format(val))
        else:
            await self.bot.say("La saison ne peut pas être nulle ou négative.")

    @setbms.command(pass_context=True)
    async def stop(self, ctx):
        """Stop le jeu en pleine partie."""
        if self.system["STOP"] == False:
            self.system["STOP"] = True
            self.save("system")
            await self.bot.say("La partie va bientôt être stoppée")
        else:
            await self.bot.say("Le stop est déjà activé.")

    @setbms.command(pass_context=True)
    async def ext(self, ctx, val:str):
        """Change l'extension de la session."""
        nom = val
        val += ".txt"
        exts = os.listdir("data/biomes/ext/")
        if val in exts:
            self.system["EXT"] = nom
            self.save("system")
            await self.bot.say("Extension {} selectionnée ".format(nom.title()))
        else:
            await self.bot.say("Cette extension n'existe pas.")

    @commands.group(pass_context=True)
    async def bms(self, ctx):
        """Commandes Biomes"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @bms.command(pass_context=True, no_pm=True, hidden=True)
    @checks.admin_or_permissions(kick_members=True)
    async def forcejoin(self, ctx, user: discord.Member):
        """Permet de forcer un utilisateur à rejoindre une partie. (Gratuitement)"""
        author = user
        if self.system["OPEN"] is True:
            if self.system["PLAYERS"] < self.system["MAX_PLAYERS"]:
                if author.id not in self.player:
                    self.player[author.id] = {"PSEUDO" : author.name,
                                              "ATK" : 1,
                                              "DEF" : 1,
                                              "ETAT" : "Sain",
                                              "FAIM" : 7,
                                              "GAIN" : 100}
                                
                    self.system["PLAYERS"] += 1
                    self.save()
                    await self.bot.say("[{}/{}] **Inscription réussie** {}".format(self.system["PLAYERS"], self.system["MAX_PLAYERS"], author.mention))
                else:
                    await self.bot.say("Vous êtes déjà inscrit.")
            else:
                await self.bot.say("Le max de joueurs est atteint.")
        else:
            await self.bot.say("Les inscriptions ne sont pas ouvertes.")

    @bms.command(pass_context=True, no_pm=True)
    async def join(self, ctx, offre:int):
        """Permet de rejoindre une partie."""
        author = ctx.message.author
        bank = self.bot.get_cog('Economy').bank
        if self.system["OPEN"] is True:
            if self.system["PLAYERS"] < self.system["MAX_PLAYERS"]:
                if author.id not in self.player:
                    if bank.account_exists(author):
                        if offre >= 100:
                            if bank.can_spend(author, offre):
                                self.player[author.id] = {"PSEUDO" : author.name,
                                                          "ATK" : 1,
                                                          "DEF" : 1,
                                                          "ETAT" : "Sain",
                                                          "FAIM" : 7,
                                                          "GAIN" : offre}
                                            
                                self.system["PLAYERS"] += 1
                                self.save()
                                bank.withdraw_credits(author, offre)
                                await self.bot.say("[{}/{}] **Inscription réussie** {}".format(self.system["PLAYERS"], self.system["MAX_PLAYERS"], author.mention))
                            else:
                                await self.bot.say("Vous n'avez pas assez d'argent.")
                        else:
                            await self.bot.say("L'offre doit être au minimum de 100§.")
                    else:
                        await self.bot.say("Vous n'avez pas de compte bancaire.")
                else:
                    await self.bot.say("Vous êtes déjà inscrit.")
            else:
                if self.system["SPONSOR_NB"] < 2:
                    if author.id not in self.player:
                        if author.id not in self.sponsor:
                            self.sponsor[author.id] = {"PSEUDO" : author.name,
                                                       "JOUEUR" : None,
                                                       "DON" : False,
                                                       "ITEM" : None}
                            self.system["SPONSOR_NB"] += 1
                            self.save()
                            await self.bot.say("[+{}/2] **Inscription réussie en tant que Sponsor** {} \n*Je ne vais pas prélever votre offre.*".format(self.system["SPONSOR_NB"], author.mention))
                        else:
                            await self.bot.say("Vous êtes déjà inscrit.")
                    else:
                        await self.bot.say("Vous êtes déjà inscrit.")
                else:
                    await self.bot.say("Le max de joueurs est atteint.")
        else:
            await self.bot.say("Les inscriptions ne sont pas ouvertes.")

    @bms.command(pass_context=True, no_pm=True)
    async def bonus(self, ctx, user: discord.Member, item=None):
        """Permet aux Sponsors de faire don d'un bonus à un joueur.

        Si aucun item n'est spéficié, renvoie une liste."""
        author = ctx.message.author
        if self.system["PLAYING"] == True:
            if item != None:
                if author.id in self.sponsor:
                    if self.sponsor[author.id]["JOUEUR"] is None:
                        if self.sponsor[author.id]["DON"] is False:
                            for e in self.charge["BNS"]["ITEMS"]:
                                if item in e:
                                    if user.id in self.player:
                                        self.sponsor[author.id]["JOUEUR"] = user.id
                                        self.sponsor[author.id]["ITEM"] = e
                                        self.save("sponsor")
                                        await self.bot.whisper("**Don enregistré.**\n*{} sera donné à {} à la prochaine heure.*".format(e, user.name))
                                        await self.bot.say("**Don enregisté.** Il sera reçu par le joueur dans peu de temps.")
                                        return
                                    else:
                                        await self.bot.whisper("Le joueur n'est pas en train de jouer.")
                            else:
                                msg = "**__Items disponibles dans l'extension {}:__**\n".format(self.system["EXT"].upper())
                                for i in self.charge["BNS"]["ITEMS"]:
                                    msg += "- {}\n".format(i)
                                else:
                                    await self.bot.whisper(msg)
                        else:
                            await self.bot.whisper("Vous avez déjà donné.")
                    else:
                        await self.bot.whisper("Vous avez déjà donné.")
                else:
                    await self.bot.whisper("Vous n'êtes pas sponsor.")
            else:
                msg = "**__Items disponibles dans l'extension {}:__**\n".format(self.system["EXT"].upper())
                for i in self.charge["BNS"]["ITEMS"]:
                    msg += "- {}\n".format(i)
                else:
                    await self.bot.whisper(msg)
        else:
            await self.bot.say("Aucune partie est en cours.")

    @bms.command(pass_context=True, no_pm=True)
    async def bonuslist(self, ctx):
        """Affiche les bonus disponibles dans l'extension chargée."""
        if self.system["PLAYING"] is True:
            msg = "**__Items disponibles dans l'extension {}:__**\n".format(self.system["EXT"].upper())
            for i in self.charge["BNS"]["ITEMS"]:
                msg += "- {}\n".format(i.title())
            else:
                await self.bot.whisper(msg)
        else:
            await self.bot.say("Aucune extension n'est chargée.")

    @bms.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(ban_members=True)
    async def open(self, ctx):
        """Permet d'ouvrir les inscriptions."""
        server = ctx.message.server
        if self.system["OPEN"] is False:
            if self.system["PLAYING"] is False:
                self.system["OPEN"] = True
                r = discord.utils.get(ctx.message.server.roles, name="Play")
                await self.bot.say(r.mention + " **Les inscriptions pour Biomes sont ouvertes !**\n*Faîtes [p]bms join <offre> pour rejoindre !*")
                self.save()
            else:
                await self.bot.say("Une partie est en cours.")
        else:
            await self.bot.say("Les inscriptions sont déjà ouvertes.")

    @bms.command(pass_context=True, no_pm=True)
    async def infos(self, ctx):
        """Affiche différentes informations."""
        if self.system["OPEN"] is True:
            msg = "**__INFORMATIONS__**\n"
            msg += "**Saison :** {}\n".format(self.system["SAISON"])
            msg += "**Nombre de joueurs max :** {}\n".format(self.system["MAX_PLAYERS"])
            msg += "**Nombre de sponsors max :** 2\n"
            msg += "**Joueurs inscrits :**\n"
            for id in self.player:
                msg += "|*{}*\n".format(self.player[id]["PSEUDO"])
            else:
                msg += "**Joueurs sponsors :**\n"
                if self.sponsor != {}:
                    for id in self.sponsor:
                        msg += "|*{}*\n".format(self.sponsor[id]["PSEUDO"])
                else:
                    msg += "Aucun\n"
            await self.bot.say(msg)
        else:
            await self.bot.say("Aucune partie n'est lancée.")

    @bms.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(ban_members=True)
    async def start(self, ctx):
        """Permet de démarrer une partie."""
        server = ctx.message.server
        if self.system["PLAYING"] is False:
            if self.system["OPEN"] is True:
                if self.system["PLAYERS"] == self.system["MAX_PLAYERS"]:
                    self.system["OPEN"] = False
                    self.system["PLAYING"] = True
                    await self.bot.say("*Les conditions semble remplies. Nous allons pouvoir commencer.*")
                    await asyncio.sleep(1.5)
                    await self.bot.say("**Recherche d'extensions (...)**")
                    if self.system["EXT"] is None:
                        msg = "**Environnements disponibles :**\n"
                        exts = os.listdir("data/biomes/ext/")
                        for e in exts:
                            e = e.replace(".txt", "")
                            msg += "-{}\n".format(e)
                        else:
                            await self.bot.whisper(msg + "\n**Vous avez 30 secondes pour en sélectionner une avec '[p]setbms ext' sinon une extension sera choisie aléatoirement.**")
                            await self.bot.say("**En attente de sélection d'une extension ...**\n*Une extension sera sélectionnée automatiquement dans 30s si aucune n'est spécifiée.*")
                            await asyncio.sleep(30)
                            if self.system["EXT"] is None:
                                ext = str(random.choice(exts))
                                ext = ext.replace(".txt", "")
                                self.system["EXT"] = ext
                                await self.bot.say("**'{}'** sélectionné aléatoirement.".format(ext.title()))
                            else:
                                await self.bot.say("**'{}'** sélectionné.".format(self.system["EXT"].title()))
                    else:
                        await asyncio.sleep(1)
                        await self.bot.say("**'{}'** préselectionné.".format(self.system["EXT"].title()))
                    await asyncio.sleep(2)
                    await self.bot.say("**Chargement des actions...**")
                    await asyncio.sleep(2)
                    await self.bot.say("**Chargement de l'extension...**")
                    self.charge_ext()
                    await asyncio.sleep(1.5)
                    await self.bot.say("**Chargement terminé. La partie va commencer !**")
                    await asyncio.sleep(2)
                    em = discord.Embed(title="{} de {}".format(self.system["EXT"].upper(), self.gen("AUT").title()), colour=discord.Colour.blue())
                    em.set_image(url=self.gen("EXT"))
                    await self.bot.say(embed=em)
                    await asyncio.sleep(5)
                    await self.bot.say("**Bienvenue à la saison {} de Biomes !**\n*Le but est de survivre durant les douzes prochaines heures (virtuelles)*".format(self.system["SAISON"]))
                    await asyncio.sleep(1)
                    await self.bot.say("__**Bon courage et puisse le sort vous être favorable !**__")
                    await self.bot.change_presence(game = discord.Game(name="Biomes S{}".format(self.system["SAISON"])))
                    self.system["HEURE"] = 0
                    while self.system["HEURE"] != 12 and self.nb_vie() > 1:
                        self.system["HEURE"] += 1
                        await self.bot.say("**=========== HEURE {} ===========**".format(self.system["HEURE"]))
                        await asyncio.sleep(2)
                        for id in self.sponsor:
                            if self.sponsor[id]["JOUEUR"] != None:
                                if self.sponsor[id]["DON"] is False:
                                    item = self.sponsor[id]["ITEM"]
                                    pm = server.get_member(self.sponsor[id]["JOUEUR"])
                                    self.sponsor[id]["DON"] = True
                                    msg = "**{}** fournit *{}* à **{}**.\n".format(self.sponsor[id]["PSEUDO"], item, pm.name)
                                    effet = random.randint(1,3)
                                    if effet == 1: #ATK BONUS
                                        bonus = random.randint(1, 3)
                                        bonusp = "+{} ATK".format(bonus)
                                        msg += "*Bonus {}*".format(bonusp)
                                        self.player[pm.id]["ATK"] += bonus
                                        self.save("player")
                                        await self.bot.say(msg)
                                    elif effet == 2: #DEF BONUS
                                        bonus = random.randint(1, 3)
                                        bonusp = "+{} DEF".format(bonus)
                                        msg += "*Bonus {}*".format(bonusp)
                                        self.player[pm.id]["DEF"] += bonus
                                        self.save("player")
                                        await self.bot.say(msg)
                                    elif effet == 3: #ETAT BONUS
                                        if self.player[pm.id]["ETAT"] != "Sain":
                                            self.player[pm.id]["ETAT"] = "Sain"
                                            msg += "*Vous êtes de nouveau Sain."
                                            self.save("player")
                                        else:
                                            msg += "*Hum, ça n'a eu aucun effet.*"
                                        await self.bot.say(msg)
                                else:
                                    pass
                            else:
                                pass
                            
                        if self.system["HEURE"] < 7: #JOUR ============================================
                            if self.system["HEURE"] == 1:
                                await self.bot.say("*Vous êtes assignés chacun à votre cadran. Dans 6 heures les murs tombent.*\n" +
                                                   "*Profitez de ce temps pour chasser, manger et trouver de quoi vous défendre à la nuit tombée.*\n" +
                                                   "*Bon courage !*")
                                await asyncio.sleep(1.5)
                            for id in self.player:
                                if self.player[id]["ETAT"] != "Mort":
                                    self.player[id]["GAIN"] *= 1.20
                                    await asyncio.sleep(2.25)
                                    idm = server.get_member(id)
                                    actnum = random.randint(1,6)
                                    if actnum == 1: #REPOS
                                        lieu = self.gen("LIE")
                                        phrase = random.choice(d_repos)
                                        atx = phrase.format(idm.name, lieu)
                                        if self.player[id]["ETAT"] == "Malade":
                                            atx += "\n*{} se rétabli de sa maladie*".format(idm.name)
                                            self.player[id]["ETAT"] = "Sain"
                                        self.save("player")
                                    elif actnum == 2: #CHASSE
                                        animal = self.gen("FAU")
                                        phrase = random.choice(d_chasse)
                                        atx = phrase.format(idm.name, animal)
                                        self.player[id]["FAIM"] = 7
                                        if self.player[id]["ETAT"] == "Blessé":
                                            atx += "\n*{} se rétabli de sa blessure*".format(idm.name)
                                            self.player[id]["ETAT"] = "Sain"
                                        self.save("player")
                                    elif actnum == 3: #CUEILLETTE
                                        plante = self.gen("FLR")
                                        phrase = random.choice(d_cueil)
                                        atx = phrase.format(idm.name, plante)
                                        self.player[id]["FAIM"] = 7
                                        if self.player[id]["ETAT"] == "Empoisonné":
                                            atx += "\n*{} se rétabli de son empoisonnement*".format(idm.name)
                                            self.player[id]["ETAT"] = "Sain"
                                        self.save("player")
                                    elif actnum == 4: #CHANGEMENT d'ETAT
                                        etat = random.choice(["Sain","Malade","Blessé","Empoisonné"])
                                        if self.player[id]["ETAT"] == "Sain":
                                            if etat != "Sain":
                                                if etat == "Malade":
                                                    atx = "**{}** *tombe malade*".format(idm.name)
                                                    self.player[id]["ETAT"] = "Malade"
                                                    self.save("player")
                                                elif etat == "Blessé":
                                                    atx = "**{}** *se blesse*".format(idm.name)
                                                    self.player[id]["ETAT"] = "Blessé"
                                                    self.save("player")
                                                elif etat == "Empoisonné":
                                                    atx = "**{}** *s'est empoisonné*".format(idm.name)
                                                    self.player[id]["ETAT"] = "Empoisonné"
                                                    self.save("player")
                                            else:
                                                axt = "**{}** souffre de son état !".format(idm.name)
                                        else:
                                            text = random.choice([1,2])
                                            if text == 1:
                                                atx = "**{}** s'assoit pour contempler la vue".format(idm.name)
                                            else:
                                                atx = "**{}** se fait courser par **{}**...".format(idm.name, self.gen("FAU"))
                                    elif actnum == 5: #TROUVAILLE OFFENSIVE
                                        item = self.gen("OBO")
                                        bonus = random.randint(1, 3)
                                        bonusp = "+{} ATK".format(bonus)
                                        phrase = random.choice(d_trouve)
                                        atx = phrase.format(idm.name, item, bonusp)
                                        self.player[id]["ATK"] += bonus
                                        self.save("player")
                                    elif actnum == 6: #TROUVAILLE DEFENSIVE
                                        item = self.gen("OBD")
                                        bonus = random.randint(1, 3)
                                        bonusp = "+{} DEF".format(bonus)
                                        phrase = random.choice(d_trouve)
                                        atx = phrase.format(idm.name, item, bonusp)
                                        self.player[id]["DEF"] += bonus
                                        self.save("player")
                                    await self.bot.say(atx)
                                    self.save("player")
                                    await asyncio.sleep(1)
                                
                        else:
                            if self.system["HEURE"] == 7: #NUIT ===================================
                                await self.bot.say("*La nuit tombe et les murs s'abaissent ! Vous ne pouvez plus augmenter vos stats.*\n" +
                                                   "*Faîtes attention à vous et bon courage !*")
                                await asyncio.sleep(1.5)
                                for id in self.player:
                                    idm = server.get_member(id)
                                    if self.player[id]["ETAT"] == "Malade":
                                        await self.bot.say("**{}** est affecté par sa maladie (-2 DEF)".format(idm.name))
                                        self.player[id]["DEF"] -= 2
                                        self.save("player")
                                    elif self.player[id]["ETAT"] == "Blessé":
                                        await self.bot.say("**{}** est mort de sa blessure".format(idm.name))
                                        self.player[id]["ETAT"] = "Mort"
                                        self.save("player")
                                    elif self.player[id]["ETAT"] == "Empoisonné":
                                        await self.bot.say("**{}** est affecté par l'empoisonnement (-2 ATK)".format(idm.name))
                                        self.player[id]["DEF"] -= 2
                                        self.save("player")

                            for id in self.player:
                                if self.player[id]["ETAT"] != "Mort":
                                    await asyncio.sleep(2)
                                    idm = server.get_member(id)
                                    actnum = random.randint(1, 7)
                                    if actnum == 1: #REPOS GRP
                                        lieu = self.gen("LIE")
                                        play2 = self.adv([id])
                                        play2m = server.get_member(play2)
                                        play3 = self.adv([id, play2])
                                        if play3 != False:
                                            play3m = server.get_member(play3)
                                            phrase = random.choice(d_reposgrp)
                                            atx = phrase.format(idm.name, play2m.name, play3m.name, lieu)
                                            if self.player[id]["ETAT"] == "Malade":
                                                atx += "\n*{} se rétabli de sa maladie*".format(idm.name)
                                                self.player[id]["ETAT"] = "Sain"
                                            if self.player[play2]["ETAT"] == "Malade":
                                                atx += "\n*{} se rétabli de sa maladie*".format(play2m.name)
                                                self.player[play2]["ETAT"] = "Sain"
                                            if self.player[play3]["ETAT"] == "Malade":
                                                atx += "\n*{} se rétabli de sa maladie*".format(play3m.name)
                                                self.player[play3]["ETAT"] = "Sain"
                                            self.save("player")
                                        else:
                                            atx = "**{}** s'est perdu.".format(idm.name)
                                    elif actnum == 2: #CHASSE
                                        animal = self.gen("FAU")
                                        phrase = random.choice(d_chasse)
                                        atx = phrase.format(idm.name, animal)
                                        self.player[id]["FAIM"] = 7
                                        if self.player[id]["ETAT"] == "Blessé":
                                            atx += "\n*{} se rétabli de sa blessure*".format(idm.name)
                                            self.player[id]["ETAT"] = "Sain"
                                        self.save("player")
                                    elif actnum == 3: #CUEILLETTE
                                        plante = self.gen("FLR")
                                        phrase = random.choice(d_cueil)
                                        atx = phrase.format(idm.name, plante)
                                        self.player[id]["FAIM"] = 7
                                        if self.player[id]["ETAT"] == "Empoisonné":
                                            atx += "\n*{} se rétabli de son empoisonnement*".format(idm.name)
                                            self.player[id]["ETAT"] = "Sain"
                                        self.save("player")
                                    elif actnum == 4: #CHANGEMENT d'ETAT
                                        etat = random.choice(["Sain","Malade","Blessé","Empoisonné"])
                                        if self.player[id]["ETAT"] == "Sain":
                                            if etat != "Sain":
                                                if etat == "Malade":
                                                    atx = "**{}** *tombe malade*".format(idm.name)
                                                    self.player[id]["ETAT"] = "Malade"
                                                    self.save("player")
                                                elif etat == "Blessé":
                                                    atx = "**{}** *se blesse*".format(idm.name)
                                                    self.player[id]["ETAT"] = "Blessé"
                                                    self.save("player")
                                                elif etat == "Empoisonné":
                                                    atx = "**{}** *à été empoisonné*".format(idm.name)
                                                    self.player[id]["ETAT"] = "Empoisonné"
                                                    self.save("player")
                                            else:
                                                axt = "**{}** souffre de son état ! (-1 DEF)".format(idm.name)
                                                self.player[id]["DEF"] -= 1
                                                self.save("player")
                                        else:
                                            text = random.choice([1,2])
                                            if text == 1:
                                                atx = "**{}** s'assoit pour contempler la vue".format(idm.name)
                                            else:
                                                atx = "**{}** se fait courser par **{}**...".format(idm.name, self.gen("FAU"))
                                    elif actnum == 5: #COMBAT 1V1
                                        ad = self.adv([id])
                                        if ad != False:
                                            adm = server.get_member(ad)
                                            phrase = random.choice(d_combat)
                                            comb = self.calcwin(id, ad)
                                            winner = comb[0]
                                            loser = comb[1]
                                            losm = server.get_member(loser)
                                            self.player[losm.id]["ETAT"] = "Mort"
                                            if id == winner:
                                                self.player[id]["GAIN"] *= 1.4
                                            self.save("player")
                                            atx = phrase.format(idm.name, adm.name)
                                            atx += "\n*{} est mort*".format(losm.name)
                                        else:
                                            atx = "{} n'a plus d'adversaires à combattre.".format(idm.name)
                                    elif actnum == 6: #PIEGE
                                        ad = self.adv([id])
                                        adm = server.get_member(ad)
                                        self.player[id]["ETAT"] = "Mort"
                                        phrase = random.choice(d_piege)
                                        atx = phrase.format(idm.name, adm.name)
                                        self.save("player")
                                        atx += "\n*{} est mort*".format(idm.name)
                                    elif actnum == 7: #COMBAT 2V2 Linéaire (2viv/2mor)
                                        if self.nb_vie() >= 4:
                                            ad1= self.adv([id])
                                            ad1m = server.get_member(ad1)
                                            ad2= self.adv([id, ad1])
                                            ad2m = server.get_member(ad2)
                                            al= self.adv([id, ad1, ad2])
                                            if al != False:
                                                alm = server.get_member(al)
                                                phrase = random.choice(d_combat2)
                                                comb = self.calcwin2(id, al, ad1, ad2)
                                                win = [comb[0],comb[1]]
                                                los = [comb[2],comb[3]]
                                                self.player[comb[2]]["ETAT"] = "Mort"
                                                self.player[comb[3]]["ETAT"] = "Mort"
                                                self.save("player")
                                                lm1 = server.get_member(los[0])
                                                lm2 = server.get_member(los[1])
                                                atx = phrase.format(idm.name, alm.name, ad1m.name, ad2m.name)
                                                if id == comb[0] or id == comb[1]:
                                                    self.player[id]["GAIN"] *= 1.3
                                                if al == comb[0] or al == comb[1]:
                                                    self.player[al]["GAIN"] *= 1.3
                                                atx += "\n*{} et {} sont morts*".format(lm1.name, lm2.name)
                                            else:
                                                atx = "{} n'a plus d'adversaires à combattre.".format(idm.name)
                                        else:
                                            atx = "**{}** croit avoir aperçu quelqu'un mais ce n'était qu'**{}**".format(idm.name, self.gen("FAU"))
                                    await self.bot.say(atx)
                                    self.save("player")
                                    await asyncio.sleep(1)
                                
                        for id in self.player:
                            if self.player[id]["ETAT"] != "Mort":
                                self.player[id]["FAIM"] -= 1
                                if self.player[id]["FAIM"] == 0:
                                    await self.bot.say("*{}* est mort de faim !".format(self.player[id]["PSEUDO"]))
                                    self.player[id]["ETAT"] = "Mort"
                                else:
                                    pass
                            else:
                                pass
                        else:
                            self.save("player")
                        await asyncio.sleep(2)
                        await self.bot.say("**{}e Heure terminée !**\nVoyons un petit récapitulatif...".format(self.system["HEURE"]))
                        await asyncio.sleep(1)
                        msg = ""
                        for id in self.player:
                            msg += "**{}** | *{}*\n".format(self.player[id]["PSEUDO"], self.player[id]["ETAT"])
                        msg += "*Il y a encore {} personne(s) en vie.*".format(self.nb_vie())
                        await self.bot.say(msg)
                        if self.system["STOP"] == True:
                            await self.bot.say("**Arrêt de la partie.**")
                            await self.bot.change_presence(game = discord.Game(name="#"))
                            self.system["STOP"] = False
                            self.reset()
                            return
                        await asyncio.sleep(10)

                    await asyncio.sleep(2)
                    await self.bot.say("**TERMINE !**")
                    await asyncio.sleep(1)
                    await self.bot.say("*Et les gagnants sont ...*")
                    await asyncio.sleep(1)
                    bank = self.bot.get_cog('Economy').bank
                    if self.nb_vie() >= 1:
                        for id in self.player:
                            if self.player[id]["ETAT"] != "Mort":
                                self.player[id]["GAIN"] *= 5
                                await self.bot.say("*{}* ! Tu remportes {}§".format(self.player[id]["PSEUDO"], int(self.player[id]["GAIN"])))
                                idm = server.get_member(id)
                                if bank.account_exists(idm):
                                    bank.deposit_credits(idm, int(self.player[id]["GAIN"]))
                                    await self.bot.send_message(idm, "**Vous venez de recevoir {}§ sur votre compte.**".format(int(self.player[id]["GAIN"])))
                                else:
                                    await self.bot.send_message(idm, "*Vous n'avez pas de compte bancaire. Vous avez donc pas gagné d'argent.")
                            else:
                                pass
                        else:
                            msg = await self.bot.say("*Voilà pour les gagnants !*")
                    else:
                        msg = await self.bot.say("*Personne ! Vous êtes tous morts !*")
                    await asyncio.sleep(0.5)
                    tmp = msg.timestamp
                    tmp = int(tmp.strftime("%H"))
                    if tmp >= 0 and tmp <= 11:
                        notif = "Bonne matinée"
                    elif tmp >= 12 and tmp <= 18:
                        notif = "Bonne journée"
                    else:
                        notif = "Bonne soirée"
                    await self.bot.say("**Cette session est terminée.** {} à tous !".format(notif))
                    self.system["PLAYING"] = False
                    self.system["SAISON"] += 1
                    await self.bot.change_presence(game = discord.Game(name="#"))
                    self.reset()
                else:
                    await self.bot.say("Il n'y a pas assez de joueurs pour lancer une partie.")
            else:
                await self.bot.say("Les inscriptions n'ont même pas encore démarées !")
        else:
            await self.bot.say("Il y a déjà une partie en cours.")
                                    
    def save(self, spec:str = None):
        if spec is None:
            fileIO("data/biomes/player.json", "save", self.player)
            fileIO("data/biomes/system.json", "save", self.system)
            fileIO("data/biomes/charge.json", "save", self.charge)
            fileIO("data/biomes/sponsor.json", "save", self.sponsor)
            return True
        elif spec is "player":
            fileIO("data/biomes/player.json", "save", self.player)
            return True
        elif spec is "system":
            fileIO("data/biomes/system.json", "save", self.system)
            return True
        elif spec is "charge":
            fileIO("data/biomes/charge.json", "save", self.charge)
            return True
        elif spec is "sponsor":
            fileIO("data/biomes/sponsor.json", "save", self.sponsor)
            return True
        else:
            return False

    def gen(self, tag):
        if tag in self.charge:
            gen = random.choice(self.charge[tag]["ITEMS"])
            return gen
        else:
            return False

    def nb_vie(self):
        nb = 0
        for id in self.player:
            if self.player[id]["ETAT"] != "Mort":
                nb += 1
        return nb

    def adv(self, ignore):
        clean = []
        for id in self.player:
            if id not in ignore:
                if self.player[id]["ETAT"] != "Mort":
                    clean.append(id)
                else:
                    pass
            else:
                pass
        else:
            if clean != []:
                choix = random.choice(clean)
                return choix
            else:
                return False

    def calcwin(self, p1, p2):
        atk_p1 = self.player[p1]["ATK"]
        atk_p2 = self.player[p2]["ATK"]
        def_p1 = self.player[p1]["DEF"]
        def_p2 = self.player[p2]["DEF"]
        pot_p1 = atk_p1 - def_p2
        pot_p2 = atk_p2 - def_p1
        if pot_p1 > pot_p2:
            return [p1,p2]
        elif pot_p2 > pot_p1:
            return [p2,p1]
        else:
            choix = random.choice([pot_p1, pot_p2])
            if choix == pot_p1:
                return [p1,p2]
            else:
                return [p2,p1]

    def calcwin2(self, al1, al2, en1, en2):
        atk_al = self.player[al1]["ATK"] + self.player[al2]["ATK"]
        atk_en = self.player[en1]["ATK"] + self.player[en2]["ATK"]
        def_al = self.player[al1]["DEF"] + self.player[al2]["DEF"]
        def_en = self.player[en1]["DEF"] + self.player[en2]["DEF"]
        pot_al = atk_al - def_en
        pot_en = atk_en - def_al
        if pot_al > pot_en:
            return [al1,al2,en1,en2]
        elif pot_en > pot_al:
            return [en1,en2,al1,al2]
        else:
            choix = random.choice([pot_al, pot_en])
            if choix == pot_al:
                return [al1,al2,en1,en2]
            else:
                return [en1,en2,al1,al2]

    def reset(self): #Préparation à une nouvelle partie (reset)
        self.charge = {}
        self.player = {}
        self.sponsor = {}
        self.system["OPEN"] = False
        self.system["PLAYING"] = False
        self.system["PLAYERS"] = 0
        self.system["STOP"] = False
        self.system["EXT"] = None
        self.system["SPONSOR_NB"] = 0
        self.save()

    def charge_ext(self):
        extdiv = "data/biomes/ext/{}.txt"
        chemin = extdiv.format(self.system["EXT"])
        if os.path.isfile(chemin):
            liste = chemin
            with open(liste, "r", encoding="ISO-8859-1") as f:
                liste = f.readlines()
            self.charge = {}
            for line in liste:
                line = line.replace("\n", "")
                tag = line[:3]
                item = line[4:]
                if tag not in self.charge:
                    self.charge[tag] = {"TAG" : tag, "ITEMS" : []}
                self.charge[tag]["ITEMS"].append(item)
            else:
                self.save("charge")
                return True
        else:
            return False

def check_folders():
    if not os.path.exists("data/biomes"):
        print("Creation du fichier Biomes...")
        os.makedirs("data/biomes")

    if not os.path.exists("data/biomes/ext/"):
        print("Creation du fichier Extensions Biomes...")
        os.makedirs("data/biomes/ext/")

def check_files():
    
    if not os.path.isfile("data/biomes/player.json"):
        print("Creation du fichier de joueurs Biomes...")
        fileIO("data/biomes/player.json", "save", {})

    if not os.path.isfile("data/biomes/system.json"):
        print("Creation du fichier de paramétrages Biomes...")
        fileIO("data/biomes/system.json", "save", {"SPONSOR_NB": 0, "STOP" : False, "EXT" : None,"OPEN" : False, "PLAYING" : False,"PLAYERS" : 0,"MAX_PLAYERS" : 12, "SAISON" : 1})

    if not os.path.isfile("data/biomes/charge.json"):
        print("Creation du fichier de Chargement Biomes...")
        fileIO("data/biomes/charge.json", "save", {})

    if not os.path.isfile("data/biomes/sponsor.json"):
        print("Creation du fichier de Sponsors...")
        fileIO("data/biomes/sponsor.json", "save", {})

def setup(bot):
    check_folders()
    check_files()
    n = Biomes(bot)
    bot.add_cog(n)
