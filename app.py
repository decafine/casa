from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room
import random
import string
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = "casa_secret"

socketio = SocketIO(
    app,
    cors_allowed_origins="*"
)

waiting_player = None
rooms = {}


# -----------------------------
# 메인 페이지
# -----------------------------
@app.route("/")
def index():
    return render_template("index.html")


# -----------------------------
# 랜덤 룸 코드 생성
# -----------------------------
def generate_room_code(length=6):

    return ''.join(
        random.choice(string.ascii_uppercase)
        for _ in range(length)
    )

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


# -----------------------------
# 랜덤 매칭
# -----------------------------
@socketio.on("join_random")
def join_random():

    global waiting_player

    sid = request.sid

    # 대기열 없으면 대기
    if waiting_player is None:

        waiting_player = sid

        emit("waiting")

    # 상대 있으면 매칭
    else:

        room = generate_room_code()

        join_room(room, sid=sid)
        join_room(room, sid=waiting_player)

        rooms[room] = {
            "players": [waiting_player, sid]
        }

        socketio.emit(
            "matched",
            {"room": room},
            room=room
        )

        waiting_player = None


@socketio.on("create_room")
def create_room():

    room = generate_room_code()

    rooms[room] = {
        "players":[request.sid]
    }

    join_room(room)

    emit("room_created",{
        "room":room
    })

@socketio.on("join_room_custom")
def join_room_custom(data):

    room = data["room"]

    if room not in rooms:

        emit("error_message",{
            "message":"방 없음"
        })

        return

    if len(rooms[room]["players"]) >= 2:

        emit("error_message",{
            "message":"방 꽉참"
        })

        return

    rooms[room]["players"].append(
        request.sid
    )

    join_room(room)

    socketio.emit(
        "matched",
        {"room":room},
        room=room
    )

# -----------------------------
# 상대에게 이동 전달
# -----------------------------
@socketio.on("make_move")
def make_move(data):

    room = data.get("room")

    emit(
        "opponent_move",
        data,
        room=room,
        include_self=False
    )


# -----------------------------
# 연결 종료
# -----------------------------
@socketio.on("disconnect")
def on_disconnect():

    global waiting_player

    sid = request.sid

    if waiting_player == sid:
        waiting_player = None

    print(f"{sid} disconnected")


# -----------------------------
# 서버 실행
# -----------------------------
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    socketio.run(
        app,
        host="0.0.0.0",
        port=port
    )