material_table = {
    'p': 1,
    'n': 3,
    'b': 3,
    'r': 5,
    'q': 9,
    'P': -1,
    'N': -3,
    'B': -3,
    'R': -5,
    'Q': -9
}

def material_eval(state, player):
    board = state["board"]
    material_count = 0
    for i in range(8):
        for j in range(8):
            if board[i][j] in material_table:
                material_count += material_table[board[i][j]]
    if player == 2: material_count *= -1
    return material_count