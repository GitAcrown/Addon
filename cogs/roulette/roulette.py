# Original par Redjumpman - Modifié
import os
import random
import asyncio
from .utils.dataIO import fileIO
from discord.ext import commands
from .utils import checks
import time
import discord


class Russianroulette:
    """[2 à 6 joueurs] Roulette russe (Adapté à BitKhey)"""

    def __init__(self, bot):
        self.bot = bot
        self.rrgame = fileIO("data/roulette/rrgame.json", "load")

    @commands.command(aliases=["rr"], pass_context=True, no_pm=True)
    async def roulette(self, ctx, bet: int):
        """Roulette russe. Requiert au moins 2 joueurs, 6 max."""
        user = ctx.message.author
        bank = self.bot.get_cog('Mirage').api
        server = ctx.message.server
        if not self.rrgame["System"]["Active"]:
            if bet >= self.rrgame["Config"]["Min Bet"]:
                if self.rrgame["System"]["Player Count"] < 6:
                    if self.enough_points(user, bet):
                        if not self.rrgame["System"]["Roulette Initial"]:
                            bank._sub(user, bet, "Démarrage Roulette")
                            self.rrgame["System"]["Player Count"] += 1
                            self.rrgame["System"]["Pot"] += bet
                            self.rrgame["System"]["Start Bet"] += bet
                            self.rrgame["Players"][user.mention] = {"Name": user.name,
                                                                    "ID": user.id,
                                                                    "Mention": user.mention,
                                                                    "Bet": bet}
                            self.rrgame["System"]["Roulette Initial"] = True
                            fileIO("data/roulette/rrgame.json", "save", self.rrgame)
                            await self.bot.say("**" + user.name + "** commence un jeu de la roulette avec comme offre de départ **" +
                                               str(bet) + " BK**.\n" "La partie commence dans 60s (Max. 5 joueurs)")
                            await asyncio.sleep(60)
                            if self.rrgame["System"]["Player Count"] > 1 and self.rrgame["System"]["Player Count"] < 6:
                                self.rrgame["System"]["Active"] = True
                                await self.bot.say("Je vais mettre des balles dans le revolver.")
                                await asyncio.sleep(3)
                                await self.bot.say("Puis vous vous le passerez jusqu'a que l'un de vous s'explose la tête.")
                                await asyncio.sleep(4)
                                await self.bot.say("Le gagnant est le dernier encore en vie.")
                                await asyncio.sleep(2)
                                await self.bot.say("Bonne chance !")
                                await asyncio.sleep(1)
                                await self.roulette_game(server)
                            elif self.rrgame["System"]["Player Count"] < 2:
                                bank._add(user, bet, "Remboursement partie vide")
                                await self.bot.say("Je suis désolé mais vous êtes seul, ça serait du suicide." + "\n" +
                                                   "Essayez d'abord de vous trouver des amis.")
                                self.system_reset()
                        elif user.mention not in self.rrgame["Players"]:
                            if bet >= self.rrgame["System"]["Start Bet"]:
                                bank._sub(user, bet, "Inscription Roulette")
                                self.rrgame["System"]["Pot"] += bet
                                self.rrgame["System"]["Player Count"] += 1
                                self.rrgame["Players"][user.mention] = {"Name": user.name,
                                                                        "ID": user.id,
                                                                        "Mention": user.mention,
                                                                        "Bet": bet}
                                fileIO("data/roulette/rrgame.json", "save", self.rrgame)
                                players = self.rrgame["System"]["Player Count"]
                                needed_players = 6 - players
                                if self.rrgame["System"]["Player Count"] > 5:
                                    self.rrgame["System"]["Active"] = True
                                    await self.bot.say("Je vais laisser qu'**une seule** balle vidée dans ce revolver.")
                                    await asyncio.sleep(4)
                                    await self.bot.say("Ensuite, vous vous le passerez jusqu'à que l'un de vous "
                                                       "s'explose la tête..")
                                    await asyncio.sleep(5)
                                    await self.bot.say("Le gagnant est le dernier en vie !")
                                    await asyncio.sleep(3)
                                    await self.bot.say("Bonne chance !")
                                    await asyncio.sleep(1)
                                    await self.roulette_game(server)
                                else:
                                    await self.bot.say("**" + user.name + "** a rejoint le cercle des suicidaires.")
                            else:
                                await self.bot.say("Votre offre doit être égale ou supérieure à l'offre de départ.")
                        else:
                            await self.bot.say("Vous êtes déjà dans la session.")
                    else:
                        await self.bot.say("Vous n'avez pas assez d'argent.")
                else:
                    await self.bot.say("Trop de joueurs jouent déjà.")
            else:
                min_bet = self.rrgame["Config"]["Min Bet"]
                await self.bot.say("L'offre doit être supérieure à **{} BK** ".format(min_bet))
        else:
            await self.bot.say("Il y a déjà un jeu en cours.")

    @commands.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(manage_server=True)
    async def rrclear(self):
        """En cas d'urgence seulement."""
        self.system_reset()
        await self.bot.say("Reset avec succès")

    @commands.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(manage_server=True)
    async def rrset(self, ctx, bet: int):
        """Change l'offre de départ demandée"""
        if bet > 0:
            self.rrgame["Config"]["Min Bet"] = bet
            fileIO("data/roulette/rrgame.json", "save", self.rrgame)
            await self.bot.say("Le pari initial est maintenant de " + str(bet))
        else:
            await self.bot.say("J'ai besoin d'un chiffre supérieur à 0.")

    async def roulette_game(self, server):
        i = self.rrgame["System"]["Player Count"]
        players = [subdict for subdict in self.rrgame["Players"]]
        count = len(players)
        turn = 0
        bank = self.bot.get_cog('Mirage').api
        high_noon_heure = int(time.strftime("%H", time.localtime()))
        high_noon_min = int(time.strftime("%M", time.localtime()))
        if high_noon_heure != 12:
            while i > 0:
                if i == 1:
                    mention = [subdict["Mention"] for subdict in self.rrgame["Players"].values()]
                    player_id = [subdict["ID"] for subdict in self.rrgame["Players"].values()]
                    mobj = server.get_member(player_id[0])
                    pot = self.rrgame["System"]["Pot"]
                    await asyncio.sleep(2)
                    await self.bot.say("Bravo " + str(mention[0]) + ". Tu viens de gagner " + str(pot) + "BK !")
                    bank._add(mobj, pot, "Gain Roulette")
                    suc = bank.success(mobj, "Chanceux", "Avoir survécu à 3 parties de suite de Roulette", 1, 3)
                    if suc:
                        await self.bot.say("{} **Succès débloqué** | **{}** - *{}*".format(mobj.mention, suc[0],
                                                                                           suc[1]))
                    self.system_reset()
                    await self.bot.say("**Terminé**")
                    break
                elif i > 1:
                    i = i - 1
                    turn = turn + 1
                    names = [subdict for subdict in self.rrgame["Players"]]
                    count = len(names)
                    await self.roulette_round(count, names, turn, server)
        else:
            if 0 <= high_noon_min <= 15:
                noon_names = []
                for player in players:
                    name = self.rrgame["Players"][player]["Name"]
                    id = self.rrgame["Players"][player]["ID"]
                    mobj = server.get_member(id)
                    noon_names.append(name)
                    suc = bank.success(mobj, "On m'appelle McCree", "Avoir été tué par McCree en Roulette", 1, 1)
                    if suc:
                        await self.bot.say("{} **Succès débloqué** | **{}** - *{}*".format(mobj.mention, suc[0],
                                                                                           suc[1]))
                v = ", ".join(noon_names)
                boom = " **BOOM!** " * i
                await self.bot.say("It's HIGGGHHH NOOOOOONN")
                await asyncio.sleep(1)
                await self.bot.say("**...**")
                await asyncio.sleep(3)
                await self.bot.say(str(boom))
                await asyncio.sleep(1)
                await self.bot.say("`" + str(v) + " ont mordu la poussière." + "`")
                await asyncio.sleep(2)
                await self.bot.say("McCree vous a tué et a pris l'argent...")
                self.system_reset()
                await asyncio.sleep(2)
                await self.bot.say("**Terminé**")

    async def roulette_round(self, count, player_names, turn, server):
        bank = self.bot.get_cog('Mirage').api
        list_names = player_names
        furd = 0
        await self.bot.say("**Manche " + str(turn) + "**")
        await asyncio.sleep(2)
        while furd == 0:
            chance = random.randint(1, count)
            name_mention = random.choice(list_names)
            name = self.rrgame["Players"][name_mention]["Name"]
            id = self.rrgame["Players"][name_mention]["ID"]
            user = server.get_member(id)
            if chance > 1:
                await self.bot.say(str(name) + " presse la détente...")
                await asyncio.sleep(4)
                await self.bot.say("**CLICK!**")
                await asyncio.sleep(2)
                await self.bot.say("`" + str(name) + " a survécu" + "`")
                list_names.remove(name_mention)
                count = count - 1
            elif chance <= 1:
                await self.bot.say(str(name) + " presse la détente...")
                await asyncio.sleep(4)
                await self.bot.say("**BOOM!**")
                await asyncio.sleep(1)
                await self.bot.say(str(name_mention) + " s'explose la tête.")
                await asyncio.sleep(2)
                await self.bot.say("Je vais nettoyer ça...")
                await asyncio.sleep(4)
                await self.bot.say("Continuons...")
                bank.success(user, "Chanceux", "Avoir survécu à 3 parties de suite de Roulette", 0, 3)
                del self.rrgame["Players"][name_mention]
                fileIO("data/roulette/rrgame.json", "save", self.rrgame)
                break

    def enough_points(self, uid, amount):
        bank = self.bot.get_cog('Mirage').api
        if bank.enough(uid, amount):
            return True
        else:
            return False

    def system_reset(self):
        self.rrgame["System"]["Pot"] = 0
        self.rrgame["System"]["Player Count"] = 0
        self.rrgame["System"]["Active"] = False
        self.rrgame["System"]["Roulette Initial"] = False
        self.rrgame["System"]["Start Bet"] = 0
        del self.rrgame["Players"]
        self.rrgame["Players"] = {}
        fileIO("data/roulette/rrgame.json", "save", self.rrgame)
        fileIO("data/roulette/rrgame.json", "save", self.rrgame)


def check_folders():
    if not os.path.exists("data/roulette"):
        print("Creating data/roulette folder...")
        os.makedirs("data/roulette")


def check_files():
    system = {"System": {"Pot": 0,
                         "Active": False,
                         "Start Bet": 0,
                         "Roulette Initial": False,
                         "Player Count": 0},
              "Players": {},
              "Config": {"Min Bet": 50}}

    f = "data/roulette/rrgame.json"
    if not fileIO(f, "check"):
        print("Creating default rrgame.json...")
        fileIO(f, "save", system)
    else:  # consistency check
        current = fileIO(f, "load")
        if current.keys() != system.keys():
            for key in system.keys():
                if key not in current.keys():
                    current[key] = system[key]
                    print("Adding " + str(key) +
                          " field to russian roulette rrgame.json")
            fileIO(f, "save", current)


def setup(bot):
    check_folders()
    check_files()
    n = Russianroulette(bot)
    bot.add_cog(n)