import discord
from discord.ext import commands
from .utils import checks
import asyncio
import os
import operator
import random
from cogs.utils.dataIO import fileIO, dataIO
from __main__ import send_cmd_help, settings
import time

class Just:
    """Ajoute des fonctionnalités supplémentaires à la modération"""

    def __init__(self, bot):
        self.bot = bot
        self.sys = dataIO.load_json("data/just/sys.json")
        self.reg = dataIO.load_json("data/just/reg.json")
        self.cycle_task = bot.loop.create_task(self.reduce())

    async def reduce(self):
        await self.bot.wait_until_ready()
        try:
            await asyncio.sleep(20)  # Temps de mise en route
            while True:
                for p in self.reg:
                    if self.reg[p]["BANG"] >= 1:
                        self.reg[p]["BANG"] -= 1
                self.save()
                await asyncio.sleep(20)  # Toutes les 24h
        except asyncio.CancelledError:
            pass

    def save(self):
        fileIO("data/just/sys.json", "save", self.sys)
        fileIO("data/just/reg.json", "save", self.reg)
        return True

    def new_event(self, classe, destination, auteur, temps="?"):
        today = time.strftime("%d/%m/%Y", time.localtime())
        if not "HISTORIQUE" in self.sys:
            self.sys["HISTORIQUE"] = []
        self.sys["HISTORIQUE"].append([today, classe, destination, auteur, temps])
        self.save()
        return True

    def convert_sec(self, form: str, val: int):
        if form == "j":
            return val * 86400
        elif form == "h":
            return val * 3600
        elif form == "m":
            return val * 60
        else:
            return val #On considère alors que c'est déjà en secondes

    @commands.command(aliases=["p", "jail"], pass_context=True)
    @checks.admin_or_permissions(manage_messages=True)
    async def prison(self, ctx, user: discord.Member, temps: str = "5m"):
        """Mettre un membre en prison pendant un certain temps (Par défaut 5m).
        
        user = Utilisateur à mettre en prison
        temps = Temps pendant lequel l'utilisateur est en prison (Minimum 60s)
        Format de temps:
        's' pour seconde(s)
        'm' pour minute(s)
        'h' pour heure(s)
        'j' pour jour(s)
        Exemple : &p @membre 5h
        
        Note - Il est possible d'ajouter ou retirer du temps avec '+' et '-' avant le chiffre
        Exemple : &p @membre +10m"""
        server = ctx.message.server
        if temps.isdigit():
            await self.bot.whisper("**N'oubliez pas le format !**\n"
                                   "Formats disponibles : m (minutes), h (heures), j (jours)\n"
                                   "Exemple: &p @membre 5h")
            return
        role = self.sys["ROLE_PRISON"]
        apply = discord.utils.get(ctx.message.server.roles, name=role)
        form = temps[-1:]
        save = user.name
        if temps.startswith("+") or temps.startswith("-"): #Ajouter ou retirer du temps de prison
            val = temps.replace(form, "")
            val = int(val.replace(temps[0], ""))
            if user.id in self.reg:
                if role in [r.name for r in user.roles]:
                    modif = self.convert_sec(form, val)
                    if temps[0] == "+":
                        self.reg[user.id]["FIN_PEINE"] += modif
                        self.new_event("add", user.id, ctx.message.author.id, modif)
                        estim = time.strftime("%H:%M", time.localtime(self.reg[user.id]["FIN_PEINE"]))
                        await self.bot.say("**Ajout de *{}{}* pour *{}* réalisé avec succès.**".format(val, form, user.name))
                        await self.bot.send_message(user, "*{}{}* ont été ajoutés à ta peine par *{}*\nSortie désormais prévue à: `{}`".format(val, form, ctx.message.author.name, estim))
                    elif temps[0] == "-":
                        self.reg[user.id]["FIN_PEINE"] -= modif
                        self.new_event("sub", user.id, ctx.message.author.id, modif)
                        estim = time.strftime("%H:%M", time.localtime(self.reg[user.id]["FIN_PEINE"]))
                        await self.bot.say(
                            "**Retrait de *{}{}* pour *{}* réalisé avec succès.**".format(val, form, user.name))
                        await self.bot.send_message(user,
                                                    "*{}{}* ont été retirés de ta peine par *{}*\nSortie désormais prévue à: `{}`".format(
                                                        val, form, ctx.message.author.name, estim))
                    else:
                        await self.bot.say("Symbole non reconnu. Ajoutez du temps avec '+' et retirez-en avec '-'.")
                        return
                else:
                    await self.bot.say("L'utilisateur n'est pas en prison. Vous ne pouvez donc pas lui ajouter ni retirer du temps de peine.")
                    return
            else:
                await self.bot.say("L'utilisateur n'a jamais été en prison. Vous ne pouvez donc pas lui ajouter ni retirer du temps de peine.")
                return
        else:
            val = int(temps.replace(form, ""))
            sec = self.convert_sec(form, val)
            if sec >= 60: #Au moins une minute
                if sec > 86400:
                    await self.bot.whisper("Il est déconseillé d'utiliser la prison pour une peine dépassant 24h (1j) à cause des instabilités de Discord pouvant causer une peine infinie.")
                if user.id not in self.reg:
                    self.reg[user.id] = {"FIN_PEINE": None,
                                         "DEB_PEINE": None,
                                         "BANG": 0,
                                         "ROLES": [r.name for r in user.roles],
                                         "D_PSEUDO": user.display_name,
                                         "TRACKER": []}
                    self.save()
                if role not in [r.name for r in user.roles]:
                    b_peine = time.time()
                    estim = time.strftime("%H:%M", time.localtime(b_peine + sec))
                    self.reg[user.id]["DEB_PEINE"] = b_peine
                    self.reg[user.id]["FIN_PEINE"] = b_peine + sec
                    self.new_event("in", user.id, ctx.message.author.id, temps)
                    await self.bot.add_roles(user, apply)
                    await self.bot.say("{} **a été mis(e) en prison pendant *{}* par *{}***".format(user.mention, temps, ctx.message.author.name))
                    await self.bot.send_message(user, "**Tu as été mis(e) en prison pendant {}**\nSortie prévue à: `{}`\n"
                                                      "Un salon textuel écrit est disponible sur le serveur afin de contester cette punition ou afin d'obtenir plus d'informations.".format(temps, estim))
                    self.save()
                    try:
                        while time.time() < self.reg[user.id]["FIN_PEINE"] or self.reg[user.id]["FIN_PEINE"] != None:
                            await asyncio.sleep(1)
                    except:
                        pass
                    if user in server.members:
                        if role in [r.name for r in user.roles]:
                            self.reg[user.id]["DEB_PEINE"] = self.reg[user.id]["FIN_PEINE"] = None
                            self.new_event("out", user.id, "auto")
                            await self.bot.remove_roles(user, apply)
                            await self.bot.say("{} **est libre**".format(user.mention))
                            self.save()
                        else:
                            return
                    else:
                        await self.bot.say("{} ne peut être sorti de prison car il n'est plus sur le serveur.".format(save))
                else:
                    self.reg[user.id]["DEB_PEINE"] = self.reg[user.id]["FIN_PEINE"] = None
                    self.new_event("out", user.id, ctx.message.author.id)
                    await self.bot.remove_roles(user, apply)
                    await self.bot.say("{} **a été libéré par *{}***".format(user.mention, ctx.message.author.name))
                    self.save()
            else:
                await self.bot.say("Le temps minimum est de 1m")

    @commands.command(pass_context=True)
    async def niv(self, ctx, user:discord.Member = None):
        """Permet de voir le niveau Bang de quelqu'un ou de soit-même."""
        if user is None:
            user = ctx.message.author
        if user.id in self.reg:
            await self.bot.say("**{}** est au niveau **{}**.".format(user.name, self.reg[user.id]["BANG"]))
        else:
            await self.bot.say("L'utilisateur n'a pas de casier.")

    @commands.command(pass_context=True)
    @checks.admin_or_permissions(administrator=True)
    async def bangp(self, ctx):
        """Permet de régler les punitions affligées par Bangbang.
        
        (Admin seulement)"""
        author = ctx.message.author
        if "BANG_PUN" not in self.sys:
            self.sys["BANG_PUN"] = {"1": {"CLASS": "prison", "REGLAGE": "5m"},
                                    "2": {"CLASS": "prison", "REGLAGE": "1h"},
                                    "3": {"CLASS": "prison", "REGLAGE": "12h"},
                                    "4": {"CLASS": "kick", "REGLAGE": None}}
        while True:
            msg = ""
            for e in self.sys["BANG_PUN"]:
                msg += "**{}** - *{}* {}\n".format(e, self.sys["BANG_PUN"][e]["CLASS"], "({})".format(self.sys["BANG_PUN"][e]["REGLAGE"] if self.sys["BANG_PUN"][e]["REGLAGE"] is not None else ""))
            em = discord.Embed(title="Réglages Bangbang", description=msg, color=0xFE2E2E)
            em.set_footer(text="Tapez le numéro correspondant au niveau de punition pour la modifier (Ignorez pour quitter)")
            m = await self.bot.whisper(embed=em)
            t = False
            while t is False:
                rep = await self.bot.wait_for_message(channel=m.channel, author=author, timeout=30)
                if rep is None:
                    await self.bot.whisper("Timeout atteint - Annulation :wave:")
                    return
                elif rep.content in self.sys["BANG_PUN"]:
                    t = True
                    await self.bot.whisper("**Punitions disponibles :**\n- Prison (De 1m à 1j)\n- Kick\n- Warning (Message de prévention)\n- Retrogradation (de rôle)\n\n"
                                       "Choisissez votre punition en tapant son nom (Ex: 'prison' pour la Prison ou 'kick' pour Kick) ou tapez 'annuler' pour retourner en arrière.")
                    t2 = False
                    while t2 is False:
                        rap = await self.bot.wait_for_message(channel=m.channel, author=author, timeout=30)
                        if rap is None:
                            await self.bot.whisper("Timeout atteint - Annulation :wave:")
                            return
                        elif rap.content.lower() == "prison":
                            t2 = True
                            await self.bot.whisper("Combien de temps ? Formats: s, m, h, j\n*Exemples: 90s, 8m, 10h, 1j...*")
                            t3 = False
                            while t3 is False:
                                rop = await self.bot.wait_for_message(channel=m.channel, author=author, timeout=30)
                                if rop is None:
                                    await self.bot.whisper("Timeout atteint - Annulation :wave:")
                                    return
                                elif len(rop.content) >= 2:
                                    if not rop.content.isdigit():
                                        self.sys["BANG_PUN"][rep.content] = {"CLASS": "prison", "REGLAGE": rop.content.lower()}
                                        self.save()
                                        await self.bot.whisper("Punition réglée avec succès - Retour au menu...")
                                        t3 = True
                                    else:
                                        await self.bot.whisper("Le format n'est pas bon. Lisez bien")
                                else:
                                    await self.bot.whisper("Le format n'est pas bon. Lisez bien")
                        elif rap.content.lower() == "kick":
                            t2 = True
                            self.sys["BANG_PUN"][rep.content] = {"CLASS": "kick", "REGLAGE": None}
                            self.save()
                            await self.bot.whisper("Punition réglée avec succès - Retour au menu...")
                        elif rap.content.lower() == "warning":
                            t2 = True
                            await self.bot.whisper(
                                "Quel message doit être envoyé ? (>5 caractères)")
                            t3 = False
                            while t3 is False:
                                rop = await self.bot.wait_for_message(channel=m.channel, author=author, timeout=30)
                                if rop is None:
                                    await self.bot.whisper("Timeout atteint - Annulation :wave:")
                                    return
                                elif len(rop.content) >= 5:
                                    self.sys["BANG_PUN"][rep.content] = {"CLASS": "warning",
                                                                         "REGLAGE": rop.content}
                                    self.save()
                                    await self.bot.whisper("Punition réglée avec succès - Retour au menu...")
                                    t3 = True
                                else:
                                    await self.bot.whisper("Le format n'est pas bon. Lisez bien")
                        elif rap.content.lower() == "retrogradation":
                            t2 = True
                            await self.bot.whisper(
                                "Il y a t'il des rôles que je ne dois pas retirer ? (Dans ce cas, je retire celui directement en dessous) Sinon tapez 'non'.\n**Format:** role1;role2;role3...\n*Donnez les noms de rôles EXACTS (Majuscule comprise), sinon ça ne fonctionnera pas.*")
                            t3 = False
                            while t3 is False:
                                rop = await self.bot.wait_for_message(channel=m.channel, author=author, timeout=30)
                                if rop is None:
                                    await self.bot.whisper("Timeout atteint - Annulation :wave:")
                                    return
                                elif rop.content.lower() == "non":
                                    self.sys["BANG_PUN"][rep.content] = {"CLASS": "retro",
                                                                         "REGLAGE": []}
                                    self.save()
                                    await self.bot.whisper("Punition réglée avec succès - Retour au menu...")
                                    t3 = True
                                elif len(rop.content.split(";")) > 1:
                                    liste = rop.content.split(";")
                                    self.sys["BANG_PUN"][rep.content] = {"CLASS": "retro",
                                                                         "REGLAGE": liste}
                                    self.save()
                                    await self.bot.whisper("Punition réglée avec succès - Retour au menu...")
                                    t3 = True
                                else:
                                    await self.bot.whisper("Invalide. Lisez bien les directives ci-dessus.")
                        elif rap.content.lower() == "annuler":
                            t2 = True
                        else:
                            await self.bot.whisper("Invalide, réessayez.")
                else:
                    await self.bot.say("Invalide. Tapez le numéro correspondant au niveau que vous voulez modifier.")

    async def renew(self, user):
        server = user.server
        chanp = self.bot.get_channel("204585334925819904")
        role = self.sys["ROLE_PRISON"]
        save = user.name
        apply = discord.utils.get(server.roles, name=role)
        if user.id in self.reg:
            if role not in [r.name for r in user.roles]:
                if self.reg[user.id]["FIN_PEINE"] != None:
                    if self.reg[user.id]["FIN_PEINE"] > time.time():
                        await self.bot.add_roles(user, apply)
                        estim = time.strftime("%H:%M", time.localtime(self.reg[user.id]["FIN_PEINE"]))
                        await self.bot.send_message(chanp, "**{} retourne automatiquement en prison pour finir sa peine**".format(user.name))
                        await self.bot.send_message("**Rappel: Vous aviez été mis en prison et votre peine n'est pas terminée.**\nSortie prévue à: `{}`".format(estim))
                        while time.time() < self.reg[user.id]["FIN_PEINE"] or self.reg[user.id]["FIN_PEINE"] != None:
                            await asyncio.sleep(1)
                        if user in server.members:
                            if role in [r.name for r in user.roles]:
                                self.reg[user.id]["DEB_PEINE"] = self.reg[user.id]["FIN_PEINE"] = None
                                self.new_event("out", user.id, "auto")
                                await self.bot.remove_roles(user, apply)
                                await self.bot.send_message(chanp, "{} **est libre**".format(user.mention))
                                self.save()
                            else:
                                return
                        else:
                            await self.bot.send_message(chanp, "{} ne peut être libéré de prison car il n'est plus sur ce serveur.".format(save))

    async def bang(self, reaction, author):
        user = reaction.message.author
        role = self.sys["ROLE_PRISON"]
        save = user.name
        server = user.server
        chanp = self.bot.get_channel("329071582129422337")
        apply = discord.utils.get(server.roles, name=role)
        if reaction.emoji == "‼":
            if author.server_permissions.manage_messages is True:
                if "BANG_PUN" in self.sys:
                    if user not in self.reg:
                        self.reg[user.id] = {"FIN_PEINE": None,
                                             "DEB_PEINE": None,
                                             "BANG": 0,
                                             "ROLES": [r.name for r in user.roles],
                                             "D_PSEUDO": user.display_name,
                                             "TRACKER": []}
                        self.save()
                    #Début
                    if self.reg[user.id]["BANG"] < 4:
                        self.reg[user.id]["BANG"] += 1
                        self.save()
                    else:
                        await self.bot.send_message(author, "Le membre est déjà au niveau maximal.\n**La punition de niveau 4 est répétée.**")
                    pun = self.sys["BANG_PUN"][str(self.reg[user.id]["BANG"])]["CLASS"]
                    if pun == "prison":
                        if role not in [r.name for r in user.roles]:
                            plus = self.sys["BANG_PUN"][str(self.reg[user.id]["BANG"])]["REGLAGE"]
                            form = plus[-1:]
                            val = int(plus.replace(form, ""))
                            sec = self.convert_sec(form, val)
                            b_peine = time.time()
                            self.reg[user.id]["DEB_PEINE"] = b_peine
                            self.reg[user.id]["FIN_PEINE"] = b_peine + sec
                            self.save()
                            await self.bot.add_roles(user, apply)
                            estim = time.strftime("%H:%M", time.localtime(self.reg[user.id]["FIN_PEINE"]))
                            await self.bot.send_message(chanp,
                                                        "**{} est envoyé en prison pour {} par {}**".format(
                                                            user.name, plus, author.name))
                            await self.bot.send_message(user,
                                "**Vous avez été mis en prison dans le cadre d'une punition.**\nSortie prévue à: `{}`\nUn salon textuel est disponible sur le serveur afin de contester cette décision.".format(
                                    estim))
                            while time.time() < self.reg[user.id]["FIN_PEINE"]:
                                await asyncio.sleep(1)
                            if user in server.members:
                                if role in [r.name for r in user.roles]:
                                    self.reg[user.id]["DEB_PEINE"] = self.reg[user.id]["FIN_PEINE"] = None
                                    self.new_event("out", user.id, "auto")
                                    await self.bot.remove_roles(user, apply)
                                    await self.bot.send_message(chanp, "{} **est libre**".format(user.mention))
                                    self.save()
                                else:
                                    return
                            else:
                                await self.bot.send_message(chanp,
                                                            "{} ne peut être libéré de prison car il n'est plus sur ce serveur.".format(
                                                                save))
                        else:
                            await self.bot.send_message(chanp, "Punition abandonnée - Le membre est déjà en train du purger une peine de prison.")
                            return
                    elif pun == "kick":
                        await self.bot.kick(user)
                        await self.bot.send_message("**{}** a été kick par **{}**".format(save, author.name))
                        return
                    elif pun == "retro":
                        liste = self.sys["BANG_PUN"][str(self.reg[user.id]["BANG"])]["REGLAGE"]
                        roles = [r.name for r in user.roles]
                        roles.remove("@everyone")
                        if roles != []:
                            fait = False
                            num = user.top_role.position
                            while fait is False:
                                if roles[num] in liste:
                                    ret = discord.utils.get(server.roles, name=roles[num])
                                    await self.bot.remove_roles(user, ret)
                                    fait = True
                                else:
                                    num -= 1
                            await self.bot.send_message(chanp, "**{}** à eu son rôle *{}* retiré.".format(user.name, roles[num]))
                            return
                        else:
                            await self.bot.send_message(chanp, "L'utilisateur n'a pas de rôles, il ne peut être rétrogradé.")
                    elif pun == "warning":
                        await self.bot.send_message(chanp, "{} **{}**".format(user.mention, self.sys["BANG_PUN"][str(self.reg[user.id]["BANG"])]["REGLAGE"]))
                    else:
                        pass
                    #TODO Mise en surveillance (Garde)

def check_folders():
    folders = ("data", "data/just/")
    for folder in folders:
        if not os.path.exists(folder):
            print("Création du fichier " + folder)
            os.makedirs(folder)

def check_files():
    default = {"ROLE_PRISON": "Prison"}
    if not os.path.isfile("data/just/reg.json"):
        fileIO("data/just/reg.json", "save", {})
    if not os.path.isfile("data/just/sys.json"):
        fileIO("data/just/sys.json", "save", default)

def setup(bot):
    check_folders()
    check_files()
    n = Just(bot)
    bot.add_listener(n.renew, "on_member_join")
    bot.add_listener(n.bang, "on_reaction_add")
    bot.add_cog(n)