import discord
from discord.ext import commands
from .utils import checks
import asyncio
import os
import operator
import random
import time
import datetime
from cogs.utils.dataIO import fileIO, dataIO
from __main__ import send_cmd_help, settings

default = {"GEP_ROLE" : None, "GEP_IDEES" : {}, "GEP_PTAG" : 1}

class Extra:
    """Module d'outils communautaire."""

    def __init__(self, bot):
        self.bot = bot
        self.sys = dataIO.load_json("data/extra/sys.json")

# PRESIDENT ============================================================

    @commands.group(pass_context=True)
    async def gep(self, ctx):
        """Outils Président."""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @gep.command(pass_context=True)
    @checks.mod_or_permissions(administrator=True)
    async def reset(self, ctx):
        """Reset la partie présidentielle du Module."""
        self.sys["GEP_IDEES"] = {}
        self.sys["GEP_PTAG"] = 1
        fileIO("data/astra/sys.json", "save", self.sys)
        await self.bot.say("Fait.")

    @gep.command(pass_context=True, no_pm=True, hidden=True)
    @checks.mod_or_permissions(ban_members=True)
    async def set(self, ctx, role:discord.Role):
        """Change le rôle de président enregistré."""
        channel = ctx.message.channel
        author = ctx.message.author
        if self.sys["GEP_ROLE"] is None:
            self.sys["GEP_ROLE"] = role.name
            fileIO("data/extra/sys.json", "save", self.sys)
            await self.bot.say("Rôle de président enregistré.")
        else:
            await self.bot.say("Le rôle {} est déja renseigné. Voulez-vous l'enlever ? (O/N)".format(self.sys["GEP_ROLE"]))
            rep = await self.bot.wait_for_message(author=author, channel=channel)
            rep = rep.content.lower()
            if rep == "o":
                await self.bot.say("Le rôle à été retiré de ma BDD.")
                self.sys["GEP_ROLE"] = None
                fileIO("data/extra/sys.json", "save", self.sys)
            elif rep == "n":
                await self.bot.say("Le rôle est conservé.")
            else:
                await self.bot.say("Réponse invalide, le rôle est conservé.")

# BOITE A IDEES --------------------

    @commands.command(pass_context=True)
    async def propose(self, ctx):
        """[MP] Permet de proposer une idée au Président."""
        author= ctx.message.author
        if self.sys["GEP_ROLE"] != None:
            tag = str(self.sys["GEP_PTAG"])
            self.sys["GEP_PTAG"] += 1
            ntime = time.strftime("%d/%m/%Y %H:%M:%S", time.localtime())
            r = lambda: random.randint(0,255)
            color = '0x%02X%02X%02X' % (r(),r(),r())
            base = await self.bot.whisper("__**Proposer une idée**__\n**Entrez le titre que vous voulez donner à votre idée :**")
            channel = base.channel
            verif = False
            while verif != True:
                rep = await self.bot.wait_for_message(author=author, channel=channel)
                if len(rep.content) >= 5:
                    titre=rep.content
                    verif = True
                elif rep.content.lower() == "q":
                    await self.bot.whisper("Votre idée n'est pas conservée. Bye :wave:")
                    return
                else:
                    await self.bot.whisper("Invalide, réessayez. (Votre titre doit être d'au moins 5 caractères)")
            
            await self.bot.whisper("**Entrez votre idée :**\n*(Tip: Pour mettre un espace sans valider votre message, utilisez MAJ + Entrer)*")
            verif = False
            while verif != True:
                rep = await self.bot.wait_for_message(author=author, channel=channel)
                if len(rep.content) >= 30:
                    idee = rep.content
                    verif = True
                elif rep.content.lower() == "q":
                    await self.bot.whisper("Votre idée n'est pas conservée. Bye :wave:")
                    return
                else:
                    await self.bot.whisper("Invalide, réessayez. (Votre texte doit faire au moins 30 caractères)")
            
            await self.bot.whisper("**Désirez-vous être anonyme ? (O/N)**")
            verif = False
            while verif != True:
                rep = await self.bot.wait_for_message(author=author, channel=channel)
                if rep.content.lower() == "o":
                    name = "Anonyme"
                    await self.bot.whisper("Merci pour votre contribution !\nVotre idée est enregistrée dans nos fichiers (Votre pseudo ne sera pas affiché).")
                    image = "http://i.imgur.com/iDZRdNk.png"
                    verif = True
                elif rep.content.lower() == "n":
                    name = str(author)
                    await self.bot.whisper("Merci pour votre contribution !\nVotre idée est enregistrée dans nos fichiers.")
                    image = author.avatar_url
                    verif = True
                elif rep.content.lower() == "q":
                    await self.bot.whisper("Votre idée n'est pas conservée. Bye :wave:")
                    return
                else:
                    await self.bot.whisper("Invalide, réessayez. ('O' pour OUI, 'N' pour NON, 'Q' pour Annuler et quitter)")

            self.sys["GEP_IDEES"][tag] = {"TAG" : tag, "CHECK" : False, "AUTHOR" : name, "IMAGE" : image, "TITRE" : titre, "TEXTE" : idee, "COLOR" : color, "TIME": ntime}
            fileIO("data/extra/sys.json", "save", self.sys)
        else:
            await self.bot.whisper("Aucun président n'est enregistré sur ce serveur !")

    @gep.command(pass_context=True, no_pm=True)
    async def bai(self, ctx):
        """Permet de voir les idées enregistrées dans la boite à idée."""
        author = ctx.message.author
        if not ctx.message.server:
            await self.bot.whisper("Lancez cette commande sur le serveur où vous êtes Président.")
            return
        role = self.sys["GEP_ROLE"]
        r = discord.utils.get(ctx.message.server.roles, name=role)
        if role in [r.name for r in author.roles]:
            retour = False
            while retour == False:
                em = discord.Embed(inline=False)
                msg = ""
                for i in self.sys["GEP_IDEES"]:
                    if self.sys["GEP_IDEES"][i]["CHECK"] is False:
                        msg += "__#{}__| **{}** - *{}*\n".format(self.sys["GEP_IDEES"][i]["TAG"],self.sys["GEP_IDEES"][i]["AUTHOR"],self.sys["GEP_IDEES"][i]["TITRE"])
                    else:
                        msg += "__@{}__| **{}** - *{}*\n".format(self.sys["GEP_IDEES"][i]["TAG"],self.sys["GEP_IDEES"][i]["AUTHOR"],self.sys["GEP_IDEES"][i]["TITRE"])
                else:
                    em.set_footer(text="Tapez un numéro pour en savoir plus ou tapez 'Q' pour quitter")
                    if msg != "":
                        em.add_field(name="__Boite à idées__",value=msg)
                    else:
                        em.add_field(name="__Boite à idées__",value="*La boite à idées est vide*")
                    nec = await self.bot.whisper(embed=em)
                    channel = nec.channel
                verif = False
                while verif != True:
                    rep = await self.bot.wait_for_message(author=author, channel=channel)
                    if rep.content.lower() == "q":
                        await self.bot.whisper("Bye :wave:")
                        return
                    if rep.content in self.sys["GEP_IDEES"]:
                        num = rep.content
                        verif = True
                        if self.sys["GEP_IDEES"][num]["AUTHOR"] is "Anonyme":
                            em = discord.Embed(colour= int(self.sys["GEP_IDEES"][num]["COLOR"], 16), inline=False)
                            em.set_author(name="Anonyme", icon_url="http://i.imgur.com/iDZRdNk.png")
                            em.add_field(name=self.sys["GEP_IDEES"][num]["TITRE"], value=self.sys["GEP_IDEES"][num]["TEXTE"])
                            em.set_footer(text="Soumise le: " + self.sys["GEP_IDEES"][num]["TIME"])
                            msg = await self.bot.whisper(embed=em)
                        else:
                            em = discord.Embed(colour=int(self.sys["GEP_IDEES"][num]["COLOR"], 16),inline=False)
                            em.set_author(name=self.sys["GEP_IDEES"][num]["AUTHOR"], icon_url=self.sys["GEP_IDEES"][num]["IMAGE"])
                            em.add_field(name=self.sys["GEP_IDEES"][num]["TITRE"],
                                         value=self.sys["GEP_IDEES"][num]["TEXTE"])
                            em.set_footer(text="Soumise le: " + self.sys["GEP_IDEES"][num]["TIME"])
                            msg = await self.bot.whisper(embed=em)
                        await asyncio.sleep(0.25)
                        await self.bot.add_reaction(msg, "✔")  # Check
                        await self.bot.add_reaction(msg, "✖")  # Supprimer
                        await self.bot.add_reaction(msg, "🔙")  # Menu
                        await self.bot.add_reaction(msg, "🔚")  # Quitter
                        await asyncio.sleep(0.25)
                        sec = False
                        while sec != True:
                            rep = await self.bot.wait_for_reaction(["✔","✖","🔙","🔚"], message=msg, user=author)
                            if rep.reaction.emoji == "✔":
                                if self.sys["GEP_IDEES"][num]["CHECK"] is False:
                                    await self.bot.whisper("Idée approuvée !")
                                    self.sys["GEP_IDEES"][num]["CHECK"] = True
                                    fileIO("data/extra/sys.json", "save", self.sys)
                                else:
                                    await self.bot.whisper("Idée désaprouvée !")
                                    self.sys["GEP_IDEES"][num]["CHECK"] = False
                                    fileIO("data/extra/sys.json", "save", self.sys)
                            elif rep.reaction.emoji == "✖":
                                await self.bot.whisper("Idée supprimée.")
                                del self.sys["GEP_IDEES"][num]
                                fileIO("data/extra/sys.json", "save", self.sys)
                                sec = True
                            elif rep.reaction.emoji == "🔙":
                                sec = True
                            elif rep.reaction.emoji == "🔚":
                                await self.bot.whisper("Bye :wave: !")
                                await asyncio.sleep(0.25)
                                return
                            else:
                                await self.bot.whisper("Invalide")
                    else:
                        await self.bot.whisper("Invalide, réessayez.")
        else:
            await self.bot.whisper("Vous n'êtes pas président.")

    @gep.command(pass_context=True, no_pm=True)
    @checks.mod_or_permissions(administrator=True)
    async def forcebai(self, ctx):
        """[ADMIN] Permet de voir les idées enregistrées dans la boite à idée."""
        author = ctx.message.author
        if not ctx.message.server:
            await self.bot.whisper("Lancez cette commande sur le serveur où vous êtes Admin.")
            return
        role = self.sys["GEP_ROLE"]
        r = discord.utils.get(ctx.message.server.roles, name=role)
        retour = False
        while retour == False:
            em = discord.Embed(inline=False)
            msg = ""
            for i in self.sys["GEP_IDEES"]:
                if self.sys["GEP_IDEES"][i]["CHECK"] is False:
                    msg += "__#{}__| **{}** - *{}*\n".format(self.sys["GEP_IDEES"][i]["TAG"],
                                                             self.sys["GEP_IDEES"][i]["AUTHOR"],
                                                             self.sys["GEP_IDEES"][i]["TITRE"])
                else:
                    msg += "__@{}__| **{}** - *{}*\n".format(self.sys["GEP_IDEES"][i]["TAG"],
                                                             self.sys["GEP_IDEES"][i]["AUTHOR"],
                                                             self.sys["GEP_IDEES"][i]["TITRE"])
            else:
                em.set_footer(text="Tapez un numéro pour en savoir plus ou tapez 'Q' pour quitter")
                if msg != "":
                    em.add_field(name="__Boite à idées__", value=msg)
                else:
                    em.add_field(name="__Boite à idées__", value="*La boite à idées est vide*")
                nec = await self.bot.whisper(embed=em)
                channel = nec.channel
            verif = False
            while verif != True:
                rep = await self.bot.wait_for_message(author=author, channel=channel)
                if rep.content.lower() == "q":
                    await self.bot.whisper("Bye :wave:")
                    return
                if rep.content in self.sys["GEP_IDEES"]:
                    num = rep.content
                    verif = True
                    if self.sys["GEP_IDEES"][num]["AUTHOR"] is "Anonyme":
                        em = discord.Embed(colour=int(self.sys["GEP_IDEES"][num]["COLOR"], 16), inline=False)
                        em.set_author(name="Anonyme", icon_url="http://i.imgur.com/iDZRdNk.png")
                        em.add_field(name=self.sys["GEP_IDEES"][num]["TITRE"],
                                     value=self.sys["GEP_IDEES"][num]["TEXTE"])
                        em.set_footer(text="Soumise le: " + self.sys["GEP_IDEES"][num]["TIME"])
                        msg = await self.bot.whisper(embed=em)
                    else:
                        em = discord.Embed(colour=int(self.sys["GEP_IDEES"][num]["COLOR"], 16), inline=False)
                        em.set_author(name=self.sys["GEP_IDEES"][num]["AUTHOR"],
                                      icon_url=self.sys["GEP_IDEES"][num]["IMAGE"])
                        em.add_field(name=self.sys["GEP_IDEES"][num]["TITRE"],
                                     value=self.sys["GEP_IDEES"][num]["TEXTE"])
                        em.set_footer(text="Soumise le: " + self.sys["GEP_IDEES"][num]["TIME"])
                        msg = await self.bot.whisper(embed=em)
                    await asyncio.sleep(0.25)
                    await self.bot.add_reaction(msg, "✔")  # Check
                    await self.bot.add_reaction(msg, "✖")  # Supprimer
                    await self.bot.add_reaction(msg, "🔙")  # Menu
                    await self.bot.add_reaction(msg, "🔚")  # Quitter
                    await asyncio.sleep(0.25)
                    sec = False
                    while sec != True:
                        rep = await self.bot.wait_for_reaction(["✔", "✖", "🔙", "🔚"], message=msg, user=author)
                        if rep.reaction.emoji == "✔":
                            if self.sys["GEP_IDEES"][num]["CHECK"] is False:
                                await self.bot.whisper("Idée approuvée !")
                                self.sys["GEP_IDEES"][num]["CHECK"] = True
                                fileIO("data/extra/sys.json", "save", self.sys)
                            else:
                                await self.bot.whisper("Idée désaprouvée !")
                                self.sys["GEP_IDEES"][num]["CHECK"] = False
                                fileIO("data/extra/sys.json", "save", self.sys)
                        elif rep.reaction.emoji == "✖":
                            await self.bot.whisper("Idée supprimée.")
                            del self.sys["GEP_IDEES"][num]
                            fileIO("data/extra/sys.json", "save", self.sys)
                            sec = True
                        elif rep.reaction.emoji == "🔙":
                            sec = True
                        elif rep.reaction.emoji == "🔚":
                            await self.bot.whisper("Bye :wave: !")
                            await asyncio.sleep(0.25)
                            return
                        else:
                            await self.bot.whisper("Invalide")
                else:
                    await self.bot.whisper("Invalide, réessayez.")

# SYSTEME ==============================================================

def check_folders():
    folders = ("data", "data/extra/")
    for folder in folders:
        if not os.path.exists(folder):
            print("Création du fichier " + folder)
            os.makedirs(folder)

def check_files():
    if not os.path.isfile("data/extra/sys.json"):
        print("Création du fichier systeme Extra...")
        fileIO("data/extra/sys.json", "save", default)

def setup(bot):
    check_folders()
    check_files()
    n = Extra(bot)
    bot.add_cog(n)