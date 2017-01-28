import discord
from discord.ext import commands
from .utils.chat_formatting import *
from .utils.dataIO import fileIO, dataIO
from .utils import checks
from random import randint
from random import choice as randchoice
import datetime
import time
import aiohttp
import asyncio
import requests
import os
from urllib import request

settings = {"POLL_DURATION" : 60}
headers = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.130 Safari/537.36"
default = {"CHANNEL" : "", "CB_AUTO" : False, "ACTIVE" : False, "BOT_ID" : ""}

class General:
    """General commands."""

    def __init__(self, bot):
        self.bot = bot
        self.sett = dataIO.load_json("data/gen/sett.json")
        self.stopwatches = {}
        self.box = dataIO.load_json("data/gen/box.json")
        self.ball = ["A ce que je vois, oui.", "C'est certain.", "J'hésite.", "Plutôt oui.", "Il semble que oui.",
                     "Les esprits penchent pour un oui.", "Sans aucun doute.", "Oui.", "Oui - C'est sûr.", "Tu peux compter dessus.", "Je ne sais pas.",
                     "Ta question n'est pas très interessante...", "Je ne vais pas te le dire.", "Je ne peux pas prédire le futur.", "Vaut mieux pas que te révelle la vérité.",
                     "n'y comptes pas.", "Ma réponse est non.", "Des sources fiables assurent que oui.", "J'en doute.", "Non, clairement."]
        self.poll_sessions = []
        
    @commands.command(hidden=True)
    async def ping(self):
        """Pong."""
        await self.bot.say("Pong.")

    @commands.command(hidden=True, pass_context=True)
    async def msginfo(self, ctx):
        """Infos de message"""
        message = ctx.message
        await self.bot.say("Contenu :" + message.content)
        await self.bot.say("Timestamp : {:%c}".format(ctx.message.timestamp))
        await self.bot.say("Auteur :" + message.author)

    @commands.command(pass_context=True)
    async def suce(self, ctx, user : discord.Member):
        """Permet de sucer un confrère."""
        author = ctx.message.author
        if author.id != user.id:
            await self.bot.say("{} suce goulûment {}".format(author.name, user.name))
        else:
            await self.bot.say("{} s'autosuce, quelle souplesse !".format(author.name))

    @commands.command(pass_context=True)
    async def make(self, ctx, *objet):
        """Fait un objet en particulier."""
        objet = " ".join(objet)
        user = ctx.message.author
        await self.bot.say("**{}** en préparation ...".format(objet))
        wait = randint(15, 25)
        await asyncio.sleep(wait)
        await self.bot.say("Voilà {}, votre **{}** est prêt(e) !".format(user.mention, objet))

    @commands.command()
    async def choose(self, *choices):
        """Choisi parmis plusieurs choix.
        """
        choices = [escape_mass_mentions(choice) for choice in choices]
        if len(choices) < 2:
            await self.bot.say('Il n\'y a pas assez de choix.')
        else:
            await self.bot.say(randchoice(choices))

    @commands.command(pass_context=True, hidden=True)
    @checks.admin_or_permissions(kick_members=True)
    async def dbg(self, ctx):
        """Upload le fichier de débug du bot."""
        channel = ctx.message.channel
        chemin = 'data/red/red.log'
        await self.bot.say("Upload en cours...")
        await asyncio.sleep(0.25)
        try:
            await self.bot.send_file(channel, chemin)
        except:
            await self.bot.say("Impossible d'upload le fichier.")

    @commands.command(pass_context=True, hidden=True)
    @checks.admin_or_permissions(kick_members=True)
    async def dbgdel(self, ctx):
        """Vide le fichier de logs du bot."""
        channel = ctx.message.channel
        chemin = 'data/red/red.log'
        with open(chemin, 'w'):
            pass
        await self.bot.say("Le fichier de log est vidé.")
        
    @commands.command(pass_context=True)
    async def roll(self, ctx, number : int = 100):
        """Sort un nombre aléatoire entre 1 et X

        Par défaut 100.
        """
        author = ctx.message.author
        if number > 1:
            n = str(randint(1, number))
            return await self.bot.say("{} :game_die: {} :game_die:".format(author.mention, n))
        else:
            return await self.bot.say("{} Plus haut que 1 ?".format(author.mention))

    @commands.command(pass_context=True)
    async def flip(self, ctx, user : discord.Member=None):
        """Lance une pièce ou retourne un utilisateur..

        Par défaut une pièce.
        """
        if user != None:
            msg = ""
            if user.id == self.bot.user.id:
                user = ctx.message.author
                msg = "Bien essayé. Tu penses que c'est drôle ? Si on faisait *ça* à la place:\n\n"
            char = "abcdefghijklmnopqrstuvwxyz"
            tran = "ɐqɔpǝɟƃɥᴉɾʞlɯuodbɹsʇnʌʍxʎz"
            table = str.maketrans(char, tran)
            name = user.name.translate(table)
            char = char.upper()
            tran = "∀qƆpƎℲפHIſʞ˥WNOԀQᴚS┴∩ΛMX⅄Z"
            table = str.maketrans(char, tran)
            name = name.translate(table)
            return await self.bot.say(msg + "(╯°□°）╯︵ " + name[::-1])
        else:
            return await self.bot.say("*Lance une pièce et... " + randchoice(["FACE !*", "PILE !*"]))

    @commands.command(pass_context=True)
    async def rps(self, ctx, choice : str):
        """Joue à Rock Paper Scissors (EN)"""
        author = ctx.message.author
        rpsbot = {"rock" : ":moyai:",
           "paper": ":page_facing_up:",
           "scissors":":scissors:"}
        choice = choice.lower()
        if choice in rpsbot.keys():
            botchoice = randchoice(list(rpsbot.keys()))
            msgs = {
                "win": " T'as gagné {}!".format(author.mention),
                "square": " Nous sommes à égalité {}!".format(author.mention),
                "lose": " T'as perdu {}!".format(author.mention)
            }
            if choice == botchoice:
                await self.bot.say(rpsbot[botchoice] + msgs["square"])
            elif choice == "rock" and botchoice == "paper":
                await self.bot.say(rpsbot[botchoice] + msgs["lose"])
            elif choice == "rock" and botchoice == "scissors":
                await self.bot.say(rpsbot[botchoice] + msgs["win"])
            elif choice == "paper" and botchoice == "rock":
                await self.bot.say(rpsbot[botchoice] + msgs["win"])
            elif choice == "paper" and botchoice == "scissors":
                await self.bot.say(rpsbot[botchoice] + msgs["lose"])
            elif choice == "scissors" and botchoice == "rock":
                await self.bot.say(rpsbot[botchoice] + msgs["lose"])
            elif choice == "scissors" and botchoice == "paper":
                await self.bot.say(rpsbot[botchoice] + msgs["win"])
        else:
            await self.bot.say("Choose rock, paper or scissors.")

    @commands.command(name="8", aliases=["8ball"])
    async def _8ball(self, *question):
        """Pose une question au bot

        Il ne réponds que par OUI ou NON.
        """
        question = " ".join(question)
        if question.endswith("?") and question != "?":
            return await self.bot.say("`" + randchoice(self.ball) + "`")
        else:
            return await self.bot.say("Ce n'est pas une question ça.")

    @commands.command(aliases = ["colt"],pass_context=True, no_pm=True, hidden=True)
    async def collect(self, ctx, user : discord.Member = None):
        """Permet de collecter l'avatar d'un utilisateur."""
        author = ctx.message.author
        if user == None:
            user = author
        await self.bot.whisper("Avatar de **{}**: {}".format(user.name, user.avatar_url))

#BOX ========================================================

    @commands.command(pass_context=True)
    async def inbox(self, ctx, recherche : str = None, mp : str = "Non"):
        """Affiche des liens et des messages pré-enregistrés dans Inbox."""
        if recherche != None:
            for nom in self.box:
                if recherche in nom:
                    if self.box[nom]["COLOR"] != None:
                        col = self.box[nom]["COLOR"]
                    else:
                        col = discord.Colour.light_grey()
                    tick = self.box[nom]["TICK"]
                    em = discord.Embed(colour=col)
                    if "##" in tick:
                        tick = tick.replace("##","\n")
                    clean = []
                    if "@@" in tick:
                        for elt in tick.split("@@"):
                            alt = elt.split("!!")
                            clean.append([alt[0],alt[1]])
                    else:
                        elt = tick
                        alt = elt.split("!!")
                        clean.append([alt[0],alt[1]])
                    inline = True
                    for e in clean:
                        for a in e:
                            if "??" in a:
                                inline = False
                    for e in clean:
                        if "??" in e[0]:
                            name = e[0].replace("??","")
                        else:
                            name = e[0]
                        if "??" in e[1]:
                            value = e[1].replace("??","")
                        else:
                            value = e[1]
                        em.add_field(name=name, value=value, inline=inline)
                    if self.box[nom]["IMG"] != None:
                        img = self.box[nom]["IMG"]
                        em.set_image(url=img)
                    if self.box[nom]["FOOTER"] != None:
                        footer = self.box[nom]["FOOTER"]
                        em.set_footer(text=footer)
                    if mp == "Non":
                        await self.bot.say(embed=em)
                    else:
                        await self.bot.whisper(embed=em)
                    return
            else:
                await self.bot.say("Aucun ticket ne correspond à cette recherche.")
        else:
            prt = "**__Disponibles:__**\n"
            for e in self.box:
                prt += "¤ **{}**\n".format(self.box[e]["NOM"])
            else:
                await self.bot.whisper(prt)

    @commands.command(pass_context=True)
    @checks.admin_or_permissions(kick_members=True)
    async def addbox(self, ctx, nom : str, tick : str, coul = None, footer = None, imgurl = None):
        """Permet de rajouter un ticket Inbox.

        --- Obligatoire ---
        Nom = Nom de votre ticket.
        Tick = Ce qu'il y a dans le ticket.
        FORMAT : "Titre !!Message@@Autre Titre!!Autre Message (...)"
        - '!!' pour passer du titre au message/valeur
        - '##' pour sauter une ligne
        - '@@' pour couper le ticket en plusieures parties
        - Ajoutez '??' n'importe où dans le ticket pour passer en mode colonne
        - Ne mettez pas d'espaces entre les messages.
        ----- Options -----
        Coul = Change la couleur du ticket. (Forme HEX: 0x<hex>)
        Footer = Affiche un message en bas du ticket.
        Imgurl = Affiche une image dans le ticket."""
        if nom not in self.box:
            if coul != None:
                coul = int(coul, 16)
            self.box[nom] = {"NOM" : nom,
                             "TICK" : tick,
                             "COLOR" : coul,
                             "FOOTER" : footer,
                             "IMG" : imgurl}
            fileIO("data/gen/box.json", "save", self.box)
            await self.bot.whisper("**Enregisté**. Je vais vous envoyer un aperçu d'ici quelques secondes...")
            await asyncio.sleep(2)
            # ======= AFFICHAGE =========
            if self.box[nom]["COLOR"] != None:
                col = self.box[nom]["COLOR"]
            else:
                col = discord.Colour.light_grey()
            tick = self.box[nom]["TICK"]
            em = discord.Embed(colour=col)
            if "##" in tick:
                tick = tick.replace("##","\n")
            clean = []
            if "@@" in tick:
                for elt in tick.split("@@"):
                    alt = elt.split("!!")
                    clean.append([alt[0],alt[1]])
            else:
                elt = tick
                alt = elt.split("!!")
                clean.append([alt[0],alt[1]])
            inline = True
            for e in clean:
                for a in e:
                    if "??" in a:
                        inline = False
            for e in clean:
                if "??" in e[0]:
                    name = e[0].replace("??","")
                else:
                    name = e[0]
                if "??" in e[1]:
                    value = e[1].replace("??","")
                else:
                    value = e[1]
                em.add_field(name=name, value=value, inline=inline)
            if self.box[nom]["IMG"] != None:
                img = self.box[nom]["IMG"]
                em.set_image(url=img)
            if self.box[nom]["FOOTER"] != None:
                footer = self.box[nom]["FOOTER"]
                em.set_footer(text=footer)
            await self.bot.whisper(embed=em)
        else:
            await self.bot.say("Ce nom est déjà dans ma base de données.")

    @commands.command(pass_context=True)
    @checks.admin_or_permissions(kick_members=True)
    async def rembox(self, ctx, nom):
        """Permet la suppression d'un ticker Inbox"""
        if nom in self.box:
            del self.box[nom]
            fileIO("data/gen/box.json", "save", self.box)
            await self.bot.say("Supprimé.")
        else:
            await self.bot.say("Ce nom n'existe pas.")

    @commands.command(pass_context=True)
    @checks.admin_or_permissions(kick_members=True)
    async def ltrbox(self, ctx, nom):
        """Affiche le ticket sans formatage."""
        for e in self.box:
            if nom in e:
                await self.bot.say("**{}** | \"*{}*\" ".format(self.box[e]["NOM"], self.box[e]["TICK"]))
                return
            else:
                pass
        else:
            await self.bot.say("Aucun nom ne correspond à la recherche.")

    @commands.command(pass_context=True)
    @checks.admin_or_permissions(kick_members=True)
    async def edtbox(self, ctx, nom, tick : str, coul = None, footer = None, imgurl = None):
        """Permet d'éditer un ticket.

        --- Obligatoire ---
        Nom = Nom de votre ticket à modifier.
        Tick = Ce qu'il y a dans le ticket.
        FORMAT : "Titre !!Message@@Autre Titre!!Autre Message (...)"
        - '!!' pour passer du titre au message/valeur
        - '##' pour sauter une ligne
        - '@@' pour couper le ticket en plusieures parties
        - Ajoutez '??' n'importe où dans le ticket pour passer en mode colonne
        - Ne mettez pas d'espaces entre les messages.
        ----- Options -----
        Coul = Change la couleur du ticket. (Forme HEX: 0x<hex>)
        Footer = Affiche un message en bas du ticket.
        Imgurl = Affiche une image dans le ticket."""
        if nom in self.box:
            if coul != None:
                coul = int(coul, 16)
            if "##" in msg:
                msg = msg.replace("##","\n")
            self.box[nom] = {"NOM" : nom,
                             "TICK" : tick,
                             "COLOR" : coul,
                             "FOOTER" : footer,
                             "IMG" : imgurl}
            fileIO("data/gen/box.json", "save", self.box)
            await self.bot.whisper("**Modifié**. Je vais vous envoyer un aperçu d'ici quelques secondes...")
            await asyncio.sleep(2)
            if self.box[nom]["COLOR"] != None:
                col = self.box[nom]["COLOR"]
            else:
                col = discord.Colour.light_grey()
            tick = self.box[nom]["TICK"]
            em = discord.Embed(colour=col)
            if "##" in tick:
                tick = tick.replace("##","\n")
            clean = []
            if "@@" in tick:
                for elt in tick.split("@@"):
                    alt = elt.split("!!")
                    clean.append([alt[0],alt[1]])
            else:
                elt = tick
                alt = elt.split("!!")
                clean.append([alt[0],alt[1]])
            inline = True
            for e in clean:
                for a in e:
                    if "??" in a:
                        inline = False
            for e in clean:
                if "??" in e[0]:
                    name = e[0].replace("??","")
                else:
                    name = e[0]
                if "??" in e[1]:
                    value = e[1].replace("??","")
                else:
                    value = e[1]
                em.add_field(name=name, value=value, inline=inline)
            if self.box[nom]["IMG"] != None:
                img = self.box[nom]["IMG"]
                em.set_image(url=img)
            if self.box[nom]["FOOTER"] != None:
                footer = self.box[nom]["FOOTER"]
                em.set_footer(text=footer)
            await self.bot.whisper(embed=em)
        else:
            await self.bot.say("Ce nom n'est pas dans ma base de données.")

    @commands.command(aliases=["sw"], pass_context=True)
    async def stopwatch(self, ctx):
        """Démarre ou arrête un Compte à rebours (CaR)."""
        author = ctx.message.author
        if not author.id in self.stopwatches:
            self.stopwatches[author.id] = int(time.perf_counter())
            await self.bot.say(author.mention + " CàR démarré !")
        else:
            tmp = abs(self.stopwatches[author.id] - int(time.perf_counter()))
            tmp = str(datetime.timedelta(seconds=tmp))
            await self.bot.say(author.mention + " CàR arrêté ! Temps: **" + str(tmp) + "**")
            self.stopwatches.pop(author.id, None)

    @commands.command()
    async def lmgtfy(self, *, search_terms : str):
        """Crée un lien lmgtfy"""
        search_terms = escape_mass_mentions(search_terms.replace(" ", "+"))
        await self.bot.say("http://lmgtfy.com/?q={}".format(search_terms))

    @commands.command(no_pm=True)
    async def hug(self, user : discord.Member, intensity : int=1):
        """Parce que tout le monde aime les calins.

        Avec 10 niveaux d'intensité."""
        name = " *" + user.name + "*"
        if intensity <= 0:
            msg = "(っ˘̩╭╮˘̩)っ" + name
        elif intensity <= 3:
            msg = "(っ´▽｀)っ" + name
        elif intensity <= 6:
            msg = "╰(*´︶`*)╯" + name
        elif intensity <= 9:
            msg = "(つ≧▽≦)つ" + name
        elif intensity >= 10:
            msg = "(づ￣ ³￣)づ" + name + " ⊂(´・ω・｀⊂)"
        await self.bot.say(msg)

    @commands.command()
    async def updown(self, url):
        """Recherche si un site est disponible ou pas."""
        if url == "":
            await self.bot.say("Vous n'avez pas rentré de site à rechercher.")
            return
        if "http://" not in url or "https://" not in url:
            url = "http://" + url
        try:
            with aiohttp.Timeout(15):
                await self.bot.say("Test de " + url + "…")
                try:
                    response = await aiohttp.get(url, headers = { 'user_agent': headers })
                    if response.status == 200:
                        await self.bot.say(url + " semble répondre correctement.")
                    else:
                        await self.bot.say(url + " ne réponds pas. Le site est mort.")
                except:
                    await self.bot.say(url + " est down.")
        except asyncio.TimeoutError:
            await self.bot.say(url + " est down.")

    @commands.command(pass_context=True, no_pm=True)
    async def userinfo(self, ctx, user : discord.Member = None):
        """Montre les informations à propos d'un utilisateur."""
        author = ctx.message.author
        if not user:
            user = author
        roles = [x.name for x in user.roles if x.name != "@everyone"]
        if not roles: roles = ["None"]
        data = "```python\n"
        data += "Nom: {}\n".format(escape_mass_mentions(str(user)))
        data += "ID: {}\n".format(user.id)
        passed = (ctx.message.timestamp - user.created_at).days
        data += "Crée: {} (Il y a {} jours)\n".format(user.created_at, passed)
        passed = (ctx.message.timestamp - user.joined_at).days
        data += "Rejoint le: {} (Il y a {} jours)\n".format(user.joined_at, passed)
        data += "Rôles: {}\n".format(", ".join(roles))
        data += "Avatar: {}\n".format(user.avatar_url)
        data += "```"
        await self.bot.say(data)

    @commands.command(pass_context=True, no_pm=True)
    async def serverinfo(self, ctx):
        """Montre les infos du serveur."""
        server = ctx.message.server
        online = str(len([m.status for m in server.members if str(m.status) == "online" or str(m.status) == "idle"]))
        total_users = str(len(server.members))
        text_channels = len([x for x in server.channels if str(x.type) == "text"])
        voice_channels = len(server.channels) - text_channels

        data = "```python\n"
        data += "Nom: {}\n".format(server.name)
        data += "ID: {}\n".format(server.id)
        data += "Region: {}\n".format(server.region)
        data += "Utilisateurs: {}/{}\n".format(online, total_users)
        data += "Canaux Textuels: {}\n".format(text_channels)
        data += "Canaux Vocaux: {}\n".format(voice_channels)
        data += "Rôles: {}\n".format(len(server.roles))
        passed = (ctx.message.timestamp - server.created_at).days
        data += "Crée: {} (Il y a {} jours)\n".format(server.created_at, passed)
        data += "Propriétaire: {}\n".format(server.owner)
        data += "Icône: {}\n".format(server.icon_url)
        data += "```"
        await self.bot.say(data)

    @commands.command()
    async def urban(self, *, search_terms : str, definition_number : int=1):
        """Recherche dans le Urban Dictionnary (EN)

        Le nombre de définitions doit être entre 1 et 10"""
        search_terms = search_terms.split(" ")
        try:
            if len(search_terms) > 1:
                pos = int(search_terms[-1]) - 1
                search_terms = search_terms[:-1]
            else:
                pos = 0
            if pos not in range(0, 11):
                pos = 0                 
        except ValueError:
            pos = 0
        search_terms = "+".join(search_terms)
        url = "http://api.urbandictionary.com/v0/define?term=" + search_terms
        try:
            async with aiohttp.get(url) as r:
                result = await r.json()
            if result["list"]:
                definition = result['list'][pos]['definition']
                example = result['list'][pos]['example']
                defs = len(result['list'])
                msg = ("**Definition #{} sur {}:\n**{}\n\n"
                       "**Exemple:\n**{}".format(pos+1, defs, definition,
                                                 example))
                msg = pagify(msg, ["\n"])
                for page in msg:
                    await self.bot.say(page)
            else:
                await self.bot.say("Aucun résultat.")
        except IndexError:
            await self.bot.say("Aucune définition #{}".format(pos+1))
        except:
            await self.bot.say("Erreur.")

    @commands.command(pass_context=True, no_pm=True)
    async def poll(self, ctx, *text):
        """Démarre ou arrête un poll."""
        message = ctx.message
        if len(text) == 1:
            if text[0].lower() == "stop":
                await self.endpoll(message)
                return
        if not self.getPollByChannel(message):
            check = " ".join(text).lower()
            if "@everyone" in check or "@here" in check:
                await self.bot.say("Eheh, bien essayé.")
                return
            p = NewPoll(message, self)
            if p.valid:
                self.poll_sessions.append(p)
                await p.start()
            else:
                await self.bot.say("*poll question;option1;option2 (...)*")
        else:
            await self.bot.say("Un poll est déjà en cours.")

    async def endpoll(self, message):
        if self.getPollByChannel(message):
            p = self.getPollByChannel(message)
            if p.author == message.author.id: # or isMemberAdmin(message)
                await self.getPollByChannel(message).endPoll()
            else:
                await self.bot.say("L'auteur du poll ou l'admin sont les seuls à pouvoir stopper ça.")
        else:
            await self.bot.say("Aucun poll sur ce channel.")

    def getPollByChannel(self, message):
        for poll in self.poll_sessions:
            if poll.channel == message.channel:
                return poll
        return False

    async def check_poll_votes(self, message):
        if message.author.id != self.bot.user.id:
            if self.getPollByChannel(message):
                    self.getPollByChannel(message).checkAnswer(message)


class NewPoll():
    def __init__(self, message, main):
        self.channel = message.channel
        self.author = message.author.id
        self.client = main.bot
        self.poll_sessions = main.poll_sessions
        msg = message.content[6:]
        msg = msg.split(";")
        if len(msg) < 2: # Au moins une question avec 2 réponses
            self.valid = False
            return None
        else:
            self.valid = True
        self.already_voted = []
        self.question = msg[0]
        msg.remove(self.question)
        self.answers = {}
        i = 1
        for answer in msg: # {id : {answer, votes}}
            self.answers[i] = {"ANSWER" : answer, "VOTES" : 0}
            i += 1

    async def start(self):
        msg = "**POLL DEMARRE !**\n\n{}\n\n".format(self.question)
        for id, data in self.answers.items():
            msg += "{}. *{}*\n".format(id, data["ANSWER"])
        msg += "\nTapez le chiffre pour voter !"
        await self.client.send_message(self.channel, msg)
        await asyncio.sleep(settings["POLL_DURATION"])
        if self.valid:
            await self.endPoll()

    async def endPoll(self):
        self.valid = False
        msg = "**POLL ARRETE !**\n\n{}\n\n".format(self.question)
        for data in self.answers.values():
            msg += "*{}* - {} votes\n".format(data["ANSWER"], str(data["VOTES"]))
        await self.client.send_message(self.channel, msg)
        self.poll_sessions.remove(self)

    def checkAnswer(self, message):
        try:
            i = int(message.content)
            if i in self.answers.keys():
                if message.author.id not in self.already_voted:
                    data = self.answers[i]
                    data["VOTES"] += 1
                    self.answers[i] = data
                    self.already_voted.append(message.author.id)
        except ValueError:
            pass

def check_folders():
    if not os.path.exists("data/gen"):
        print("Creation du fichier General...")
        os.makedirs("data/gen")

def check_files():
    
    if not os.path.isfile("data/gen/sett.json"):
        print("Creation du fichier de réglages General...")
        fileIO("data/gen/sett.json", "save", default)

    if not os.path.isfile("data/gen/box.json"):
        print("Creation du fichier BOX...")
        fileIO("data/gen/box.json", "save", {})

def setup(bot):
    check_folders()
    check_files()
    n = General(bot)
    bot.add_listener(n.check_poll_votes, "on_message")
    bot.add_cog(n)
