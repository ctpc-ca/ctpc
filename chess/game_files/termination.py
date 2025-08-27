from chess import chess_utils

def is_terminal(state, move):
    legal_moves_white = chess_utils.get_legal_moves(state, 1)
    legal_moves_black = chess_utils.get_legal_moves(state, 2)

    # checkmate/stalemate
    if (len(legal_moves_white) == 0 and move % 2 == 1) or (len(legal_moves_black) == 0 and move % 2 == 0): return True

    # 3-fold repetition
    if chess_utils.is_3_fold(state["hdict"]): return True

    # 50-move rule
    if chess_utils.is_50_move_rule(state["history"]): return True

    # insufficient material
    if chess_utils.is_insufficient_material(state["board"]): return True

    return False


def fetch_result(terminal_state):
    white_check = chess_utils.is_check(terminal_state, 1)
    black_check = chess_utils.is_check(terminal_state, 2)
    legal_moves_white = chess_utils.get_legal_moves(terminal_state, 1)
    legal_moves_black = chess_utils.get_legal_moves(terminal_state, 2)

    if len(legal_moves_white) == 0 or len(legal_moves_black) == 0:
        if not white_check and not black_check: return 'D' # stalemate
        return 'W' # checkmate

    return 'D' # 3-fold, 50-move rule

    