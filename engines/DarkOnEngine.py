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
strength_profile = "weak"  # Optionen: "weak", "normal"

piece_values = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0
}

center_squares = [chess.D4, chess.E4, chess.D5, chess.E5]

# =====================
# Zeit → Denkzeit Mapping
# =====================
def calculate_think_time(remaining_time_ms):
    t = remaining_time_ms / 1000  # Sekunden

    if t >= 1800:      # 30 Minuten
        return random.uniform(20, 60)
    elif t >= 600:     # 10 Minuten
        return random.uniform(10, 40)
    elif t >= 180:     # 3 Minuten
        return random.uniform(3, 20)
    elif t >= 60:      # 1 Minute
        return random.uniform(1, 10)
    elif t >= 15:      # 15 Sekunden
        return random.uniform(1, 4)
    elif t >= 3:       # 3 Sekunden
        return random.uniform(0.5, 2)
    else:              # < 3 Sekunden
        return 0.02

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
    for piece_type in piece_values:
        score += len(board.pieces(piece_type, chess.WHITE)) * piece_values[piece_type]
        score -= len(board.pieces(piece_type, chess.BLACK)) * piece_values[piece_type]

    # Zentrum
    for square in center_squares:
        piece = board.piece_at(square)
        if piece:
            score += 0.2 if piece.color == chess.WHITE else -0.2

    # Anti-Dame (früh bewegen bestrafen)
    if board.fullmove_number < 10:
        score -= 0.3 * len(board.pieces(chess.QUEEN, chess.WHITE))
        score += 0.3 * len(board.pieces(chess.QUEEN, chess.BLACK))

    # König in Eröffnung stark bestrafen
    if board.fullmove_number < 10:
        white_king_square = board.king(chess.WHITE)
        black_king_square = board.king(chess.BLACK)
        if white_king_square not in (chess.G1, chess.C1):
            score -= 5.0
        if black_king_square not in (chess.G8, chess.C8):
            score += 5.0

    return score

# =====================
# Minimax-Suche
# =====================
def minimax(board, depth):
    if stop_time and time.time() > stop_time:
        return evaluate_board(board)

    if depth == 0 or board.is_game_over():
        return evaluate_board(board)

    if board.turn == chess.WHITE:
        best = -float('inf')
        for move in board.legal_moves:
            # Königzüge in den ersten 10 Zügen blockieren
            if board.fullmove_number < 10 and board.piece_at(move.from_square).piece_type == chess.KING:
                continue
            board.push(move)
            val = minimax(board, depth - 1)
            board.pop()
            best = max(best, val)
        return best
    else:
        best = float('inf')
        for move in board.legal_moves:
            if board.fullmove_number < 10 and board.piece_at(move.from_square).piece_type == chess.KING:
                continue
            board.push(move)
            val = minimax(board, depth - 1)
            board.pop()
            best = min(best, val)
        return best

# =====================
# Züge auswählen
# =====================
def choose_move(board):
    global remaining_time_ms

    if remaining_time_ms < 1000:
        return random.choice(list(board.legal_moves))

    if board.fullmove_number == 1:
        return random.choice(list(board.legal_moves))

    # ---------------------
    # Dynamische Tiefe mit Zwischenwerten
    # ---------------------
    if remaining_time_ms < 15000:          # < 15 s
        depth = 2
    elif remaining_time_ms < 60000:        # < 1 min
        depth = 2
        if random.random() < 0.5:
            depth = 3
    elif remaining_time_ms < 180000:       # < 3 min
        depth = 3
    elif remaining_time_ms < 600000:       # < 10 min
        depth = 3
        if random.random() < 0.5:
            depth = 4
    elif remaining_time_ms < 1800000:      # < 30 min
        depth = 4
    else:                                  # 30+ min
        depth = 3

    best_score = -float('inf') if board.turn == chess.WHITE else float('inf')
    best_moves = []

    for move in board.legal_moves:
        if stop_time and time.time() > stop_time:
            break

        # Königzüge in Eröffnung überspringen
        if board.fullmove_number < 10 and board.piece_at(move.from_square).piece_type == chess.KING:
            continue

        board.push(move)
        score = minimax(board, depth)
        board.pop()

        # Menschliche Ungenauigkeit basierend auf Strength-Profile
        if strength_profile == "weak":
            score += random.uniform(-0.1, 0.1)
        else:  # normal schwach
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

    # Wenn keine zulässigen Züge nach King-Schutz, dann legalen nehmen
    if not best_moves:
        best_moves = [move for move in board.legal_moves]

    return random.choice(best_moves) if best_moves else random.choice(list(board.legal_moves))

# =====================
# Hauptloop
# =====================
def main():
    global remaining_time_ms, stop_time, strength_profile
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
                    for mv in parts[parts.index("moves") + 1:]:
                        board.push_uci(mv)
            elif "fen" in parts:
                fen_index = parts.index("fen")
                fen = " ".join(parts[fen_index + 1:fen_index + 7])
                board.set_fen(fen)
                if "moves" in parts:
                    for mv in parts[parts.index("moves") + 1:]:
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

            target_think_time = calculate_think_time(remaining_time_ms)

            # Rechenabbruch für Minimax
            stop_time = time.time() + min(target_think_time * 0.7, 3.0)

            start = time.time()
            move = choose_move(board)

            # Warten bis Zielzeit erreicht
            elapsed = time.time() - start
            if elapsed < target_think_time:
                time.sleep(target_think_time - elapsed)

            print("bestmove", move.uci() if move else "0000")

        elif line.startswith("setoption name Strength value"):
            val = line.split()[-1].lower()
            if val in ("weak", "normal"):
                strength_profile = val

        elif line == "quit":
            break

        sys.stdout.flush()

if __name__ == "__main__":
    main()
