import discord
from discord.ext import commands
from .utils import checks
import asyncio
import os
import operator
import random
import time
import datetime
from .utils.chat_formatting import *
from cogs.utils.dataIO import fileIO, dataIO
from __main__ import send_cmd_help, settings

default = {"GEP_ROLE": None, "GEP_IDEES": {}, "GEP_PTAG": 1, "AFK_LIST": [], "AFK": True, "ELECT": False,
           "ROLELIST": [], "ELECT_START": False, "ELECT_NUM": 1, "VOTED": [], "BLANC": 0, "AUTORISE": []}

class Extra:
    """Module d'outils communautaire."""

    def __init__(self, bot):
        self.bot = bot
        self.sys = dataIO.load_json("data/extra/sys.json")
        self.goulag = dataIO.load_json("data/extra/goulag.json")
        self.wiki = dataIO.load_json("data/extra/wiki.json")
        self.elect = dataIO.load_json("data/extra/elect.json")
        if "AUTORISE" not in self.sys:
            self.old()  # Importe les anciennes données en ajoutant les nouvelles

    def eligible(self, server, user):
        for role in self.sys["ROLELIST"]:
            r = discord.utils.get(server.roles, name=role)
            if role in [r.name for r in user.roles]:
                return True
        else:
            return False

    def old(self):  # C'est bordélique mais ça marche
        gep_role = self.sys["GEP_ROLE"]
        gep_idees = self.sys["GEP_IDEES"]
        gep_ptag = self.sys["GEP_PTAG"]
        afk_list = self.sys["AFK_LIST"]
        afk = self.sys["AFK"]
        self.sys = default
        self.sys["GEP_ROLE"] = gep_role
        self.sys["GEP_IDEES"] = gep_idees
        self.sys["GEP_PTAG"] = gep_ptag
        self.sys["AFK_LIST"] = afk_list
        self.sys["AFK"] = afk
        fileIO("data/extra/sys.json", "save", self.sys)

    def find_adv(self, server, exc = []):
        liste = []
        for member in server.members:
            if member.id in self.mgdata:
                if not member.id in exc:
                    if self.mgdata[member.id]["ACTIF"] == True:
                        liste.append(member.id)
        else:
            rand = random.choice(liste)
            return rand

    @commands.command(pass_context=True)
    async def cred(self, ctx):
        author = ctx.message.author
        arc = self.bot.get_cog('Arcade').arc
        await self.bot.say("Vous avez {} crédits Arc !".format(arc.get_profil(author).credits))

    # RP ===================================================================

    @commands.command(aliases = ["d"], pass_context=True)
    async def rolld(self, ctx, nombre: int, multiple: int = None):
        """Permet de rouler un dé

        Ajouter un multiple permet de lancer x dés en même temps."""
        if nombre > 1:
            msg = ""
            if nombre < 100:
                if multiple != None:
                    a = 0
                    while a < multiple:
                        a += 1
                        roll = random.randint(1, nombre)
                        msg += "d{} - #{}: {}\n".format(nombre, a, roll)
                    await self.bot.say(msg)
                else:
                    roll = random.randint(1, nombre)
                    await self.bot.say("d{}: {}".format(nombre, roll))
            elif nombre == 100:
                if multiple != None:
                    a = 0
                    while a < multiple:
                        unite = random.randint(0, 9)
                        diz = random.randint(0, 9)
                        a += 1
                        roll =  "{}&{}".format(unite, diz)
                        msg += "d{} - #{}: {}\n".format(nombre, a, roll)
                    await self.bot.say(msg)
                else:
                    unite = random.randint(0, 9)
                    diz = random.randint(0, 9)
                    roll = "{}&{}".format(unite, diz)
                    await self.bot.say("d{}: {}\n".format(nombre, roll))
            else:
                await self.bot.say("Le nombre doit être inférieur ou égal à 100.")
        else:
            await self.bot.say("Le nombre doit être positif et supérieur à 1.")


    # ELECT >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    @commands.group(pass_context=True)
    async def pres(self, ctx):
        """Commandes d'élections présidentielles"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @pres.command(pass_context=True)
    @checks.admin_or_permissions(ban_members=True)
    async def candidature(self, ctx):
        """Permet de démarrer/arrêter les candidatures."""
        if "ELECT" not in self.sys:
            self.sys["ELECT"] = False
            self.sys["ROLELIST"] = []
            fileIO("data/extra/sys.json", "save", self.sys)
        if self.sys["ELECT"] is False:
            self.sys["ELECT"] = True
            fileIO("data/extra/sys.json", "save", self.sys)
            await self.bot.say("**Les candidatures sont démarrées.**")
        else:
            self.sys["ELECT"] = False
            self.elect = {}
            self.sys["ELECT_START"] = False
            self.sys["ELECT_NUM"] = 1
            self.sys["VOTED"] = []
            self.sys["BLANC"] = 0
            fileIO("data/extra/sys.json", "save", self.sys)
            fileIO("data/extra/elect.json", "save", self.elect)
            await self.bot.say("**L'élection est terminée.**")

    @pres.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(ban_members=True)
    async def rolelist(self, ctx):
        """Permet de régler les rôles pour la candidature."""
        roles = ctx.message.role_mentions
        self.sys["ROLELIST"] = []
        msg = ""
        if roles != []:
            for role in roles:
                self.sys["ROLELIST"].append(role.name)
                msg += "- Ajout de {}\n".format(role.name)
            await self.bot.say(msg)
        else:
            await self.bot.say("Vous devez mentionner au moins un rôle dans votre commande.")
        fileIO("data/extra/sys.json", "save", self.sys)

    @pres.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(ban_members=True)
    async def register(self, ctx, user: discord.Member, supp: discord.Member):
        """Ajouter un candidat à la présidentielle."""
        author = ctx.message.author
        server = ctx.message.server
        rolelist = self.sys["ROLELIST"]
        if self.sys["ELECT"] is True:
            if self.eligible(server, user) and self.eligible(server, supp):
                if user.id in self.elect:
                    await self.bot.whisper(
                        "L'utilisateur étant déjà inscrit, ses informations sont remises à 0 pour une réinscription.")
                num = self.sys["ELECT_NUM"]
                self.sys["ELECT_NUM"] += 1
                self.elect[user.id] = {"NUMERO": num, "USER_NAME": user.name, "USER_ID": user.id,
                                       "SUPP_NAME": supp.name,
                                       "SUPP_ID": supp.id, "MOTTO": None, "PROG": None, "AFFICHE": None, "VOTES": 0}
                msg = await self.bot.whisper(
                    "**Veuillez fournir une phrase d'accroche**\n*Si le candidat n'en possède pas, tapez 'none'*")
                verif = False
                while verif != True:
                    rep = await self.bot.wait_for_message(author=author, channel=msg.channel, timeout=120)
                    if len(rep.content) > 4:
                        await self.bot.whisper("Enregistrée.")
                        self.elect[user.id]["MOTTO"] = rep.content
                        fileIO("data/extra/elect.json", "save", self.elect)
                        verif = True
                    elif rep == None:
                        await self.bot.whisper("Annulation.. (Vous ne répondez pas). Au revoir :wave:")
                        return
                    elif rep.content.lower() == "none":
                        await self.bot.whisper("Ignoré.")
                        verif = True
                    else:
                        await self.bot.whisper("Invalide, réessayez avec au moins 4 caractères.")
                await asyncio.sleep(0.5)
                await self.bot.whisper(
                    "**Veuillez fournir un URL valide et publique vers son programme**\n*Si le candidat n'en possède pas, tapez 'none'*")
                verif = False
                while verif != True:
                    rep = await self.bot.wait_for_message(author=author, channel=msg.channel, timeout=500)
                    if "http" in rep.content:
                        await self.bot.whisper("Enregistrée.")
                        self.elect[user.id]["PROG"] = rep.content
                        fileIO("data/extra/elect.json", "save", self.elect)
                        verif = True
                    elif rep == None:
                        await self.bot.whisper("Annulation.. (Vous ne répondez pas). Au revoir :wave:")
                        return
                    elif rep.content.lower() == "none":
                        await self.bot.whisper("Ignoré.")
                        verif = True
                    else:
                        await self.bot.whisper("Invalide, le lien ne semble pas valide.")
                await asyncio.sleep(0.5)
                await self.bot.whisper(
                    "**Veuillez fournir un URL valide et publique vers l'affiche**\n*Si le candidat n'en possède pas, tapez 'none'*")
                verif = False
                while verif != True:
                    rep = await self.bot.wait_for_message(author=author, channel=msg.channel, timeout=500)
                    if "http" in rep.content:
                        await self.bot.whisper("Enregistrée.")
                        self.elect[user.id]["AFFICHE"] = rep.content
                        fileIO("data/extra/elect.json", "save", self.elect)
                        verif = True
                    elif rep == None:
                        await self.bot.whisper("Annulation.. (Vous ne répondez pas). Au revoir :wave:")
                        return
                    elif rep.content.lower() == "none":
                        await self.bot.whisper("Ignoré.")
                        verif = True
                    else:
                        await self.bot.whisper("Invalide, le lien ne semble pas valide.")
                await asyncio.sleep(0.25)
                await self.bot.whisper("Terminé, le candidat est inscrit aux présidentielles !")
            else:
                await self.bot.say("Le candidat ou son suppléant ne sont pas éligible.")
        else:
            await self.bot.say("Aucune élection n'est ouverte.")

    def compare_role(self, user, rolelist):
        for role in rolelist:
            if role in [r.name for r in user.roles]:
                return True
        else:
            return False

    @pres.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(ban_members=True)
    async def ready(self, ctx, titre: str, description: str = None):
        """Permet de démarrer/terminer les élections présidentielles."""
        server = ctx.message.server
        if self.sys["ELECT"] is True:
            if self.sys["ELECT_START"] is False:
                self.sys["ELECT_START"] = True
                to_mp = []
                roles = self.sys["ROLELIST"]
                for member in server.members:
                    if self.compare_role(member, roles):
                        try:
                            to_mp.append(member.id)
                        except:
                            pass

                if description != None:
                    em = discord.Embed(title=titre, description=description)
                else:
                    em = discord.Embed(title=titre)
                msg = ""
                await asyncio.sleep(0.5)
                await self.bot.say("**Rédaction du message...**")
                for cand in self.elect:
                    num = self.elect[cand]["NUMERO"]
                    pseudo = self.elect[cand]["USER_NAME"]
                    supp = self.elect[cand]["SUPP_NAME"]
                    msg += "__#{}__ | **{}** / *{}*\n".format(num, pseudo, supp)
                em.add_field(name="__Candidats et suppléants__", value=msg)
                em.set_footer(text="Utilisez la commande '{}vote' pour voter !".format(ctx.prefix))
                await asyncio.sleep(0.5)
                await self.bot.say("**Listage et envoie des MP...**")
                erreur = []
                for user in to_mp:
                    member = server.get_member(user)
                    self.sys["AUTORISE"].append(member.id)
                    try:
                        await self.bot.send_message(member, embed=em)
                    except:
                        erreur.append(str(member))
                await asyncio.sleep(0.25)
                if erreur == []:
                    await self.bot.say("**L'ensemble des MP ont été correctement envoyés**")
                else:
                    liste = ""
                    for u in erreur:
                        liste += "- *{}*\n".format(u)
                    await self.bot.say(
                        "**Les MP ont étés envoyés.**\nQuelques personnes peuvent ne pas avoir reçu le MP (Banni, bloqué, etc...):\n{}".format(
                            liste))
                fileIO("data/extra/elect.json", "save", self.elect)
                fileIO("data/extra/sys.json", "save", self.sys)
            else:
                await self.bot.say("Voulez-vous arrêter les élections ? (O/N)")
                rep = await self.bot.wait_for_message(author=ctx.message.author, channel=ctx.message.channel,
                                                      timeout=20)
                hip = rep.content.lower()
                ok = False
                if hip == "o":
                    await self.bot.say("Arrêt des éléctions...")
                    ok = True
                elif hip == "n":
                    await self.bot.say("Annulation...")
                    return
                elif rep == None:
                    await self.bot.say("Annulation... (Temps de réponse trop long)")
                    return
                else:
                    await self.bot.say("Annulation... (Invalide)")
                    return
                if ok is True:
                    self.sys["ELECT_START"] = False
                    await self.bot.say("Mentionnez le(s) channel(s) où je dois poster les résulats")
                    rep = await self.bot.wait_for_message(author=ctx.message.author, channel=ctx.message.channel)
                    if rep.channel_mentions != []:
                        em = discord.Embed(title="Résultats des élections")
                        res = ""
                        clean = []
                        total = self.sys["BLANC"]
                        for cand in self.elect:
                            total += self.elect[cand]["VOTES"]
                        for cand in self.elect:
                            prc = (self.elect[cand]["VOTES"] / total) * 100
                            prc = round(prc, 2)
                            clean.append([self.elect[cand]["USER_NAME"], self.elect[cand]["SUPP_NAME"],
                                          self.elect[cand]["VOTES"], prc])
                        prc = (self.sys["BLANC"] / total) * 100
                        prc = round(prc, 2)
                        clean.append(["Blanc", "X", self.sys["BLANC"], prc])

                        clean = sorted(clean, key=operator.itemgetter(2))
                        clean.reverse()
                        for e in clean:
                            res += "{} voix ({}%) | **{}** / *{}*\n".format(e[2], e[3], e[0], e[1])
                        em.add_field(name="Votes (%) | Candidat / Suppléant", value=res)
                        em.set_footer(
                            text="Merci d'avoir participé et félicitation aux gagnants ! [Total = {} votes]".format(
                                total))
                        for chan in rep.channel_mentions:
                            await asyncio.sleep(0.25)
                            await self.bot.send_message(chan, embed=em)
                        for u in self.elect:
                            self.elect[u]["VOTES"] = 0
                        self.sys["VOTED"] = []
                        self.sys["BLANC"] = 0
                        fileIO("data/extra/elect.json", "save", self.elect)
                        fileIO("data/extra/sys.json", "save", self.sys)
                    else:
                        await self.bot.say("Annulation... (Vous n'avez rien mentionné)")
                else:
                    pass
        else:
            await self.bot.say("Aucune élection n'est ouverte.")

    @pres.command(pass_context=True)
    @checks.admin_or_permissions(ban_members=True)
    async def stats(self, ctx):
        """Permet de voir les statistiques (Modération/Administration)"""
        if self.sys["ELECT"] is True:
            if self.sys["ELECT_START"] is True:
                em = discord.Embed(title="Statistiques")
                res = ""
                clean = []
                total = self.sys["BLANC"]
                for cand in self.elect:
                    total += self.elect[cand]["VOTES"]
                for cand in self.elect:
                    prc = (self.elect[cand]["VOTES"] / total) * 100
                    prc = round(prc, 2)
                    clean.append([self.elect[cand]["USER_NAME"], self.elect[cand]["SUPP_NAME"],
                                  self.elect[cand]["VOTES"], prc])
                prc = (self.sys["BLANC"] / total) * 100
                prc = round(prc, 2)
                clean.append(["Blanc", "X", self.sys["BLANC"], prc])

                clean = sorted(clean, key=operator.itemgetter(2))
                clean.reverse()
                for e in clean:
                    res += "__{}__ ({}%) | **{}** / *{}*\n".format(e[2], e[3], e[0], e[1])
                em.add_field(name="Votes (%) | Candidat / Suppléant", value=res)
                em.set_footer(
                    text="Ces statistiques sont privées et doivent rester confidentielles [Total = {} votes]".format(
                        total))
                await self.bot.whisper(embed=em)
            else:
                await self.bot.say("Aucun vote en cours.")
        else:
            await self.bot.say("Pas d'élections prévues.")

    @pres.command(pass_context=True)
    @checks.admin_or_permissions(ban_members=True)
    async def denied(self, ctx, user: discord.Member):
        """Permet d'empêcher un utilisateur de pouvoir voter."""
        if self.sys["ELECT_START"] is True:
            if user.id in self.sys["AUTORISE"]:
                self.sys["AUTORISE"].remove(user.id)
                await self.bot.say("Il ne pourra plus voter.")
                fileIO("data/extra/sys.json", "save", self.sys)
            else:
                await self.bot.say("L'utilisateur ne peut déjà ne pas voter.")
        else:
            await self.bot.say("Aucune élection en cours.")

    @pres.command(pass_context=True)
    @checks.admin_or_permissions(ban_members=True)
    async def accept(self, ctx, user: discord.Member):
        """Permet d'autoriser un utilisateur à pouvoir voter."""
        if self.sys["ELECT_START"] is True:
            if user.id not in self.sys["AUTORISE"]:
                self.sys["AUTORISE"].append(user.id)
                await self.bot.say("Il pourra désormais voter.")
                fileIO("data/extra/sys.json", "save", self.sys)
            else:
                await self.bot.say("L'utilisateur peut déjà voter.")
        else:
            await self.bot.say("Aucune élection en cours.")

    @commands.command(name="vote", pass_context=True)
    async def elect_vote(self, ctx):
        """Permet de voter en MP avec le bot."""
        author = ctx.message.author
        if self.sys["ELECT"] is True:
            if self.sys["ELECT_START"] is True:
                if author.id in self.sys["AUTORISE"]:
                    if author.id not in self.sys["VOTED"]:
                        retour = False
                        while retour == False:
                            em = discord.Embed()
                            msg = ""
                            for cand in self.elect:
                                num = self.elect[cand]["NUMERO"]
                                pseudo = self.elect[cand]["USER_NAME"]
                                supp = self.elect[cand]["SUPP_NAME"]
                                msg += "__#{}__ | **{}** / *{}*\n".format(num, pseudo, supp)
                            em.add_field(name="__Candidats et suppléants__", value=msg)
                            em.set_footer(text="Suivez les indications ci-dessous pour voter".format(ctx.prefix))
                            await self.bot.whisper(embed=em)
                            await asyncio.sleep(1)
                            em = discord.Embed()
                            em.add_field(name="Voter", value="Tapez le numéro d'un candidat pour en savoir plus.")
                            em.set_footer(text="Tapez 'blanc' pour voter Blanc")
                            menu = await self.bot.whisper(embed=em)
                            verif = False
                            while verif != True:
                                rep = await self.bot.wait_for_message(author=ctx.message.author, channel=menu.channel,
                                                                      timeout=30)
                                if rep == None:
                                    await self.bot.whisper("Bye :wave:")
                                    return
                                elif "&" in rep.content:
                                    await self.bot.whisper("Ne marquez que le numéro correspondant au candidat !")
                                elif rep.content.lower() == "blanc":
                                    terc = False
                                    while terc == False:
                                        await self.bot.whisper("Voulez-vous voter blanc ? (O/N)")
                                        rep = await self.bot.wait_for_message(author=ctx.message.author,
                                                                              channel=ctx.message.channel, timeout=20)
                                        hip = rep.content.lower()
                                        if hip == "o":
                                            await self.bot.whisper(
                                                "Vous votez Blanc !\nVotre vote à été pris en compte. Au revoir :wave:")
                                            self.sys["BLANC"] += 1
                                            self.sys["VOTED"].append(author.id)
                                            fileIO("data/extra/elect.json", "save", self.elect)
                                            fileIO("data/extra/sys.json", "save", self.sys)
                                            return
                                        elif hip == "n":
                                            await self.bot.say("Retour au menu...")
                                            await asyncio.sleep(1)
                                            terc = True
                                        elif rep == None:
                                            await self.bot.say("Retour au menu...")
                                            await asyncio.sleep(1)
                                            terc = True
                                        else:
                                            await self.bot.say("Retour au menu...")
                                            await asyncio.sleep(1)
                                            terc = True
                                elif int(rep.content) in [self.elect[cand]["NUMERO"] for cand in self.elect]:
                                    for c in self.elect:
                                        if self.elect[c]["NUMERO"] == int(rep.content):
                                            verif = True
                                            em = discord.Embed()
                                            em.title = "Candidature de **{}**".format(self.elect[c]["USER_NAME"])
                                            if self.elect[c]["AFFICHE"] != None:
                                                em.set_thumbnail(url=self.elect[c]["AFFICHE"])
                                            em.add_field(name="Suppléant", value=self.elect[c]["SUPP_NAME"])
                                            if self.elect[c]["MOTTO"] != None:
                                                em.add_field(name="Slogan", value="*" + self.elect[c]["MOTTO"] + "*")
                                            if self.elect[c]["PROG"] != None:
                                                em.add_field(name="Programme", value=self.elect[c]["PROG"])
                                            em.set_footer(
                                                text="Cliquez sur une réaction pour intéragir (Cliquez sur '?' pour plus d'aide)")
                                            an = await self.bot.whisper(embed=em)
                                            await self.bot.add_reaction(an, "✔")  # Voter pour lui
                                            await self.bot.add_reaction(an, "🔙")  # Retour à la liste
                                            await self.bot.add_reaction(an, "🔚")  # Annuler le vote
                                            await self.bot.add_reaction(an, "❓")  # Plus d'aide
                                            await asyncio.sleep(0.25)
                                            sec = False
                                            while sec != True:
                                                amp = await self.bot.wait_for_reaction(["✔", "❓", "🔙", "🔚"],
                                                                                       message=an, user=author)
                                                if amp.reaction.emoji == "✔":
                                                    await self.bot.whisper(
                                                        "Vous avez voté pour **{}** !\nVotre vote est pris en compte. Au revoir :wave:".format(
                                                            self.elect[c]["USER_NAME"]))
                                                    self.elect[c]["VOTES"] += 1
                                                    self.sys["VOTED"].append(author.id)
                                                    fileIO("data/extra/elect.json", "save", self.elect)
                                                    fileIO("data/extra/sys.json", "save", self.sys)
                                                    return
                                                elif amp.reaction.emoji == "🔙":
                                                    sec = True
                                                elif amp.reaction.emoji == "🔚":
                                                    await self.bot.whisper("Au revoir :wave:")
                                                    return
                                                elif amp.reaction.emoji == "❓":
                                                    aide = "__**AIDE**__\n"
                                                    aide += "✔ = Voter pour le candidat\n"
                                                    aide += "🔙 = Retour à la liste des candidats\n"
                                                    aide += "🔚 = Quitter l'interface sans voter\n"
                                                    aide += "❓ = Obtenir de l'aide"
                                                    await self.bot.whisper(aide)
                                                else:
                                                    await self.bot.whisper("Invalide...")
                                        else:
                                            pass
                                else:
                                    await self.bot.whisper("Invalide, essayez un autre numéro !")
                    else:
                        await self.bot.whisper("Vous avez déjà voté !")
                else:
                    await self.bot.whisper("Vous n'êtes pas autorisé à voter.")
            else:
                await self.bot.whisper(
                    "Les votes ne sont pas encore ouverts ! Vous recevrez un MP lorsque ce sera le cas.")
        else:
            await self.bot.whisper("Il ne semble pas y avoir d'élections en ce moment.")

            # WIKI =================================================================

    @commands.group(pass_context=True)
    async def wikiset(self, ctx):
        """Gestion du wiki de commandes."""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @wikiset.command(pass_context=True)
    async def add(self, ctx, commande, *desc):
        """Permet d'ajouter une aide au Wiki."""
        desc = " ".join(desc)
        if commande not in self.wiki:
            self.wiki[commande] = {"COMMANDE": commande, "DESCRIPTION": desc}
            fileIO("data/extra/wiki.json", "save", self.wiki)
            await self.bot.say("Aide pour *{}* ajoutée.".format(commande))
        else:
            await self.bot.say("Cette aide existe déjà.")

    @wikiset.command(pass_context=True)
    async def delete(self, ctx, commande):
        """Permet de retirer une aide du Wiki."""
        if commande in self.wiki:
            del self.wiki[commande]
            fileIO("data/extra/wiki.json", "save", self.wiki)
            await self.bot.say("Aide pour *{}* retirée.".format(commande))
        else:
            await self.bot.say("Cette aide n'existe pas.")

    @wikiset.command(pass_context=True)
    async def edit(self, ctx, commande, *desc):
        """Permet d'éditer une aide du Wiki."""
        desc = " ".join(desc)
        if commande in self.wiki:
            self.wiki[commande] = {"COMMANDE": commande, "DESCRIPTION": desc}
            fileIO("data/extra/wiki.json", "save", self.wiki)
            await self.bot.say("Aide pour *{}* éditée.".format(commande))
        else:
            await self.bot.say("Cette aide n'existe pas.")

    @commands.command(name="wiki", pass_context=True)
    async def wiki_search(self, ctx, inverse: bool, *rec):
        """Permet de chercher de l'aide pour une commande.

        La recherche est flexible, entrer une partie du mot donne accès à un menu."""
        reverse = inverse
        rec = " ".join(rec)
        if len(rec) >= 1:
            if reverse is False:
                msg = "**__Résultats pour {}__**\n".format(rec)
                if rec in self.wiki:
                    await self.bot.say("**{}** | *{}*".format(rec, self.wiki[rec]["DESCRIPTION"]))
                else:
                    for e in self.wiki:
                        if rec in e:
                            msg += "- **{}**\n".format(self.wiki[e]["COMMANDE"])
                    if msg != "**__Résultats pour {}__**\n".format(rec):
                        msg += "\n*Rentrez la commande précise pour en savoir plus*"
                        await self.bot.say(msg)
                        verif = False
                        while verif == False:
                            com = await self.bot.wait_for_message(author=ctx.message.author,
                                                                  channel=ctx.message.channel, timeout=30)
                            if com == None:
                                await self.bot.say("Temps de réponse trop long, annulation...")
                                return
                            elif com.content in self.wiki:
                                await self.bot.say(
                                    "**{}** | *{}*".format(com.content, self.wiki[com.content]["DESCRIPTION"]))
                                verif = True
                            else:
                                await self.bot.say("Invalide, réessayez")
                    else:
                        await self.bot.say("Essayez une recherche moins précise.")
            else:
                if len(rec) >= 3:
                    msg = "**__Résultats de votre recherche inversée__**\n"
                    for e in self.wiki:
                        if rec in self.wiki[e]["DESCRIPTION"].lower():
                            msg += "**{}** | *{}*\n".format(self.wiki[e]["COMMANDE"], self.wiki[e]["DESCRIPTION"])
                    await self.bot.whisper(msg)
                else:
                    await self.bot.say("Rentrez au moins 3 caractères pour lancer une recherche inversée.")
        else:
            await self.bot.say("Rentrez au moins un caractère")

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
        fileIO("data/extra/sys.json", "save", self.sys)
        await self.bot.say("Fait.")

    @gep.command(pass_context=True, no_pm=True, hidden=True)
    @checks.mod_or_permissions(ban_members=True)
    async def set(self, ctx, role: discord.Role):
        """Change le rôle de président enregistré."""
        channel = ctx.message.channel
        author = ctx.message.author
        if self.sys["GEP_ROLE"] is None:
            self.sys["GEP_ROLE"] = role.name
            fileIO("data/extra/sys.json", "save", self.sys)
            await self.bot.say("Rôle de président enregistré.")
        else:
            await self.bot.say(
                "Le rôle {} est déja renseigné. Voulez-vous l'enlever ? (O/N)".format(self.sys["GEP_ROLE"]))
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
        author = ctx.message.author
        if self.sys["GEP_ROLE"] != None:
            tag = str(self.sys["GEP_PTAG"])
            self.sys["GEP_PTAG"] += 1
            ntime = time.strftime("%d/%m/%Y %H:%M:%S", time.localtime())
            r = lambda: random.randint(0, 255)
            color = '0x%02X%02X%02X' % (r(), r(), r())
            base = await self.bot.whisper(
                "__**Proposer une idée**__\n**Entrez le titre que vous voulez donner à votre idée :**")
            channel = base.channel
            verif = False
            while verif != True:
                rep = await self.bot.wait_for_message(author=author, channel=channel)
                if len(rep.content) >= 5:
                    titre = rep.content
                    verif = True
                elif rep.content.lower() == "q":
                    await self.bot.whisper("Votre idée n'est pas conservée. Bye :wave:")
                    return
                else:
                    await self.bot.whisper("Invalide, réessayez. (Votre titre doit être d'au moins 5 caractères)")

            await self.bot.whisper(
                "**Entrez votre idée :**\n*(Tip: Pour mettre un espace sans valider votre message, utilisez MAJ + Entrer)*")
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
                    await self.bot.whisper(
                        "Merci pour votre contribution !\nVotre idée est enregistrée dans nos fichiers (Votre pseudo ne sera pas affiché).")
                    image = "http://i.imgur.com/iDZRdNk.png"
                    verif = True
                elif rep.content.lower() == "n":
                    name = str(author)
                    await self.bot.whisper(
                        "Merci pour votre contribution !\nVotre idée est enregistrée dans nos fichiers.")
                    image = author.avatar_url
                    verif = True
                elif rep.content.lower() == "q":
                    await self.bot.whisper("Votre idée n'est pas conservée. Bye :wave:")
                    return
                else:
                    await self.bot.whisper(
                        "Invalide, réessayez. ('O' pour OUI, 'N' pour NON, 'Q' pour Annuler et quitter)")

            self.sys["GEP_IDEES"][tag] = {"TAG": tag, "CHECK": False, "AUTHOR": name, "IMAGE": image, "TITRE": titre,
                                          "TEXTE": idee, "COLOR": color, "TIME": ntime}
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
                    rep = await self.bot.wait_for_message(author=author, channel=channel, timeout=60)
                    if rep == None:
                        await self.bot.whisper("Réponse trop longue, bye :wave:")
                        return
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
                rep = await self.bot.wait_for_message(author=author, channel=channel, timeout=60)
                if rep == None:
                    await self.bot.whisper("Réponse trop longue, bye :wave:")
                    return
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

                    # AFK DETECT ===========================================================

    async def trigger(self, message):
        if self.sys["AFK"] is True:
            author = message.author
            channel = message.channel
            if message.author.id in self.sys["AFK_LIST"]:
                self.sys["AFK_LIST"].remove(author.id)
                fileIO("data/extra/sys.json", "save", self.sys)
            elif message.content.lower() == "afk":
                if author.id not in self.sys["AFK_LIST"]:
                    self.sys["AFK_LIST"].append(author.id)
                    fileIO("data/extra/sys.json", "save", self.sys)
            elif message.mentions != []:
                for user in message.mentions:
                    if user.id in self.sys["AFK_LIST"]:
                        await self.bot.send_message(channel, "**{}** est AFK".format(user.name))
            else:
                pass

    async def spy(self, reaction, author):
        if "Staff" in [r.name for r in author.roles]:
            if reaction.emoji == "❔":
                user = reaction.message.author
                message = reaction.message
                roles = [x.name for x in user.roles if x.name != "@everyone"]
                if not roles: roles = ["None"]
                data = "```python\n"
                data += "Nom: {}\n".format(str(user))
                data += "ID: {}\n".format(user.id)
                passed = (message.timestamp - user.created_at).days
                data += "Crée: {} (Il y a {} jours)\n".format(user.created_at, passed)
                passed = (message.timestamp - user.joined_at).days
                data += "Rejoint le: {} (Il y a {} jours)\n".format(user.joined_at, passed)
                data += "Rôles: {}\n".format(", ".join(roles))
                data += "Avatar: {}\n".format(user.avatar_url)
                data += "```"
                await self.bot.send_message(author, data)

    @commands.command(pass_context=True)
    @checks.mod_or_permissions(ban_members=True)
    async def toggleafk(self, ctx):
        """Permet d'activer l'AFK."""
        if "AFK" not in self.sys:
            self.sys["AFK"] = False
            self.sys["AFK_LIST"] = []
        if self.sys["AFK"] is True:
            await self.bot.say("Désactivé.")
            self.sys["AFK"] = False
            self.sys["AFK_LIST"] = []
            fileIO("data/extra/sys.json", "save", self.sys)
        else:
            await self.bot.say("Activé.")
            self.sys["AFK"] = True
            fileIO("data/extra/sys.json", "save", self.sys)


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

    if not os.path.isfile("data/extra/wiki.json"):
        print("Création du fichier pour le Wiki...")
        fileIO("data/extra/wiki.json", "save", {})

    if not os.path.isfile("data/extra/elect.json"):
        print("Création du fichier d'Elections...")
        fileIO("data/extra/elect.json", "save", {})

    if not os.path.isfile("data/extra/goulag.json"):
        print("Création du fichier de prison...")
        fileIO("data/extra/goulag.json", "save", {})

    if not os.path.isfile("data/extra/mgdata.json"):
        print("Création du fichier pour les Mini-jeux...")
        fileIO("data/extra/mgdata.json", "save", {})

def setup(bot):
    check_folders()
    check_files()
    n = Extra(bot)
    bot.add_listener(n.trigger, "on_message")
    bot.add_listener(n.spy,'on_reaction_add')
    bot.add_cog(n)