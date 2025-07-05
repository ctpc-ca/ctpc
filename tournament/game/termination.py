def is_terminal(state, move):
    # determine end state here
    if state % 5 == 2 or state >= 50 or move >= 10:
        return True
    return False

def fetch_result(terminal_state):
    # returns 'W' if game is won,
    #         'L' if game is lost,
    #     and 'D' if game is drawn
    if terminal_state % 3 == 0: return 'W'
    elif terminal_state % 3 == 1: return 'D'
    else: return 'L'
    