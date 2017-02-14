#  Heist was created by Redjumpman for Redbot

# Standard Library
import asyncio
import os
import random
import time
from bisect import bisect
from operator import itemgetter

# Discord / Red Bot
import discord
from discord.ext import commands
from .utils.dataIO import dataIO
from .utils import checks
from __main__ import send_cmd_help

# Third party library requirement
try:
    from tabulate import tabulate
    tabulateAvailable = True
except ImportError:
    tabulateAvailable = False

good = [["{} prépare la voiture, prêt à partir +25 points.", 25],
        ["{} coupe le courant +50 points.", 50],
        ["{} se sert d'un Jean-hacker pour ouvrir un coffre +50 points.", 50],
        ["{} efface l'enregistrement vidéo +50 points", 50],
        ["{} hack le systeme de sécurité et remplace la vidéo par Vitas - The 7th element +75 points", 75],
        ["{} tue le garde qui tentait d'appuyer sur l'alarme +50 points", 50],
        ["{} assome le garde de sécurité +50 points", 50],
        ["{} a préféré ammener un camion plutôt qu'une vieille volvo +50 points", 50],
        ["{} a tué un random qui tentait de faire le héros +50 points", 50],
        ["{} a réussit à forcer la police a livrer une pizza pour tout le monde +25 points", 25],
        ["{} a acheté des masques pour cacher son identité +25 points", 25],
        ["{} trouve la porte de derrière +25 points", 25],
        ["{} s'est entrainé sur Payday 2 +25 points", 25],
        ["{} s'est entrainé sur GTAV +25 points", 25],
        ["{} a ammené des munitions supplémentaires pour le crew +25 points", 25],
        ["{} perce le coffre comme dans du beurre +25 points", 25],
        ["{} garde les otages sous contrôle +25 points", 25],
        ["{} lance de pierres sur les policiers +25 points", 25],
        ["{} apporte des explosifs pour la porte +50 points", 50],
        ["{} campe comme un kikoo-callof sur le toît +100 points", 100],
        ["{} distrait le garde en se déshabillant devant la caméra +25 points", 25],
        ["{} a pris du café pour le crew +25 points", 25],
        ["{} agite les bras pour faire peur aux enfants +25 points", 25],
        ["{} s'équipe du baton à 250€ pour repousser les policiers +25 points", 25],
        ["{} a infiltré la banque en employé +25 points", 25],
        ["{} se sert d'un enfant cancéreux comme bouclier humain +50 points", 50],
        ["{} distribue des gants pour ne pas laisser ses empreintes +50 points", 50],
        ["{} a mis des gants, lui. +50 points", 50],
        ["{} trouve une boite de diamants sur un civil +75 points", 75]]

bad = [["Un tir à eu lieu avec la police locale et {0} est touché...mais survit!", "Saisi"],
       ["La police a retracé les empreintes digitales de {0}.", "Saisi"],
       ["{0} a pensé qu'il pouvait doubler le crew et a payé pour ça.", "Mort"],
       ["{0} explose un pneu en approchant la voiture.", "Saisi"],
       ["Le pistolet de {0} s'est enrayé et la police l'a attrapé.", "Saisi"],
       ["{0} a distrait la police pendant que le reste du crew s'enfuyait.", "Saisi"],
       ["Un otage à distrait le crew et {0} est capturé.", "Saisi"],
       ["{0} est venu au braquage sans aucun outil et il est capturé.", "Saisi"],
       ["Le sac de {0} contenait une cartouche de liquide bleu qui a permis de le retrouver.", "Saisi"],
       ["{0} a été snipé par un homme du GIGN.", "Mort"],
       ["Le crew a décidé d'abandonner {0}.", "Mort"],
       ["Des preuves trouvées chez {0} a permis à la police de le retrouver", "Saisi"],
       ["Le crew a loupé une caméra qui a tout filmé et {0} avait sa face exposée.", "Saisi"],
       ["{0} a oublié par où le crew sortait et s'est retrouvé face à la police.", "Saisi"],
       ["{0} a été touché par un tir allié.", "Mort"],
       ["Un garde poursuit {0} et l'assomme.", "Saisi"],
       ["{0} a accidentellement révélé son identité sur Twitter.", "Saisi"],
       ["Le GIGN lance des gaz soporifiques, {0} dort comme un bébé.", "Saisi"],
       ["'FLASH BANG!', a été la dernière chose que {0} a entendu.", "Saisi"],
       ["'GRENADE !', {0} dort maintenant avec les rats.", "Mort"],
       ["{0} touche un laser de sécurité et se fait saisir.", "Saisi"],
       ["Un des otage a réussi à identifier {0} au poste.", "Saisi"],
       ["Durant la fusillade {0} a été pris de confusion et s'en alla du mauvais côté.", "Saisi"],
       ["{0} a été laissé par le crew à cause de sa jambe blessée.", "Saisi"],
       ["{0} a éternué alors que le crew se cachait de la police.", "Saisi"],
       ["Un garde taze {0}. Il est maintenant en train de baver sur le sol.", "Saisi"],
       ["Le GIGN est passé par l'aération pour appréhender {0}.", "Saisi"]]


# Thanks stack overflow http://stackoverflow.com/questions/21872366/plural-string-formatting
class PluralDict(dict):
    def __missing__(self, key):
        if '(' in key and key.endswith(')'):
            key, rest = key.split('(', 1)
            value = super().__getitem__(key)
            suffix = rest.rstrip(')').split(',')
            if len(suffix) == 1:
                suffix.insert(0, '')
            return suffix[0] if value <= 1 else suffix[1]
        raise KeyError(key)


class Heist:
    """Braquage de banques"""

    def __init__(self, bot):
        self.bot = bot
        self.file_path = "data/JumperCogs/heist/heist.json"
        self.system = dataIO.load_json(self.file_path)
        self.version = "2.0.8.1"
        self.cycle_task = bot.loop.create_task(self.vault_updater())

    @commands.group(pass_context=True, no_pm=True)
    async def payday(self, ctx):
        """Commandes Payday"""

        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @payday.command(name="reset", pass_context=True)
    @checks.admin_or_permissions(manage_server=True)
    async def _reset_heist(self, ctx):
        """Reset du module en cas de problèmes"""
        server = ctx.message.server
        settings = self.check_server_settings(server)
        self.reset_heist(settings)
        await self.bot.say("```Module reset```")

    @payday.command(name="clear", pass_context=True)
    @checks.admin_or_permissions(manage_server=True)
    async def _clear_heist(self, ctx, user: discord.Member):
        """Permet de nettoyer un membre."""
        author = ctx.message.author
        settings = self.check_server_settings(author.server)
        self.user_clear(settings, user)
        await self.bot.say("```{} a nettoyé administrativement {}```".format(author.name, user.name))

    @payday.command(name="version", pass_context=True)
    @checks.admin_or_permissions(manage_server=True)
    async def _version_heist(self, ctx):
        """Montre la version de Payday"""
        await self.bot.say("Payday version {}.".format(self.version))

    @payday.command(name="banks", pass_context=True)
    async def _banks_heist(self, ctx):
        """Montre une liste des banques"""
        server = ctx.message.server
        settings = self.check_server_settings(server)
        if len(settings["Banks"].keys()) < 0:
            msg = ("Aucune banque ! Utilisez {}payday "
                   "createbank .".format(ctx.prefix))
        else:
            bank_names = [x for x in settings["Banks"]]
            crews = [subdict["Crew"] - 1 for subdict in settings["Banks"].values()]
            success = [str(subdict["Success"]) + "%" for subdict in settings["Banks"].values()]
            vaults = [subdict["Vault"] for subdict in settings["Banks"].values()]
            data = list(zip(bank_names, crews, vaults, success))
            table_data = sorted(data, key=itemgetter(1), reverse=True)
            table = tabulate(table_data, headers=["Bank", "Max Crew", "Vault", "Success Rate"])
            msg = "```Python\n{}```".format(table)
        await self.bot.say(msg)

    @payday.command(name="sortie", pass_context=True)
    async def _bailout_heist(self, ctx, user: discord.Member=None):
        """Payer sa caution pour sortir de prison.

        Vous pouvez viser quelqu'un d'autre et payer sa caution."""
        author = ctx.message.author
        server = ctx.message.server
        settings = self.check_server_settings(server)
        self.account_check(settings, author)
        if not user:
            user = author
        if settings["Players"][user.id]["Status"] == "Saisi":
            cost = settings["Players"][user.id]["Bail Cost"]
            if not self.bank_check(settings, user, cost):
                await self.bot.say("Vous n'avez pas assez de crédit pour ça.")
                return

            if user.id == author.id:
                msg = ("Voulez-vous vraiment payer la caution ? Cela vous coutera {}§. Si vous êtes pris "
                       "la prochaine fois la caution va tripler. Voulez-vous toujours le faire ?".format(cost))
            else:
                msg = ("Vous allez payer la caution de {0} et ça vous coutera {1}§. "
                       "Êtes-vous sûr de vouloir payer {1} pour {0}?".format(user.name, cost))

            await self.bot.say(msg)
            response = await self.bot.wait_for_message(timeout=15, author=author)

            if response is None:
                await self.bot.say("Trop long, demande annulée.")
                return

            if response.content.title() == "Oui":
                msg = ("Bravo {} tu es libre ! Profite de la liberté.".format(user.name))
                self.subtract_costs(settings, author, cost)
                print("Author ID :{}\nUser ID :{}".format(author.id, user.id))
                settings["Players"][user.id]["Status"] = "Free"
                settings["Players"][user.id]["OOB"] = True
                dataIO.save_json(self.file_path, self.system)
            elif response.content.title() == "Non":
                msg = "Transaction annulée."
            else:
                msg = "Réponse incorrecte, transaction annulée."
            await self.bot.say(msg)

    @payday.command(name="createbank", pass_context=True)
    @checks.admin_or_permissions(manage_server=True)
    async def _bankadd_heist(self, ctx):
        """Ajoute une banque"""

        author = ctx.message.author
        server = ctx.message.server
        settings = self.check_server_settings(server)
        cancel = ctx.prefix + "cancel"
        check = lambda m: m.content.isdigit() and int(m.content) > 0 or m.content == cancel
        start = ("Vous allez créer une banque. Ce processus peut-être arrêté à tout moment avec {}cancel. Commençons avec la première question.\nQuel est le nom de votre banque ?".format(ctx.prefix))

        await self.bot.say(start)
        name = await self.bot.wait_for_message(timeout=35, author=author)

        if name is None:
            await self.bot.say("Trop long, annulation...")
            return

        if name.content == cancel:
            await self.bot.say("Annulé.")
            return

        if name.content.title() in list(settings["Banks"].keys()):
            await self.bot.say("Ce nom existe déjà.")
            return

        await self.bot.say("Quel est le nombre de personnes maximale dans le Crew ? (Doit être différent des autres banques)")
        crew = await self.bot.wait_for_message(timeout=35, author=author, check=check)

        if crew is None:
            await self.bot.say("Trop long, annulation...")
            return

        if crew.content == cancel:
            await self.bot.say("Création annulée.")
            return

        if int(crew.content) + 1 in [subdict["Crew"] for subdict in settings["Banks"].values()]:
            await self.bot.say("La taille du crew doit être différente d'une autre banque déjà existante.")
            return

        await self.bot.say("Combien de crédits possède cette banque ?")
        vault = await self.bot.wait_for_message(timeout=35, author=author, check=check)

        if vault is None:
            await self.bot.say("Trop long, annulation...")
            return

        if vault.content == cancel:
            await self.bot.say("Création annulée.")
            return

        await self.bot.say("Quel est le max de crédits que la banque peut avoir ?")
        vault_max = await self.bot.wait_for_message(timeout=35, author=author, check=check)

        if vault_max is None:
            await self.bot.say("Trop long, annulation...")
            return

        if vault_max.content == cancel:
            await self.bot.say("Création annulée.")
            return

        await self.bot.say("Quelle est la chance pour chaque individu d'avoir un bonus pour cette banque ?  (1-100)")
        check = lambda m: m.content.isdigit() and 0 < int(m.content) <= 100 or m.content == cancel
        success = await self.bot.wait_for_message(timeout=35, author=author, check=check)

        if success is None:
            await self.bot.say("Trop long, annulation...")
            return

        if success.content == cancel:
            await self.bot.say("Création annulée.")
            return
        else:
            msg = ("Banque créée.\n```Nom:       {}\nCrew:       {}\nCoffre:      {}\nMontant Max:  "
                   "{}\nSuccess:    {}%```".format(name.content.title(), crew.content,
                                                   vault.content, vault_max.content,
                                                   success.content)
                   )
            bank_fmt = {"Crew": int(crew.content) + 1, "Vault": int(vault.content),
                        "Vault Max": int(vault_max.content), "Success": int(success.content)}
            settings["Banks"][name.content.title()] = bank_fmt
            dataIO.save_json(self.file_path, self.system)
            await self.bot.say(msg)

    @payday.command(name="remove", pass_context=True)
    @checks.admin_or_permissions(manage_server=True)
    async def _remove_heist(self, ctx, *, bank: str):
        """Retire une banque de la liste"""
        author = ctx.message.author
        server = ctx.message.server
        settings = self.check_server_settings(server)
        if bank.title() in settings["Banks"].keys():
            await self.bot.say("Êtes-vous sûr de vouloir enlever {} de la liste des banques ?".format(bank.title()))
            response = await self.bot.wait_for_message(timeout=15, author=author)
            if response is None:
                msg = "Trop long, annulation..."
            elif response.content.title() == "Oui":
                settings["Banks"].pop(bank.title())
                dataIO.save_json(self.file_path, self.system)
                msg = "{} a été retiré de la liste.".format(bank.title())
            else:
                msg = "Annulation."
        else:
            msg = "Cette banque n'existe pas."
        await self.bot.say(msg)

    @payday.command(name="info", pass_context=True)
    async def _info_heist(self, ctx):
        """Montre les informations à propors de Payday."""
        server = ctx.message.server
        settings = self.check_server_settings(server)

        if settings["Config"]["Hardcore"]:
            hardcore = "ON"
        else:
            hardcore = "OFF"
        wait = settings["Config"]["Wait Time"]
        heist_cost = settings["Config"]["Heist Cost"]
        bail = settings["Config"]["Bail Base"]
        police = settings["Config"]["Police Alert"]
        sentence = settings["Config"]["Sentence Base"]
        death = settings["Config"]["Death Timer"]
        timers = list(map(self.time_format, [wait, police, sentence, death]))
        description = "{} Paramètres Payday".format(server.name)
        footer = "Payday - Braquage de banque virtuelles."

        embed = discord.Embed(colour=0x0066FF, description=description)
        embed.title = "Payday Version {}".format(self.version)
        embed.add_field(name="Prix", value=heist_cost)
        embed.add_field(name="Caution de base", value=bail)
        embed.add_field(name="Temps de recrutement", value=timers[0])
        embed.add_field(name="Timer de la police", value=timers[1])
        embed.add_field(name="Sentence de prison", value=timers[2])
        embed.add_field(name="Timer de Mort", value=timers[3])
        embed.add_field(name="Hardcore Mode", value=hardcore)
        embed.set_footer(text=footer)

        await self.bot.say(embed=embed)

    @payday.command(name="release", pass_context=True)
    async def _release_heist(self, ctx):
        """Vous retire de la prison."""
        author = ctx.message.author
        server = ctx.message.server
        settings = self.check_server_settings(server)
        self.account_check(settings, author)
        player_time = settings["Players"][author.id]["Time Served"]
        base_time = settings["Players"][author.id]["Sentence"]
        OOB = settings["Players"][author.id]["OOB"]

        if settings["Players"][author.id]["Status"] == "Saisi" or OOB:
            remaining = self.cooldown_calculator(settings, player_time, base_time)
            if remaining:
                msg = ("Vous avez toujours du temps sur votre sentence:\n"
                       "```{}```".format(remaining))
            else:
                msg = "C'est bon, vous pouvez sortir !"
                if OOB:
                    msg = "Vous n'avez aucune charge."
                    settings["Players"][author.id]["OOB"] = False
                settings["Players"][author.id]["Sentence"] = 0
                settings["Players"][author.id]["Time Served"] = 0
                settings["Players"][author.id]["Status"] = "Free"
                dataIO.save_json(self.file_path, self.system)
        else:
            msg = "Vous n'êtes pas en prison en fait..."
        await self.bot.say(msg)

    @payday.command(name="revive", pass_context=True)
    async def _revive_heist(self, ctx):
        """Vous fait revenir à la vie !"""
        author = ctx.message.author
        server = ctx.message.server
        settings = self.check_server_settings(server)
        self.account_check(settings, author)
        player_time = settings["Players"][author.id]["Death Timer"]
        base_time = settings["Config"]["Death Timer"]

        if settings["Players"][author.id]["Status"] == "Mort":
            remainder = self.cooldown_calculator(settings, player_time, base_time)
            if not remainder:
                settings["Players"][author.id]["Death Timer"] = 0
                settings["Players"][author.id]["Status"] = "Free"
                dataIO.save_json(self.file_path, self.system)
                msg = "Vous êtes revenus à la vie !"
            else:
                msg = ("Vous ne pouvez pas revivre encore, vous devrez attendre :\n"
                       "```{}```".format(remainder))
        else:
            msg = "You still have a pulse. I can't revive someone who isn't Mort."
        await self.bot.say(msg)

    @payday.command(name="stats", pass_context=True)
    async def _stats_heist(self, ctx):
        """Montre les statistiques Payday"""
        author = ctx.message.author
        server = ctx.message.server
        avatar = ctx.message.author.avatar_url
        settings = self.check_server_settings(server)
        self.account_check(settings, author)

        status = settings["Players"][author.id]["Status"]
        sentence = settings["Players"][author.id]["Sentence"]
        time_served = settings["Players"][author.id]["Time Served"]
        jail_fmt = self.cooldown_calculator(settings, time_served, sentence)
        bail = settings["Players"][author.id]["Bail Cost"]
        jail_counter = settings["Players"][author.id]["Jail Counter"]
        death_timer = settings["Players"][author.id]["Death Timer"]
        base_death_timer = settings["Config"]["Death Timer"]
        death_fmt = self.cooldown_calculator(settings, death_timer, base_death_timer)
        spree = settings["Players"][author.id]["Spree"]
        probation = settings["Players"][author.id]["OOB"]
        total_deaths = settings["Players"][author.id]["Deaths"]
        total_jail = settings["Players"][author.id]["Total Jail"]
        level = settings["Players"][author.id]["Criminal Level"]
        rank = self.criminal_level(level)

        embed = discord.Embed(colour=0x0066FF, description=rank)
        embed.title = author.name
        embed.set_thumbnail(url=avatar)
        embed.add_field(name="Status", value=status)
        embed.add_field(name="Spree", value=spree)
        embed.add_field(name="Coût caution", value=bail)
        embed.add_field(name="Sorties", value=probation)
        embed.add_field(name="Sentence de prison", value=jail_fmt)
        embed.add_field(name="Saisies", value=jail_counter)
        embed.add_field(name="Timer de Mort", value=death_fmt)
        embed.add_field(name="Morts totales", value=total_deaths)
        embed.add_field(name="Total des saisies", value=total_jail)

        await self.bot.say(embed=embed)

    @payday.command(name="play", pass_context=True)
    async def _play_heist(self, ctx):
        """Démarre un braquage"""
        author = ctx.message.author
        server = ctx.message.server
        settings = self.check_server_settings(server)
        cost = settings["Config"]["Heist Cost"]
        wait_time = settings["Config"]["Wait Time"]
        prefix = ctx.prefix
        self.account_check(settings, author)
        outcome, msg = self.requirement_check(settings, prefix, author, cost)

        if not outcome:
            await self.bot.say(msg)
        elif not settings["Config"]["Heist Planned"]:
            self.subtract_costs(settings, author, cost)
            settings["Config"]["Heist Planned"] = True
            settings["Crew"][author.id] = {}
            await self.bot.say("Un braquage est prévu par {}\nLe braquage commence dans {} secondes. Tapez {}payday play pour rejoindre"
                               " son crew.".format(author.name, wait_time, ctx.prefix))
            await asyncio.sleep(wait_time)
            if len(settings["Crew"].keys()) <= 1:
                await self.bot.say("Tu as essayé mais personne veut te suivre...")
                self.reset_heist(settings)
            else:
                crew = len(settings["Crew"])
                target = self.heist_target(settings, crew)
                good_out = good[:]
                bad_out = bad[:]
                settings["Config"]["Heist Start"] = True
                players = [server.get_member(x) for x in list(settings["Crew"])]
                results = self.game_outcomes(settings, good_out, bad_out, players, target)
                await self.bot.say("Recrutement terminé. Chargement...\n*Le braquage commence*\nLe crew a décidé de frapper "
                                   "**{}**.".format(target))
                await asyncio.sleep(3)
                await self.show_results(settings, server, results, target)
                if settings["Crew"]:
                    players = [server.get_member(x) for x in list(settings["Crew"])]
                    data = self.calculate_credits(settings, players, target)
                    headers = ["Criminals", "Credits Stolen", "Bonuses", "Total"]
                    t = tabulate(data, headers=headers)
                    msg = ("Les crédits volés ont étés répartis entre les membres:\n```"
                           "Python\n{}```".format(t))
                else:
                    msg = "Personne n'a réussi. Les gentils ont gagnés"
                await self.bot.say(msg)
                settings["Config"]["Alert"] = int(time.perf_counter())
                self.reset_heist(settings)
                dataIO.save_json(self.file_path, self.system)
        else:
            self.subtract_costs(settings, author, cost)
            settings["Crew"][author.id] = {}
            crew_size = len(settings["Crew"])
            await self.bot.say("{} a rejoint le crew.\n*Nombre de membres: {}*".format(author.name, crew_size))

    @commands.group(pass_context=True, no_pm=True)
    async def setpayday(self, ctx):
        """Change la configuration du module Payday"""

        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @setpayday.command(name="sentence", pass_context=True)
    @checks.admin_or_permissions(manage_server=True)
    async def _sentence_setheist(self, ctx, seconds: int):
        """Change le temps en prison une fois attrapé"""
        server = ctx.message.server
        settings = self.check_server_settings(server)

        if seconds > 0:
            settings["Config"]["Sentence Base"] = seconds
            dataIO.save_json(self.file_path, self.system)
            time_fmt = self.time_format(seconds)
            msg = "Ajustement de la sentence à {}.".format(time_fmt)
        else:
            msg = "Le nombre doit être supérieur à 0."
        await self.bot.say(msg)

    @setpayday.command(name="cost", pass_context=True)
    @checks.admin_or_permissions(manage_server=True)
    async def _cost_setheist(self, ctx, cost: int):
        """Change le prix demandé pour jouer au Jeu"""
        server = ctx.message.server
        settings = self.check_server_settings(server)

        if cost >= 0:
            settings["Config"]["Heist Cost"] = cost
            dataIO.save_json(self.file_path, self.system)
            msg = "Il faut désormais {}§.".format(cost)
        else:
            msg = "Numbre supérieur ou égal à 0."
        await self.bot.say(msg)

    @setpayday.command(name="police", pass_context=True)
    @checks.admin_or_permissions(manage_server=True)
    async def _police_setheist(self, ctx, seconds: int):
        """Change le timer de la police"""
        server = ctx.message.server
        settings = self.check_server_settings(server)

        if seconds > 0:
            settings["Config"]["Police Alert"] = seconds
            dataIO.save_json(self.file_path, self.system)
            time_fmt = self.time_format(seconds)
            msg = "Police alertée pendant {}s.".format(time_fmt)
        else:
            msg = "Le nombre doit être supérieur à 0"
        await self.bot.say(msg)

    @setpayday.command(name="bail", pass_context=True)
    @checks.admin_or_permissions(manage_server=True)
    async def _bail_setheist(self, ctx, cost: int):
        """Change le prix de la caution"""
        server = ctx.message.server
        settings = self.check_server_settings(server)

        if cost >= 0:
            settings["Config"]["Bail Cost"] = cost
            dataIO.save_json(self.file_path, self.system)
            msg = "Ajusté à {}.".format(cost)
        else:
            msg = "Le nombre doit être supérieur ou égal à 0."
        await self.bot.say(msg)

    @setpayday.command(name="death", pass_context=True)
    @checks.admin_or_permissions(manage_server=True)
    async def _death_setheist(self, ctx, seconds: int):
        """Change le nombre de secondes où les joueurs sont morts"""
        server = ctx.message.server
        settings = self.check_server_settings(server)

        if seconds > 0:
            settings["Config"]["Death Timer"] = seconds
            dataIO.save_json(self.file_path, self.system)
            time_fmt = self.time_format(seconds)
            msg = "Timer reglé à {}s.".format(time_fmt)
        else:
            msg = "Nombre supérieur à 0."
        await self.bot.say(msg)

    @setpayday.command(name="hardcore", pass_context=True, hidden=True)
    @checks.admin_or_permissions(manage_server=True)
    async def _hardcore_setheist(self, ctx):
        """Set game to hardcore mode. Deaths will wipe credits and chips."""
        server = ctx.message.server
        settings = self.check_server_settings(server)

        if settings["Config"]["Hardcore"]:
            settings["Config"]["Hardcore"] = False
            msg = "Hardcore mode now OFF."
        else:
            settings["Config"]["Hardcore"] = True
            msg = "Hardcore mode now ON! **Warning** death will result in credit **and chip wipe**."
        dataIO.save_json(self.file_path, self.system)
        await self.bot.say(msg)

    @setpayday.command(name="wait", pass_context=True)
    @checks.admin_or_permissions(manage_server=True)
    async def _wait_setheist(self, ctx, seconds: int):
        """Change la valeur de l'attente pour le recrutement"""
        server = ctx.message.server
        settings = self.check_server_settings(server)

        if seconds > 0:
            settings["Config"]["Wait Time"] = seconds
            dataIO.save_json(self.file_path, self.system)
            time_fmt = self.time_format(seconds)
            msg = "Ajusté à {}s.".format(time_fmt)
        else:
            msg = "Supérieur à 0 ?"
        await self.bot.say(msg)

    async def show_results(self, settings, server, results, target):
        for result in results:
            await self.bot.say(result)
            await asyncio.sleep(5)
        await self.bot.say("**Le braquage est terminé**\nJe vais compter les crédits...")
        await asyncio.sleep(5)

    async def vault_updater(self):
        await self.bot.wait_until_ready()
        try:
            await asyncio.sleep(15)  # Start-up Time
            while True:
                servers = [x.id for x in self.bot.servers if x.id in self.system["Servers"].keys()]
                for serverid in servers:
                    for bank in list(self.system["Servers"][serverid]["Banks"].keys()):
                        vault = self.system["Servers"][serverid]["Banks"][bank]["Vault"]
                        vault_max = self.system["Servers"][serverid]["Banks"][bank]["Vault Max"]
                        if vault < vault_max:
                            increment = min(vault + 45, vault_max)
                            self.system["Servers"][serverid]["Banks"][bank]["Vault"] = increment
                        else:
                            pass
                dataIO.save_json(self.file_path, self.system)
                await asyncio.sleep(120)  # task runs every 120 seconds
        except asyncio.CancelledError:
            pass

    def __unload(self):
        self.cycle_task.cancel()
        self.shutdown_save()
        dataIO.save_json(self.file_path, self.system)

    def calculate_credits(self, settings, players, target):
        names = [player.name for player in players]
        bonuses = [subdict["Bonus"] for subdict in settings["Crew"].values()]
        vault = settings["Banks"][target]["Vault"]
        credits_stolen = int(vault * 0.75 / len(settings["Crew"].keys()))
        stolen_data = [credits_stolen] * len(settings["Crew"].keys())
        total_winnings = [x + y for x, y in zip(stolen_data, bonuses)]
        settings["Banks"][target]["Vault"] -= credits_stolen
        credit_data = list(zip(names, stolen_data, bonuses, total_winnings))
        deposits = list(zip(players, total_winnings))
        self.award_credits(deposits)
        return credit_data

    def game_outcomes(self, settings, good_out, bad_out, players, target):
        success_rate = settings["Banks"][target]["Success"]
        results = []
        for player in players:
            chance = random.randint(1, 100)
            if chance <= success_rate:
                good_thing = random.choice(good_out)
                good_out.remove(good_thing)
                settings["Crew"][player.id] = {"Name": player.name, "Bonus": good_thing[1]}
                settings["Players"][player.id]["Spree"] += 1
                results.append(good_thing[0].format(player.name))
            else:
                bad_thing = random.choice(bad_out)
                dropout_msg = bad_thing[0] + "```\n{0} est hors-jeu.```"
                self.failure_handler(settings, player, bad_thing[1])
                settings["Crew"].pop(player.id)
                bad_out.remove(bad_thing)
                results.append(dropout_msg.format(player.name))
        dataIO.save_json(self.file_path, self.system)
        return results

    def hardcore_handler(self, settings, user):
        bank = self.bot.get_cog('Economy').bank
        balance = bank.get_balance(user)
        bank.withdraw_credits(user, balance)
        try:
            casino = self.bot.get_cog('Casino')
            chip_balance = casino.chip_balance(user)
            casino.withdraw_chips(user, chip_balance)
        except AttributeError:
            print("Module Casino non chargé.")

    def failure_handler(self, settings, user, status):
        settings["Players"][user.id]["Spree"] = 0

        if status == "Saisi":
            settings["Players"][user.id]["Jail Counter"] += 1
            bail_base = settings["Config"]["Bail Base"]
            offenses = settings["Players"][user.id]["Jail Counter"]
            sentence_base = settings["Config"]["Bail Base"]

            sentence = sentence_base * offenses
            bail = bail_base * offenses
            if settings["Players"][user.id]["OOB"]:
                bail = bail * 3

            settings["Players"][user.id]["Status"] = "Saisi"
            settings["Players"][user.id]["Bail Cost"] = bail
            settings["Players"][user.id]["Sentence"] = sentence
            settings["Players"][user.id]["Time Served"] = int(time.perf_counter())
            settings["Players"][user.id]["OOB"] = False
            settings["Players"][user.id]["Total Jail"] += 1
            settings["Players"][user.id]["Criminal Level"] += 1
        else:
            self.run_death(settings, user)

    def heist_target(self, settings, crew):
        groups = sorted([(x, y["Crew"]) for x, y in settings["Banks"].items()], key=itemgetter(1))
        crew_sizes = [x[1] for x in groups]
        breakpoints = [x for x in crew_sizes if x != max(crew_sizes)]
        banks = [x[0] for x in groups]
        return banks[bisect(breakpoints, crew)]

    def run_death(self, settings, user):
        settings["Players"][user.id]["Criminal Level"] = 0
        settings["Players"][user.id]["OOB"] = False
        settings["Players"][user.id]["Bail Cost"] = 0
        settings["Players"][user.id]["Sentence"] = 0
        settings["Players"][user.id]["Status"] = "Mort"
        settings["Players"][user.id]["Deaths"] += 1
        settings["Players"][user.id]["Jail Counter"] = 0
        settings["Players"][user.id]["Death Timer"] = int(time.perf_counter())
        if settings["Config"]["Hardcore"]:
            self.hardcore_handler(settings, user)

    def user_clear(self, settings, user):
        settings["Players"][user.id]["Status"] = "Free"
        settings["Players"][user.id]["Criminal Level"] = 0
        settings["Players"][user.id]["Jail Counter"] = 0
        settings["Players"][user.id]["Death Timer"] = 0
        settings["Players"][user.id]["Bail Cost"] = 0
        settings["Players"][user.id]["Sentence"] = 0
        settings["Players"][user.id]["Time Served"] = 0
        settings["Players"][user.id]["OOB"] = False
        dataIO.save_json(self.file_path, self.system)

    def reset_heist(self, settings):
        settings["Crew"] = {}
        settings["Config"]["Heist Planned"] = False
        settings["Config"]["Heist Start"] = False
        dataIO.save_json(self.file_path, self.system)

    def award_credits(self, deposits):
        for player in deposits:
            bank = self.bot.get_cog('Economy').bank
            bank.deposit_credits(player[0], player[1])

    def subtract_costs(self, settings, author, cost):
        bank = self.bot.get_cog('Economy').bank
        bank.withdraw_credits(author, cost)

    def requirement_check(self, settings, prefix, author, cost):
        (alert, remaining) = self.police_alert(settings)
        if not list(settings["Banks"]):
            msg = ("Aucune banque disponible !")
            return None, msg
        elif settings["Config"]["Heist Start"]:
            msg = ("Un braquage est déjà en cours.")
            return None, msg
        elif author.id in settings["Crew"]:
            msg = "Vous êtes déjà dans le crew."
            return None, msg
        elif settings["Players"][author.id]["Status"] == "Saisi":
            bail = settings["Players"][author.id]["Bail Cost"]
            sentence_raw = settings["Players"][author.id]["Sentence"]
            time_served = settings["Players"][author.id]["Time Served"]
            remaining = self.cooldown_calculator(settings, sentence_raw, time_served)
            sentence = self.time_format(sentence_raw)
            if remaining:
                msg = ("Vous êtes en prison pour {}.\nVous pouvez attendre encore: {} ou payer {} crédits pour régler "
                       "votre caution.".format(sentence, remaining, bail))
            else:
                msg = ("Vous avez terminé votre temps en prison mais vous devez signer votre sortie. Utilisez {}payday release.".format(prefix))
            return None, msg
        elif settings["Players"][author.id]["Status"] == "Mort":
            death_time = settings["Players"][author.id]["Death Timer"]
            base_timer = settings["Config"]["Death Timer"]
            remaining = self.cooldown_calculator(settings, death_time, base_timer)
            if remaining:
                msg = ("Vous êtes mort. Vous revivrez dans:\n{}\nUtilisez la commande {}payday revive quand le timer sera expiré.".format(remaining, prefix))
            else:
                msg = ("Vous pouvez désormais revivre en utilisant {}payday revive.".format(prefix))
            return None, msg
        elif not self.bank_check(settings, author, cost):
            msg = ("Vous n'avez pas assez d'argent pour participer. Vous avez besoin de {} credits pour cela.".format(cost))
            return None, msg
        elif not (alert):
            msg = ("La police est en alerte. Vous devez encore attendre avant de retenter quoi que ce soit.\n"
                   "Temps restant : *{}*".format(remaining))
            return None, msg
        else:
            return "True", ""

    def police_alert(self, settings):
        police_time = settings["Config"]["Police Alert"]
        alert_time = settings["Config"]["Alert Time"]
        if settings["Config"]["Alert Time"] == 0:
            return "True", None
        elif abs(alert_time - int(time.perf_counter())) >= police_time:
            settings["Config"]["Alert Time"] == 0
            dataIO.save_json(self.file_path, self.system)
            return "True", None
        else:
            s = abs(alert_time - int(time.perf_counter()))
            seconds = abs(s - police_time)
            amount = self.time_format(seconds)
            return None, amount

    def shutdown_save(self):
        for server in self.system["Servers"]:
            death_time = self.system["Servers"][server]["Config"]["Death Timer"]
            for player in self.system["Servers"][server]["Players"]:
                player_death = self.system["Servers"][server]["Players"][player]["Death Timer"]
                player_sentence = self.system["Servers"][server]["Players"][player]["Time Served"]
                sentence = self.system["Servers"][server]["Players"][player]["Sentence"]

                if player_death > 0:
                    s = abs(player_death - int(time.perf_counter()))
                    seconds = abs(s - death_time)
                    self.system["Servers"][server]["Players"][player]["Death Timer"] = seconds

                if player_sentence > 0:
                    s = abs(player_sentence - int(time.perf_counter()))
                    seconds = abs(s - sentence)
                    self.system["Servers"][server]["Players"][player]["Time Served"] = seconds

    def cooldown_calculator(self, settings, player_time, base_time):
        if abs(player_time - int(time.perf_counter())) >= base_time:
            return None
        else:
            s = abs(player_time - int(time.perf_counter()))
            seconds = abs(s - base_time)
            time_remaining = self.time_format(seconds)
            return time_remaining

    def time_format(self, seconds):
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        data = PluralDict({'hour': h, 'minute': m, 'second': s})
        if h > 0:
            fmt = "{hour} hour{hour(s)}"
            if data["minute"] > 0 and data["second"] > 0:
                fmt += ", {minute} minute{minute(s)}, et {second} secondes{second(s)}"
            if data["second"] > 0 == data["minute"]:
                fmt += ", and {second} second{second(s)}"
            msg = fmt.format_map(data)
        elif h == 0 and m > 0:
            if data["second"] == 0:
                fmt = "{minute} minute{minute(s)}"
            else:
                fmt = "{minute} minute{minute(s)}, et {second} secondes{second(s)}"
            msg = fmt.format_map(data)
        elif m == 0 and h == 0 and s > 0:
            fmt = "{second} second{second(s)}"
            msg = fmt.format_map(data)
        elif m == 0 and h == 0 and s == 0:
            msg = "Aucun cooldown"
        return msg

    def bank_check(self, settings, user, amount):
        bank = self.bot.get_cog('Economy').bank
        amount = settings["Config"]["Heist Cost"]
        if bank.account_exists(user):
            if bank.can_spend(user, amount):
                return True
            else:
                return False
        else:
            return False

    def criminal_level(self, level):
        status = ["Innocent", "Bank Robber", "Notorious", "Serial", "Most Wanted",
                  "Criminal Mastermind"]
        breakpoints = [1, 10, 25, 50, 100]
        return status[bisect(breakpoints, level)]

    def account_check(self, settings, author):
        if author.id not in settings["Players"]:
            criminal = {"Name": author.name, "Status": "Free", "Sentence": 0, "Time Served": 0,
                        "Death Timer": 0, "OOB": False, "Bail Cost": 0, "Jail Counter": 0,
                        "Spree": 0, "Criminal Level": 0, "Total Jail": 0, "Deaths": 0}
            settings["Players"][author.id] = criminal
            dataIO.save_json(self.file_path, self.system)
        else:
            pass

    def check_server_settings(self, server):
        if server.id not in self.system["Servers"]:
            default = {"Config": {"Heist Start": False, "Heist Planned": False, "Heist Cost": 100,
                                  "Wait Time": 20, "Hardcore": False, "Police Alert": 60,
                                  "Alert Time": 0, "Sentence Base": 600, "Bail Base": 500,
                                  "Death Timer": 86400},
                       "Players": {},
                       "Crew": {},
                       "Banks": {},
                       }
            self.system["Servers"][server.id] = default
            dataIO.save_json(self.file_path, self.system)
            print("Creating Heist settings for Server: {}".format(server.name))
            path = self.system["Servers"][server.id]
            return path
        else:
            path = self.system["Servers"][server.id]
            return path

    # =========== Commission hooks =====================

    def reaper_hook(self, server, author, user):
        settings = self.check_server_settings(server)
        self.account_check(settings, user)
        if settings["Players"][user.id]["Status"] == "Mort":
            msg = "Sort loupé. {} est mort.".format(user.name)
            action = None
        else:
            self.run_death(settings, user)
            dataIO.save_json(self.file_path, self.system)
            msg = ("{} lance :skull: `death` :skull: sur {} et l'envoie "
                   "au cimetière.".format(author.name, user.name))
            action = "True"
        return action, msg

    def cleric_hook(self, server, author, user):
        settings = self.check_server_settings(server)
        self.account_check(settings, user)
        if settings["Players"][user.id]["Status"] == "Mort":
            settings["Players"][user.id]["Death Timer"] = 0
            settings["Players"][user.id]["Status"] = "Free"
            dataIO.save_json(self.file_path, self.system)
            msg = ("{} lance :trident: `resurrection` :trident: sur {} et le ressucite.".format(author.name, user.name))
            action = "True"
        else:
            msg = "Loupé. {} est en vie.".format(user.name)
            action = None
        return action, msg


def check_folders():
    if not os.path.exists("data/JumperCogs/heist"):
        print("Creating data/JumperCogs/heist folder...")
        os.makedirs("data/JumperCogs/heist")


def check_files():
    default = {"Servers": {}}

    f = "data/JumperCogs/heist/heist.json"
    if not dataIO.is_valid_json(f):
        print("Creating default heist.json...")
        dataIO.save_json(f, default)


def setup(bot):
    check_folders()
    check_files()
    n = Heist(bot)
    if tabulateAvailable:
        bot.add_cog(n)
    else:
        raise RuntimeError("You need to run 'pip3 install tabulate' in command prompt.")
