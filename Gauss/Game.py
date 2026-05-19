from enum import Enum
import random

MAX_SKILL_LEVELS = [4, 5, 3, 3, 3]

class Move(Enum):
    PASS = 0
    INCOME = 1
    PLACE = 2
    DISPLACE = 3
    DISPLACE_REMOVE = 4 # remove pieces to pay displace cost
    DISPLACE_PLACE = 5 # place new piece
    DISPLACE_REPLACE = 6 # displaced player places new pieces
    DISPLACE_REPLACE_STOCK = 7
    DISPLACE_REPLACE_SUPPLY = 8
    DISPLACE_REPLACE_PASS = 9
    MOVE = 10
    MOVE_REMOVE = 11 # remove pieces to be moved
    MOVE_REPLACE = 12 # place removed pieces back on board
    CREATE_TRADE_ROUTE = 13
    ESTABLISH_TRADING_POST = 14
    ESTABLISH_BONUS_OFFICE = 15
    IMPROVE_SKILL = 16
    PLACE_ON_COELLEN = 17
    TRADE_ROUTE_NO_BONUS = 18
    USE_BONUS_TOKEN = 19
    PLACE_BONUS_TOKEN = 20

class Tradesman(Enum):
    TRADER = 0
    MERCHANT = 1

class BonusToken(Enum):
    NONE = 0
    ADDITIONAL_POST = 1
    EXCHANGE_POSTS = 2
    MOVE_THREE = 3
    DEVELOP_ABILITY = 4
    THREE_ACTIONS = 5
    FOUR_ACTIONS = 6

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
        self.coellenSpots = [-1, -1, -1, -1]
        self.displaceRoute = 0
        self.displacedPlayer = 0
        self.eastWestConnections = 0 # number of east-west connections which have been completed
        self.currentAction = Move.PASS
        self.bonusTokens = []
        self.bonusTokenOverdraw = False
        self.isOver = False
        self.printingEnabled = True # todo
        if initialState:
            self.setup()

    # todo: somehow routes are filling up which shouldn't happen with the number of pieces available in 2p

    def makeMove(self, move):
        if self.currentAction == Move.PASS:
            self.players[self.activePlayer].actions -= 1
            if move[0] == Move.INCOME:
                self.players[self.activePlayer].income(self.getIncomeAmount(self.players[self.activePlayer].skills[4]))
            elif move[0] == Move.CREATE_TRADE_ROUTE:
                self.displaceRoute = move[1] # reuse displaceRoute for the trade route being created
                controller = self.cities[self.routes[self.displaceRoute].leftCity.value].getController()
                if controller != -1:
                    self.players[controller].gainPoints(1)
                controller = self.cities[self.routes[self.displaceRoute].rightCity.value].getController()
                if controller != -1:
                    self.players[controller].gainPoints(1)
                if self.routes[self.displaceRoute].bonusToken != BonusToken.NONE:
                    self.players[self.activePlayer].unusedBonusTokens.append(self.routes[self.displaceRoute].bonusToken)
                    self.routes[self.displaceRoute].bonusToken = BonusToken.NONE
                    self.drawBonusToken()
                self.currentAction = Move.CREATE_TRADE_ROUTE
            elif move[0] == Move.MOVE:
                self.players[self.activePlayer].toRemove = self.players[self.activePlayer].skills[3] + 2
                self.currentAction = Move.MOVE
            else:
                self.currentAction = move[0]
        else:
            match move[0]:
                case Move.PLACE:
                    self.routes[move[2]].placeTradesman(self.activePlayer, move[1])
                    self.currentAction = Move.PASS
                case Move.DISPLACE:
                    self.players[move[1]].toReplace[move[2].value] += 1
                    self.routes[move[3]].removeTradesman(move[1], move[2])
                    self.players[move[1]].toRemove += 1 + move[2].value
                    self.players[self.activePlayer].toRemove += 1 + move[2].value
                    self.currentAction = Move.DISPLACE_REMOVE
                    self.displaceRoute = move[3]
                    self.displacedPlayer = move[1]
                case Move.DISPLACE_REMOVE:
                    self.players[self.activePlayer].supply[move[1].value] -= 1
                    self.players[self.activePlayer].stock[move[1].value] += 1
                    self.players[self.activePlayer].toRemove -= 1
                    if self.players[self.activePlayer].toRemove == 0:
                        self.currentAction = Move.DISPLACE_PLACE
                case Move.DISPLACE_PLACE:
                    self.players[self.activePlayer].supply[move[1].value] -= 1
                    self.routes[self.displaceRoute].placeTradesman(self.activePlayer, move[1])
                    self.currentAction = Move.DISPLACE_REPLACE
                case Move.DISPLACE_REPLACE:
                    self.routes[move[1]].placeTradesman(self.displacedPlayer, move[2])
                    self.players[self.displacedPlayer].toReplace[move[2].value] -= 1
                    if ((self.players[self.displacedPlayer].toRemove) == 0 and
                            sum(self.players[self.displacedPlayer].toReplace) == 0):
                        self.currentAction = Move.PASS
                case Move.DISPLACE_REPLACE_STOCK:
                    self.players[self.displacedPlayer].stock[move[1].value] -= 1
                    self.players[self.displacedPlayer].toReplace[move[1].value] += 1
                    self.players[self.displacedPlayer].toRemove -= 1
                case Move.DISPLACE_REPLACE_SUPPLY:
                    self.players[self.displacedPlayer].supply[move[1].value] -= 1
                    self.players[self.displacedPlayer].toReplace[move[1].value] += 1
                    self.players[self.displacedPlayer].toRemove -= 1
                case Move.DISPLACE_REPLACE_PASS:
                    self.players[self.displacedPlayer].toRemove = 0
                    self.currentAction = Move.PASS
                case Move.MOVE_REMOVE:
                    if move[1] == Move.PASS:
                        self.players[self.activePlayer].toRemove = 0
                        if sum(self.players[self.activePlayer].toReplace) == 0:
                            self.currentAction = Move.PASS
                    else:
                        self.routes[move[2]].removeTradesman(self.activePlayer, move[1])
                        self.players[self.activePlayer].toReplace[move[1].value] += 1
                        self.players[self.activePlayer].toRemove -= 1
                case Move.MOVE_REPLACE:
                    self.routes[move[2]].placeTradesman(self.activePlayer, move[1])
                    self.players[self.activePlayer].toReplace[move[1].value] -= 1
                    if sum(self.players[self.activePlayer].toReplace) == 0:
                        self.currentAction = Move.PASS
                case Move.ESTABLISH_TRADING_POST:
                    # todo: also need to check for east west connection here
                    # todo: add 1 to completed cities if complete
                    if move[2]:
                        # bonus token
                        self.players[self.activePlayer].useBonusToken(BonusToken.ADDITIONAL_POST)
                        self.cities[move[1].value].fillBonusPost(self.activePlayer)
                        self.routes[self.displaceRoute].removeTrader(self.activePlayer)
                    else:
                        info = self.cities[move[1].value].fillPost(self.activePlayer)
                        self.players[self.activePlayer].gainPoints(info[0])
                        self.routes[self.displaceRoute].removeTradesman(self.activePlayer, info[1])
                    for space in self.routes[self.displaceRoute].spaces:
                        if space[0] == self.activePlayer:
                            if space[1] == Tradesman.TRADER:
                                self.players[self.activePlayer].stock[0] += 1
                            elif space[1] == Tradesman.MERCHANT:
                                self.players[self.activePlayer].stock[0] += 1
                    self.routes[self.displaceRoute].clear()
                    self.currentAction = Move.PASS
                case Move.IMPROVE_SKILL:
                    self.players[self.activePlayer].skills[move[1]] += 1
                    for space in self.routes[self.displaceRoute].spaces:
                        if space[0] == self.activePlayer:
                            if space[1] == Tradesman.TRADER:
                                self.players[self.activePlayer].stock[0] += 1
                            elif space[1] == Tradesman.MERCHANT:
                                self.players[self.activePlayer].stock[0] += 1
                    self.routes[self.displaceRoute].clear()
                    self.currentAction = Move.PASS
                case Move.PLACE_ON_COELLEN:
                    self.coellenSpots[move[1]] = self.activePlayer
                    self.routes[self.displaceRoute].removeTradesman(self.activePlayer, Tradesman.MERCHANT)
                    for space in self.routes[self.displaceRoute].spaces:
                        if space[0] == self.activePlayer:
                            if space[1] == Tradesman.TRADER:
                                self.players[self.activePlayer].stock[0] += 1
                            elif space[1] == Tradesman.MERCHANT:
                                self.players[self.activePlayer].stock[0] += 1
                    self.routes[self.displaceRoute].clear()
                    self.currentAction = Move.PASS
                case Move.TRADE_ROUTE_NO_BONUS:
                    for space in self.routes[self.displaceRoute].spaces:
                        if space[0] == self.activePlayer:
                            if space[1] == Tradesman.TRADER:
                                self.players[self.activePlayer].stock[0] += 1
                            elif space[1] == Tradesman.MERCHANT:
                                self.players[self.activePlayer].stock[0] += 1
                    self.routes[self.displaceRoute].clear()
                    self.currentAction = Move.PASS


    def getOptions(self):
        ret = []
        if self.currentAction == Move.PASS:
            # no current action so get options for next action
            # income, place tradesman, displace tradesman, move tradesmen, create trade route
            if self.players[self.activePlayer].actions > 0:
                if sum(self.players[self.activePlayer].stock) > 0:
                    ret.append((Move.INCOME, ))
                if sum(self.players[self.activePlayer].supply) > 0:
                    if self.spaceOnRoutes():
                        ret.append((Move.PLACE, ))
                    tokensOnRoutes = self.checkOtherTokensOnRoutes()
                    if (tokensOnRoutes[0] and (sum(self.players[self.activePlayer].supply) > 1) or
                            (tokensOnRoutes[1] and (sum(self.players[self.activePlayer].supply) > 2))):
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
                    if self.players[self.activePlayer].supply[0] > 0:
                        ret.append((Move.PLACE, Tradesman.TRADER, route))
                    if self.players[self.activePlayer].supply[0] > 1:
                        ret.append((Move.PLACE, Tradesman.MERCHANT, route))
                route += 1
        elif self.currentAction == Move.DISPLACE:
            route = 0
            while route < len(self.routes):
                for space in self.routes[route].spaces:
                    if space[0] != -1 and space[0] != self.activePlayer:
                        if space[1] == Tradesman.MERCHANT:
                            if sum(self.players[self.activePlayer].supply) > 2:
                                ret.append((Move.DISPLACE, space[0], Tradesman.MERCHANT, route))
                        else:
                            # active player will have at least 2 tradesmen if they were allowed to take this action
                            ret.append((Move.DISPLACE, space[0], Tradesman.TRADER, route))
                route += 1
        elif self.currentAction == Move.DISPLACE_REMOVE:
            # active player must remove pieces from their supply to pay cost
            if self.players[self.activePlayer].supply[0] > 0:
                ret.append((Move.DISPLACE_REMOVE, Tradesman.TRADER))
            if self.players[self.activePlayer].supply[1] > 0:
                ret.append((Move.DISPLACE_REMOVE, Tradesman.MERCHANT))
        elif self.currentAction == Move.DISPLACE_PLACE:
            if self.players[self.activePlayer].supply[0] > 0:
                ret.append((Move.DISPLACE_PLACE, Tradesman.TRADER))
            if self.players[self.activePlayer].supply[1] > 0:
                ret.append((Move.DISPLACE_PLACE, Tradesman.MERCHANT))
        elif self.currentAction == Move.DISPLACE_REPLACE:
            # todo: displacePlayer replaces pieces
            # todo: what if the board is full? should they be allowed to displace?
            # toReplace is pieces that need to be placed, toRemove is number of additional pieces that can be chosen
            if sum(self.players[self.displacedPlayer].toReplace) > 0:
                for route in self.getDisplaceReplaceRoutes(self.displaceRoute):
                    if self.players[self.displacedPlayer].toReplace[0] > 0:
                        ret.append((Move.DISPLACE_REPLACE, route, Tradesman.TRADER))
                    if self.players[self.displacedPlayer].toReplace[1] > 0:
                        ret.append((Move.DISPLACE_REPLACE, route, Tradesman.MERCHANT))
            else:
                if sum(self.players[self.displacedPlayer].stock) > 0:
                    if self.players[self.displacedPlayer].stock[0] > 1:
                        ret.append((Move.DISPLACE_REPLACE_STOCK, Tradesman.TRADER))
                    if self.players[self.displacedPlayer].stock[1] > 1:
                        ret.append((Move.DISPLACE_REPLACE_STOCK, Tradesman.MERCHANT))
                else:
                    if self.players[self.displacedPlayer].stock[0] > 1:
                        ret.append((Move.DISPLACE_REPLACE_SUPPLY, Tradesman.TRADER))
                    if self.players[self.displacedPlayer].stock[1] > 1:
                        ret.append((Move.DISPLACE_REPLACE_SUPPLY, Tradesman.MERCHANT))
                ret.append((Move.DISPLACE_REPLACE_PASS, ))
        elif self.currentAction == Move.MOVE:
            if self.players[self.activePlayer].toRemove > 0:
                route = 0
                while route < len(self.routes):
                    for space in self.routes[route].spaces:
                        if space[0] == self.activePlayer:
                            ret.append((Move.MOVE_REMOVE, space[1], route))
                    route += 1
                ret.append((Move.MOVE_REMOVE, Move.PASS)) # finish choosing pieces to move
            else:
                route = 0
                while route < len(self.routes):
                    if self.routes[route].hasSpace():
                        if self.players[self.activePlayer].toReplace[0] > 0:
                            ret.append((Move.MOVE_REPLACE, Tradesman.TRADER, route))
                        if self.players[self.activePlayer].toReplace[1] > 0:
                            ret.append((Move.MOVE_REPLACE, Tradesman.MERCHANT, route))
                    route += 1
        elif self.currentAction == Move.CREATE_TRADE_ROUTE:
            # if empty post in adjacent city, add establish post (or if bonus token, todo) if possible
            postReqs = self.cities[self.routes[self.displaceRoute].leftCity.value].getPostReqs()
            if (self.routes[self.displaceRoute].hasTradesman(postReqs[0]) and
                    self.players[self.activePlayer].skills[Skill.PRIVILEGE.value - 1] >= postReqs[1].value):
                ret.append((Move.ESTABLISH_TRADING_POST, self.routes[self.displaceRoute].leftCity, False))
            postReqs = self.cities[self.routes[self.displaceRoute].rightCity.value].getPostReqs()
            if (self.routes[self.displaceRoute].hasTradesman(postReqs[0]) and
                    self.players[self.activePlayer].skills[Skill.PRIVILEGE.value - 1] >= postReqs[1].value):
                ret.append((Move.ESTABLISH_TRADING_POST, self.routes[self.displaceRoute].rightCity, False))
            if self.players[self.activePlayer].unusedBonusTokens.__contains__(BonusToken.ADDITIONAL_POST):
                if self.routes[self.displaceRoute].leftCity.getFirstVacantPostPos() != 0:
                    ret.append((Move.ESTABLISH_TRADING_POST, self.routes[self.displaceRoute].leftCity, True))
                if self.routes[self.displaceRoute].rightCity.getFirstVacantPostPos() != 0:
                    ret.append((Move.ESTABLISH_TRADING_POST, self.routes[self.displaceRoute].rightCity, True))
            # if skill city and skill is not max level, add improve skill option
            if 0 < self.cities[self.routes[self.displaceRoute].leftCity.value].skill.value < 6:
                skillID = self.cities[self.routes[self.displaceRoute].leftCity.value].skill.value - 1
                if self.players[self.activePlayer].skills[skillID] < MAX_SKILL_LEVELS[skillID]:
                    ret.append((Move.IMPROVE_SKILL, skillID))
            if 0 < self.cities[self.routes[self.displaceRoute].rightCity.value].skill.value < 6:
                skillID = self.cities[self.routes[self.displaceRoute].rightCity.value].skill.value - 1
                if self.players[self.activePlayer].skills[skillID] < MAX_SKILL_LEVELS[skillID]:
                    ret.append((Move.IMPROVE_SKILL, skillID))
            # if coellen and can place, add place on coellen option
            if ((self.routes[self.displaceRoute].leftCity == CityName.COELLEN or
                    self.routes[self.displaceRoute].rightCity == CityName.COELLEN) and
                    self.routes[self.displaceRoute].hasTradesman(Tradesman.MERCHANT)):
                i = 0
                while i < 4:
                    if self.coellenSpots[i] == -1 and self.players[self.activePlayer].skills[2] >= i:
                        ret.append((Move.PLACE_ON_COELLEN, i))
                    i += 1
            # do nothing option
            ret.append((Move.TRADE_ROUTE_NO_BONUS, ))
        ret = set(ret) # remove duplicates
        return tuple(ret)

    def spaceOnRoutes(self):
        # check if there is space somewhere to place a piece
        for route in self.routes:
            if route.hasSpace():
                return True
        return False

    def getDisplaceReplaceRoutes(self, initialRoute):
        routes = {initialRoute}
        routesWithSpace = []
        while len(routesWithSpace) == 0:
            # add adjacent routes
            for route in routes.copy():
                i = 0
                while i < len(self.routes):
                    if self.adjacent(self.routes[i], self.routes[route]):
                        routes.add(i)
                    i += 1
            # check routes for empty space
            for route in routes:
                if route != initialRoute and self.routes[route].hasSpace():
                    routesWithSpace.append(route)
        return routesWithSpace

    def adjacent(self, route1, route2):
        return (route1.leftCity == route2.leftCity or route1.leftCity == route2.rightCity or
                route1.rightCity == route2.leftCity or route1.rightCity == route2.rightCity)

    def getIncomeAmount(self, skillLevel):
        if skillLevel == 0:
            return 3
        if skillLevel == 1:
            return 5
        if skillLevel == 2:
            return 7
        return 99 # all

    def drawBonusToken(self):
        if len(self.bonusTokens) == 0:
            self.bonusTokenOverdraw = True
            return
        self.players[self.activePlayer].bonusTokensToPlace.append(self.bonusTokens.pop())

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

    def checkGameEnd(self):
        # check if the game should end, should be called at the end of each action that can trigger the conditions (todo?)
        if self.bonusTokenOverdraw or self.completedCities >= 10:
            self.isOver = True
        for player in self.players:
            if player.points >= 20:
                self.isOver = True
                return


    def getOptionPlayerID(self):
        # return brain of player to move
        if self.currentAction == Move.DISPLACE_REPLACE:
            return self.displacedPlayer
        return self.activePlayer

    def getOptionPlayer(self):
        # return brain of player to move
        if self.currentAction == Move.DISPLACE_REPLACE:
            return self.players[self.displacedPlayer].brain
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

    def gainPoints(self, amount):
        self.points += amount

    def useBonusToken(self, token):
        if self.unusedBonusTokens.__contains__(token):
            self.unusedBonusTokens.remove(token)
            self.usedBonusTokens.append(token)

class City:
    def __init__(self, skill, posts, postRequirements, postPoints):
        self.skill = skill
        self.posts = posts
        self.postRequirements = postRequirements
        self.bonusPosts = []
        self.postPoints = postPoints

    def getController(self):
        players = [0, 0, 0, 0, 0]
        for post in self.bonusPosts:
            players[post] += 1
        for post in self.posts:
            if post != -1:
                players[post] += 1
        highest = max(players)
        # return the player with the rightmost post, or -1 if unoccupied
        winner = -1
        for post in self.posts:
            if players[post] == highest:
                winner = post
        return winner

    def getFirstVacantPostPos(self):
        i = 0
        while i < len(self.posts):
            if self.posts[i] == -1:
                return i
            i += 1
        return -1

    def getPostReqs(self):
        pos = self.getFirstVacantPostPos()
        if pos == -1:
            return (-1, -1)
        return self.postRequirements[pos]

    def fillPost(self, player):
        i = 0
        while i < len(self.posts):
            if self.posts[i] == -1:
                self.posts[i] = player
                return (self.postPoints[i], self.postRequirements[i][0])
            i += 1

class Route:
    def __init__(self, spaces, leftCity, rightCity):
        self.spaces = spaces
        # left/right are mostly to differentiate the two adjacent cities and otherwise arbitrary
        self.leftCity = leftCity
        self.rightCity = rightCity
        self.bonusToken = BonusToken.NONE

    def isEmpty(self):
        for space in self.spaces:
            if space[0] != -1:
                return False
        return True

    def clear(self):
        i = 0
        while i < len(self.spaces):
            self.spaces[i] = [-1, 0]
            i += 1

    def hasSpace(self):
        for space in self.spaces:
            if space[0] == -1:
                return True
        return False

    def hasTradesman(self, type):
        for space in self.spaces:
            if space[1] == type:
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

    def removeTrader(self, player):
        # try to remove a trader
        for space in self.spaces:
            if space[0] == player and space[1] == Tradesman.TRADER:
                space[0] = -1
                # vacancy is just determined by player id so don't need to reset type
                return
        # if no traders, remove merchant
        for space in self.spaces:
            if space[0] == player:
                space[0] = -1
                # vacancy is just determined by player id so don't need to reset type
                return

