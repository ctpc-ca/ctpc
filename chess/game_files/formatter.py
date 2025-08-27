import chess.chess_utils as chess_utils

def format(state):
    if not state: return None
    board = state["board"]
    boardStr = ""
    for i in range(8):
        for j in range(8):
            boardStr += chess_utils.legend[board[i][j]]
        boardStr += '\n'
    return boardStr
