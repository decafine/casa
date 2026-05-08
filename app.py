from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room
import random
import string

app = Flask(__name__)
app.config["SECRET_KEY"] = "casa_secret"

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
)

waiting_player = None
rooms = {}

@app.route("/")
def index():
    return render_template("index.html")


def generate_room_code(length=6):
    return ''.join(
        random.choice(string.ascii_uppercase)
        for _ in range(length)
    )


@socketio.on("join_random")
def join_random():

    global waiting_player

    sid = request.sid

    if waiting_player is None:

        waiting_player = sid

        emit("waiting")

    else:

        room = generate_room_code()

        join_room(room, sid=sid)
        join_room(room, sid=waiting_player)

        rooms[room] = {
            "players":[waiting_player, sid]
        }

        socketio.emit(
            "matched",
            {
                "room":room,
                "team":"red"
            },
            room=waiting_player
        )

        socketio.emit(
            "matched",
            {
                "room":room,
                "team":"blue"
            },
            room=sid
        )

        waiting_player = None


@socketio.on("make_move")
def make_move(data):

    room = data.get("room")

    emit(
        "opponent_move",
        data,
        room=room,
        include_self=False
    )


@socketio.on("disconnect")
def on_disconnect():

    global waiting_player

    sid = request.sid

    if waiting_player == sid:
        waiting_player = None

    print(f"{sid} disconnected")


if __name__ == "__main__":
    socketio.run(app)