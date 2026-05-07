from enum import Enum
import random

MAX_SKILL_LEVELS = [4, 5, 3, 3, 3]

class Move(Enum):
    PASS = 0
    INCOME = 1
    PLACE = 2
    DISPLACE = 3
    DISPLACE_REMOVE = 4
    DISPLACE_PLACE = 5
    DISPLACE_REPLACE = 6
    MOVE = 7
    MOVE_REMOVE = 8
    MOVE_REPLACE = 9
    CREATE_TRADE_ROUTE = 10
    USE_BONUS_TOKEN = 11
    PLACE_BONUS_TOKEN = 12

class Tradesman(Enum):
    TRADER = 0
    MERCHANT = 1

class BonusToken(Enum):
    ADDITIONAL_POST = 0
    EXCHANGE_POSTS = 1
    MOVE_THREE = 2
    DEVELOP_ABILITY = 3
    THREE_ACTIONS = 4
    FOUR_ACTIONS = 5

class Skill(Enum):
    NONE = 0
    KEYS = 1
    ACTIONS = 2
    PRIVILEGE = 3
    BOOK = 4
    BANK = 5
    COELLEN = 6 # technically not a skill but functionally similar

class CityName(Enum):
    GRONINGEN = 0
    EMDEN = 1
    STADE = 2
    HAMBURG = 3
    LUBECK = 4
    KAMPEN = 5
    OSNABRUCK = 6
    BREMEN = 7
    HANNOVER = 8
    LUNEBURG = 9
    BERLEBERG = 10
    ARNHEIM = 11
    MUNSTER = 12
    MINDEN = 13
    BRUNSWICK = 14
    STENDAL = 15
    DUISBURG = 16
    DORTMUND = 17
    PADERBORN = 18
    HILDESHEIM = 19
    GOSLAR = 20
    MAGDEBURG = 21
    COELLEN = 22
    MARBURG = 23
    GOTTINGEN = 24
    QUEDLINBURG = 25
    HALLE = 26

class Color(Enum):
    WHITE = 0
    ORANGE = 1
    PINK = 2
    BLACK = 3

class BoardState:
    def __init__(self, players, initialState):
        self.players = players
        self.activePlayer = 0
        self.completedCities = 0
        self.cities = []
        self.routes = []
        self.currentAction = Move.PASS
        self.bonusTokens = []
        self.isOver = False
        self.printingEnabled = True # todo
        if initialState:
            self.setup()

    def makeMove(self, move):
        if self.currentAction == Move.PASS:
            self.players[self.activePlayer].actions -= 1
            if move[0] == Move.INCOME:
                self.players[self.activePlayer].income(self.getIncomeAmount(self.players[self.activePlayer].skills[4]))
            elif move[0] == Move.CREATE_TRADE_ROUTE:
                # todo: score and claim bonus tokens
                self.currentAction = Move.CREATE_TRADE_ROUTE
            else:
                self.currentAction = move[0]
        else:
            if move[0] == Move.PLACE:
                self.routes[move[2]].placeTradesman(self.activePlayer, move[1])
                self.currentAction = Move.PASS
            elif move[0] == Move.DISPLACE:
                # todo
                pass
            elif move[0] == Move.MOVE_REMOVE:
                self.routes[move[2]].removeTradesman(self.activePlayer, move[1])
                self.players[self.activePlayer].toReplace[move[1]] += 1
                self.players[self.activePlayer].toRemove -= 1
                pass
            elif move[0] == Move.MOVE_REPLACE:
                self.routes[move[2]].placeTradesman(self.activePlayer, move[1])
                self.players[self.activePlayer].toReplace[move[1]] -= 1
                pass
            elif move[0] == Move.CREATE_TRADE_ROUTE:
                # todo: choose whether to make an office, improve skill, or place on coellen
                pass


    def getOptions(self):
        ret = []
        if self.currentAction == Move.PASS:
            # no current action so get options for next action
            # income, place tradesman, displace tradesman, move tradesmen, create trade route
            if self.players[self.activePlayer].actions > 0:
                if self.players[self.activePlayer].stock[0] > 0 or self.players[self.activePlayer].stock[1] > 0:
                    ret.append((Move.INCOME, ))
                if self.players[self.activePlayer].supply[0] > 0 or self.players[self.activePlayer].supply[1] > 0:
                    ret.append((Move.PLACE, ))
                    tokensOnRoutes = self.checkOtherTokensOnRoutes()
                    if ((tokensOnRoutes[0] and (self.players[self.activePlayer].supply[0] +
                                               self.players[self.activePlayer].supply[1]) > 1) or
                            (tokensOnRoutes[1] and (self.players[self.activePlayer].supply[0] +
                                                    self.players[self.activePlayer].supply[1] > 2))):
                        ret.append((Move.DISPLACE, ))
                tokensOnRoutes = self.checkSelfTokensOnRoutes()
                if tokensOnRoutes[0] or tokensOnRoutes[1]:
                    ret.append((Move.MOVE, ))
                route = 0
                while route < len(self.routes):
                    if self.routes[route].belongsTo(self.activePlayer):
                        ret.append((Move.CREATE_TRADE_ROUTE, route))
                    route += 1
            for token in self.players[self.activePlayer].unusedBonusTokens:
                if token != BonusToken.ADDITIONAL_POST:
                    ret.append((Move.USE_BONUS_TOKEN, token))
            if len(ret) == 0:
                for token in self.players[self.activePlayer].bonusTokensToPlace:
                    route = 0
                    while route < len(self.routes):
                        if self.canPlaceBonusToken(route):
                            ret.append((Move.PLACE_BONUS_TOKEN, token, route))
                        route += 1
                if len(ret) == 0:
                    # active player has no actions or bonus tokens, move to next player's turn
                    self.activePlayer = (self.activePlayer + 1) % len(self.players)
                    self.players[self.activePlayer].gainActions()
                    return self.getOptions()
            else:
                # allow passing mainly for saving bonus tokens
                ret.append((Move.PASS, ))
        elif self.currentAction == Move.PLACE:
            route = 0
            while route < len(self.routes):
                if self.routes[route].hasSpace():
                    if self.players[self.activePlayer].stock[0] > 0:
                        ret.append((Move.PLACE, Tradesman.TRADER, route))
                    if self.players[self.activePlayer].stock[0] > 1:
                        ret.append((Move.PLACE, Tradesman.MERCHANT, route))
                route += 1
        elif self.currentAction == Move.DISPLACE:
            # todo: first choose a piece to displace (pay necessary amount), then replace with own piece, then displaced player places pieces
            pass
        elif self.currentAction == Move.MOVE:
            if self.players[self.activePlayer].toRemove > 0:
                for route in self.routes:
                    for space in route.spaces:
                        if space[0] == self.activePlayer:
                            ret.append((Move.MOVE_REMOVE, space[1], route))
                    route += 1
            else:
                route = 0
                while route < len(self.routes):
                    if self.routes[route].hasSpace():
                        if self.players[self.activePlayer].toReplace[0] > 0:
                            ret.append((Move.MOVE_REPLACE, Tradesman.TRADER, route))
                        if self.players[self.activePlayer].toReplace[1] > 0:
                            ret.append((Move.MOVE_REPLACE, Tradesman.MERCHANT, route))
                    route += 1
        ret = set(ret) # remove duplicates
        return tuple(ret)

    def getIncomeAmount(self, skillLevel):
        if skillLevel == 0:
            return 3
        if skillLevel == 1:
            return 5
        if skillLevel == 2:
            return 7
        return 99 # all

    def canPlaceBonusToken(self, route):
        if self.routes[route].bonusToken == -1:
            return False
        for space in self.routes[route]:
            if space != -1:
                return False
        return (self.cities[self.routes[route].leftCity].hasEmptyOffice() or
                self.cities[self.routes[route].rightCity].hasEmptyOffice())

    def checkSelfTokensOnRoutes(self):
        # check if there is a trader or merchant belong to the active player on the board
        trader = False
        merchant = False
        for route in self.routes:
            for space in route.spaces:
                if space[0] == self.activePlayer:
                    if space[1] == Tradesman.TRADER:
                        trader = True
                    else:
                        merchant = True
            if trader and merchant:
                return (True, True)
        return (trader, merchant)

    def checkOtherTokensOnRoutes(self):
        # check if there is a trader or merchant belong to a player other than the active player on the board
        trader = False
        merchant = False
        for route in self.routes:
            for space in route.spaces:
                if space[0] != -1 and space[0] != self.activePlayer:
                    if space[1] == Tradesman.TRADER:
                        trader = True
                    else:
                        merchant = True
            if trader and merchant:
                return (True, True)
        return (trader, merchant)

    def getOptionPlayerID(self):
        # return brain of player to move
        # todo: when displacing a player other than the active player needs to move
        return self.activePlayer

    def getOptionPlayer(self):
        # return brain of player to move
        # todo: when displacing a player other than the active player needs to move
        return self.players[self.activePlayer].brain

    def setup(self):
        traders = 5
        for player in self.players:
            player.supply = [traders, 1]
            player.stock = [11 - traders, 0]
            traders += 1
        self.players[self.activePlayer].gainActions()
        # Groningen
        self.cities.append(City(Skill.BOOK, [-1, -1], ((Tradesman.TRADER, Color.WHITE),
                                                       (Tradesman.MERCHANT, Color.ORANGE)), (1, 0)))
        # Emden
        self.cities.append(City(Skill.NONE, [-1, -1], ((Tradesman.MERCHANT, Color.WHITE),
                                                       (Tradesman.TRADER, Color.PINK)), (0, 0)))
        # Stade
        if len(self.players) > 3:
            self.cities.append(City(Skill.PRIVILEGE, [-1],
                                    ((Tradesman.MERCHANT, Color.WHITE), ), (0, )))
        else:
            self.cities.append(City(Skill.PRIVILEGE, [-1],
                                    ((Tradesman.MERCHANT, Color.WHITE), ), (1, )))
        # Hamburg
        self.cities.append(City(Skill.NONE, [-1, -1, -1], ((Tradesman.TRADER, Color.WHITE),
                                                           (Tradesman.TRADER, Color.ORANGE),
                                                           (Tradesman.TRADER, Color.BLACK)), (0, 0, 0)))
        # Lubeck
        self.cities.append(City(Skill.BANK, [-1, -1], ((Tradesman.TRADER, Color.WHITE),
                                                       (Tradesman.TRADER, Color.PINK)), (1, 0)))
        # Kampen
        if len(self.players) > 3:
            self.cities.append(City(Skill.NONE, [-1, -1], ((Tradesman.MERCHANT, Color.ORANGE),
                                                           (Tradesman.TRADER, Color.BLACK)), (0, 0)))
        else:
            self.cities.append(City(Skill.NONE, [-1, -1], ((Tradesman.TRADER, Color.ORANGE),
                                                           (Tradesman.TRADER, Color.BLACK)), (0, 0)))
        # Osnabruck
        self.cities.append(City(Skill.NONE, [-1, -1, -1], ((Tradesman.TRADER, Color.WHITE),
                                                           (Tradesman.TRADER, Color.ORANGE),
                                                           (Tradesman.TRADER, Color.BLACK)), (0, 0, 0)))
        # Bremen
        if len(self.players) > 3:
            self.cities.append(City(Skill.NONE, [-1, -1], ((Tradesman.MERCHANT, Color.WHITE),
                                                           (Tradesman.TRADER, Color.PINK)), (0, 0)))
        else:
            self.cities.append(City(Skill.NONE, [-1], ((Tradesman.TRADER, Color.PINK), ),
                                    (0, )))
        # Hannover
        self.cities.append(City(Skill.NONE, [-1, -1], ((Tradesman.TRADER, Color.WHITE),
                                                       (Tradesman.TRADER, Color.PINK)), (0, 0)))
        # Luneburg
        if len(self.players) > 3:
            self.cities.append(City(Skill.NONE, [-1, -1], ((Tradesman.MERCHANT, Color.ORANGE),
                                                           (Tradesman.TRADER, Color.BLACK)), (0, 0)))
        else:
            self.cities.append(City(Skill.NONE, [-1], ((Tradesman.MERCHANT, Color.WHITE), ),
                                    (0, )))
        # Berleburg
        self.cities.append(City(Skill.NONE, [-1, -1, -1], ((Tradesman.TRADER, Color.WHITE),
                                                           (Tradesman.TRADER, Color.PINK),
                                                           (Tradesman.MERCHANT, Color.BLACK)), (0, 0, 0)))
        # Arnheim
        self.cities.append(City(Skill.NONE, [-1, -1, -1, -1], ((Tradesman.TRADER, Color.WHITE),
                                                           (Tradesman.MERCHANT, Color.WHITE),
                                                           (Tradesman.TRADER, Color.ORANGE),
                                                           (Tradesman.TRADER, Color.PINK)), (0, 0, 0, 0)))
        # Munster
        self.cities.append(City(Skill.NONE, [-1, -1], ((Tradesman.MERCHANT, Color.WHITE),
                                                           (Tradesman.TRADER, Color.ORANGE)), (0, 0)))
        # Minden
        self.cities.append(City(Skill.NONE, [-1, -1, -1, -1], ((Tradesman.TRADER, Color.WHITE),
                                                           (Tradesman.TRADER, Color.ORANGE),
                                                           (Tradesman.TRADER, Color.PINK),
                                                           (Tradesman.TRADER, Color.BLACK)), (0, 0, 0, 0)))
        # Brunswick
        self.cities.append(City(Skill.NONE, [-1], ((Tradesman.TRADER, Color.ORANGE), ),
                                (0, )))
        # Stendal
        self.cities.append(City(Skill.NONE, [-1, -1, -1, -1], ((Tradesman.TRADER, Color.WHITE),
                                                               (Tradesman.MERCHANT, Color.WHITE),
                                                               (Tradesman.TRADER, Color.ORANGE),
                                                               (Tradesman.TRADER, Color.PINK)), (0, 0, 0, 0)))
        # Duisburg
        self.cities.append(City(Skill.NONE, [-1], ((Tradesman.TRADER, Color.WHITE), ),
                                (0, )))
        # Dortmund
        if len(self.players) > 3:
            self.cities.append(City(Skill.NONE, [-1, -1, -1], ((Tradesman.MERCHANT, Color.WHITE),
                                                           (Tradesman.TRADER, Color.ORANGE),
                                                           (Tradesman.TRADER, Color.PINK)), (0, 0, 0)))
        else:
            self.cities.append(City(Skill.NONE, [-1, -1], ((Tradesman.MERCHANT, Color.WHITE),
                                                           (Tradesman.TRADER, Color.ORANGE)), (0, 0)))
        # Paderborn
        self.cities.append(City(Skill.NONE, [-1, -1], ((Tradesman.TRADER, Color.WHITE),
                                                       (Tradesman.MERCHANT, Color.BLACK)), (0, 0)))
        # Hildesheim
        self.cities.append(City(Skill.NONE, [-1, -1], ((Tradesman.TRADER, Color.WHITE),
                                                       (Tradesman.TRADER, Color.BLACK)), (0, 0)))
        # Goslar
        if len(self.players) > 3:
            self.cities.append(City(Skill.NONE, [-1, -1], ((Tradesman.TRADER, Color.WHITE),
                                                           (Tradesman.TRADER, Color.BLACK)), (0, 0)))
        else:
            self.cities.append(City(Skill.NONE, [-1], ((Tradesman.TRADER, Color.WHITE), ),
                                    (0, )))
        # Magdeburg
        self.cities.append(City(Skill.NONE, [-1, -1], ((Tradesman.MERCHANT, Color.WHITE),
                                                       (Tradesman.TRADER, Color.ORANGE)), (0, 0)))
        # Coellen
        self.cities.append(City(Skill.COELLEN, [-1, -1], ((Tradesman.TRADER, Color.WHITE),
                                                       (Tradesman.TRADER, Color.PINK)), (1, 0)))
        # Marburg
        if len(self.players) > 3:
            self.cities.append(City(Skill.NONE, [-1, -1], ((Tradesman.TRADER, Color.ORANGE),
                                                           (Tradesman.TRADER, Color.PINK)), (0, 0)))
        else:
            self.cities.append(City(Skill.NONE, [-1, -1], ((Tradesman.TRADER, Color.ORANGE),
                                                           (Tradesman.TRADER, Color.PINK)), (1, 0)))
        # Gottingen
        if len(self.players) > 3:
            self.cities.append(City(Skill.ACTIONS, [-1, -1, -1], ((Tradesman.TRADER, Color.WHITE),
                                                           (Tradesman.MERCHANT, Color.WHITE),
                                                           (Tradesman.TRADER, Color.PINK)), (0, 0, 0)))
        else:
            self.cities.append(City(Skill.ACTIONS, [-1, -1], ((Tradesman.TRADER, Color.WHITE),
                                                           (Tradesman.TRADER, Color.ORANGE)), (0, 0)))
        # Quedlinburg
        self.cities.append(City(Skill.NONE, [-1, -1], ((Tradesman.MERCHANT, Color.ORANGE),
                                                       (Tradesman.MERCHANT, Color.PINK)), (0, 0)))
        # Halle
        self.cities.append(City(Skill.KEYS, [-1, -1], ((Tradesman.TRADER, Color.WHITE),
                                                       (Tradesman.TRADER, Color.ORANGE)), (1, 0)))
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0]], CityName.GRONINGEN, CityName.EMDEN))
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0], [-1, 0]], CityName.EMDEN, CityName.OSNABRUCK))
        self.routes.append(Route([[-1, 0], [-1, 0]], CityName.KAMPEN, CityName.OSNABRUCK))
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0]], CityName.OSNABRUCK, CityName.BREMEN)) # todo: bonus token here
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0]], CityName.KAMPEN, CityName.ARNHEIM))
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0]], CityName.ARNHEIM, CityName.MUNSTER))
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0]], CityName.ARNHEIM, CityName.DUISBURG))
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0], [-1, 0]], CityName.BREMEN, CityName.HAMBURG))
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0]], CityName.BREMEN, CityName.HANNOVER))
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0]], CityName.BREMEN, CityName.MINDEN))
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0]], CityName.STADE, CityName.HAMBURG))
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0]], CityName.HAMBURG, CityName.LUBECK))
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0], [-1, 0]], CityName.HAMBURG, CityName.LUNEBURG))
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0]], CityName.HANNOVER, CityName.LUNEBURG))
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0]], CityName.MINDEN, CityName.HANNOVER))
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0]], CityName.LUNEBURG, CityName.BERLEBERG)) # todo: bonus token here
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0]], CityName.BERLEBERG, CityName.STENDAL))
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0], [-1, 0]], CityName.MINDEN, CityName.BRUNSWICK))
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0]], CityName.MINDEN, CityName.PADERBORN))
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0], [-1, 0]], CityName.BRUNSWICK, CityName.STENDAL))
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0]], CityName.STENDAL, CityName.MAGDEBURG))
        self.routes.append(Route([[-1, 0], [-1, 0]], CityName.GOSLAR, CityName.MAGDEBURG))
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0], [-1, 0]], CityName.GOSLAR, CityName.QUEDLINBURG))
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0]], CityName.GOTTINGEN, CityName.QUEDLINBURG))
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0], [-1, 0]], CityName.QUEDLINBURG, CityName.HALLE))
        self.routes.append(Route([[-1, 0], [-1, 0]], CityName.DUISBURG, CityName.DORTMUND))
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0]], CityName.DORTMUND, CityName.PADERBORN))
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0]], CityName.PADERBORN, CityName.HILDESHEIM))
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0]], CityName.HILDESHEIM, CityName.GOSLAR)) # todo: bonus token here
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0]], CityName.PADERBORN, CityName.MARBURG))
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0], [-1, 0]], CityName.COELLEN, CityName.MARBURG))
        if len(self.players) > 3:
            self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0]], CityName.EMDEN, CityName.STADE))
            self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0]], CityName.MARBURG, CityName.GOTTINGEN))
        # todo: bonus token pile

    def printBoard(self):
        print(f"active player: {self.activePlayer}")
        print(f"")
        city = 0
        while city < len(self.cities):
            print(f"city: {CityName(city).name}, posts:")
            post = 0
            while post < len(self.cities[city].bonusPosts):
                print(f"bonus post occupied by player {self.cities[city].bonusPosts[post]}", end=", ")
                post += 1
            post = 0
            while post < len(self.cities[city].posts) - 1:
                if self.cities[city].posts[post] == -1:
                    print(f"unoccupied {self.cities[city].postRequirements[post][1].name} "
                          f"{self.cities[city].postRequirements[post][0].name} post", end=", ")
                else:
                    print(f"{self.cities[city].postRequirements[post][1].name} "
                          f"{self.cities[city].postRequirements[post][0].name} post occupied by player "
                          f"{self.cities[city].posts[post]}", end=", ")
                post += 1
            if self.cities[city].posts[post] == -1:
                print(f"unoccupied {self.cities[city].postRequirements[post][1].name} "
                      f"{self.cities[city].postRequirements[post][0].name} post")
            else:
                print(f"{self.cities[city].postRequirements[post][1].name} "
                      f"{self.cities[city].postRequirements[post][0].name} post occupied by player "
                      f"{self.cities[city].posts[post]}")
            city += 1
        route = 0
        while route < len(self.routes):
            print(f"route between {self.routes[route].leftCity.name} and {self.routes[route].rightCity.name}:")
            space = 0
            while space < len(self.routes[route].spaces) - 1:
                if self.routes[route].spaces[space][0] == -1:
                    print(f"unoccupied space", end=", ")
                else:
                    print(f"player {self.routes[route].spaces[space][0]}'s "
                          f"{self.routes[route].spaces[space][1].name}", end=", ")
                space += 1
            if self.routes[route].spaces[space][0] == -1:
                print(f"unoccupied space")
            else:
                print(f"player {self.routes[route].spaces[space][0]}'s {self.routes[route].spaces[space][1].name}")
            route += 1

class Player:
    def __init__(self, brain):
        self.brain = brain
        # keys, actions, privilege, book, money
        self.skills = [0, 0, 0, 0, 0]
        # traders, merchants
        self.supply = [0, 0]
        self.stock = [0, 0]
        self.actions = 0
        self.points = 0
        self.toRemove = 0 # number of pieces that may still be moved with a move action
        self.toReplace = [0, 0] # number of each tradesman type that is being moved by a move action
        self.unusedBonusTokens = []
        self.usedBonusTokens = []
        self.bonusTokensToPlace = [] # place at end of turn

    def gainActions(self):
        # gain a number of actions based on skill level
        self.actions = (self.skills[2] + 1) // 2 + 2

    def income(self, amount):
        while self.stock[1] > 0 and amount > 0:
            self.stock[1] -= 1
            self.supply[1] += 1
            amount -= 1
        while self.stock[0] > 0 and amount > 0:
            self.stock[0] -= 1
            self.supply[0] += 1
            amount -= 1

    def upgradeSkill(self, skill):
        if skill == 3:
            self.supply[1] += 1
        else:
            self.supply[0] += 1
        self.skills[skill] += 1

class City:
    def __init__(self, skill, posts, postRequirements, postPoints):
        self.skill = skill
        self.posts = posts
        self.postRequirements = postRequirements
        self.bonusPosts = []
        self.postPoints = postPoints

class Route:
    def __init__(self, spaces, leftCity, rightCity):
        self.spaces = spaces
        # left/right are mostly to differentiate the two adjacent cities and otherwise arbitrary
        self.leftCity = leftCity
        self.rightCity = rightCity
        self.bonusToken = -1

    def isEmpty(self):
        for space in self.spaces:
            if space[0] != -1:
                return False
        return True

    def hasSpace(self):
        for space in self.spaces:
            if space[0] == -1:
                return True
        return False

    def belongsTo(self, player):
        for space in self.spaces:
            if space[0] != player:
                return False
        return True

    def placeTradesman(self, player, type):
        for space in self.spaces:
            if space[0] == -1:
                space[0] = player
                space[1] = type
                return

    def removeTradesman(self, player, type):
        for space in self.spaces:
            if space[0] == player and space[1] == type:
                space[0] = -1
                # vacancy is just determined by player id so don't need to reset type
                return
