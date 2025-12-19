#!/usr/bin/env python3
import sys
import chess
import random

SPEED = 5  # 1 - too slow but smart, 10 - too fast but dumb.

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


# ---------------- MINIMAX ----------------

def minimax(board, depth):
    if depth == 0 or board.is_game_over():
        return evaluate_board(board)

    if board.turn == chess.WHITE:
        best = -float('inf')
        for move in board.legal_moves:
            board.push(move)
            best = max(best, minimax(board, depth - 1))
            board.pop()
        return best
    else:
        best = float('inf')
        for move in board.legal_moves:
            board.push(move)
            best = min(best, minimax(board, depth - 1))
            board.pop()
        return best


def speed_to_depth():
    return max(1, 6 - SPEED // 2)


def choose_move(board):
    depth = speed_to_depth()

    # старт — случайный ход
    if board.fullmove_number == 1:
        return random.choice(list(board.legal_moves))

    best_score = -float('inf') if board.turn == chess.WHITE else float('inf')
    best_moves = []

    for move in board.legal_moves:
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

    return random.choice(best_moves) if best_moves else None


# ---------------- UCI ----------------

def main():
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
                    idx = parts.index("moves") + 1
                    for mv in parts[idx:]:
                        board.push_uci(mv)
            elif "fen" in parts:
                idx = parts.index("fen") + 1
                fen = " ".join(parts[idx:idx + 6])
                board.set_fen(fen)
                if "moves" in parts:
                    idx = parts.index("moves") + 1
                    for mv in parts[idx:]:
                        board.push_uci(mv)

        elif line.startswith("go"):
            move = choose_move(board)
            print("bestmove", move.uci() if move else "0000")

        elif line == "quit":
            break

        sys.stdout.flush()


if __name__ == "__main__":
    main()
