import Game
import HansaPlayers


def printMove(move, player, board):
    print(f"making move: {move}")
    match move[0]:
        case Game.Move.PASS:
            print(f"Player {player} passes")
        case Game.Move.INCOME:
            print(f"Player {player} collects income ({board.getIncomeAmount(board.players[board.getOptionPlayerID()].skills[4])})")
        case Game.Move.PLACE:
            if len(move) == 1:
                print(f"Player {player} chooses to place a tradesman on a route")
            else:
                print(f"Player {player} places a {move[1].name} on the route between {board.routes[move[2]].leftCity.name} "
                      f"and {board.routes[move[2]].rightCity.name}")
        case Game.Move.DISPLACE:
            if len(move) == 1:
                print(f"Player {player} chooses to displace an opponent's tradesman")
            else:
                print(f"Player {player} displaces player {move[1]}'s {move[2].name} on the route between "
                      f"{board.routes[move[3]].leftCity.name} and {board.routes[move[3]].rightCity.name}")
        case Game.Move.DISPLACE_REMOVE:
            print(f"Player {player} removes one {move[1].name} from their supply to pay for displacing")
        case Game.Move.DISPLACE_PLACE:
            print(f"Player {player} places a {move[1].name} on the route between {board.routes[board.displaceRoute].leftCity.name} "
                  f"and {board.routes[board.displaceRoute].rightCity.name}")
        case Game.Move.DISPLACE_REPLACE:
            print(f"Player {player} places a {move[2].name} on the route between {board.routes[move[1]].leftCity.name}"
                  f" and {board.routes[move[1]].rightCity.name}")
        case Game.Move.DISPLACE_REPLACE_STOCK:
            print(f"Player {player} places a {move[1].name} from their stock")
        case Game.Move.DISPLACE_REPLACE_SUPPLY:
            print(f"Player {player} places a {move[1].name} from their supply")
        case Game.Move.DISPLACE_REPLACE_PASS:
            print(f"Player {player} finishes placing pieces")
        case Game.Move.MOVE:
            print(f"Player {player} chooses to move up to {board.players[board.activePlayer].skills[3] + 2} tradesmen")
        case Game.Move.MOVE_REMOVE:
            if (move[1] == Game.Move.PASS):
                print(f"Player {player} finishes choosing tradesmen to move")
            else:
                print(f"Player {player} chooses to move the {move[1].name} on the route between {board.routes[move[2]].leftCity.name} "
                      f"and {board.routes[move[2]].rightCity.name}")
        case Game.Move.MOVE_REPLACE:
            print(f"Player {player} places a {move[1].name} on the route between {board.routes[move[2]].leftCity.name} "
                  f"and {board.routes[move[2]].rightCity.name}")
        case Game.Move.CREATE_TRADE_ROUTE:
            print(f"Player {player} creates a trade route between the cities {board.routes[move[1]].leftCity.name} and "
                  f"{board.routes[move[1]].rightCity.name}")
        case Game.Move.ESTABLISH_TRADING_POST:
            print(f"Player {player} establishes a trading post in the city of {move[1].name}") # todo: probably print post type
        case Game.Move.IMPROVE_SKILL:
            print(f"Player {player} improves their {Game.Skill(move[1] + 1).name} skill")
        case Game.Move.TRADE_ROUTE_NO_BONUS:
            print(f"Player {player} establishes a trade route with no bonus")
        case Game.Move.PLACE_ON_COELLEN:
            print(f"Player {player} places a merchant on Coellen") # todo: which space
        case Game.Move.USE_BONUS_TOKEN:
            print(f"Player {player} uses a {move[1].name} bonus token")
        case _:
            print(f"Player {player} makes a move: unsupported action type - {move[0]}")


board = Game.BoardState((Game.Player(HansaPlayers.HumanPlayer()), Game.Player(HansaPlayers.RandomPlayer())), True)
board.printBoard()

while not board.isOver:
    options = board.getOptions() # turn advances in get options currently which causes bugs if we don't call it before letting the player move
    player = board.getOptionPlayerID()
    print(options)
    move = board.getOptionPlayer().play(board)
    if board.printingEnabled:
        printMove(move, player, board)
    board.makeMove(move)
    #if board.printingEnabled:
        #board.printBoard()
print("game over")
for i in range(len(board.players)):
    print(f"Player {i} has {board.players[i].points} points")
