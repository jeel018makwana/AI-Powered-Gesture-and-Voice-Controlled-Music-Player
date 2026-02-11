# import cv2
# import time
# import requests
# import mediapipe as mp
# from mediapipe.tasks.python.vision import hand_landmarker
# from mediapipe.tasks.python import core
# import os
# import threading

# # ---------------- CONFIG ----------------
# API_BASE = "http://127.0.0.1:5000/api"
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# MODEL_PATH = os.path.join(BASE_DIR, "hand_landmarker.task")
# COOLDOWN = 0.8  # seconds between gestures

# running = False
# last_action_time = 0
# last_gesture_ping = 0
# gesture_thread = None  # Thread-safe for EXE

# # ---------------------------------------

# # ------------ CALLBACK -----------
# def gesture_callback(result, output_image, timestamp_ms):
#     global last_action_time
#     global last_gesture_ping
#     if not running:
#         return

#     if time.time() - last_gesture_ping > 2: 
#         try:
#             requests.post(f"{API_BASE}/gesture_active")
#         except:
#             pass
#         last_gesture_ping = time.time()

#     if time.time() - last_action_time < COOLDOWN:
#         return

#     if not result.hand_landmarks:
#         return

#     hand = result.hand_landmarks[0]

#     thumb_tip = hand[4]
#     index_tip = hand[8]
#     middle_tip = hand[12]
#     ring_tip = hand[16]
#     pinky_tip = hand[20]
#     wrist = hand[0]

#     # Open palm -> Play
#     if all([thumb_tip.y < index_tip.y,
#             index_tip.y < middle_tip.y,
#             middle_tip.y < ring_tip.y,
#             ring_tip.y < pinky_tip.y]):
#         try:
#             requests.post(f"{API_BASE}/play")
#         except:
#             pass
#         print("Play")
#         last_action_time = time.time()
#         return

#     # Fist -> Pause
#     if all([thumb_tip.y > index_tip.y,
#             index_tip.y > middle_tip.y,
#             middle_tip.y > ring_tip.y,
#             ring_tip.y > pinky_tip.y]):
#         try:
#             requests.post(f"{API_BASE}/pause")
#         except:
#             pass
#         print("Pause")
#         last_action_time = time.time()
#         return

#     # Swipe right -> Next
#     if index_tip.x - wrist.x > 0.25:
#         try:
#             requests.post(f"{API_BASE}/next")
#         except:
#             pass
#         print("Next")
#         last_action_time = time.time()
#         return

#     # Swipe left -> Previous
#     if index_tip.x - wrist.x < -0.25:
#         try:
#             requests.post(f"{API_BASE}/prev")
#         except:
#             pass
#         print("Prev")
#         last_action_time = time.time()
#         return

#     # Pinch out -> Volume up
#     pinch_dist = abs(thumb_tip.x - index_tip.x)
#     if pinch_dist > 0.18:
#         try:
#             requests.post(f"{API_BASE}/volume_up")
#         except:
#             pass
#         print("Volume Up")
#         last_action_time = time.time()
#         return

#     if pinch_dist < 0.04:
#         try:
#             requests.post(f"{API_BASE}/volume_down")
#         except:
#             pass
#         print("Volume Down")
#         last_action_time = time.time()
#         return

#     # Thumb up -> Like
#     if thumb_tip.y < index_tip.y - 0.05:
#         try:
#             requests.post(f"{API_BASE}/like")
#         except:
#             pass
#         print("Like")
#         last_action_time = time.time()
#         return

#     # Thumb down -> Dislike
#     if thumb_tip.y > index_tip.y + 0.1:
#         try:
#             requests.post(f"{API_BASE}/dislike")
#         except:
#             pass
#         print("Dislike")
#         last_action_time = time.time()
#         return

# # --------- Initialize HandLandmarker Task -------

# landmarker = None

# # ---------------- CAMERA LOOP ----------------
# def _gesture_loop():
#     global running, landmarker
#     if landmarker is None:
#         base_options = core.base_options.BaseOptions(model_asset_path=MODEL_PATH)
#         options = hand_landmarker.HandLandmarkerOptions(
#             base_options=base_options,
#             running_mode=hand_landmarker._RunningMode.LIVE_STREAM,
#             result_callback=gesture_callback,
#             num_hands=1
#         )
#         landmarker = hand_landmarker.HandLandmarker.create_from_options(options)

#     cap = cv2.VideoCapture(0)
#     while running:
#         ret, frame = cap.read()
#         if not ret:
#             break

#         frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
#         timestamp_ms = int(time.time() * 1000)
#         landmarker.detect_async(mp_image, timestamp_ms)

#         cv2.namedWindow("Gesture Control", cv2.WINDOW_NORMAL)
#         cv2.resizeWindow("Gesture Control", 640, 480)
#         cv2.imshow("Gesture Control", frame)
#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             stop_gesture()
#             break

#     cap.release()
#     cv2.destroyAllWindows()
#     running = False

# def start_gesture():
#     global running, gesture_thread
#     if running:
#         return
#     running = True
#     gesture_thread = threading.Thread(target=_gesture_loop, daemon=True)
#     gesture_thread.start()

# def stop_gesture():
#     global running, landmarker
#     if running:
#         running = False
#         landmarker = None
#         try:
#             requests.post(f"{API_BASE}/gesture_inactive")
#         except:
#             pass




import time
import requests

# ---------------- CONFIG ----------------
API_BASE = "http://127.0.0.1:5000/api"
COOLDOWN = 0.8  # seconds between gestures
last_action_time = 0

# ---------------- GESTURE LOGIC ----------------
def detect_from_image(frame):
    """
    Input: frame (image from browser)
    Output: action string ("play", "pause", "next", "prev", "volume_up", "volume_down", "like", "dislike", "none")
    Logic: Same as original EXE version
    """
    global last_action_time
    import mediapipe as mp

    # --- Mediapipe Hand Detection ---
    mp_hands = mp.solutions.hands
    with mp_hands.Hands(static_image_mode=True, max_num_hands=1) as hands:
        results = hands.process(frame)

        if not results.multi_hand_landmarks:
            return "none"

        hand = results.multi_hand_landmarks[0]

        thumb_tip = hand.landmark[4]
        index_tip = hand.landmark[8]
        middle_tip = hand.landmark[12]
        ring_tip = hand.landmark[16]
        pinky_tip = hand.landmark[20]
        wrist = hand.landmark[0]

        current_time = time.time()
        if current_time - last_action_time < COOLDOWN:
            return "none"

        # Open palm -> Play
        if all([thumb_tip.y < index_tip.y,
                index_tip.y < middle_tip.y,
                middle_tip.y < ring_tip.y,
                ring_tip.y < pinky_tip.y]):
            last_action_time = current_time
            return "play"

        # Fist -> Pause
        if all([thumb_tip.y > index_tip.y,
                index_tip.y > middle_tip.y,
                middle_tip.y > ring_tip.y,
                ring_tip.y > pinky_tip.y]):
            last_action_time = current_time
            return "pause"

        # Swipe right -> Next
        if index_tip.x - wrist.x > 0.25:
            last_action_time = current_time
            return "next"

        # Swipe left -> Previous
        if index_tip.x - wrist.x < -0.25:
            last_action_time = current_time
            return "prev"

        # Pinch out -> Volume up
        pinch_dist = abs(thumb_tip.x - index_tip.x)
        if pinch_dist > 0.18:
            last_action_time = current_time
            return "volume_up"

        if pinch_dist < 0.04:
            last_action_time = current_time
            return "volume_down"

        # Thumb up -> Like
        if thumb_tip.y < index_tip.y - 0.05:
            last_action_time = current_time
            return "like"

        # Thumb down -> Dislike
        if thumb_tip.y > index_tip.y + 0.1:
            last_action_time = current_time
            return "dislike"

    return "none"

# ---------------- SEND ACTION TO SERVER ----------------
def send_action(action):
    if action == "none":
        return
    try:
        requests.post(f"{API_BASE}/{action}")
    except:
        pass
