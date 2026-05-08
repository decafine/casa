from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room
import random
import string

app = Flask(__name__)

socketio = SocketIO(
    app,
    cors_allowed_origins="*"
)

waiting_player = None

@app.route("/")
def index():
    return render_template("index.html")


# 랜덤 매치
@socketio.on("join_random")
def join_random():

    global waiting_player

    sid = request.sid

    if waiting_player is None:

        waiting_player = sid

        emit("waiting")

    else:

        room = ''.join(
            random.choices(
                string.ascii_uppercase + string.digits,
                k=6
            )
        )

        join_room(room, sid=waiting_player)
        join_room(room, sid=sid)

        socketio.emit(
            "matched",
            {
                "room":room,
                "team":"red"
            },
            to=waiting_player
        )

        socketio.emit(
            "matched",
            {
                "room":room,
                "team":"blue"
            },
            to=sid
        )

        waiting_player = None


# 친선전 생성
@socketio.on("create_room")
def create_room():

    room = ''.join(
        random.choices(
            string.ascii_uppercase + string.digits,
            k=6
        )
    )

    join_room(room)

    emit(
        "room_created",
        {
            "room":room
        }
    )


# 친선전 참가
@socketio.on("join_room_custom")
def join_room_custom(data):

    room = data["room"]

    join_room(room)

    emit(
        "matched",
        {
            "room":room,
            "team":"blue"
        },
        room=room
    )


# 이동 전달
@socketio.on("make_move")
def make_move(data):

    room = data["room"]

    emit(
        "opponent_move",
        {
            "boardData":data["boardData"],
            "currentTurn":data["currentTurn"]
        },
        room=room,
        include_self=False
    )


if __name__ == "__main__":
    socketio.run(app)