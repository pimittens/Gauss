import copy
import random
from enum import Enum

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
    BONUS_TOKEN_REMOVE = 20
    BONUS_TOKEN_REPLACE = 21
    BONUS_TOKEN_PASS = 22
    PLACE_BONUS_TOKEN = 23

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
        self.lastPlayer = 0
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

    def copyState(self):
        newPlayers = copy.deepcopy(self.players)
        newState = BoardState(newPlayers, False)
        newState.activePlayer = self.activePlayer
        newState.lastPlayer = self.lastPlayer
        newState.completedCities = self.completedCities
        newState.cities = copy.deepcopy(self.cities)
        newState.routes = copy.deepcopy(self.routes)
        newState.coellenSpots = copy.deepcopy(self.coellenSpots)
        newState.displaceRoute = self.displaceRoute
        newState.displacedPlayer = self.displacedPlayer
        newState.eastWestConnections = self.eastWestConnections
        newState.currentAction = self.currentAction
        newState.bonusTokens = copy.deepcopy(self.bonusTokens)
        newState.bonusTokenOverdraw = self.bonusTokenOverdraw
        newState.isOver = self.isOver
        newState.printingEnabled = False
        return newState

    def makeMove(self, move):
        self.lastPlayer = self.getOptionPlayerID()
        if self.currentAction == Move.PASS:
            if move[0] == Move.PLACE_BONUS_TOKEN:
                self.routes[move[2]].bonusToken = move[1]
                self.players[self.activePlayer].bonusTokensToPlace.remove(move[1])
            elif move[0] == Move.USE_BONUS_TOKEN:
                self.players[self.activePlayer].useBonusToken(move[1])
                if move[1] == BonusToken.THREE_ACTIONS:
                    self.players[self.activePlayer].actions += 3
                elif move[1] == BonusToken.FOUR_ACTIONS:
                    self.players[self.activePlayer].actions += 4
                elif move[1] == BonusToken.DEVELOP_ABILITY:
                    self.players[self.activePlayer].skills[move[2]] += 1
                    if move[2] == 3:
                        self.players[self.activePlayer].stock[1] += 1
                    else:
                        self.players[self.activePlayer].stock[0] += 1
                elif move[1] == BonusToken.EXCHANGE_POSTS:
                    self.cities[move[2]].exchangePosts(move[3])
                elif move[1] == BonusToken.MOVE_THREE:
                    self.players[self.activePlayer].toRemove = 3
                    self.currentAction = Move.BONUS_TOKEN_REMOVE
            else:
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
                    self.players[self.activePlayer].supply[move[1].value] -= 1
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
                    if move[2]:
                        # bonus token
                        self.players[self.activePlayer].useBonusToken(BonusToken.ADDITIONAL_POST)
                        self.cities[move[1].value].fillBonusPost(self.activePlayer)
                        self.routes[self.displaceRoute].removeTrader(self.activePlayer)
                    else:
                        info = self.cities[move[1].value].fillPost(self.activePlayer)
                        self.players[self.activePlayer].gainPoints(info[0])
                        self.routes[self.displaceRoute].removeTradesman(self.activePlayer, info[1])
                        if self.cities[move[1].value].isComplete():
                            self.completedCities += 1
                    self.checkEastWestConnection(self.activePlayer)
                    for space in self.routes[self.displaceRoute].spaces:
                        if space[0] == self.activePlayer:
                            if space[1] == Tradesman.TRADER:
                                self.players[self.activePlayer].stock[0] += 1
                            elif space[1] == Tradesman.MERCHANT:
                                self.players[self.activePlayer].stock[0] += 1
                    self.routes[self.displaceRoute].clear()
                    self.currentAction = Move.PASS
                    self.checkGameEnd()
                case Move.IMPROVE_SKILL:
                    self.players[self.activePlayer].skills[move[1]] += 1
                    if move[1] == 1 and self.players[self.activePlayer].skills[move[1]] in [1, 3, 5]:
                        self.players[self.activePlayer].actions += 1
                    if move[1] == 3:
                        self.players[self.activePlayer].supply[1] += 1
                    else:
                        self.players[self.activePlayer].supply[0] += 1
                    for space in self.routes[self.displaceRoute].spaces:
                        if space[0] == self.activePlayer:
                            if space[1] == Tradesman.TRADER:
                                self.players[self.activePlayer].stock[0] += 1
                            elif space[1] == Tradesman.MERCHANT:
                                self.players[self.activePlayer].stock[1] += 1
                    self.routes[self.displaceRoute].clear()
                    self.currentAction = Move.PASS
                    self.checkGameEnd()
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
                    self.checkGameEnd()
                case Move.TRADE_ROUTE_NO_BONUS:
                    for space in self.routes[self.displaceRoute].spaces:
                        if space[0] == self.activePlayer:
                            if space[1] == Tradesman.TRADER:
                                self.players[self.activePlayer].stock[0] += 1
                            elif space[1] == Tradesman.MERCHANT:
                                self.players[self.activePlayer].stock[0] += 1
                    self.routes[self.displaceRoute].clear()
                    self.currentAction = Move.PASS
                    self.checkGameEnd()
                case Move.BONUS_TOKEN_REMOVE:
                    self.players[self.activePlayer].toRemove -= 1
                    self.players[self.activePlayer].oppID = self.routes[move[1]].spaces[move[2]][0]
                    self.players[self.activePlayer].toReplace[self.routes[move[1]].spaces[move[2]][1].value] += 1
                    self.routes[move[1]].spaces[move[2]][0] = -1 # remove piece
                    self.currentAction = Move.BONUS_TOKEN_REPLACE
                case Move.BONUS_TOKEN_REPLACE:
                    if self.players[self.activePlayer].toReplace[0] > 0:
                        self.players[self.activePlayer].toReplace[0] -= 1
                        self.routes[move[1]].placeTradesman(self.players[self.activePlayer].oppID, Tradesman.TRADER)
                    elif self.players[self.activePlayer].toReplace[1] > 0:
                        self.players[self.activePlayer].toReplace[1] -= 1
                        self.routes[move[1]].placeTradesman(self.players[self.activePlayer].oppID, Tradesman.MERCHANT)
                    if self.players[self.activePlayer].toRemove == 0:
                        self.currentAction = Move.PASS
                    else:
                        self.currentAction = Move.BONUS_TOKEN_REMOVE
                case Move.BONUS_TOKEN_PASS:
                    self.players[self.activePlayer].toRemove = 0
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
                for route in range(len(self.routes)):
                    if self.routes[route].belongsTo(self.activePlayer):
                        ret.append((Move.CREATE_TRADE_ROUTE, route))
            # passing with only bonus token options left forces turn end by reducing actions to -1
            if self.players[self.activePlayer].actions > -1:
                for token in self.players[self.activePlayer].unusedBonusTokens:
                    if token != BonusToken.ADDITIONAL_POST:
                        if token == BonusToken.DEVELOP_ABILITY:
                            for skill in range(len(self.players[self.activePlayer].skills)):
                                if self.players[self.activePlayer].skills[skill] < MAX_SKILL_LEVELS[skill]:
                                    ret.append((Move.USE_BONUS_TOKEN, token, skill))
                        elif token == BonusToken.MOVE_THREE:
                            found = False
                            for route in self.routes:
                                for space in route.spaces:
                                    if space[0] != -1 and space[0] != self.activePlayer:
                                        ret.append((Move.USE_BONUS_TOKEN, token))
                                        found = True
                                        break
                                if found:
                                    break
                        elif token == BonusToken.EXCHANGE_POSTS:
                            for city in range(len(self.cities)):
                                posts = self.cities[city].posts
                                for post in range(len(posts) - 1):
                                    if (posts[post] == self.activePlayer and posts[post + 1] != -1 and
                                            posts[post + 1] != self.activePlayer):
                                        ret.append((Move.USE_BONUS_TOKEN, token, city, post))
                        else:
                            ret.append((Move.USE_BONUS_TOKEN, token))
            if len(ret) == 0:
                for token in self.players[self.activePlayer].bonusTokensToPlace:
                    for route in range(len(self.routes)):
                        if self.canPlaceBonusToken(route):
                            ret.append((Move.PLACE_BONUS_TOKEN, token, route))
                if len(ret) == 0:
                    # active player has no actions or bonus tokens, move to next player's turn
                    self.players[self.activePlayer].actions = 0
                    self.activePlayer = (self.activePlayer + 1) % len(self.players)
                    self.players[self.activePlayer].gainActions()
                    return self.getOptions()
            else:
                # allow passing mainly for saving bonus tokens
                ret.append((Move.PASS, ))
        elif self.currentAction == Move.PLACE:
            for route in range(len(self.routes)):
                if self.routes[route].hasSpace():
                    if self.players[self.activePlayer].supply[0] > 0:
                        ret.append((Move.PLACE, Tradesman.TRADER, route))
                    if self.players[self.activePlayer].supply[1] > 0:
                        ret.append((Move.PLACE, Tradesman.MERCHANT, route))
        elif self.currentAction == Move.DISPLACE:
            for route in range(len(self.routes)):
                for space in self.routes[route].spaces:
                    if space[0] != -1 and space[0] != self.activePlayer:
                        if space[1] == Tradesman.MERCHANT:
                            if sum(self.players[self.activePlayer].supply) > 2:
                                ret.append((Move.DISPLACE, space[0], Tradesman.MERCHANT, route))
                        else:
                            # active player will have at least 2 tradesmen if they were allowed to take this action
                            ret.append((Move.DISPLACE, space[0], Tradesman.TRADER, route))
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
                for route in range(len(self.routes)):
                    for space in self.routes[route].spaces:
                        if space[0] == self.activePlayer:
                            ret.append((Move.MOVE_REMOVE, space[1], route))
                ret.append((Move.MOVE_REMOVE, Move.PASS)) # finish choosing pieces to move
            else:
                for route in range(len(self.routes)):
                    if self.routes[route].hasSpace():
                        if self.players[self.activePlayer].toReplace[0] > 0:
                            ret.append((Move.MOVE_REPLACE, Tradesman.TRADER, route))
                        if self.players[self.activePlayer].toReplace[1] > 0:
                            ret.append((Move.MOVE_REPLACE, Tradesman.MERCHANT, route))
        elif self.currentAction == Move.CREATE_TRADE_ROUTE:
            # if empty post in adjacent city, add establish post (or if bonus token) if possible
            postReqs = self.cities[self.routes[self.displaceRoute].leftCity.value].getPostReqs()
            if (self.routes[self.displaceRoute].hasTradesman(postReqs[0]) and
                    self.players[self.activePlayer].skills[Skill.PRIVILEGE.value - 1] >= postReqs[1].value):
                ret.append((Move.ESTABLISH_TRADING_POST, self.routes[self.displaceRoute].leftCity, False))
            postReqs = self.cities[self.routes[self.displaceRoute].rightCity.value].getPostReqs()
            if (self.routes[self.displaceRoute].hasTradesman(postReqs[0]) and
                    self.players[self.activePlayer].skills[Skill.PRIVILEGE.value - 1] >= postReqs[1].value):
                ret.append((Move.ESTABLISH_TRADING_POST, self.routes[self.displaceRoute].rightCity, False))
            if self.players[self.activePlayer].unusedBonusTokens.__contains__(BonusToken.ADDITIONAL_POST):
                if self.cities[self.routes[self.displaceRoute].leftCity.value].getFirstVacantPostPos() != 0:
                    ret.append((Move.ESTABLISH_TRADING_POST, self.routes[self.displaceRoute].leftCity, True))
                if self.cities[self.routes[self.displaceRoute].rightCity.value].getFirstVacantPostPos() != 0:
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
                for i in range(4):
                    if self.coellenSpots[i] == -1 and self.players[self.activePlayer].skills[2] >= i:
                        ret.append((Move.PLACE_ON_COELLEN, i))
            # do nothing option
            ret.append((Move.TRADE_ROUTE_NO_BONUS, ))
        elif self.currentAction == Move.BONUS_TOKEN_REMOVE:
            for route in range(len(self.routes)):
                for space in range(len(self.routes[route].spaces)):
                    if (self.routes[route].spaces[space][0] != self.activePlayer and
                            self.routes[route].spaces[space][0] != -1):
                        ret.append((Move.BONUS_TOKEN_REMOVE, route, space))
            ret.append((Move.BONUS_TOKEN_PASS, ))
        elif self.currentAction == Move.BONUS_TOKEN_REPLACE:
            for route in range(len(self.routes)):
                if self.routes[route].hasSpace():
                    ret.append((Move.BONUS_TOKEN_REPLACE, route))
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
                for i in range(len(self.routes)):
                    if self.adjacent(self.routes[i], self.routes[route]):
                        routes.add(i)
            # check routes for empty space
            for route in routes:
                if route != initialRoute and self.routes[route].hasSpace():
                    routesWithSpace.append(route)
        return routesWithSpace

    def adjacent(self, route1, route2):
        return (route1.leftCity == route2.leftCity or route1.leftCity == route2.rightCity or
                route1.rightCity == route2.leftCity or route1.rightCity == route2.rightCity)

    def getAdjacentCities(self, city):
        # return set of all cities adjacent to the given city
        # two cities are adjacent if they are the left and right city of a route
        adjacent = set()
        for route in self.routes:
            if route.leftCity == city:
                adjacent.add(route.rightCity)
            elif route.rightCity == city:
                adjacent.add(route.leftCity)
        return adjacent

    def getAdjacentCitiesWithPosts(self, city, player):
        # return set of all cities adjacent to the given city which have posts owned by player
        # two cities are adjacent if they are the left and right city of a route
        adjacent = set()
        for route in self.routes:
            if route.leftCity == city:
                if self.cities[route.rightCity].numPosts(player) > 0:
                    adjacent.add(route.rightCity)
            elif route.rightCity == city:
                if self.cities[route.leftCity].numPosts(player) > 0:
                    adjacent.add(route.leftCity)
        return adjacent

    def checkEastWestConnection(self, player):
        if (self.cities[CityName.ARNHEIM.value].numPosts(player) == 0 or
                self.cities[CityName.STENDAL.value].numPosts(player) == 0):
            return
        network = {CityName.ARNHEIM.value}
        self.expandNetwork(network, player)
        for city in network:
            if city == CityName.STENDAL.value:
                if self.eastWestConnections == 0:
                    self.players[player].gainPoints(7)
                elif self.eastWestConnections == 1:
                    self.players[player].gainPoints(4)
                elif self.eastWestConnections == 2:
                    self.players[player].gainPoints(2)
                self.eastWestConnections += 1
                return

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
        for space in self.routes[route].spaces:
            if space[0] != -1:
                return False
        return not (self.cities[self.routes[route].leftCity.value].isComplete() and
                self.cities[self.routes[route].rightCity.value].isComplete())

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
        # check if the game should end, should be called at the end of each action that can trigger the conditions
        if self.bonusTokenOverdraw or self.completedCities >= 10:
            self.isOver = True
        for player in self.players:
            if player.points >= 20:
                self.isOver = True
        if self.isOver:
            for i in range(len(self.players)):
                player = self.players[i]
                for i in range(1, 5):
                    if player.skills[i] == MAX_SKILL_LEVELS[i]:
                        player.gainPoints(4) # 4 points for each completed skill except keys
                bonusTokens = len(player.unusedBonusTokens) + len(player.usedBonusTokens)
                if bonusTokens > 9:
                    player.gainPoints(21)
                elif bonusTokens > 7:
                    player.gainPoints(15)
                elif bonusTokens > 5:
                    player.gainPoints(10)
                elif bonusTokens > 3:
                    player.gainPoints(6)
                elif bonusTokens > 1:
                    player.gainPoints(3)
                elif bonusTokens > 0:
                    player.gainPoints(1)
                # find largest network
                networks = set() # store each network of cities with player presence as a set of city IDs
                for city in range(len(self.cities)):
                    if self.cities[city].numPosts(i) > 0:
                        network = {city}
                        self.expandNetwork(network, i)
                        networks.add(network)
                posts = set() # number of posts in each network
                for network in networks:
                    count = 0
                    for city in network:
                        count += self.cities[city].numPosts(i)
                    posts.add(count)
                if posts:
                    player.gainPoints(max(posts) * self.getKeyMultiplier(player.skills[0]))
            for i in range(len(self.coellenSpots)):
                if self.coellenSpots[i] != -1:
                    self.players[i].gainPoints(7 + i)
                    if i == 3:
                        self.players[i].gainPoints(1)
            for city in self.cities:
                controller = city.getController()
                if controller != -1:
                    self.players[controller].gainPoints(2)

    def forceScore(self):
        # force the game to do end of game scoring for early playout termination
        if self.isOver:
            return # already scored
        self.isOver = True
        self.checkGameEnd()

    def getWinners(self):
        # todo: tiebreakers
        scores = [player.points for player in self.players]
        highScore = max(scores)
        count = 0
        winners = []
        for score in scores:
            if score == highScore:
                winners.append(1)
                count += 1
            else:
                winners.append(0)
        if count > 1:
            winners = [winner / 2 for winner in winners]
        return winners

    def countPosts(self, player):
        posts = 0
        for city in self.cities:
            for post in city.posts:
                if post == player:
                    posts += 1
        return posts

    def getKeyMultiplier(self, skillLevel):
        if skillLevel < 2:
            return skillLevel + 1
        return skillLevel

    def expandNetwork(self, network, player):
        # find ids of all connected cities containing posts and add them to network
        newCities = set()
        for city in network:
            newCities = newCities.union(self.getAdjacentCitiesWithPosts(city, player))
        newCities = newCities.difference(network)
        while newCities:
            network = network.union(newCities)
            newCities = set()
            for city in network:
                newCities = newCities.union(self.getAdjacentCitiesWithPosts(city, player))
            newCities = newCities.difference(network)


    def getOptionPlayerID(self):
        # return id of player to move
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
        startingTokens = [BonusToken.ADDITIONAL_POST, BonusToken.EXCHANGE_POSTS, BonusToken.MOVE_THREE]
        random.shuffle(startingTokens)
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0]], CityName.GRONINGEN, CityName.EMDEN))
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0], [-1, 0]], CityName.EMDEN, CityName.OSNABRUCK))
        self.routes.append(Route([[-1, 0], [-1, 0]], CityName.KAMPEN, CityName.OSNABRUCK))
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0]], CityName.OSNABRUCK, CityName.BREMEN, startingTokens.pop()))
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0]], CityName.KAMPEN, CityName.ARNHEIM))
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0]], CityName.ARNHEIM, CityName.MUNSTER))
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0]], CityName.MUNSTER, CityName.MINDEN))
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0]], CityName.ARNHEIM, CityName.DUISBURG))
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0], [-1, 0]], CityName.BREMEN, CityName.HAMBURG))
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0]], CityName.BREMEN, CityName.HANNOVER))
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0]], CityName.BREMEN, CityName.MINDEN))
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0]], CityName.STADE, CityName.HAMBURG))
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0]], CityName.HAMBURG, CityName.LUBECK))
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0], [-1, 0]], CityName.HAMBURG, CityName.LUNEBURG))
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0]], CityName.HANNOVER, CityName.LUNEBURG))
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0]], CityName.MINDEN, CityName.HANNOVER))
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0]], CityName.LUNEBURG, CityName.BERLEBERG, startingTokens.pop()))
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
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0]], CityName.HILDESHEIM, CityName.GOSLAR, startingTokens.pop()))
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0]], CityName.PADERBORN, CityName.MARBURG))
        self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0], [-1, 0]], CityName.COELLEN, CityName.MARBURG))
        if len(self.players) > 3:
            self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0]], CityName.EMDEN, CityName.STADE))
            self.routes.append(Route([[-1, 0], [-1, 0], [-1, 0]], CityName.MARBURG, CityName.GOTTINGEN))
        self.bonusTokens = [BonusToken.ADDITIONAL_POST, BonusToken.ADDITIONAL_POST, BonusToken.ADDITIONAL_POST,
                            BonusToken.EXCHANGE_POSTS, BonusToken.EXCHANGE_POSTS, BonusToken.MOVE_THREE,
                            BonusToken.DEVELOP_ABILITY, BonusToken.DEVELOP_ABILITY, BonusToken.THREE_ACTIONS,
                            BonusToken.THREE_ACTIONS, BonusToken.FOUR_ACTIONS, BonusToken.FOUR_ACTIONS]
        random.shuffle(self.bonusTokens)

    def printBoard(self):
        print(f"active player: {self.activePlayer}")
        print(f"")
        for player in range(len(self.players)):
            print(f"player {player}:")
            self.players[player].printPlayer()
        for city in range(len(self.cities)):
            print(f"city: {CityName(city).name}, posts:")
            for post in range(len(self.cities[city].bonusPosts)):
                print(f"bonus post occupied by player {self.cities[city].bonusPosts[post]}", end=", ")
            for post in range(len(self.cities[city].posts) - 1):
                if self.cities[city].posts[post] == -1:
                    print(f"unoccupied {self.cities[city].postRequirements[post][1].name} "
                          f"{self.cities[city].postRequirements[post][0].name} post", end=", ")
                else:
                    print(f"{self.cities[city].postRequirements[post][1].name} "
                          f"{self.cities[city].postRequirements[post][0].name} post occupied by player "
                          f"{self.cities[city].posts[post]}", end=", ")
            post = len(self.cities[city].posts) - 1
            if self.cities[city].posts[post] == -1:
                print(f"unoccupied {self.cities[city].postRequirements[post][1].name} "
                      f"{self.cities[city].postRequirements[post][0].name} post")
            else:
                print(f"{self.cities[city].postRequirements[post][1].name} "
                      f"{self.cities[city].postRequirements[post][0].name} post occupied by player "
                      f"{self.cities[city].posts[post]}")
        for route in range(len(self.routes)):
            print(f"route between {self.routes[route].leftCity.name} and {self.routes[route].rightCity.name}:")
            if self.routes[route].bonusToken != BonusToken.NONE:
                print(f"bonus token: {self.routes[route].bonusToken}")
            for space in range(len(self.routes[route].spaces) - 1):
                if self.routes[route].spaces[space][0] == -1:
                    print(f"unoccupied space", end=", ")
                else:
                    print(f"player {self.routes[route].spaces[space][0]}'s "
                          f"{self.routes[route].spaces[space][1].name}", end=", ")
            space = len(self.routes[route].spaces) - 1
            if self.routes[route].spaces[space][0] == -1:
                print(f"unoccupied space")
            else:
                print(f"player {self.routes[route].spaces[space][0]}'s {self.routes[route].spaces[space][1].name}")

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
        self.oppID = 0 # opp that piece removed by bonus token belongs to

    def gainActions(self):
        # gain a number of actions based on skill level
        self.actions = (self.skills[1] + 1) // 2 + 2

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

    def printPlayer(self):
        print(self.brain)
        print("skill levels:")
        print(f"keys: {self.skills[0]}")
        print(f"actions: {self.skills[1]}")
        print(f"privilege: {self.skills[2]}")
        print(f"book: {self.skills[3]}")
        print(f"income: {self.skills[4]}")
        print(f"stock: {self.stock[0]} traders and {self.stock[1]} merchants")
        print(f"supply: {self.supply[0]} traders and {self.supply[1]} merchants")
        print(f"actions: {self.actions}")
        print(f"points: {self.points}")
        print(f"toRemove: {self.toRemove}, toReplace: {self.toReplace}")
        print(f"unused bonus tokens: {self.unusedBonusTokens}, used bonus tokens: {self.usedBonusTokens}")
        print(f"bonusTokensToPlace: {self.bonusTokensToPlace}")

class City:
    def __init__(self, skill, posts, postRequirements, postPoints):
        self.skill = skill
        self.posts = posts
        self.postRequirements = postRequirements
        self.bonusPosts = []
        self.postPoints = postPoints

    def isComplete(self):
        return -1 not in self.posts

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

    def numPosts(self, player):
        posts = 0
        for post in self.bonusPosts:
            if post == player:
                posts += 1
        for post in self.posts:
            if post == player:
                posts += 1
        return posts

    def getFirstVacantPostPos(self):
        for i in range(len(self.posts)):
            if self.posts[i] == -1:
                return i
        return -1

    def getPostReqs(self):
        pos = self.getFirstVacantPostPos()
        if pos == -1:
            return (-1, -1)
        return self.postRequirements[pos]

    def fillPost(self, player):
        for i in range(len(self.posts)):
            if self.posts[i] == -1:
                self.posts[i] = player
                return (self.postPoints[i], self.postRequirements[i][0])

    def fillBonusPost(self, player):
        self.bonusPosts.append(player)

    def exchangePosts(self, post):
        buffer = self.posts[post]
        self.posts[post] = self.posts[post + 1]
        self.posts[post + 1] = buffer

class Route:
    def __init__(self, spaces, leftCity, rightCity, bonusToken=BonusToken.NONE):
        self.spaces = spaces
        # left/right are mostly to differentiate the two adjacent cities and otherwise arbitrary
        self.leftCity = leftCity
        self.rightCity = rightCity
        self.bonusToken = bonusToken

    def isEmpty(self):
        for space in self.spaces:
            if space[0] != -1:
                return False
        return True

    def clear(self):
        for i in range(len(self.spaces)):
            self.spaces[i] = [-1, 0]

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

    def countPieces(self, player):
        count = 0
        for space in self.spaces:
            if space[0] == player:
                count += 1
        return count

    def countEmptySpace(self):
        count = 0
        for space in self.spaces:
            if space[0] == -1:
                count += 1
        return count

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

