# dfs.py
from . import chess_utils, gameplay
import time

INF = 10**12

time_limit = 0.5

def dfsopponenteval(evaluation, state, opponent):
    movelist = chess_utils.get_legal_moves(state, opponent)

    if len(movelist) == 0:
        if chess_utils.is_check(state, opponent): return INF
        else: return 0
    
    # curr_eval

    best_eval = INF
    
    for move in movelist:
        new_state = chess_utils.simulate_move(state, move, opponent)
        curr_eval = evaluation(new_state, 3 - opponent)
        best_eval = min(best_eval, curr_eval)

    return best_eval

def dfsbasic(evaluation, state, player):
    movelist = chess_utils.get_legal_moves(state, player)
    # evaluation(state, player) -> number
    if len(movelist) == 0: return None, []

    start_time = time.time()
    end_time = start_time + time_limit

    scored = []

    for move in movelist:
        if time.time() >= end_time:
            break
        new_state = chess_utils.simulate_move(state, move, player)
        curr_eval = evaluation(new_state, player)
        scored.append([curr_eval, move, new_state])
    
    scored.sort(reverse=True)

    considered = []

    while time.time() < end_time and len(scored) > 0:
        [next_eval, next_move, next_state] = scored.pop(0)
        eval2 = dfsopponenteval(evaluation, next_state, 3 - player)
        considered.append([eval2, next_move])

    considered.sort(reverse=True)
    return considered[0][1]


