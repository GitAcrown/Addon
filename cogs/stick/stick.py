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

class Stick:
    """Système de stickers personnalisés (Refonte)"""

    def __init__(self, bot):
        self.bot = bot
        self.img = dataIO.load_json("data/stick/img.json")
        self.import_old()

    def import_old(self):
        if "SUBMIT" not in self.img:
            self.img["SUBMIT"] = {}
            fileIO("data/stick/img.json", "save", self.img)
        if "CLAIM" not in self.img["CATEGORIE"]:
            self.img["CATEGORIE"] = {}
            self.img["CATEGORIE"]["CLAIM"] = {"NOM" : "CLAIM",
                                              "DESC" : "Images qui n'appartiennent à personne",
                                              "CREATEUR" : "Bot"}
            for stk in self.img["STICKER"]:
                self.img["STICKER"][stk]["CAT"] = "CLAIM"
            fileIO("data/stick/img.json", "save", self.img)
        else:
            pass

    @commands.group(pass_context=True)  # UTILISATEUR
    async def stk(self, ctx):
        """Commandes de gestion des stickers"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @stk.command(aliases=["s"], pass_context=True)
    async def submit(self, ctx, nom: str, url: str):
        """Permet de soumettre une idée de sticker au Staff

        L'URL doit être un lien direct provenant de Imgur ou Noelshack."""
        author = ctx.message.author
        server = ctx.message.server
        for stk in self.img["SUBMIT"]:
            if self.img["SUBMIT"][stk]["ID"] == author.id:
                await self.bot.say("Une seule demande à la fois par utilisateur.")
                return
        if "imgur" not in url.lower():
            if "noelshack" not in url.lower():
                await self.bot.say("Votre lien doit provenir de Imgur ou Noelshack\n*Ces sites n'imposent pas de cookies, ce qui permet un téléchargement propre de l'image*")
                return
        nom = nom.lower()
        if nom not in self.img["STICKER"]:
            if nom not in self.img["SUBMIT"]:
                self.img["SUBMIT"][nom] = {"AUTEUR" : author.name,
                                           "ID" : author.id,
                                           "NOM": nom,
                                           "URL": url}
                fileIO("data/stick/img.json", "save", self.img)
                modchan = server.get_channel("212749025760378883")
                em = discord.Embed(title="Proposition de {} - :{}:".format(author.name, nom))
                em.add_field(name="Options",
                             value="✔ = Sticker accepté\n"
                                   "✖ = Sticker refusé")
                em.set_image(url=url)
                em.set_footer(
                    text="Cliquez sur une réaction pour interagir (Valable 5 minutes)")
                act = await self.bot.send_message(modchan, embed=em)
                await self.bot.add_reaction(act, "✔")  # Accepte
                await self.bot.add_reaction(act, "✖")  # Refuse
                await asyncio.sleep(0.25)
                rep = await self.bot.wait_for_reaction(["✔","✖"], message=act ,timeout=300)
                if rep == None:
                    await self.bot.send_message(modchan, "**La demande de sticker de **{}** à expirée\n"
                                       "Vous pouvez la réactiver avec {}stk act {}".format(author.name, ctx.prefix, author.mention))
                    return
                elif rep.reaction.emoji == "✔":
                    await self.bot.send_message(modchan, "**La demande est acceptée**\n*Ajout automatique...*")
                    await self.bot.say("{} - **Votre demande à été acceptée.**".format(author.mention))
                    await asyncio.sleep(1)
                    del self.img["SUBMIT"][nom]
                    #PAVE

                    cat = ctx.message.author.name.upper()
                    if cat not in self.img["CATEGORIE"]:
                        self.img["CATEGORIE"][cat] = {"NOM": cat,
                                                       "DESC": "Inventaire de {}".format(ctx.message.author.name),
                                                       "CREATEUR": ctx.message.author.id}
                        fileIO("data/stick/img.json", "save", self.img)
                        await self.bot.whisper("Votre inventaire de stickers a été créé.")
                    if nom not in self.img["STICKER"]:
                        filename = url.split('/')[-1]
                        if filename in os.listdir("data/stick/imgstk"):
                            exten = filename.split(".")[1]
                            nomsup = random.randint(1, 99999)
                            filename = filename.split(".")[0] + str(nomsup) + "." + exten
                        try:
                            f = open(filename, 'wb')
                            f.write(request.urlopen(url).read())
                            f.close()
                            file = "data/stick/imgstk/" + filename
                            os.rename(filename, file)
                            aff = "URL"
                            self.img["STICKER"][nom] = {"NOM": nom,
                                                        "CHEMIN": file,
                                                        "URL": url,
                                                        "CAT": cat,
                                                        "AFF": aff,
                                                        "POP": 0}
                            fileIO("data/stick/img.json", "save", self.img)
                            await self.bot.say("Votre proposition à été ajoutée avec succès")
                            await self.bot.send_message(modchan, "Opération réussie")
                        except Exception as e:
                            print("Impossible de télécharger une image : {}".format(e))
                            await self.bot.say(
                                "Impossible de télécharger cette image.\nContactez un membre du staff pour qu'il rajoute manuellement le sticker.")
                elif rep.reaction.emoji == "✖":
                    await self.bot.send_message(modchan,"**Demande refusée**")
                    del self.img["SUBMIT"][nom]
                    fileIO("data/stick/img.json", "save", self.img)

            else:
                await self.bot.say("Ce sticker a déjà été proposé.")
        else:
            await self.bot.say("Ce sticker est déjà approuvé et disponible.")

    def findact(self, user):
        for stk in self.img["SUBMIT"]:
            if user.id == self.img["SUBMIT"][stk]["ID"]:
                return stk

    @stk.command(aliases=["c"], pass_context=True)
    @checks.mod_or_permissions(kick_members=True)
    async def act(self, ctx, user:discord.Member):
        """Permet de consulter la proposition de sticker d'un membre."""
        author = user
        server = ctx.message.server
        if self.findact(user):
            stk = self.findact(user)
            nom = self.img["SUBMIT"][stk]["NOM"]
            url = self.img["SUBMIT"][stk]["URL"]
            modchan = server.get_channel("212749025760378883")
            em = discord.Embed(title="Proposition de {} - :{}:".format(author.name, nom))
            em.add_field(name="Options",
                         value="✔ = Sticker accepté\n"
                               "✖ = Sticker refusé")
            em.set_image(url=url)
            em.set_footer(
                text="Cliquez sur une réaction pour interagir (Valable 5 minutes)")
            act = await self.bot.send_message(modchan, embed=em)
            await self.bot.add_reaction(act, "✔")  # Accepte
            await self.bot.add_reaction(act, "✖")  # Refuse
            await asyncio.sleep(0.25)
            rep = await self.bot.wait_for_reaction(["✔", "✖"], message=act, timeout=300)
            if rep == None:
                await self.bot.send_message(modchan, "**La demande de sticker de **{}** à expirée\n"
                                                     "Vous pouvez la réactiver avec {}stk act {}".format(
                    author.name, ctx.prefix, author.mention))
                return
            elif rep.reaction.emoji == "✔":
                await self.bot.send_message(modchan, "**La demande est acceptée**\n*Ajout automatique...*")
                await self.bot.send_message(user, "{} - **Votre demande à été acceptée.**".format(author.mention))
                await asyncio.sleep(1)
                del self.img["SUBMIT"][nom]
                # PAVE

                cat = ctx.message.author.name.upper()
                if cat not in self.img["CATEGORIE"]:
                    self.img["CATEGORIE"][cat] = {"NOM": cat,
                                                   "DESC": "Inventaire de {}".format(ctx.message.author.name),
                                                   "CREATEUR": ctx.message.author.id}
                    fileIO("data/stick/img.json", "save", self.img)
                    await self.bot.send_message(user, "Votre inventaire de stickers a été créé.")
                if nom not in self.img["STICKER"]:
                    filename = url.split('/')[-1]
                    if filename in os.listdir("data/stick/imgstk"):
                        exten = filename.split(".")[1]
                        nomsup = random.randint(1, 99999)
                        filename = filename.split(".")[0] + str(nomsup) + "." + exten
                    try:
                        f = open(filename, 'wb')
                        f.write(request.urlopen(url).read())
                        f.close()
                        file = "data/stick/imgstk/" + filename
                        os.rename(filename, file)
                        aff = "URL"
                        self.img["STICKER"][nom] = {"NOM": nom,
                                                    "CHEMIN": file,
                                                    "URL": url,
                                                    "CAT": cat,
                                                    "AFF": aff,
                                                    "POP": 0}
                        fileIO("data/stick/img.json", "save", self.img)
                        await self.bot.send_message(user, "Votre proposition à été ajoutée avec succès")
                        await self.bot.send_message(modchan, "Opération réussie")
                    except Exception as e:
                        print("Impossible de télécharger une image : {}".format(e))
                        await self.bot.send_message(user,
                            "Impossible de télécharger cette image.\nContactez un membre du staff pour qu'il rajoute manuellement le sticker.")
            elif rep.reaction.emoji == "✖":
                await self.bot.send_message(modchan, "**Demande refusée**")
                del self.img["SUBMIT"][nom]
                fileIO("data/stick/img.json", "save", self.img)
        else:
            await self.bot.whisper("Cet utilisateur n'a pas fait de propositions.")

    @stk.command(aliases=["a"], pass_context=True)
    @checks.mod_or_permissions(kick_members=True)
    async def add(self, ctx, nom, url, aff=None):
        """Ajout rapide d'un sticker (STAFF)

        Nom = Nom du sticker
        URL = Url de l'image
        Aff = Type d'affichage (URL,UPLOAD,INTEGRE)"""
        nom = nom.lower()
        cat = ctx.message.author.name.upper()
        if cat not in self.img["CATEGORIE"]:
            self.img["CATEGORIE"][cat] = {"NOM" : cat,
                                           "DESC" : "Inventaire de {}".format(ctx.message.author.name),
                                           "CREATEUR" : ctx.message.author.id}
            fileIO("data/stick/img.json", "save", self.img)
            await self.bot.whisper("Votre inventaire de stickers a été créé.")
        if nom not in self.img["STICKER"]:
            filename = url.split('/')[-1]
            if ".gif" in filename:
                await self.bot.say("*Assurez-vous que l'icone 'GIF' ne cache pas votre sticker.*")
                await asyncio.sleep(0.25)
            if filename in os.listdir("data/stick/imgstk"):
                exten = filename.split(".")[1]
                nomsup = random.randint(1, 99999)
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
                fileIO("data/stick/img.json", "save", self.img)
                await self.bot.say("Fichier **{}** enregistré localement.".format(filename))
            except Exception as e:
                print("Impossible de télécharger une image : {}".format(e))
                await self.bot.say(
                    "Impossible de télécharger cette image.\nChanger d'hebergeur va surement régler le problème.")
        else:
            await self.bot.say("Sticker déjà présent.")

    @stk.command(aliases = ["e"],pass_context=True)
    @checks.mod_or_permissions(kick_members=True)
    async def edit(self, ctx, nom, attrib, aff=None, url=None):
        """Permet d'éditer un sticker.

        Nom = Nom du sticker à éditer
        Attrib = Nom de la personne qui en est l'auteur
        Aff = Affichage (URL,UPLOAD,INTEGRE) - Par défaut conserve l'affichage
        URL = Url du sticker - Par défaut conserve l'URL"""
        cat = attrib.upper()
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
                pop = self.img["STICKER"][nom]["POP"]
                self.img["STICKER"][nom] = {"NOM": nom, "CHEMIN": file, "URL": url, "CAT":cat, "AFF":aff, "POP": pop}
                fileIO("data/stick/img.json","save",self.img)
                await self.bot.say("Sticker **{}** modifié avec succès.".format(nom))
            else:
                await self.bot.say("Ce sticker n'existe pas.")
        else:
            await self.bot.say("Cette catégorie n'existe pas. Je vais vous envoyer une liste de catégories disponibles.")
            msg = ""
            for categorie in self.img["CATEGORIE"]:
                msg += "**{}** | *{}*\n".format(self.img["CATEGORIE"][categorie]["NOM"], self.img["CATEGORIE"][categorie]["DESC"])
            else:
                await self.bot.whisper(msg)

    @stk.command(aliases=["d"], pass_context=True)
    @checks.mod_or_permissions(kick_members=True)
    async def delete(self, ctx, nom):
        """Permet d'effacer définitivement un sticker."""
        nom = nom.lower()
        if nom in self.img["STICKER"]:
            chemin = self.img["STICKER"][nom]["CHEMIN"]
            file = self.img["STICKER"][nom]["CHEMIN"].split('/')[-1]
            splitted = "/".join(chemin.split('/')[:-1]) + "/"
            if file in os.listdir(splitted):
                try:
                    os.remove(chemin)
                    await self.bot.say("Fichier lié supprimé.")
                except:
                    await self.bot.say("Le fichier est introuvable. Poursuite...")
                    await asyncio.sleep(1)
            else:
                await self.bot.say("Le fichier est introuvable. Poursuite...")
                await asyncio.sleep(1)
            del self.img["STICKER"][nom]
            await self.bot.say("Données du sticker supprimés.")
            fileIO("data/stick/img.json", "save", self.img)
        else:
            await self.bot.say("Ce sticker n'existe pas.")

    @stk.command(aliases=["i"], pass_context=True)
    async def inter(self, ctx):
        """Interface permettant la recherche et le listage des stickers."""
        author = ctx.message.author
        cat = author.name.upper() if author.name.upper() in self.img["CATEGORIE"] else None
        retour = False
        while retour is False:
            em = discord.Embed(title="Interface Stickers")
            em.add_field(name="Options",
                         value="📦 = Liste votre inventaire de stickers\n"
                               "👌 = Liste les stickers les plus populaires\n"
                               "📖 = Liste l'ensemble des stickers\n"
                               "🔬 = Recherche d'un sticker")
            em.set_footer(text="Cliquez sur une réaction ci-dessous pour continuer. (Patientez pour quitter l'interface)")
            menu = await self.bot.whisper(embed=em)
            await self.bot.add_reaction(menu, "📦")  # Inventaire
            await self.bot.add_reaction(menu, "👌")  # Populaires
            await self.bot.add_reaction(menu, "📖")  # Tous les stickers
            await self.bot.add_reaction(menu, "🔬")  # Recherche
            await asyncio.sleep(0.25)
            sec = False
            while sec != True:
                rep = await self.bot.wait_for_reaction(["📦", "👌", "📖", "🔬"], message=menu, user=author,timeout= 20)
                if rep == None:
                    await self.bot.whisper("*Annulation... (Timeout)*\nBye :wave:")
                    return
                elif rep.reaction.emoji == "📦":
                    if cat != None:
                        msg = "**INVENTAIRE**\n"
                        msg += "*Votre inventaire de stickers*\n\n"
                        a = 1
                        for stk in self.img["STICKER"]:
                            if self.img["STICKER"][stk]["CAT"] == cat:
                                msg += "**{}**\n".format(self.img["STICKER"][stk]["NOM"])
                                if len(msg) >= 1900 * a:
                                    msg += "!!"
                                    a += 1
                        else:
                            lmsg = msg.split("!!")
                            for msg in lmsg:
                                await self.bot.whisper(msg)
                            return
                    else:
                        await self.bot.whisper("Vous n'avez pas d'inventaire.")
                elif rep.reaction.emoji == "👌":
                    umsg = "**POPULAIRES**\n"
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
                        a = 1
                        while a < maxp:
                            nom = clsm[a]
                            nom = nom[0]
                            umsg += "- {} | {}\n".format(self.img["STICKER"][nom]["POP"],
                                                         self.img["STICKER"][nom]["NOM"])
                            a += 1
                    if umsg != "":
                        await self.bot.whisper(umsg)
                        return
                    else:
                        await self.bot.whisper("Aucun classement ne peut être établi")
                elif rep.reaction.emoji == "📖":
                    msg = "**STICKERS DISPONIBLES**\n"
                    msg += "*Liste de tous les stickers*\n\n"
                    a = 1
                    for stk in self.img["STICKER"]:
                        msg += "**{}**\n".format(self.img["STICKER"][stk]["NOM"])
                        if len(msg) >= 1950 * a:
                            msg += "!!"
                            a += 1
                    else:
                        lmsg = msg.split("!!")
                        for msg in lmsg:
                            await self.bot.whisper(msg)
                        return
                elif rep.reaction.emoji == "🔬":
                    await self.bot.whisper("**Entrez le terme recherché :**")
                    verif = False
                    while verif != True:
                        rep = await self.bot.wait_for_message(author=author, channel=menu.channel, timeout=30)
                        if rep == None:
                            await self.bot.whisper("Annulation... (Timeout)\nBye :wave:")
                            return
                        if rep.content.upper() in self.img["CATEGORIE"]:
                            cat = rep.content.upper()
                            msg = "**RECHERCHE - INVENTAIRE**\n"
                            msg += "*Stickers de l'inventaire de {}*\n\n".format(cat.title())
                            a = 1
                            for stk in self.img["STICKER"]:
                                if self.img["STICKER"][stk]["CAT"] == cat:
                                    msg += "**{}**\n".format(self.img["STICKER"][stk]["NOM"])
                                    if len(msg) >= 1900 * a:
                                        msg += "!!"
                                        a += 1
                            else:
                                lmsg = msg.split("!!")
                                for msg in lmsg:
                                    await self.bot.whisper(msg)
                                return
                        else:
                            for stk in self.img["STICKER"]:
                                msg = "**RECHERCHE - STICKER**\n"
                                msg += "*Résultats pour {}*\n\n".format(rep.content.lower())
                                a = 1
                                if rep.content.lower() in self.img["STICKER"][stk]["NOM"]:
                                    msg += "**{}** - *{}*\n".format(self.img["STICKER"][stk]["NOM"],self.img["STICKER"][stk]["CAT"])
                                    if len(msg) >= 1950 * a:
                                        msg += "!!"
                                        a += 1
                            else:
                                lmsg = msg.split("!!")
                                for msg in lmsg:
                                    await self.bot.whisper(msg)
                                return
                else:
                    await self.bot.whisper("Invalide")

# CHECK <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    async def check_msg(self, message):
        author = message.author
        channel = message.channel

        if ":" in message.content:
            output = re.compile(':(.*?):', re.DOTALL | re.IGNORECASE).findall(message.content)
            if output:
                for stk in output:
                    if stk in self.img["STICKER"]:
                        self.img["STICKER"][stk]["POP"] += 1

                        if self.img["STICKER"][stk]["AFF"] == "URL":  # URL
                            url = self.img["STICKER"][stk]["URL"]
                            if url != None:
                                await self.bot.send_message(channel, url)
                            else:
                                print("L'URL de l'image est indisponible.")

                        elif self.img["STICKER"][stk]["AFF"] == "UPLOAD":  # UPLOAD
                            chemin = self.img["STICKER"][stk]["CHEMIN"]
                            try:
                                await self.bot.send_file(channel, chemin)
                            except Exception as e:
                                print("Erreur, impossible d'upload l'image : {}".format(e))
                                if self.img["STICKER"][stk]["URL"] != None:
                                    await self.bot.send_message(channel, self.img["STICKER"][stk]["URL"])
                                else:
                                    print("Il n'y a pas d'URL lié au Sticker.")

                        elif self.img["STICKER"][stk]["AFF"] == "INTEGRE":  # INTEGRE
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
        fileIO("data/stick/img.json", "save", {"STICKER": {}, "CATEGORIE": {}})

def setup(bot):
    check_folders()
    check_files()
    n = Stick(bot)
    bot.add_listener(n.check_msg, "on_message")
    bot.add_cog(n)