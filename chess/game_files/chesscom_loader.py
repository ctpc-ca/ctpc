from datetime import date

def to_pgn_movelist(movelist):
    body_lines = []
    for i in range(0, len(movelist), 2):
        white_move = movelist[i]
        black_move = movelist[i + 1] if i + 1 < len(movelist) else ""
        turn = f"{i//2 + 1}. {white_move} {black_move}".strip()
        body_lines.append(turn)

    body = "\n".join(body_lines)
    return body


print(to_pgn_movelist(

['a3', 'a6', 'a4', 'b6', 'b3', 'c6', 'Bc1b2', 'd6', 'Bb2xg7', 'Bf8xg7', 'a5', 'Bg7xa1', 'axb6', 'Qd8xb6', 'b4', 'Qb6xb4', 'c3', 'Qb4xb1', 'Qd1xb1', 'Ba1xc3', 'dxc3', 'Ke8d7', 'Qb1xb8', 'Ra8xb8', 'Ke1d2', 'Kd7e8', 'Kd2e3', 'Ke8d7', 'Ke3d4', 'Kd7e8', 'Kd4e3', 'Ke8d7', 'Ke3d4', 'Kd7e8', 'Kd4e3']

))

