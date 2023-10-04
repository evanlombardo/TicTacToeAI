import os

from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from threading import Thread
import random
import math
import csv
import datetime

from helpers import check_win, get_state


# Defines epsilon, or the percentage of AI moves that are random during training
# Epsilon must have the range: 1 >= epsilon > 0
epsilon = 1


# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Defines the learning rate of the AI
alpha = .02

# Defines the discount factor of the AI, set at 1 to prioritize long term
gamma = 1

# Variable to tell whether the bot is learning
learning = False


# Loads/creates the Q table, which tells the AI what to do
q_table = {}
if os.path.exists("qtable.csv"):
    with open("qtable.csv", "r") as file:
        reader = csv.reader(file)
        for row in reader:

            # Formats data if valid row
            if len(row) == 10:
                for i in range(1, 10):
                    if row[i] == "-inf":
                        row[i] = -math.inf
                    else:
                        row[i] = float(row[i])

                # Sets up format for Q table
                top = [row[1], row[2], row[3]]
                middle = [row[4], row[5], row[6]]
                bottom = [row[7], row[8], row[9]]

                # Inserts into Q table
                q_table[row[0]] = [top, middle, bottom]


@app.route("/", methods=["GET", "POST"])
def index():
    # Creates board and related data
    if "board" not in session:
        session["board"] = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        session["turn"] = 0

    # Player makes action
    if request.method == "POST":
        # If somehow the user presses multiple buttons, this ensures only the first one detected will count
        do_break = False

        # Iterates through the buttons to see if any were submitted
        for i in range(3):
            for j in range(3):
                if request.form.get(f"button[{i}][{j}]") and session["board"][i][j] == 0:
                    session["board"][i][j] = 1
                    session["turn"] += 1
                    do_break = True
                    break
            if do_break:
                break

        # Moves the AI against the player if they moved
        if do_break:
            data = AI_move(session["board"], session["turn"], None, 0)
            session["board"] = data[0]
            session["turn"] = data[1]

        # Checks for a winner
        winner = check_win(session["board"])
        if winner != 0:
            return win(winner)

    # Displays the board after moves
    display = display_board()
    return render_template("index.html", link="new", new="New Game", board=display[0], button=display[1])


@app.route("/learn", methods=["GET", "POST"])
def learn():
    """Allows the learning to be started and stopped and the AI to be reset"""
    global learning

    # Starts and stops learning when respective buttons are pressed
    if request.method == "POST":
        if request.form.get("start") and not learning:
            learning = True
            Thread(target=learner).start()
        elif request.form.get("stop"):
            learning = False

    # Displays the start/stop buttons, disabling the correct one
    start, stop = "", "disabled"
    if learning:
        start, stop = stop, start
    return render_template("learn.html", link="newtable", new="Reset AI", start=start, stop=stop)


@app.route("/new")
def new():
    """Makes new game by clearing session variable and returning to the default route"""
    session.clear()
    return redirect("/")


@app.route("/newtable")
def newtable():
    """Makes new table by clearing the q_table, deleting the file, and returning to the learn route"""

    # Ends any learning
    global learning
    learning = False

    # Empties the Q table when the bot is not learning
    while True:
        if not Thread(target=learner).is_alive():
            q_table.clear()
            break

    # Deletes file save of the Q table
    if os.path.exists("qtable.csv"):
        os.remove("qtable.csv")
    return redirect("/learn")


def learner():
    # Used to stop multiple save calls within the same second
    once = True

    # Creates a new board and related data
    board = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
    turn = 0
    old_move1, old_move2 = [], []

    # Repeats learning until stop button is pressed
    while learning:
        # Moves Player 1 AI
        data = AI_move(board, turn, old_move1, epsilon)
        board = data[0]
        turn = data[1]
        old_move1 = data[2]

        # Moves Player 2 AI (the one we need to learn)
        data = AI_move(board, turn, old_move2, epsilon)
        board = data[0]
        turn = data[1]
        old_move2 = data[2]

        # Checks for a winner after both AI move
        winner = check_win(board)
        if winner != 0:
            board = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
            turn = 0
            old_move1.clear()
            old_move2.clear()

        # Save Q table once every 5 minutes
        now = datetime.datetime.now()
        if now.minute % 5 == 0 and now.second == 0 and once:
            once = False
            save()

        # Allow another save for the next 5 minute period
        elif now.minute % 5 == 0 and now.second == 30:
            once = True


# Moves for the AI
def AI_move(board, turn, old_move, epsilon):
    # Gets state # of the board
    new_move = []
    new_move.append(get_state(board))

    # Creates a spot in the Q table for new states
    if str(new_move[0]) not in q_table:
        q_table[f"{new_move[0]}"] = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]

        # Replaces occupied spots with negative infinity so that the board will not choose it when making decisions
        for i in range(3):
            for j in range(3):
                if board[i][j] != 0:
                    q_table[f"{new_move[0]}"][i][j] = -math.inf

    # Moves for the AI if nobody won or tied
    winner = check_win(board)
    if random.uniform(0, 1) < epsilon and winner == 0:  # Moves randomly if the number is less than epsilon
        # If there is a previous move, updates the Q value for the previous move
        # Formula requires the state of the next move to calculate the Q value for this round, so must calculate the Q value after the other player moves
        if len(old_move) == 3:
            best_action = find_max(new_move[0])  # Move for current state that has the highest Q value, used in updating Q table
            q_table[str(old_move[0])][old_move[1]][old_move[2]] = q_table[str(old_move[0])
                                                                          ][old_move[1]][old_move[2]] + alpha * (gamma * q_table[str(new_move[0])][best_action[0]][best_action[1]
                                                                                                                                                                   ] - q_table[str(old_move[0])][old_move[1]][old_move[2]])

        # Picks a random spot on the board
        row = random.randint(0, 2)
        column = random.randint(0, 2)

        # Makes sure that spot is not occupied
        while board[row][column] != 0:
            row = random.randint(0, 2)
            column = random.randint(0, 2)

        # Move the AI to the valid spot
        if turn % 2 != 0:
            board[row][column] = 2
            new_move.append(row)
            new_move.append(column)
        else:
            board[row][column] = 1
            new_move.append(row)
            new_move.append(column)
        turn += 1

    # Moves based on the best (learned) available move
    elif winner == 0:
        # Gets the coordinates for the space with the highest Q value
        action = find_max(new_move[0])

        # Places X or O depending on the turn
        if turn % 2 != 0:
            board[action[0]][action[1]] = 2
            new_move.append(action[0])
            new_move.append(action[1])
        else:
            board[action[0]][action[1]] = 1
            new_move.append(action[0])
            new_move.append(action[1])
        turn += 1

    # Checks for a winner after the AI moves
    winner = check_win(board)
    if winner != 0 and epsilon != 0:
        # Punishes bot for losing
        if winner == 1:
            reward = -1

        # Rewards bot for winning
        elif winner == 2:
            reward = 1

        # Slightly rewards bot for tying
        else:
            reward = .5

        # Calculates the best action for the current board
        best_action = find_max(new_move[0])

        # Updates Q table with value when the AI loses
        if reward == -1 and len(best_action) == 2:
            q_table[str(old_move[0])][old_move[1]][old_move[2]] = q_table[str(old_move[0])][old_move[1]
                                                                                            ][old_move[2]] + alpha * (reward + gamma * q_table[str(new_move[0])][best_action[0]][best_action[1]] - q_table[str(old_move[0])][old_move[1]][old_move[2]])

        # Updates Q table when the AI is tied against
        elif (reward == .5 and turn % 2 != 0) or reward == -1:
            q_table[str(old_move[0])][old_move[1]][old_move[2]] = q_table[str(old_move[0])][old_move[1]
                                                                                            ][old_move[2]] + alpha * (reward - q_table[str(old_move[0])][old_move[1]][old_move[2]])

        # Updates Q table when AI won or caused a tie
        elif reward == 1 or reward == .5:
            q_table[str(new_move[0])][new_move[1]][new_move[2]] = q_table[str(new_move[0])][new_move[1]
                                                                                            ][new_move[2]] + alpha * (reward - q_table[str(new_move[0])][new_move[1]][new_move[2]])

    # Returns the data from the move that the bot did this turn
    return [board, turn, new_move]


# Disables buttons that are taken up and converts 1 and 2 into X and O respectively
def display_board():
    display_board = [["", "", ""], ["", "", ""], ["", "", ""]]
    button = [["", "", ""], ["", "", ""], ["", "", ""]]

    for i in range(3):
        for j in range(3):
            if session["board"][i][j] == 1:
                display_board[i][j] = "X"
                button[i][j] = "disabled"

            elif session["board"][i][j] == 2:
                display_board[i][j] = "O"
                button[i][j] = "disabled"

    display = [display_board, button]
    return display


# Saves the Q table
def save():
    with open("qtable.csv", "w", newline='') as file:
        writer = csv.writer(file)
        for key in q_table.keys():
            writer.writerow([key, q_table[key][0][0], q_table[key][0][1], q_table[key][0][2], q_table[key][1][0],
                             q_table[key][1][1], q_table[key][1][2], q_table[key][2][0], q_table[key][2][1], q_table[key][2][2]])


# Gets the location of the maximum Q value for that state
def find_max(state):
    max = -math.inf
    location = []
    for i in range(3):
        for j in range(3):
            # Replaces the max with anything that is greater or equal and gets the location if there is a new max
            # To avoid NAN values, must exclude infinity values
            if q_table[f"{state}"][i][j] != -math.inf and float(q_table[f"{state}"][i][j]) >= max:
                max = float(q_table[f"{state}"][i][j])
                location = [i, j]
    return location


# Displays winner/tie on the screen
def win(winner):
    # Clears the users board
    display = display_board()
    session.clear()

    # Displays the winner/tie
    if winner == 3:
        return render_template("message.html", link="new", new="New Game", message=f"Tie!", board=display[0])
    elif winner == 2:
        return render_template("message.html", link="new", new="New Game", message=f"The AI Wins!", board=display[0])
    else:
        return render_template("message.html", link="new", new="New Game", message=f"You Win!", board=display[0])
