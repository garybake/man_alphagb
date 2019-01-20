import copy
from dlgo.gotypes import Player


class Move():
    """
    User can play, pass or resign

    Move.play(point)
    Move.pass_turn()
    Move.resign()
    """
    def __init__(self, point=None, is_pass=False, is_resign=False):
        assert (point is None) ^ is_pass ^ is_resign
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
    A liberty is the number of empty points in its direct neighbourhood
    This tracks the liberties of the GoStrings
    """
    def __init__(self, color, stones, liberties):
        self.color = color
        self.stones = set(stones)
        self.liberties = liberties

    def remove_liberty(self, point):
        """
        Remove a liberty from the set
        """
        self.liberties.remove(point)

    def add_liberty(self, point):
        """
        Add a liberty to the set
        """
        self.liberties.add(point)

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
    def __init__(self, num_rows, num_cols):
        self.num_rows = num_rows
        self.num_cols = num_cols
        self._grid = ()

    def place_stone(self, player, point):
        assert self.is_on_grid(point)  # point is within bounds
        assert self._grid.get(point) is None  # point is not already played

        adjacent_same_color = []
        adjacent_opposite_color = []
        liberties = []
        for neighbour in point.neighbours():
            # firs examine direct neighbours of the point
            if not self.is_on_grid(neighbour):
                continue
            neighbour_string = self._grid.get(neighbour)
            if neighbour_string is None:
                liberties.append(neighbour)
            elif neighbour_string.color == player:
                if neighbour_string not in adjacent_same_color:
                    adjacent_same_color.append(neighbour_string)
            else:
                if neighbour_string not in adjacent_opposite_color:
                    adjacent_opposite_color.append(neighbour_string)
        new_string = GoString(player, [point], liberties)

