import heapq
from copy import deepcopy
from heapq import heappush, heappop
from itertools import chain
import time
import argparse
import sys

#====================================================================================

char_goal = '1'
char_single = '2'

class Piece:
    """
    This represents a piece on the Hua Rong Dao puzzle.
    """

    def __init__(self, is_goal, is_single, coord_x, coord_y, orientation):
        """
        :param is_goal: True if the piece is the goal piece and False otherwise.
        :type is_goal: bool
        :param is_single: True if this piece is a 1x1 piece and False otherwise.
        :type is_single: bool
        :param coord_x: The x coordinate of the top left corner of the piece.
        :type coord_x: int
        :param coord_y: The y coordinate of the top left corner of the piece.
        :type coord_y: int
        :param orientation: The orientation of the piece (one of 'h' or 'v') 
            if the piece is a 1x2 piece. Otherwise, this is None
        :type orientation: str
        """

        self.is_goal = is_goal
        self.is_single = is_single
        self.coord_x = coord_x
        self.coord_y = coord_y
        self.orientation = orientation

    def __repr__(self):
        return '{} {} {} {} {}'.format(self.is_goal, self.is_single, \
            self.coord_x, self.coord_y, self.orientation)

class Board:
    """
    Board class for setting up the playing board.
    """

    def __init__(self, pieces):
        """
        :param pieces: The list of Pieces
        :type pieces: List[Piece]
        """

        self.width = 4
        self.height = 5

        self.pieces = pieces

        # self.grid is a 2-d (size * size) array automatically generated
        # using the information on the pieces when a board is being created.
        # A grid contains the symbol for representing the pieces on the board.
        self.grid = []
        self.__construct_grid()


    def __construct_grid(self):
        """
        Called in __init__ to set up a 2-d grid based on the piece location information.

        """

        for i in range(self.height):
            line = []
            for j in range(self.width):
                line.append('.')
            self.grid.append(line)

        for piece in self.pieces:
            if piece.is_goal:
                self.grid[piece.coord_y][piece.coord_x] = char_goal
                self.grid[piece.coord_y][piece.coord_x + 1] = char_goal
                self.grid[piece.coord_y + 1][piece.coord_x] = char_goal
                self.grid[piece.coord_y + 1][piece.coord_x + 1] = char_goal
            elif piece.is_single:
                self.grid[piece.coord_y][piece.coord_x] = char_single
            else:
                if piece.orientation == 'h':
                    self.grid[piece.coord_y][piece.coord_x] = '<'
                    self.grid[piece.coord_y][piece.coord_x + 1] = '>'
                elif piece.orientation == 'v':
                    self.grid[piece.coord_y][piece.coord_x] = '^'
                    self.grid[piece.coord_y + 1][piece.coord_x] = 'v'

    def display(self):
        """
        Print out the current board.

        """
        for i, line in enumerate(self.grid):
            for ch in line:
                print(ch, end='')
            print()
        

class State:
    """
    State class wrapping a Board with some extra current state information.
    Note that State and Board are different. Board has the locations of the pieces. 
    State has a Board and some extra information that is relevant to the search: 
    heuristic function, f value, current depth and parent.
    """

    def __init__(self, board, f, depth, parent=None):
        """
        :param board: The board of the state.
        :type board: Board
        :param f: The f value of current state.
        :type f: int
        :param depth: The depth of current state in the search tree.
        :type depth: int
        :param parent: The parent of current state.
        :type parent: Optional[State]
        """
        self.board = board
        self.f = f
        self.depth = depth
        self.parent = parent
        self.id = hash(board)  # The id for breaking ties.

    def __lt__(self, other):
        if self.f == other.f:
            return self.id < other.id
        return self.f < other.f


def read_from_file(filename):
    """
    Load initial board from a given file.

    :param filename: The name of the given file.
    :type filename: str
    :return: A loaded board
    :rtype: Board
    """

    puzzle_file = open(filename, "r")

    line_index = 0
    pieces = []
    g_found = False

    for line in puzzle_file:

        for x, ch in enumerate(line):

            if ch == '^': # found vertical piece
                pieces.append(Piece(False, False, x, line_index, 'v'))
            elif ch == '<': # found horizontal piece
                pieces.append(Piece(False, False, x, line_index, 'h'))
            elif ch == char_single:
                pieces.append(Piece(False, True, x, line_index, None))
            elif ch == char_goal:
                if g_found == False:
                    pieces.append(Piece(True, False, x, line_index, None))
                    g_found = True
        line_index += 1

    puzzle_file.close()

    board = Board(pieces)
    
    return board


# List of Helper functions
def goal_test(state):
    """
    Helper function to test weather the state is a goal state or not.
    """
    current_board = state.board

    # Check the position of the goal piece, if it is at the designated place, return true
    # Else return false
    for piece in current_board.pieces:
        if piece.is_goal:
            if piece.coord_x == 1 and piece.coord_y == 3:
                return True

    return False


def heuristic_function(state):
    """
    Given a state, return its heuristic value.
    """
    state_board = state.board
    for piece in state_board.pieces:
        if piece.is_goal:
            curr_x = piece.coord_x
            curr_y = piece.coord_y
            return abs(curr_x - 1) + abs(curr_y - 3)


def locate_empty_squares(game_board):
    """
    Locates the 2 empty squares on the board, return them as a tuple.
    """
    square_1 = []
    square_2 = []

    for row in range(len(game_board.grid)):
        for column in range(len(game_board.grid[row])):
            if game_board.grid[row][column] == ".":
                if square_1:
                    square_2.append(column)
                    square_2.append(row)
                else:
                    square_1.append(column)
                    square_1.append(row)

    return square_1, square_2


def move_piece_right(game_board, piece):
    """
    Given the game board and the piece of interest, move it right by 1.
    Return a new game board of the result.
    """
    new_board = deepcopy(game_board)

    # Get the coordinates of the piece
    x_cord = piece.coord_x
    y_cord = piece.coord_y

    # Change the coordinate of the piece in the new board.
    for new_piece in new_board.pieces:
        if new_piece.coord_x == x_cord and new_piece.coord_y == y_cord:
            new_piece.coord_x += 1
            break

    # Change the grid of the new board.
    if piece.is_single:  # The piece is 1x1
        new_board.grid[y_cord][x_cord + 1] = "2"
        new_board.grid[y_cord][x_cord] = "."
    elif piece.orientation == "h":  # The piece is 1x2
        new_board.grid[y_cord][x_cord + 2] = ">"
        new_board.grid[y_cord][x_cord + 1] = "<"
        new_board.grid[y_cord][x_cord] = "."
    elif piece.orientation == "v":  # The piece is 2x1
        new_board.grid[y_cord][x_cord + 1] = "^"
        new_board.grid[y_cord + 1][x_cord + 1] = "v"
        new_board.grid[y_cord][x_cord] = "."
        new_board.grid[y_cord + 1][x_cord] = "."
    elif piece.is_goal:  # The piece is 2x2
        new_board.grid[y_cord][x_cord + 2] = "1"
        new_board.grid[y_cord + 1][x_cord + 2] = "1"
        new_board.grid[y_cord][x_cord] = "."
        new_board.grid[y_cord + 1][x_cord] = "."

    return new_board


def check_left(square, game_board, state):
    """
    Given a board and the empty square, check the left side of it and consider the possible moves.
    """
    x_cord = square[0]
    y_cord = square[1]
    board_grid = game_board.grid
    new_board = None
    new_state = None

    if x_cord > 0:  # If the x-coordinate is 0 then there's no possible moves.
        # Start checking for the squares on the left of the coordinate
        if board_grid[y_cord][x_cord - 1] == "2":  # the piece on the left is a 1x1 piece.
            for piece in game_board.pieces:
                if piece.coord_x == x_cord - 1 and piece.coord_y == y_cord:
                    new_board = move_piece_right(game_board, piece)
                    break
        elif board_grid[y_cord][x_cord - 1] == ">":  # the piece on the left is a 1x2 piece.
            for piece in game_board.pieces:
                if piece.coord_x == x_cord - 2 and piece.coord_y == y_cord:
                    new_board = move_piece_right(game_board, piece)
                    break
        elif board_grid[y_cord][x_cord - 1] == "v":  # the piece on the left is the bottom of a 2x1 piece
            if board_grid[y_cord - 1][x_cord] == ".":  # Indicating that the piece is legal to move.
                for piece in game_board.pieces:
                    if piece.coord_x == x_cord - 1 and piece.coord_y == y_cord - 1:
                        new_board = move_piece_right(game_board, piece)
                        break
        elif board_grid[y_cord][x_cord - 1] == "^":  # the piece on the left is the top of a 2x1 piece
            if board_grid[y_cord + 1][x_cord] == ".":  # Indicating that the piece is legal to move.
                for piece in game_board.pieces:
                    if piece.coord_x == x_cord - 1 and piece.coord_y == y_cord:
                        new_board = move_piece_right(game_board, piece)
                        break
        elif board_grid[y_cord][x_cord - 1] == "1":  # the piece on the left is a 2x2 piece
            if y_cord < len(board_grid) - 1:
                if board_grid[y_cord + 1][x_cord] == "." and board_grid[y_cord + 1][x_cord - 1] == "1":
                    for piece in game_board.pieces:
                        if piece.coord_x == x_cord - 2 and piece.coord_y == y_cord:
                            new_board = move_piece_right(game_board, piece)
                            break
            else:
                if board_grid[y_cord - 1][x_cord] == "." and board_grid[y_cord - 1][x_cord - 1] == "1":
                    for piece in game_board.pieces:
                        if piece.coord_x == x_cord - 2 and piece.coord_y == y_cord - 1:
                            new_board = move_piece_right(game_board, piece)
                            break

        if new_board is not None:
            old_cost = state.f - heuristic_function(state)
            new_state = State(new_board, old_cost + 1, state.depth + 1, state)
            new_state.f += heuristic_function(new_state)
        return new_state


def move_piece_left(game_board, piece):
    """
    Given the game board and the piece of interest, move it left by 1.
    Return a new game board of the result.
    """
    new_board = deepcopy(game_board)

    # Get the coordinates of the piece
    x_cord = piece.coord_x
    y_cord = piece.coord_y

    # Change the coordinate of the piece in the new board.
    for new_piece in new_board.pieces:
        if new_piece.coord_x == x_cord and new_piece.coord_y == y_cord:
            new_piece.coord_x -= 1
            break

    # Change the grid of the new board.
    if piece.is_single:  # The piece is 1x1
        new_board.grid[y_cord][x_cord - 1] = "2"
        new_board.grid[y_cord][x_cord] = "."
    elif piece.orientation == "h":  # The piece is 1x2
        new_board.grid[y_cord][x_cord - 1] = "<"
        new_board.grid[y_cord][x_cord] = ">"
        new_board.grid[y_cord][x_cord + 1] = "."
    elif piece.orientation == "v":  # The piece is 2x1
        new_board.grid[y_cord][x_cord - 1] = "^"
        new_board.grid[y_cord + 1][x_cord - 1] = "v"
        new_board.grid[y_cord][x_cord] = "."
        new_board.grid[y_cord + 1][x_cord] = "."
    elif piece.is_goal:  # The piece is 2x2
        new_board.grid[y_cord][x_cord - 1] = "1"
        new_board.grid[y_cord + 1][x_cord - 1] = "1"
        new_board.grid[y_cord][x_cord + 1] = "."
        new_board.grid[y_cord + 1][x_cord + 1] = "."

    return new_board


def check_right(square, game_board, state):
    """
    Given a board and the empty square, check the right side of it and consider the possible moves.
    """
    x_cord = square[0]
    y_cord = square[1]
    board_grid = game_board.grid
    new_board = None
    new_state = None

    if x_cord < len(board_grid[0]) - 1:  # If the x-coordinate is the max length then there's no possible moves.
        # Start checking for the squares on the right of the coordinate
        if board_grid[y_cord][x_cord + 1] == "2":  # the piece on the right is a 1x1 piece.
            for piece in game_board.pieces:
                if piece.coord_x == x_cord + 1 and piece.coord_y == y_cord:
                    new_board = move_piece_left(game_board, piece)
                    break
        elif board_grid[y_cord][x_cord + 1] == "<":  # the piece on the right is a 1x2 piece.
            for piece in game_board.pieces:
                if piece.coord_x == x_cord + 1 and piece.coord_y == y_cord:
                    new_board = move_piece_left(game_board, piece)
                    break
        elif board_grid[y_cord][x_cord + 1] == "v":  # the piece on the right is the bottom of a 2x1 piece
            if board_grid[y_cord - 1][x_cord] == ".":  # Indicating that the piece is legal to move.
                for piece in game_board.pieces:
                    if piece.coord_x == x_cord + 1 and piece.coord_y == y_cord - 1:
                        new_board = move_piece_left(game_board, piece)
                        break
        elif board_grid[y_cord][x_cord + 1] == "^":  # the piece on the left is the top of a 2x1 piece
            if board_grid[y_cord + 1][x_cord] == ".":  # Indicating that the piece is legal to move.
                for piece in game_board.pieces:
                    if piece.coord_x == x_cord + 1 and piece.coord_y == y_cord:
                        new_board = move_piece_left(game_board, piece)
                        break
        elif board_grid[y_cord][x_cord + 1] == "1":  # the piece on the left is a 2x2 piece
            if y_cord < len(board_grid) - 1:
                if board_grid[y_cord + 1][x_cord] == "." and board_grid[y_cord + 1][x_cord + 1] == "1":
                    for piece in game_board.pieces:
                        if piece.coord_x == x_cord + 1 and piece.coord_y == y_cord:
                            new_board = move_piece_left(game_board, piece)
                            break
            else:
                if board_grid[y_cord - 1][x_cord] == "." and board_grid[y_cord - 1][x_cord + 1] == "1":
                    for piece in game_board.pieces:
                        if piece.coord_x == x_cord + 1 and piece.coord_y == y_cord - 1:
                            new_board = move_piece_left(game_board, piece)
                            break

        if new_board is not None:
            old_cost = state.f - heuristic_function(state)
            new_state = State(new_board, old_cost + 1, state.depth + 1, state)
            new_state.f += heuristic_function(new_state)
        return new_state


def move_piece_down(game_board, piece):
    """
    Given the game board and the piece of interest, move it down by 1.
    Return a new game board of the result.
    """
    new_board = deepcopy(game_board)

    # Get the coordinates of the piece
    x_cord = piece.coord_x
    y_cord = piece.coord_y

    # Change the coordinate of the piece in the new board.
    for new_piece in new_board.pieces:
        if new_piece.coord_x == x_cord and new_piece.coord_y == y_cord:
            new_piece.coord_y += 1
            break

    # Change the grid of the new board.
    if piece.is_single:  # The piece is 1x1
        new_board.grid[y_cord + 1][x_cord] = "2"
        new_board.grid[y_cord][x_cord] = "."
    elif piece.orientation == "v":  # The piece is 2x1
        new_board.grid[y_cord + 2][x_cord] = "v"
        new_board.grid[y_cord + 1][x_cord] = "^"
        new_board.grid[y_cord][x_cord] = "."
    elif piece.orientation == "h":  # The piece is 1x2
        new_board.grid[y_cord + 1][x_cord] = "<"
        new_board.grid[y_cord + 1][x_cord + 1] = ">"
        new_board.grid[y_cord][x_cord] = "."
        new_board.grid[y_cord][x_cord + 1] = "."
    elif piece.is_goal:  # The piece is 2x2
        new_board.grid[y_cord + 2][x_cord] = "1"
        new_board.grid[y_cord + 2][x_cord + 1] = "1"
        new_board.grid[y_cord][x_cord] = "."
        new_board.grid[y_cord][x_cord + 1] = "."

    return new_board


def check_top(square, game_board, state):
    """
    Given a board and the empty square, check the top side of it and consider the possible moves.
    """
    x_cord = square[0]
    y_cord = square[1]
    board_grid = game_board.grid
    new_board = None
    new_state = None

    if y_cord > 0:  # If the y-coordinate is 0 then there's no possible moves.
        # Start checking for the squares on the top of the square
        if board_grid[y_cord - 1][x_cord] == "2":  # the piece on the top is a 1x1 piece.
            for piece in game_board.pieces:
                if piece.coord_x == x_cord and piece.coord_y == y_cord - 1:
                    new_board = move_piece_down(game_board, piece)
                    break
        elif board_grid[y_cord - 1][x_cord] == "v":  # the piece on the top is a 2x1 piece.
            for piece in game_board.pieces:
                if piece.coord_x == x_cord and piece.coord_y == y_cord - 2:
                    new_board = move_piece_down(game_board, piece)
                    break
        elif board_grid[y_cord - 1][x_cord] == "<":  # the piece on the top is the left of the 1x2 piece
            if board_grid[y_cord][x_cord + 1] == ".":  # Indicating that the piece is legal to move.
                for piece in game_board.pieces:
                    if piece.coord_x == x_cord and piece.coord_y == y_cord - 1:
                        new_board = move_piece_down(game_board, piece)
                        break
        elif board_grid[y_cord - 1][x_cord] == ">":  # right of the 1x2 piece
            if board_grid[y_cord][x_cord - 1] == ".":
                for piece in game_board.pieces:
                    if piece.coord_x == x_cord - 1 and piece.coord_y == y_cord - 1:
                        new_board = move_piece_down(game_board, piece)
                        break
        elif board_grid[y_cord - 1][x_cord] == "1":  # the piece is a 2x2 piece.
            if x_cord < len(board_grid[0]) - 1:
                if board_grid[y_cord][x_cord + 1] == "." and board_grid[y_cord - 1][x_cord + 1] == "1":
                    for piece in game_board.pieces:
                        if piece.coord_x == x_cord and piece.coord_y == y_cord - 2:
                            new_board = move_piece_down(game_board, piece)
                            break
            else:
                if board_grid[y_cord][x_cord - 1] == "." and board_grid[y_cord - 1][x_cord - 1] == "1":
                    for piece in game_board.pieces:
                        if piece.coord_x == x_cord - 1 and piece.coord_y == y_cord - 2:
                            new_board = move_piece_down(game_board, piece)
                            break

    if new_board is not None:
        old_cost = state.f - heuristic_function(state)
        new_state = State(new_board, old_cost + 1, state.depth + 1, state)
        new_state.f += heuristic_function(new_state)
    return new_state


def move_piece_up(game_board, piece):
    """
    Given the game board and the piece of interest, move it up by 1.
    Return a new game board of the result.
    """
    new_board = deepcopy(game_board)

    # Get the coordinates of the piece
    x_cord = piece.coord_x
    y_cord = piece.coord_y

    # Change the coordinate of the piece in the new board.
    for new_piece in new_board.pieces:
        if new_piece.coord_x == x_cord and new_piece.coord_y == y_cord:
            new_piece.coord_y -= 1
            break

    # Change the grid of the new board.
    if piece.is_single:  # The piece is 1x1
        new_board.grid[y_cord - 1][x_cord] = "2"
        new_board.grid[y_cord][x_cord] = "."
    elif piece.orientation == "v":  # The piece is 2x1
        new_board.grid[y_cord - 1][x_cord] = "^"
        new_board.grid[y_cord][x_cord] = "v"
        new_board.grid[y_cord + 1][x_cord] = "."
    elif piece.orientation == "h":  # The piece is 1x2
        new_board.grid[y_cord - 1][x_cord] = "<"
        new_board.grid[y_cord - 1][x_cord + 1] = ">"
        new_board.grid[y_cord][x_cord] = "."
        new_board.grid[y_cord][x_cord + 1] = "."
    elif piece.is_goal:  # The piece is 2x2
        new_board.grid[y_cord - 1][x_cord] = "1"
        new_board.grid[y_cord - 1][x_cord + 1] = "1"
        new_board.grid[y_cord + 1][x_cord] = "."
        new_board.grid[y_cord + 1][x_cord + 1] = "."

    return new_board


def check_bottom(square, game_board, state):
    """
    Given a board and the empty square, check the bottom side of it and consider the possible moves.
    """
    x_cord = square[0]
    y_cord = square[1]
    board_grid = game_board.grid
    new_board = None
    new_state = None

    if y_cord < len(board_grid) - 1:  # If the y-coordinate is at the bottom then there's no possible moves.
        # Start checking for the squares on the bottom of the square
        if board_grid[y_cord + 1][x_cord] == "2":  # the piece on the bottom is a 1x1 piece.
            for piece in game_board.pieces:
                if piece.coord_x == x_cord and piece.coord_y == y_cord + 1:
                    new_board = move_piece_up(game_board, piece)
                    break
        elif board_grid[y_cord + 1][x_cord] == "^":  # the piece on the bottom is a 2x1 piece.
            for piece in game_board.pieces:
                if piece.coord_x == x_cord and piece.coord_y == y_cord + 1:
                    new_board = move_piece_up(game_board, piece)
                    break
        elif board_grid[y_cord + 1][x_cord] == "<":  # the piece on the bottom is the left of the 1x2 piece
            if board_grid[y_cord] [x_cord + 1]== ".":  # Indicating that the piece is legal to move.
                for piece in game_board.pieces:
                    if piece.coord_x == x_cord and piece.coord_y == y_cord + 1:
                        new_board = move_piece_up(game_board, piece)
                        break
        elif board_grid[y_cord + 1][x_cord] == ">":  # right of the 1x2 piece
            if board_grid[y_cord][x_cord - 1] == ".":
                for piece in game_board.pieces:
                    if piece.coord_x == x_cord - 1 and piece.coord_y == y_cord + 1:
                        new_board = move_piece_up(game_board, piece)
                        break
        elif board_grid[y_cord + 1][x_cord] == "1":  # the piece is a 2x2 piece.
            if x_cord < len(board_grid[0]) - 1:
                if board_grid[y_cord][x_cord + 1] == "." and board_grid[x_cord + 1][y_cord + 1] == "1":
                    for piece in game_board.pieces:
                        if piece.coord_x == x_cord and piece.coord_y == y_cord + 1:
                            new_board = move_piece_up(game_board, piece)
                            break
            else:
                if board_grid[y_cord][x_cord - 1] == "." and board_grid[x_cord - 1][y_cord + 1] == "1":
                    for piece in game_board.pieces:
                        if piece.coord_x == x_cord - 1 and piece.coord_y == y_cord + 1:
                            new_board = move_piece_up(game_board, piece)
                            break

    if new_board is not None:
        old_cost = state.f - heuristic_function(state)
        new_state = State(new_board, old_cost + 1, state.depth + 1, state)
        new_state.f += heuristic_function(new_state)
    return new_state


def remove_duplicate_boards(result_states):
    """
    Helper that remove duplicate states/boards from the list.
    The list is a cleaned version and has no NULL states or boards.
    """
    grid_explored = []
    filtered_state = []

    for state in result_states:
        if state.board.grid not in grid_explored:
            filtered_state.append(state)
            grid_explored.append(state.board.grid)

    return filtered_state


def generate_successors(state):
    """
    Given a state, return a list of possible successors of this state.
    """
    result_states = []  # List of the resulting successor states
    cleaned_states = []  # List of the cleaned successor states
    state_board = deepcopy(state.board)

    squares = locate_empty_squares(state_board)  # locate the 2 empty squares and return them as a tuple

    for square in squares:
        result_states.append(check_left(square, state_board, state))
        result_states.append(check_right(square, state_board, state))
        result_states.append(check_top(square, state_board, state))
        result_states.append(check_bottom(square, state_board, state))

    for state in result_states:
        if state is not None and state.board is not None:
            cleaned_states.append(state)

    further_cleaned_states = remove_duplicate_boards(cleaned_states)

    return further_cleaned_states


def get_solution(state):
    """
    Given a goal state, backtrack through the parent references until the init state.
    Return a sequence of state from init state to goal state.
    """
    result_sequence = []
    curr_state = state

    while curr_state.parent is not None:
        result_sequence.append(curr_state)
        curr_state = curr_state.parent

    result_sequence.append(curr_state)  # add the init state to the list
    result_sequence.reverse()  # flips the sequence so that it starts from init and ends at goal.

    return result_sequence


def dfs(state):
    """
    Given an initial state, conduct DFS and returns when a solution is found.
    Multi-path pruning will also be implemented.
    """
    # Initialize frontier and nodes explored
    frontier = []
    grids_explored = set()

    # Add the initial state to the frontier, and add the initial_grid to the explored list
    frontier.append(state)

    # While frontier is not empty, look for a solution, else return none.
    while frontier:
        temp_state = frontier.pop()  # Remove the last element of the frontier

        flattened_grid = list(chain.from_iterable(temp_state.board.grid))
        grid_string = ' '.join(flattened_grid)
        if grid_string not in grids_explored:  # Check if the grid is explored
            grids_explored.add(grid_string)

            if goal_test(temp_state):  # Check if the current state is the goal state
                return get_solution(temp_state)
            else:
                successor_states = generate_successors(temp_state)  # Generate it's successor states

                for successor in successor_states:  # Successors can potentially go to an already explored state
                    flattened_successor_grid = list(chain.from_iterable(successor.board.grid))
                    successor_string = ' '.join(flattened_successor_grid)
                    if successor_string not in grids_explored:
                        frontier.append(successor)

    return None  # No solution


def astar(state):
    """
    Given an initial state, conduct A* search and returns when a solution is found.
    Multi-path pruning will also be implemented.
    """
    # Initialize frontier and nodes explored
    frontier = []
    grids_explored = set()

    # Add the initial state to the frontier. More specifically, its f-value
    heapq.heappush(frontier, (state.f, state))

    # While frontier is not empty, look for a solution, else return none.
    while frontier:
        # Get the smallest f-value available
        temp_state = heapq.heappop(frontier)[1]

        # temp_state = None  # Initialize temp_state

        # for state_to_search in frontier:
        #     # Find the corresponding state that has the smallest f-value.
        #     if state_to_search.f + heuristic_function(state_to_search) == smallest_f_value:
        #         temp_state = state_to_search
        #         frontier.remove(temp_state)  # Remove the state from the frontier.
        #         break
        flattened_grid = list(chain.from_iterable(temp_state.board.grid))
        grid_string = ' '.join(flattened_grid)
        if grid_string not in grids_explored:  # Check if the grid is explored
            grids_explored.add(grid_string)

            if goal_test(temp_state):  # Check if the current state is the goal state
                return get_solution(temp_state)
            else:
                successor_states = generate_successors(temp_state)  # Generate it's successor states

                for successor in successor_states:
                    flattened_successor_grid = list(chain.from_iterable(successor.board.grid))
                    successor_string = ' '.join(flattened_successor_grid)
                    if successor_string not in grids_explored:
                        # Add successors to frontier
                        heapq.heappush(frontier, (successor.f, successor))

    return None  # No solution


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--inputfile",
        type=str,
        required=True,
        help="The input file that contains the puzzle."
    )
    parser.add_argument(
        "--outputfile",
        type=str,
        required=True,
        help="The output file that contains the solution."
    )
    parser.add_argument(
        "--algo",
        type=str,
        required=True,
        choices=['astar', 'dfs'],
        help="The searching algorithm."
    )
    args = parser.parse_args()

    args_dict = vars(args)

    # read the board from the file
    init_board = read_from_file(args_dict["inputfile"])
    init_state = State(board=init_board, f=0, depth=0, parent=None)

    # Create and write to the output file
    output_file = open(args_dict["outputfile"], "w")
    if args_dict["algo"] == "dfs":
        result = dfs(init_state)
        if result is not None:
            for state in result:
                for line in state.board.grid:
                    for char in line:
                        output_file.write(char)
                    output_file.write("\n")
                output_file.write("\n")
        else:
            output_file.write("\n")
    elif args_dict["algo"] == "astar":
        result = astar(init_state)
        if result is not None:
            for state in result:
                for line in state.board.grid:
                    for char in line:
                        output_file.write(char)
                    output_file.write("\n")
                output_file.write("\n")
        else:
            output_file.write("\n")

    output_file.close()

    # The following lines are for debugging
    # test_board = read_from_file("testhrd_easy1.txt")
    # test_state = State(test_board, 0, 0, None)
    # test_state.f += heuristic_function(test_state)
    #
    # test_dfs_result = dfs(test_state)
    # if test_dfs_result is not None:
    #     for result in test_dfs_result:
    #         result.board.display()

    # test_astar_result = astar(test_state)
    #
    # if test_astar_result is not None:
    #     for result in test_astar_result:
    #         result.board.display()

    # used for debugging
    something = 1




