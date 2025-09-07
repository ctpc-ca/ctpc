import os
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

from tournament.bot_runner.docker_cleanup import clean_previous_bot_containers
from tournament.core.engine import execute


def run_swiss_tournament(bots, num_rounds, top_k, verbose=False, *, initial, scoring,
                         is_terminal, fetch_result, is_legal_move, make_move, move_types):
    """
    Parallel Swiss: identical signature & behavior to your original function,
    except matches within each round are executed concurrently and we store PGNs.
    """
    # Pre-flight: remove any stragglers from previous crashes
    clean_previous_bot_containers(force=True)

    start = time.time()
    scores = {
        bot.name: {
            "score": 0.0,
            "sb": 0.0,
            "win": 0,
            "draw": 0,
            "loss": 0,
        } for bot in bots
    }
    pairing_history = defaultdict(lambda: defaultdict(float))
    side_counts = defaultdict(lambda: {"first": 0, "second": 0})
    up_down_tracker = defaultdict(bool)
    pairings_log = []
    moves = 0

    # NEW: store PGNs instead of state/move histories
    # (list to allow multiple games per pairing if rematches happen)
    pgn_histories = defaultdict(lambda: defaultdict(list))

    bot_list = {bot.name: bot for bot in bots}
    # Choose a reasonable concurrency (env override allowed)
    try:
        workers_env = int(os.getenv("CTPC_WORKERS", "0"))
    except ValueError:
        workers_env = 0
    max_workers = workers_env if workers_env > 0 else max(1, (os.cpu_count() or 2) - 1)

    print(f"MAX WORKERS: {max_workers}")

    try:
        for round_num in range(num_rounds):
            print(f"--- Running Round {round_num + 1} of {num_rounds} ---")

            # Build score groups once per round (same as original)
            score_groups = defaultdict(list)
            for b in bot_list:
                score_groups[scores[b]["score"]].append(b)

            used = set()
            round_pairs = []          # [(starter, responder)]
            scheduled_matches = []    # [(starter, responder, args_for_execute)]

            # Main pairing logic
            for group_score in sorted(score_groups.keys(), reverse=True):
                group = score_groups[group_score]
                random.shuffle(group)

                i = 0
                while i < len(group):
                    b1 = group[i]
                    if b1 in used:
                        i += 1
                        continue

                    pair_found = False

                    # 1 - Try pairing from the same group
                    for j in range(i + 1, len(group)):
                        b2 = group[j]
                        if b2 not in used and b2 not in pairing_history[b1]:
                            starter, responder = pick_turn_order(b1, b2, side_counts)

                            # Schedule match (defer execution)
                            scheduled_matches.append((
                                starter, responder,
                                (
                                    bot_list[starter].code,
                                    bot_list[responder].code,
                                    starter, responder,
                                    initial, is_terminal, fetch_result, is_legal_move, make_move, move_types
                                )
                            ))
                            round_pairs.append((starter, responder))
                            used.add(b1)
                            used.add(b2)
                            pair_found = True
                            break

                    # 2 - Pair up/down if possible
                    if not pair_found:
                        alt_group_scores = sorted(score_groups.keys(), reverse=True)
                        for alt_score in alt_group_scores:
                            if alt_score == group_score:
                                continue
                            for b2 in score_groups[alt_score]:
                                if b2 not in used and b2 not in pairing_history[b1]:
                                    starter, responder = pick_turn_order(b1, b2, side_counts)

                                    scheduled_matches.append((
                                        starter, responder,
                                        (
                                            bot_list[starter].code,
                                            bot_list[responder].code,
                                            starter, responder,
                                            initial, is_terminal, fetch_result, is_legal_move, make_move, move_types
                                        )
                                    ))
                                    round_pairs.append((starter, responder))
                                    used.add(b1)
                                    used.add(b2)
                                    up_down_tracker[b1] = True
                                    up_down_tracker[b2] = True
                                    pair_found = True
                                    break
                            if pair_found:
                                break

                    # 3 - Resort to rematches
                    if not pair_found:
                        alt_group_scores = sorted(score_groups.keys(), reverse=True)
                        for alt_score in alt_group_scores:
                            for b2 in score_groups[alt_score]:
                                if b2 != b1 and b2 not in used:
                                    starter, responder = pick_turn_order(b1, b2, side_counts)

                                    scheduled_matches.append((
                                        starter, responder,
                                        (
                                            bot_list[starter].code,
                                            bot_list[responder].code,
                                            starter, responder,
                                            initial, is_terminal, fetch_result, is_legal_move, make_move, move_types
                                        )
                                    ))
                                    round_pairs.append((starter, responder))
                                    used.add(b1)
                                    used.add(b2)
                                    if verbose:
                                        print(f"[INFO] Fallback rematch: {b1} vs {b2}")
                                    pair_found = True
                                    break
                            if pair_found:
                                break

                    i += 1

            # Parallel execution
            # Collect: (starter, responder, outcome, moves, pgn_str)
            results_this_round = []

            def _worker(args_tuple):
                _starter, _responder, _exec_args = args_tuple
                (p1_code, p2_code, id1, id2, _initial,
                 _is_terminal, _fetch_result, _is_legal_move, _make_move, _move_types) = _exec_args

                # Execute now returns (mOutcome, mState, mMoves, pgn_str)
                mOutcome, mState, mMoves, pgn_str = execute(
                    p1_code, p2_code, id1, id2,
                    initial_state=_initial, verbose=False,
                    is_terminal=_is_terminal,
                    fetch_result=_fetch_result,
                    is_legal_move=_is_legal_move,
                    make_move=_make_move,
                    move_types=_move_types
                )
                return _starter, _responder, mOutcome, mMoves, pgn_str

            if scheduled_matches:
                with ThreadPoolExecutor(max_workers=max_workers) as pool:
                    futures = [pool.submit(_worker, sm) for sm in scheduled_matches]
                    for fut in as_completed(futures):
                        results_this_round.append(fut.result())

            # Fold results back
            round_pairs_with_results = []
            for starter, responder, mOutcome, mMoves, pgn_str in results_this_round:
                moves += mMoves
                # Record the raw PGN string for this game
                pgn_histories[starter][responder].append(pgn_str or "")
                update_scores_and_history(mOutcome, starter, responder, scores, scoring, pairing_history, side_counts)
                round_pairs_with_results.append((starter, responder, mOutcome))

            pairings_log.append(round_pairs_with_results)

        # SB tiebreaks
        get_sb(scores, pairing_history)

        end = time.time()
        print("\n" + "*" * 30)
        print("SWISS STATS:")
        print(str(num_rounds * len(bot_list) // 2) + " matches played")
        print(str(moves) + " total moves made")
        print(str(moves / (end - start)) + " average moves per second")
        print(str(end - start) + "s spent in total")
        print("*" * 30)

        top_bots = sorted(bot_list, key=lambda b: (-scores[b]["score"], -scores[b]["sb"], random.random()))[:top_k]

        if verbose:
            print("TOP BOTS", top_bots)
            print("SCORES", scores)

        return top_bots, scores, pairings_log, pgn_histories

    finally:
        # Post-run: remove any stopped containers with our label
        clean_previous_bot_containers(force=False)


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
    for bot in history:
        for opponent in history[bot]:
            scores[bot]["sb"] += history[bot][opponent] * scores[opponent]["score"]
    return scores
