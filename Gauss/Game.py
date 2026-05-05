from enum import Enum
import random

MAX_SKILL_LEVELS = [4, 5, 3, 3, 3]

class Move(Enum):
    PASS = 0
    INCOME = 1
    PLACE = 2
    DISPLACE = 3
    MOVE = 4
    MOVE_REMOVE = 5
    MOVE_REPLACE = 6
    CREATE_TRADE_ROUTE = 7
    USE_BONUS_TOKEN = 8
    PLACE_BONUS_TOKEN = 9

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

class BoardState:
    def __init__(self, players, initialState):
        self.players = players
        self.activePlayer = 0
        self.completedCities = 0
        self.cities = []
        self.routes = []
        self.currentAction = 0
        self.bonusTokens = []
        if initialState:
            self.setup()

    def makeMove(self, move):
        if self.currentAction == Move.PASS:
            if move[0] == Move.INCOME:
                self.players[self.activePlayer].income()
                self.players[self.activePlayer].actions -= 1
            elif move[0] == Move.CREATE_TRADE_ROUTE:
                # todo: score and claim bonus tokens
                if
                self.currentAction = Move.CREATE_TRADE_ROUTE
            else:
                self.currentAction = move[0]
        else:
            if move[0] == Move.PLACE:
                # todo
            elif move[0] == Move.DISPLACE:
                # todo
            elif move[0] == Move.MOVE:
                # todo
            elif move[0] == Move.CREATE_TRADE_ROUTE:
                # todo


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
            for token in self.players[self.activePlayer].unusedBonusTokens:
                if token != BonusToken.ADDITIONAL_POST:
                    ret.append((Move.USE_BONUS_TOKEN, token))
            if len(ret) == 0:
                # todo: place bonus tokens before advancing turn
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
        elif self.currentAction == Move.DISPLACE:
            # todo: first choose a piece to displace (pay necessary amount), then replace with own piece, then displaced player places pieces
        elif self.currentAction == Move.MOVE:
            if self.players[self.activePlayer].toRemove > 0:
                for route in self.routes:
                    for space in route.spaces:
                        if space[0] == self.activePlayer:
                            ret.append((Move.MOVE_REMOVE, space[1], route))
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


    def setup(self):
        traders = 5
        for player in self.players:
            player.supply = [traders, 1]
            player.stock = [11 - traders, 0]
            traders += 1
        # todo: map, bonus tokens

class Player:
    def __init__(self):
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
    def __init__(self, name, skill, posts, postColors):
        self.name = name
        self.skill = skill
        self.posts = posts
        self.postColors = postColors
        self.bonusPosts = []

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
