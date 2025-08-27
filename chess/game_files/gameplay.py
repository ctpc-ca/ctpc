import copy
import chess.chess_utils as chess_utils

def is_legal_move(state, move, player):
    return (move in chess_utils.get_legal_moves(state, player))

def make_move(state, move, player):
    return chess_utils.simulate_move(state, move, player)
