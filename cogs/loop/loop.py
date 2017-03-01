import asyncio
import os
import random
from .utils import checks
from copy import deepcopy
import discord
from collections import namedtuple
from __main__ import send_cmd_help
from discord.ext import commands
from .utils.dataIO import fileIO, dataIO

#'Addon' Exclusive/ Pour Plume - Issoubot
# /!\ >> SI VOUS NE VOULEZ PAS DE SPOIL, OU SI VOUS NE VOULEZ PAS ÊTRE PENALISE POUR AVOIR TRICHE, NE LISEZ PAS LES LIGNES CI-DESSOUS. <<

# Types :
# - Normal (Texte en noir - Grande distribution)
# - Unique (Texte en bleu - Personnelle et Non-échangeable type Rôles)
# - Rare (Texte en rouge - Fait remarquable)
# - Collector (Texte en or - Event particulier)

dcart = [["oldfag","Pour avoir été un oldfag","http://image.noelshack.com/fichiers/2017/09/1488317998-carteoldfag.png","unique"],
         ["fortuné","Pour avoir été virtuellement le plus riche une fois dans sa vie","http://image.noelshack.com/fichiers/2017/09/1488318000-cartefortune.png","unique"],
         ["staff","Pour avoir été dans le staff","http://image.noelshack.com/fichiers/2017/09/1488317994-cartestaff.png","unique"],
         ["a voté","Pour avoir exercé son devoir de citoyen","http://image.noelshack.com/fichiers/2017/09/1488311074-cartevote.png","commune"],
         ["detective","Pour avoir découvert un Easter-egg !","http://image.noelshack.com/fichiers/2017/09/1488316832-cartedetective.png","collector"],
         ["chanceux","Pour avoir multiplié son offre par 5000 dans la Machine à sous", "http://image.noelshack.com/fichiers/2017/09/1488318404-cartechanceux.png","rare"],
         ["malsain","Pour avoir été sur le serveur original, tel un vrai malsain","http://image.noelshack.com/fichiers/2017/09/1488317991-cartemalsain.png","unique"]]

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

    def find_carte(self, carte): #Retrouve une carte à partir de son nom
        Carte = namedtuple('Carte', ['nom', 'condition', 'image_url', 'type'])
        for c in dcart:
            if c[0] == carte:
                return Carte(c[0], c[1], c[2], c[3])
        else:
            return False

    def pos_carte(self, user, carte): #Renvoie True si possédé, False si manquante chez l'utilisateur visé
        if user.id in self.acc:
            for c in self.acc[user.id]["SUCESS"]:
                if c == carte:
                    return True
            else:
                return False
        else:
            return False

    def add_carte(self, user, carte):
        """Permet d'ajouter une carte à un utilisateur."""
        if self.find_carte(carte) != False:
            carte = self.find_carte(carte)
            if user.id in self.acc:
                if not self.pos_carte(user, carte.nom):
                    self.acc[user.id]["SUCESS"].append(carte.nom)
                    self.save()
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False

    def del_carte(self, user, carte):
        """Permet de retirer une carte à un utilisateur."""
        if self.find_carte(carte) != False:
            carte = self.find_carte(carte)
            if user.id in self.acc:
                if self.pos_carte(user, carte.nom):
                    self.acc[user.id]["SUCESS"].remove(carte.nom)
                    self.save()
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False

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
        """Retrouver l'utilisateur qui possède un snip en particulier. (S'appuie sur le serveur - Précis)"""
        for id in self.acc:
            if self.acc[id]["SNIP"] == snip:
                user = server.get_member(self.acc[id]["ID"])
                return user
        else:
            return False

    def offlinesnip(self, snip):
        """Retrouver un utilisateur en offline (S'appuie sur les données enregistées - Moins précis)"""
        for id in self.acc:
            if self.acc[id]["SNIP"] == snip:
                return self.acc[id]["PSEUDO"]
        else:
            return False

    def gen_profil(self, user, complete=False):
        if complete is True:
            em = discord.Embed(title="{}".format(user.name), color=0x667399)
            em.set_author(name="[LOOP BETA]",icon_url="http://image.noelshack.com/fichiers/2017/09/1488319163-looplog.png")
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
            em.set_author(name="[LOOP BETA]", icon_url="http://image.noelshack.com/fichiers/2017/09/1488319163-looplog.png")
            em.set_thumbnail(url=user.avatar_url)
            em.set_footer(text="Cette personne ne vous autorise pas à voir l'intégralité de son profil.")
            return em

    # COMMANDES >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    @commands.group(pass_context=True)
    async def loop(self, ctx):
        """Commandes de Loop"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @loop.command(pass_context=True, hidden=True)
    async def forcesync(self, ctx):
        """Permet de synchroniser de force la distribution de cartes Uniques (Rôles)"""
        server = ctx.message.server
        for m in server.members:
            msg = self.carte_synchro(m)
            if msg != False:
                await self.bot.send_message(m, msg)
            else:
                pass
        else:
            await self.bot.say("**Synchronisation terminée**")

    @loop.command(pass_context=True, no_pm=True)
    @checks.mod_or_permissions(kick_members=True)
    async def attrib(self, ctx, user:discord.Member, carte: str = None):
        """Permet d'attribuer une carte à un utilisateur.

        Si aucune carte n'est spécifiée, renvoie une liste des cartes disponibles."""
        if carte == None:
            new_message = deepcopy(ctx.message)
            new_message.content = ctx.prefix + "loop cartes"
            await self.bot.process_commands(new_message)
            return
        else:
            carte = carte.lower()
            if user.id in self.acc:
                if self.find_carte(carte) != False:
                    if not self.pos_carte(user, carte):
                        carte = self.find_carte(carte)
                        self.add_carte(user, carte.nom)
                        await self.bot.send_message(user, "On vous a débloqué la carte **{}** ! [{}]".format(carte.nom.title(), carte.type.upper()))
                        await self.bot.say("Carte attribuée avec succès.")
                    else:
                        await self.bot.say("L'utilisateur possède déjà cette carte.")
                else:
                    await self.bot.say("Cette carte n'existe pas. Utilisez '{}loop cartes' pour avoir la liste des cartes disponibles.".format(ctx.prefix))
            else:
                await self.bot.say("L'utilisateur n'est pas inscrit sur Loop.")

    @loop.command(pass_context=True, no_pm=True)
    @checks.mod_or_permissions(kick_members=True)
    async def retire(self, ctx, user: discord.Member, carte: str = None):
        """Permet de retirer une carte à un utilisateur.

        Si aucune carte n'est spécifiée, renvoie une liste des cartes possédés par l'utilisateur."""
        if carte == None:
            msg = "__**Cartes possédées par {}**__\n".format(user.name)
            if user.id in self.acc:
                for c in self.acc[user.id]["SUCESS"]:
                    msg += "- **{}**\n".format(c.title())
                await self.bot.say(msg)
            await self.bot.say("L'utilisateur n'est pas inscrit sur Loop")
            return
        else:
            carte = carte.lower()
            if user.id in self.acc:
                if self.find_carte(carte) != False:
                    if self.pos_carte(user, carte):
                        carte = self.find_carte(carte)
                        self.del_carte(user, carte.nom)
                        await self.bot.send_message(user, "Votre carte **{}** [{}] vous a été retirée.".format(
                            carte.nom.title(), carte.type.upper()))
                        await self.bot.say("Carte retirée avec succès.")
                    else:
                        await self.bot.say("L'utilisateur ne possède pas cette carte.")
                else:
                    await self.bot.say(
                        "Cette carte n'existe pas. Utilisez '{}loop cartes' pour avoir la liste des cartes disponibles.".format(
                            ctx.prefix))
            else:
                await self.bot.say("L'utilisateur n'est pas inscrit sur Loop.")

    @loop.command(pass_context=True)
    async def cartes(self, ctx):
        """Renvoie une liste des cartes collectionnables."""
        em = discord.Embed(color=0x667399)
        msg = ""
        em.set_author(name="[LOOP BETA]", icon_url="http://image.noelshack.com/fichiers/2017/09/1488319163-looplog.png")
        for c in dcart:
            carte = self.find_carte(c[0])
            msg += "**{}** [*{}*] | *{}*\n".format(carte.nom.title(), carte.type.title(), carte.condition if carte.type != "collector" else "?")
        em.add_field(name="Cartes Loop", value=msg)
        em.set_footer(text="-- Cartes à collectionner Loop --")
        await self.bot.whisper(embed=em)

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
                    em.set_author(name="[LOOP BETA]",icon_url="http://image.noelshack.com/fichiers/2017/09/1488319163-looplog.png")
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
                        rep = await self.bot.wait_for_message(author=author, channel=menu.channel, timeout=45)
                        if rep == None:
                            return
                        onglet = rep.content.upper()
                        if onglet == "A":
                            verif1 = True
                            em = discord.Embed(color=0x667399)
                            em.set_author(name="[LOOP BETA]", icon_url="http://image.noelshack.com/fichiers/2017/09/1488319163-looplog.png")
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
                            em.set_author(name="[LOOP BETA]", icon_url="http://image.noelshack.com/fichiers/2017/09/1488319163-looplog.png")
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
                            em.set_author(name="[LOOP BETA]", icon_url="http://image.noelshack.com/fichiers/2017/09/1488319163-looplog.png")
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
                            em.set_author(name="[LOOP BETA]", icon_url="http://image.noelshack.com/fichiers/2017/09/1488319163-looplog.png")
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
                            em.set_author(name="[LOOP BETA]", icon_url="http://image.noelshack.com/fichiers/2017/09/1488319163-looplog.png")
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
                            em.set_author(name="[LOOP BETA]", icon_url="http://image.noelshack.com/fichiers/2017/09/1488319163-looplog.png")
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
                    em.set_author(name="[LOOP BETA]", icon_url="http://image.noelshack.com/fichiers/2017/09/1488319163-looplog.png")
                    msg = "**Champs**\n"
                    msg += "A = Sexe\n"
                    msg += "B = Date d'anniversaire\n"
                    msg += "C = Signature\n"
                    msg += "D = Profession\n"
                    msg += "E = Comptes\n"
                    msg += "F = Confidentialité\n"
                    msg += "----------------\n"
                    msg += "S = Supprimer mon profil\n"
                    msg += "T = Terminer\n"
                    msg += "Q = Quitter sans sauvegarder"
                    em.add_field(name="Menu", value=msg)
                    em.set_footer(text="Tapez la lettre correspondant à l'onglet à déployer.")
                    menu = await self.bot.whisper(embed=em)
                    verif1 = False
                    while verif1 != True:
                        rep = await self.bot.wait_for_message(author=author, channel=menu.channel, timeout=30)
                        if rep == None:
                            return
                        onglet = rep.content.upper()
                        if onglet == "A":
                            verif1 = True
                            em = discord.Embed(color=0x667399)
                            em.set_author(name="[LOOP BETA]", icon_url="http://image.noelshack.com/fichiers/2017/09/1488319163-looplog.png")
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
                            em.set_author(name="[LOOP BETA]", icon_url="http://image.noelshack.com/fichiers/2017/09/1488319163-looplog.png")
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
                            em.set_author(name="[LOOP BETA]", icon_url="http://image.noelshack.com/fichiers/2017/09/1488319163-looplog.png")
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
                            em.set_author(name="[LOOP BETA]", icon_url="http://image.noelshack.com/fichiers/2017/09/1488319163-looplog.png")
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
                            em.set_author(name="[LOOP BETA]", icon_url="http://image.noelshack.com/fichiers/2017/09/1488319163-looplog.png")
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
                            em.set_author(name="[LOOP BETA]", icon_url="http://image.noelshack.com/fichiers/2017/09/1488319163-looplog.png")
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
                        elif onglet == "S":
                            an = await self.bot.whisper("Voulez-vous réellement supprimer définitivement votre profil ? (O/N)")
                            rep = await self.bot.wait_for_message(author=author, channel=an.channel, timeout=15)
                            if rep == None:
                                await self.bot.whisper("Réponse trop longue. Action annulée.")
                                verif = True
                            elif rep.content.lower() == "o":
                                key = self.acc[author.id]["SNIP"]
                                for u in self.acc:
                                    if key in self.acc[u]["FAGS"]:
                                        self.acc[u]["FAGS"].remove(key)
                                del self.acc[author.id]
                                await self.bot.whisper("**Supprimé.**")
                                self.save()
                                return
                            elif rep.content.lower() == "n":
                                await self.bot.whisper("Action annulée.")
                                verif = True
                            else:
                                await self.bot.whisper("Invalide. Action annulée.")
                                verif = True
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
            if author.id not in self.acc:
                an = await self.bot.whisper("Un compte vide va être créé, vous pourrez le personnaliser lorsque vous serez sur un écran plus grand.\n*Voulez-vous vous inscrire ?* (O/N)")
                verif = False
                while verif == False:
                    rep = await self.bot.wait_for_message(author=author, channel=an.channel, timeout=10)
                    if rep == None:
                        await self.bot.whisper("Annulation...")
                        return
                    elif rep.content.lower() == "o":
                        verif = True
                        await self.bot.whisper("**Création d'un compte vide...**")
                        await asyncio.sleep(1)
                        self.new_acc(author)
                        self.acc[author.id]["SEXE"] = None
                        self.acc[author.id]["ANNIV"] = None
                        self.acc[author.id]["PROF"] = None
                        self.acc[author.id]["COMPTES"] = None
                        self.acc[author.id]["SIGN"] = None
                        self.acc[author.id]["PUBLIC"] = False
                        await self.bot.whisper(
                            "**Votre compte à été créé avec succès.**\nVous pouvez y accéder depuis {0}loop log\nVous pourrez le modifier avec {0}loop sign".format(
                                ctx.prefix))
                        self.save()
                        return
                    elif rep.content.lower() == "n":
                        await self.bot.whisper("Annulation...")
                        return
                    else:
                        await self.bot.whisper("Invalide, réessayez.")
            else:
                await self.bot.whisper("Vous avez déjà un compte. Vous pouvez y accéder depuis {}loop log".format(ctx.prefix))


    @loop.command(pass_context=True)
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
                                    em.set_author(name="[LOOP BETA]", icon_url="http://image.noelshack.com/fichiers/2017/09/1488319163-looplog.png")
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
                                em.set_author(name="[LOOP BETA", icon_url="http://image.noelshack.com/fichiers/2017/09/1488319163-looplog.png")
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
                    await self.bot.add_reaction(menu, "📃") #Voir mes cartes (succès)
                    await self.bot.add_reaction(menu, "📝") #Modifier profil
                    await self.bot.add_reaction(menu, "❓") #Aide
                    await asyncio.sleep(0.25)
                    verif = False
                    while verif != True:
                        rep = await self.bot.wait_for_reaction(["👥","📃","📝","❓"], message=menu, user=user, timeout=60)
                        if rep == None:
                            return
                        elif rep.reaction.emoji == "👥":
                            if self.acc[user.id]["FAGS"] != []:
                                em = discord.Embed(color=0x667399)
                                amis = ""
                                for fag in self.acc[user.id]["FAGS"]:
                                    ami = self.offlinesnip(fag)
                                    amis += "#*{}* | **{}**\n".format(fag, ami)
                                em.add_field(name= "Vos fags",value=amis)
                                await self.bot.whisper(embed=em)
                                await asyncio.sleep(1)
                                verif = True
                            else:
                                await self.bot.whisper("Vous n'avez pas d'amis.")
                                await asyncio.sleep(0.5)
                                verif = True
                        elif rep.reaction.emoji == "📃":
                            if self.acc[user.id]["SUCESS"] != []:
                                supp = False
                                while supp != True:
                                    em = discord.Embed(color=0x667399)
                                    sucs = ""
                                    n = 1
                                    liste = []
                                    for suc in self.acc[user.id]["SUCESS"]:
                                        liste.append([n,self.find_carte(suc)])
                                        n += 1
                                    for i in liste:
                                        sucs += "{} | **{}**\n".format(i[0],i[1].nom.title())
                                    em.add_field(name="Vos cartes", value=sucs)
                                    em.set_footer(text="Tapez un chiffre pour en savoir plus sur la carte ou patientez pour revenir au menu.")
                                    an = await self.bot.whisper(embed=em)
                                    verif2 = False
                                    while verif2 != True:
                                        rep = await self.bot.wait_for_message(author=user, channel=an.channel,timeout=10)
                                        if rep == None:
                                            verif2 = True
                                            supp = True
                                            verif = True
                                        elif rep.content.isdigit():
                                            for i in liste:
                                                if rep.content == str(i[0]):
                                                    em = discord.Embed(title=i[1].nom.title(), description=i[1].condition,color=0x667399)
                                                    em.set_image(url=i[1].image_url)
                                                    em.set_footer(text="-- Cartes à collectionner Loop --")
                                                    await self.bot.whisper(embed=em)
                                                    await asyncio.sleep(1.5)
                                                    verif2 = True
                                        else:
                                            await self.bot.whisper("Invalide, réessayez.")
                            else:
                                await self.bot.whisper("Vous n'avez pas de cartes.")
                        elif rep.reaction.emoji == "📝":
                            await self.bot.whisper("Chargement ...")
                            await asyncio.sleep(1)
                            new_message = deepcopy(ctx.message)
                            new_message.content = ctx.prefix + "loop sign"
                            await self.bot.process_commands(new_message)
                            return
                        elif rep.reaction.emoji == "❓":
                            aide = "**__AIDE__**\n"
                            aide += "👥 = Voir ses fags\n"
                            aide += "📃 = Voir ses cartes\n"
                            aide += "📝 = Modifier son profil\n"
                            aide += "❓ = Recevoir de l'aide\n"
                            await self.bot.whisper(aide)
                            await asyncio.sleep(1)
                            verif=True
                        else:
                            await self.bot.whisper("Invalide.")

        else:
            if author.id not in self.acc:
                await self.bot.whisper("Vous ne possédez pas de compte Loop. *Redirection vers inscription...*")
                await asyncio.sleep(1.5)
                new_message = deepcopy(ctx.message)
                new_message.content = ctx.prefix + "loop sign"
                await self.bot.process_commands(new_message)
                return
            else:
                await self.bot.whisper("L'utilisateur ne possède pas de compte Loop.")

    def carte_synchro(self, after):
        if after.id in self.acc:
            if "Staff" in [r.name for r in after.roles]:
                if not self.pos_carte(after, "staff"):
                    self.add_carte(after, "staff")
                    return "Vous avez débloqué la carte **Staff** ! [Unique]"
            if "Oldfag" in [r.name for r in after.roles]:
                if not self.pos_carte(after, "oldfag"):
                    self.add_carte(after, "oldfag")
                    return "Vous avez débloqué la carte **Oldfag** ! [Unique]"
            if "Malsain" in [r.name for r in after.roles]:
                if not self.pos_carte(after, "malsain"):
                    self.add_carte(after, "malsain")
                    return "Vous avez débloqué la carte **Malsain** ! [Unique]"
        else:
            return False

    async def cardupdate(self, before:discord.Member, after:discord.Member):
        if before.roles != after.roles:
            msg = self.carte_synchro(after)
            if msg != False:
                await self.bot.send_message(after, msg)
            else:
                pass
        else:
            pass

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
    bot.add_listener(n.cardupdate, "on_member_update")