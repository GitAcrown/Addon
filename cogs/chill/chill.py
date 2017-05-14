import discord
from discord.ext import commands
from .utils import checks
import asyncio
import os
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

    @commands.command(pass_context=True, no_pm=True)
    async def decodex(self, ctx, *question):
        """Pose une question au decodex"""
        q = " ".join(question)
        if "?" in q:
            await self.bot.send_typing(ctx.message.channel)
            r = random.choice(["http://i.imgur.com/FpdvBHC.png","http://i.imgur.com/MvloOKT.png","http://i.imgur.com/VnEK487.png"])
            em = discord.Embed()
            em.set_image(url=r)
            em.set_footer(text=q)
            await self.bot.send_message(ctx.message.channel, embed=em)
        else:
            await self.bot.say("Tapez une question !")

    @commands.command(aliases = ["rf"], pass_context=True, no_pm=True)
    async def reactflood(self, ctx, channel: discord.Channel, msgid, text: str):
        """Rajoute automatiquement les réactions qui correspondent au texte fournis sur un message."""
        authormess = ctx.message
        emojis = [s for s in "🇦🇧🇨🇩🇪🇫🇬🇭🇮🇯🇰🇱🇲🇳🇴🇵🇶🇷🇸🇹🇺🇻🇼🇽🇾🇿"]
        letters = [a for a in "abcdefghijklmnopqrstuvwxyz"]
        msg = await self.bot.get_message(channel, msgid)
        classment = [f for f in text.lower()]
        try:
            await self.bot.delete_message(authormess)
        except:
            pass
        for e in classment:
            if e in letters:
                input = letters.index(e)
                output = emojis[input]
                try:
                    await self.bot.add_reaction(msg, output)
                except:
                    pass


    @commands.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(kick_members=True)
    async def gomod(self, ctx, user: discord.Member, temps: int = 5, mute=None):
        """Ajoute/Enlève une personne en prison"""
        server = ctx.message.server
        id = user.id
        spe = discord.utils.get(ctx.message.server.roles, name="Prison")
        if mute == None:
            mute = False
        else:
            mute = bool(mute)
        if temps >= 1:
            sec = temps * 60  # Temps en secondes
            if "Prison" not in [r.name for r in user.roles]:
                await self.bot.add_roles(user, spe)
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
                    await self.bot.remove_roles(user, spe)
                    await asyncio.sleep(0.25)
                    await self.bot.server_voice_state(user, mute=False)
                    await asyncio.sleep(0.25)
                    await self.bot.say("**{}** est sorti de prison.".format(user.display_name))
                    await self.bot.send_message(user, "Vous êtes désormais libre.")
                else:
                    return
            else:
                await self.bot.remove_roles(user, spe)
                await asyncio.sleep(0.25)
                await self.bot.server_voice_state(user, mute=False)
                await asyncio.sleep(0.25)
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

    async def spoil(self, message):
        channel = message.channel
        text = message.content
        author = message.author
        if "§" in text:
            await self.bot.delete_message(message)
            text = text.split("§")
            if not "SPOIL_DB" in self.sys:
                self.sys["SPOIL_DB"] = []
                fileIO("data/chill/sys.json", "save", self.sys)
            else:
                em = discord.Embed(color= author.color)
                em.set_author(name=author.display_name, url=author.avatar_url)
                em.add_field(name=text[0] if text[0] != "" else "Sans titre", value="Un spoil à été caché par {}".format(author.display_name))
                em.set_footer(text="-- Cliquez sur la cloche pour voir le spoil --")
                msg = await self.bot.send_message(channel, embed=em)
                await self.bot.add_reaction(msg, "🔔")
                self.sys["SPOIL_DB"].append([msg.id, text[1], text[0], author.display_name])
                fileIO("data/chill/sys.json", "save", self.sys)

    async def spoilreact(self, reaction, user):
        message = reaction.message
        if reaction.emoji == "🔔":
            for msg in self.sys["SPOIL_DB"]:
                if message.id == msg[0]:
                    em = discord.Embed(color=user.color)
                    em.set_author(name=msg[3])
                    em.add_field(name=msg[2] if msg[2] != "" else "Sans titre", value=msg[1] if msg[1] != "" else "~~Vide~~")
                    try:
                        await self.bot.send_message(user, embed=em)
                    except:
                        pass
                    if len(self.sys["SPOIL_DB"]) > 30:
                        self.sys["SPOIL_DB"].pop(0)
                        fileIO("data/chill/sys.json", "save", self.sys)

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
    bot.add_listener(n.spoil, "on_message")
    bot.add_listener(n.spoilreact, "on_reaction_add")
    bot.add_cog(n)