from core.loader import load_bots
from core.results import single_result
from core.leaderboard import print_sandbox

from user.player_bot import move

bots = load_bots("bots_test")
result = single_result(move, bots)
print_sandbox(result)
