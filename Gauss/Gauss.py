import Game
import HansaPlayers


def printMove(move):
    print(f"making move: {move}")  # todo: more detail


board = Game.BoardState((Game.Player(HansaPlayers.HumanPlayer()), Game.Player(HansaPlayers.HumanPlayer())), True)
board.printBoard()

while not board.isOver:
    options = board.getOptions() # turn advances in get options currently which causes bugs if we don't call it before letting the player move
    print(options)
    move = board.getOptionPlayer().play(board)
    if board.printingEnabled:
        printMove(move)
    board.makeMove(move)
