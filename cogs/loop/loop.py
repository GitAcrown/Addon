import asyncio
import os
import random
from copy import deepcopy
import discord
from __main__ import send_cmd_help
from discord.ext import commands
from .utils.dataIO import fileIO, dataIO


#'Addon' Exclusive

class Loop:
    """Extension sociale pour Discord."""

    def __init__(self, bot):
        self.bot = bot
        self.acc = dataIO.load_json("data/loop/acc.json") #Comptes
        self.sys = dataIO.load_json("data/loop/sys.json") #Paramètres

    def save(self):
        fileIO("data/loop/acc.json", "save", self.acc)
        fileIO("data/loop/sys.json", "save", self.sys)
        return True

    def new_acc(self, user):
        """Création d'un compte vierge"""
        let = ["A","B","C","D","E","F","G","H","I","J","K","L","M",
               "N","O","P","Q","R","S","T","U","V","W","X","Y","Z"]
        m = random.sample(let, 3)
        mstr = ""
        for e in m:
            mstr += e
        self.acc[user.id] = {"PSEUDO": user.name,
                             "ID": user.id,
                             "SNIP" : "[" + str(user.id[:4]) + "|" + mstr + "]",
                             "SEXE" : None,
                             "ANNIV" : None,
                             "SIGN" : None,
                             "PROF" : None,
                             "COMPTES" : None,
                             "PUBLIC": None,
                             "SUCESS" : [],
                             "FAGS" : []}
        self.save()

    def can_see(self, user, perm):
        """Défini si quelqu'un peut voir le profil d'un autre.
        user > L'utilisateur visé
        perm > Celui qui demande la permission de voir le profil"""
        if user.id and perm.id in self.acc:
            if self.acc[user.id]["PUBLIC"] is True:
                return True
            else:
                if self.acc[perm.id]["SNIP"] in self.acc[user.id]["FAGS"]:
                    return True
                else:
                    return False
        else:
            return None

    def usersnip(self, server, snip):
        """Retrouver l'utilisateur qui possède un snip en particulier."""
        for id in self.acc:
            if self.acc[id]["SNIP"] == snip:
                user = server.get_member(self.acc[id]["ID"])
                return user
        else:
            return False

    def gen_profil(self, user, complete=False):
        if complete is True:
            em = discord.Embed(title="{}".format(user.name), color=0x667399)
            em.set_author(name="[LOOP BETA]",icon_url="http://i.imgur.com/EsX4ZXo.png")
            em.set_thumbnail(url=user.avatar_url)
            em.add_field(name="Sexe", value=self.acc[user.id]["SEXE"] if self.acc[user.id]["SEXE"] != None else "N.R.")
            em.add_field(name="Anniversaire", value=self.acc[user.id]["ANNIV"] if self.acc[user.id]["ANNIV"] != None else "N.R.")
            em.add_field(name="Profession", value=self.acc[user.id]["PROF"] if self.acc[user.id]["PROF"] != None else "N.R.")
            comptes = self.acc[user.id]["COMPTES"]
            if comptes != None:
                msg = ""
                for compte in comptes:
                    msg += "{}: *{}*\n".format(compte[0], compte[1])
                em.add_field(name="Comptes externes", value=msg)
            else:
                em.add_field(name="Comptes externes", value="Aucun")
            em.set_footer(text=self.acc[user.id]["SIGN"])
            return em
        else:
            em = discord.Embed(title="{}".format(user.name), color=0x667399)
            em.set_author(name="[LOOP BETA]", icon_url="http://i.imgur.com/EsX4ZXo.png")
            em.set_thumbnail(url=user.avatar_url)
            em.set_footer(text="Cette personne ne vous autorise pas à voir l'intégralité de son profil.")
            return em

    @commands.group(pass_context=True)
    async def loop(self, ctx):
        """Commandes de Loop"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @loop.command(pass_context=True)
    async def sign(self, ctx, mobile:bool=False):
        """Permet la modification de son profil ou sa création."""
        author = ctx.message.author
        if mobile is False:
            if author.id not in self.acc:
                main = False
                profil_public = profil_sexe = profil_comptes = profil_prof = profil_sign = profil_anniv = None #Défaut
                while main is False:
                    em = discord.Embed(title="INSCRIPTION",color=0x667399)
                    em.set_author(name="[LOOP BETA]",icon_url="http://i.imgur.com/EsX4ZXo.png")
                    msg = "**Champs**\n"
                    msg += "A = Sexe\n"
                    msg += "B = Date d'anniversaire\n"
                    msg += "C = Signature\n"
                    msg += "D = Profession\n"
                    msg += "E = Comptes\n"
                    msg += "F = Confidentialité²\n"
                    msg += "----------------\n"
                    msg += "T = Terminer\n"
                    msg += "Q = Quitter sans sauvegarder"
                    em.add_field(name="Menu",value=msg)
                    em.set_footer(text="Tapez la lettre correspondant à l'onglet à déployer. ² = Champ obligatoire")
                    menu = await self.bot.whisper(embed = em)
                    verif1 = False
                    while verif1 != True:
                        rep = await self.bot.wait_for_message(author=author, channel=menu.channel, timeout=30)
                        onglet = rep.content.upper()
                        if onglet == "A":
                            verif1 = True
                            em = discord.Embed(color=0x667399)
                            em.set_author(name="[LOOP BETA]", icon_url="http://i.imgur.com/EsX4ZXo.png")
                            em.add_field(name="Sexe", value="Quel est votre sexe ?\n👨 = Homme\n👩 = Femme\n❔ = Autre")
                            em.set_footer(text="Utilisez les réactions pour indiquer votre sexe.")
                            sexe = await self.bot.whisper(embed= em)
                            await self.bot.add_reaction(sexe, "👨")
                            await self.bot.add_reaction(sexe, "👩")
                            await self.bot.add_reaction(sexe, "❔")
                            await asyncio.sleep(0.25)
                            rep = await self.bot.wait_for_reaction(["👨","👩","❔"],message=sexe, user=author)
                            if rep.reaction.emoji == "👨":
                                profil_sexe = "Homme"
                                await self.bot.whisper("**Enregistré.**")
                            elif rep.reaction.emoji == "👩":
                                profil_sexe = "Femme"
                                await self.bot.whisper("**Enregistré.**")
                            elif rep.reaction.emoji == "❔":
                                await self.bot.whisper("Veuillez préciser le sexe :")
                                verif2 = False
                                while verif2 != True:
                                    rep2 = await self.bot.wait_for_message(author=author, channel=menu.channel, timeout=30)
                                    if rep2 == None:
                                        await self.bot.whisper("Trop long, retour au menu.")
                                        verif2 = True
                                    else:
                                        profil_sexe = rep2.content.title()
                                        await self.bot.whisper("**Enregistré**")
                                        verif2 = True
                            else:
                                await self.bot.whisper("Invalide.")
                        elif onglet == "B":
                            verif1 = True
                            em = discord.Embed(color=0x667399)
                            em.set_author(name="[LOOP BETA]", icon_url="http://i.imgur.com/EsX4ZXo.png")
                            em.add_field(name="Anniversaire", value="Quel est votre date d'anniversaire ?")
                            em.set_footer(text="Format: jj/mm/aaaa")
                            await self.bot.whisper(embed=em)
                            verif2 = False
                            while verif2 != True:
                                rep = await self.bot.wait_for_message(author=author, channel=menu.channel, timeout=45)
                                if rep == None:
                                    await self.bot.whisper("Trop long, retour au menu.")
                                    verif2 = True
                                elif "/" in rep.content:
                                    if len(rep.content) == 10:
                                        profil_anniv = rep.content
                                        await self.bot.whisper("**Enregistré**")
                                        verif2 = True
                                    else:
                                        await self.bot.whisper("Invalide, réessayez.")
                                else:
                                    await self.bot.whisper("Invalide, réessayez.")
                        elif onglet == "C":
                            verif1 = True
                            em = discord.Embed(color=0x667399)
                            em.set_author(name="[LOOP BETA]", icon_url="http://i.imgur.com/EsX4ZXo.png")
                            em.add_field(name="Signature",
                                         value="Donnez une signature :")
                            em.set_footer(text="Elle apparaitra en bas de votre profil.")
                            await self.bot.whisper(embed=em)
                            verif2 = False
                            while verif2 != True:
                                rep = await self.bot.wait_for_message(author=author, channel=menu.channel, timeout=300)
                                if rep == None:
                                    await self.bot.whisper("Trop long, retour au menu.")
                                    verif2 = True
                                elif len(rep.content) >= 20:
                                    await self.bot.whisper("**Enregistré**")
                                    verif2 = True
                                    profil_sign = rep.content
                                else:
                                    await self.bot.whisper("Invalide (< 20 caractères)")
                        elif onglet == "D":
                            verif1 = True
                            em = discord.Embed(color=0x667399)
                            em.set_author(name="[LOOP BETA]", icon_url="http://i.imgur.com/EsX4ZXo.png")
                            em.add_field(name="Profession",
                                         value="Indiquez votre profession.")
                            em.set_footer(text="Si vous n'en avez pas, écrivez 'Aucune'.")
                            await self.bot.whisper(embed=em)
                            verif2 = False
                            while verif2 != True:
                                rep = await self.bot.wait_for_message(author=author, channel=menu.channel, timeout=60)
                                if rep == None:
                                    await self.bot.whisper("Trop long, retour au menu.")
                                    verif2 = True
                                elif len(rep.content) >= 3:
                                    await self.bot.whisper("**Enregistré**")
                                    verif2 = True
                                    profil_prof= rep.content
                                else:
                                    await self.bot.whisper("Invalide (< 3 caractères)")
                        elif onglet == "E":
                            verif1 = True
                            em = discord.Embed(color=0x667399)
                            em.set_author(name="[LOOP BETA]", icon_url="http://i.imgur.com/EsX4ZXo.png")
                            em.add_field(name="Comptes",
                                         value="Rentrez vos comptes externes.")
                            em.set_footer(text="Format : plateforme1:nomdecompte1/plateforme2:nomdecompte2/[etc]")
                            await self.bot.whisper(embed=em)
                            verif2 = False
                            while verif2 != True:
                                rep = await self.bot.wait_for_message(author=author, channel=menu.channel, timeout=60)
                                if rep == None:
                                    await self.bot.whisper("Trop long, retour au menu.")
                                    verif2 = True
                                elif ":" in rep.content:
                                    diff = rep.content.split("/")
                                    profil_comptes = []
                                    for e in diff:
                                        compte = e.split(":")
                                        profil_comptes.append([compte[0],compte[1]])
                                    if profil_comptes != []:
                                        await self.bot.whisper("**Enregistré**")
                                        verif2=True
                                    else:
                                        await self.bot.whisper("**Invalide, ressayez**")
                                else:
                                    await self.bot.whisper("Invalide, suivez le format indiqué.")
                        elif onglet == "F":
                            verif1 = True
                            em = discord.Embed(color=0x667399)
                            em.set_author(name="[LOOP BETA]", icon_url="http://i.imgur.com/EsX4ZXo.png")
                            em.add_field(name="Confidentialité",
                                         value="🔓 = Public, tous les utilisateurs inscrits à Loop peuvent voir votre profil.\n🔒 = Privé, seuls les utilisateurs que vous avez autorisé peuvent voir votre profil.")
                            em.set_footer(text="Utilisez les réactions ci-dessous pour intéragir")
                            mess = await self.bot.whisper(embed=em)
                            await self.bot.add_reaction(mess, "🔓")
                            await self.bot.add_reaction(mess, "🔒")
                            await asyncio.sleep(0.25)
                            rep = await self.bot.wait_for_reaction(["🔓","🔒"], message=mess, user=author)
                            if rep.reaction.emoji == "🔓":
                                profil_public = True
                                await self.bot.whisper("**Enregistré**")
                            elif rep.reaction.emoji == "🔒":
                                profil_public = False
                                await self.bot.whisper("**Enregistré**")
                            else:
                                await self.bot.whisper("Invalide")
                        elif onglet == "T":
                            verif1 = True
                            if profil_public != None:
                                await self.bot.whisper("**Ouverture du compte...**")
                                self.new_acc(author)
                                await asyncio.sleep(1.5)
                                self.acc[author.id]["SEXE"] = profil_sexe
                                self.acc[author.id]["ANNIV"] = profil_anniv
                                self.acc[author.id]["PROF"] = profil_prof
                                self.acc[author.id]["COMPTES"] = profil_comptes
                                self.acc[author.id]["SIGN"] = profil_sign
                                self.acc[author.id]["PUBLIC"] = profil_public
                                await self.bot.whisper("**Votre compte à été ouvert !**\nVous pouvez y accéder depuis {}loop log".format(ctx.prefix))
                                self.save()
                                return
                            else:
                                await self.bot.whisper("Avant de terminer, vous devez définir vos paramètres de confidentialité.")
                        elif onglet == "Q":
                            await self.bot.whisper("Votre progression n'est pas sauvegardée. Au revoir :wave:")
                            return
                        else:
                            await self.bot.whisper("Invalide, essayez une autre lettre.")
            else:
                main = False
                profil_public = self.acc[author.id]["PUBLIC"]
                profil_anniv = self.acc[author.id]["ANNIV"]
                profil_sexe = self.acc[author.id]["SEXE"]
                profil_sign = self.acc[author.id]["SIGN"]
                profil_comptes = self.acc[author.id]["COMPTES"]
                profil_prof = self.acc[author.id]["PROF"]
                # Défaut
                while main is False:
                    em = discord.Embed(title="MODIFICATION", color=0x667399)
                    em.set_author(name="[LOOP BETA]", icon_url="http://i.imgur.com/EsX4ZXo.png")
                    msg = "**Champs**\n"
                    msg += "A = Sexe\n"
                    msg += "B = Date d'anniversaire\n"
                    msg += "C = Signature\n"
                    msg += "D = Profession\n"
                    msg += "E = Comptes\n"
                    msg += "F = Confidentialité\n"
                    msg += "----------------\n"
                    msg += "T = Terminer\n"
                    msg += "Q = Quitter sans sauvegarder"
                    em.add_field(name="Menu", value=msg)
                    em.set_footer(text="Tapez la lettre correspondant à l'onglet à déployer.")
                    menu = await self.bot.whisper(embed=em)
                    verif1 = False
                    while verif1 != True:
                        rep = await self.bot.wait_for_message(author=author, channel=menu.channel, timeout=30)
                        onglet = rep.content.upper()
                        if onglet == "A":
                            verif1 = True
                            em = discord.Embed(color=0x667399)
                            em.set_author(name="[LOOP BETA]", icon_url="http://i.imgur.com/EsX4ZXo.png")
                            em.add_field(name="Sexe", value="Quel est votre sexe ?\n👨 = Homme\n👩 = Femme\n❔ = Autre")
                            em.set_footer(text="Utilisez les réactions pour indiquer votre sexe.")
                            sexe = await self.bot.whisper(embed=em)
                            await self.bot.add_reaction(sexe, "👨")
                            await self.bot.add_reaction(sexe, "👩")
                            await self.bot.add_reaction(sexe, "❔")
                            await asyncio.sleep(0.25)
                            rep = await self.bot.wait_for_reaction(["👨", "👩", "❔"], message=sexe, user=author)
                            if rep.reaction.emoji == "👨":
                                profil_sexe = "Homme"
                                await self.bot.whisper("**Enregistré.**")
                            elif rep.reaction.emoji == "👩":
                                profil_sexe = "Femme"
                                await self.bot.whisper("**Enregistré.**")
                            elif rep.reaction.emoji == "❔":
                                await self.bot.whisper("Veuillez préciser le sexe :")
                                verif2 = False
                                while verif2 != True:
                                    rep2 = await self.bot.wait_for_message(author=author, channel=menu.channel, timeout=30)
                                    if rep2 == None:
                                        await self.bot.whisper("Trop long, retour au menu.")
                                        verif2 = True
                                    else:
                                        profil_sexe = rep2.content.title()
                                        await self.bot.whisper("**Enregistré**")
                                        verif2 = True
                            else:
                                await self.bot.whisper("Invalide.")
                        elif onglet == "B":
                            verif1 = True
                            em = discord.Embed(color=0x667399)
                            em.set_author(name="[LOOP BETA]", icon_url="http://i.imgur.com/EsX4ZXo.png")
                            em.add_field(name="Anniversaire", value="Quel est votre date d'anniversaire ?")
                            em.set_footer(text="Format: jj/mm/aaaa")
                            await self.bot.whisper(embed=em)
                            verif2 = False
                            while verif2 != True:
                                rep = await self.bot.wait_for_message(author=author, channel=menu.channel, timeout=45)
                                if rep == None:
                                    await self.bot.whisper("Trop long, retour au menu.")
                                    verif2 = True
                                elif "/" in rep.content:
                                    if len(rep.content) == 10:
                                        profil_anniv = rep.content
                                        await self.bot.whisper("**Enregistré**")
                                        verif2 = True
                                    else:
                                        await self.bot.whisper("Invalide, réessayez.")
                                else:
                                    await self.bot.whisper("Invalide, réessayez.")
                        elif onglet == "C":
                            verif1 = True
                            em = discord.Embed(color=0x667399)
                            em.set_author(name="[LOOP BETA]", icon_url="http://i.imgur.com/EsX4ZXo.png")
                            em.add_field(name="Signature",
                                         value="Donnez une signature :")
                            em.set_footer(text="Elle apparaitra en bas de votre profil.")
                            await self.bot.whisper(embed=em)
                            verif2 = False
                            while verif2 != True:
                                rep = await self.bot.wait_for_message(author=author, channel=menu.channel, timeout=300)
                                if rep == None:
                                    await self.bot.whisper("Trop long, retour au menu.")
                                    verif2 = True
                                elif len(rep.content) >= 20:
                                    await self.bot.whisper("**Enregistré**")
                                    verif2 = True
                                    profil_sign = rep.content
                                else:
                                    await self.bot.whisper("Invalide (< 20 caractères)")
                        elif onglet == "D":
                            verif1 = True
                            em = discord.Embed(color=0x667399)
                            em.set_author(name="[LOOP BETA]", icon_url="http://i.imgur.com/EsX4ZXo.png")
                            em.add_field(name="Profession",
                                         value="Indiquez votre profession.")
                            em.set_footer(text="Si vous n'en avez pas, écrivez 'Aucune'.")
                            await self.bot.whisper(embed=em)
                            verif2 = False
                            while verif2 != True:
                                rep = await self.bot.wait_for_message(author=author, channel=menu.channel, timeout=60)
                                if rep == None:
                                    await self.bot.whisper("Trop long, retour au menu.")
                                    verif2 = True
                                elif len(rep.content) >= 3:
                                    await self.bot.whisper("**Enregistré**")
                                    verif2 = True
                                    profil_prof = rep.content
                                else:
                                    await self.bot.whisper("Invalide (< 3 caractères)")
                        elif onglet == "E":
                            verif1 = True
                            em = discord.Embed(color=0x667399)
                            em.set_author(name="[LOOP BETA]", icon_url="http://i.imgur.com/EsX4ZXo.png")
                            em.add_field(name="Comptes",
                                         value="Rentrez vos comptes externes.")
                            em.set_footer(text="Format : plateforme1:nomdecompte1/plateforme2:nomdecompte2/[etc]")
                            await self.bot.whisper(embed=em)
                            verif2 = False
                            while verif2 != True:
                                rep = await self.bot.wait_for_message(author=author, channel=menu.channel, timeout=60)
                                if rep == None:
                                    await self.bot.whisper("Trop long, retour au menu.")
                                    verif2 = True
                                elif ":" in rep.content:
                                    diff = rep.content.split("/")
                                    profil_comptes = []
                                    for e in diff:
                                        compte = e.split(":")
                                        profil_comptes.append([compte[0], compte[1]])
                                    if profil_comptes != []:
                                        await self.bot.whisper("**Enregistré**")
                                        verif2 = True
                                    else:
                                        await self.bot.whisper("**Invalide, ressayez**")
                                else:
                                    await self.bot.whisper("Invalide, suivez le format indiqué.")
                        elif onglet == "F":
                            verif1 = True
                            em = discord.Embed(color=0x667399)
                            em.set_author(name="[LOOP BETA]", icon_url="http://i.imgur.com/EsX4ZXo.png")
                            em.add_field(name="Confidentialité",
                                         value="🔓 = Public, tous les utilisateurs inscrits à Loop peuvent voir votre profil.\n🔒 = Privé, seuls les utilisateurs que vous avez autorisé peuvent voir votre profil.")
                            em.set_footer(text="Utilisez les réactions ci-dessous pour intéragir")
                            mess = await self.bot.whisper(embed=em)
                            await self.bot.add_reaction(mess, "🔓")
                            await self.bot.add_reaction(mess, "🔒")
                            await asyncio.sleep(0.25)
                            rep = await self.bot.wait_for_reaction(["🔓", "🔒"], message=mess, user=author)
                            if rep.reaction.emoji == "🔓":
                                profil_public = True
                                await self.bot.whisper("**Enregistré**")
                            elif rep.reaction.emoji == "🔒":
                                profil_public = False
                                await self.bot.whisper("**Enregistré**")
                            else:
                                await self.bot.whisper("Invalide")
                        elif onglet == "T":
                            verif1 = True
                            await self.bot.whisper("**Modification du compte...**")
                            await asyncio.sleep(1)
                            self.acc[author.id]["SEXE"] = profil_sexe
                            self.acc[author.id]["ANNIV"] = profil_anniv
                            self.acc[author.id]["PROF"] = profil_prof
                            self.acc[author.id]["COMPTES"] = profil_comptes
                            self.acc[author.id]["SIGN"] = profil_sign
                            self.acc[author.id]["PUBLIC"] = profil_public
                            await self.bot.whisper("**Votre compte à été modifié avec succès.**\nVous pouvez y accéder depuis {}loop log".format(ctx.prefix))
                            self.save()
                            return

                        elif onglet == "Q":
                            await self.bot.whisper("Votre progression n'est pas sauvegardée. Au revoir :wave:")
                            return
                        else:
                            await self.bot.whisper("Invalide, essayez une autre lettre.")
        else:
            await self.bot.whisper("Un affichage version mobile arrivera bientôt !\n En attendant, inscrivez-vous sur un appareil doté d'un écran suffisamment grand.")

    @loop.command(pass_context=True, no_pm=True)
    async def log(self, ctx, user:discord.Member = None):
        """Permet de voir le profil d'un utilisateur ou à défaut de soi-même."""
        author = ctx.message.author
        server = ctx.message.server
        if user == None:
            user = author
        if user.id and author.id in self.acc:
            if user.id != author.id:
                auto = self.can_see(user, author)
                if auto is True:
                    if self.acc[author.id]["SNIP"] in self.acc[user.id]["FAGS"]:
                        em = self.gen_profil(user, complete=True)
                        menu = await self.bot.whisper(embed=em)
                        await self.bot.add_reaction(menu, "✖") #Retirer l'ami
                        await self.bot.add_reaction(menu, "❓")
                        await asyncio.sleep(0.25)
                        verif = False
                        while verif != True:
                            rep = await self.bot.wait_for_reaction(["✖", "❓"], message=menu, user=author, timeout=60)
                            if rep == None:
                                return
                            elif rep.reaction.emoji == "✖":
                                an = await self.bot.whisper(
                                    "Voulez-vous réellement retirer ce Fag de votre entourage ? (O/N)")
                                rep = await self.bot.wait_for_message(author=author, channel=an.channel, timeout=15)
                                if rep == None:
                                    await self.bot.whisper("Réponse trop longue. Action annulée.")
                                    verif = True
                                elif rep.content.lower() == "o":
                                    self.acc[user.id]["FAGS"].remove(self.acc[author.id]["SNIP"])
                                    self.acc[author.id]["FAGS"].remove(self.acc[user.id]["SNIP"])
                                    await self.bot.whisper("**Retiré.**")
                                    self.save()
                                    return
                                elif rep.content.lower() == "n":
                                    await self.bot.whisper("Action annulée.")
                                    verif = True
                                else:
                                    await self.bot.whisper("Invalide. Action annulée.")
                                    verif = True
                            elif rep.reaction.emoji == "❓":
                                aide = "**__AIDE__**\n"
                                aide += "✖ = Retirer ce Fag\n"
                                aide += "❓ = Recevoir de l'aide\n"
                                await self.bot.whisper(aide)
                                await asyncio.sleep(1)
                                verif=True
                            else:
                                await self.bot.whisper("Invalide")
                    else:
                        em = self.gen_profil(user, complete=True)
                        menu = await self.bot.whisper(embed=em)
                        await self.bot.add_reaction(menu, "📨")  # Envoyer requete
                        await self.bot.add_reaction(menu, "❓")
                        await asyncio.sleep(0.25)
                        verif = False
                        while verif != True:
                            rep = await self.bot.wait_for_reaction(["📨", "❓"], message=menu, user=author, timeout=60)
                            if rep == None:
                                return
                            elif rep.reaction.emoji == "📨":
                                an = await self.bot.whisper(
                                    "Voulez-vous envoyer une requete d'amis à cette personne ? (O/N)")
                                rep = await self.bot.wait_for_message(author=author, channel=an.channel, timeout=15)
                                if rep == None:
                                    await self.bot.whisper("Réponse trop longue. Action annulée.")
                                    verif = True
                                elif rep.content.lower() == "o":
                                    await self.bot.whisper(
                                        "**Demande envoyée**\n*Si aucune réponse n'est donnée dans les 5 prochaines minutes, la demande expirera*")
                                    em = discord.Embed(color=0x667399)
                                    em.set_author(name="[LOOP BETA]", icon_url="http://i.imgur.com/EsX4ZXo.png")
                                    em.add_field(name="Demande d'amitié",
                                                 value="**{}** demande à être ami avec vous.\nVous l'acceptez ?".format(author.name))
                                    em.set_footer(text="Interagissez avec les boutons ci-dessous.")
                                    sec = await self.bot.send_message(user, embed=em)
                                    await self.bot.add_reaction(sec, "✔")
                                    await self.bot.add_reaction(sec, "✖")
                                    await asyncio.sleep(0.25)
                                    rep = await self.bot.wait_for_reaction(["✖", "✔"], message=sec, user=user,
                                                                           timeout=300)
                                    if rep == None:
                                        await self.bot.send_message(user,
                                                                    "Temps de réponse trop long (> 5m). Demande expirée.")
                                        await self.bot.whisper("**La demande a expirée**")
                                        verif = True
                                    elif rep.reaction.emoji == "✔":
                                        self.acc[author.id]["FAGS"].append(self.acc[user.id]["SNIP"])
                                        self.acc[user.id]["FAGS"].append(self.acc[author.id]["SNIP"])
                                        await self.bot.send_message(user, "**Demande acceptée.**")
                                        await self.bot.whisper("**Demande acceptée.**")
                                        self.save()
                                        return
                                    elif rep.reaction.emoji == "✖":
                                        await self.bot.send_message(user, "**Demande refusée.**")
                                        await self.bot.whisper("**Demande refusée.**")
                                        verif = True
                                    else:
                                        await self.bot.send_message(user, "Invalide")
                                elif rep.content.lower() == "n":
                                    await self.bot.whisper("Action annulée.")
                                    verif = True
                                else:
                                    await self.bot.whisper("Invalide. Action annulée.")
                                    verif = True
                            elif rep.reaction.emoji == "❓":
                                aide = "**__AIDE__**\n"
                                aide += "📨 = Envoyer requete d'amis\n"
                                aide += "❓ = Recevoir de l'aide\n"
                                await self.bot.whisper(aide)
                                await asyncio.sleep(1)
                                verif = True
                            else:
                                await self.bot.whisper("Invalide")

                elif auto is False:
                    em = self.gen_profil(user, complete=False)
                    menu = await self.bot.whisper(embed=em)
                    await self.bot.add_reaction(menu, "📨")  # Envoyer requete
                    await self.bot.add_reaction(menu, "❓")
                    await asyncio.sleep(0.25)
                    verif = False
                    while verif != True:
                        rep = await self.bot.wait_for_reaction(["📨", "❓"], message=menu, user=author, timeout=60)
                        if rep == None:
                            return
                        elif rep.reaction.emoji == "📨":
                            an = await self.bot.whisper(
                                "Voulez-vous envoyer une requete d'amis à cette personne ? (O/N)")
                            rep = await self.bot.wait_for_message(author=author, channel=an.channel, timeout=15)
                            if rep == None:
                                await self.bot.whisper("Réponse trop longue. Action annulée.")
                                verif = True
                            elif rep.content.lower() == "o":
                                await self.bot.whisper("**Demande envoyée**\n*Si aucune réponse n'est donnée dans les 5 prochaines minutes, la demande expirera*")
                                em = discord.Embed(color=0x667399)
                                em.set_author(name="[LOOP BETA", icon_url="http://i.imgur.com/EsX4ZXo.png")
                                em.add_field(name="Demande d'amitié",value="**{}** demande à être ami avec vous.\nVous l'acceptez ?".format(author.name))
                                em.set_footer(text="Interagissez avec les boutons ci-dessous.")
                                sec = await self.bot.send_message(user, embed=em)
                                await self.bot.add_reaction(sec, "✔")
                                await self.bot.add_reaction(sec, "✖")
                                await asyncio.sleep(0.25)
                                rep = await self.bot.wait_for_reaction(["✖","✔"], message=sec, user=user, timeout=300)
                                if rep == None:
                                    await self.bot.send_message(user, "Temps de réponse trop long (> 5m). Demande expirée.")
                                    await self.bot.whisper("**La demande a expirée**")
                                    verif = True
                                elif rep.reaction.emoji == "✔":
                                    self.acc[author.id]["FAGS"].append(self.acc[user.id]["SNIP"])
                                    self.acc[user.id]["FAGS"].append(self.acc[author.id]["SNIP"])
                                    await self.bot.send_message(user ,"**Demande acceptée.**")
                                    await self.bot.whisper("**Demande acceptée.**")
                                    self.save()
                                    return
                                elif rep.reaction.emoji == "✖":
                                    await self.bot.send_message(user, "**Demande refusée.**")
                                    await self.bot.whisper("**Demande refusée.**")
                                    verif = True
                                else:
                                    await self.bot.send_message(user, "Invalide")
                            elif rep.content.lower() == "n":
                                await self.bot.whisper("Action annulée.")
                                verif = True
                            else:
                                await self.bot.whisper("Invalide. Action annulée.")
                                verif = True
                        elif rep.reaction.emoji == "❓":
                            aide = "**__AIDE__**\n"
                            aide += "📨 = Envoyer requete d'amis\n"
                            aide += "❓ = Recevoir de l'aide\n"
                            await self.bot.whisper(aide)
                            await asyncio.sleep(1)
                            verif = True
                        else:
                            await self.bot.whisper("Invalide")
                else:
                    await self.bot.whisper("Erreur, l'un des deux utilisateur ne possède pas de profil Loop.")
            else: #L'auteur du message consulte son propre profil
                main = False
                while main != True:
                    em = self.gen_profil(user, complete=True)
                    menu = await self.bot.whisper(embed=em)
                    await self.bot.add_reaction(menu, "👥") #Voir ses fags (amis)
                    await self.bot.add_reaction(menu, "📝") #Modifier profil
                    await self.bot.add_reaction(menu, "💥") #Supprimer profil
                    await self.bot.add_reaction(menu, "❓") #Aide
                    await asyncio.sleep(0.25)
                    verif = False
                    while verif != True:
                        rep = await self.bot.wait_for_reaction(["👥","📝","💥","❓"], message=menu, user=user, timeout=60)
                        if rep == None:
                            return
                        elif rep.reaction.emoji == "👥":
                            if self.acc[user.id]["FAGS"] != []:
                                em = discord.Embed(color=0x667399)
                                amis = ""
                                for fag in self.acc[user.id]["FAGS"]:
                                    ami = self.usersnip(server, fag)
                                    amis += "#*{}* | **{}**\n".format(fag, ami.name)
                                em.add_field(name= "Vos Fags",value=amis)
                                await self.bot.whisper(embed=em)
                                await asyncio.sleep(1)
                                verif = True
                            else:
                                await self.bot.whisper("Vous n'avez pas d'amis.")
                                await asyncio.sleep(0.5)
                                verif = True
                        elif rep.reaction.emoji == "📝":
                            await self.bot.whisper("Chargement ...")
                            await asyncio.sleep(1.5)
                            new_message = deepcopy(ctx.message)
                            new_message.content = ctx.prefix + "loop sign"
                            await self.bot.process_commands(new_message)
                            return
                        elif rep.reaction.emoji == "💥":
                            an = await self.bot.whisper("Voulez-vous réellement supprimer définitivement votre profil ? (O/N)")
                            rep = await self.bot.wait_for_message(author=user, channel=an.channel, timeout=15)
                            if rep == None:
                                await self.bot.whisper("Réponse trop longue. Action annulée.")
                                verif = True
                            elif rep.content.lower() == "o":
                                key = self.acc[user.id]["SNIP"]
                                for u in self.acc:
                                    if key in self.acc[u]["FAGS"]:
                                        self.acc[u]["FAGS"].remove(key)
                                del self.acc[user.id]
                                await self.bot.whisper("**Supprimé.**")
                                self.save()
                                return
                            elif rep.content.lower() == "n":
                                await self.bot.whisper("Action annulée.")
                                verif = True
                            else:
                                await self.bot.whisper("Invalide. Action annulée.")
                                verif = True
                        elif rep.reaction.emoji == "❓":
                            aide = "**__AIDE__**\n"
                            aide += "👥 = Voir ses fags\n"
                            aide += "📝 = Modifier son profil\n"
                            aide += "💥 = Supprimer son profil\n"
                            aide += "❓ = Recevoir de l'aide\n"
                            await self.bot.whisper(aide)
                            await asyncio.sleep(1)
                            verif=True
                        else:
                            await self.bot.whisper("Invalide.")

        else:
            await self.bot.whisper("Un des deux utilisateur ne possède pas de compte Loop.")

def check_folders():
    if not os.path.exists("data/loop"):
        print("Creation du dossier loop...")
        os.makedirs("data/loop")

def check_files():
    if not os.path.isfile("data/loop/acc.json"):
        print("Creation du fichier de comptes loop...")
        fileIO("data/loop/acc.json", "save", {})

    if not os.path.isfile("data/loop/sys.json"):
        print("Creation du fichier de paramètres loop...")
        fileIO("data/loop/sys.json", "save", {})

def setup(bot):
    check_folders()
    check_files()
    n = Loop(bot)
    bot.add_cog(n)  
