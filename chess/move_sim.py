from . import chess_utils
from . import dfs
from . import material_eval
from game_files.utils import initial

def move(state, player):
    return dfs.dfsbasic(material_eval.material_eval, state, player)

def format(state):
    if not state: return None
    board = state["board"]
    boardStr = ""
    for i in range(8):
        for j in range(8):
            boardStr += chess_utils.legend[board[i][j]]
        boardStr += '\n'
    return boardStr

state = initial

state["board"] = [
    ['.', '.', '.', '.', '.', '.', '.', '.'],
    ['.', '.', '.', '.', '.', '.', '.', '.'],
    ['.', '.', '.', '.', '.', '.', '.', '.'],
    ['.', '.', '.', '.', '.', '.', '.', '.'],
    ['.', '.', '.', '.', '.', '.', '.', '.'],
    ['.', '.', '.', '.', '.', '.', '.', '.'],
    ['.', '.', '.', '.', '.', '.', '.', '.'],
    ['.', '.', '.', '.', '.', '.', '.', '.'],
]

state = chess_utils.simulate_move(state, 'Pd2d4', 1)
state = chess_utils.simulate_move(state, 'Pe4d3', 2)
print(format(state))
