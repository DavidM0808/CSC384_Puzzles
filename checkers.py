import argparse
import copy
import sys
import time
import numpy as np
from itertools import chain

cache = {}  # you can use this to implement state caching!
DEPTH_LIMIT = 10  # global variable indicating depth limit


# class board:
#     # This class represents a board, which has a grid representation
#     def __init__(self):
#         self.grid = []
#     pass


class State:
    # This class is used to represent a state.
    # board : a list of lists that represents the 8*8 board
    def __init__(self, board, depth, parent=None):

        self.board = board

        self.width = 8
        self.height = 8
        self.depth = depth
        self.parent = parent

    def display(self):
        for i in self.board:
            for j in i:
                print(j, end="")
            print("")
        print("")


def get_opp_char(player):
    if player in ['b', 'B']:
        return ['r', 'R']
    else:
        return ['b', 'B']


def get_next_turn(curr_turn):
    if curr_turn == 'r':
        return 'b'
    else:
        return 'r'


def read_from_file(filename):

    f = open(filename)
    lines = f.readlines()
    board = [[str(x) for x in l.rstrip()] for l in lines]
    f.close()

    return board


# Boolean helper to check whether if the piece can jump left and up
def piece_left_up_jump_is_possible(board, x_cord, y_cord, piece):
    if y_cord > 0:
        if x_cord > 0:
            if piece == 'B':  # The piece of interest is the black king
                if board[y_cord - 1][x_cord - 1] == 'r' or board[y_cord - 1][x_cord - 1] == 'R':
                    if y_cord - 2 >= 0 and x_cord - 2 >= 0 and board[y_cord - 2][x_cord - 2] == '.':
                        return True
            else:
                if board[y_cord - 1][x_cord - 1] == 'b' or board[y_cord - 1][x_cord - 1] == 'B':
                    if y_cord - 2 >= 0 and x_cord - 2 >= 0 and board[y_cord - 2][x_cord - 2] == '.':
                        return True

    return False


# Boolean helper to check whether if the piece can jump right and up
def piece_right_up_jump_is_possible(board, x_cord, y_cord, piece):
    if y_cord > 0:
        if x_cord < len(board) - 1:
            if piece == 'B':
                if board[y_cord - 1][x_cord + 1] == 'r' or board[y_cord - 1][x_cord + 1] == 'R':
                    if y_cord - 2 >= 0 and x_cord + 2 <= len(board) - 1 and board[y_cord - 2][x_cord + 2] == '.':
                        return True
            else:
                if board[y_cord - 1][x_cord + 1] == 'b' or board[y_cord - 1][x_cord + 1] == 'B':
                    if y_cord - 2 >= 0 and x_cord + 2 <= len(board) - 1 and board[y_cord - 2][x_cord + 2] == '.':
                        return True

    return False


# Helper function to jump the piece left
# Returns a new Board with the piece jumping
def jump_left_up(board, x_cord, y_cord, piece):
    result = copy.deepcopy(board)

    if y_cord - 2 == 0 and piece == 'r':  # The red piece reached the top row
        result[y_cord - 2][x_cord - 2] = 'R'
    else:
        result[y_cord - 2][x_cord - 2] = piece

    result[y_cord - 1][x_cord - 1] = '.'  # The black piece is captured
    result[y_cord][x_cord] = '.'  # The original red piece has moved

    return result


# Helper function to jump the piece right
# Returns a new Board with the piece jumping
def jump_right_up(board, x_cord, y_cord, piece):
    result = copy.deepcopy(board)

    if y_cord - 2 == 0 and piece == 'r':  # The red piece reached the top row
        result[y_cord - 2][x_cord + 2] = 'R'
    else:
        result[y_cord - 2][x_cord + 2] = piece

    result[y_cord - 1][x_cord + 1] = '.'  # The black piece is captured
    result[y_cord][x_cord] = '.'  # The original red piece has moved

    return result


# Helper function to do consecutive jumps
def consecutive_jumps_up(board, x_cord, y_cord, piece):
    new_board = copy.deepcopy(board)

    while piece_left_up_jump_is_possible(new_board, x_cord, y_cord, piece) or \
            piece_right_up_jump_is_possible(new_board, x_cord, y_cord, piece):

        if piece_left_up_jump_is_possible(new_board, x_cord, y_cord, piece):
            new_board = jump_left_up(new_board, x_cord, y_cord, piece)
            x_cord -= 2
            y_cord -= 2

        elif piece_right_up_jump_is_possible(new_board, x_cord, y_cord, piece):
            new_board = jump_right_up(new_board, x_cord, y_cord, piece)
            x_cord += 2
            y_cord -= 2

    return new_board


# Helper function to generate jumps
def generate_red_piece_jumps(game_state, x_cord, y_cord, piece):
    curr_board = copy.deepcopy(game_state.board)
    resulting_states = []
    # Note that red pieces can only jump up
    # Check if the piece can jump left:
    if piece_left_up_jump_is_possible(curr_board, x_cord, y_cord, piece):
        board_left = jump_left_up(curr_board, x_cord, y_cord, piece)
        x_cord -= 2
        y_cord -= 2
        result_left = consecutive_jumps_up(board_left, x_cord, y_cord, piece)  # Conduct consecutive jumps
        resulting_states.append(State(result_left, game_state.depth + 1, game_state))
    if piece_right_up_jump_is_possible(curr_board, x_cord, y_cord, piece):
        board_right = jump_right_up(curr_board, x_cord, y_cord, piece)
        x_cord += 2
        y_cord -= 2
        result_right = consecutive_jumps_up(board_right, x_cord, y_cord, piece)
        resulting_states.append(State(result_right, game_state.depth + 1, game_state))

    return resulting_states


# Helper function to conduct simple move left
def move_piece_left_up(board, x_cord, y_cord, piece):
    new_board = copy.deepcopy(board)
    if y_cord - 1 == 0 and piece == 'r':  # The red piece reached the top row
        new_board[y_cord - 1][x_cord - 1] = 'R'
    else:
        new_board[y_cord - 1][x_cord - 1] = piece
    new_board[y_cord][x_cord] = '.'
    return new_board


# Helper function to conduct simple move right
def move_piece_right_up(board, x_cord, y_cord, piece):
    new_board = copy.deepcopy(board)
    if y_cord - 1 == 0 and piece == 'r':  # The red piece reached the top row
        new_board[y_cord - 1][x_cord + 1] = 'R'
    else:
        new_board[y_cord - 1][x_cord + 1] = piece
    new_board[y_cord][x_cord] = '.'
    return new_board


# Helper function to conduct simple moves on the red pieces
def generate_red_piece_simple_moves(game_state, x_cord, y_cord, piece):
    result_states = []
    curr_board = copy.deepcopy(game_state.board)
    if y_cord > 0:
        if x_cord > 0 and curr_board[y_cord - 1][x_cord - 1] == '.':  # Legal to move left
            result_left = move_piece_left_up(curr_board, x_cord, y_cord, piece)
            result_states.append(State(result_left, game_state.depth + 1, game_state))
        if x_cord < len(curr_board) - 1 and curr_board[y_cord - 1][x_cord + 1] == '.':  # Legal to move right
            result_right = move_piece_right_up(curr_board, x_cord, y_cord, piece)
            result_states.append(State(result_right, game_state.depth + 1, game_state))

    return result_states


# Helper function to move the selected red pieces
# Returns a list of possible states
def move_red_piece(game_state, x_cord, y_cord, piece):
    # First, consider jumps
    jump_states = generate_red_piece_jumps(game_state, x_cord, y_cord, piece)  # Get the jumps if possible
    if jump_states:  # there are jumps that can be made
        return jump_states, 1
    else:
        return generate_red_piece_simple_moves(game_state, x_cord, y_cord, piece), 0


# Boolean helper to check whether if the piece can jump left and down
def piece_left_down_jump_is_possible(board, x_cord, y_cord, piece):
    if y_cord < len(board) - 1:
        if x_cord > 0:
            if piece == 'R':  # The piece is a red king
                if board[y_cord + 1][x_cord - 1] == 'b' or board[y_cord + 1][x_cord - 1] == 'B':
                    if y_cord + 2 <= len(board) - 1 and x_cord - 2 >= 0 and board[y_cord + 2][x_cord - 2] == '.':
                        return True
            else:
                if board[y_cord + 1][x_cord - 1] == 'r' or board[y_cord + 1][x_cord - 1] == 'R':
                    if y_cord + 2 <= len(board) - 1 and x_cord - 2 >= 0 and board[y_cord + 2][x_cord - 2] == '.':
                        return True

    return False


# Boolean helper to check whether if the piece can jump right and down
def piece_right_down_jump_is_possible(board, x_cord, y_cord, piece):
    if y_cord < len(board) - 1:
        if x_cord < len(board) - 1:
            if piece == 'R':
                if board[y_cord + 1][x_cord + 1] == 'b' or board[y_cord + 1][x_cord + 1] == 'B':
                    if y_cord + 2 <= len(board) - 1 and x_cord + 2 <= len(board) - 1 and \
                            board[y_cord + 2][x_cord + 2] == '.':
                        return True
            else:
                if board[y_cord + 1][x_cord + 1] == 'r' or board[y_cord + 1][x_cord + 1] == 'R':
                    if y_cord + 2 <= len(board) - 1 and x_cord + 2 <= len(board) - 1 and \
                            board[y_cord + 2][x_cord + 2] == '.':
                        return True

    return False


# Helper function to jump the piece left and down
# Returns a new Board with the piece jumping
def jump_left_down(board, x_cord, y_cord, piece):
    result = copy.deepcopy(board)

    if y_cord + 2 == len(board) - 1 and piece == 'b':  # The black piece reached the bottom row
        result[y_cord + 2][x_cord - 2] = 'B'
    else:
        result[y_cord + 2][x_cord - 2] = piece

    result[y_cord + 1][x_cord - 1] = '.'  # The red piece is captured
    result[y_cord][x_cord] = '.'  # The original black piece has moved

    return result


# Helper function to jump the piece right and down
# Returns a new Board with the piece jumping
def jump_right_down(board, x_cord, y_cord, piece):
    result = copy.deepcopy(board)

    if y_cord + 2 == len(board) - 1 and piece == 'b':  # The red piece reached the top row
        result[y_cord + 2][x_cord + 2] = 'B'
    else:
        result[y_cord + 2][x_cord + 2] = piece

    result[y_cord + 1][x_cord + 1] = '.'  # The red piece is captured
    result[y_cord][x_cord] = '.'  # The original black piece has moved

    return result


# Helper function to do consecutive jumps down
def consecutive_jumps_down(board, x_cord, y_cord, piece):
    new_board = copy.deepcopy(board)

    while piece_left_down_jump_is_possible(new_board, x_cord, y_cord, piece) or \
            piece_right_down_jump_is_possible(new_board, x_cord, y_cord, piece):

        if piece_left_down_jump_is_possible(new_board, x_cord, y_cord, piece):
            new_board = jump_left_down(new_board, x_cord, y_cord, piece)
            x_cord -= 2
            y_cord += 2

        elif piece_right_down_jump_is_possible(new_board, x_cord, y_cord, piece):
            new_board = jump_right_down(new_board, x_cord, y_cord, piece)
            x_cord += 2
            y_cord += 2

    return new_board


# Helper function to generate jumps
def generate_black_piece_jumps(game_state, x_cord, y_cord, piece):
    curr_board = copy.deepcopy(game_state.board)
    resulting_states = []
    # Note that black pieces can only jump down
    # Check if the piece can jump left:
    if piece_left_down_jump_is_possible(curr_board, x_cord, y_cord, piece):
        board_left = jump_left_down(curr_board, x_cord, y_cord, piece)
        x_cord -= 2
        y_cord += 2
        result_left = consecutive_jumps_down(board_left, x_cord, y_cord, piece)  # Conduct consecutive jumps
        resulting_states.append(State(result_left, game_state.depth + 1, game_state))
    if piece_right_down_jump_is_possible(curr_board, x_cord, y_cord, piece):
        board_right = jump_right_down(curr_board, x_cord, y_cord, piece)
        x_cord += 2
        y_cord += 2
        result_right = consecutive_jumps_down(board_right, x_cord, y_cord, piece)
        resulting_states.append(State(result_right, game_state.depth + 1, game_state))

    return resulting_states


# Helper function to conduct simple move left
def move_piece_left_down(board, x_cord, y_cord, piece):
    new_board = copy.deepcopy(board)
    if y_cord + 1 == len(board) - 1 and piece == 'b':  # The black piece reached the bottom row
        new_board[y_cord + 1][x_cord - 1] = 'B'
    else:
        new_board[y_cord + 1][x_cord - 1] = piece
    new_board[y_cord][x_cord] = '.'
    return new_board


# Helper function to conduct simple move right
def move_piece_right_down(board, x_cord, y_cord, piece):
    new_board = copy.deepcopy(board)
    if y_cord + 1 == len(board) - 1 and piece == 'b':  # The black piece reached the bottom row
        new_board[y_cord + 1][x_cord + 1] = 'B'
    else:
        new_board[y_cord + 1][x_cord + 1] = piece
    new_board[y_cord][x_cord] = '.'
    return new_board


# Helper function to conduct simple moves on the red pieces
def generate_black_piece_simple_moves(game_state, x_cord, y_cord, piece):
    result_states = []
    curr_board = copy.deepcopy(game_state.board)
    if y_cord < len(curr_board) - 1:
        if x_cord > 0 and curr_board[y_cord + 1][x_cord - 1] == '.':  # Legal to move left
            result_left = move_piece_left_down(curr_board, x_cord, y_cord, piece)
            result_states.append(State(result_left, game_state.depth + 1, game_state))
        if x_cord < len(curr_board) - 1 and curr_board[y_cord + 1][x_cord + 1] == '.':  # Legal to move right
            result_right = move_piece_right_down(curr_board, x_cord, y_cord, piece)
            result_states.append(State(result_right, game_state.depth + 1, game_state))

    return result_states


# Helper function to move the selected blue pieces
def move_black_piece(state, x_cord, y_cord, piece):

    # First, consider jumps
    jump_states = generate_black_piece_jumps(state, x_cord, y_cord, piece)  # Get the jumps if possible
    if jump_states:  # there are jumps that can be made
        return jump_states, 1
    else:
        return generate_black_piece_simple_moves(state, x_cord, y_cord, piece), 0


# Helper function to generate consecutive jumps for the king
def consecutive_jumps_king(board, x_cord, y_cord, piece):
    new_board = copy.deepcopy(board)

    while piece_left_down_jump_is_possible(new_board, x_cord, y_cord, piece) or \
            piece_right_down_jump_is_possible(new_board, x_cord, y_cord, piece) or \
            piece_left_up_jump_is_possible(new_board, x_cord, y_cord, piece) or \
            piece_right_up_jump_is_possible(new_board, x_cord, y_cord, piece):

        if piece_left_up_jump_is_possible(new_board, x_cord, y_cord, piece):
            new_board = jump_left_up(new_board, x_cord, y_cord, piece)
            x_cord -= 2
            y_cord -= 2

        elif piece_right_up_jump_is_possible(new_board, x_cord, y_cord, piece):
            new_board = jump_right_up(new_board, x_cord, y_cord, piece)
            x_cord += 2
            y_cord -= 2

        elif piece_left_down_jump_is_possible(new_board, x_cord, y_cord, piece):
            new_board = jump_left_down(new_board, x_cord, y_cord, piece)
            x_cord -= 2
            y_cord += 2

        elif piece_right_down_jump_is_possible(new_board, x_cord, y_cord, piece):
            new_board = jump_right_down(new_board, x_cord, y_cord, piece)
            x_cord += 2
            y_cord += 2

    return new_board


# Helper to generate jumps for the king
def generate_king_jumps(game_state, x_cord, y_cord, player):
    curr_board = copy.deepcopy(game_state.board)
    resulting_states = []
    # Note that the king can go both forward and backward, regardless of the color
    # Check if the piece can jump left:
    if piece_left_up_jump_is_possible(curr_board, x_cord, y_cord, player):  # Can jump left and up
        board_left = jump_left_up(curr_board, x_cord, y_cord, player)
        x_cord -= 2
        y_cord -= 2
        result_left_up = consecutive_jumps_king(board_left, x_cord, y_cord, player)  # Conduct consecutive jumps
        resulting_states.append(State(result_left_up, game_state.depth + 1, game_state))

    if piece_right_up_jump_is_possible(curr_board, x_cord, y_cord, player):  # Can jump right and up
        board_right = jump_right_up(curr_board, x_cord, y_cord, player)
        x_cord += 2
        y_cord -= 2
        result_right_up = consecutive_jumps_king(board_right, x_cord, y_cord, player)
        resulting_states.append(State(result_right_up, game_state.depth + 1, game_state))

    if piece_left_down_jump_is_possible(curr_board, x_cord, y_cord, player):
        board_left = jump_left_down(curr_board, x_cord, y_cord, player)
        x_cord -= 2
        y_cord += 2
        result_left_down = consecutive_jumps_king(board_left, x_cord, y_cord, player)
        resulting_states.append(State(result_left_down, game_state.depth + 1, game_state))

    if piece_right_down_jump_is_possible(curr_board, x_cord, y_cord, player):
        board_right = jump_right_down(curr_board, x_cord, y_cord, player)
        x_cord += 2
        y_cord += 2
        result_right_down = consecutive_jumps_king(board_right, x_cord, y_cord, player)
        resulting_states.append(State(result_right_down, game_state.depth + 1, game_state))

    return resulting_states


# Helper function to move the selected king
def move_king(game_state, x_cord, y_cord, player):

    # First, consider jumps
    jump_states = generate_king_jumps(game_state, x_cord, y_cord, player)
    if jump_states:
        return jump_states, 1
    else:
        simple_list = generate_red_piece_simple_moves(game_state, x_cord, y_cord, player) + \
                      generate_black_piece_simple_moves(game_state, x_cord, y_cord, player)

        return simple_list, 0


# Helper function to generate possible successors for red
def generate_red_moves(game_state):
    jump_successors = []
    simple_successors = []
    for row in range(game_state.height):
        for column in range(game_state.width):
            if game_state.board[row][column] == 'r':
                temp_list, signal = move_red_piece(game_state, column, row, 'r')
                if signal == 1:
                    jump_successors += temp_list
                else:  # simple moves is returned
                    simple_successors += temp_list

            elif game_state.board[row][column] == 'R':
                temp_list, signal = move_king(game_state, column, row, 'R')
                if signal == 1:
                    jump_successors += temp_list
                else:  # simple moves is returned
                    simple_successors += temp_list

    if jump_successors:
        return jump_successors

    return simple_successors


# Helper function to generate possible successors for blue
def generate_black_moves(state):
    jump_successors = []
    simple_successors = []
    for row in range(state.height):
        for column in range(state.width):
            if state.board[row][column] == 'b':
                temp_list, signal = move_black_piece(state, column, row, 'b')
                if signal == 1:
                    jump_successors += temp_list
                else:  # simple moves is returned
                    simple_successors += temp_list

            elif state.board[row][column] == 'B':
                temp_list, signal = move_king(state, column, row, 'B')
                if signal == 1:
                    jump_successors += temp_list
                else:  # simple moves is returned
                    simple_successors += temp_list

    if jump_successors:
        return jump_successors
    return simple_successors


# Helper function to generate possible successors of this state
# This helper takes a state and returns all possible states for the player specified
# Returns a list of states
def generate_successors(game_state, player):
    successors = []
    if player == 'r':  # Current player is red
        successors += generate_red_moves(game_state)

    else:  # Current player is black
        successors += generate_black_moves(game_state)

    return successors


# Helper function to evaluate the Utility of a terminal state
# Given the state and the current player.
# Precondition: The state given is a KNOWN terminal state
def utility_function(game_state, player):
    curr_board = game_state.board

    # Case 1: no more pieces remain for one of the players
    red_pieces = 0
    black_pieces = 0
    for row in range(game_state.height):
        for column in range(game_state.width):
            if curr_board[row][column] == 'r' or curr_board[row][column] == 'R':
                red_pieces += 1
            elif curr_board[row][column] == 'b' or curr_board[row][column] == 'B':
                black_pieces += 1

    if player == 'r' and red_pieces == 0:  # Current player is red, no more piece remains for red
        return -np.inf
    elif player == 'r' and black_pieces == 0:  # Current player is red, no more piece remain for black
        return np.inf

    if player == 'b' and red_pieces == 0:  # Current player is red, no more piece remains for red
        return np.inf
    elif player == 'b' and black_pieces == 0:  # Current player is red, no more piece remain for black
        return -np.inf

    # Case 2: no more legal moves left for the current player
    successors_list = generate_successors(game_state, player)

    if not successors_list:  # No legal moves left for the current player
        return -np.inf

    return 0  # Failsafe return in case if the state passed in isn't a terminal state


# Helper function to estimate the Utility of a non-terminal state
# Given a state and the current player
def evaluation_function(game_state, player):
    red_pieces = 0
    red_kings = 0
    black_pieces = 0
    black_kings = 0

    curr_board = game_state.board

    for row in range(game_state.height):
        for column in range(game_state.width):
            if curr_board[row][column] == 'r':
                red_pieces += 1
            elif curr_board[row][column] == 'R':
                red_kings += 1
            elif curr_board[row][column] == 'b':
                black_pieces += 1
            elif curr_board[row][column] == 'B':
                black_kings += 1

    # Case 1: the current player is red
    if player == 'r':
        return (2 * red_kings + red_pieces) - (2 * black_kings + black_pieces)

    return (2 * black_kings + black_pieces) - (2 * red_kings + red_pieces)


# # Recycled from A1
# def get_solution(game_state):
#     """
#     Given a goal state, backtrack through the parent references until the init state.
#     Return a sequence of state from init state to goal state.
#     """
#     result_sequence = []
#     curr_state = game_state
#
#     while curr_state.parent is not None:
#         result_sequence.append(curr_state)
#         curr_state = curr_state.parent
#
#     result_sequence.append(curr_state)  # add the init state to the list
#     result_sequence.reverse()  # flips the sequence so that it starts from init and ends at goal.
#
#     return result_sequence


# This function computes the utilities for the MAX player
def max_value(game_state, alpha, beta, depth, player):
    temp_value = utility_function(game_state, get_next_turn(player))
    if depth == DEPTH_LIMIT:  # We are at the depth limit
        if temp_value == 0:  # The state is a terminal state
            flattened_board = list(chain.from_iterable(game_state.board))
            board_as_string = ' '.join(flattened_board)
            if board_as_string not in cache.keys():
                cache[board_as_string] = evaluation_function(game_state, player)
            return cache[board_as_string]
        return temp_value
    elif temp_value != 0:  # We are not at the depth limit, but we are at the terminal state
        # terminal_state.append(game_state)
        return temp_value

    value = -np.inf
    next_actions = generate_successors(game_state, player)
    for successor in next_actions:
        successor_flattened_board = list(chain.from_iterable(successor.board))
        successor_board_as_string = ' '.join(successor_flattened_board)
        if successor_board_as_string not in cache.keys():
            value = max(value, min_value(successor, alpha, beta, depth + 1, get_next_turn(player)))
            cache[successor_board_as_string] = value
        else:
            value = cache[successor_board_as_string]
        if value >= beta:
            return value
        alpha = max(alpha, value)
    return value


# This function computes the utilities for the MIN player
def min_value(game_state, alpha, beta, depth, player):
    temp_value = utility_function(game_state, get_next_turn(player))
    if depth == DEPTH_LIMIT:  # We are at the depth limit
        if temp_value == 0:  # The state is a terminal state
            flattened_board = list(chain.from_iterable(game_state.board))
            board_as_string = ' '.join(flattened_board)
            if board_as_string not in cache.keys():
                cache[board_as_string] = evaluation_function(game_state, player)
            return cache[board_as_string]
        return temp_value
    elif temp_value != 0:  # We are not at the depth limit, but have reached a terminal state
        # terminal_state.append(game_state)
        return temp_value

    value = np.inf
    next_actions = generate_successors(game_state, player)
    for successor in next_actions:
        successor_flattened_board = list(chain.from_iterable(successor.board))
        successor_board_as_string = ' '.join(successor_flattened_board)
        if successor_board_as_string not in cache.keys():
            value = min(value, max_value(successor, alpha, beta, depth + 1, get_next_turn(player)))
            cache[successor_board_as_string] = value
        else:
            value = cache[successor_board_as_string]
        if value <= alpha:
            return value
        beta = min(beta, value)
    return value


# This function does Alpha-Beta Pruning
def alpha_beta_search(game_state, player):
    best_value = max_value(game_state, -np.inf, np.inf, 0, player)

    next_action = generate_successors(game_state, player)
    for move in next_action:
        next_flattened_board = list(chain.from_iterable(move.board))
        action_board_as_string = ' '.join(next_flattened_board)
        if action_board_as_string in cache.keys() and cache[action_board_as_string] == best_value:
            return move, cache[action_board_as_string]
    return game_state, 999


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--inputfile",
        type=str,
        required=True,
        help="The input file that contains the puzzles."
    )
    parser.add_argument(
        "--outputfile",
        type=str,
        required=True,
        help="The output file that contains the solution."
    )
    args = parser.parse_args()

    # initial_board = read_from_file("checkers2.txt")
    initial_board = read_from_file(args.inputfile)
    initial_state = State(initial_board, 0, None)
    turn = 'r'
    ctr = 0

    # Attempting to simulate a checker games
    move_list = [initial_state]

    next_state, state_value = alpha_beta_search(initial_state, turn)
    while state_value != 999:
        move_list.append(next_state)
        # if ctr == DEPTH_LIMIT - 1:
        #     break
        new_state = next_state
        turn = get_next_turn(turn)
        next_state, state_value = alpha_beta_search(new_state, turn)
        ctr += 1

    for state_action in move_list:
        state_action.display()

    output_file = open(args.outputfile, "w")
    if move_list:
        for action in move_list:
            for line in action.board:
                for char in line:
                    output_file.write(char)
                output_file.write("\n")
            output_file.write("\n")

    output_file.close()

    # sys.stdout = open(args.outputfile, 'w')
    #
    # sys.stdout = sys.__stdout__

    # something = 1  # Used for debugging

