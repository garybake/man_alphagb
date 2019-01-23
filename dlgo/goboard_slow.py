import copy

from dlgo.gotypes import Player
from dlgo import zobrist


class Move():
    """
    User can play, pass or resign

    Move.play(point)
    Move.pass_turn()
    Move.resign()
    """
    def __init__(self, point=None, is_pass=False, is_resign=False):
        assert (point is not None) ^ is_pass ^ is_resign
        self.point = point
        self.is_play = (self.point is not None)
        self.is_pass = is_pass
        self.is_resign = is_resign

    @classmethod
    def play(cls, point):
        """
        Places a stone on the board
        """
        return Move(point=point)

    @classmethod
    def pass_turn(cls):
        """
        Pass the go
        """
        return Move(is_pass=True)

    @classmethod
    def resign(cls):
        """
        Resign the game
        """
        return Move(is_resign=True)


class GoString():
    """
    Used to track connected groups of stones and their liberties
    A GoString string is the set of connected stones
    A liberty is the number of empty points in its direct neighborhood
    This tracks the liberties of the GoStrings
    """
    def __init__(self, color, stones, liberties):
        self.color = color
        self.stones = frozenset(stones)
        self.liberties = frozenset(liberties)

    # def remove_liberty(self, point):
    #     """
    #     Remove a liberty from the set
    #     """
    #     self.liberties.remove(point)

    def without_liberty(self, point):
        new_liberties = self.liberties - set([point])
        return GoString(self.color, self.stones, new_liberties)

    # def add_liberty(self, point):
    #     """
    #     Add a liberty to the set
    #     """
    #     self.liberties.add(point)

    def with_liberty(self, point):
        """
        Add a liberty to the set
        """
        new_liberties = self.liberties | set(point)
        return GoString(self.color, self.stones, new_liberties)

    def merged_with(self, go_string):
        """
        Merge 2 sets of goStrings together
        """
        assert go_string.color == self.color
        combined_stones = self.stones | go_string.stones
        return GoString(
                self.color,
                combined_stones,
                (self.liberties | go_string.liberties) - combined_stones)

    @property
    def num_liberties(self):
        """
        The number of liberties a GoString has
        """
        return len(self.liberties)

    def __eq__(self, other):
        """
        Test for equality of a GoString with another
        """
        return isinstance(other, GoString) and \
            self.color == other.color and \
            self.stones == other.stones and \
            self.liberties == other.liberties


class Board():
    """
    Holds a game board in a particular state
    """

    def __init__(self, num_rows, num_cols):
        self.num_rows = num_rows
        self.num_cols = num_cols
        self._grid = {}
        self._hash = zobrist.EMPTY_BOARD

    def place_stone(self, player, point):
        assert self.is_on_grid(point)  # point is within bounds
        assert self._grid.get(point) is None  # point is not already played

        adjacent_same_color = []
        adjacent_opposite_color = []
        liberties = []
        for neighbor in point.neighbors():
            # first examine direct neighbors of the point
            if not self.is_on_grid(neighbor):
                continue
            neighbor_string = self._grid.get(neighbor)

            if neighbor_string is None:
                # if the neighbor is empty add it to the liberties
                liberties.append(neighbor)
            elif neighbor_string.color == player:
                # if the neighbor is ours add it to our pot
                if neighbor_string not in adjacent_same_color:
                    adjacent_same_color.append(neighbor_string)
            else:
                # if the neighbor is not ours add it to the other pot
                if neighbor_string not in adjacent_opposite_color:
                    adjacent_opposite_color.append(neighbor_string)
        new_string = GoString(player, [point], liberties)

        # Merge any adjacent strings of the same color
        for same_color_string in adjacent_same_color:
            new_string = new_string.merged_with(same_color_string)
        for new_string_point in new_string.stones:
            self._grid[new_string_point] = new_string

        # Reduce liberties of any adjacent strings of the opposite color
        for other_color_string in adjacent_opposite_color:
            other_color_string.remove_liberty(point)
        # Remove any opposite-color strings that now have zero liberties
        for other_color_string in adjacent_opposite_color:
            if other_color_string.num_liberties == 0:
                self._remove_string(other_color_string)

    def is_on_grid(self, point):
        """
        Returns if the point is within the bounds of the grid
        """
        return 1 <= point.row <= self.num_rows and \
            1 <= point.col <= self.num_cols

    def get(self, point):
        """
        Returns content of point on the board
        Player if stone is on that point
        else None
        """
        string = self._grid.get(point)
        if string is None:
            return None
        return string.color

    def get_go_string(self, point):
        """
        Returns entire string of stones at a point
        GoString if stone is on that point
        else None
        """
        string = self._grid.get(point)
        if string is None:
            return None
        return string

    def _remove_string(self, string):
        """
        Removes a string of stones
        """
        for point in string.stones:
            for neighbor in point.neighbors():
                # Removing a string can create liberties for other strings
                neighbor_string = self._grid.get(neighbor)
                if neighbor_string is None:
                    continue
                if neighbor_string is not string:
                    neighbor_string.add_liberty(point)
            self._grid[point] = None


class GameState():
    """
    Captures the current state of the game
    Know about the board positions, next player, prev state and last move
    """
    def __init__(self, board, next_player, previous, move):
        self.board = board
        self.next_player = next_player
        self.previous_state = previous
        self.last_move = move

    def apply_move(self, move):
        """
        Applies a move to the current game state
        """
        if move.is_play:
            next_board = copy.deepcopy(self.board)
            next_board.place_stone(self.next_player, move.point)
        else:
            next_board = self.board
        return GameState(next_board, self.next_player.other, self, move)

    @classmethod
    def new_game(cls, board_size):
        """
        Creates a new blank GameState
        """
        if isinstance(board_size, int):
            board_size = (board_size, board_size)
        board = Board(*board_size)
        return GameState(board, Player.black, None, None)

    def is_over(self):
        """
        Is the game over
        - Player resigns
        - Both last moves were passes
        """
        if self.last_move is None:
            return False
        if self.last_move.is_resign:
            return True
        second_last_move = self.previous_state.last_move
        if second_last_move is None:
            return False
        return self.last_move.is_pass and second_last_move.is_pass

    def is_move_self_capture(self, player, move):
        """
        Prevents a user making a move that would capture themselves
        """
        if not move.is_play:
            return False
        next_board = copy.deepcopy(self.board)
        next_board.place_stone(player, move.point)
        new_string = next_board.get_go_string(move.point)
        return new_string.num_liberties == 0

    @property
    def situation(self):
        return (self.next_player, self.board)

    def does_move_violate_ko(self, player, move):
        """
        Prevents ko
        - returning the board to the exact previous position
        - A player may not play a stone that would re-create a previous
        game state (situational superko)
        """
        if not move.is_play:
            return False
        next_board = copy.deepcopy(self.board)
        next_board.place_stone(player, move.point)
        next_situation = (player.other, next_board)
        past_state = self.previous_state
        while past_state is not None:
            if past_state.situation == next_situation:
                return True
            past_state = past_state.previous_state
        return False

    def is_valid_move(self, move):
        if self.is_over():
            return False
        if move.is_pass or move.is_resign:
            return True
        return (
            self.board.get(move.point) is None and
            not self.is_move_self_capture(self.next_player, move) and
            not self.does_move_violate_ko(self.next_player, move))
