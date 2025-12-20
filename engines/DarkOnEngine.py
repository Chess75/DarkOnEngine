#!/usr/bin/env python3
import sys
import chess
import random
import time

# =====================
# Globale Variablen
# =====================
remaining_time_ms = 10000
stop_time = None
strength_profile = "weak"  # "weak" oder "normal"
last_moves = []  # Letzte bewegte Figuren speichern

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
# Denkzeit abhängig von Restzeit
# =====================
def calculate_think_time(remaining_time_ms):
    t = remaining_time_ms / 1000  # Sekunden

    if t >= 1800:      # 30 Minuten
        return random.uniform(20, 30)
    elif t >= 1200:    # 20 Minuten
        return random.uniform(16, 25)
    elif t >= 600:     # 10 Minuten
        return random.uniform(12, 20)
    elif t >= 420:     # 7 Minuten
        return random.uniform(8, 15)
    elif t >= 300:     # 5 Minuten
        return random.uniform(6, 12)
    elif t >= 180:     # 3 Minuten
        return random.uniform(7, 12)
    elif t >= 60:      # 1 Minute
        return random.uniform(4, 6)
    elif t >= 30:
        return random.uniform(1, 2)
    elif t >= 10:
        return random.uniform(0.5, 1)
    else:
        return 0.05

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
        score -= 1.5 * len(board.pieces(chess.QUEEN, chess.WHITE))
        score += 1.5 * len(board.pieces(chess.QUEEN, chess.BLACK))

    # Anti-König-Gezappel / Rochade
    if board.fullmove_number < 15:
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
            board.push(move)
            val = minimax(board, depth - 1)
            board.pop()
            best = max(best, val)
        return best
    else:
        best = float('inf')
        for move in board.legal_moves:
            board.push(move)
            val = minimax(board, depth - 1)
            board.pop()
            best = min(best, val)
        return best

# =====================
# Züge auswählen
# =====================
def choose_move(board):
    global remaining_time_ms, last_moves

    if remaining_time_ms < 1000:
        return random.choice(list(board.legal_moves))

    if board.fullmove_number == 1:
        return random.choice(list(board.legal_moves))

    # Dynamische Tiefe
    if remaining_time_ms < 15000:
        depth = 2
    elif remaining_time_ms < 60000:
        depth = random.choice([2,3])
    elif remaining_time_ms < 180000:
        depth = 3
    elif remaining_time_ms < 600000:
        depth = random.choice([3,4])
    else:
        depth = 4

    best_score = -float('inf') if board.turn == chess.WHITE else float('inf')
    best_moves = []

    for move in board.legal_moves:
        piece = board.piece_at(move.from_square)

        # König in Eröffnung nicht bewegen
        if board.fullmove_number < 10 and piece.piece_type == chess.KING:
            continue

        board.push(move)
        score = minimax(board, depth)
        board.pop()

        # Prüfen, ob die gezogene Figur sofort angegriffen wird
        piece_after = board.piece_at(move.to_square)
        if piece_after and board.is_attacked_by(not piece_after.color, move.to_square):
            score -= piece_values[piece_after.piece_type] * 5  # stark bestrafen

        # Keine Wiederholung: Figur in den letzten 3 Zügen bewegt?
        if piece in last_moves[-3:]:
            score -= 2.0

        # Kleine menschliche Fehler
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

    if not best_moves:
        best_moves = [m for m in board.legal_moves]

    chosen_move = random.choice(best_moves)

    # Letzte Züge aktualisieren
    moved_piece = board.piece_at(chosen_move.from_square)
    last_moves.append(moved_piece)
    if len(last_moves) > 10:
        last_moves.pop(0)

    return chosen_move

# =====================
# Hauptloop
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
