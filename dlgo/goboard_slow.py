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
                # if the neighbour is empty add it to the liberties
                liberties.append(neighbour)
            elif neighbour_string.color == player:
                # if the neighbour is ours add it to our pot
                if neighbour_string not in adjacent_same_color:
                    adjacent_same_color.append(neighbour_string)
            else:
                # if the neighbour is not ours add it to the other pot
                if neighbour_string not in adjacent_opposite_color:
                    adjacent_opposite_color.append(neighbour_string)
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

    def remove_string(self, string):
        """
        Removes a string of stones
        """
        for point in string.stones:
            for neighbour in point.neighbours():
                # Removing a string can create liberties for other strings
                neighbour_string = self._grid.get(neighbour)
                if neighbour_string is None:
                    continue
                if neighbour_string is not string:
                    neighbour_string.add_liberty(point)
            self._grid[point] = None
