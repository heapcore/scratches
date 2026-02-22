from connect4 import Connect4


def test_check_winner():
    game = Connect4(6, 7)
    game.COLUMNS = [
        [0, 0, 0, 2, 2, 2],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 2],
        [0, 0, 0, 0, 1, 1],
        [0, 0, 0, 0, 1, 2],
        [0, 0, 0, 0, 1, 1],
    ]
    assert game.check_winner() == 1
