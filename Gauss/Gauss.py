import random
import threading

import Game
import HansaPlayers

import tkinter as tk
from PIL import Image, ImageTk

BOARD_WIDTH = 800
BOARD_HEIGHT = 600
DESK_WIDTH = 330 # approx 1.65 times width
DESK_HEIGHT = 200

PLAYER_COLORS = ('blue', 'yellow', 'red', 'green', 'purple')

class interface():
    def __init__(self, board):
        self.board = board

        self.root = tk.Tk()
        self.root.title('Gauss')
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(self.root, width=DESK_WIDTH * 5, height=BOARD_HEIGHT + DESK_HEIGHT)
        self.canvas.pack()

        if len(board.players) < 4:
            image = Image.open("assets/2_to_3_p_board.png")
        else:
            image = Image.open("assets/4_to_5_p_board.png")
        image = image.resize(
            (BOARD_WIDTH, BOARD_HEIGHT),
            Image.Resampling.LANCZOS
        )
        self.boardImage = ImageTk.PhotoImage(image)

        self.deskImages = []
        for color in PLAYER_COLORS:
            image = Image.open(f"assets/desk_{color}.png")
            image = image.resize(
                (DESK_WIDTH, DESK_HEIGHT),
                Image.Resampling.LANCZOS
            )
            self.deskImages.append(ImageTk.PhotoImage(image))

        self.redraw()
        self.root.mainloop()

    def redraw(self):
        self.canvas.delete("all")

        self.canvas.create_image(
            0, 0,
            anchor="nw",
            image=self.boardImage
        )

        for i in range(5):
            self.canvas.create_image(
                DESK_WIDTH * i, BOARD_HEIGHT,
                anchor="nw",
                image=self.deskImages[i]
            )

        if len(self.board.players) < 4:
            for route in self.board.routes:
                if route.adjacentTo(Game.CityName.GRONINGEN, Game.CityName.EMDEN):
                    self.drawRoutePieces(route, ((0.13, 0.24), (0.18, 0.23), (0.23, 0.19)))
                elif route.adjacentTo(Game.CityName.EMDEN, Game.CityName.OSNABRUCK):
                    self.drawRoutePieces(route, ((0.293, 0.23), (0.26, 0.27), (0.235, 0.32), (0.265, 0.36)))
                elif route.adjacentTo(Game.CityName.KAMPEN, Game.CityName.OSNABRUCK):
                    self.drawRoutePieces(route, ((0.13, 0.39), (0.195, 0.4)))
                elif route.adjacentTo(Game.CityName.KAMPEN, Game.CityName.ARNHEIM):
                    self.drawRoutePieces(route, ((0.06, 0.38), (0.08, 0.42), (0.1, 0.465)))
                # todo: remaining routes
        else:
            pass # todo: 4-5 player board

        self.root.after(1000, self.redraw)

    def drawRoutePieces(self, route, offsets):
        for sp in range(len(route.spaces)):
            space = route.spaces[sp]
            if space[0] != -1:
                if space[1] == Game.Tradesman.TRADER:
                    self.canvas.create_rectangle(
                        BOARD_WIDTH * offsets[sp][0], BOARD_HEIGHT * offsets[sp][1],
                        BOARD_WIDTH * offsets[sp][0] + 17, BOARD_HEIGHT * offsets[sp][1] + 17,
                        fill=PLAYER_COLORS[space[0]]
                    )
                elif space[1] == Game.Tradesman.MERCHANT:
                    self.canvas.create_oval(
                        BOARD_WIDTH * offsets[sp][0], BOARD_HEIGHT * offsets[sp][1],
                        BOARD_WIDTH * offsets[sp][0] + 20, BOARD_HEIGHT * offsets[sp][1] + 20,
                        fill=PLAYER_COLORS[space[0]]
                    )


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


theBoard = Game.BoardState((Game.Player(HansaPlayers.HumanPlayer()), Game.Player(HansaPlayers.RandomPlayer())), True)
theBoard.printBoard()

def worker():
    for route in theBoard.routes:
        for space in route.spaces:
            space[0] = random.choice(range(5))
            space[1] = random.choice((Game.Tradesman.TRADER, Game.Tradesman.MERCHANT))

    while not theBoard.isOver:
        options = theBoard.getOptions() # turn advances in get options currently which causes bugs if we don't call it before letting the player move
        player = theBoard.getOptionPlayerID()
        print(options)
        move = theBoard.getOptionPlayer().play(theBoard)
        if theBoard.printingEnabled:
            printMove(move, player, theBoard)
        theBoard.makeMove(move)
        #if board.printingEnabled:
        #board.printBoard()
    print("game over")
    for i in range(len(theBoard.players)):
        print(f"Player {i} has {theBoard.players[i].points} points")

thread = threading.Thread(target=worker, daemon=True)
thread.start()

gui = interface(theBoard)
