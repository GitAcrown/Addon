import discord
from discord.ext import commands
from .utils.dataIO import fileIO, dataIO
from .utils import checks
from __main__ import send_cmd_help, settings
from urllib import request
import re
import asyncio
import os
import time
import random
import sys
import operator

default = {}

class Charm:
    """Gère les Stickers et d'autres fonctions liés aux salons textuels."""
    def __init__(self, bot):
        self.bot = bot
        self.stk = dataIO.load_json("data/charm/stk.json")
        self.sys = dataIO.load_json("data/charm/sys.json")
        self.old = dataIO.load_json("data/stick/img.json")
        ### Après avoir importé les anciens stickers importants:
        #TODO Retirer self.old
        #TODO Effacer l'ensemble de l'ancien dossier de sticker

    def check(self, reaction, user):
        if user.server_permissions.manage_messages is True:
            return True
        else:
            return False

    def old_stick(self, nom):
        if nom in self.old["STICKER"]:
            return True
        else:
            return False

# TRIGGERS >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><

    @commands.group(name="wel", pass_context=True, no_pm=True)
    @checks.mod_or_permissions(kick_members=True)
    async def charm_wel(self, ctx):
        """Gestion Welcome"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @charm_wel.command(pass_context=True)
    async def message(self, ctx, *message):
        """Permet de définir un message à envoyer à un membre venant d'arriver sur le serveur."""
        message = " ".join(message)
        self.sys["WELCOME_MSG"] = message
        fileIO("data/charm/sys.json", "save", self.sys)
        await self.bot.say("Message réglé. Vous allez recevoir un aperçu.")
        await self.bot.whisper("Voici un aperçu de ce que devrait voir un utilisateur arrivant sur le serveur:\n\n{}".format(message))

    @charm_wel.command(pass_context=True)
    async def channel(self, ctx, channel: discord.Channel):
        """Permet de définir le channel où sera affiché les messages d'arrivées et de départ."""
        self.sys["NOTIF_CHANNEL"] = channel.id
        fileIO("data/charm/sys.json", "save", self.sys)
        await self.bot.say("Les notifications seront désormais affichées sur *{}*".format(channel.name))

# STICKERS >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><

    @commands.command(pass_context=True, no_pm=True, hidden=True)
    async def egotest(self, ctx):
        """Test la connexion entre Charm et EGO"""
        try:
            ego = self.bot.get_cog('Ego').ego
            card = ego.log(ctx.message.author)
            await self.bot.say(str(card.born))
        except:
            await self.bot.say("Ego n'est pas connecté.")

    @commands.group(name = "stk", pass_context=True)
    async def charm_stk(self, ctx):
        """Gestion Stickers"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    #TODO Fonction recherche avancée

    @charm_stk.command(name="import", pass_context=True)
    async def import_sticker(self, ctx, nom, nomimport = None):
        """Permet d'importer un ancien sticker et de le réencoder dans le nouveau format.
        
        Vous pouvez lui donner un nouveau nom en précisant NomImport"""
        if nom in self.old["STICKER"]:
            if nomimport != None:
                if nomimport in self.stk["STICKERS"]:
                    await self.bot.say("Ce nouveau nom existe déjà dans ma base de données. Donnez-lui en un autre.")
                    return
            else:
                nomimport = nom
                if nom in self.stk["STICKERS"]:
                    await self.bot.say("Ce nouveau nom existe déjà dans ma base de données. Donnez-lui en un autre à l'aide du paramètre NomImport.")
                    return
            chemin = self.old["STICKER"][nom]["CHEMIN"]
            filename = chemin.split('/')[-1]
            url = self.old["STICKER"][nom]["URL"]
            aff = self.old["STICKER"][nom]["AFF"]
            try:
                file = "data/charm/stkimg/" + filename
                os.rename(chemin, file)
                self.stk["STICKERS"][nom] = {"NOM": nomimport,
                                             "URL": url,
                                             "CHEMIN": file,
                                             "FORMAT": aff}
                fileIO("data/charm/stk.json", "save", self.stk)
                await self.bot.say("Image importée avec succès !")
            except:
                await self.bot.say("Je ne peux pas importer cette image, elle n'est plus disponible (Sticker de 1ere gen.) ou ses données sont corrompues.\nVous pouvez la réajouter manuellement avec &stk submit.\n*Voici l'URL fournie lors de sa première création :* {}".format(url))
                return
        else:
            await self.bot.say("Ce nom n'existe pas dans mes anciens fichiers de sticker. Désolé !")

    @charm_stk.command(aliases=["d"], pass_context=True)
    @checks.mod_or_permissions(kick_members=True)
    async def delete(self, ctx, nom):
        """Supprime définitivement un sticker."""
        nom = nom.lower()
        if nom in self.stk["STICKERS"]:
            chemin = self.stk["STICKERS"][nom]["CHEMIN"]
            file = self.stk["STICKERS"][nom]["CHEMIN"].split('/')[-1]
            splitted = "/".join(chemin.split('/')[:-1]) + "/"
            try:
                if file in os.listdir(splitted):
                    try:
                        os.remove(chemin)
                        await self.bot.say("Image supprimée.")
                    except:
                        await self.bot.say("L'image est introuvable dans le stock classique. Recherche dans les dossiers proches...")
                        # Poursuite
                        await asyncio.sleep(0.5)
                else:
                    await self.bot.say("L'image est introuvable. Je vais simplement effacer les données liées...")
                    #Poursuite
                    await asyncio.sleep(0.5)
            except:
                await self.bot.say("Les données liées à l'image semblent corrompues. Je vais tenter de forcer sa suppression...")
                await asyncio.sleep(1.5)
            del self.stk["STICKERS"][nom]
            await self.bot.say("Données supprimées avec succès.")
            fileIO("data/charm/stk.json", "save", self.stk)
        else:
            await self.bot.say("Ce sticker n'existe pas.")

    @charm_stk.command(aliases=["e"], pass_context=True)
    async def edit(self, ctx, nom, aff=None, url=None):
        """Permet d'éditer un sticker.

        Nom = Nom du sticker à éditer
        Url = Url liée à l'image
        Aff = Affichage (INTEGRE, URL ou UPLOAD)"""
        nom = nom.lower()
        if nom in self.stk["STICKERS"]:
            if aff == None or "":
                aff = self.stk["STICKERS"][nom]["FORMAT"]
                await self.bot.say("*Format d'affichage conservé.*")
            elif aff.upper() in ["URL", "UPLOAD", "INTEGRE"]:
                aff = aff.upper()
            else:
                await self.bot.say("Cet affichage n'existe pas (URL, UPLOAD ou INTEGRE).")
                return
            if url == None or "":
                url = self.stk["STICKERS"][nom]["URL"]
                await self.bot.say("*URL conservée.*")
            file = self.stk["STICKERS"][nom]["CHEMIN"]
            self.stk["STICKERS"][nom] = {"NOM": nom,
                                         "URL": url,
                                         "CHEMIN": file,
                                         "FORMAT": aff}
            fileIO("data/charm/stk.json", "save", self.stk)
            await self.bot.say("Sticker **{}** modifié avec succès.".format(nom))
        else:
            await self.bot.say("Ce sticker n'existe pas.")

    @charm_stk.command(aliases=["s"], pass_context=True)
    async def submit(self, ctx, nom: str, url: str, format: str = "UPLOAD"):
        """Propose l'ajout d'un sticker.
        == Paramètres ==
        Nom - Le nom de votre sticker ('custom' si personnel)
        Url - Url du sticker (Noelshack, Imgur ou Giphy de préférence)
        Format (Optionnel) - Format d'affichage (URL, INTEGRE ou UPLOAD)
        
        Les membres du Staff peuvent directement appliquer un sticker."""
        nom = nom.lower()
        format = format.upper()
        message = ctx.message
        author = message.author
        server = message.server
        channel = message.channel
        if format not in ["URL", "UPLOAD", "INTEGRE"]:
            await self.bot.say("Les formats disponibles sont 'URL', 'UPLOAD' ou 'INTEGRE'.")
            return
        if "imgur" not in url.lower():
            if "noelshack" not in url.lower():
                if "giphy" not in url.lower():
                    await self.bot.say("Votre lien doit provenir de Imgur, Giphy ou Noelshack\n*Ces sites n'imposent pas de cookies, ce qui permet un téléchargement correct de l'image*")
                    return

        if not author.id in self.stk["USERS"]:
            self.stk["USERS"][author.id] = {"ID": author.id,
                                            "CUSTOM_URL": None,
                                            "CUSTOM_FORMAT": None,
                                            "COLLECTION": []}
            fileIO("data/charm/stk.json", "save", self.stk)

        if nom == "custom":
            if format == "INTEGRE" or "URL":
                self.stk["USERS"][author.id]["CUSTOM_URL"] = url
                self.stk["USERS"][author.id]["CUSTOM_FORMAT"] = format
                fileIO("data/charm/stk.json", "save", self.stk)
                await self.bot.say("Votre sticker custom à été modifié. Il sera affiché en format {}.".format(format))
            else:
                await self.bot.say("Le format de votre sticker custom ne peut pas être autre que 'Integre' ou 'Url'.")
            return

        if nom not in self.stk["STICKERS"]:
            filename = url.split('/')[-1]
            if author.server_permissions.manage_messages is False:
                try:
                    await self.bot.delete_message(message)
                except:
                    pass
                em = discord.Embed(title="Proposition de {} - :{}:".format(author.name, nom))
                em.add_field(name="Staff, Que voulez-vous faire ? ",
                             value="✔ = Sticker accepté\n"
                                   "✖ = Sticker refusé")
                em.set_image(url=url)
                em.set_footer(
                    text="Cliquez sur une réaction pour interagir (Valable 5 minutes)")
                act = await self.bot.send_message(channel, embed=em)
                await self.bot.add_reaction(act, "✔")  # Accepte
                await self.bot.add_reaction(act, "✖")  # Refuse
                await asyncio.sleep(0.25)
                rep = await self.bot.wait_for_reaction(["✔", "✖"], message=act, timeout=300, check=self.check)
                if rep == None:
                    await self.bot.send_message(channel, "La demande de sticker de *{}* à expirée".format(author.name))
                    return
                elif rep.reaction.emoji == "✖":
                    await self.bot.send_message(channel,"**Demande refusée**")
                    return
                else:
                    await self.bot.send_message(channel,"{} **- Demande acceptée**".format(author.mention))

            if filename in os.listdir("data/charm/stkimg"):
                exten = filename.split(".")[1]
                nomsup = random.randint(1, 999999)
                filename = filename.split(".")[0] + str(nomsup) + "." + exten
            try:
                f = open(filename, 'wb')
                f.write(request.urlopen(url).read())
                f.close()
                file = "data/charm/stkimg/" + filename
                os.rename(filename, file)
                self.stk["STICKERS"][nom] = {"NOM": nom,
                                             "URL": url,
                                             "CHEMIN": file,
                                             "FORMAT": format}
                self.stk["USERS"][author.id]["COLLECTION"].append(nom)
                fileIO("data/charm/stk.json", "save", self.stk)
                await self.bot.say("L'Image **{}** à été enregistrée correctement.\nVous pouvez désormais l'utilser avec *:{}:*".format(filename, nom))
            except Exception as e:
                print("Impossible de télécharger une image : {}".format(e))
                await self.bot.say(
                    "Impossible de télécharger cette image.\nEssayez de changer d'hébergeur (Noelshack ou Imgur)")

        else:
            await self.bot.say("Sticker déjà présent.")

    async def charm_msg(self, message):
        author = message.author
        channel = message.channel
        mentions = message.mentions
        #Système AFK
        if "AFK" not in self.sys:
            self.sys["AFK"] = []
        for afk in self.sys["AFK"]:
            if author.id == afk[0]:
                self.sys["AFK"].remove([afk[0], afk[1], afk[2]])
                fileIO("data/charm/sys.json", "save", self.sys)
        if message.content.lower().startswith("afk"):
            raison = message.content.lower()[3:]
            if raison.startswith(" "):
                raison = raison[1:]
            self.sys["AFK"].append([author.id, author.name, raison])
            fileIO("data/charm/sys.json", "save", self.sys)
        if message.mentions != []:
            for m in message.mentions:
                for afk in self.sys["AFK"]:
                    if m.id == afk[0]:
                        if afk[2] != "":
                            if mentions == []:
                                await self.bot.send_message(channel, "**{}** est AFK\n**Raison:** *{}*".format(afk[1], afk[2]))
                            else:
                                await self.bot.send_message(channel, "**{}** est AFK".format(afk[1]))
                        else:
                            await self.bot.send_message(channel, "**{}** est AFK".format(afk[1]))

        #Système Stickers
        nb = 0
        if ":" in message.content:
            output = re.compile(':(.*?):', re.DOTALL | re.IGNORECASE).findall(message.content)
            if output:
                for stk in output:
                    if nb <= 3:
                        if stk == "list":
                            msg = "**__Liste des stickers disponibles__**\n\n"
                            n = 1
                            for s in self.stk["STICKERS"]:
                                msg += "- *{}*\n".format(self.stk["STICKERS"][s]["NOM"])
                                if len(msg) > 1950 * n:
                                    msg += "!!"
                                    n += 1
                            else:
                                msglist = msg.split("!!")
                                for m in msglist:
                                    await self.bot.send_message(author, m)
                                return
                        if stk == "custom":
                            nb += 1
                            if author.id in self.stk["USERS"]:
                                if self.stk["USERS"][author.id]["CUSTOM_URL"] != None:
                                    return_img = [self.stk["USERS"][author.id]["CUSTOM_URL"], None, self.stk["USERS"][author.id]["CUSTOM_FORMAT"]]
                                else:
                                    await self.bot.send_message(author,
                                                                "Vous n'avez pas de sticker custom. Vous pouvez un mettre un avec &stk submit custom <url>")
                            else:
                                await self.bot.send_message(author, "Vous n'avez pas de sticker custom. Vous pouvez un mettre un avec {}stk submit custom <url>")
                        elif stk in self.stk["STICKERS"]:
                            return_img = [self.stk["STICKERS"][stk]["URL"], self.stk["STICKERS"][stk]["CHEMIN"], self.stk["STICKERS"][stk]["FORMAT"]]
                        elif stk in self.old["STICKER"]:
                            if stk not in self.stk["STICKERS"]:
                                if "VERIF_STICK" not in self.sys:
                                    self.sys["VERIF_STICK"] = {}
                                if author.id not in self.sys["VERIF_STICK"]:
                                    self.sys["VERIF_STICK"][author.id] = []
                                if stk not in self.sys["VERIF_STICK"][author.id]:
                                    await self.bot.send_message(author, "Ce sticker existe dans mes anciens fichiers mais à été archivé.\n"
                                                                        "Vous pouvez l'importer avec '&stk import {}' sur le channel #bot !".format(stk))
                                    self.sys["VERIF_STICK"][author.id].append(stk)
                                else:
                                    return
                        else:
                            break

                        if return_img[2] == "INTEGRE":
                            em = discord.Embed(color=author.color)
                            em.set_image(url=return_img[0])
                            try:
                                await self.bot.send_message(channel, embed=em)
                            except:
                                print("L'URL de :{}: est indisponible. Je ne peux pas l'envoyer. (Format: INTEGRE)".format(stk))
                        elif return_img[2] == "UPLOAD":
                            try:
                                await self.bot.send_file(channel, return_img[1])
                            except:
                                print("Le fichier de :{}: n'existe plus ou n'a jamais existé. Je ne peux pas l'envoyer. (Format: UPLOAD)\nJe vais envoyer l'URL liée à la place...".format(stk))
                                try: #En cas que l'upload fail, on envoie l'URL brute
                                    await self.bot.send_message(channel, return_img[0])
                                except:
                                    print(
                                        "L'URL de :{}: est indisponible. Je ne peux pas l'envoyer. (Format: FailedUPLOAD)".format(
                                            stk))
                        else:
                            try:
                                await self.bot.send_message(channel, return_img[0])
                            except:
                                print("L'URL de :{}: est indisponible. Je ne peux pas l'envoyer. (Format: URL/Defaut)".format(stk))
                    else:
                        await self.bot.send_message(author, "**Ne spammez pas les stickers.**\nCela est considéré comme du spam.")
                        break

    async def member_join(self, user :discord.Member):
        ego = self.bot.get_cog('Ego').ego
        card = ego.log(user)
        if "NOTIF_CHANNEL" not in self.sys:
            self.sys["NOTIF_CHANNEL"] = "204585334925819904"
        if not self.sys["NOTIF_CHANNEL"] is None:
            channel = self.bot.get_channel(self.sys["NOTIF_CHANNEL"])
            if not channel.server.id == "204585334925819904":
                return
            if card.born < (time.time() - 3600):
                await self.bot.send_message(channel, "{} **est de revenu(e)**".format(user.mention))
            else:
                await self.bot.send_message(channel, "{} **est arrivé(e)**".format(user.mention))
            if "WELCOME_MSG" not in self.sys:
                self.sys["WELCOME_MSG"] = None
            if not self.sys["WELCOME_MSG"] is None:
                await self.bot.send_message(user, self.sys["WELCOME_MSG"])

    async def member_leave(self, user :discord.Member):
        if "NOTIF_CHANNEL" not in self.sys:
            self.sys["NOTIF_CHANNEL"] = "204585334925819904"
        if not self.sys["NOTIF_CHANNEL"] is None:
            channel = self.bot.get_channel(self.sys["NOTIF_CHANNEL"])
            if not channel.server.id == "204585334925819904":
                return
            await self.bot.send_message(channel, "{} **est parti(e)** :wave:".format(str(user)))

def check_folders():
    if not os.path.exists("data/charm"):
        print("Creation du fichier Charm...")
        os.makedirs("data/charm")

    if not os.path.exists("data/charm/stkimg"):
        print("Creation du fichier de Stockage d'images...")
        os.makedirs("data/charm/stkimg")

def check_files():
    default = {"NOTIF_CHANNEL": None, "WELCOME_MSG": None}
    if not os.path.isfile("data/charm/stk.json"):
        print("Creation du fichier de Charm stk.json...")
        fileIO("data/charm/stk.json", "save", {"USERS": {}, "STICKERS": {}})

    if not os.path.isfile("data/charm/sys.json"):
        print("Création du fichier systeme Charm...")
        fileIO("data/charm/sys.json", "save", default)

def setup(bot):
    check_folders()
    check_files()
    n = Charm(bot)
    bot.add_cog(n)
    bot.add_listener(n.charm_msg, "on_message")
    # Triggers
    bot.add_listener(n.member_join, "on_member_join")
    bot.add_listener(n.member_leave, "on_member_remove")