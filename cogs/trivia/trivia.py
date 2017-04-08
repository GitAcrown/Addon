import discord
from discord.ext import commands
from random import randint
from random import choice as randchoice
from .utils.dataIO import dataIO
from .utils import checks
import datetime
import time
import os
import aiohttp
import asyncio
import chardet

#Originalement créé pour Red (Twentysix26)
#Modifié pour intégrer diverses fonctions et supporter plus de formats.

class Trivia:
    """Commandes Trivia. (Refonte)"""
    def __init__(self, bot):
        self.bot = bot
        self.trivia_sessions = []
        self.file_path = "data/trivia/settings.json"
        self.settings = dataIO.load_json(self.file_path)

    @commands.group(pass_context=True)
    @checks.mod_or_permissions(kick_members=True)
    async def triviaset(self, ctx):
        """Change les paramètres du Trivia"""
        if ctx.invoked_subcommand is None:
            msg = "```\n"
            for k, v in self.settings.items():
                msg += "{}: {}\n".format(k, v)
            msg += "```\nVoyez {}help triviaset pour changer les paramètres".format(ctx.prefix)
            await self.bot.say(msg)

    @triviaset.command()
    async def maxscore(self, score : int):
        """Points requis pour gagner."""
        if score > 0:
            self.settings["TRIVIA_MAX_SCORE"] = score
            dataIO.save_json(self.file_path, self.settings)
            await self.bot.say("Les points requis pour gagner seront désormais {}".format(str(score)))
        else:
            await self.bot.say("Le score doit être supérieur à 0.")

    @triviaset.command()
    async def timelimit(self, seconds : int):
        """Maximum de temps en secondes pour répondre."""
        if seconds > 4:
            self.settings["TRIVIA_DELAY"] = seconds
            dataIO.save_json(self.file_path, self.settings)
            await self.bot.say("Temps maximal reglé à {}s".format(str(seconds)))
        else:
            await self.bot.say("Les secondes doivent dépasser 5.")

    @triviaset.command()
    async def botplays(self):
        """Le bot gagne des points lorsque les membres perdent."""
        if self.settings["TRIVIA_BOT_PLAYS"] is True:
            self.settings["TRIVIA_BOT_PLAYS"] = False
            await self.bot.say("Je ne gagnerai plus de points lorsque vous perdez.")
        else:
            self.settings["TRIVIA_BOT_PLAYS"] = True
            await self.bot.say("Je gagnerai désormais des points à chaque fois que vous perdez.")
        dataIO.save_json(self.file_path, self.settings)

    @triviaset.command(pass_context=True) #AJOUT
    async def addlist(self, ctx):
        """Permet d'ajouter une liste

        Uploadez votre liste en .txt et ajoutez &triviaset addlist en commentaire."""
        attach = ctx.message.attachments
        server = ctx.message.server
        if len(attach) > 1:
            await self.bot.say("Vous ne pouvez ajouter qu'une seule liste à la fois.")
            return
        if attach:
            a = attach[0]
            url = a["url"]
            filename = a["filename"]
        else:
            await self.bot.say("Vous devez upload votre fichier dans un bon format.")
            return
        filepath = os.path.join("data/trivia/", filename)
        if not ".txt" in filepath:
            await self.bot.say("Le format du fichier n'est pas correct. Utilisez un .txt")
            return
        if os.path.splitext(filename)[0] in os.listdir("data/trivia"):
            await self.bot.reply("Une liste avec ce nom est déjà disponible.")
            return

        async with aiohttp.get(url) as new:
            f = open(filepath, "wb")
            f.write(await new.read())
            f.close()

        await self.bot.say("Fichier enregistré avec succès")

    @triviaset.command(pass_context=True) #AJOUT
    async def dellist(self, ctx, nom):
        """Permet de retirer une liste Trivia"""
        path = "data/trivia/" + nom.lower() + ".txt"
        mini = nom.lower() + '.txt'
        if mini in os.listdir("data/trivia/"):
            try:
                os.remove(path)
                await self.bot.say("Fichier retiré avec succès")
            except:
                await self.bot.say("Une erreur est inervenue lors de la suppression du fichier, veuillez le supprimer manuellement (data/trivia)")
        else:
            await self.bot.say("Ce fichier n'existe pas.")

    @triviaset.command(pass_context=True)
    async def aide(self, ctx):
        """Aide pour ajouter une liste"""
        msg = "**La liste doit suivre les règles suivantes :**\n"
        msg += "- Le fichier doit absolument être en '.txt' et le nom du document correspond au nom de votre liste sur le jeu.\n"
        msg += "- La question commence par une majuscule et se termine par un point d'interrogation.\n"
        msg += "- Les réponses sont séparées par des + et il ne doit y avoir aucun espace entre chaque réponse.\n"
        msg += "- Pensez à rentrer plusieurs formats de réponses à chacune de vos questions.\n"
        msg += "- Enfin, il doit y avoir qu'une seule question par ligne dans le document. Vous êtes théoriquement limités à 800 questions par fichier texte.\n"
        msg += "Exemple : http://i.imgur.com/RhdTDXL.png"
        await self.bot.say(msg)

    @commands.command(pass_context=True)
    async def trivia(self, ctx, list_name : str=None):
        """Démarre une partie avec une certaine liste.

        trivia stop = Termine la session en cours
        trivia - Montre une liste des trivias disponibles
        """
        message = ctx.message
        if list_name == None:
            await self.trivia_list(ctx.message.author)
        elif list_name.lower() == "stop":
            if await get_trivia_by_channel(message.channel):
                s = await get_trivia_by_channel(message.channel)
                await s.end_game()
                await self.bot.say("Trivia arrêté.")
            else:
                await self.bot.say("Aucune session n'est en cours.")
        elif not await get_trivia_by_channel(message.channel):
            t = TriviaSession(message, self.settings)
            self.trivia_sessions.append(t)
            await t.load_questions(message.content)
        else:
            await self.bot.say("Une session Trivia est déjà en cours.")

    async def trivia_list(self, author):
        msg = "**Listes disponibles:** \n\n```"
        lists = os.listdir("data/trivia/")
        if lists:
            clean_list = []
            for txt in lists:
                if txt.endswith(".txt") and " " not in txt:
                    txt = txt.replace(".txt", "")
                    clean_list.append(txt)
            if clean_list:
                for i, d in enumerate(clean_list):
                    if i % 4 == 0 and i != 0:
                        msg = msg + d + "\n"
                    else:
                        msg = msg + d + "\t"
                msg += "```"
                if len(clean_list) > 100:
                    await self.bot.send_message(author, msg)
                else:
                    await self.bot.say(msg)
            else:
                await self.bot.say("Aucune liste disponible.")
        else:
            await self.bot.say("Il n'y a pas de listes disponibles.")

class TriviaSession():
    def __init__(self, message, settings):
        self.gave_answer = ["Facile ! {}!", "C'était... {}.", "Vraiment ? C'était {}, évidemment."]
        self.current_q = None # {"QUESTION" : "String", "ANSWERS" : []}
        self.question_list = ""
        self.channel = message.channel
        self.score_list = {}
        self.status = None
        self.timer = None
        self.count = 0
        self.settings = settings

    async def load_questions(self, msg):
        msg = msg.split(" ")
        if len(msg) == 2:
            _, qlist = msg
            if qlist == "random":
                chosen_list = randchoice(glob.glob("data/trivia/*.txt"))
                self.question_list = self.load_list(chosen_list)
                self.status = "new question"
                self.timeout = time.perf_counter()
                if self.question_list: await self.new_question()
            else:
                if os.path.isfile("data/trivia/" + qlist + ".txt"):
                    self.question_list = await self.load_list("data/trivia/" + qlist + ".txt")
                    self.status = "new question"
                    self.timeout = time.perf_counter()
                    if self.question_list: await self.new_question()
                else:
                    await trivia_manager.bot.say("Aucune liste n'existe avec ce nom.")
                    await self.stop_trivia()
        else:
            await trivia_manager.bot.say("trivia [nom de liste]")

    async def stop_trivia(self):
        self.status = "stop"
        trivia_manager.trivia_sessions.remove(self)

    async def end_game(self):
        self.status = "stop"
        if self.score_list:
            await self.send_table()
        trivia_manager.trivia_sessions.remove(self)

    def guess_encoding(self, trivia_list):
        with open(trivia_list, "rb") as f:
            try:
                return chardet.detect(f.read())["encoding"]
            except:
                return "ISO-8859-1"

    async def load_list(self, qlist):
        encoding = self.guess_encoding(qlist)
        with open(qlist, "r", encoding=encoding) as f:
            qlist = f.readlines()
        parsed_list = []
        for line in qlist:
            if "+" in line and len(line) > 4:
                line = line.replace("\n", "")
                line = line.split("+")
                question = line[0]
                answers = []
                for l in line[1:]:
                    answers.append(l.lower().strip())
                if len(line) >= 2:
                    line = {"QUESTION" : question, "ANSWERS": answers} #string, list
                    parsed_list.append(line)
        if parsed_list != []:
            return parsed_list
        else:
            await self.stop_trivia()
            return None

    async def new_question(self):
        for score in self.score_list.values():
            if score == self.settings["TRIVIA_MAX_SCORE"]:
                await self.end_game()
                return True
        if self.question_list == []:
            await self.end_game()
            return True
        self.current_q = randchoice(self.question_list)
        self.question_list.remove(self.current_q)
        self.status = "waiting for answer"
        self.count += 1
        self.timer = int(time.perf_counter())
        msg = "**Question #{} !**\n\n{}".format(str(self.count), self.current_q["QUESTION"])
        try:
            await trivia_manager.bot.say(msg)
        except:
            await asyncio.sleep(0.5)
            await trivia_manager.bot.say(msg)

        while self.status != "correct answer" and abs(self.timer - int(time.perf_counter())) <= self.settings["TRIVIA_DELAY"]:
            if abs(self.timeout - int(time.perf_counter())) >= self.settings["TRIVIA_TIMEOUT"]:
                await trivia_manager.bot.say("Hey ? Il y a quelqu'un ? Arrêt de la session...")
                await self.stop_trivia()
                return True
            await asyncio.sleep(1) #Waiting for an answer or for the time limit
        if self.status == "correct answer":
            self.status = "new question"
            await asyncio.sleep(3)
            if not self.status == "stop":
                await self.new_question()
        elif self.status == "stop":
            return True
        else:
            msg = randchoice(self.gave_answer).format(self.current_q["ANSWERS"][0].title())
            if self.settings["TRIVIA_BOT_PLAYS"]:
                msg += " **+1** pour moi !"
                self.add_point(trivia_manager.bot.user.name)
            self.current_q["ANSWERS"] = []
            try:
                await trivia_manager.bot.say(msg)
                await trivia_manager.bot.send_typing(self.channel)
            except:
                await asyncio.sleep(0.5)
                await trivia_manager.bot.say(msg)
            await asyncio.sleep(3)
            if not self.status == "stop":
                await self.new_question()

    async def send_table(self):
        self.score_list = sorted(self.score_list.items(), reverse=True, key=lambda x: x[1]) # orders score from lower to higher
        t = "```Scores: \n\n"
        for score in self.score_list:
            t += score[0] # name
            t += "\t"
            t += str(score[1]) # score
            t += "\n"
        t += "```"
        await trivia_manager.bot.say(t)

    async def check_answer(self, message):
        if message.author.id != trivia_manager.bot.user.id:
            self.timeout = time.perf_counter()
            if self.current_q is not None:
                for answer in self.current_q["ANSWERS"]:
                    if answer.lower() in message.content.lower():
                        self.current_q["ANSWERS"] = []
                        self.status = "correct answer"
                        self.add_point(message.author.name)
                        msg = "Bien joué {} ! **+1** pour toi.".format(message.author.name)
                        try:
                            await trivia_manager.bot.send_typing(self.channel)
                            await trivia_manager.bot.send_message(message.channel, msg)
                        except:
                            await asyncio.sleep(0.5)
                            await trivia_manager.bot.send_message(message.channel, msg)
                        return True

    def add_point(self, user):
        if user in self.score_list:
            self.score_list[user] += 1
        else:
            self.score_list[user] = 1

    def get_trivia_question(self):
        q = randchoice(list(trivia_questions.keys()))
        return q, trivia_questions[q] # question, answer

async def get_trivia_by_channel(channel):
        for t in trivia_manager.trivia_sessions:
            if t.channel == channel:
                return t
        return False

async def check_messages(message):
    if message.author.id != trivia_manager.bot.user.id:
        if await get_trivia_by_channel(message.channel):
            trvsession = await get_trivia_by_channel(message.channel)
            await trvsession.check_answer(message)


def check_folders():
    folders = ("data", "data/trivia/")
    for folder in folders:
        if not os.path.exists(folder):
            print("Création de " + folder)
            os.makedirs(folder)


def check_files():
    settings = {"TRIVIA_MAX_SCORE" : 10, "TRIVIA_TIMEOUT" : 120,  "TRIVIA_DELAY" : 15, "TRIVIA_BOT_PLAYS" : False}

    if not os.path.isfile("data/trivia/settings.json"):
        print("Creating empty settings.json...")
        dataIO.save_json("data/trivia/settings.json", settings)


def setup(bot):
    global trivia_manager
    check_folders()
    check_files()
    bot.add_listener(check_messages, "on_message")
    trivia_manager = Trivia(bot)
    bot.add_cog(trivia_manager)