from enum import Enum
import random

MAX_SKILL_LEVELS = [4, 5, 3, 3, 3]

class Move(Enum):
    PASS = 0
    INCOME = 1
    PLACE = 2
    DISPLACE = 3
    MOVE = 4
    CREATE_TRADE_ROUTE = 5
    USE_BONUS_TOKEN = 6

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

class BoardState:
    def __init__(self, players, initialState):
        self.players = players
        self.activePlayer = 0
        self.completedCities = 0
        self.cities = []
        self.routes = []
        self.currentAction = 0
        if initialState:
            self.setup()

    def makeMove(self, move):
        if self.currentAction == Move.PASS:
            if move[0] == Move.INCOME:
                self.players[self.activePlayer].income()
                self.players[self.activePlayer].actions -= 1
            elif move[0] == Move.CREATE_TRADE_ROUTE:
                # todo: score and claim bonus tokens
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
                # todo: actions
                if self.players[self.activePlayer].stock[0] > 0 or self.players[self.activePlayer].stock[1] > 0:
                    ret.append((Move.INCOME, ))
                if self.players[self.activePlayer].supply[0] > 0 or self.players[self.activePlayer].supply[1] > 0:
                    ret.append((Move.PLACE, ))
                    # todo: if there are any tokens on routes belonging to other players add displace (only if they can afford it)
                # todo: if there are any tokens on routes belong to the active player add move
                # todo: create trade route if they can
            for token in self.players[self.activePlayer].unusedBonusTokens:
                if token != BonusToken.ADDITIONAL_POST:
                    ret.append((Move.USE_BONUS_TOKEN, token))
            if len(ret) == 0:
                # active player has no actions or bonus tokens, move to next player's turn
                self.activePlayer = (self.activePlayer + 1) % len(self.players)
                self.players[self.activePlayer].gainActions()
                return self.getOptions()
            else:
                # allow passing mainly for saving bonus tokens
                ret.append((Move.PASS, ))
        elif self.currentAction == Move.PLACE:
            # todo: generate place move for each location and each available tradesman type
        elif self.currentAction == Move.DISPLACE:
            # todo: first choose a piece to displace (pay necessary amount), then replace with own piece, then displaced player places pieces
        elif self.currentAction == Move.MOVE:
            # todo: first need to remove pieces, then place them back


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
        self.unusedBonusTokens = []
        self.usedBonusTokens = []

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
