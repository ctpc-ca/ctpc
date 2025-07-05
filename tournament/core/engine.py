from game.termination import is_terminal, fetch_result
from game.gameplay import isLegalMove, makeMove
from game.utils import moveTypes
from bot_runner.docker_runner import run_bot_in_docker

def execute(bot1_code, bot2_code, initial_state):
    state = initial_state
    turn = 0

    while not is_terminal(state, turn):
        turn += 1

        current_bot_code = bot1_code if turn % 2 == 1 else bot2_code

        try:
            move = run_bot_in_docker(current_bot_code, state)

            if move is None or not isinstance(move, moveTypes):
                print(f"[!] Invalid move or bot crash.")
                return {'result': str(2 - ((turn+1) % 2)), 'state':state, 'moves': turn}

        except Exception as e:
            print(f"[!] Exception during bot execution: {e}")
            return {'result': str(2 - ((turn+1) % 2)), 'state':state, 'moves': turn}

        if not isLegalMove(state, move):
            print(f"[!] Illegal move detected")
            return {'result':str(2 - ((turn+1) % 2)), 'state':state, 'moves':turn}  # opponent wins

        state = makeMove(state, move)

    result = fetch_result(state)
    if result == 'D':
        return {'result':'D', 'state':state, 'moves':turn}
    elif (result == 'W' and turn % 2 == 1) or (result == 'L' and turn % 2 == 0):
        return {'result':'1', 'state':state, 'moves':turn}
    else:
        return {'result':'2', 'state':state, 'moves':turn}
