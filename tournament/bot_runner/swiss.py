import random
import time

from collections import defaultdict
from tournament.core.engine import execute

def run_swiss_tournament(bots, num_rounds, top_k, verbose=False, *, initial, scoring, is_terminal, fetch_result, is_legal_move, make_move, move_types):
    start = time.time()
    scores = {
        bot.name: {
            "score": 0,
            "sb": 0,
            "win": 0,
            "draw": 0,
            "loss": 0,
        } for bot in bots
    }
    pairing_history = defaultdict(lambda: defaultdict(float))
    state_histories = defaultdict(lambda: defaultdict(list))
    move_histories = defaultdict(lambda: defaultdict(list))
    side_counts = defaultdict(lambda: {"first": 0, "second": 0})
    up_down_tracker = defaultdict(bool)
    pairings_log = []
    moves = 0

    bot_list = {bot.name : bot for bot in bots}

    for round_num in range(num_rounds):
        if verbose: print(f"--- Round {round_num + 1} of {num_rounds} ---")

        score_groups = defaultdict(list)
        for b in bot_list:
            score_groups[scores[b]["score"]].append(b)

        used = set()
        round_pairs = []

        for group_score in sorted(score_groups.keys(), reverse=True):
            group = score_groups[group_score]
            random.shuffle(group)

            i = 0
            while i < len(group):
                b1 = group[i]
                if b1 in used:
                    i += 1
                    continue

                # try group pairing
                pair_found = False
                for j in range(i + 1, len(group)):
                    b2 = group[j]
                    if b2 not in used and b2 not in pairing_history[b1]:
                        starter, responder = pick_turn_order(b1, b2, side_counts)
                        mOutcome, mState, mMoves, sHistory, mHistory = execute(bot_list[starter].code,
                                                                               bot_list[responder].code,
                                                                               starter,
                                                                               responder,
                                                                               initial_state=initial,
                                                                               verbose=False,
                                                                               is_terminal=is_terminal,
                                                                               fetch_result=fetch_result,
                                                                               is_legal_move=is_legal_move,
                                                                               make_move=make_move,
                                                                               move_types=move_types)
                        result = mOutcome
                        moves += mMoves
                        state_histories[starter][responder] = sHistory
                        move_histories[starter][responder] = mHistory

                        update_scores_and_history(result, starter, responder, scores, scoring, pairing_history, side_counts)
                        round_pairs.append((starter, responder, result))
                        used.add(b1)
                        used.add(b2)
                        pair_found = True
                        break

                if not pair_found: # up/down pairings
                    alt_group_scores = sorted(score_groups.keys(), reverse=True)
                    for alt_score in alt_group_scores:
                        if alt_score == group_score:
                            continue
                        for b2 in score_groups[alt_score]:
                            if b2 not in used and b2 not in pairing_history[b1]:
                                starter, responder = pick_turn_order(b1, b2, side_counts)
                                mOutcome, mState, mMoves, sHistory, mHistory = execute(bot_list[starter].code,
                                                                                       bot_list[responder].code,
                                                                                       starter,
                                                                                       responder,
                                                                                       initial_state=initial,
                                                                                       verbose=False,
                                                                                       is_terminal=is_terminal,
                                                                                       fetch_result=fetch_result,
                                                                                       is_legal_move=is_legal_move,
                                                                                       make_move=make_move,
                                                                                       move_types=move_types)
                                result = mOutcome
                                moves += mMoves
                                state_histories[starter][responder] = sHistory
                                move_histories[starter][responder] = mHistory

                                update_scores_and_history(result, starter, responder, scores, scoring, pairing_history, side_counts)
                                round_pairs.append((starter, responder, result))
                                used.add(b1)
                                used.add(b2)
                                up_down_tracker[b1] = True
                                up_down_tracker[b2] = True
                                pair_found = True
                                break
                        if pair_found:
                            break

                if not pair_found: # last resort - rematches
                    for alt_score in alt_group_scores:
                        for b2 in score_groups[alt_score]:
                            if b2 != b1 and b2 not in used:
                                starter, responder = pick_turn_order(b1, b2, side_counts)
                                mOutcome, mState, mMoves, sHistory, mHistory = execute(
                                    bot_list[starter].code,
                                    bot_list[responder].code,
                                    starter,
                                    responder,
                                    initial_state=initial,
                                    verbose=False,
                                    is_terminal=is_terminal,
                                    fetch_result=fetch_result,
                                    is_legal_move=is_legal_move,
                                    make_move=make_move,
                                    move_types=move_types,
                                )
                                result = mOutcome
                                moves += mMoves
                                state_histories[starter][responder] = sHistory
                                move_histories[starter][responder] = mHistory

                                update_scores_and_history(
                                    result, starter, responder,
                                    scores, scoring, pairing_history, side_counts
                                )
                                round_pairs.append((starter, responder, result))
                                used.add(b1)
                                used.add(b2)
                                print(f"[INFO] Fallback rematch: {b1} vs {b2}")
                                pair_found = True
                                break
                        if pair_found:
                            break
                i += 1

        pairings_log.append(round_pairs)

    get_sb(scores, pairing_history)

    end = time.time()

    print("\n" + "*" * 30)
    print("SWISS STATS:")
    print(str(num_rounds * len(bot_list) // 2) + " matches played")
    print(str(moves) + " total moves made")
    print(str(moves/(end - start)) + " average moves per second")
    print(str(end - start) + "s spent in total")
    print("*" * 30)

    top_bots = sorted(bot_list, key=lambda b: (-scores[b]["score"], -scores[b]["sb"], random.random()))[:top_k]
    
    print("TOP BOTS", top_bots)
    print("SCORES", scores)
    
    return top_bots, scores, pairings_log, state_histories, move_histories

def pick_turn_order(bot1, bot2, side_counts):
    b1_firsts = side_counts[bot1]['first']
    b1_seconds = side_counts[bot1]['second']
    b2_firsts = side_counts[bot2]['first']
    b2_seconds = side_counts[bot2]['second']
    if b1_firsts <= b1_seconds and b2_seconds <= b2_firsts:
        return bot1, bot2
    else:
        return bot2, bot1

def update_scores_and_history(result, starter, responder, scores, scoring, history, side_counts):
    win_score = float(scoring['win'])
    loss_score = float(scoring['loss'])
    draw_score = float(scoring['draw'])

    if result == '1':
        scores[starter]["score"] += win_score
        scores[starter]["win"] += 1
        scores[responder]["loss"] += 1
        history[starter][responder] = win_score
        history[responder][starter] = loss_score
    elif result == '2':
        scores[responder]["score"] += win_score
        scores[responder]["win"] += 1
        scores[starter]["loss"] += 1
        history[starter][responder] = loss_score
        history[responder][starter] = win_score
    else:
        scores[starter]["score"] += draw_score
        scores[responder]["score"] += draw_score
        scores[starter]["draw"] += 1
        scores[responder]["draw"] += 1
        history[starter][responder] = draw_score
        history[responder][starter] = draw_score


    side_counts[starter]['first'] += 1
    side_counts[responder]['second'] += 1

def get_sb(scores, history):
    # print("SCORES", scores)
    # print("HISTORY", history)
    for bot in history:
        for opponent in history[bot]:
            scores[bot]["sb"] += history[bot][opponent] * scores[opponent]["score"]
    return scores
