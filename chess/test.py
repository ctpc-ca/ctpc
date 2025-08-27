from dfs import dfsbasic
from evals import material_eval
from game_files.utils import initial
import time

start_time = time.time()

state = initial

state["board"] = [
    ['.', '.', '.', '.', 'K', '.', 'R', 'q'],
    ['.', '.', '.', '.', '.', '.', '.', '.'],
    ['.', '.', '.', '.', '.', '.', '.', '.'],
    ['.', '.', '.', '.', '.', '.', '.', '.'],
    ['.', '.', '.', '.', '.', '.', 'R', '.'],
    ['.', '.', '.', '.', '.', '.', '.', '.'],
    ['.', '.', '.', '.', '.', '.', '.', '.'],
    ['.', '.', '.', '.', 'k', '.', '.', '.'],
]

score, move = dfsbasic(evaluation=material_eval, state=state, move_num=1)

end_time = time.time()

print("CHOSEN MOVE:", move, "with eval", score)
print("TIME TAKEN:", end_time - start_time, "seconds")
