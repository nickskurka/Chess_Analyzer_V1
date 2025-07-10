import pygame
import chess
import chess.engine
import os
import time

# Initialize Pygame
pygame.init()

# Constants for display and board setup
WIDTH, HEIGHT = 850, 800
BOARD_SIZE = 800
SQUARE_SIZE = BOARD_SIZE // 8
EVAL_BAR_WIDTH = 50
FPS = 60

# Color definitions for the chess board and UI elements
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_BROWN = (222, 184, 135)
DARK_BROWN = (139, 69, 19)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# Set up the main display window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Chess Analyzer (Stockfish)")

# Mapping of chess piece symbols to their image filenames
piece_mapping = {
    'K': 'King',
    'Q': 'Queen',
    'R': 'Rook',
    'B': 'Bishop',
    'N': 'Knight',
    'P': 'Pawn'
}

# Load chess piece images from files
pieces = {}
for color in ['White', 'Black']:
    for symbol, piece_name in piece_mapping.items():
        filename = f"{piece_name}_{color}.jpg"
        # Updated path: inside assets/pieces/
        filepath = os.path.join(os.path.dirname(__file__), "assets", "pieces", filename)
        if os.path.exists(filepath):
            try:
                image = pygame.image.load(filepath)
                pieces[f"{symbol}_{color}"] = pygame.transform.scale(image, (SQUARE_SIZE, SQUARE_SIZE))
                print(f"Loaded {filename}")
            except pygame.error as e:
                print(f"Error loading {filename}: {e}")
        else:
            print(f"File not found: {filepath}")

print(f"Loaded {len(pieces)} pieces")

# Initialize the chess board using python-chess library
board = chess.Board()

# Initialize Stockfish engine for move analysis
# Updated path: inside engines/
engine_path = os.path.join(os.path.dirname(__file__), "engines", "stockfish-windows-x86-64-avx2.exe")
engine = chess.engine.SimpleEngine.popen_uci(engine_path)

# Game state variables
aggressive_mate = False  # Toggle for aggressive checkmate seeking
white_at_bottom = True  # Board orientation
selected_square = None  # Currently selected square
promotion_pending = None  # Stores pending promotion move
show_promotion_dialog = False  # Flag to show promotion piece selection


# Function to draw the chess board squares
def draw_board():
    """Draw the alternating colored squares of the chess board"""
    for row in range(8):
        for col in range(8):
            # Alternate between light and dark squares
            color = LIGHT_BROWN if (row + col) % 2 == 0 else DARK_BROWN
            pygame.draw.rect(screen, color,
                             (EVAL_BAR_WIDTH + col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))


# Function to draw all chess pieces on the board
def draw_pieces():
    """Draw all chess pieces at their current positions on the board"""
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            # Convert chess square to screen coordinates
            col = chess.square_file(square)
            row = chess.square_rank(square)

            # Flip coordinates if board is rotated
            if not white_at_bottom:
                col = 7 - col
                row = 7 - row

            # Get the appropriate piece image
            piece_symbol = piece.symbol().upper()
            color = 'White' if piece.color else 'Black'
            piece_key = f"{piece_symbol}_{color}"

            if piece_key in pieces:
                screen.blit(pieces[piece_key], (EVAL_BAR_WIDTH + col * SQUARE_SIZE, (7 - row) * SQUARE_SIZE))
            else:
                print(f"Missing piece image: {piece_key}")


# Function to highlight all legal moves for a selected piece
def highlight_moves(square):
    """Highlight all legal moves for the piece on the given square"""
    legal_moves = [move for move in board.legal_moves if move.from_square == square]
    for move in legal_moves:
        col = chess.square_file(move.to_square)
        row = chess.square_rank(move.to_square)

        # Adjust coordinates for board orientation
        if not white_at_bottom:
            col = 7 - col
            row = 7 - row

        # Draw green outline around legal move squares
        pygame.draw.rect(screen, GREEN,
                         (EVAL_BAR_WIDTH + col * SQUARE_SIZE, (7 - row) * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 3)


# Function to get the best move from the engine and highlight it
def get_and_highlight_best_move():
    """Analyze current position and highlight the best move"""
    # Check for forced mate moves if aggressive mate is enabled
    if aggressive_mate:
        result = engine.play(board, chess.engine.Limit(time=.001), info=chess.engine.INFO_ALL)
        if 'score' in result.info and result.info['score'].is_mate():
            mate_move = result.move
        else:
            mate_move = None

        if mate_move:
            highlight_move(mate_move, BLUE)
            return mate_move

    # Get best move from engine
    result = engine.play(board, chess.engine.Limit(time=0.001))
    if result.move:
        highlight_move(result.move, RED)
    return result.move


# Function to draw a line highlighting a specific move
def highlight_move(move, color):
    """Draw a colored line from the move's starting square to its destination"""
    from_col = chess.square_file(move.from_square)
    from_row = chess.square_rank(move.from_square)
    to_col = chess.square_file(move.to_square)
    to_row = chess.square_rank(move.to_square)

    # Adjust coordinates for board orientation
    if not white_at_bottom:
        from_col = 7 - from_col
        from_row = 7 - from_row
        to_col = 7 - to_col
        to_row = 7 - to_row

    # Draw line from center of source square to center of destination square
    pygame.draw.line(screen, color,
                     (EVAL_BAR_WIDTH + from_col * SQUARE_SIZE + SQUARE_SIZE // 2,
                      (7 - from_row) * SQUARE_SIZE + SQUARE_SIZE // 2),
                     (EVAL_BAR_WIDTH + to_col * SQUARE_SIZE + SQUARE_SIZE // 2,
                      (7 - to_row) * SQUARE_SIZE + SQUARE_SIZE // 2),
                     3)


# Function to draw the position evaluation bar
def draw_eval_bar(evaluation):
    """Draw a vertical bar showing the current position evaluation"""
    bar_height = HEIGHT
    # Convert evaluation to bar height (clamped between -10 and +10)
    white_height = int((evaluation + 10) / 20 * bar_height)
    white_height = max(0, min(white_height, bar_height))
    black_height = bar_height - white_height

    # Draw white and black portions of the evaluation bar
    pygame.draw.rect(screen, WHITE, (0, black_height, EVAL_BAR_WIDTH, white_height))
    pygame.draw.rect(screen, BLACK, (0, 0, EVAL_BAR_WIDTH, black_height))

    # Display numerical evaluation in the center
    font = pygame.font.Font(None, 24)
    text = font.render(f"{evaluation:.2f}", True, RED)
    text_rect = text.get_rect(center=(EVAL_BAR_WIDTH // 2, HEIGHT // 2))
    screen.blit(text, text_rect)


# Function to check if a move is a pawn promotion
def is_promotion_move(move):
    """Check if the given move is a pawn promotion"""
    piece = board.piece_at(move.from_square)
    if piece and piece.piece_type == chess.PAWN:
        # Check if pawn is moving to the back rank
        if (piece.color == chess.WHITE and chess.square_rank(move.to_square) == 7) or \
                (piece.color == chess.BLACK and chess.square_rank(move.to_square) == 0):
            return True
    return False


# Function to draw the promotion piece selection dialog
def draw_promotion_dialog():
    """Draw a dialog box for selecting promotion piece"""
    if not show_promotion_dialog or not promotion_pending:
        return

    # Determine which color's pieces to show
    piece = board.piece_at(promotion_pending.from_square)
    if not piece:
        return

    color = 'White' if piece.color else 'Black'

    # Dialog box dimensions
    dialog_width = 4 * SQUARE_SIZE
    dialog_height = SQUARE_SIZE
    dialog_x = (WIDTH - dialog_width) // 2
    dialog_y = (HEIGHT - dialog_height) // 2

    # Draw dialog background
    pygame.draw.rect(screen, YELLOW, (dialog_x, dialog_y, dialog_width, dialog_height))
    pygame.draw.rect(screen, BLACK, (dialog_x, dialog_y, dialog_width, dialog_height), 3)

    # Draw promotion piece options: Queen, Rook, Bishop, Knight
    promotion_pieces = ['Q', 'R', 'B', 'N']
    for i, piece_symbol in enumerate(promotion_pieces):
        piece_key = f"{piece_symbol}_{color}"
        if piece_key in pieces:
            piece_x = dialog_x + i * SQUARE_SIZE
            piece_y = dialog_y
            screen.blit(pieces[piece_key], (piece_x, piece_y))

    # Draw instruction text
    font = pygame.font.Font(None, 36)
    text = font.render("Select promotion piece:", True, BLACK)
    text_rect = text.get_rect(center=(WIDTH // 2, dialog_y - 30))
    screen.blit(text, text_rect)


# Function to handle promotion piece selection
def handle_promotion_click(pos):
    """Handle mouse click on promotion dialog"""
    if not show_promotion_dialog or not promotion_pending:
        return False

    # Calculate dialog position
    dialog_width = 4 * SQUARE_SIZE
    dialog_height = SQUARE_SIZE
    dialog_x = (WIDTH - dialog_width) // 2
    dialog_y = (HEIGHT - dialog_height) // 2

    # Check if click is within dialog bounds
    if dialog_x <= pos[0] <= dialog_x + dialog_width and \
            dialog_y <= pos[1] <= dialog_y + dialog_height:

        # Determine which piece was clicked
        piece_index = (pos[0] - dialog_x) // SQUARE_SIZE
        promotion_pieces = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]

        if 0 <= piece_index < len(promotion_pieces):
            # Create promotion move with selected piece
            promotion_move = chess.Move(
                promotion_pending.from_square,
                promotion_pending.to_square,
                promotion=promotion_pieces[piece_index]
            )

            # Execute the promotion move
            if promotion_move in board.legal_moves:
                board.push(promotion_move)
                print(f"Pawn promoted to {chess.piece_name(promotion_pieces[piece_index])}")

            # Reset promotion state
            reset_promotion_state()
            return True

    return False


# Function to reset promotion dialog state
def reset_promotion_state():
    """Reset all promotion-related state variables"""
    global promotion_pending, show_promotion_dialog, selected_square
    promotion_pending = None
    show_promotion_dialog = False
    selected_square = None


# Main game loop
clock = pygame.time.Clock()
running = True
last_analysis_time = 0
best_move = None
evaluation = 0

print("Chess Game Controls:")
print("- Click to select and move pieces")
print("- Press 'M' to toggle aggressive mate finding")
print("- Press 'P' to flip the board")
print("- Pawn promotion: Click on promotion piece when dialog appears")

while running:
    # Handle all pygame events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Handle promotion dialog clicks first
            if show_promotion_dialog:
                if handle_promotion_click(event.pos):
                    continue

            # Convert mouse position to chess square coordinates
            col = (event.pos[0] - EVAL_BAR_WIDTH) // SQUARE_SIZE
            row = 7 - (event.pos[1] // SQUARE_SIZE)

            # Adjust coordinates for board orientation
            if not white_at_bottom:
                col = 7 - col
                row = 7 - row

            # Ensure click is within board bounds
            if 0 <= col < 8 and 0 <= row < 8:
                square = chess.square(col, row)

                if selected_square is None:
                    # Select a square if none is currently selected
                    selected_square = square
                else:
                    # Try to make a move from selected square to clicked square
                    move = chess.Move(selected_square, square)

                    # Check if this is a pawn promotion move
                    if is_promotion_move(move):
                        # Store the move and show promotion dialog
                        promotion_pending = move
                        show_promotion_dialog = True
                        print("Pawn promotion detected - select piece type")
                    elif move in board.legal_moves:
                        # Execute regular move
                        board.push(move)
                        best_move = None  # Reset best move after a move is made
                        selected_square = None
                    else:
                        # Invalid move, deselect
                        selected_square = None

        elif event.type == pygame.KEYDOWN:
            # Handle keyboard shortcuts
            if event.key == pygame.K_m:
                aggressive_mate = not aggressive_mate
                print(f"Aggressive mate {'enabled' if aggressive_mate else 'disabled'}")
            elif event.key == pygame.K_p:
                white_at_bottom = not white_at_bottom
                print(f"Board flipped. White is now at the {'bottom' if white_at_bottom else 'top'}")
            elif event.key == pygame.K_ESCAPE:
                # Cancel promotion dialog or deselect square
                if show_promotion_dialog:
                    reset_promotion_state()
                else:
                    selected_square = None

    # Clear screen and draw all game elements
    screen.fill(WHITE)
    draw_eval_bar(evaluation)
    draw_board()
    draw_pieces()

    # Highlight legal moves for selected piece
    if selected_square is not None and not show_promotion_dialog:
        highlight_moves(selected_square)

    # Update engine analysis periodically (every 0.1 seconds)
    current_time = time.time()
    if current_time - last_analysis_time > 0.1:
        # Get position evaluation and best move from engine
        info = engine.analyse(board, chess.engine.Limit(time=0.1))
        evaluation = info['score'].white().score(mate_score=10000) / 100
        best_move = get_and_highlight_best_move()
        last_analysis_time = current_time
    elif best_move:
        # Continue highlighting the previously calculated best move
        highlight_move(best_move, BLUE if aggressive_mate else RED)

    # Draw promotion dialog if needed (drawn last so it appears on top)
    if show_promotion_dialog:
        draw_promotion_dialog()

    # Update display and maintain frame rate
    pygame.display.flip()
    clock.tick(FPS)

# Cleanup: quit pygame and close the chess engine
pygame.quit()
engine.quit()
print("Game ended. Thank you for playing!")