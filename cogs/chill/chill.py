import discord
from discord.ext import commands
from .utils import checks
import asyncio
import os
import re
import random
import time
import datetime
from cogs.utils.dataIO import fileIO, dataIO
from __main__ import send_cmd_help
from copy import deepcopy
import operator

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