# Tic-Tac-Toe AI

## Dependencies

Must have `flask` and `flask-session` installed in order to run the server.

## Running the Application

To start the application, run the following command:

```console
$ flask --app application.py run
```

## Using the Application

Initially, the AI will not be trained, so it will not know how to play Tic-Tac-Toe.

### Training the AI

Visit (http://127.0.0.1:5000/learn)[http://127.0.0.1:5000/learn] to manage the AI's training. You can begin its training by pressing the `Start Learning` button, stop its training with the `Stop Learning` button, and reset the AI's knowledge by pressing the `Reset AI` link. Every 5 minutes the AI will save its knowledge to a CSV file, which will be loaded when the application is restarted.

### Playing Against the AI

To start a new game at any time, go to (http://127.0.0.1:5000/new)[http://127.0.0.1:5000/new], or press the `New Game` button on the homepage. Then, just click any tile on the board, and the AI will play against you.
