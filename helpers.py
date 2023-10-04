import math


# Checks each tic tac toe win condition and for ties
# Returns 0 for no winner, 1 for player 1, 2 for player 2, and 3 for a tie
def check_win(board):
    tie = True

    if board[0][0] == board[0][1] == board[0][2] and board[0][0] != 0:
        return board[0][0]

    elif board[1][0] == board[1][1] == board[1][2] and board[1][0] != 0:
        return board[1][0]

    elif board[2][0] == board[2][1] == board[2][2] and board[2][0] != 0:
        return board[2][0]

    elif board[0][0] == board[1][0] == board[2][0] and board[0][0] != 0:
        return board[0][0]

    elif board[0][1] == board[1][1] == board[2][1] and board[0][1] != 0:
        return board[0][1]

    elif board[0][2] == board[1][2] == board[2][2] and board[0][2] != 0:
        return board[0][2]

    elif board[0][0] == board[1][1] == board[2][2] and board[0][0] != 0:
        return board[0][0]

    elif board[0][2] == board[1][1] == board[2][0] and board[0][2] != 0:
        return board[0][2]

    else:
        for row in board:
            for value in row:
                if value == 0:
                    tie = False
    if tie:
        return 3

    else:
        return 0


# Quantifies the state of the board
def get_state(board):
    state, counter = 0, 0

    # Uses a base of 3 to calculate state
    for i in range(3):
        for j in range(3):
            # Calculate the number, n, that the digit represents
            digit = math.pow(3, counter)

            # X is 1 * n because 1 represents X on the board
            if board[i][j] == 1:
                state += digit

            # O is 2 * n because 2 represents O on the board
            elif board[i][j] == 2:
                state += 2 * digit

            # Since 0 represents no marker on the board, we do not count the squares that have a 0

            # Moves to next digit place
            counter += 1
    return state
