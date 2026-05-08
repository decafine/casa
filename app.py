from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room

import random
import string

app = Flask(__name__)

socketio = SocketIO(
    app,
    cors_allowed_origins="*"
)

waiting_player = None

# room 정보 저장
rooms_data = {}

@app.route("/")
def index():
    return render_template("index.html")


# =========================
# 랜덤 매치
# =========================
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

        join_room(room, waiting_player)
        join_room(room, sid)

        rooms_data[room] = {
            "red": waiting_player,
            "blue": sid
        }

        socketio.emit(
            "matched",
            {
                "room": room,
                "team": "red"
            },
            to=waiting_player
        )

        socketio.emit(
            "matched",
            {
                "room": room,
                "team": "blue"
            },
            to=sid
        )

        waiting_player = None


# =========================
# 친선전 생성
# =========================
@socketio.on("create_room")
def create_room():

    sid = request.sid

    room = ''.join(
        random.choices(
            string.ascii_uppercase + string.digits,
            k=6
        )
    )

    join_room(room)

    rooms_data[room] = {
        "red": sid,
        "blue": None
    }

    emit(
        "room_created",
        {
            "room": room,
            "team": "red"
        }
    )


# =========================
# 친선전 참가
# =========================
@socketio.on("join_room_custom")
def join_room_custom(data):

    sid = request.sid

    room = data["room"]

    if room not in rooms_data:

        emit("join_failed")

        return

    if rooms_data[room]["blue"] is not None:

        emit("join_failed")

        return

    join_room(room)

    rooms_data[room]["blue"] = sid

    # 참가자
    socketio.emit(
        "matched",
        {
            "room": room,
            "team": "blue"
        },
        to=sid
    )

    # 방장
    socketio.emit(
        "matched",
        {
            "room": room,
            "team": "red"
        },
        to=rooms_data[room]["red"]
    )


# =========================
# 이동 전달
# =========================
@socketio.on("make_move")
def make_move(data):

    sid = request.sid

    room = data["room"]

    if room not in rooms_data:
        return

    room_info = rooms_data[room]

    current_turn = data["currentTurn"]

    # 턴 검증
    if current_turn == "blue":

        if sid != room_info["red"]:
            return

    else:

        if sid != room_info["blue"]:
            return

    emit(
        "opponent_move",
        {
            "boardData": data["boardData"],
            "currentTurn": data["currentTurn"]
        },
        room=room,
        include_self=False
    )


# =========================
# 연결 종료
# =========================
@socketio.on("disconnect")
def disconnect():

    global waiting_player

    sid = request.sid

    if waiting_player == sid:
        waiting_player = None

    remove_rooms = []

    for room, info in rooms_data.items():

        if (
            info["red"] == sid or
            info["blue"] == sid
        ):

            socketio.emit(
                "enemy_left",
                room=room
            )

            remove_rooms.append(room)

    for room in remove_rooms:
        del rooms_data[room]


if __name__ == "__main__":
    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=True
    )