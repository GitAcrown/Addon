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
    async def int(self, ctx, message, url=None):
        """Permet d'afficher un message en format INTEGRE"""
        em = discord.Embed(color=ctx.message.author.color, description=message)
        if url != None:
            em.set_image(url=url)
        em.set_author(name=ctx.message.author.name, icon_url=ctx.message.author.avatar_url)
        await self.bot.say(embed=em)

    @commands.command(aliases=["gb"], pass_context=True, no_pm=True)
    async def ghostbuster(self, ctx, user: discord.Member):
        """Permet de révéler une personne en 'Invisible'"""
        if user.status == discord.Status.invisible:
            await self.bot.say("**{}** est connecté. Il est juste invisible ¯\_(ツ)_/¯".format(user.display_name))
        elif user.status == discord.Status.offline:
            await self.bot.say("Cet utilisateur n'est pas connecté. Il n'est pas invisible...")
        else:
            await self.bot.say("Cet utilisateur est connecté mais n'est pas invisible.")

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