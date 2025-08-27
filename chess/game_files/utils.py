initial_board = [
    ["R", "N", "B", "Q", "K", "B", "N", "R"],
    ["P", "P", "P", "P", "P", "P", "P", "P"],
    [".", ".", ".", ".", ".", ".", ".", "."],
    [".", ".", ".", ".", ".", ".", ".", "."],
    [".", ".", ".", ".", ".", ".", ".", "."],
    [".", ".", ".", ".", ".", ".", ".", "."],
    ["p", "p", "p", "p", "p", "p", "p", "p"],
    ["r", "n", "b", "q", "k", "b", "n", "r"]
]

initial = {
    "board": initial_board,
    "E1K": False,
    "E8K": False,
    "A1R": False,
    "A8R": False,
    "H1R": False,
    "H8R": False,
    "prev_move": None,
    "history": [initial_board],
    "hdict": {"RNBQKBNRPPPPPPPP................................pppppppprnbqkbnr":1},
    "movelist": []
}

scoring = {'win': 1, 'draw': 0.5, 'loss': 0}
move_types = (str)