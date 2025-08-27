import copy
from datetime import date

initial_board = [
    ["R", "N", "B", "Q", "K", "B", "N", "R"],
    ["P", "P", "P", "P", "P", "P", "P", "P"],
    [".", ".", ".", ".", ".", ".", ".", "."],
    [".", ".", ".", ".", ".", ".", ".", "."],
    [".", ".", ".", ".", ".", ".", ".", "."],
    [".", ".", ".", ".", ".", ".", ".", "."],
    ["p", "p", "p", "p", "p", "p", "p", "p"],
    ["r", "n", "b", "q", "k", "b", "n", "r"]
]

initial = {
    "board": initial_board,
    "E1K": False,
    "E8K": False,
    "A1R": False,
    "A8R": False,
    "H1R": False,
    "H8R": False,
    "prev_move": None,
    "history": [initial_board],
    "hdict": {"RNBQKBNRPPPPPPPP................................pppppppprnbqkbnr":1},
    "movelist": []
}

legend = {
    'p': '♙',
    'n': '♘',
    'b': '♗',
    'r': '♖',
    'q': '♕',
    'k': '♔',
    'P': '♟',
    'N': '♞',
    'B': '♝',
    'R': '♜',
    'Q': '♛',
    'K': '♚',
    '.': '.'
}

piece_values = {
    'p': 1,
    'P': 1,
    'n': 3,
    'N': 3,
    'b': 3,
    'B': 3,
    'r': 5,
    'R': 5,
    'q': 9,
    'Q': 9
}

non_pawns = "NBRQ"

def format_board(state):
    board = state["board"]
    for i in range(8):
        row = ""
        for j in range(8):
            row += legend[board[i][j]]
        print(row)

def format_attacked_squares(grid):
    for i in range(8):
        row = ""
        for j in range(8):
            if grid[i][j]: row += '#'
            else: row += '.'
        print(row)



def to_pgn_movelist(movelist):
    body_lines = []
    for i in range(0, len(movelist), 2):
        white_move = movelist[i]
        black_move = movelist[i + 1] if i + 1 < len(movelist) else ""
        turn = f"{i//2 + 1}. {white_move} {black_move}".strip()
        body_lines.append(turn)

    body = "\n".join(body_lines)
    return body



def count_pieces(board):
    empty_spaces = 0
    for row in board:
        for square in row:
            if square == '.':
                empty_spaces += 1

    return 64 - empty_spaces

def is_equal_pawns(p1, p2):
    for i in range(8):
        for j in range(8):
            s1, s2 = p1[i][j], p2[i][j]
            if s1 in ('p', 'P') and s2 != s1:
                return True  # Pawn moved from this square
            if s2 in ('p', 'P') and s1 != s2:
                return True  # Pawn moved to this square
    return False  # No pawn moved


universal_attacks = {
    "knight": {
        "offsets": [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                    (1, -2), (1, 2), (2, -1), (2, 1)],
        "slide": False
    },
    "bishop": {
        "offsets": [(-1, -1), (-1, 1), (1, -1), (1, 1)],
        "slide": True
    },
    "rook": {
        "offsets": [(-1, 0), (1, 0), (0, -1), (0, 1)],
        "slide": True
    },
    "queen": {
        "offsets": [(-1, -1), (-1, 1), (1, -1), (1, 1),
                    (-1, 0), (1, 0), (0, -1), (0, 1)],
        "slide": True
    },
    "king": {
        "offsets": [(-1, -1), (-1, 1), (1, -1), (1, 1),
                    (-1, 0), (1, 0), (0, -1), (0, 1)],
        "slide": False
    }
}

attack_patterns = {
    'p': {
        "offsets": [(-1, -1), (-1, 1)],
        "slide": False
    },
    'P': {
        "offsets": [(1, -1), (1, 1)],
        "slide": False
    },
    'n': universal_attacks["knight"],
    'N': universal_attacks["knight"],
    'b': universal_attacks["bishop"],
    'B': universal_attacks["bishop"],
    'r': universal_attacks["rook"],
    'R': universal_attacks["rook"],
    'q': universal_attacks["queen"],
    'Q': universal_attacks["queen"],
    'k': universal_attacks["king"],
    'K': universal_attacks["king"]
}

def is_empty(board, row, col):
    return board[row][col] == '.'

def is_enemy_piece(piece, player):
    if piece == '.': return False
    return (piece.isupper() and player == 1) or (piece.islower() and player == 2)

def is_players_piece(piece, player):
    if piece == '.': return False
    return not is_enemy_piece(piece, player)

def pos_to_coord(row, col):
    return chr(ord('a') + col) + str(8 - row)

def coord_to_pos(coord):
    col = ord(coord[0]) - ord('a')
    row = 8 - int(coord[1])
    return row, col

def in_bounds(row, col):
    return 0 <= row < 8 and 0 <= col < 8

def get_attacked_squares(state, player):
    board = state["board"]
    attacked_grid = [[0 for _ in range(8)] for _ in range(8)]

    # print("ATTACK SCAN ON BOARD", board)

    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if not is_enemy_piece(piece, player):
                continue

            if piece not in attack_patterns:
                print(f"[!!!] Invalid piece in get_attacked_squares: {repr(piece)} at ({row}, {col})")
                raise ValueError(f"Unexpected piece {piece} found on board!")

            pattern = attack_patterns[piece]

            for dr, dc in pattern["offsets"]:
                r, c = row + dr, col + dc

                if pattern["slide"]:
                    while in_bounds(r, c):
                        attacked_grid[r][c] = 1
                        if not is_empty(board, r, c):
                            break
                        r += dr
                        c += dc
                else:
                    if in_bounds(r, c):
                        attacked_grid[r][c] = 1

    return attacked_grid

def get_castling_moves(state, player):
    board = state["board"]
    moves = []
    attacked = get_attacked_squares(state, player)

    if player == 1:  # white
        king_row = 7

        if not state["E1K"] and not state["H1R"]: # short
            if (board[king_row][4] == 'k' and board[king_row][7] == 'r' and
                board[king_row][5] == '.' and board[king_row][6] == '.' and
                attacked[king_row][4] == 0 and  # e1
                attacked[king_row][5] == 0 and  # f1
                attacked[king_row][6] == 0):    # g1
                moves.append("O-O")
        
        if not state["E1K"] and not state["A1R"]: # long
            if (board[king_row][4] == 'k' and board[king_row][0] == 'r' and
                board[king_row][1] == '.' and board[king_row][2] == '.' and board[king_row][3] == '.' and
                attacked[king_row][4] == 0 and  # e1
                attacked[king_row][3] == 0 and  # d1
                attacked[king_row][2] == 0):    # c1
                moves.append("O-O-O")

    else:  # black
        king_row = 0
        
        if not state["E8K"] and not state["H8R"]: # short
            if (board[king_row][4] == 'K' and board[king_row][7] == 'R' and
                board[king_row][5] == '.' and board[king_row][6] == '.' and
                attacked[king_row][4] == 0 and  # e8
                attacked[king_row][5] == 0 and  # f8
                attacked[king_row][6] == 0):    # g8
                moves.append("O-O")
        
        if not state["E8K"] and not state["A8R"]: # long
            if (board[king_row][4] == 'K' and board[king_row][0] == 'R' and
                board[king_row][1] == '.' and board[king_row][2] == '.' and board[king_row][3] == '.' and
                attacked[king_row][4] == 0 and  # e8
                attacked[king_row][3] == 0 and  # d8
                attacked[king_row][2] == 0):    # c8
                moves.append("O-O-O")

    return moves

def get_en_passant_moves(state, player):
    board = state["board"]
    move = state["prev_move"]
    en_passant_moves = []

    if not move or len(move) != 5:
        return en_passant_moves

    piece = move[0]
    start = move[1:3]
    end = move[3:5]

    # Only consider if opponent just made a 2-step pawn move
    if piece.upper() != 'P':
        return en_passant_moves

    start_row, start_col = coord_to_pos(start)
    end_row, end_col = coord_to_pos(end)

    if abs(start_row - end_row) != 2:
        return en_passant_moves

    # Determine en passant capture square and pawn rank based on player
    if player == 1:  # white (p), capturing black (P) on rank 5 (row 3)
        capture_row = end_row - 1
        pawn_row = 3
        pawn_piece = 'p'
    else:  # player == 2 (black, P), capturing white (p) on rank 4 (row 4)
        capture_row = end_row + 1
        pawn_row = 4
        pawn_piece = 'P'

    for dc in [-1, 1]:  # check left and right of the moved pawn
        adj_col = end_col + dc
        if in_bounds(pawn_row, adj_col) and board[pawn_row][adj_col] == pawn_piece:
            from_sq = pos_to_coord(pawn_row, adj_col)
            to_sq = pos_to_coord(capture_row, end_col)
            move_str = f"{pawn_piece.upper()}{from_sq}{to_sq}"
            en_passant_moves.append(move_str)

    return en_passant_moves

def is_check(state, player):
    board = state["board"]

    king_symbol = 'k' if player == 1 else 'K'
    king_pos = None

    # get king placement
    for row in range(8):
        for col in range(8):
            if board[row][col] == king_symbol:
                king_pos = (row, col)
                break
        if king_pos:
            break

    if not king_pos:
        raise ValueError("NO KING FOUND")

    attacked = get_attacked_squares(state, player)

    return attacked[king_pos[0]][king_pos[1]] == 1

def generate_pawn_moves(state, row, col, player):
    board = state["board"]
    moves = []
    direction = -1 if player == 1 else 1
    start_row = 6 if player == 1 else 1
    promotion_row = 0 if player == 1 else 7
    piece = board[row][col]
    piece_symbol = piece.upper()

    # One square forward
    if in_bounds(row + direction, col) and is_empty(board, row + direction, col):
        dest_row = row + direction
        if dest_row == promotion_row:
            for promo in non_pawns:
                # print(f"[PROMO DEBUG] Adding promotion move: {piece_symbol}{pos_to_coord(row, col)}{pos_to_coord(dest_row, col)}={promo}")
                # print("piece_symbol:", piece_symbol)
                # print("pos_to_coord(row, col):", pos_to_coord(row, col))
                # print("pos_to_coord(dest_row, col):", pos_to_coord(dest_row, col))
                # print("promo:", promo)
                moves.append(f"{piece_symbol}{pos_to_coord(row, col)}{pos_to_coord(dest_row, col)}={promo}")
        else:
            moves.append(f"{piece_symbol}{pos_to_coord(row, col)}{pos_to_coord(dest_row, col)}")

        # Two squares forward
        if row == start_row and is_empty(board, row + 2 * direction, col):
            moves.append(f"{piece_symbol}{pos_to_coord(row, col)}{pos_to_coord(row + 2 * direction, col)}")

    # Captures (diagonals)
    for dc in [-1, 1]:
        c = col + dc
        r = row + direction
        if in_bounds(r, c) and is_enemy_piece(board[r][c], player):
            if r == promotion_row:
                for promo in non_pawns:
                    moves.append(f"{piece_symbol}{pos_to_coord(row, col)}{pos_to_coord(r, c)}={promo}")
            else:
                moves.append(f"{piece_symbol}{pos_to_coord(row, col)}{pos_to_coord(r, c)}")

    return moves

def simulate_move(state, move, player):
    new_state = copy.deepcopy(state)
    board = new_state["board"]

    piece = move[0]
    from_sq = move[1:3]
    to_sq = move[3:5]

    # Castle
    if player == 1:
        if move == "O-O":
            new_state["E1K"] = True
            new_state["H1R"] = True
            board[7][4] = '.'
            board[7][5] = 'r'
            board[7][6] = 'k'
            board[7][7] = '.'
        elif move == "O-O-O":
            new_state["E1K"] = True
            new_state["A1R"] = True
            board[7][0] = '.'
            board[7][2] = 'k'
            board[7][3] = 'r'
            board[7][4] = '.'
        else:
            if from_sq == "e1": new_state["E1K"] = True
            elif from_sq == "a1": new_state["A1R"] = True
            elif from_sq == "h1": new_state["H1R"] = True
    else:
        if move == "O-O":
            new_state["E8K"] = True
            new_state["H8R"] = True
            board[0][4] = '.'
            board[0][5] = 'R'
            board[0][6] = 'K'
            board[0][7] = '.'
        elif move == "O-O-O":
            new_state["E8K"] = True
            new_state["A8R"] = True
            board[0][0] = '.'
            board[0][2] = 'K'
            board[0][3] = 'R'
            board[0][4] = '.'
        else:
            if from_sq == "e8": new_state["E8K"] = True
            elif from_sq == "a8": new_state["A8R"] = True
            elif from_sq == "h8": new_state["H8R"] = True

    if move != "O-O" and move != "O-O-O":
        from_row, from_col = coord_to_pos(from_sq)
        to_row, to_col = coord_to_pos(to_sq)
    
        if '=' in move:
            promotion = move[-1]
        else:
            promotion = None

        # Move piece (promotion handled)

        en_passant = (
            piece.lower() == 'p' and
            from_col != to_col and
            board[to_row][to_col] == '.'
        )

        if en_passant:
            captured_row = to_row + 1 if player == 1 else to_row - 1
            board[captured_row][to_col] = '.'

        if promotion:
            board[to_row][to_col] = promotion.lower() if player == 1 else promotion.upper()
        else:
            board[to_row][to_col] = board[from_row][from_col]

        board[from_row][from_col] = '.'

        # Update prev_move
        new_state["prev_move"] = move

    # Update history
    new_state["history"].append(new_state["board"])
    bstr = board_to_str(new_state["board"])
    new_state["hdict"][bstr] = new_state["hdict"].get(bstr, 0) + 1

    # Detect captures
    capture = (
        count_pieces(state["board"]) !=
        count_pieces(new_state["board"])
    )

    for i in range(8):
        for j in range(8):
            piece = board[i][j]
            if len(piece) > 1 or (piece != '.' and piece not in attack_patterns):
                print(f"[!!!] ABNORMAL PIECE FOUND: {repr(piece)} at ({i},{j}) from move {move}")
                raise ValueError(f"Invalid piece on board: {repr(piece)}")


    # Update movelist
    new_state["movelist"].append(algebraic_notation(move, capture))

    return new_state


def regular_moves(state, player):
    board = state["board"]
    legal_moves = []

    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if not is_players_piece(piece, player):
                continue

            if piece.lower() == 'p':
                legal_moves.extend(generate_pawn_moves(state, row, col, player))
            else:
                legal_moves.extend(generate_piece_moves(state, row, col, piece, player))

    return legal_moves


def generate_piece_moves(state, row, col, piece, player):
    board = state["board"]
    if piece not in attack_patterns:
        print(f"[!!!] Invalid piece {repr(piece)} at ({row},{col})")
        raise ValueError(f"Invalid piece in attack_patterns: {repr(piece)}")

    pattern = attack_patterns[piece]

    moves = []
    piece_symbol = piece.upper()

    for dr, dc in pattern["offsets"]:
        r, c = row + dr, col + dc

        if pattern["slide"]:
            while in_bounds(r, c):
                if is_players_piece(board[r][c], player):
                    break
                moves.append(f"{piece_symbol}{pos_to_coord(row, col)}{pos_to_coord(r, c)}")
                if is_enemy_piece(board[r][c], player):
                    break
                r += dr
                c += dc
        else:
            if in_bounds(r, c) and not is_players_piece(board[r][c], player):
                moves.append(f"{piece_symbol}{pos_to_coord(row, col)}{pos_to_coord(r, c)}")

    return moves

def get_legal_moves(state, player):
    legal_moves = regular_moves(state, player) + get_castling_moves(state, player) + get_en_passant_moves(state, player)
    
    final_moves = []
    for move in legal_moves:
        next_state = simulate_move(state, move, player)
        if not is_check(next_state, player):
            final_moves.append(move)

    return final_moves

def board_to_str(board):
    return ''.join(''.join(row) for row in board)

def algebraic_notation(move, capture):
    if move in ("O-O", "O-O-O"):
        return move

    piece_map = {
        "P": "",
        "N": "N",
        "B": "B",
        "R": "R",
        "Q": "Q",
        "K": "K"
    }

    piece = move[0]
    from_sq = move[1:3]
    to_sq = move[3:5]
    suffix = ""

    if '=' in move:
        parts = move.split('=')
        if len(parts) != 2 or len(parts[1]) != 1:
            raise ValueError(f"Invalid promotion in move: {repr(move)}")
        suffix = f"={parts[1]}"
    else:
        suffix = ""


    if piece == "P":
        if capture:
            return f"{from_sq[0]}x{to_sq}{suffix}"
        else:
            return f"{to_sq}{suffix}"

    if capture:
        return f"{piece_map[piece]}{from_sq}x{to_sq}{suffix}"
    else:
        return f"{piece_map[piece]}{from_sq}{to_sq}{suffix}"

def pos_to_str(board):
    return ''.join(''.join(row) for row in board)

def is_3_fold(hdict):
    return any(val >= 3 for val in hdict.values())

def is_50_move_rule(history):
    if len(history) <= 101: return False
    if count_pieces(history[-101]) > count_pieces(history[-1]): return False
    return is_equal_pawns(history[-101], history[-1])

def is_insufficient_material(board):
    material = 0
    pieces = 0 # not counting kings
    for i in range(8):
        for j in range(8):
            if board[i][j] in piece_values:
                pieces += 1
                material += piece_values[board[i][j]]

    return (material == 0 or (material == 3 and pieces == 1))
