import Game

game = Game.BoardState((Game.Player(), ), True)
game.printBoard()

while not game.isOver:
    break # todo: play until game ends