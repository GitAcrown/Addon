import discord
from discord.ext import commands
from .utils import checks
import asyncio
import os
import random
from cogs.utils.dataIO import fileIO, dataIO
from copy import deepcopy

default = {"ACQUIS": [], "PREFIX": "&", "ULTRAD_PREFIX": ">"}

class Chill:
    """Module vraiment très fun."""

    def __init__(self, bot):
        self.bot = bot
        self.sys = dataIO.load_json("data/chill/sys.json")

    @commands.command(pass_context=True)
    @checks.admin_or_permissions(kick_members=True)
    async def distrib(self, ctx, nombre: int):
        """Permet de distribuer de l'argent à travers un nouveau système."""
        if nombre == 0:
            await self.bot.say("Reset effectué")
            self.sys["ACQUIS"] = []
            fileIO("data/chill/sys.json", "save", self.sys)
            return
        restant = nombre
        acquis = []
        bank = self.bot.get_cog('Economy').bank
        em = discord.Embed(inline=False)
        em.add_field(name="*Distribution d'argent*".format(nombre),
                     value="Il y a {} tickets disponibles.".format(nombre))
        em.set_footer(text="-- Cliquez sur la reaction pour obtenir un ticket --")
        emsg = await self.bot.say(embed=em)
        await self.bot.add_reaction(emsg, "🏷")
        await asyncio.sleep(0.5)
        while restant != 0:
            rep = await self.bot.wait_for_reaction("🏷", message=emsg)
            if rep.reaction.emoji == "🏷":
                if rep.user.id != self.bot.user.id:
                    if rep.user.id not in acquis:
                        user = rep.user
                        restant -= 1
                        acquis.append(user.id)
                        somme = random.randint(50, 500)
                        if bank.account_exists(user):
                            bank.deposit_credits(user, somme)
                            await self.bot.send_message(user, "Vous obtenez {}§ !".format(somme))
                        else:
                            await self.bot.send_message(user, "Vous n'avez pas de compte bancaire !")
                        em = discord.Embed(inline=False)
                        em.add_field(name="*Distribution d'argent*".format(nombre),
                                     value="Il reste encore {} tickets sur {} !".format(restant, nombre))
                        em.set_footer(text="-- Appuyez sur la reaction pour obtenir un ticket --")
                        await self.bot.edit_message(emsg, embed=em)
                    else:
                        pass
            else:
                pass
        em = discord.Embed(inline=False)
        em.add_field(name="*Distribution d'argent*".format(nombre),
                     value="La distribution est terminée !")
        em.set_footer(text="-- Merci d'avoir participé à cette distribution --")
        await self.bot.edit_message(emsg, embed=em)
        self.sys["ACQUIS"] = []
        fileIO("data/chill/sys.json", "save", self.sys)

    @commands.command(pass_context=True)
    @checks.admin_or_permissions(ban_members=True)
    async def upre(self, ctx, prefixe: str):
        """Régler l'Ultradprefix"""
        self.sys["PREFIX"] = str(ctx.prefix)
        self.sys["ULTRAD_PREFIX"] = prefixe
        fileIO("data/chill/sys.json", "save", self.sys)
        await self.bot.say("Fait")

    @commands.command(pass_context=True)
    async def suck(self, ctx, user: discord.Member):
        """Eheheh"""
        phrases = ["{0} suce goulument {1}",
                   "{1} se fait plaisir avec {0}",
                   "{0} fait une gaterie à {1}",
                   "{1} se fait sucer par {0}"]
        if user == ctx.message.author:
            msg = "{} s'autosuce, quelle souplesse !".format(ctx.message.author.display_name)
        else:
            msg = random.choice(phrases)
            msg = msg.format(ctx.message.author.display_name, user.display_name)
        await self.bot.say(msg)

    # TRADUCTEUR ================================================================

    async def ultrad(self, message):
        msg = message.content
        if self.sys["ULTRAD_PREFIX"] in msg and len(msg) > 2:
            command = msg[1:]
            prefix = self.sys["PREFIX"]
            new_message = deepcopy(message)
            new_message.content = prefix + command
            await self.bot.process_commands(new_message)
        else:
            pass

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
    bot.add_listener(n.ultrad, "on_message")
    bot.add_cog(n)