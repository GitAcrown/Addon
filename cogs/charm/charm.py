import asyncio
import operator
import os
import random
import re
import time
from urllib import request

import discord
from __main__ import send_cmd_help
from discord.ext import commands

from .utils import checks
from .utils.dataIO import fileIO, dataIO

default = {}

class Charm:
    """Gère les Stickers et d'autres fonctions liés aux salons textuels."""
    def __init__(self, bot):
        self.bot = bot
        self.stk = dataIO.load_json("data/charm/stk.json")
        self.sys = dataIO.load_json("data/charm/sys.json")
        self.ress = dataIO.load_json("data/charm/ress.json")
        # ============= #
        self.old = dataIO.load_json("data/stick/img.json")
        ### Après avoir importé les anciens stickers importants:
        #TODO Retirer self.old
        #TODO Effacer l'ensemble de l'ancien dossier de sticker

    def check(self, reaction, user):
        if user.server_permissions.manage_messages is True:
            return True
        else:
            return False

    def erucheck(self, reaction, user):
        if user.bot is False:
            return True
        else:
            return False

    def old_stick(self, nom):
        if nom in self.old["STICKER"]:
            return True
        else:
            return False

    def s_eru(self, num, list):
        for i in list:
            if num == i[0]:
                return i
        else:
            return False

    def levenshtein(self, s1, s2):
        if len(s1) < len(s2):
            m = s1
            s1 = s2
            s2 = m
        if len(s2) == 0:
            return len(s1)
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[
                                 j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]

    def plusproche(self, liste_b, listes):
        pt = {}
        for e in liste_b:
            for l in listes:
                nom = ""
                for i in l: nom += "{}/".format(i)
                if e in l:
                    if nom not in pt:
                        pt[nom] = 1
                    else:
                        pt[nom] += 1

    def similarite(self, mot, liste, tolerance = 5):
        prochenb = tolerance
        prochenom = None
        for i in liste:
            if self.levenshtein(i, mot) < prochenb:
                prochenom = i
                prochenb = self.levenshtein(i, mot)
        else:
            return prochenom

        # RESS >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><

    @commands.command(pass_context=True)
    async def eru(self, ctx, modif:bool = False):
        """Accès à l'Encyclopedie des Ressources Utiles.
        
        Différents liens, classés par domaine."""
        if modif is False:
            menu = False
            while True:
                liste = ""
                emoji = []
                for dom in self.ress:
                    liste += "{} **{}**\n".format(self.ress[dom]["EMOJI"], self.ress[dom]["NOM"])
                    emoji.append(self.ress[dom]["EMOJI"])
                em = discord.Embed(title="Encyclopedie des Ressources Utiles | Menu", description=liste, color=0x212427)
                em.set_footer(text="Cliquez sur une réaction pour choisir un domaine")
                if menu is False:
                    menu = await self.bot.say(embed=em)
                else:
                    await self.bot.clear_reactions(menu)
                    menu = await self.bot.edit_message(menu, embed=em)
                for e in emoji:
                    await self.bot.add_reaction(menu, e)
                await asyncio.sleep(0.5)
                choix = await self.bot.wait_for_reaction(emoji, message=menu, timeout=30, check=self.erucheck)
                if choix is None:
                    em.set_footer(text="---- Timeout atteint ----")
                    await self.bot.edit_message(menu, embed=em)
                    return
                else:
                    for dom in self.ress:
                        if choix.reaction.emoji == self.ress[dom]["EMOJI"]: # On cherche à quel domaine appartient cet emoji
                            rlist = []
                            n = 1
                            for r in self.ress[dom]["RESSOURCES"]:
                                rlist.append([n, self.ress[dom]["RESSOURCES"][r]["nom"], self.ress[dom]["RESSOURCES"][r]["desc"], self.ress[dom]["RESSOURCES"][r]["image"], self.ress[dom]["RESSOURCES"][r]["lien"]])
                                n += 1
                            if rlist != []:
                                disp = random.choice(rlist)
                                num = disp[0]
                                sort = sorted(rlist, key=operator.itemgetter(0), reverse=True)
                                max = sort[0][0]  # Le dernier de la liste
                                retour = False
                                while retour is False:
                                    if num < 1:
                                        num = max
                                    elif num > max:
                                        num = 1
                                    else:
                                        pass
                                    for rb in rlist:
                                        if num == rb[0]:
                                            disp = rb
                                    descr = disp[2]
                                    if len(disp[2]) > 1900:
                                        descr = descr[:1900]
                                        descr += "..."
                                    em = discord.Embed(title="E.R.U. | {} - *{}*".format(self.ress[dom]["NOM"].title(), disp[1]),
                                                       description=descr, color=0x212427, url=disp[4])
                                    em.set_thumbnail(url=disp[3])
                                    em.set_footer(text="Utilisez les réactions ci-dessous pour naviguer")
                                    try:
                                        await self.bot.clear_reactions(menu)
                                        menu = await self.bot.edit_message(menu, embed=em)
                                        await self.bot.add_reaction(menu, "⏪")
                                        await self.bot.add_reaction(menu, "⏹")
                                        await self.bot.add_reaction(menu, "⏩")
                                        act = await self.bot.wait_for_reaction(["⏪","⏹", "⏩"], message=menu, timeout=90, check=self.erucheck)
                                        if act == None:
                                            em.set_footer(text="---- Session expiré ----")
                                            await self.bot.edit_message(menu, embed=em)
                                            return
                                        elif act.reaction.emoji == "⏪":
                                            num += 1
                                        elif act.reaction.emoji == "⏹":
                                            retour = True
                                        elif act.reaction.emoji == "⏩":
                                            num -= 1
                                        else:
                                            pass
                                    except:
                                        num += 1
                            else:
                                em.set_footer(text="Aucune ressource n'est disponible pour ce domaine | Retour au menu")
                                await self.bot.edit_message(menu, embed=em)
                                await asyncio.sleep(1.5)
        else:
            em = discord.Embed(title="E.R.U. | Ajouter une ressource", description="Afin d'ajouter une ressource suivez le format ci-dessous:\n"
                                                                                   "**categorie**|**nom**|**description rapide**|**url de la vignette**|**lien vers la ressource**")
            em.add_field(name="Catégories disponibles", value="Sciences\nHistgeo\nEcopol\nCulture\nInfos\nDivers")
            em.set_footer(text="Entrez ci-dessous les informations de votre ressource en respectant le format ci-dessus (| = Altgr 6)")
            txt = await self.bot.whisper(embed=em)
            verif = False
            while verif is False:
                rep = await self.bot.wait_for_message(author=ctx.message.author, channel=txt.channel, timeout=300)
                if rep is None:
                    await self.bot.whisper("Vous avez mis trop de temps | Bye :wave:")
                    return
                else:
                    ress = rep.content.split("|")
                    if ress[0].upper() in self.ress:
                        msg = "**Nom** *{}*\n" \
                              "**Description** *{}*\n" \
                              "**URL Image** *{}*\n" \
                              "**Lien ressource** *{}*\n\n" \
                              "__Verifiez les informations. Si c'est bon, tapez 'OK' sinon tapez 'retour'__".format(ress[1], ress[2], ress[3], ress[4])
                        await self.bot.whisper(msg)
                        rop = await self.bot.wait_for_message(author=ctx.message.author, channel=txt.channel, timeout=120)
                        if rop is None:
                            await self.bot.whisper("Vous avez mis trop de temps | Bye :wave:")
                            return
                        elif rop.content.lower() == "ok":
                            await self.bot.whisper("Votre ressource est enregistrée avec succès !")
                            self.ress[ress[0].upper()]["RESSOURCES"][ress[1].lower()] = {"nom": ress[1], "desc": ress[2], "image": ress[3], "lien": ress[4]}
                            fileIO("data/charm/ress.json", "save", self.ress)
                            return
                        else:
                            await self.bot.whisper("Veuillez donc entrer de nouveau les informations de votre ressource en suivant le format indiqué.")
                    else:
                        await self.bot.whisper("Cette catégorie n'existe pas. Verifiez l'orthographe et réessayez.")

    @commands.command(pass_context=True)
    @checks.mod_or_permissions(kick_members=True)
    async def reperu(self, ctx, nom:str):
        """Permet de supprimer une ressource corrompue"""
        for dom in self.ress:
            if nom.lower() in self.ress[dom]["RESSOURCES"]:
                del self.ress[dom]["RESSOURCES"][nom]
                await self.bot.say("Ressource corrompue supprimée avec succès.")
                return
        else:
            await self.bot.say("Introuvable.")

    @commands.command(pass_context=True)
    async def udbg(self, ctx, chemin):
        """Permet d'obtenir les fichiers d'un module."""
        try:
            await self.bot.say("Upload en cours...")
            await self.bot.send_file(ctx.message.channel, chemin)
        except:
            await self.bot.say("Impossible d'upload ce fichier")

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

# GhostButser (Pour les ghostfags) >>>>>>>>>>>>>>>>>>>>>>>>>>>>><

    @commands.command(aliases= ["gb"], pass_context=True, no_pm=True)
    async def ghostbuster(self, ctx):
        """Permet de contacter aléatoirement un ghostfag du serveur."""
        if "GB_LIST" not in self.sys:
            self.sys["GB_LIST"] = []
            fileIO("data/charm/sys.json", "save", self.sys)
        server = ctx.message.server
        await self.bot.whisper("**Recherche d'un ghostfag disponible et non contacté...**")
        for m in server.members:
            if m.top_role.name == "@everyone":
                if m.status != discord.Status.offline:
                    if m.id not in self.sys["GB_LIST"]:
                        await asyncio.sleep(1.5)
                        self.sys["GB_LIST"].append(m.id)
                        await self.bot.whisper("**Voilà votre cible:**\nPseudo: {}\nSurnom: {}\nID: {}".format(m.name, m.display_name, m.id))
                        fileIO("data/charm/sys.json", "save", self.sys)
                        return
        else:
            await self.bot.whisper("**Aucun ghostfag n'est disponible ou ils ont déjà tous été contactés.**")

# STICKERS >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><

    @commands.group(name="stk", pass_context=True)
    async def charm_stk(self, ctx):
        """Gestion Stickers"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    #TODO Fonction recherche avancée

    @charm_stk.command(name="import", pass_context=True)
    async def import_sticker(self, ctx, nom, nomimport = None):
        """Permet d'importer un ancien sticker et de le réencoder dans le nouveau format.
        
        Vous pouvez lui donner un nouveau nom en précisant NomImport"""
        author = ctx.message.author
        if not author.id in self.stk["USERS"]:
            self.stk["USERS"][author.id] = {"ID": author.id,
                                            "CUSTOM_URL": None,
                                            "CUSTOM_FORMAT": None,
                                            "COLLECTION": []}
            fileIO("data/charm/stk.json", "save", self.stk)

        if nom in self.old["STICKER"]:
            if nomimport is not None:
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
                await self.bot.say("Les données de l'image sont corrompues ou sont obsolètes (Sticker de 1er Gen.)\n**Rétablissement automatique du sticker en cours...**")
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
                                                 "FORMAT": "URL"}
                    self.stk["USERS"][author.id]["COLLECTION"].append(nom)
                    fileIO("data/charm/stk.json", "save", self.stk)
                    await self.bot.say(
                        "L'Image **{}** à été rétablie correctement.\nVous pouvez de nouveau l'utiliser avec *:{}:*".format(
                            filename, nom))
                except Exception as e:
                    print("Impossible de télécharger une image : {}".format(e))
                    await self.bot.say(
                        "Impossible de rétablir cette image.\nL'URL n'est plus compatible. Changez l'image d'hébergeur et réajoutez la manuellement avec &stk submit\nUrl fournie à sa création: {}".format(url))
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
        server = message.server
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
                    nb += 1
                    if nb <= 3:
                        if stk == "random":
                            liste = []
                            for s in self.stk["STICKERS"]:
                                liste.append(s)
                            stk = random.choice(liste)
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
                        if stk == "vent": #EE
                            await asyncio.sleep(0.5)
                            await self.bot.send_typing(channel)
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
                            liste = []
                            for s in self.stk["STICKERS"]:
                                liste.append(s)
                            img = self.similarite(stk, liste, 2)
                            if stk not in [e.name for e in server.emojis]:
                                return_img = [self.stk["STICKERS"][img]["URL"], self.stk["STICKERS"][img]["CHEMIN"],
                                              self.stk["STICKERS"][img]["FORMAT"]]
                            else:
                                return

                        if return_img[2] == "INTEGRE":
                            em = discord.Embed(color=author.color)
                            em.set_image(url=return_img[0])
                            try:
                                await self.bot.send_typing(channel)
                                await self.bot.send_message(channel, embed=em)
                            except:
                                print("L'URL de :{}: est indisponible. Je ne peux pas l'envoyer. (Format: INTEGRE)".format(stk))
                        elif return_img[2] == "UPLOAD":
                            try:
                                await self.bot.send_typing(channel)
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
                                await self.bot.send_typing(channel)
                                await self.bot.send_message(channel, return_img[0])
                            except:
                                print("L'URL de :{}: est indisponible. Je ne peux pas l'envoyer. (Format: URL/Defaut)".format(stk))
                    else:
                        await self.bot.send_message(author, "**Ne spammez pas les stickers !**")
                        break

    @commands.command(pass_context=True, no_pm=True, hidden=True)
    async def egotest(self, ctx):
        """Test la connexion entre Charm et EGO"""
        try:
            ego = self.bot.get_cog('Ego').ego
            card = ego.log(ctx.message.author)
            await self.bot.say(str(card.born))
        except:
            await self.bot.say("Ego n'est pas connecté.")

    async def member_join(self, user :discord.Member):
        server = user.server
        if server.id == "204585334925819904":
            ego = self.bot.get_cog('Ego').ego
            card = ego.log(user)
            msgs = ["{} **est arrivé(e)**", "{} **est entré(e) sur le serveur**", "**Bienvenue à** {}", "**Nouvel arrivant:** {}"]
            welcome = random.choice(msgs)
            if "NOTIF_CHANNEL" not in self.sys:
                self.sys["NOTIF_CHANNEL"] = "204585334925819904"
            if not self.sys["NOTIF_CHANNEL"] is None:
                channel = self.bot.get_channel(self.sys["NOTIF_CHANNEL"])
                if not channel.server.id == "204585334925819904":
                    return
                if card.born < (time.time() - 3600):
                    await self.bot.send_message(channel, "{} **est revenu(e)**".format(user.mention))
                else:
                    await self.bot.send_message(channel, welcome.format(user.mention))
                if "WELCOME_MSG" not in self.sys:
                    self.sys["WELCOME_MSG"] = None
                if not self.sys["WELCOME_MSG"] is None:
                    await self.bot.send_message(user, self.sys["WELCOME_MSG"])

    async def member_leave(self, user :discord.Member):
        server = user.server
        if server.id == "204585334925819904":
            msgs = ["{} **est parti(e)**", "{} **s'en va**", "**Au revoir** {}",
                    "**Départ de:** {}", "{} **a quitté le serveur**"]
            bye = random.choice(msgs)
            if "NOTIF_CHANNEL" not in self.sys:
                self.sys["NOTIF_CHANNEL"] = "204585334925819904"
            if not self.sys["NOTIF_CHANNEL"] is None:
                channel = self.bot.get_channel(self.sys["NOTIF_CHANNEL"])
                if not channel.server.id == "204585334925819904":
                    return
                await self.bot.send_message(channel, bye.format(str(user)))

# NOUVEAU POLL >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><

    @commands.command(aliases=["fp"], pass_context=True, no_pm=True)
    async def fastpoll(self, ctx, *qr):
        """Permet de lancer un sondage rapide (Avec réactions)
        Format de <qr>:
        question;reponse1;reponse2;reponseN..."""
        qr = " ".join(qr)
        question = qr.split(";")[0]
        repsf = qr.split(";")[1:]
        emojis = [s for s in "🇦🇧🇨🇩🇪🇫🇬🇭🇮🇯🇰🇱🇲🇳🇴🇵🇶🇷🇸🇹🇺🇻🇼🇽🇾🇿"]
        r = lambda: random.randint(0,255)
        rcolor = int('0x%02X%02X%02X' % (r(), r(), r()), 16)
        n = 0
        randomcode = random.randint(100, 999)
        rep = []
        if len(repsf) <= 9:
            if len(repsf) > 1:
                msg = ""
                sch = []
                for r in repsf:
                    if r.startswith(" "):
                        r = r[1:]
                    if r.endswith(" "):
                        r = r[:-1]
                    rep.append([emojis[n], r])
                    sch.append(emojis[n])
                    msg += "\{} *{}*\n".format(emojis[n], r)
                    n += 1
                em = discord.Embed(color=rcolor)
                em.set_author(name="#{} | {}".format(randomcode, question), icon_url=ctx.message.author.avatar_url)
                em.add_field(name="Réponses", value=msg)
                em.set_footer(text="Chargement... Patientez quelques secondes...")
                try:
                    await self.bot.delete_message(ctx.message)
                except:
                    pass
                menu = await self.bot.say(embed=em)
                if "SONDAGES" not in self.sys:
                    self.sys["SONDAGES"] = {}
                for e in sch:
                    try:
                        await self.bot.add_reaction(menu, e)
                    except:
                        pass
                await asyncio.sleep(0.5)
                em.set_footer(text="Votez avec les réactions correspondantes ci-dessous | Un vote par membre")
                await self.bot.edit_message(menu, embed=em)
                self.sys["SONDAGES"][menu.id] = {"QUESTION": question,
                                                 "REPEMOJI": rep,
                                                 "DETECT": sch,
                                                 "AVOTE": [],
                                                 "STATS": {},
                                                 "DESC": msg,
                                                 "TOTAL": 0,
                                                 "AVATAR": ctx.message.author.avatar_url,
                                                 "COLOR": rcolor,
                                                 "IDENT": "#{}".format(randomcode)}
                fileIO("data/charm/sys.json", "save", self.sys)
            else:
                await self.bot.say("Vous devez rentrer au moins 2 réponses possible.\n*fp question;option1;option2 (...)*")
        else:
            await self.bot.say("Vous ne pouvez pas rentrer plus de 9 réponses.\n*fp question;option1;option2 (...)*")

    async def fp_listen(self, reaction, user):
        message = reaction.message
        if "SONDAGES" in self.sys:
            if message.id in self.sys["SONDAGES"]:
                if reaction.emoji in self.sys["SONDAGES"][message.id]["DETECT"]:
                    if user.id not in self.sys["SONDAGES"][message.id]["AVOTE"]:
                        for r in self.sys["SONDAGES"][message.id]["REPEMOJI"]:
                            if r[0] == reaction.emoji:
                                if r[1] not in self.sys["SONDAGES"][message.id]["STATS"]:
                                    self.sys["SONDAGES"][message.id]["STATS"][r[1]] = {"REPONSE": r[1],
                                                                                       "NB": 1}
                                else:
                                    self.sys["SONDAGES"][message.id]["STATS"][r[1]]["NB"] += 1
                                self.sys["SONDAGES"][message.id]["TOTAL"] += 1
                                self.sys["SONDAGES"][message.id]["AVOTE"].append(user.id)
                                msg = self.sys["SONDAGES"][message.id]["DESC"]
                                res = ""
                                for s in self.sys["SONDAGES"][message.id]["STATS"]:
                                    res += "**{}** - *{}* (*{}%*)\n".format(self.sys["SONDAGES"][message.id]["STATS"][s]["REPONSE"], self.sys["SONDAGES"][message.id]["STATS"][s]["NB"], round((self.sys["SONDAGES"][message.id]["STATS"][s]["NB"] / self.sys["SONDAGES"][message.id]["TOTAL"]) * 100, 1))
                                res += "\n**Total:** {}".format(self.sys["SONDAGES"][message.id]["TOTAL"])
                                em = discord.Embed(color=self.sys["SONDAGES"][message.id]["COLOR"])
                                em.add_field(name="Réponses", value=msg, inline=False)
                                em.add_field(name="Résultats", value=res, inline=False)
                                question = self.sys["SONDAGES"][message.id]["QUESTION"]
                                randomcode = self.sys["SONDAGES"][message.id]["IDENT"]
                                em.set_author(name="{} | {}".format(randomcode, question), icon_url=self.sys["SONDAGES"][message.id]["AVATAR"])
                                em.set_footer(
                                    text="Votez avec les réactions correspondantes ci-dessous | Un vote par membre")
                                fileIO("data/charm/sys.json", "save", self.sys)
                                await self.bot.edit_message(message, embed=em)
                                await self.bot.send_message(user, "**{}** | Merci d'avoir voté !".format(self.sys["SONDAGES"][message.id]["IDENT"]))
                    else:
                        try:
                            await self.bot.send_message(user, "**{}** | Tu as déjà voté !".format(self.sys["SONDAGES"][message.id]["IDENT"]))
                        except:
                            pass



def check_folders():
    if not os.path.exists("data/charm"):
        print("Creation du fichier Charm...")
        os.makedirs("data/charm")

    if not os.path.exists("data/charm/stkimg"):
        print("Creation du fichier de Stockage d'images...")
        os.makedirs("data/charm/stkimg")

def check_files():
    default = {"NOTIF_CHANNEL": None, "WELCOME_MSG": None}
    eru_base = {"SCIENCES": {"NOM": "Sciences", "EMOJI": "🔬", "COLOR": 0xdb2929, "RESSOURCES": {}},
                "HISTGEO": {"NOM": "Histoire & Geographie", "EMOJI": "🗺", "COLOR": 0xe5ca27, "RESSOURCES": {}},
                "ECOPOL": {"NOM": "Economie & Politique", "EMOJI": "🔖", "COLOR": 0x2997db, "RESSOURCES": {}},
                "CULTURE": {"NOM": "Culture", "EMOJI": "🗿", "COLOR": 0x2f29db, "RESSOURCES": {}},
                "INFOS": {"NOM": "Infos", "EMOJI": "📰", "COLOR": 0xf4f4f4, "RESSOURCES": {}},
                "DIVERS": {"NOM": "Divers", "EMOJI": "❔", "COLOR": 0x55c182, "RESSOURCES": {}}}
    if not os.path.isfile("data/charm/stk.json"):
        print("Creation du fichier de Charm stk.json...")
        fileIO("data/charm/stk.json", "save", {"USERS": {}, "STICKERS": {}})

    if not os.path.isfile("data/charm/sys.json"):
        print("Création du fichier systeme Charm...")
        fileIO("data/charm/sys.json", "save", default)

    if not os.path.isfile("data/charm/ress.json"):
        print("Création du fichier encyclopedie Charm...")
        fileIO("data/charm/ress.json", "save", eru_base)

def setup(bot):
    check_folders()
    check_files()
    n = Charm(bot)
    bot.add_cog(n)
    # Triggers
    bot.add_listener(n.charm_msg, "on_message")
    bot.add_listener(n.member_join, "on_member_join")
    bot.add_listener(n.member_leave, "on_member_remove")
    bot.add_listener(n.fp_listen, "on_reaction_add")