import discord
from discord.ext import commands
from .utils import checks
import asyncio
import os
import re
import random
from cogs.utils.dataIO import fileIO, dataIO
from __main__ import send_cmd_help
from copy import deepcopy

default = {"ACQUIS": [], "PREFIX": "&", "FACTORY_PREFIX": ">","FACTORY_ACTIF" : True, "INTERDIT" : [], "NUMERO" : 1, "SPOIL_DB" : []}

class Chill:
    """Module vraiment très fun."""

    def __init__(self, bot):
        self.bot = bot
        self.sys = dataIO.load_json("data/chill/sys.json")
        self.factory = dataIO.load_json("data/chill/factory.json")

    @commands.command(pass_context=True)
    async def spn(self, ctx, max: int, nom: str):
        """Récupère les dates SPN."""
        await self.bot.say("Début de récolte...")
        cl = self.bot.get_all_channels()
        channel = None
        for c in cl:
            if c.name.lower() == nom.lower():
                channel = c
        if channel is None:
            await self.bot.say("Inaccessible.")
            return
        cmt = []
        async for msg in self.bot.logs_from(channel, limit=max):
            ts = msg.timestamp
            strts = "{}/{}/{} {}:{}:{}".format(ts.day, ts.month, ts.year, ts.hour, ts.minute, ts.second)
            cmt.append([strts, msg.content, msg.author.name])
        await self.bot.say("Récolte terminée\nTri des résultats...")
        ordre = []
        for e in cmt:
            tc = time.mktime(time.strptime(e[0], "%d/%m/%Y %H:%M:%S"))
            ordre.append([tc, e[0], e[1], e[2]])
        new = sorted(ordre, key=operator.itemgetter(0))
        filename = "Spnstf_{}".format(str(random.randint(1, 99999)))
        fileIO("data/chill/{}.txt".format(filename), "save", "")
        file = open("data/chill/{}.txt".format(filename), "w", encoding="UTF-8")
        txt = ""
        for e in new:
            txt += "{}[{}]\t{}\n".format(e[3], e[1], e[2])
        file.write(txt)
        file.close()
        try:
            await self.bot.send_file(ctx.message.channel, "data/chill/{}.txt".format(filename))
            await asyncio.sleep(1.5)
            os.remove("data/chill/{}.txt".format(filename))
        except:
            await self.bot.say("Impossible d'upload le fichier...")

    @commands.command(pass_context=True)
    async def int(self, ctx, message, url=None):
        """Permet d'afficher un message en format INTEGRE"""
        em = discord.Embed(color=ctx.message.author.color, description=message)
        if url != None:
            em.set_image(url=url)
        em.set_author(name=ctx.message.author.name, icon_url=ctx.message.author.avatar_url)
        await self.bot.say(embed=em)

    @commands.command(pass_context=True, no_pm=True)
    async def decodex(self, ctx, *question):
        """Pose une question au decodex"""
        q = " ".join(question)
        if "?" in q:
            l = [["Vrai", 0x36ea1a, "Sans aucun doute !"],
                 ["Plutôt vrai", 0x7fea1a, "Je n'en suis pas certain mais je suis confiant."],
                 ["Incertain", 0xe8ea1a, "Je ne sais pas trop..."],
                 ["Plutôt faux", 0xea831a, "Je pense que c'est faux mais mes sources sont contestables..."],
                 ["Faux", 0xea1a1a, "C'est un mensonge ! #FAKENEWS"]]
            r = random.choice(l)
            em = discord.Embed(title=r[0], description=r[2], color=r[1])
            em.set_footer(text=q)
            await self.bot.say(embed=em)
        else:
            await self.bot.say("C'est pas une question !")

    @commands.command(pass_context=True)
    async def recup(self, ctx, *nom):
        """Permet de récupérer le fichier texte d'une playlist Audio"""
        nom = " ".join(nom)
        nom += ".txt"
        channel = ctx.message.channel
        server = ctx.message.server.id
        if nom in os.listdir("data/audio/playlists/{}/".format(server)):
            chemin = "data/audio/playlists/{}/{}".format(server, nom)
            try:
                await self.bot.send_file(channel, chemin)
            except:
                await self.bot.say("Impossible d'upload le fichier de playlist.")
        else:
            await self.bot.say("Désolé mais je n'ai pas trouvé cette playlist")

def check_folders():
    folders = ("data", "data/chill/")
    for folder in folders:
        if not os.path.exists(folder):
            print("Création du fichier " + folder)
            os.makedirs(folder)

def check_files():
    if not os.path.isfile("data/chill/sys.json"):
        print("Création du fichier systeme Chill...")
        fileIO("data/chill/sys.json", "save", default)

def setup(bot):
    check_folders()
    check_files()
    n = Chill(bot)
    bot.add_cog(n)