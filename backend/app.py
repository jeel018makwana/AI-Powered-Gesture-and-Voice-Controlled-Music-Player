from flask import Flask, request, jsonify, redirect, send_from_directory
from flask_cors import CORS
from backend.models import db, User, Song
from backend.player import MusicPlayer 
from backend.spotify_control import SpotifyController
import os , sys
import threading
from backend.gesture_control import detect_from_image
from backend.voice_control import start_voice, stop_voice
import pygame

# ---------------- DATABASE ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")
FRONTEND_BUILD = os.path.join(BASE_DIR, "..", "frontend", "build")

app = Flask(__name__,static_folder=os.path.join(FRONTEND_BUILD, "static"),
    template_folder=FRONTEND_BUILD)
CORS(app)

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

# ---------------- MUSIC FOLDER ----------------
MUSIC_FOLDER = os.path.join(BASE_DIR, "music")
os.makedirs(MUSIC_FOLDER, exist_ok=True)

# Load local songs
local_songs = [
    os.path.join(MUSIC_FOLDER, f)
    for f in os.listdir(MUSIC_FOLDER)
    if f.endswith(".mp3")
]

# ---------------- SPOTIFY ----------------
spotify_ctrl = SpotifyController(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
    redirect_uri="YOUR_REDIRECT_URI"
)

# ---------------- PLAYER ----------------
player = MusicPlayer(
    local_songs=local_songs,
    spotify_controller=spotify_ctrl
)

player_state = {
    "mode": "local",        # local / spotify
    "status": "stopped",    # playing / paused
    "song": "",
    "volume": 50,
    "liked": None,
    "voice": False,
    "gesture": False
}

gesture_thread = None
voice_thread = None

gesture_running = False
voice_running = False

# ---------------- BASIC ROUTE ----------------
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.template_folder, "index.html")

# Route to serve individual songs
@app.route("/songs/<path:filename>")
def serve_song(filename):
    return send_from_directory(MUSIC_FOLDER, filename)

# ---------------- SONG LIST ----------------
@app.route("/api/songs", methods=["GET"])
def get_local_songs():
    files = os.listdir(MUSIC_FOLDER)
    songs = [f for f in files if f.endswith(".mp3") or f.endswith(".wav")]
    return jsonify({"songs": songs})

# ---------------- AUTH ----------------
@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if User.query.filter((User.email == email) | (User.username == username)).first():
        return jsonify({"error": "User already exists"}), 400

    user = User(username=username, email=email, password=password)
    db.session.add(user)
    db.session.commit()
    
    return jsonify({"message": "Signup successful"}), 201


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    email_or_username = data.get("email_or_username")
    password = data.get("password")

    user = User.query.filter(
        (User.email == email_or_username) |
        (User.username == email_or_username)
    ).first()

    if user and user.password == password:
        return jsonify({"user_id": user.id}), 200

    return send_from_directory(app.template_folder, "index.html")

@app.route("/api/logout", methods=["POST"])
def logout():
    return jsonify({"message": "Logged out"}), 200

@app.route("/api/current_index", methods=["GET"])
def current_index():
    return jsonify({
        "index": player.current_index
    })

@app.route("/api/state", methods=["GET"])
def get_state():
    return jsonify({
        "mode": player_state["mode"],
        "status": player_state["status"],

        # 🔥 MAIN FIX FOR HIGHLIGHT
        "current_index": player.current_index if hasattr(player, "current_index") else 0,

        # voice + gesture
        "voice": voice_status.get("active", False),
        "gesture": False
    })



# ---------------- LOCAL PLAYER CONTROLS ----------------
@app.route("/api/play", methods=["POST"])
def play():
    player.play()
    player_state["status"] = "playing"
    player_state["mode"] = "local"
    return jsonify({"message": "Playing local song"}), 200

@app.route("/api/play_by_name", methods=["POST"])
def play_by_name():
    data = request.get_json()
    name = data.get("name", "").lower().strip()

    # ----- SPECIAL COMMANDS -----
    if name == "last song":
        player.current_index = len(local_songs) - 1
        player.play()
        return jsonify({"message": "playing last song"})

    if name == "first song":
        player.current_index = 0
        player.play()
        return jsonify({"message": "playing first song"})

    if name == "random song":
        import random
        player.current_index = random.randint(0, len(local_songs)-1)
        player.play()
        return jsonify({"message": "playing random song"})
    # ----- FUZZY + HALF MATCH -----
    best_index = None

    for i, song in enumerate(local_songs):
        base = os.path.basename(song).lower()

        clean = base.replace(".mp3","").replace("_"," ").replace("-"," ")
        # exact / partial match
        if name in clean:
            best_index = i
            break

        # fuzzy replace
        if name.replace("a","aa") in clean or name.replace("aa","a") in clean:
            best_index = i
            break
    if best_index is not None:
        player.current_index = best_index
        player.play()

        return jsonify({
            "message": "playing",
            "index": best_index,
            "song": os.path.basename(local_songs[best_index])
        })
    return jsonify({"error": "song not found"}), 404

@app.route("/api/play_index", methods=["POST"])
def play_index():
    data = request.get_json()
    index = int(data.get("index"))

    # ✅ Sahi list use karo
    if index < 0 or index >= len(local_songs):
        return jsonify({"error": "invalid index"})

    # ✅ MusicPlayer ka index set
    player.current_index = index

    # ✅ Existing player ka play function use karo
    player.play()

    player_state["status"] = "playing"
    player_state["mode"] = "local"

    return jsonify({
        "msg": "playing",
        "index": index,
        "song": os.path.basename(local_songs[index])
    })

@app.route("/api/pause", methods=["POST"])
def pause():
    player.pause()
    player_state["status"] = "paused"
    player_state["mode"] = "local"
    return jsonify({"message": "Paused"}), 200

@app.route("/api/next", methods=["POST"])
def next_song():
    player.next_song()

    player_state["status"] = "playing"
    player_state["mode"] = "local"

    return jsonify({
        "message": "Next song",
        "current_index": player.current_index
    }), 200

@app.route("/api/prev", methods=["POST"])
def prev_song():
    player.prev_song()

    player_state["status"] = "playing"
    player_state["mode"] = "local"

    return jsonify({
        "message": "Previous song",
        "current_index": player.current_index
    }), 200


@app.route("/api/volume_up", methods=["POST"])
def volume_up():
    player.volume_up()
    player_state["status"] = "volumed up"
    player_state["mode"] = "local"
    return jsonify({"message": "Volume up"}), 200

@app.route("/api/volume_down", methods=["POST"])
def volume_down():
    player.volume_down()
    player_state["status"] = "volumed down"
    player_state["mode"] = "local"
    return jsonify({"message": "Volume down"}), 200

@app.route("/api/like", methods=["POST"])
def like():
    player.like()
    player_state["status"] = "liked"
    player_state["mode"] = "local"
    return jsonify({"message": "Liked"}), 200

@app.route("/api/dislike", methods=["POST"])
def dislike():
    player.dislike()
    player_state["status"] = "disliked"
    player_state["mode"] = "local"
    return jsonify({"message": "Disliked"}), 200

# ---------------- SPOTIFY CONTROLS ----------------
@app.route("/api/spotify/login")
def spotify_login():
    auth_url = spotify_ctrl.oauth.get_authorize_url()
    return redirect(auth_url)


@app.route("/api/spotify/callback")
def spotify_callback():
    code = request.args.get("code")
    token_info = spotify_ctrl.oauth.get_access_token(code)
    spotify_ctrl.set_token(token_info)

    return redirect("http://localhost:3000")

@app.route("/api/spotify/play", methods=["POST"])
def spotify_play():
    if not spotify_ctrl.is_ready():
        return jsonify({"error": "Spotify not logged in"}), 401
    player.play_spotify()
    player_state["status"] = "playing"
    player_state["mode"] = "spotify"
    return jsonify({"message": "Spotify playing"}), 200


@app.route("/api/spotify/stop", methods=["POST"])
def spotify_stop():
    if not spotify_ctrl.is_ready():
        return jsonify({"error": "Spotify not logged in"}), 401
    player.stop_spotify()
    player_state["status"] = "paused"
    player_state["mode"] = "spotify"
    return jsonify({"message": "Spotify stopped"}), 200

@app.route("/api/spotify/next", methods=["POST"])
def spotify_next():
    if not spotify_ctrl.is_ready():
        return jsonify({"error": "Spotify not logged in"}), 401
    player.next_spotify()
    player_state["status"] = "next song"
    player_state["mode"] = "spotify"
    return jsonify({"message": "Spotify next"}), 200

@app.route("/api/spotify/prev", methods=["POST"])
def spotify_prev():
    if not spotify_ctrl.is_ready():
        return jsonify({"error": "Spotify not logged in"}), 401
    player.prev_spotify()
    player_state["status"] = "previous song"
    player_state["mode"] = "spotify"
    return jsonify({"message": "Spotify previous"}), 200


# gesture and voice api routes
@app.route("/api/gesture/start", methods=["POST"])
def gesture_start_route():
    start_gesture_thread = threading.Thread(target=start_gesture, daemon=True)
    start_gesture_thread.start()
    return "", 200

@app.route("/api/gesture/stop", methods=["POST"])
def gesture_stop_route():
    stop_gesture()
    return "", 200

@app.route("/api/web_gesture", methods=["POST"])
def web_gesture():
    import base64, cv2, numpy as np
    data = request.json["image"]
    img_data = base64.b64decode(data.split(",")[1])
    np_arr = np.frombuffer(img_data, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    action = detect_from_image(frame)

    if action == "play": player.play()
    elif action == "pause": player.pause()
    elif action == "next": player.next_song()
    elif action == "prev": player.prev_song()

    return jsonify({"action": action})

@app.route("/api/voice_text", methods=["POST"])
def voice_text():
    text = request.json["text"].lower()
    if "play" in text: player.play()
    elif "pause" in text: player.pause()
    elif "next" in text: player.next_song()
    elif "previous" in text or "prev" in text: player.prev_song()
    elif "volume up" in text: player.volume_up()
    elif "volume down" in text: player.volume_down()
    return {"ok": True}



voice_status = {"active":False}
@app.route("/api/voice/start", methods=["POST"])
def voice_start_route():
    start_voice()
    voice_status["active"] = True
    return {"status":"voice started"}, 200

@app.route("/api/voice/stop", methods=["POST"])
def voice_stop_route():
    stop_voice()
    voice_status["active"] = False
    return {"status":"voice stopped"}, 200

@app.route("/api/voice_active", methods=["POST"])
def voice_active():
    voice_status["active"] = True
    print("🎤 Voice wake word detected")
    return {"status": "voice active"}

@app.route("/api/voice_inactive", methods=["POST"])
def voice_inactive():
    voice_status["active"] = False
    return {"active": False}

@app.route("/api/voice_status")
def get_voice_status():
    return voice_status

@app.route('/shutdown', methods=['POST'])
def shutdown():
    os._exit(0)
    return "ok"


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
