from dlgo.gotypes import Point


def is_point_an_eye(board, point, color):
    """
    An eye is an empty point surrounded by pieces
    - an empty point where all adjacent points and at least 3 out of 4
      diagonally adjacent points are filled with friendly stones
    """
    if board.get(point) is not None:
        # Needs to be an empty point
        return False

    # All adjacent points must contain friendly stones
    for neighbor in point.neighbors():
        if board.is_on_grid(neighbor):
            neighbor_color = board.get(neighbor)
            if neighbor_color != color:
                return False

    # We must control 3 out of the 4 corners if the point is in the middle
    # of the board; on the edge you must control all corners
    friendly_corners = 0
    off_board_corners = 0
    corners = [
        Point(point.row - 1, point.col - 1),
        Point(point.row - 1, point.col + 1),
        Point(point.row + 1, point.col - 1),
        Point(point.row + 1, point.col + 1)
    ]

    for corner in corners:
        if board.is_on_grid(corner):
            corner_color = board.get(corner)
            if corner_color == color:
                friendly_corners += 1
        else:
            off_board_corners += 1

    if off_board_corners > 0:
        # Point is on the edge or corner
        return off_board_corners + friendly_corners == 4
    # Point is in the middle
    return friendly_corners >= 3
