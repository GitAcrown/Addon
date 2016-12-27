import discord
from discord.ext import commands
from .utils.dataIO import fileIO, dataIO
from .utils import checks
from __main__ import send_cmd_help, settings
from urllib import request
import re
import asyncio
import os
import random
import sys
import operator

#Exclusif

class Stick:
    """Permet de stocker des images en local."""

    def __init__(self, bot):
        self.bot = bot
        self.img = dataIO.load_json("data/stick/img.json")
        self.user = dataIO.load_json("data/stick/user.json")
        if "stock" in os.listdir("data/"):
            self.oldimg = dataIO.load_json("data/stock/img.json")

    @commands.group(pass_context=True) #UTILISATEUR
    async def utl(self, ctx):
        """Gestion utilisateur du module Stickers."""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @utl.command(pass_context=True, hidden=True)
    async def repare(self, ctx):
        """Permet de réparer son compte UTL."""
        author = ctx.message.author
        for stk in self.user[author.id]["FAVORIS"]:
            if "[P]" in stk:
                clean = stk[:-4]
                self.user[author.id]["FAVORIS"].remove(stk)
                self.user[author.id]["FAVORIS"].append(clean)
            else:
                pass
        else:
            await self.bot.say("Compte réparé.")

    @utl.command(pass_context=True)
    async def coll(self, ctx, nom):
        """Permet d'ajouter un sticker à sa collection."""
        nom = nom.lower()
        author = ctx.message.author
        if nom in self.img["STICKER"]:
            if author.id in self.user:
                self.user[author.id]["FAVORIS"].append(nom)
                fileIO("data/stick/user.json","save",self.user)
                await self.bot.say("**{}** ajouté à votre collection !".format(nom))
            else:
                await self.bot.say("Vous n'avez pas de suivi.")
        else:
            await self.bot.say("Ce sticker n'existe pas.")

    @utl.command(pass_context=True)
    async def uncoll(self, ctx, nom):
        """Permet d'enlever un sticker de sa collection."""
        nom = nom.lower()
        author = ctx.message.author
        if nom in self.img["STICKER"]:
            if author.id in self.user:
                self.user[author.id]["FAVORIS"].remove(nom)
                fileIO("data/stick/user.json","save",self.user)
                await self.bot.say("**{}** retiré de votre collection.".format(nom))
            else:
                await self.bot.say("Vous n'avez pas de suivi.")
        else:
            await self.bot.say("Ce sticker n'existe pas.")

    @utl.command(pass_context=True)
    async def color(self, ctx, hexa):
        """Permet de changer la couleur de la Box lorsque vous postez des INTEGRE

        Hexa est la couleur désirée en hexadécimal. Format : 0x<hex>"""
        author = ctx.message.author
        if author.id in self.user:
            if "0x" in hexa:  
                self.user[author.id]["COLOR"] = hexa
                fileIO("data/stick/user.json","save",self.user)
                await self.bot.say("La couleur a bien été integrée. Je vous envoie une démo.")
                em = discord.Embed(title="DEMO", description="Voici une démo de votre couleur {}".format(hexa), colour = int(hexa, 16))
                await self.bot.send_message(author, embed=em)
            else:
                await self.bot.say("Couleur invalide. Format : 0x<hex>")
        else:
            await self.bot.say("Vous n'avez pas de suivi")

    @utl.command(pass_context=True)
    async def top(self, ctx):
        """Affiche vos stickers les plus utilisés."""
        author = ctx.message.author
        if author.id in self.user:
            if len(self.user[author.id]["UTIL"]) >= 3:
                msg = "**TOP**\n"
                msg += "*Classés du plus au moins utilisé*\n\n"
                clsm = []
                for stk in self.user[ctx.message.author.id]["UTIL"]:
                    clsm.append([self.user[author.id]["UTIL"][stk]["NOM"],self.user[author.id]["UTIL"][stk]["NB"]])
                else:
                    maxs = len(clsm)
                    if maxs > 10:
                        maxs = 10
                    clsm = sorted(clsm, key=operator.itemgetter(1))
                    clsm.reverse()
                    a = 0
                    while a < maxs:
                        nom = clsm[a]
                        nom = nom[0]
                        msg += "- {} | {}\n".format(self.img["STICKER"][nom]["NOM"], self.img["STICKER"][nom]["AFF"].title())
                        a += 1
                await self.bot.whisper(msg)
            else:
                await self.bot.whisper("Vous êtes trop récent pour avoir un top.")
        else:
            await self.bot.say("Vous n'avez pas de suivi.")

    @commands.group(pass_context=True) #STICKERS
    async def stk(self, ctx):
        """Gestion des stickers."""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @stk.command(pass_context=True, hidden=True)
    @checks.mod_or_permissions(kick_members=True)
    async def imp(self, ctx):
        """Permet d'importer les stickers de l'ancien module."""
        if "NONE" not in self.img["CATEGORIE"]:
            self.img["CATEGORIE"]["NONE"] = {"NOM" : "NONE", "DESC" : "Sans catégories"}
        msg = "**__Importés:__**\n"
        for stk in self.oldimg["IMG"]:
            nom = self.oldimg["IMG"][stk]["NOM"]
            url = self.oldimg["IMG"][stk]["URL"]
            chemin = self.oldimg["IMG"][stk]["CHEMIN"]
            cat = self.oldimg["IMG"][stk]["CAT"]
            if cat == "INTEGRE":
                aff = "INTEGRE"
            elif cat == "URLONLY":
                aff = "URL"
            else:
                aff = "UPLOAD"
            if nom not in self.img["STICKER"]:
                self.img["STICKER"][nom] = {"NOM": nom,
                                            "CHEMIN": chemin,
                                            "URL": url,
                                            "CAT": "NONE",
                                            "AFF": aff,
                                            "POP": 0}
                fileIO("data/stick/img.json","save",self.img)
                msg += "Fichier **{}** importé.\n".format(nom)
            else:
                nom += "imp" + str(random.randint(1, 999))
                self.img["STICKER"][nom] = {"NOM": nom,
                                            "CHEMIN": chemin,
                                            "URL": url,
                                            "CAT": "NONE",
                                            "AFF": aff,
                                            "POP": 0}
                fileIO("data/stick/img.json","save",self.img)
                msg += "Fichier **{}** (Nom doublon) importé.\n".format(nom)
        else:
            await self.bot.say(msg)

    @stk.command(aliases = ["p"], pass_context=True)
    async def pop(self, ctx, top:int = 20):
        """Affiche les stickers les plus populaires sur le serveur."""
        if top < 10 or top > 30:
            await self.bot.say("Veuillez mettre un top supérieur à 10 et inférieur à 30.")
            return
        umsg = "\n" + "**POPULAIRES**\n"
        umsg += "*Les plus utilisés par la communauté*\n\n"
        clsm = []
        for stk in self.img["STICKER"]:
            clsm.append([self.img["STICKER"][stk]["NOM"], self.img["STICKER"][stk]["POP"]])
        else:
            maxp = len(clsm)
            if maxp > top:
                maxp = top
            clsm = sorted(clsm, key=operator.itemgetter(1))
            clsm.reverse()
            a = 0
            while a < maxp:
                nom = clsm[a]
                nom = nom[0]
                umsg += "- {} | {}\n".format(self.img["STICKER"][nom]["POP"], self.img["STICKER"][nom]["NOM"])
                a += 1
        await self.bot.say(umsg)

    @stk.command(aliases = ["a"],pass_context=True)
    @checks.mod_or_permissions(kick_members=True)
    async def add(self, ctx, nom, cat, url, aff=None):
        """Permet de créer un sticker pour le serveur.

        Si l'affichage n'est pas précisé, sera réglé sur UPLOAD"""
        nom = nom.lower()
        cat = cat.upper()
        author = ctx.message.author
        if "NONE" not in self.img["CATEGORIE"]:
            self.img["CATEGORIE"]["NONE"] = {"NOM" : "NONE", "DESC" : "Sans catégories"}
        if aff == None:
            aff = "UPLOAD"
        elif aff.upper() in ["URL","UPLOAD","INTEGRE"]:
            aff = aff.upper()
        else:
            await self.bot.say("Cet affichage n'existe pas (URL, UPLOAD ou INTEGRE).")
            return
        if cat in self.img["CATEGORIE"]:
            if nom not in self.img["STICKER"]:
                filename = url.split('/')[-1]
                if ".gif" in filename:
                    await self.bot.say("*Assurez-vous que l'icone 'GIF' ne cache pas votre sticker.*")
                if filename in os.listdir("data/stick/imgstk"):
                    exten = filename.split(".")[1]
                    nomsup = random.randint(1,99999)
                    filename = filename.split(".")[0] + str(nomsup) + "." + exten
                try:
                    f = open(filename, 'wb')
                    f.write(request.urlopen(url).read())
                    f.close()
                    file = "data/stick/imgstk/" + filename
                    os.rename(filename, file)
                    self.img["STICKER"][nom] = {"NOM": nom,
                                                "CHEMIN": file,
                                                "URL": url,
                                                "CAT": cat,
                                                "AFF": aff,
                                                "POP": 0}
                    fileIO("data/stick/img.json","save",self.img)
                    await self.bot.say("Fichier **{}** enregistré localement.".format(filename))
                except Exception as e:
                    print("Impossible de télécharger une image : {}".format(e))
                    await self.bot.say("Impossible de télécharger cette image.\nChanger d'hebergeur va surement régler le problème.")
            else:
                await self.bot.say("Sticker déjà chargé.")
        else:
            await self.bot.say("Cette catégorie n'existe pas. Je vais vous envoyer une liste de catégories disponibles.")
            msg = ""
            for categorie in self.img["CATEGORIE"]:
                msg += "**{}** | *{}*\n".format(self.img["CATEGORIE"][categorie]["NOM"], self.img["CATEGORIE"][categorie]["DESC"])
            else:
                await self.bot.whisper(msg)

    @stk.command(aliases = ["e"],pass_context=True)
    @checks.mod_or_permissions(kick_members=True)
    async def edit(self, ctx, nom, cat, aff=None, url=None):
        """Permet de changer des données liées à un sticker.

        Si aucun affichage n'est spécifié, l'affichage sera conservé tel quel."""
        cat = cat.upper()
        nom = nom.lower()
        if cat in self.img["CATEGORIE"]:
            if nom in self.img["STICKER"]:
                if aff == None:
                    aff = self.img["STICKER"][nom]["AFF"]
                    await self.bot.say("*Affichage conservé.*")
                elif aff.upper() in ["URL","UPLOAD","INTEGRE"]:
                    aff = aff.upper()
                else:
                    await self.bot.say("Cet affichage n'existe pas (URL, UPLOAD ou INTEGRE).")
                    return
                if url == None:
                    url = self.img["STICKER"][nom]["URL"]
                    await self.bot.say("*URL conservée.*")
                file = self.img["STICKER"][nom]["CHEMIN"]
                self.img["STICKER"][nom] = {"NOM": nom, "CHEMIN":file, "URL": url, "CAT":cat, "AFF":aff, "POP": 0}
                fileIO("data/stick/img.json","save",self.img)
                await self.bot.say("Données de **{}** modifiés.".format(nom))
            else:
                await self.bot.say("Ce sticker n'existe pas.")
        else:
            await self.bot.say("Cette catégorie n'existe pas. Je vais vous envoyer une liste de catégories disponibles.")
            msg = ""
            for categorie in self.img["CATEGORIE"]:
                msg += "**{}** | *{}*\n".format(self.img["CATEGORIE"][categorie]["NOM"], self.img["CATEGORIE"][categorie]["DESC"])
            else:
                await self.bot.whisper(msg)

    @stk.command(aliases = ["d"],pass_context=True)
    @checks.mod_or_permissions(kick_members=True)
    async def delete(self, ctx, nom):
        """Permet d'effacer définitivement un sticker."""
        nom = nom.lower()
        if nom in self.img["STICKER"]:
            chemin = self.img["STICKER"][nom]["CHEMIN"]
            file =self.img["STICKER"][nom]["CHEMIN"].split('/')[-1]
            splitted = "/".join(chemin.split('/')[:-1]) + "/"
            if file in os.listdir(splitted):
                os.remove(chemin)
                await self.bot.say("Fichier lié supprimé.")
            del self.img["STICKER"][nom]
            await self.bot.say("Données du sticker supprimés.")
            fileIO("data/stick/img.json","save",self.img)
        else:
            await self.bot.say("Ce sticker n'existe pas.")

    @stk.command(aliases = ["l"],pass_context=True)
    async def list(self, ctx, cat = None):
        """Affiche une liste des stickers disponibles.

        Si aucune catégorie n'est précisée, donne tout les stickers disponibles.
        Pour avoir les favoris serveur, précisez 'fav'."""
        umsg = ""
        author = ctx.message.author
        if cat == None:
            msg = "__**Stickers disponibles:**__\n"
            if "NONE" not in self.img["CATEGORIE"]:
                self.img["CATEGORIE"]["NONE"] = {"NOM" : "NONE", "DESC" : "Sans catégories"}
            for cat in self.img["CATEGORIE"]:
                msg += "\n" + "**{}**\n".format(self.img["CATEGORIE"][cat]["NOM"])
                msg += "*{}*\n\n".format(self.img["CATEGORIE"][cat]["DESC"])
                a = 10
                for stk in self.img["STICKER"]:
                    if self.img["STICKER"][stk]["CAT"] == cat:
                        msg += "- {} | {}\n".format(self.img["STICKER"][stk]["NOM"], self.img["STICKER"][stk]["AFF"].title())
                        if len(msg) > a * 195:
                            msg += "!!"
                            a += 10
                    else:
                        pass
            else:
                if ctx.message.author.id in self.user:
                    if len(self.user[author.id]["UTIL"]) >= 3:
                        umsg += "\n" + "**VOS FAVORIS**\n"
                        umsg += "*Vos stickers les plus utilisés*\n\n"
                        clsm = []
                        for stk in self.user[ctx.message.author.id]["UTIL"]:
                            clsm.append([self.user[author.id]["UTIL"][stk]["NOM"],self.user[author.id]["UTIL"][stk]["NB"]])
                        else:
                            maxs = len(clsm)
                            if maxs > 10:
                                maxs = 10
                            clsm = sorted(clsm, key=operator.itemgetter(1))
                            clsm.reverse()
                            a = 0
                            while a < maxs:
                                nom = clsm[a]
                                nom = nom[0]
                                umsg += "- {}".format(self.img["STICKER"][nom]["NOM"])
                                a += 1

                        umsg += "\n" + "**VOTRE COLLECTION**\n"
                        umsg += "*Votre collection personnelle*\n\n"
                        for stk in self.user[author.id]["FAVORIS"]:
                            umsg += "- {}\n".format(self.img["STICKER"][stk]["NOM"])
                        
                        umsg += "\n" + "**POPULAIRES**\n"
                        umsg += "*Les plus utilisés par la communauté*\n\n"
                        clsm = []
                        for stk in self.img["STICKER"]:
                            clsm.append([self.img["STICKER"][stk]["NOM"], self.img["STICKER"][stk]["POP"]])
                        else:
                            maxp = len(clsm)
                            if maxp > 10:
                                maxp = 10
                            clsm = sorted(clsm, key=operator.itemgetter(1))
                            clsm.reverse()
                            a = 0
                            while a < maxp:
                                nom = clsm[a]
                                nom = nom[0]
                                umsg += "- {} | {}\n".format(self.img["STICKER"][nom]["POP"], self.img["STICKER"][nom]["NOM"])
                                a += 1
            lmsg = msg.split("!!")
            for e in lmsg:
                await self.bot.whisper(e)
            if umsg != "":
                await self.bot.whisper(umsg)
        elif cat == "fav":
            if ctx.message.author.id in self.user:
                if len(self.user[author.id]["UTIL"]) >= 3:
                    umsg += "\n" + "**VOS FAVORIS**\n"
                    umsg += "*Vos stickers les plus utilisés*\n\n"
                    clsm = []
                    for stk in self.user[ctx.message.author.id]["UTIL"]:
                        clsm.append([self.user[author.id]["UTIL"][stk]["NOM"],self.user[author.id]["UTIL"][stk]["NB"]])
                    else:
                        maxs = len(clsm)
                        if maxs > 10:
                            maxs = 10
                        clsm = sorted(clsm, key=operator.itemgetter(1))
                        clsm.reverse()
                        a = 0
                        while a < maxs:
                            nom = clsm[a]
                            nom = nom[0]
                            umsg += "- {} | {}\n".format(self.img["STICKER"][nom]["NOM"], self.img["STICKER"][nom]["AFF"].title())
                            a += 1

                    umsg += "\n" + "**VOTRE COLLECTION**\n"
                    umsg += "*Votre collection personnelle*\n\n"
                    for stk in self.user[author.id]["FAVORIS"]:
                        umsg += "- {} | {}\n".format(self.img["STICKER"][stk]["NOM"], self.img["STICKER"][stk]["AFF"].title())
                    
                    umsg += "\n" + "**POPULAIRES**\n"
                    umsg += "*Les plus utilisés par la communauté*\n\n"
                    clsm = []
                    for stk in self.img["STICKER"]:
                        clsm.append([self.img["STICKER"][stk]["NOM"], self.img["STICKER"][stk]["POP"]])
                    else:
                        maxp = len(clsm)
                        if maxp > 10:
                            maxp = 10
                        clsm = sorted(clsm, key=operator.itemgetter(1))
                        clsm.reverse()
                        a = 0
                        while a < maxp:
                            nom = clsm[a]
                            nom = nom[0]
                            umsg += "- {} | {}\n".format(self.img["STICKER"][nom]["NOM"], self.img["STICKER"][nom]["AFF"].title())
                            a += 1
                    await self.bot.whisper(umsg)
                else:
                    await self.bot.whisper("Vous êtes trop récent pour avoir un suivi.")
            else:
                await self.bot.whisper("Vous n'avez pas de suivi.")
        else:
            cat = cat.upper()
            if "NONE" not in self.img["CATEGORIE"]:
                self.img["CATEGORIE"]["NONE"] = {"NOM" : "NONE", "DESC" : "Sans catégories"}
            msg = "__**Stickers dans la catégorie : {}**__\n".format(cat)
            for stk in self.img["STICKER"]:
                if self.img["STICKER"][stk]["CAT"] == cat:
                    msg += "- {}\n".format(self.img["STICKER"][stk]["NOM"])
                    a = 10
                    if len(msg) > a * 195:
                        msg += "!!"
                        a += 10
                else:
                    pass
            else:
                if "!!" in msg:
                    msgl = msg.split("!!")
                    for l in msgl:
                        await self.bot.whisper(l)
                else:
                    await self.bot.whisper(msg)

    @stk.command(aliases = ["s"], pass_context=True)
    async def search(self, ctx, arg:str):
        """Permet de rechercher un sticker."""
        arg = arg.lower()
        msg = "**__Résultats pour : {}__**\n".format(arg)
        for stk in self.img["STICKER"]:
            if arg in stk:
                msg += "**{}** | *{}*\n".format(self.img["STICKER"][stk]["NOM"], self.img["STICKER"][stk]["CAT"])
        else:
            await self.bot.whisper(msg)

    @commands.group(pass_context=True) #CATEGORIE
    @checks.mod_or_permissions(kick_members=True)
    async def cat(self, ctx):
        """Gestion des catégories."""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @cat.command(pass_context=True)
    async def crt(self, ctx, nom, *descr):
        """Ajoute une catégorie au module."""
        nom = nom.upper()
        descr = " ".join(descr)
        if descr != "":
            if nom not in self.img["CATEGORIE"]:
                self.img["CATEGORIE"][nom] = {"NOM" : nom, "DESC" : descr}
                fileIO("data/stick/img.json", "save", self.img)
                await self.bot.say("Votre catégorie **{}** à été crée.".format(nom.upper()))
            else:
                await self.bot.say("Cette catégorie existe déjà.")
        else:
            await self.bot.say("Vous devez ajouter une description à votre catégorie.")

    @cat.command(pass_context=True)
    async def rem(self, ctx, nom):
        """Supprime une catégorie existante et déplace les images dans 'NONE'"""
        nom = nom.upper()
        if nom in self.img["CATEGORIE"] or nom == "NONE":
            if "NONE" not in self.img["CATEGORIE"]:
                self.img["CATEGORIE"]["NONE"] = {"NOM" : "NONE", "DESC" : "Sans catégories"}
            for sticker in self.img["STICKER"]:
                if self.img["STICKER"][sticker]["CAT"] == nom:
                    self.img["STICKER"][sticker]["CAT"] = "NONE"
            del self.img["STICKER"][nom]
            fileIO("data/stick/img.json", "save", self.img)
            await self.bot.say("**Votre catégorie {} à été retirée.**\n *Les images ayant cette catégorie sont déplacés dans 'AUTRES'.*".format(nom.title()))
        else:
            await self.bot.say("Cette catégorie n'existe pas ou ne peut pas être supprimée.")

    # MSG CHECK ========================

    async def check_msg(self, message):
        author = message.author
        channel = message.channel
        if ":" in message.content:
            output = re.compile(':(.*?):', re.DOTALL |  re.IGNORECASE).findall(message.content)
            if output:
                for stk in output:
                    if stk in self.img["STICKER"]:
                        self.img["STICKER"][stk]["POP"] += 1
                        if author.id in self.user:
                            if stk in self.user[author.id]["UTIL"]:
                                self.user[author.id]["UTIL"][stk]["NB"] += 1
                            else:
                                self.user[author.id]["UTIL"][stk] = {"NOM": stk, "NB" : 0}
                                fileIO("data/stick/user.json","save",self.user)
                        else:
                            self.user[author.id] = {"FAVORIS" : [],
                                                    "COLOR" : "0x607d8b",
                                                    "UTIL" : {}}
                            fileIO("data/stick/user.json","save",self.user)
                                
                        if self.img["STICKER"][stk]["AFF"] == "URL": #URL
                            url = self.img["STICKER"][stk]["URL"]
                            if url != None:
                                await self.bot.send_message(channel, url)
                            else:
                                print("L'URL de l'image est indisponible.")

                        elif self.img["STICKER"][stk]["AFF"] == "UPLOAD": #UPLOAD
                            chemin = self.img["STICKER"][stk]["CHEMIN"]
                            try:
                                await self.bot.send_file(channel, chemin)
                            except Exception as e:
                                print("Erreur, impossible d'upload l'image : {}".format(e))
                                if self.img["STICKER"][stk]["URL"] != None:
                                    await self.bot.send_message(channel, self.img["STICKER"][stk]["URL"])
                                else:
                                    print("Il n'y a pas d'URL lié au Sticker.")

                        elif self.img["STICKER"][stk]["AFF"] == "INTEGRE": #INTEGRE
                            url = self.img["STICKER"][stk]["URL"]
                            if url != None:
                                couleur = self.user[author.id]["COLOR"]
                                couleur = int(couleur, 16)
                                em = discord.Embed(colour=couleur)
                                em.set_image(url=url)
                                await self.bot.send_message(channel, embed=em)
                            else:
                                print("Impossible d'afficher ce sticker.")
                        else:
                            url = self.img["STICKER"][stk]["URL"]
                            if url != None:
                                await self.bot.send_message(channel, url)
                            else:
                                print("L'URL de l'image est indisponible (DEFAUT).")
                    else:
                        pass
                else:
                    pass
            else:
                pass
        else:
            pass

def check_folders():
    if not os.path.exists("data/stick"):
        print("Creation du fichier Sticker...")
        os.makedirs("data/stick")

    if not os.path.exists("data/stick/imgstk"):
        print("Creation du fichier de Stockage d'images...")
        os.makedirs("data/stick/imgstk")


def check_files():
    
    if not os.path.isfile("data/stick/img.json"):
        print("Creation du fichier de Stick img.json...")
        fileIO("data/stick/img.json", "save", {"STICKER" : {}, "CATEGORIE" : {}})

    if not os.path.isfile("data/stick/user.json"):
        print("Creation du fichier de Stick user.json...")
        fileIO("data/stick/user.json", "save", {})

def setup(bot):
    check_folders()
    check_files()
    n = Stick(bot)
    bot.add_listener(n.check_msg, "on_message")
    bot.add_cog(n)
            
