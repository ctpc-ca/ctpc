from . import chess_utils, termination, gameplay

def rcsvdfs(evaluation, depth, state, player, move_num):
    legal_moves = chess_utils.get_legal_moves(state, player)

    if termination.is_terminal(state, move_num):
        result = termination.fetch_result(state)
        if result == 'D':
            return 0, None
        else:
            # Current player is being checkmated
            return float('-inf'), None

    best_score = float('-inf')
    best_move = legal_moves[0]

    for move in legal_moves:
        new_state = gameplay.make_move(state, move, player)
        next_player = 2 if player == 1 else 1
        if depth == 1:
            score = evaluation(new_state, player)
        else:
            score, _ = rcsvdfs(evaluation, depth - 1, new_state, next_player, move_num + 1)
            score = -score  # because opponent is choosing next
        if score > best_score:
            best_score = score
            best_move = move

    return best_score, best_move

def dfsbasic(evaluation, state, move_num):
    return rcsvdfs(evaluation, 2, state, 2 - move_num%2, move_num)[1]


