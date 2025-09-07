import subprocess
from tournament.bot_runner.persistent_runner import PersistentDockerBot
from chess.chess_utils import to_pgn_movelist

def auto_lose(turn):
    return str(2 - ((turn + 1) % 2))

def execute(bot1_code, bot2_code, bot1_name, bot2_name, initial_state, verbose=False, *,
            is_terminal, fetch_result, is_legal_move, make_move, move_types):
    bot1 = PersistentDockerBot(bot1_code, "bot1_container")
    bot2 = PersistentDockerBot(bot2_code, "bot2_container")

    state = initial_state
    turn = 0
    # history = [initial_state]
    # move_history = [[1, None]]  # [legal?, move]

    final_outcome = None
    final_turn = None
    final_state = None

    try:
        if verbose:
            print("." * 30)

        while True:
            turn += 1
            # print(f"move {turn}")
            current_bot = bot1 if turn % 2 == 1 else bot2
            bot_name = bot1_name if turn % 2 == 1 else bot2_name

            try:
                move = current_bot.send_state(state, 2 - turn % 2)

                if verbose:
                    print(f"NEXT MOVE ({turn}) from {bot_name}:", move)

                if move is None or not isinstance(move, move_types):
                    print(f"[!] Invalid move or crash by {bot_name}: {move}")
                    # history.append(None)
                    # move_history.append([0, f"INCORRECT TYPE: {move}"])
                    final_outcome, final_state, final_turn = auto_lose(turn), state, turn
                    break

            except subprocess.TimeoutExpired:
                print(f"[!] {bot_name} timed out.")
                # history.append(None)
                # move_history.append([0, "TIME LIMIT EXCEEDED"])
                final_outcome, final_state, final_turn = auto_lose(turn), state, turn
                break

            except Exception as e:
                print(f"[!] Exception from {bot_name}: {e}")
                # history.append(None)
                # move_history.append([0, f"{e}"])
                final_outcome, final_state, final_turn = auto_lose(turn), state, turn
                break

            if not is_legal_move(state, move, 2 - turn % 2):
                print(f"[!] Illegal move by {bot_name}: {move}")
                # history.append(None)
                # move_history.append([0, f"ILLEGAL MOVE: {move}"])
                final_outcome, final_state, final_turn = auto_lose(turn), state, turn
                break

            state = make_move(state, move, 2 - turn % 2)
            # history.append(state)
            # move_history.append([1, move])

            if is_terminal(state, turn) and "movelist" in state:
                # print("MOVE LIST:", state["movelist"])
                # decide winner after loop
                final_state, final_turn = state, turn
                break

        # If we already decided (crash/illegal/timeout), return that
        if final_outcome is not None:
            if verbose:
                print("." * 30)
            pgn_str = to_pgn_movelist(final_state["movelist"])
            if final_outcome == '1': print(f"{bot1_name} vs {bot2_name}: 1-0")
            elif final_outcome == '2': print(f"{bot1_name} vs {bot2_name}: 0-1")
            else: print(f"{bot1_name} vs {bot2_name}: 0.5-0.5")
            return final_outcome, final_state, final_turn, pgn_str

        # Otherwise, compute from terminal position
        result = fetch_result(final_state)

        if result == 'W':
            print(f"{bot1_name} vs {bot2_name}: 1-0" if final_turn % 2 == 1 else f"{bot1_name} vs {bot2_name}: 0-1")
        elif result == 'L':
            print(f"{bot1_name} vs {bot2_name}: 0-1" if final_turn % 2 == 1 else f"{bot1_name} vs {bot2_name}: 1-0")
        else:
            print(f"{bot1_name} vs {bot2_name}: 0.5-0.5")

        if verbose:
            print("." * 30)

        pgn_str = to_pgn_movelist(final_state["movelist"])
        if result == 'D':
            return '0', final_state, final_turn, pgn_str
        elif (result == 'W' and final_turn % 2 == 1) or (result == 'L' and final_turn % 2 == 0):
            return '1', final_state, final_turn, pgn_str
        else:
            return '2', final_state, final_turn, pgn_str

    finally:
        try: bot1.shutdown()
        finally:
            bot2.shutdown()
