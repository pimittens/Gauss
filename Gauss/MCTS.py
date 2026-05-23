import math
import time
import Game
import random


class Node:
    def __init__(self, state, prior=0, parent=None, move=None):
        self.state = state
        self.parent = parent
        self.move = move
        self.children = []
        self.visits = 0
        self.prior = prior
        self.points = 0
        self.expanded = False

    def Q(self):
        if self.visits == 0:
            return 0
        return self.points / self.visits

    def isTerminalNode(self):
        return self.state.isOver

    def bestChild(self, cpuct=1.41):
        bestScore = float("-inf")
        bestChild = None
        for child in self.children:
            score = child.Q() + (cpuct * child.prior * math.sqrt(self.visits) / (1 + child.visits))
            if score > bestScore:
                bestScore = score
                bestChild = child
        return bestChild

    def mostVisitedChild(self):
        visits = [child.visits for child in self.children]
        return self.children[visits.index(max(visits))]

    def expand(self):
        options = self.state.getOptions()
        scores = []
        for move in options:
            scores.append(policyScore(self.state, move))
        total = sum(scores)
        priors = [score / total for score in scores]
        for move, prior in zip(options, priors):
            nextState = self.state.copyState()
            nextState.makeMove(move)
            child = Node(nextState, prior, self, move)
            self.children.append(child)
        self.expanded = True

    def backpropagate(self, result):
        self.visits += 1
        self.points += result[self.state.lastPlayer]
        if self.parent:
            self.parent.backpropagate(result)

def policyScore(state, move):
    score = 1
    player = state.getOptionPlayerID
    if move[0] == Game.Move.PLACE:
        if len(move) > 1:
            route = state.routes[move[2]]
            if (state.cities[route.leftCity.value].skill != Game.Skill.NONE or
                    state.cities[route.rightCity.value].skill != Game.Skill.NONE):
                score += 400 # prioritize routes adjacent to skill cities
            myPieces = route.countPieces(player)
            remaining = len(route.spaces) - myPieces
            if remaining == 1:
                score += 500 # completing a route is valuable
            elif remaining == 2:
                score += 50
            oppPieces = remaining - route.countEmptySpace()
            if oppPieces == 2 or oppPieces == 3:
                score += 300 # try to block opponents
            if oppPieces == 1:
                score += 50
        else:
            score += 100 # placing pieces is generally valuable
    elif move[0] == Game.Move.CREATE_TRADE_ROUTE:
        score += 500 # completing trade routes is good
    elif move[0] == Game.Move.IMPROVE_SKILL:
        score += 500
    elif move[0] == Game.Move.ESTABLISH_TRADING_POST:
        score += 200
    return score

def evaluate(state):
    if state.isOver:
        return state.getWinners()
    result = []
    for player in range(len(state.players)):
        score = 1
        # skill upgrades
        score += (10 * state.players[player].points)
        score += (150 * state.players[player].skills[1])
        score += (100 * state.players[player].skills[2])
        score += (80 * state.players[player].skills[3])
        score += (60 * state.players[player].skills[4])
        # pieces on routes
        for route in state.routes:
            myPieces = route.countPieces(player)
            remaining = len(route.spaces) - myPieces
            if remaining == 0:
                score += 100
            elif remaining > 0:
                # nearly complete routes are valuable
                score += 20 / remaining
        # trading posts
        score += 40 * state.countPosts(player)
        result.append(score)
    average = sum(result) / len(result)
    result = [math.tanh((res - average) / 200) for res in result]
    return result

def mcts(rootState, numSims):
    startTime = time.time()
    root = Node(rootState.copyState())
    for _ in range(numSims):
        node = root
        # selection
        while node.expanded and node.children:
            node = node.bestChild()
        # expansion
        if not node.isTerminalNode():
            node.expand()
            node = node.bestChild()
        # evaluation
        result = evaluate(node.state)
        # backpropagation
        node.backpropagate(result)
    if rootState.printingEnabled:
        print("mcts results")
        for node in root.children:
            print(
                f"Move: {node.move}, visits:{node.visits}, prior: {node.prior}, win probability: "
                f"{node.points / max(1, node.visits)}, lastPlayer: {node.state.lastPlayer}")
        print(f"time elapsed: {time.time() - startTime} seconds")
    #if rootState.loggingEnabled:
    #    rootState.log.write("mcts results\n")
    #    for node in root.children:
    #        rootState.log.write(
    #            f"Move: {node.move}, visits:{node.visits}, win probability: {node.points / node.visits}, lastPlayer: {node.state.lastPlayer}\n")
    #    rootState.log.write(f"time elapsed: {time.time() - startTime} seconds\n")
    return root.mostVisitedChild().move

TOP_K_MOVES = 5
ROLLOUT_DEPTH = 50

EPSILON = 0.10

def generateReasonableMoves(state):
    moves = state.getOptions()
    scoredMoves = []
    tacticalMoves = []
    for move in moves:
        score = quickMoveScore(state, move)
        #
        # force critical tactical moves
        #
        if score >= 1000:
            tacticalMoves.append(move)
        scoredMoves.append((score, move))
    #
    # always search tactical moves
    #
    if tacticalMoves:
        return tacticalMoves
    #
    # sort descending
    #
    scoredMoves.sort(
        key=lambda x: x[0],
        reverse=True
    )
    #
    # keep top K only
    #
    return [
        move
        for _, move in scoredMoves[:TOP_K_MOVES]
    ]


# ==================================================
# FAST MOVE HEURISTIC
# ==================================================

def quickMoveScore(state, move):
    #
    # VERY IMPORTANT:
    # this function must stay FAST
    #
    player = state.getOptionPlayerID()
    score = 0
    #
    # avoid pass
    #
    if move == (Game.Move.PASS,):
        return -99999
    #
    # simulate move
    #
    testState = state.copyState()
    testState.makeMove(move)
    # ------------------------------------------------
    # 1. completing routes
    # ------------------------------------------------
    for route in testState.routes:
        myPieces = route.countPieces(player)
        if myPieces == len(route.spaces):
            #
            # huge priority
            #
            score += 2000
    # ------------------------------------------------
    # 2. nearly-complete routes
    # ------------------------------------------------
    for route in testState.routes:
        myPieces = route.countPieces(player)
        remaining = len(route.spaces) - myPieces
        if remaining == 1:
            score += 500
        elif remaining == 2:
            score += 150
    # ------------------------------------------------
    # 3. upgrades
    # ------------------------------------------------
    #
    # Replace with your actual methods
    #
    score += (50 * testState.players[player].skills[1])
    score += (30 * testState.players[player].skills[2])
    score += (20 * testState.players[player].skills[3])
    score += (10 * testState.players[player].skills[4])
    # ------------------------------------------------
    # 4. blocking opponents
    # ------------------------------------------------
    for opponent in testState.players:
        if opponent == player:
            continue
        for route in testState.routes:
            oppPieces = route.countPieces(opponent)
            remaining = len(route.spaces) - oppPieces
            #
            # opponent almost completed route
            #
            if remaining == 1:
                #
                # if we now occupy route space
                #
                if route.countPieces(player) > 0:
                    score += 400
    # ------------------------------------------------
    # 5. centrality
    # ------------------------------------------------
    #
    # Optional:
    # reward good board locations
    #
    '''if hasattr(move, "position"):

        position = move.position

        if position in CENTRALITY:
            score += CENTRALITY[position]'''
    # ------------------------------------------------
    # 6. discourage pointless movement
    # ------------------------------------------------
    #
    # You should customize this heavily.
    #
    if isProbablyUselessMove(state, move):
        score -= 500
    #
    # tiny noise
    #
    score += random.random()
    return score

# ==================================================
# USELESS MOVE DETECTION
# ==================================================

def isProbablyUselessMove(state, move):

    #
    # Placeholder examples.
    #
    # Customize for your engine.
    #

    #
    # moving piece that was already helping route
    # to isolated area
    #

    #
    # rearranging without improving anything
    #

    #
    # moving away from contested routes
    #

    return False


# ==================================================
# POSITION EVALUATION
# ==================================================

def evaluatePlayer(state, player):
    score = 0
    # ------------------------------------------------
    # actual VP
    # ------------------------------------------------
    score += (10 * state.players[player].points)
    # ------------------------------------------------
    # upgrades matter enormously
    # ------------------------------------------------
    score += (150 * state.players[player].skills[1])
    score += (100 * state.players[player].skills[2])
    score += (80 * state.players[player].skills[3])
    score += (60 * state.players[player].skills[4])
    # ------------------------------------------------
    # route pressure
    # ------------------------------------------------
    for route in state.routes:
        myPieces = route.countPieces(player)
        remaining = len(route.spaces) - myPieces
        if remaining == 0:
            score += 100
        elif remaining > 0:
            # nearly complete routes are valuable
            score += 20 / remaining
    score += 40 * state.countPosts(player)
    return score

def evaluatePosition(state, rootPlayer):
    myScore = evaluatePlayer(state, rootPlayer)
    others = []
    for player in range(len(state.players)):
        if player != rootPlayer:
            others.append(evaluatePlayer(state, player))
    avgOpponent = (sum(others) / len(others))
    #
    # relative advantage
    #
    value = myScore - avgOpponent
    #
    # squash to stable range
    #
    return math.tanh(value / 100)

def chooseMove(state, moves):
    #
    # epsilon-greedy:
    #
    # 10% random
    # 90% heuristic best move
    #
    if random.random() < EPSILON:
        return random.choice(moves)
    bestScore = float("-inf")
    bestMove = None
    for move in moves:
        score = quickMoveScore(state, move)
        if score > bestScore:
            bestScore = score
            bestMove = move
    return bestMove

def rollout(state, rootPlayer):
    currentState = state.copyState()
    depth = 0
    while not currentState.isOver and depth < ROLLOUT_DEPTH:
        possibleMoves = generateReasonableMoves(currentState)
        move = chooseMove(currentState, possibleMoves)
        currentState.makeMove(move)
        depth += 1
    currentState.forceScore()
    return evaluatePosition(currentState, rootPlayer)