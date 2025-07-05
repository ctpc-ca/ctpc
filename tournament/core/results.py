import time
import subprocess

from collections import defaultdict
from tournament.core.engine import execute
from tournament.bot_runner.swiss import run_swiss_tournament

def round_robin(bots, verbose=False, *, initial, scoring, is_terminal, fetch_result, is_legal_move, make_move, move_types):
    start_time = time.time()
    matches = 0
    moves = 0
    game_history = defaultdict(lambda: defaultdict(list))
    match_results = defaultdict(lambda: defaultdict(str))

    results = {
        bot.name: {'score': 0, 'win': [], 'draw': [], 'loss': []}
        for bot in bots
    }
    total_matches = len(bots) * (len(bots) - 1)

    for bot1 in bots:
        for bot2 in bots:
            if bot1.id == bot2.id:
                continue

            matches += 1
            id1 = bot1.name
            id2 = bot2.name

            if verbose:
                print("\n" + "=" * 30)
                print(f"RUNNING MATCH {matches} of {total_matches}: {id1} vs {id2}")

            mOutcome, mState, mMoves, mHistory = execute(bot1.code, bot2.code, id1, id2, initial, verbose=False, is_terminal=is_terminal, fetch_result=fetch_result, is_legal_move=is_legal_move, make_move=make_move, move_types=move_types)
            moves += mMoves
            game_history[id1][id2] = mHistory

            if mOutcome == '1':
                results[id1]['win'].append(f"{id2} [2]")
                results[id2]['loss'].append(f"{id1} [1]")
                result_text = f"{bot1.name} won"
            elif mOutcome == '2':
                results[id1]['loss'].append(f"{id2} [2]")
                results[id2]['win'].append(f"{id1} [1]")
                result_text = f"{bot2.name} won"
            else:
                results[id1]['draw'].append(f"{id2} [2]")
                results[id2]['draw'].append(f"{id1} [1]")
                result_text = "Draw"

            match_results[id1][id2] = result_text

            if verbose:
                outcome_msg = {
                    '1': f"Result: {id1} won in {mMoves} moves",
                    '2': f"Result: {id2} won in {mMoves} moves",
                    None: f"Result: Draw in {mMoves} moves"
                }
                print(outcome_msg[mOutcome])

            subprocess.run(
                "docker ps -aq --filter ancestor=bot-runner | xargs -r docker rm -f",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

    for bot in results:
        results[bot]['score'] = (
            len(results[bot]['win']) * scoring['win'] +
            len(results[bot]['draw']) * scoring['draw'] +
            len(results[bot]['loss']) * scoring['loss']
        )

    end_time = time.time()
    print("\n" + "*" * 30)
    print("ROUND ROBIN STATS:")
    print(f"{matches} matches played")
    print(f"{moves} total moves made")
    print(f"{moves / (end_time - start_time):.2f} average moves per second")
    print(f"{end_time - start_time:.2f}s spent in total")
    print("*" * 30)

    return dict(sorted(results.items(), key=lambda item: item[1]['score'], reverse=True)), game_history,match_results


# sandbox run, twice against all sample bots
def sandbox_results(user_code, sample_bots, *, initial, scoring):
    start_time = time.time()
    matches = 0
    moves_total = 0

    game_history = defaultdict(lambda: defaultdict(list)) # states of each turn of each game
    match_results = defaultdict(lambda: defaultdict(str)) # results of each game

    results = {}

    for sample in sample_bots:
        bot_name = sample.name
        results[bot_name] = {
            "wins": 0,
            "losses": 0,
            "draws": 0,
            "score": 0,
            "details": []
        }

        for i, (p1_code, p2_code, position) in enumerate([
            (user_code, sample.code, "User First"),
            (sample.code, user_code, "User Second")
        ]):
            matches += 1

            bot1_name = "User" if position == "User First" else bot_name
            bot2_name = bot_name if position == "User First" else "User"

            try:
                mOutcome, mState, mMoves, mHistory = execute(
                    p1_code, p2_code, bot1_name, bot2_name, initial, False
                )
                game_history[bot1_name][bot2_name] = mHistory

                if (mOutcome == "1" and p1_code == user_code) or (mOutcome == "2" and p2_code == user_code):
                    results[bot_name]["wins"] += 1
                    result_text = "User won"
                    score = scoring["win"]
                elif mOutcome == "0":
                    results[bot_name]["draws"] += 1
                    result_text = "Draw"
                    score = scoring["draw"]
                else:
                    results[bot_name]["losses"] += 1
                    result_text = "User lost"
                    score = scoring["loss"]

                results[bot_name]["score"] += score
                results[bot_name]["details"].append(result_text)
                match_results[bot1_name][bot2_name] = result_text

            except Exception as e:
                error_msg = f"Error ({position}): {e}"
                results[bot_name]["details"].append(error_msg)
                match_results[bot1_name][bot2_name] = error_msg

            subprocess.run(
                "docker ps -aq --filter ancestor=bot-runner | xargs -r docker rm -f",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

    end_time = time.time()

    print("\n" + "*" * 30)
    print("SANDBOX STATS:")
    print(f"{matches} matches played")
    print(f"{moves_total} total moves made")
    print(f"{moves_total/(end_time - start_time):.2f} average moves per second")
    print(f"{end_time - start_time:.2f}s spent in total")
    print("*" * 30)

    return dict(sorted(results.items(), key=lambda item: item[1]["score"], reverse=True)), game_history, match_results
