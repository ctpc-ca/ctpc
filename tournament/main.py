from core.loader import load_bots
from core.results import return_results
from core.leaderboard import print_lb

final_lb = return_results(load_bots("bots"))
print_lb(final_lb)