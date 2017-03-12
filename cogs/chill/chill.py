import discord
from discord.ext import commands
from .utils import checks
import asyncio
import os
import random
from cogs.utils.dataIO import fileIO, dataIO
from __main__ import send_cmd_help
from copy import deepcopy

default = {"ACQUIS": [], "PREFIX": "&", "FACTORY_PREFIX": ">","FACTORY_ACTIF" : True, "INTERDIT" : [], "NUMERO" : 1}

class Chill:
    """Module vraiment très fun."""

    def __init__(self, bot):
        self.bot = bot
        self.sys = dataIO.load_json("data/chill/sys.json")
        self.factory = dataIO.load_json("data/chill/factory.json")

    @commands.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(kick_members=True)
    async def gomod(self, ctx, user: discord.Member, temps: int = 5, mute=None):
        """Ajoute/Enlève une personne en prison"""
        server = ctx.message.server
        id = user.id
        r = discord.utils.get(ctx.message.server.roles, name="Prison")
        if mute == None:
            mute = False
        else:
            mute = bool(mute)
        if temps >= 1:
            sec = temps * 60  # Temps en secondes
            if "Prison" not in [r.name for r in user.roles]:
                await self.bot.add_roles(user, r)
                if mute == True:
                    self.bot.server_voice_state(user, mute=True)
                else:
                    pass
                await self.bot.say("**{}** est désormais en prison pour {} minute(s).".format(user.display_name, temps))
                await self.bot.send_message(user,
                                            "Vous êtes en prison pour {} minute(s).\n*Vous avez accès au salon #prison pour toute plainte*".format(
                                                temps))
                # \/ Sortie
                await asyncio.sleep(sec)  # Attente
                if "Prison" in [r.name for r in user.roles]:
                    try:
                        await self.bot.remove_roles(user, r)
                        await self.bot.server_voice_state(user, mute=False)
                        await self.bot.say("**{}** est sorti de prison.".format(user.display_name))
                        await self.bot.send_message(user, "Vous êtes désormais libre.")
                    except:
                        pass
                else:
                    return
            else:
                await self.bot.remove_roles(user, r)
                await self.bot.server_voice_state(user, mute=False)
                await self.bot.say("**{}** a été libéré de la prison.".format(user.display_name))
                await self.bot.send_message(user, "Vous avez été libéré de la prison plus tôt que prévu.")
        else:
            await self.bot.say("Le temps doit être de plus d'une minute.")

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

    # FACTORY ================================================================

    @commands.group(pass_context=True)
    @checks.admin_or_permissions(kick_members=True)
    async def fry(self, ctx):
        """Gestion des commandes personnalisées."""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @fry.command(pass_context=True)
    @checks.admin_or_permissions(ban_members=True)
    async def set(self, ctx, prefixe: str = None):
        """Régler le préfixe Factory

        Ne rien rentrer désactive Factory"""
        if prefixe != None:
            self.sys["FACTORY_ACTIF"] = True
            self.sys["PREFIX"] = str(ctx.prefix)
            self.sys["FACTORY_PREFIX"] = prefixe
            fileIO("data/chill/sys.json", "save", self.sys)
            await self.bot.say("Fait")
        else:
            await self.bot.say("Factory désactivé")
            self.sys["FACTORY_ACTIF"] = False
            fileIO("data/chill/sys.json", "save", self.sys)

    @commands.command(pass_context=True, hidden=True)
    @checks.admin_or_permissions(ban_members=True)
    async def rollback(self, ctx):
        try:
            if self.sys["LIMITE"]:
                del self.sys["LIMITE"]
            if self.sys["ULTRAD_PREFIX"]:
                self.sys["FACTORY_PREFIX"] = self.sys["ULTRAD_PREFIX"]
                del self.sys["ULTRAD_PREFIX"]
            if self.sys["ULTRAD_ACTIF"]:
                self.sys["FACTORY_ACTIF"] = self.sys["ULTRAD_ACTIF"]
                del self.sys["ULTRAD_ACTIF"]
            fileIO("data/chill/sys.json", "save", self.sys)
        except:
            await self.bot.say("Non disponible")
            return
        await self.bot.say("Fait")

    @commands.command(pass_context=True, hidden=True)
    @checks.admin_or_permissions(ban_members=True)
    async def fwipe(self, ctx):
        """Efface l'ensemble des bannis de Factory"""
        self.sys["FACTORY_PREFIX"] = "!"
        self.sys["FACTORY_ACTIF"] = True
        self.sys["INTERDIT"] = []
        fileIO("data/chill/sys.json", "save", self.sys)
        await self.bot.say("Fait")

    @fry.command(pass_context=True)
    @checks.admin_or_permissions(kick_members=True)
    async def interdit(self, ctx, user: discord.Member = None):
        """Exclut/Inclut les personnes ayant les droits d'utiliser Factory

        Ne rien rentrer donne une liste des utilisateurs exclus."""
        server = ctx.message.server
        if user != None:
            if user.id not in self.sys["INTERDIT"]:
                self.sys["INTERDIT"].append(user.id)
                await self.bot.say("{} ne pourra plus utiliser Factory.".format(user.name))
                fileIO("data/chill/sys.json", "save", self.sys)
            else:
                self.sys["INTERDIT"].remove(user.id)
                await self.bot.say("{} peut de nouveau utiliser Factory.".format(user.name))
                fileIO("data/chill/sys.json", "save", self.sys)
        else:
            msg = "**Utilisateurs exclus :**\n"
            for u in self.sys["INTERDIT"]:
                user = self.bot.get_member(u)
                msg += "- *{}*\n".format(user.name)
            else:
                await self.bot.say(msg)

    @fry.command(pass_context=True)
    @checks.admin_or_permissions(kick_members=True)
    async def make(self, ctx):
        """Permet de créer une commande Factory."""
        author = ctx.message.author
        dispo = "✉ Message seul\n👥 Interaction"
        em = discord.Embed(inline=False)
        em.add_field(name="Canvas",value=dispo)
        em.set_footer(text="Choisissez le canvas de votre commande")
        menu = await self.bot.say(embed=em)
        await self.bot.add_reaction(menu, "✉")
        await self.bot.add_reaction(menu, "👥")
        await self.bot.add_reaction(menu, "🔚")
        await asyncio.sleep(0.25)
        rep = await self.bot.wait_for_reaction(["✉", "👥", "🔚"], message=menu, user=author)
        if rep.reaction.emoji == "🔚":
            await self.bot.say("Votre commande n'est pas conservée. Bye :wave:")
        elif rep.reaction.emoji == "✉":
            await self.bot.clear_reactions(menu)
            em = discord.Embed(inline=False)
            em.add_field(name="Nom", value="Donnez un nom à votre commande")
            em.set_footer(text="Il ne doit être composé que d'un seul mot")
            await self.bot.edit_message(menu, embed=em)
            verif = False
            while verif == False:
                sec = await self.bot.wait_for_message(author=author, channel=menu.channel)
                sec = sec.content
                if len(sec) >= 3:
                    verif = True
                    nom = sec
                    self.factory[nom] = {"AUTHOR": author.name, "NOM": nom, "TYPE": "message", "COMMANDE": None}
                    fileIO("data/chill/factory.json", "save", self.factory)
                elif sec == "q":
                    await self.bot.say("Bye :wave:")
                else:
                    await self.bot.say("Réessayez, le nom doit avoir plus de 3 caractères.")

            await self.bot.clear_reactions(menu)
            em = discord.Embed(inline=False)
            em.add_field(name="Message", value="Tapez le message désiré")
            em.set_footer(text="Ce message sera envoyé lorsque la commande sera executée")
            await self.bot.edit_message(menu, embed=em)
            verif = False
            while verif == False:
                sec = await self.bot.wait_for_message(author=author, channel=menu.channel)
                sec = sec.content
                if len(sec) >= 5:
                    verif = True
                    self.factory[nom]["COMMANDE"] = sec
                    forme = self.sys["FACTORY_PREFIX"] + self.factory[nom]["NOM"]
                    em = discord.Embed(inline=False)
                    em.add_field(name="Terminé", value="Votre commande est bien enregistrée")
                    em.set_footer(text="Vous pouvez y accéder avec {}".format(forme))
                    await self.bot.edit_message(menu, embed=em)
                    fileIO("data/chill/factory.json", "save", self.factory)
                elif sec == "q":
                    await self.bot.say("Bye :wave:")
                else:
                    await self.bot.say("Réessayez, le message doit avoir plus de 5 caractères.")

        elif rep.reaction.emoji == "👥":
            await self.bot.clear_reactions(menu)
            em = discord.Embed(inline=False)
            em.add_field(name="Nom", value="Donnez un nom à votre commande")
            em.set_footer(text="Il ne doit être composé que d'un seul mot")
            await self.bot.edit_message(menu, embed=em)
            verif = False
            while verif == False:
                sec = await self.bot.wait_for_message(author=author, channel=menu.channel)
                sec = sec.content
                if len(sec) >= 3:
                    verif = True
                    nom = sec
                    self.factory[nom] = {"AUTHOR": author.name, "NOM": nom, "TYPE": "interaction", "COMMANDE": None}
                    fileIO("data/chill/factory.json", "save", self.factory)
                elif sec == "q":
                    await self.bot.say("Bye :wave:")
                else:
                    await self.bot.say("Réessayez, le nom doit avoir plus de 3 caractères.")

            await self.bot.clear_reactions(menu)
            em = discord.Embed(inline=False)
            em.add_field(name="Interaction", value="Tapez le message désiré\n\n*@a* = Auteur de la commande\n*@v* = Personne visée\n*/* = Faire plusieur versions du message")
            em.set_footer(text="Exemple: @a est frappé par @v/@v se fait descendre par @a/(etc...)")
            await self.bot.edit_message(menu, embed=em)
            verif = False
            while verif == False:
                sec = await self.bot.wait_for_message(author=author, channel=menu.channel)
                sec = sec.content
                test = sec.split("/")
                accord = True
                for e in test:
                    if "@a" and "@v" in e:
                        pass
                    else:
                        accord = False
                if accord is True:
                    sec = sec.replace("@a","{0}")
                    sec = sec.replace("@v","{1}")
                    sec = sec.split("/")
                    verif = True
                    self.factory[nom]["COMMANDE"] = sec
                    forme = self.sys["FACTORY_PREFIX"] + self.factory[nom]["NOM"]
                    em = discord.Embed(inline=False)
                    em.add_field(name="Terminé", value="Votre commande est bien enregistrée")
                    em.set_footer(text="Vous pouvez y accéder avec {} @pseudo".format(forme))
                    await self.bot.edit_message(menu, embed=em)
                    fileIO("data/chill/factory.json", "save", self.factory)
                elif sec == "q":
                    await self.bot.say("Bye :wave:")
                else:
                    await self.bot.say("Réessayez, il doit y avoir *@a* et *@v* dans chaque version du message.")
        else:
            await self.bot.say("Invalide, arrêt.")

    @fry.command(pass_context=True)
    @checks.admin_or_permissions(kick_members=True)
    async def remove(self, ctx, commande: str):
        """Retire une commande Factory."""
        if commande in self.factory:
            del self.factory[commande]
            fileIO("data/chill/factory.json", "save", self.factory)
            await self.bot.say("Effacée avec succès.")
        else:
            await self.bot.say("Cette commande n'existe pas.")

    @commands.command(name = "fl", pass_context=True)
    async def factory_list(self, ctx):
        """Permet de voir les commandes autorisées par préfixe secondaire."""
        author = ctx.message.author
        if author.id not in self.sys["INTERDIT"]:
            msg = "**Commandes disponibles :**\n"
            for e in self.factory:
                msg += "- *{}*\n".format(self.factory[e]["NOM"])
            else:
                await self.bot.whisper(msg)
        else:
            await self.bot.say("Vous n'êtes pas autorisé à utiliser le préfixe secondaire.")

    async def custom(self, message):
        msg = message.content
        channel = message.channel
        if message.author.id not in self.sys["INTERDIT"]:
            if self.sys["FACTORY_ACTIF"]:
                if msg.startswith(self.sys["FACTORY_PREFIX"]):
                    command = msg.split(" ")[0][1:]
                    if command in self.factory:
                        canvas = self.factory[command]["TYPE"]
                        if canvas == "message":
                            await self.bot.send_message(channel, self.factory[command]["COMMANDE"])
                        elif canvas == "interaction":
                            msg = random.choice(self.factory[command]["COMMANDE"])
                            vise = message.mentions[0]
                            msg = msg.format(message.author.name, vise.name)
                            await self.bot.send_message(channel, msg)
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

    if not os.path.isfile("data/chill/factory.json"):
        print("Création du fichier Factory...")
        fileIO("data/chill/factory.json", "save", {})

def setup(bot):
    check_folders()
    check_files()
    n = Chill(bot)
    bot.add_listener(n.custom, "on_message")
    bot.add_cog(n)