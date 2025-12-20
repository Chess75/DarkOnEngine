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
    chess.PAWN: 2,
    chess.KNIGHT: 6,
    chess.BISHOP: 6,
    chess.ROOK: 10,
    chess.QUEEN: 18,
    chess.KING: 0
}

center_squares = [chess.D4, chess.E4, chess.D5, chess.E5]

# =====================
# Zeit → Denkzeit Mapping
# =====================
def calculate_think_time(remaining_time_ms):
    t = remaining_time_ms / 1000

    if t >= 1800:
        return random.uniform(20, 30)
    elif t >= 600:
        return random.uniform(12, 20)
    elif t >= 180:
        return random.uniform(3, 12)
    elif t >= 60:
        return random.uniform(1, 6)
    elif t >= 10:
        return random.uniform(0.5, 1)
    else:
        return 0.0

# =====================
# Bewertungsfunktion
# =====================
def evaluate_board(board):
    if board.is_checkmate():
        return 10000 if board.turn == chess.BLACK else -10000
    if board.is_stalemate():
        return 0

    score = 0

    # Material
    for pt in piece_values:
        score += len(board.pieces(pt, chess.WHITE)) * piece_values[pt]
        score -= len(board.pieces(pt, chess.BLACK)) * piece_values[pt]

    # Zentrum
    for sq in center_squares:
        p = board.piece_at(sq)
        if p:
            score += 0.3 if p.color == chess.WHITE else -0.3

    # Anti-Dame früh
    if board.fullmove_number < 15:
        score -= 1.3 * len(board.pieces(chess.QUEEN, chess.WHITE))
        score += 1.3 * len(board.pieces(chess.QUEEN, chess.BLACK))

    # Königssicherheit
    if board.fullmove_number < 30:
        if board.king(chess.WHITE) not in (chess.G1, chess.C1):
            score -= 6.0
        if board.king(chess.BLACK) not in (chess.G8, chess.C8):
            score += 6.0

    return score

# =====================
# Minimax (unverändert)
# =====================
def minimax(board, depth):
    if stop_time and time.time() > stop_time:
        return evaluate_board(board)

    if depth == 0 or board.is_game_over():
        return evaluate_board(board)

    if board.turn == chess.WHITE:
        best = -float('inf')
        for m in board.legal_moves:
            board.push(m)
            best = max(best, minimax(board, depth - 1))
            board.pop()
        return best
    else:
        best = float('inf')
        for m in board.legal_moves:
            board.push(m)
            best = min(best, minimax(board, depth - 1))
            board.pop()
        return best

# =====================
# Zugauswahl (HIER IST DER FIX)
# =====================
def choose_move(board):
    global remaining_time_ms

    if remaining_time_ms < 1000:
        return random.choice(list(board.legal_moves))

    if board.fullmove_number == 1:
        return random.choice(list(board.legal_moves))

    depth = 3  # stabiler als 4

    best_score = -float('inf') if board.turn == chess.WHITE else float('inf')
    best_moves = []

    for move in board.legal_moves:
        if stop_time and time.time() > stop_time:
            break

        board.push(move)
        score = minimax(board, depth)

        # =====================
        # HÄNGENDE-FIGUR-STRAFE
        # =====================
        moved_piece = board.piece_at(move.to_square)
        if moved_piece:
            if board.is_attacked_by(not board.turn, move.to_square):
                score -= piece_values[moved_piece.piece_type] * 3

        board.pop()

        # Sehr kleiner Zufall (menschlich, aber kein Müll)
        score += random.uniform(-0.05, 0.05)

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

    return random.choice(best_moves) if best_moves else random.choice(list(board.legal_moves))

# =====================
# UCI Loop
# =====================
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

        elif line == "ucinewgame":
            board.reset()

        elif line.startswith("position"):
            parts = line.split()
            if "startpos" in parts:
                board.reset()
                if "moves" in parts:
                    for mv in parts[parts.index("moves")+1:]:
                        board.push_uci(mv)
            elif "fen" in parts:
                idx = parts.index("fen")
                board.set_fen(" ".join(parts[idx+1:idx+7]))
                if "moves" in parts:
                    for mv in parts[parts.index("moves")+1:]:
                        board.push_uci(mv)

        elif line.startswith("go"):
            parts = line.split()
            if "wtime" in parts and board.turn == chess.WHITE:
                remaining_time_ms = int(parts[parts.index("wtime")+1])
            if "btime" in parts and board.turn == chess.BLACK:
                remaining_time_ms = int(parts[parts.index("btime")+1])

            think = calculate_think_time(remaining_time_ms)
            stop_time = time.time() + min(think * 0.7, 3.0)

            start = time.time()
            move = choose_move(board)
            elapsed = time.time() - start
            if elapsed < think:
                time.sleep(think - elapsed)

            print("bestmove", move.uci())

        elif line == "quit":
            break

        sys.stdout.flush()

if __name__ == "__main__":
    main()
