import discord
from discord.ext import commands
from .utils import checks
import asyncio
import os
import random
from cogs.utils.dataIO import fileIO, dataIO
from __main__ import send_cmd_help
from copy import deepcopy

default = {"ACQUIS": [], "PREFIX": "&", "ULTRAD_PREFIX": ">","ULTRAD_ACTIF" : True, "INTERDIT" : [], "LIMITE" : []}

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
    async def suck(self, ctx, user: discord.Member):
        """C'est votre délire."""
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

    @commands.command(pass_context=True)
    async def claque(self, ctx, user: discord.Member):
        """Pour giffler des randoms."""
        phrases = ["{0} claque violemment {1}",
                   "{0} défonce {1} à coup de baffes",
                   "{0} met une claque à {1}",
                   "{1} s'est pris une giffle par {0}"]
        if user == ctx.message.author:
            msg = "{} se met une claque. Il est un peu masochiste.".format(ctx.message.author.display_name)
        else:
            msg = random.choice(phrases)
            msg = msg.format(ctx.message.author.display_name, user.display_name)
        await self.bot.say(msg)

    @commands.command(pass_context=True)
    async def gaz(self, ctx, user: discord.Member):
        """Comme à l'époque."""
        phrases = ["{0} enferme {1} dans une chambre à gaz",
                   "{1} meurt à cause du Zyklon B lancé par {0}",
                   "{0} emmène {1} prendre une douche"]
        if user == ctx.message.author:
            msg = "RIP {}".format(ctx.message.author.display_name)
        else:
            msg = random.choice(phrases)
            msg = msg.format(ctx.message.author.display_name, user.display_name)
        await self.bot.say(msg)

    # TRADUCTEUR ULTRAD ================================================================

    @commands.group(pass_context=True)
    @checks.admin_or_permissions(kick_members=True)
    async def ultrad(self, ctx):
        """Gestion de Ultrad (Traducteur de commandes)"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @ultrad.command(pass_context=True)
    @checks.admin_or_permissions(ban_members=True)
    async def set(self, ctx, prefixe: str = None):
        """Régler le préfixe d'Ultrad

        Ne rien rentrer désactive Ultrad."""
        if prefixe != None:
            self.sys["ULTRAD_ACTIF"] = True
            self.sys["PREFIX"] = str(ctx.prefix)
            self.sys["ULTRAD_PREFIX"] = prefixe
            fileIO("data/chill/sys.json", "save", self.sys)
            await self.bot.say("Fait")
        else:
            await self.bot.say("Ultrad désactivé")
            self.sys["ULTRAD_ACTIF"] = False
            fileIO("data/chill/sys.json", "save", self.sys)

    @ultrad.command(pass_context=True, hidden=True)
    @checks.admin_or_permissions(ban_members=True)
    async def wipe(self, ctx):
        """Efface l'ensemble des données enregistrées Utilisateur"""
        self.sys["LIMITE"] = []
        self.sys["INTERDIT"] = []
        fileIO("data/chill/sys.json", "save", self.sys)
        await self.bot.say("Fait")

    @ultrad.command(pass_context=True)
    @checks.admin_or_permissions(kick_members=True)
    async def change(self, ctx, user :discord.Member = None):
        """Exclut/Inclut les personnes ayant les droits d'Ultrad

        Ne rien rentrer donne une liste des utilisateurs exclus."""
        server = ctx.message.server
        if user != None:
            if user.id not in self.sys["INTERDIT"]:
                self.sys["INTERDIT"].append(user.id)
                await self.bot.say("{} ne pourra plus utiliser Ultrad.".format(user.name))
                fileIO("data/chill/sys.json", "save", self.sys)
            else:
                self.sys["INTERDIT"].remove(user.id)
                await self.bot.say("{} peut de nouveau utiliser Ultrad.".format(user.name))
                fileIO("data/chill/sys.json", "save", self.sys)
        else:
            msg = "**Utilisateurs exclus :**\n"
            for u in self.sys["INTERDIT"]:
                user = self.bot.get_member(u)
                msg += "- *{}*\n".format(user.name)
            else:
                await self.bot.say(msg)

    @ultrad.command(pass_context=True)
    @checks.admin_or_permissions(kick_members=True)
    async def limite(self, ctx, commande:str = None):
        """Interdit/Autorise les commandes à travers Ultrad

        Ne rien rentrer donne une liste des commandes interdites."""
        if commande != None:
            if commande not in self.sys["LIMITE"]:
                self.sys["LIMITE"].append(commande)
                await self.bot.say("*{}* est désormais utilisable.".format(commande))
                fileIO("data/chill/sys.json", "save", self.sys)
            else:
                self.sys["LIMITE"].remove(commande)
                await self.bot.say("*{}* n'est plus utilisable.".format(commande))
                fileIO("data/chill/sys.json", "save", self.sys)
        else:
            msg = "**Commandes autorisées :**\n"
            for e in self.sys["LIMITE"]:
                msg += "- *{}*\n".format(e)
            else:
                await self.bot.say(msg)

    @commands.command(aliases = ["sl"], pass_context=True)
    async def second_list(self, ctx):
        """Permet de voir les commandes autorisées par préfixe secondaire."""
        author = ctx.message.author
        if author.id not in self.sys["INTERDIT"]:
            if self.sys["LIMITE"] != []:
                msg = "**Commandes autorisées :**\n"
                for e in self.sys["LIMITE"]:
                    msg += "- *{}*\n".format(e)
                else:
                    await self.bot.whisper(msg)
            else:
                await self.bot.say("Aucune commande autorisée.")
        else:
            await self.bot.say("Vous n'êtes pas autorisé à utiliser le préfixe secondaire.")

    async def ultrad_listen(self, message):
        msg = message.content
        if self.sys["ULTRAD_ACTIF"]:
            if self.sys["ULTRAD_PREFIX"] in msg and len(msg) > 2:
                if message.author.id not in self.sys["INTERDIT"]:
                    command = msg[1:]
                    if command in self.sys["LIMITE"]:
                        prefix = self.sys["PREFIX"]
                        new_message = deepcopy(message)
                        new_message.content = prefix + command
                        await self.bot.process_commands(new_message)

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
    bot.add_listener(n.ultrad_listen, "on_message")
    bot.add_cog(n)