import random
import numpy as np
from Game import Move

def printOptions(options, board):
    # todo: print possible moves
    print(f"Decision for player {board.getOptionPlayerID()}")
    i = 1
    for option in options:
        match option[0]:
            case Move.PASS:
                print(f"{i}: Pass")
            case Move.INCOME:
                print(f"{i}: Collect income ({board.getIncomeAmount(board.players[board.getOptionPlayerID()].skills[4])})")
            case Move.PLACE:
                if len(option) == 1:
                    print(f"{i}: Place a tradesman on a route")
                else:
                    print(f"{i}: Place a {option[1].name} on the route between {board.routes[option[2]].leftCity.name} "
                          f"and {board.routes[option[2]].rightCity.name}")
            case Move.DISPLACE:
                if len(option) == 1:
                    print(f"{i}: Displace an opponent's tradesman")
                else:
                    print(f"{i}: Displace player {option[1]}'s {option[2].name} on the route between "
                          f"{board.routes[option[3]].leftCity.name} and {board.routes[option[3]].rightCity.name}")
            case Move.DISPLACE_REMOVE:
                print(f"{i}: Remove one {option[1].name} from your supply to pay for displacing")
            case Move.DISPLACE_PLACE:
                print(f"{i}: Place a {option[1].name} on the route between {board.routes[board.displaceRoute].leftCity.name} "
                      f"and {board.routes[board.displaceRoute].rightCity.name}")
            case Move.DISPLACE_REPLACE:
                print(f"{i}: Unsupported action type - {option[0]}")
            case Move.MOVE:
                print(f"{i}: Move up to {board.players[board.activePlayer].skills[3] + 2} tradesmen")
            case Move.MOVE_REMOVE:
                if (option[1] == Move.PASS):
                    print(f"{i}: Finish choosing tradesmen to move")
                else:
                    print(f"{i}: Move the {option[1].name} on the route between {board.routes[option[2]].leftCity.name} "
                          f"and {board.routes[option[2]].rightCity.name}")
            case Move.MOVE_REPLACE:
                print(f"{i}: Place a {option[1].name} on the route between {board.routes[option[2]].leftCity.name} "
                      f"and {board.routes[option[2]].rightCity.name}")
            case Move.CREATE_TRADE_ROUTE:
                print(f"{i}: Create a trade route between the cities {board.routes[option[1]].leftCity.name} and "
                      f"{board.routes[option[1]].rightCity.name}")
            case Move.ESTABLISH_TRADING_POST:
                print(f"{i}: Establish a trading post in the city of {option[1].name}") # todo: probably print office type
            case Move.IMPROVE_SKILL:
                print(f"{i}: Improve your {option[1]} skill") # todo:
            case _:
                print(f"{i}: Unsupported action type - {option[0]}")
        i += 1


class RandomPlayer():
    def play(self, board):
        options = board.getOptions()
        if board.printingEnabled:
            printOptions(options, board)
        return options[np.random.randint(0, len(options))]

class MCTSPlayer():
    # todo
    pass

class HumanPlayer():
    def play(self, board):
        options = board.getOptions()
        if len(options) == 1:
            return options[0]
        printOptions(options, board)
        while True:
            choice = input("select from the above options: ")
            if choice == "print":
                board.printBoardState()
                printOptions(options, board)
                continue
            if not choice.isdigit():
                print("invalid choice")
                printOptions(options, board)
                continue
            choice = int(choice)
            if choice in list(range(1, len(options) + 1)):
                break
            print("invalid choice")
            printOptions(options, board)
        return options[choice - 1]