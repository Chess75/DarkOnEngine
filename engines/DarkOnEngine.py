#!/usr/bin/env python3
import sys
import chess
import random
import time

# =====================
# Globale Zeitvariablen
# =====================
remaining_time_ms = 10000
stop_time = None

piece_values = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0
}

center_squares = [chess.D4, chess.E4, chess.D5, chess.E5]


def evaluate_board(board):
    if board.is_checkmate():
        return 10000 if board.turn == chess.BLACK else -10000
    if board.is_stalemate():
        return 0

    score = 0
    for piece_type in piece_values:
        score += len(board.pieces(piece_type, chess.WHITE)) * piece_values[piece_type]
        score -= len(board.pieces(piece_type, chess.BLACK)) * piece_values[piece_type]

    for square in center_squares:
        piece = board.piece_at(square)
        if piece:
            score += 0.2 if piece.color == chess.WHITE else -0.2

    return score


def minimax(board, depth):
    # Zeitabbruch
    if stop_time and time.time() > stop_time:
        return evaluate_board(board)

    if depth == 0 or board.is_game_over():
        return evaluate_board(board)

    legal_moves = list(board.legal_moves)

    if board.turn == chess.WHITE:
        max_eval = -float('inf')
        for move in legal_moves:
            board.push(move)
            eval = minimax(board, depth - 1)
            board.pop()
            if eval > max_eval:
                max_eval = eval
        return max_eval
    else:
        min_eval = float('inf')
        for move in legal_moves:
            board.push(move)
            eval = minimax(board, depth - 1)
            board.pop()
            if eval < min_eval:
                min_eval = eval
        return min_eval


def choose_move(board):
    global remaining_time_ms

    # Panikmodus
    if remaining_time_ms < 1000:
        return random.choice(list(board.legal_moves))

    # Zufälliger erster Zug
    if board.fullmove_number == 1:
        return random.choice(list(board.legal_moves))

    # Dynamische Tiefe
    depth = 2
    if remaining_time_ms > 60000:
        depth = 3
    if remaining_time_ms > 180000:
        depth = 4

    best_score = -float('inf') if board.turn == chess.WHITE else float('inf')
    best_moves = []

    for move in board.legal_moves:
        if stop_time and time.time() > stop_time:
            break

        board.push(move)
        score = minimax(board, depth)
        board.pop()

        if board.turn == chess.WHITE:
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)
        else:
            if score < best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)

    if best_moves:
        return random.choice(best_moves)

    return random.choice(list(board.legal_moves))


def main():
    global remaining_time_ms, stop_time

    board = chess.Board()

    while True:
        line = sys.stdin.readline()
        if not line:
            break
        line = line.strip()

        if line == "uci":
            print("id name DarkOnEngine")
            print("id author Dark and Classic")
            print("uciok")

        elif line == "isready":
            print("readyok")

        elif line.startswith("ucinewgame"):
            board.reset()

        elif line.startswith("position"):
            parts = line.split()
            if "startpos" in parts:
                board.reset()
                if "moves" in parts:
                    moves = parts[parts.index("moves") + 1:]
                    for mv in moves:
                        board.push_uci(mv)
            elif "fen" in parts:
                fen_index = parts.index("fen")
                fen_str = " ".join(parts[fen_index + 1:fen_index + 7])
                board.set_fen(fen_str)
                if "moves" in parts:
                    moves = parts[parts.index("moves") + 1:]
                    for mv in moves:
                        board.push_uci(mv)

        elif line.startswith("go"):
            parts = line.split()
            wtime = btime = None

            if "wtime" in parts:
                wtime = int(parts[parts.index("wtime") + 1])
            if "btime" in parts:
                btime = int(parts[parts.index("btime") + 1])

            if board.turn == chess.WHITE and wtime is not None:
                remaining_time_ms = wtime
            elif board.turn == chess.BLACK and btime is not None:
                remaining_time_ms = btime

            # 2 % der Restzeit (min 50 ms, max 2000 ms)
            think_time_ms = max(50, min(2000, int(remaining_time_ms * 0.02)))
            stop_time = time.time() + think_time_ms / 1000

            move = choose_move(board)
            print("bestmove", move.uci() if move else "0000")

        elif line == "quit":
            break

        sys.stdout.flush()


if __name__ == "__main__":
    main()
