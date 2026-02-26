import random
import copy
from typing import List, Tuple, Optional, Dict

class ChessPiece:
    """Класс для представления шахматной фигуры"""
    
    PIECE_VALUES = {
        'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000,
        'p': -100, 'n': -320, 'b': -330, 'r': -500, 'q': -900, 'k': -20000
    }
    
    def __init__(self, piece_type: str, position: Tuple[int, int]):
        self.type = piece_type
        self.position = position
        self.has_moved = False
    
    def get_color(self) -> str:
        return 'white' if self.type.isupper() else 'black'
    
    def get_value(self) -> int:
        return self.PIECE_VALUES.get(self.type, 0)


class ChessBoard:
    """Класс для представления шахматной доски"""
    
    def __init__(self, fen: str = None):
        if fen:
            self.load_fen(fen)
        else:
            self.setup_initial_position()
    
    def setup_initial_position(self):
        """Устанавливает начальную позицию"""
        self.board = [
            ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'],
            ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],
            [None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None],
            ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],
            ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
        ]
        self.current_turn = 'white'
        self.castling_rights = {'K': True, 'Q': True, 'k': True, 'q': True}
        self.en_passant_target = None
        self.halfmove_clock = 0
        self.fullmove_number = 1
    
    def load_fen(self, fen: str):
        """Загружает позицию из FEN нотации"""
        parts = fen.split()
        board_part = parts[0]
        
        # Расстановка фигур
        self.board = []
        for rank in board_part.split('/'):
            row = []
            for char in rank:
                if char.isdigit():
                    row.extend([None] * int(char))
                else:
                    row.append(char)
            self.board.append(row)
        
        # Остальные параметры FEN
        if len(parts) > 1:
            self.current_turn = 'white' if parts[1] == 'w' else 'black'
        if len(parts) > 2:
            self.castling_rights = {
                'K': 'K' in parts[2], 'Q': 'Q' in parts[2],
                'k': 'k' in parts[2], 'q': 'q' in parts[2]
            }
        if len(parts) > 3 and parts[3] != '-':
            self.en_passant_target = parts[3]
        if len(parts) > 4:
            self.halfmove_clock = int(parts[4])
        if len(parts) > 5:
            self.fullmove_number = int(parts[5])
    
    def to_fen(self) -> str:
        """Преобразует доску в FEN нотацию"""
        fen_parts = []
        
        # Доска
        for row in self.board:
            empty_count = 0
            row_str = ''
            for piece in row:
                if piece is None:
                    empty_count += 1
                else:
                    if empty_count > 0:
                        row_str += str(empty_count)
                        empty_count = 0
                    row_str += piece
            if empty_count > 0:
                row_str += str(empty_count)
            fen_parts.append(row_str)
        
        board_fen = '/'.join(fen_parts)
        
        # Ход
        turn_char = 'w' if self.current_turn == 'white' else 'b'
        
        # Рокировка
        castling_str = ''
        if self.castling_rights['K']: castling_str += 'K'
        if self.castling_rights['Q']: castling_str += 'Q'
        if self.castling_rights['k']: castling_str += 'k'
        if self.castling_rights['q']: castling_str += 'q'
        if not castling_str: castling_str = '-'
        
        # Взятие на проходе
        en_passant_str = self.en_passant_target or '-'
        
        return f"{board_fen} {turn_char} {castling_str} {en_passant_str} {self.halfmove_clock} {self.fullmove_number}"
    
    def get_piece(self, row: int, col: int) -> Optional[str]:
        """Получает фигуру по позиции"""
        if 0 <= row < 8 and 0 <= col < 8:
            return self.board[row][col]
        return None
    
    def is_valid_position(self, row: int, col: int) -> bool:
        """Проверяет корректность позиции"""
        return 0 <= row < 8 and 0 <= col < 8
    
    def get_piece_color(self, piece: str) -> str:
        """Получает цвет фигуры"""
        if piece is None:
            return None
        return 'white' if piece.isupper() else 'black'
    
    def get_pseudo_legal_moves(self, row: int, col: int) -> List[Tuple[int, int]]:
        """Получает все возможные ходы фигуры (без учета шахов)"""
        piece = self.get_piece(row, col)
        if piece is None:
            return []
        
        moves = []
        piece_type = piece.lower()
        piece_color = self.get_piece_color(piece)
        
        if piece_type == 'p':  # Пешка
            direction = -1 if piece_color == 'white' else 1
            start_row = 6 if piece_color == 'white' else 1
            
            # Ход вперед
            if self.is_valid_position(row + direction, col):
                if self.get_piece(row + direction, col) is None:
                    moves.append((row + direction, col))
                    
                    # Ход на 2 клетки с начальной позиции
                    if row == start_row and self.get_piece(row + 2 * direction, col) is None:
                        moves.append((row + 2 * direction, col))
            
            # Взятия
            for dc in [-1, 1]:
                new_row, new_col = row + direction, col + dc
                if self.is_valid_position(new_row, new_col):
                    target = self.get_piece(new_row, new_col)
                    if target and self.get_piece_color(target) != piece_color:
                        moves.append((new_row, new_col))
        
        elif piece_type == 'n':  # Конь
            knight_moves = [
                (-2, -1), (-2, 1), (-1, -2), (-1, 2),
                (1, -2), (1, 2), (2, -1), (2, 1)
            ]
            for dr, dc in knight_moves:
                new_row, new_col = row + dr, col + dc
                if self.is_valid_position(new_row, new_col):
                    target = self.get_piece(new_row, new_col)
                    if target is None or self.get_piece_color(target) != piece_color:
                        moves.append((new_row, new_col))
        
        elif piece_type == 'b':  # Слон
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            for dr, dc in directions:
                for i in range(1, 8):
                    new_row, new_col = row + dr * i, col + dc * i
                    if not self.is_valid_position(new_row, new_col):
                        break
                    target = self.get_piece(new_row, new_col)
                    if target is None:
                        moves.append((new_row, new_col))
                    else:
                        if self.get_piece_color(target) != piece_color:
                            moves.append((new_row, new_col))
                        break
        
        elif piece_type == 'r':  # Ладья
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            for dr, dc in directions:
                for i in range(1, 8):
                    new_row, new_col = row + dr * i, col + dc * i
                    if not self.is_valid_position(new_row, new_col):
                        break
                    target = self.get_piece(new_row, new_col)
                    if target is None:
                        moves.append((new_row, new_col))
                    else:
                        if self.get_piece_color(target) != piece_color:
                            moves.append((new_row, new_col))
                        break
        
        elif piece_type == 'q':  # Ферзь
            directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
            for dr, dc in directions:
                for i in range(1, 8):
                    new_row, new_col = row + dr * i, col + dc * i
                    if not self.is_valid_position(new_row, new_col):
                        break
                    target = self.get_piece(new_row, new_col)
                    if target is None:
                        moves.append((new_row, new_col))
                    else:
                        if self.get_piece_color(target) != piece_color:
                            moves.append((new_row, new_col))
                        break
        
        elif piece_type == 'k':  # Король
            directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
            for dr, dc in directions:
                new_row, new_col = row + dr, col + dc
                if self.is_valid_position(new_row, new_col):
                    target = self.get_piece(new_row, new_col)
                    if target is None or self.get_piece_color(target) != piece_color:
                        moves.append((new_row, new_col))
        
        return moves
    
    def make_move(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> bool:
        """Выполняет ход"""
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        piece = self.get_piece(from_row, from_col)
        if piece is None:
            return False
        
        # Сбрасываем en_passant_target
        self.en_passant_target = None
        
        # Проверяем ход пешки на 2 клетки для en passant
        if piece.lower() == 'p':
            if abs(to_row - from_row) == 2:
                # Пешка идет на 2 клетки
                en_passant_col = (from_col + to_col) // 2
                en_passant_row = (from_row + to_row) // 2
                self.en_passant_target = f"{chr(ord('a') + en_passant_col)}{8 - en_passant_row}"
        
        # Выполняем ход
        self.board[to_row][to_col] = piece
        self.board[from_row][from_col] = None
        
        # Смена хода
        self.current_turn = 'black' if self.current_turn == 'white' else 'white'
        if self.current_turn == 'white':
            self.fullmove_number += 1
        
        return True
    
    def evaluate_position(self) -> int:
        """Оценивает позицию (простая материальная оценка)"""
        score = 0
        for row in self.board:
            for piece in row:
                if piece:
                    score += ChessPiece.PIECE_VALUES.get(piece, 0)
        return score
    
    def is_in_check(self, color: str) -> bool:
        """Проверяет, находится ли король под шахом"""
        # Находим короля
        king_pos = None
        king_piece = 'K' if color == 'white' else 'k'
        
        for row in range(8):
            for col in range(8):
                if self.board[row][col] == king_piece:
                    king_pos = (row, col)
                    break
            if king_pos:
                break
        
        if not king_pos:
            return False
        
        # Проверяем атаки на короля
        opponent_color = 'black' if color == 'white' else 'white'
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece and self.get_piece_color(piece) == opponent_color:
                    moves = self.get_pseudo_legal_moves(row, col)
                    if king_pos in moves:
                        return True
        
        return False


class ChessBot:
    """Базовый класс для шахматного бота"""
    
    def __init__(self, difficulty: str):
        self.difficulty = difficulty
        self.color = 'black'
    
    def get_move(self, board: ChessBoard) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """Получает лучший ход"""
        raise NotImplementedError


class EasyBot(ChessBot):
    """Легкий бот - случайные ходы"""
    
    def get_move(self, board: ChessBoard) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        all_moves = []
        
        for row in range(8):
            for col in range(8):
                piece = board.get_piece(row, col)
                if piece and board.get_piece_color(piece) == self.color:
                    moves = board.get_pseudo_legal_moves(row, col)
                    for move in moves:
                        all_moves.append(((row, col), move))
        
        if all_moves:
            return random.choice(all_moves)
        return None


class MediumBot(ChessBot):
    """Нормальный бот - базовая оценка"""
    
    def get_move(self, board: ChessBoard) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        best_move = None
        best_score = float('-inf')
        
        for row in range(8):
            for col in range(8):
                piece = board.get_piece(row, col)
                if piece and board.get_piece_color(piece) == self.color:
                    moves = board.get_pseudo_legal_moves(row, col)
                    for move in moves:
                        # Симулируем ход
                        test_board = copy.deepcopy(board)
                        test_board.make_move((row, col), move)
                        
                        # Оцениваем позицию
                        score = test_board.evaluate_position()
                        
                        # Бонус за взятие фигур
                        captured_piece = board.get_piece(move[0], move[1])
                        if captured_piece:
                            score += ChessPiece.PIECE_VALUES.get(captured_piece, 0) // 2
                        
                        if score > best_score:
                            best_score = score
                            best_move = ((row, col), move)
        
        return best_move


class HardBot(ChessBot):
    """Сложный бот - минимакс с глубиной 3"""
    
    def __init__(self, difficulty: str):
        super().__init__(difficulty)
        self.max_depth = 3
    
    def get_move(self, board: ChessBoard) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        best_move = None
        best_score = float('-inf')
        
        all_moves = []
        for row in range(8):
            for col in range(8):
                piece = board.get_piece(row, col)
                if piece and board.get_piece_color(piece) == self.color:
                    moves = board.get_pseudo_legal_moves(row, col)
                    for move in moves:
                        all_moves.append(((row, col), move))
        
        # Ограничиваем количество ходов для анализа
        random.shuffle(all_moves)
        moves_to_analyze = all_moves[:15]  # Анализируем только 15 случайных ходов
        
        for move in moves_to_analyze:
            test_board = copy.deepcopy(board)
            test_board.make_move(move[0], move[1])
            
            score = self.minimax(test_board, self.max_depth - 1, float('-inf'), float('inf'), False)
            
            if score > best_score:
                best_score = score
                best_move = move
        
        return best_move
    
    def minimax(self, board: ChessBoard, depth: int, alpha: float, beta: float, is_maximizing: bool) -> int:
        """Минимакс алгоритм с альфа-бета отсечением"""
        if depth == 0:
            return board.evaluate_position()
        
        if is_maximizing:
            max_eval = float('-inf')
            for row in range(8):
                for col in range(8):
                    piece = board.get_piece(row, col)
                    if piece and board.get_piece_color(piece) == self.color:
                        moves = board.get_pseudo_legal_moves(row, col)
                        for move in moves:
                            test_board = copy.deepcopy(board)
                            test_board.make_move((row, col), move)
                            
                            eval_score = self.minimax(test_board, depth - 1, alpha, beta, False)
                            max_eval = max(max_eval, eval_score)
                            alpha = max(alpha, eval_score)
                            
                            if beta <= alpha:
                                break
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            opponent_color = 'white' if self.color == 'black' else 'black'
            for row in range(8):
                for col in range(8):
                    piece = board.get_piece(row, col)
                    if piece and board.get_piece_color(piece) == opponent_color:
                        moves = board.get_pseudo_legal_moves(row, col)
                        for move in moves:
                            test_board = copy.deepcopy(board)
                            test_board.make_move((row, col), move)
                            
                            eval_score = self.minimax(test_board, depth - 1, alpha, beta, True)
                            min_eval = min(min_eval, eval_score)
                            beta = min(beta, eval_score)
                            
                            if beta <= alpha:
                                break
                if beta <= alpha:
                    break
            return min_eval


def create_bot(difficulty: str) -> ChessBot:
    """Создает бота в зависимости от сложности"""
    if difficulty == 'easy':
        return EasyBot(difficulty)
    elif difficulty == 'medium':
        return MediumBot(difficulty)
    elif difficulty == 'hard':
        return HardBot(difficulty)
    else:
        return EasyBot('easy')
