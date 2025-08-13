import subprocess
from tournament.bot_runner.persistent_runner import PersistentDockerBot

def auto_lose(turn):
    return str(2 - ((turn + 1) % 2))

def execute(bot1_code, bot2_code, bot1_name, bot2_name, initial_state, verbose=False, *, is_terminal, fetch_result, is_legal_move, make_move, move_types):
    bot1 = PersistentDockerBot(bot1_code, "bot1_container")
    bot2 = PersistentDockerBot(bot2_code, "bot2_container")
    
    state = initial_state
    turn = 0
    history = [initial_state]
    move_history = [[1, None]] # moves: [legal?, move]

    if verbose:
        print("." * 30)

    while not is_terminal(state, turn):
        turn += 1

        current_bot = bot1 if turn % 2 == 1 else bot2
        bot_name = bot1_name if turn % 2 == 1 else bot2_name

        try:
            move = current_bot.send_state(state, 2 - turn%2)
            if verbose:
                print(f"NEXT MOVE ({turn}) from {bot_name}:", move)

            if move is None or not isinstance(move, move_types):
                print(f"[!] Invalid move or crash by {bot_name}: {move}")
                history.append(None)
                move_history.append([0, f"INCORRECT TYPE: {move}"])
                return auto_lose(turn), state, turn, history, move_history

        except subprocess.TimeoutExpired:
            print(f"[!] {bot_name} timed out.")
            history.append(None)
            move_history.append([0, "TIME LIMIT EXCEEDED"])
            return auto_lose(turn), state, turn, history, move_history

        except Exception as e:
            print(f"[!] Exception from {bot_name}: {e}")
            history.append(None)
            move_history.append([0, f"{e}"])
            return auto_lose(turn), state, turn, history, move_history

        if not is_legal_move(state, move, 2 - turn%2):
            print(f"[!] Illegal move by {bot_name}: {move}")
            history.append(None)
            move_history.append([0, f"ILLEGAL MOVE: {move}"])
            return auto_lose(turn), state, turn, history, move_history

        state = make_move(state, move, 2 - turn%2)
        history.append(state)
        move_history.append([1, move])

    result = fetch_result(state)
    print(result, bot1_name if turn % 2 == 1 else bot2_name)
    bot1.shutdown()
    bot2.shutdown()

    if verbose:
        print("." * 30)

    if result == 'D':
        return '0', state, turn, history, move_history
    elif (result == 'W' and turn % 2 == 1) or (result == 'L' and turn % 2 == 0):
        return '1', state, turn, history, move_history
    else:
        return '2', state, turn, history, move_history
