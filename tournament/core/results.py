import time
import subprocess

from core.engine import execute
from game.utils import initial, scoring

# double round-robin simulation, no tiebreaker right now
def return_results(bots):
    print(bots)
    start_time = time.time()
    matches = 0
    moves = 0

    results = {bot:{'score':0, 'win':[], 'draw':[], 'loss':[]} for bot in bots}
    total_matches = len(results) * (len(results) - 1)

    for bot1 in bots:
        for bot2 in bots:
            if bot1 == bot2: continue
            matches += 1

            print("\n" + "=" * 30)
            print(f"RUNNING MATCH {matches} of {total_matches}: {bot1} vs {bot2}")

            match = execute(bots[bot1], bots[bot2], initial)
            outcome = match['result']
            moves += match['moves']

            if outcome == '1':
                results[bot1]['win'].append(bot2 + ' [2]')
                results[bot2]['loss'].append(bot1 + ' [1]')
            elif outcome == '2':
                results[bot1]['loss'].append(bot2 + ' [2]')
                results[bot2]['win'].append(bot1 + ' [1]')
            else:
                results[bot1]['draw'].append(bot2 + ' [2]')
                results[bot2]['draw'].append(bot1 + ' [1]')

            if match['result'] == '1':
                print(f"Result: {bot1} won in {match['moves']} moves")
            elif match['result'] == '2':
                print(f"Result: {bot2} won in {match['moves']} moves")
            else:
                print(f"Result: Draw in {match['moves']} moves")
            subprocess.run("docker ps -aq --filter ancestor=bot-runner | xargs -r docker rm -f", shell=True)
    
    for bot in results:
        results[bot]['score'] = len(results[bot]['win']) * scoring['win'] + len(results[bot]['draw']) * scoring['draw'] + len(results[bot]['loss']) * scoring['loss']

    end_time = time.time()

    print("\n" + "*" * 30)
    print("FINAL STATS:")
    print(str(matches) + " matches played")
    print(str(moves) + " total moves made")
    print(str(moves/(end_time - start_time)) + " average moves per second")
    print(str(end_time - start_time) + "s spent in total")

    return dict(sorted(results.items(), key=lambda item: item[1]['score'],reverse=True))
