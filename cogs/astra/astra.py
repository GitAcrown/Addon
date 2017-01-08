import discord
from discord.ext import commands
from .utils import checks
import asyncio
import os
import random
from cogs.utils.dataIO import fileIO, dataIO
from __main__ import send_cmd_help, settings
import time

defaut = {"PRSROLE" : None}

class Astra:
    """Collection d'outils."""

    def __init__(self, bot):
        self.bot = bot
        self.case = dataIO.load_json("data/astra/case.json")
        self.sys = dataIO.load_json("data/astra/sys.json")
        self.logs = dataIO.load_json("data/astra/logs.json")
        self.ddb = dataIO.load_json("data/astra/ddb.json")

    @commands.command(pass_context=True)
    async def signal(self, ctx, user : discord.Member, *raison):
        """Permet de signaler (DDB) un utilisateur à la modération."""
        author = ctx.message.author
        raison = " ".join(raison)
        if user.id not in self.ddb:
            self.ddb[user.id] = []
            for e in self.ddb[user.id]:
                if author.id == e[0]:
                    await self.bot.whisper("Vous avez déjà signalé cet utilisateur.")
                    return
            else:
                self.ddb[user.id].append([author.id, raison])
                fileIO("data/astra/ddb.json", "save", self.ddb)
                await self.bot.whisper("Utilisateur signalé.")
        else:
            for e in self.ddb[user.id]:
                if author.id == e[0]:
                    await self.bot.whisper("Vous avez déjà signalé cet utilisateur.")
                    return
            else:
                self.ddb[user.id].append([author.id, raison])
                fileIO("data/astra/ddb.json", "save", self.ddb)
                await self.bot.whisper("Utilisateur signalé.")

    @commands.group(pass_context=True)
    async def astra(self, ctx):
        """Gestion de ASTRA"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @astra.command(pass_context=True)
    async def suser(self, ctx, *snom):
        """Recherche un utilisateur."""
        server = ctx.message.server
        nom = " ".join(snom).lower()
        nb = 0
        for member in server.members: #On cherche le nombre de résultats [RECHERCHE ALL]
            if nom in member.name or nom in member.display_name:
                nb += 1
        if nb > 0:
            await self.bot.say("**{} Résultat(s)**".format(nb))
            await asyncio.sleep(0.25)
            msg = "**Quel mode voulez-vous utiliser ?**\n"
            msg += "*ALL* - Affiche l'ensemble des résultats\n"
            msg += "*DEB* - Affiche les résultats commençant par votre recherche\n"
            msg += "*FIN* - Affiche les résultats finissant par votre recherche\n"
            msg += "-----------------------\n"
            msg += "*ACTIF* - Affiche seulement les membres actifs\n"
            msg += "*INACT* - Affiche seulement les membres inactifs\n"
            msg += "*ROLE* - Affiche seulement les membres possédant le rôle visé\n"
            msg += "*STR* - Recherche stricte, la case est prise en compte\n"
            msg += "\n" + "**Assemblez les mots clefs ci-dessus pour lancer la recherche...**\n*Note : N'oubliez pas qu'il faut au moins 'ALL','DEB' ou 'FIN' pour démarrer la recherche !*"
            await self.bot.say(msg)
            verif = False
            while verif != True:
                rps = await self.bot.wait_for_message(author = ctx.message.author, channel = ctx.message.channel)
                rps = rps.content.lower()
                if rps != "":
                    
                    if "role" in rps:
                        verif2 = False
                        await self.bot.say("**Mentionne le(s) rôle(s) que tu veux rechercher:**")
                        while verif2 != True:
                            rmsg = await self.bot.wait_for_message(author = ctx.message.author, channel = ctx.message.channel)
                            if rmsg.content != "":
                                rlist = rmsg.role_mentions
                                verif2 = True
                            else:
                                await self.bot.say("Invalide, réessaye !")
                                continue
                                
                    if "str" in rps:
                            nom = " ".join(snom)
                    
                    if "actif" and "inactif" in rps:
                        await self.bot.say("Certains mots clefs ne sont pas compatibles entre eux ! ('ACTIF' et 'INACT' reviennent à 'ALL' !)\nRéessayez.")
                        continue
                    
                    #RECHERCHE
                    verif = True
                    if "all" in rps: #MODE FULL
                        if "actif" in rps: #FULL ACTIF
                            res = "**Voici ce que j'ai trouvé pour [ALL, ACTIF]:**\n"
                            for member in server.members:
                                if nom in member.name or nom in member.display_name:
                                    if member.status is discord.Status.online:
                                        res += "*{}* | {}\n".format(member.display_name, member.mention)
                        elif "inact" in rps: #FULL INACTIF
                            res = "**Voici ce que j'ai trouvé pour [ALL, INACT]:**\n"
                            for member in server.members:
                                if nom in member.name or nom in member.display_name:
                                    if member.status is discord.Status.offline:
                                        res += "*{}* | {}\n".format(member.display_name, member.mention)
                        elif "role" in rps: #FULL ROLE
                            res = "**Voici ce que j'ai trouvé pour [ALL, ROLE] (Avec les rôles spécifiés):**\n"
                            for member in server.members:
                                if nom in member.name or nom in member.display_name:
                                    if self.compare_role(member, rlist):
                                        res += "*{}* | {}\n".format(member.display_name, member.mention)
                        else: #FULL SIMPLE
                            res = "**Voici ce que j'ai trouvé pour [ALL]:**\n"
                            for member in server.members:
                                if nom in member.name or nom in member.display_name:
                                    res += "*{}* | {}\n".format(member.display_name, member.mention)
                        await self.bot.say(res)
                    elif "deb" in rps: #MODE DEBUT
                        r = len(nom)
                        if "actif" in rps: #DEBUT ACTIF
                            res = "**Voici ce que j'ai trouvé pour [DEB, ACTIF]:**\n"
                            for member in server.members:
                                if nom in member.name[:r] or nom in member.display_name[:r]:
                                    if member.status is discord.Status.online:
                                        res += "*{}* | {}\n".format(member.display_name, member.mention)
                        elif "inact" in rps: #DEBUT INACT
                            res = "**Voici ce que j'ai trouvé pour [DEB, INACT]:**\n"
                            for member in server.members:
                                if nom in member.name[:r] or nom in member.display_name[:r]:
                                    if member.status is discord.Status.offline:
                                        res += "*{}* | {}\n".format(member.display_name, member.mention)
                        elif "role" in rps: #DEBUT ROLE
                            res = "**Voici ce que j'ai trouvé pour [DEB, ROLE] (Avec les rôles spécifiés):**\n"
                            for member in server.members:
                                if nom in member.name[:r] or nom in member.display_name[:r]:
                                    if self.compare_role(member, rlist):
                                        res += "*{}* | {}\n".format(member.display_name, member.mention)
                        else: #DEBUT SIMPLE
                            res = "**Voici ce que j'ai trouvé pour [DEB]:**\n"
                            for member in server.members:
                                if nom in member.name[:r] or nom in member.display_name[:r]:
                                    res += "*{}* | {}\n".format(member.display_name, member.mention)
                        await self.bot.say(res)
                    elif "fin" in rps: #MODE FIN
                        r = len(nom)
                        if "actif" in rps: #FIN ACTIF
                            res = "**Voici ce que j'ai trouvé pour [FIN, ACTIF]:**\n"
                            for member in server.members:
                                if nom in member.name[-r:] or nom in member.display_name[-r:]:
                                    if member.status is discord.Status.online:
                                        res += "*{}* | {}\n".format(member.display_name, member.mention)
                        elif "inact" in rps: #FIN INACT
                            res = "**Voici ce que j'ai trouvé pour [FIN, INACT]:**\n"
                            for member in server.members:
                                if nom in member.name[-r:] or nom in member.display_name[-r:]:
                                    if member.status is discord.Status.offline:
                                        res += "*{}* | {}\n".format(member.display_name, member.mention)
                        elif "role" in rps: #FIN ROLE
                            res = "**Voici ce que j'ai trouvé pour [FIN, ROLE] (Avec les rôles spécifiés):**\n"
                            for member in server.members:
                                if nom in member.name[-r:] or nom in member.display_name[-r:]:
                                    if self.compare_role(member, rlist):
                                        res += "*{}* | {}\n".format(member.display_name, member.mention)
                        else: #FIN SIMPLE
                            res = "**Voici ce que j'ai trouvé pour [FIN]:**\n"
                            for member in server.members:
                                if nom in member.name[-r:] or nom in member.display_name[-r:]:
                                    res += "*{}* | {}\n".format(member.display_name, member.mention)
                        await self.bot.say(res)
                    else:
                        await self.bot.say("Votre recherche ne donne aucun résultat. Vérifiez vos mots-clefs.")
                        continue
                else:
                    await self.bot.say("Mettez des mots clefs pour commencer une recherche.")
                    continue



    @astra.group(pass_context=True)
    @checks.mod_or_permissions(kick_members=True)
    async def sin(self, ctx):
        """Collection de commandes Signal"""
        if ctx.invoked_subcommand is None or \
                isinstance(ctx.invoked_subcommand, commands.Group):
            await send_cmd_help(ctx)
            return

    @sin.command(pass_context=True)
    async def box(self, ctx, user : discord.Member = None):
        """Permet de voir les utilisateurs signalés.

        Si l'utilisateur est précisé, permet de voir ses signalements."""
        server = ctx.message.server
        if user is None:
            msg = "**__Utilisateurs signalés :__**\n"
            for u in self.ddb:
                mem = server.get_member(u)
                msg += "- *{}*\n".format(mem.display_name)
            await self.bot.say(msg)
        else:
            if user.id in self.ddb:
                msg = "**__Signalements pour {} :__**\n".format(user.name)
                for p in self.ddb[user.id]:
                    util = server.get_member(p[0])
                    msg += "**{}** | *{}*\n".format(util.name, p[1])
                await self.bot.say(msg)

    @sin.command(pass_context=True)
    async def done(self, ctx, user : discord.Member):
        """Permet d'indiquer qu'un signalement a été pris en compte."""
        if user.id in self.ddb:
            del self.ddb[user.id]
            await self.bot.say("Signalement retiré.")
            fileIO("data/astra/ddb.json", "save", self.ddb)
        else:
            await self.bot.say("Cet utilisateur n'est pas présent.")

    @sin.command(pass_context=True)
    async def clean(self, ctx):
        """Efface l'ensemble des signalements."""
        self.ddb = {}
        fileIO("data/astra/ddb.json", "save", self.ddb)
        await self.bot.say("L'ensemble des signalements ont été supprimés.")

    @astra.command(pass_context=True)
    @checks.mod_or_permissions(administrator=True)
    async def alogs(self, ctx, nombre :int = 10):
        """Permet de voir les X derniers logs ASTRA"""
        msg = "**__LOGS__**\n"
        for cat in self.logs:
            a = 0
            self.logs[cat].reverse()
            for e in self.logs[cat]:
                msg += "**{}** | *{}*\n".format(cat, e)
                a += 1
                if a == nombre:
                    break
                if len(msg) >= 1800:
                    msg += "!!"
        else:
            lmsg = msg.split("!!")
            for msg in lmsg:
                await self.bot.whisper(msg)

    @astra.command(pass_context=True)
    @checks.mod_or_permissions(administrator=True)
    async def wipe(self, ctx, form: str):
        """Permet de supprimer des données.

        Dispo: 'casiers' ou 'logs'"""
        if form == "casiers":
            self.case = {}
            fileIO("data/astra/case.json", "save", self.case)
            await self.bot.say("Casiers supprimés.")
        elif form == "logs":
            self.logs = {}
            fileIO("data/astra/logs.json", "save", self.logs)
            await self.bot.say("Logs supprimés.")
        else:
            await self.bot.say("Catégorie invalide.")

    @astra.command(pass_context=True)
    @checks.mod_or_permissions(kick_members=True)
    async def casier(self, ctx, user : discord.Member):
        """Permet de voir le casier d'un utilisateur."""
        if user.id in self.case:
            msg = "**__Casier de {}__**\n".format(str(user))
            msg += "**Pseudo affiché** *{}*\n".format(user.display_name)
            msg += "**ID** *{}*\n".format(user.id)
            passed = (ctx.message.timestamp - user.joined_at).days
            msg += "**Arrivé il y a** *{} jours*\n".format(passed)
            msg += "**Dernier changement** *{}*\n".format(self.case[user.id]["LOGS_PSD"])
            msg += "**---- Logs ----**\n" + "*Affichage des 10 derniers logs*\n"
            if self.case[user.id]["LOGS_MOD"] != []:
                maxa = len(self.case[user.id]["LOGS_MOD"])
                if maxa > 10:
                    maxa = 10
                a = 0
                liste = self.case[user.id]["LOGS_MOD"]
                liste.reverse()
                for log in liste:
                    msg += "> *{}*\n".format(log)
                    a += 1
                    if a == maxa:
                        break
            else:
                msg += "**Aucun log enregistré**"
            await self.bot.whisper(msg)
        else:
            await self.bot.say("L'utilisateur n'a pas de casier.")

    @astra.group(pass_context=True, no_pm=True)
    @checks.mod_or_permissions(kick_members=True)
    async def prs(self, ctx):
        """Collection de commandes Prison"""
        if ctx.invoked_subcommand is None or \
                isinstance(ctx.invoked_subcommand, commands.Group):
            await send_cmd_help(ctx)
            return

    @prs.command(pass_context=True, hidden=True)
    async def set(self, ctx, role : discord.Role):
        """Réglage du rôle Prison."""
        if self.sys["PRSROLE"] is None:
            self.sys["PRSROLE"] = role.name
            if role.hoist is False:
                await self.bot.say("Je vous conseille de régler ce rôle pour les afficher dans une liste à part.")
            fileIO("data/astra/sys.json", "save", self.sys)
            await self.bot.say("Rôle enregistré.")
        else:
            await self.bot.say("Le rôle {} est déja renseigné. Voulez-vous l'enlver ? (O/N)".format(self.sys["PRSROLE"]))
            rep = await self.bot.wait_for_message(author=author, channel=channel)
            rep = rep.content.lower()
            if rep == "o":
                await self.bot.say("Le rôle à été retiré.")
                self.sys["PRSROLE"] = None
                fileIO("data/astra/sys.json", "save", self.sys)
            elif rep == "n":
                await self.bot.say("Le rôle est conservé.")
            else:
                await self.bot.say("Réponse invalide, le rôle est conservé.")

    @prs.command(pass_context=True)
    async def mod(self, ctx, user : discord.Member, temps: int = 5, mute = None):
        """Ajoute/Enlève une personne en prison.

        Si l'utilisateur visé ne possède pas de casier, en crée un."""
        server = ctx.message.server
        id = user.id
        role = self.sys["PRSROLE"]
        r = discord.utils.get(ctx.message.server.roles, name=role)
        if mute == None:
            mute = False
        else:
            mute = bool(mute)
        if id not in self.case:
            self.case[user.id] = {"ID" : user.id,
                             "LOGS_PSD" : "Pseudo original : {}".format(user.name),
                             "LOGS_MOD" : [],
                             "SORTIE_PRS" : None}
            fileIO("data/astra/case.json", "save", self.case)
        if temps >= 1:
            sec = temps * 60 #Temps en secondes
            now = int(time.time())
            sortie = now + sec
            if role not in [r.name for r in user.roles]:
                await self.bot.add_roles(user, r)
                if mute == True:
                    self.bot.server_voice_state(user, mute=True)
                else:
                    pass
                await self.bot.say("**{}** est désormais en prison pour {} minute(s).".format(user.display_name, temps))
                await self.bot.send_message(user, "Vous êtes désormais en prison pour {} minute(s).\n*Vous avez désormais l'accès au salon #prison pour toute plainte*".format(temps))
                self.case[user.id]["LOGS_MOD"].append("{} - Entrée en prison".format(time.strftime("%d/%m %H:%M")))
                self.add_logs("MOD","{} a mis {} en prison pour {} minute(s).".format(ctx.message.author.name, user.display_name, temps))
                self.case[user.id]["SORTIE_PRS"] = sortie
                fileIO("data/astra/case.json", "save", self.case)
                # \/ Sortie
                await asyncio.sleep(sec) #Attente
                if user in server.members:
                    if role in [r.name for r in user.roles]:
                        await self.bot.remove_roles(user, r)
                        await self.bot.server_voice_state(user, mute=False)
                        await self.bot.say("**{}** est sorti de prison.".format(user.display_name))
                        await self.bot.send_message(user, "Vous êtes désormais libre.")
                        self.case[user.id]["LOGS_MOD"].append("{} - Sortie de prison".format(time.strftime("%d/%m %H:%M")))
                        self.case[user.id]["SORTIE_PRS"] = None
                        fileIO("data/astra/case.json", "save", self.case)
                    else:
                        pass
                else:
                    await self.bot.whisper("L'utilisateur {} était en prison mais a quitté le serveur avant la fin du temps.".format(user.display_name))
                    self.case[user.id]["LOGS_MOD"].append("{} - Sortie de prison (A quitté le serveur)".format(time.strftime("%d/%m %H:%M")))
                    self.case[user.id]["SORTIE_PRS"] = None
            else:
                await self.bot.remove_roles(user, r)
                await self.bot.server_voice_state(user, mute=False)
                await self.bot.say("**{}** a été libéré de la prison.".format(user.display_name))
                await self.bot.send_message(user, "Vous avez été libéré de la prison plus tôt que prévu.")
                self.add_logs("MOD","{} a retiré {} de la prison.".format(ctx.message.author.name, user.display_name))
                self.case[user.id]["LOGS_MOD"].append("{} - Sortie de prison".format(time.strftime("%d/%m %H:%M")))
                self.case[user.id]["SORTIE_PRS"] = None
                fileIO("data/astra/case.json", "save", self.case)
        else:
            await self.bot.say("Le temps doit être de plus d'une minute.")

    @prs.command(pass_context=True)
    async def visite(self, ctx, user : discord.Member, temps: int = 5):
        """Permet de visiter la prison pendant x minute(s).

        Il est possible de sortir l'utilisateur en utilisant la commande 'act' basique."""
        server = ctx.message.server
        id = user.id
        role = self.sys["PRSROLE"]
        r = discord.utils.get(ctx.message.server.roles, name=role)
        mute = False
        if id not in self.case:
            self.case[user.id] = {"ID" : user.id,
                             "LOGS_PSD" : "Pseudo original : {}".format(user.name),
                             "LOGS_MOD" : [],
                             "SORTIE_PRS" : None}
            fileIO("data/astra/case.json", "save", self.case)
        if temps >= 1:
            sec = temps * 60 #Temps en secondes
            now = int(time.time())
            sortie = now + sec
            if role not in [r.name for r in user.roles]:
                await self.bot.add_roles(user, r)
                if mute == True:
                    self.bot.server_voice_state(user, mute=True)
                else:
                    pass
                await self.bot.say("**{}** visite désormais la prison pour {} minute(s).".format(user.display_name, temps))
                await self.bot.send_message(user, "Vous visitez désormais la prison pour {} minute(s).\n*Vous avez désormais l'accès au salon #prison*".format(temps))
                self.case[user.id]["LOGS_MOD"].append("{} - Visite de la prison".format(time.strftime("%d/%m %H:%M")))
                self.add_logs("MOD","{} a mis {} en prison pour {} minute(s) dans le cadre d'une visite.".format(ctx.message.author.name, user.display_name, temps))
                self.case[user.id]["SORTIE_PRS"] = sortie
                fileIO("data/astra/case.json", "save", self.case)
                # \/ Sortie
                await asyncio.sleep(sec) #Attente
                if user in server.members:
                    if role in [r.name for r in user.roles]:
                        await self.bot.remove_roles(user, r)
                        await self.bot.server_voice_state(user, mute=False)
                        await self.bot.say("**{}** est sorti de prison. (Visite)".format(user.display_name))
                        await self.bot.send_message(user, "Vous êtes désormais libre.")
                        self.case[user.id]["LOGS_MOD"].append("{} - Sortie de prison (Visite)".format(time.strftime("%d/%m %H:%M")))
                        self.case[user.id]["SORTIE_PRS"] = None
                        fileIO("data/astra/case.json", "save", self.case)
                    else:
                        pass
                else:
                    await self.bot.whisper("L'utilisateur {} était en visite de la prison mais a quitté le serveur avant la fin du temps.".format(user.display_name))
                    self.case[user.id]["LOGS_MOD"].append("{} - Sortie de prison (Visite) (A quitté le serveur)".format(time.strftime("%d/%m %H:%M")))
                    self.case[user.id]["SORTIE_PRS"] = None
            else:
                await self.bot.remove_roles(user, r)
                await self.bot.server_voice_state(user, mute=False)
                await self.bot.say("**{}** a été libéré de la prison.".format(user.display_name))
                await self.bot.send_message(user, "Vous avez été libéré de la prison plus tôt que prévu. (Visite)")
                self.add_logs("MOD","{} a retiré {} de la prison dans le cadre d'une visite.".format(ctx.message.author.name, user.display_name))
                self.case[user.id]["LOGS_MOD"].append("{} - Sortie de prison (Visite)".format(time.strftime("%d/%m %H:%M")))
                self.case[user.id]["SORTIE_PRS"] = None
                fileIO("data/astra/case.json", "save", self.case)
        else:
            await self.bot.say("Le temps doit être de plus d'une minute.")

    @prs.command(pass_context=True)
    async def list(self, ctx):
        """Liste les utilisateurs en prison."""
        role = self.sys["PRSROLE"]
        server = ctx.message.server
        r = discord.utils.get(ctx.message.server.roles, name=role)
        msg = "**__Utilisateurs en prison :__**\n"
        for user in server.members:
            if role in [r.name for r in user.roles]:
                if user.id in self.case:
                    reste = self.case[id]["SORTIE_PRS"] - int(time.time())
                    reste /= 60
                    reste = int(reste)
                    msg += "**{}** | *{}*\n".format(user.display_name, reste)
                else:
                    pass
            else:
                pass
        else:
            if msg != "**__Utilisateurs en prison :__**\n":
                await self.bot.say(msg)
            else:
                await self.bot.say("Aucun utilisateur en prison.")

    @commands.command(pass_context=True)
    async def rest(self, ctx, user : discord.Member = None):
        """Permet d'avoir une estimation sur le temps restant en prison."""
        role = self.sys["PRSROLE"]
        r = discord.utils.get(ctx.message.server.roles, name=role)
        if user == None:
            user = ctx.message.author
        id = user.id
        if user.id in self.case:
            if role in [r.name for r in user.roles]:
                reste = self.case[id]["SORTIE_PRS"] - int(time.time())
                reste /= 60
                reste = round(reste, 0)
                sortie = time.localtime(self.case[id]["SORTIE_PRS"])
                sortie = time.strftime("%H:%M", sortie)
                await self.bot.say("**{} > Il vous reste approximativement {} minute(s) en prison.**\n*Vous sortirez vers {}.*".format(user.name, reste, sortie))
            else:
                await self.bot.say("L'utilisateur n'est plus en prison.")
        else:
            await self.bot.say("L'utilisateur n'a pas de casier.")

    async def change(self, before, after):
        user = after
        if user.id not in self.case:
            self.case[user.id] = {"ID" : user.id,
                                 "LOGS_PSD" : "Pseudo original : {}".format(user.name),
                                 "LOGS_MOD" : [],
                                 "SORTIE_PRS" : None}
            fileIO("data/astra/case.json", "save", self.case)
            
        if before.display_name != after.display_name:
            self.case[after.id]["LOGS_PSD"] = "{} est devenu {}".format(before.display_name, after.display_name)
            fileIO("data/astra/case.json", "save", self.case)
        else:
            pass

        if before.roles != after.roles:
            if len(before.roles) < len(after.roles):
                self.case[user.id]["LOGS_MOD"].append("{} - Ajout d'un rôle".format(time.strftime("%d/%m %H:%M")))
                fileIO("data/astra/case.json", "save", self.case)
            elif len(before.roles) > len(after.roles):
                self.case[user.id]["LOGS_MOD"].append("{} - Suppression d'un rôle".format(time.strftime("%d/%m %H:%M")))
                fileIO("data/astra/case.json", "save", self.case)
            else:
                self.case[user.id]["LOGS_MOD"].append("{} - Modification d'un rôle".format(time.strftime("%d/%m %H:%M")))
                fileIO("data/astra/case.json", "save", self.case)

    async def ban(self, member):
        if user.id not in self.case:
            self.case[user.id] = {"ID" : user.id,
                                 "LOGS_PSD" : "Pseudo original : {}".format(user.name),
                                 "LOGS_MOD" : [],
                                 "SORTIE_PRS" : None}
            fileIO("data/astra/case.json", "save", self.case)

        self.case[user.id]["LOGS_MOD"].append("{} - Ban".format(time.strftime("%d/%m %H:%M")))
        fileIO("data/astra/case.json", "save", self.case)

    async def unban(self, member):
        if user.id not in self.case:
            self.case[user.id] = {"ID" : user.id,
                                 "LOGS_PSD" : "Pseudo original : {}".format(user.name),
                                 "LOGS_MOD" : [],
                                 "SORTIE_PRS" : None}
            fileIO("data/astra/case.json", "save", self.case)

        self.case[user.id]["LOGS_MOD"].append("{} - Déban".format(time.strftime("%d/%m %H:%M")))
        fileIO("data/astra/case.json", "save", self.case)

    def add_logs(self, categorie, logs):
        t = time.strftime("%d/%m %H:%M")
        logs = t + " - " + logs
        if logs != "":
            if categorie in self.logs:
                self.logs[categorie].append(logs)
                fileIO("data/astra/logs.json", "save", self.logs)
            else:
                self.logs[categorie] = []
                self.logs[categorie].append(logs)
                fileIO("data/astra/logs.json", "save", self.logs)
        else:
            return False

def check_folders():
    folders = ("data", "data/astra/")
    for folder in folders:
        if not os.path.exists(folder):
            print("Création du fichier " + folder)
            os.makedirs(folder)

def check_files():
    if not os.path.isfile("data/astra/sys.json"):
        print("Création du fichier systeme Astra...")
        fileIO("data/astra/sys.json", "save", defaut)

    if not os.path.isfile("data/astra/case.json"):
        print("Création du fichier de données Astra...")
        fileIO("data/astra/case.json", "save", {})

    if not os.path.isfile("data/astra/logs.json"):
        print("Création du fichier de stockage Astra...")
        fileIO("data/astra/logs.json", "save", {})

    if not os.path.isfile("data/astra/ddb.json"):
        print("Création du fichier de signalement Astra...")
        fileIO("data/astra/ddb.json", "save", {})

def setup(bot):
    check_folders()
    check_files()
    n = Astra(bot)
    bot.add_listener(n.change, "on_member_update")
    bot.add_listener(n.ban, "on_member_ban")
    bot.add_listener(n.unban, "on_member_unban")
    bot.add_cog(n)
