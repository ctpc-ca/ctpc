def isLegalMove(state, move):
    if type(move).__name__ == 'int': return True
    return False

def makeMove(state, move):
    # modify "state" according to "move"
    return state + move