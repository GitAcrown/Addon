import discord
from discord.ext import commands
from .utils.dataIO import fileIO, dataIO
from .utils import checks
from __main__ import send_cmd_help, settings
import asyncio
import random
import os
import time
import datetime

#'Addon' EXCLUSIVE

#Facteur années ~= 31560000 secondes/an

class Nobody:
    """Nobody: Parce que vous n'êtes personne. (Extension sociale)"""

    def __init__(self, bot):
        self.bot = bot
        self.nob = dataIO.load_json("data/nobody/nob.json") #Comptes
        self.sys = dataIO.load_json("data/nobody/sys.json") #Réglages

    #------------------- DEFINITIONS ---------------------

    def in_nob(self, user):
        if user.id in self.nob:
            return True
        else:
            return False

    def new_nob(self, user): #Création profil
        if not self.in_nob(user):
            localtime = time.localtime()
            r = lambda: random.randint(0,255)
            color = '0x%02X%02X%02X' % (r(),r(),r())
            self.nob[user.id] = {"FULL" : str(user),
                                 "PSEUDO" : user.display_name,
                                 "ID" : user.id,
                                 "FAGTAG" : self.gen_fagtag(),
                                 "PRENOM" : "N.R.",
                                 "INSCR" : time.strftime("%d/%m/%Y %H:%M:%S", localtime),
                                 "ANNIV" : "N.R.",
                                 "LOCAL" : "N.R.",
                                 "ACTIVITE" : "N.R.",
                                 "DESCRIPTION" : "N.R.",
                                 "COULEUR" : color, #ALEATOIRE
                                 "COMPTES" : "N.R.",
                                 "PUBLIC" : None,
                                 "FAGS" : []}
            self.save()
            return True
        else:
            return False

    def save(self):
        fileIO("data/nobody/nob.json", "save", self.nob)
        fileIO("data/nobody/sys.json", "save", self.nob)
        return True

    def gen_fagtag(self):
        let = ["A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z"]
        t = random.sample(let, 4)
        m = ""
        for i in t:
            m += i
        tag = "F+" + m
        return tag

    def fagtag_s(self, tag):
        for id in self.nob:
            if self.nob[id]["FAGTAG"] == tag:
                return id
        else:
            return None
                

    def is_public(self, user):
        if self.in_nob(user):
            if self.nob[user.id]["PUBLIC"] == True:
                return True
            else:
                return False
        else:
            return False

    def in_fags(self, prop, user):
        if self.in_nob(user):
            if self.in_nob(prop):
                if user.id in self.nob[prop.id]["FAGS"]:
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False

       # ========================= MODULE ============================

    @commands.command(pass_context=True, hidden=True, no_pm=True)
    async def reset_sys(self, ctx):
        default = {"INVITS" : [],"AN_CHAN" : None, "SERVER_ID" : ctx.message.server.id}
        self.sys = default
        self.save()
        await self.bot.say("Fait.")

    @commands.command(pass_context=True, hidden=True)
    async def nbdv(self, ctx):
        await self.bot.say("1.0")

    @commands.group(pass_context=True)
    async def nbd(self, ctx):
        """Commandes NOBODY"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @nbd.command(pass_context=True)
    async def addfag(self, ctx):
        """Permet d'ajouter un Fag."""
        author = ctx.message.author
        server = self.sys["SERVER_ID"]
        detect = ctx.message.server
        if detect:
            await self.bot.whisper("**Cette action est privée.** Veuillez la réaliser en MP.")
            return
        if server:
            server = self.bot.get_server(server)
            if self.in_nob(author):
                chan = await self.bot.whisper("**Entrez le FAGTAG...**")
                channel = chan.channel
                verif = False
                while verif != True:
                    rep = await self.bot.wait_for_message(author=author, channel=channel)
                    ami = self.fagtag_s(rep.content)
                    if ami != None:
                        await self.bot.whisper("*Compte détecté : {}*".format(self.nob[ami]["FULL"]))
                        verif = True
                    else:
                        await self.bot.whisper("*FAGTAG Invalide.*")
                        return
                if ami in self.nob[author.id]["FAGS"]:
                    await self.bot.whisper("Vous êtes déjà amis !")
                    return
                await asyncio.sleep(0.25)
                wait = server.get_member(ami)
                await self.bot.send_message(wait, "**[{} désire être votre ami(e)]**\n*Utilisez '{}nbd accept {}' pour accepter sa demande, sinon ignorez.*".format(author.name, ctx.prefix, self.nob[author.id]["FAGTAG"]))
                await self.bot.whisper("**Demande envoyée, elle sera valide 2 minutes.**\nVous recevrez un MP si cette personne accepte votre demande.")
                self.sys["INVITS"].append([self.nob[author.id]["FAGTAG"], rep.content, author.id, author.name])
                self.save()
                await asyncio.sleep(120)
                if [self.nob[author.id]["FAGTAG"], rep.content, author.id] in self.sys["INVITS"]:
                    self.sys["INVITS"].remove([self.nob[author.id]["FAGTAG"], rep.content, author.id, author.name])
                    self.save()
                    await self.bot.whisper("*Demande expirée.*")
                    await self.bot.send_message(wait, "*La demande de {} a expiré.".format(author.name))
                else:
                    await self.bot.whisper("*Votre demande à été acceptée.*")
            else:
                await self.bot.whisper("Vous n'êtes pas inscrit sur Nobody.")
        else:
            await self.bot.whisper("Aucun serveur n'est paramétré.")

    @nbd.command(pass_context=True, hidden=True)
    async def accept(self, ctx, tag):
        """Permet d'accepter une demande."""
        author = ctx.message.author
        for t in self.sys["INVITS"]:
            if tag == t[0]:
                await self.bot.whisper("Demande de {} acceptée.".format(t[3]))
                self.nob[author.id]["FAGS"].append(t[2])
                self.nob[t[2]]["FAGS"].append(author.id)
                self.sys["INVITS"].remove([t[0],t[1],t[2], t[3]])
                self.save()
                return
            else:
                pass
        else:
            await self.bot.whisper("Aucune invitation avec ce tag n'est présente.")

    @nbd.command(pass_context=True, hidden=True)
    async def bye(self, ctx):
        """Permet de quitter Nobody."""
        author = ctx.message.author
        if self.in_nob(author):
            chan = await self.bot.whisper("Êtes-vous sûr de vouloir supprimer votre compte Nobody ? (O/N)")
            channel = chan.channel
            verif = False
            while verif != True:
                rep = await self.bot.wait_for_message(author=author, channel=channel)
                if "o" == rep.content.lower():
                    await self.bot.whisper("*Compte supprimé.*")
                    del self.nob[author.id]
                    verif = True
                    self.save()
                elif "n" == rep.content.lower():
                    await self.bot.whisper("*Compte conservé.*")
                    verif = True
                else:
                    await self.bot.whisper("*Compte conservé (Réponse invalide)*")
                    verif = True
        else:
            await self.bot.whisper("Vous n'avez pas de compte sur Nobody.")
            
    @nbd.command(pass_context=True)
    async def new(self, ctx):
        """Rejoindre Nobody !"""
        author = ctx.message.author
        if not self.in_nob(author):
            await self.bot.whisper("**Salut {} !**\n*Bienvenue sur le réseau NOBODY.*".format(author.name))
            await asyncio.sleep(0.5)
            chan = await self.bot.whisper("Nous allons remplir ensemble ton profil. Tu as juste besoin de me répondre sur ce MP comme une conversation normale.\n*Si tu veux sauter une question, tu peux juste dire 'NR' (Non Renseigné)*\n*Si tu veux un exemple, tu peux dire 'ex'.*")
            channel = chan.channel
            self.new_nob(author)

            await self.bot.whisper("**IDENTITE** - Quel est ton prénom ?")
            verif = False
            while verif != True:
                rep = await self.bot.wait_for_message(author=author, channel=channel)
                if "nr" == rep.content.lower():
                    await self.bot.whisper("*Ignoré.*")
                    verif = True
                elif "ex" == rep.content.lower():
                    await self.bot.whisper("*EXEMPLE:* Cunégonde")
                elif "stop" == rep.content.lower():
                    await self.bot.whisper("**Arrêt**")
                    return
                else:
                    self.nob[author.id]["PRENOM"] = rep.content
                    self.save()
                    await self.bot.whisper("*Enregistré !*")
                    verif = True
            await asyncio.sleep(0.5)

            await self.bot.whisper("**ANNIVERSAIRE** - Quel jour es-tu né(e) ? *Format: jj/mm/aaaa*")
            verif = False
            while verif != True:
                rep = await self.bot.wait_for_message(author=author, channel=channel)
                if "/" in rep.content:
                    if len(rep.content) == 10:
                        self.nob[author.id]["ANNIV"] = rep.content
                        self.save()
                        await self.bot.whisper("*Enregistré !*")
                        verif = True
                    else:
                        await self.bot.whisper("*Invalide, recommence !*")
                elif "nr" == rep.content.lower():
                    await self.bot.whisper("*Ignoré.*")
                    verif = True
                elif "ex" == rep.content.lower():
                    await self.bot.whisper("*EXEMPLE:* 06/11/1991")
                elif "stop" == rep.content.lower():
                    await self.bot.whisper("**Arrêt**")
                    return
                else:
                    await self.bot.whisper("*Invalide, recommence !*")
            await asyncio.sleep(0.5)
            
            await self.bot.whisper("**LOCALISATION** - Dans quel pays et dans quelle région te situe-tu ? *Format: Pays/Région*")
            verif = False
            while verif != True:
                rep = await self.bot.wait_for_message(author=author, channel=channel)
                if "/" in rep.content:
                    self.nob[author.id]["LOCAL"] = rep.content
                    self.save()
                    await self.bot.whisper("*Enregistrée !*")
                    verif = True
                elif "nr" == rep.content.lower():
                    await self.bot.whisper("*Ignoré.*")
                    verif = True
                elif "ex" == rep.content.lower():
                    await self.bot.whisper("*EXEMPLE:* France/Normandie")
                elif "stop" == rep.content.lower():
                    await self.bot.whisper("**Arrêt**")
                    return
                else:
                    await self.bot.whisper("*Invalide, recommence !*")
            await asyncio.sleep(0.5)

            await self.bot.whisper("**ACTIVITE** - Quelle est ta profession ou ta situation à ce niveau ?")
            verif = False
            while verif != True:
                rep = await self.bot.wait_for_message(author=author, channel=channel)
                if len(rep.content) > 4:
                    self.nob[author.id]["ACTIVITE"] = rep.content
                    self.save()
                    await self.bot.whisper("*Enregistrée !*")
                    verif = True
                elif "nr" == rep.content.lower():
                    await self.bot.whisper("*Ignoré.*")
                    verif = True
                elif "ex" == rep.content.lower():
                    await self.bot.whisper("*EXEMPLE:* Au RSA")
                elif "stop" == rep.content.lower():
                    await self.bot.whisper("**Arrêt**")
                    return
                else:
                    await self.bot.whisper("*Invalide, recommence !(>4 caractères)*")
            await asyncio.sleep(0.5)

            await self.bot.whisper("**DESCRIPTION** - Ce qui te passe à l'esprit...")
            verif = False
            while verif != True:
                rep = await self.bot.wait_for_message(author=author, channel=channel)
                if len(rep.content) > 4:
                    self.nob[author.id]["DESCRIPTION"] = rep.content
                    self.save()
                    await self.bot.whisper("*Enregistrée !*")
                    verif = True
                elif "nr" == rep.content.lower():
                    await self.bot.whisper("*Ignoré.*")
                    verif = True
                elif "ex" == rep.content.lower():
                    await self.bot.whisper("*EXEMPLE:* Je suis un putain de gros drogué hipster.")
                elif "stop" == rep.content.lower():
                    await self.bot.whisper("**Arrêt**")
                    return
                else:
                    await self.bot.whisper("*Invalide, recommence ! (>4 caractères)*")
            await asyncio.sleep(0.5)

            await self.bot.whisper("**COMPTES** - Si tu veux afficher des comptes externes. *Format: site1:nom_compte1/site2:nom_compte2 ...*")
            verif = False
            while verif != True:
                rep = await self.bot.wait_for_message(author=author, channel=channel)
                if ":" in rep.content:
                    n = rep.content.split("/")
                    clean = []
                    for e in n:
                        e = e.split(":")
                        clean.append([e[0],e[1]])
                    self.nob[author.id]["COMPTES"] = clean
                    self.save()
                    await self.bot.whisper("*Enregistré(s) !*")
                    verif = True
                elif "nr" == rep.content.lower():
                    await self.bot.whisper("*Ignoré.*")
                    verif = True
                elif "ex" == rep.content.lower():
                    await self.bot.whisper("*EXEMPLE:* Steam:Kevin_du_60xx/Snap:CHILL/FB:Zbeub")
                elif "stop" == rep.content.lower():
                    await self.bot.whisper("**Arrêt**")
                    return
                else:
                    await self.bot.whisper("*Invalide, recommence !*")
            await asyncio.sleep(0.5)

            await self.bot.whisper("**GLOBAL** - Veux-tu que ton compte Nobody soit visible par tous ? *Oui/Non*\n*Si tu le met en 'Privé', tes FAGS seront les seuls à pouvoir le voir entièrement.*")
            verif = False
            while verif != True:
                rep = await self.bot.wait_for_message(author=author, channel=channel)
                if len(rep.content) == 3:
                    if rep.content.lower() == "oui":
                        self.nob[author.id]["PUBLIC"] = True
                        self.save()
                        await self.bot.whisper("*Ton compte sera public*")
                        verif = True
                    else:
                        self.nob[author.id]["PUBLIC"] = False
                        self.save()
                        await self.bot.whisper("*Ton compte sera privé*")
                        verif = True
                elif "ex" == rep.content.lower():
                    await self.bot.whisper("*EXEMPLE:* Oui (Public)/Non (Privé)")
                elif "stop" == rep.content.lower():
                    await self.bot.whisper("**Arrêt**")
                    return
                elif "nr" == rep.content.lower():
                    await self.bot.whisper("*Impossible de sauter cette question !*")
                else:
                    await self.bot.whisper("*Invalide, recommence !*")
            await asyncio.sleep(0.5)

            await self.bot.whisper("*Enregistrement de tes données en cours (...)*")
            await asyncio.sleep(1)
            await self.bot.whisper("**Compte ouvert avec succès !**\nVoici ton FAGTAG: *{}*\nIl te permettra d'enregistrer des amis sur Nobody.".format(self.nob[author.id]["FAGTAG"]))
        else:
            await self.bot.whisper("Tu es déjà inscrit sur Nobody !")

    @nbd.command(pass_context=True)
    async def profil(self, ctx, user : discord.Member = None):
        """Affiche le profil Nobody d'un utilisateur."""
        author = ctx.message.author
        if user == None:
            user = author
        if user.id in self.nob:
            if user.id == author.id or author.id in self.nob[user.id]["FAGS"] or self.nob[user.id]["PUBLIC"] is True:
                coul = self.nob[user.id]["COULEUR"]
                coul = int(coul, 16)
                em = discord.Embed(colour=coul, inline=False)
                em.add_field(name="Pseudo", value = str(user.display_name))
                em.add_field(name="ID", value = str(user.id))
                em.add_field(name="Anniversaire", value = str(self.nob[user.id]["ANNIV"]))
                em.add_field(name="Pays/Région", value = str(self.nob[user.id]["LOCAL"]))
                em.add_field(name="Description", value = self.nob[user.id]["DESCRIPTION"])
                em.add_field(name="Activité", value = str(self.nob[user.id]["ACTIVITE"]))
                comptes = self.nob[user.id]["COMPTES"]
                msg = ""
                if self.nob[user.id]["COMPTES"] != "N.R.":
                    for e in comptes:
                        msg += "{}: {}\n".format(e[0],e[1])
                else:
                    msg = "N.R."
                em.add_field(name="Comptes", value= msg)
                em.set_author(name="Profil de " + str(user), icon_url=user.avatar_url)
                em.set_footer(text="Inscrit(e) le {}".format(self.nob[user.id]["INSCR"]))
                await self.bot.whisper(embed=em)
                if user.id == author.id:
                    fag = "**Votre FAGTAG:** {}\n\n".format(self.nob[user.id]["FAGTAG"])
                    fag += "**Vos FAGS:**\n"
                    if self.nob[user.id]["FAGS"] != []:
                        for f in self.nob[user.id]["FAGS"]:
                            nom = self.nob[f]["FULL"]
                            fag += "- *{}*\n".format(nom)
                    else:
                        fag += "Vous n'avez pas d'amis..."
                    await self.bot.whisper(fag)
                    
            else:
                coul = self.nob[user.id]["COULEUR"]
                coul = int(coul, 16)
                em = discord.Embed(colour=coul, inline=False)
                em.add_field(name="Pseudo", value = str(user.display_name))
                em.add_field(name="ID", value = str(user.id))
                em.set_author(name="Profil de " + str(user), icon_url=user.avatar_url)
                em.set_footer(text="Inscrit(e) le {}".format(self.nob[user.id]["INSCR"]))
                await self.bot.whisper(embed=em)
                await self.bot.whisper("Ce profil est privé et vous n'êtes pas ami avec cette personne, il n'est donc que partiellement affiché.")
        else:
            await self.bot.whisper("L'utilisateur n'est pas inscrit sur Nobody.")


def check_folders():
    if not os.path.exists("data/nobody"):
        print("Creation du dossier Nobody...")
        os.makedirs("data/nobody")

def check_files():
    if not os.path.isfile("data/nobody/nob.json"):
        print("Creation du fichier de comptes Nobody...")
        fileIO("data/nobody/nob.json", "save", {})

    if not os.path.isfile("data/nobody/sys.json"):
        print("Creation du fichier de paramètres nob...")
        fileIO("data/nobody/sys.json", "save", {})

def setup(bot):
    check_folders()
    check_files()
    n = Nobody(bot)
    bot.add_cog(n)            
