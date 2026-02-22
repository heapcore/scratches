class Connect4:
    COLUMNS = []
    NO_COLOR = "\033[0m"

    def __init__(self, rows, cols, players=2, colors=("\033[0;31m", "\033[1;33m")):
        self.rows = rows
        self.cols = cols
        self.players = players
        self.colors = colors

        for _ in range(cols):
            self.COLUMNS.append([0] * rows)

    def print_painted(self, player):
        if player:
            print(self.colors[player - 1] + "O" + self.NO_COLOR, end="")
        else:
            print(".", end="")

    def print(self):
        for i in range(self.rows):
            for j in range(self.cols):
                self.print_painted(self.COLUMNS[j][i])
            print("")

    def check_board_full(self):
        for j in range(self.cols):
            if not self.COLUMNS[j][0]:
                return False
        return True

    def place_brick(self, player, col):
        for i in range(self.rows):
            if self.COLUMNS[col][-(i + 1)] == 0:
                self.COLUMNS[col][-(i + 1)] = player
                return True
        return False

    def check_winner(self):
        for i in range(self.rows):
            for j in range(self.cols - 3):
                value = self.COLUMNS[j][i]
                if value != 0:
                    equals_num = 1
                    print(i, j)
                    for k in range(1, 4):
                        if self.COLUMNS[j + k][i] == value:
                            equals_num += 1
                        else:
                            break
                    if equals_num == 4:
                        return value
        return None

    def start(self):
        i = 1
        while True:
            if self.check_board_full():
                print("There is no more place on the board. =(")
                self.game_over()
            print("Player {} walks".format(i))
            col = input("Please enter number of column to drop brick: ")
            try:
                col = int(col)
                if col < 1 or col > self.cols:
                    raise ValueError
            except ValueError:
                print(
                    "Error! Column number must be an integer from 1 to {}".format(
                        self.cols
                    )
                )
                continue
            if self.place_brick(i, col - 1):
                self.print()
                winner = self.check_winner()
                if winner:
                    print("Congratulations! Player {} wins!".format(i))
                    self.game_over()
                else:
                    i = i + 1 if i < self.players else 1
            else:
                print("Oops! This column is full of bricks. Please try another...")

    def game_over(self):
        print("G A M E  O V E R")
        exit(0)


if __name__ == "__main__":
    print("""Play Connect4 Game!
You have to drop bricks on the board. Each brick falls to the bottom of the board.
Wins the player who first builds 4 bricks with his color in the horizontal row.""")
    game = Connect4(6, 7)
    game.start()
