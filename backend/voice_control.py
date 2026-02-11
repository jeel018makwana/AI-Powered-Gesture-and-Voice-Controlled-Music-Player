import time
import threading
import requests
import speech_recognition as sr

API_BASE = "http://127.0.0.1:5000/api"

listening = False
voice_enabled = False   # 🔥 NEW FLAG


def play_song_by_name(name):
    try:
        requests.post(
            f"{API_BASE}/play_by_name",
            json={"name": name}
        )
        print("🎵 Playing:", name)
    except Exception as e:
        print("Song play error:", e)



def voice_callback(command):
    global voice_enabled
    command = command.lower()

    # STOP LISTENING
    if "stop listening" in command or "voice off" in command:
        voice_enabled = False
        requests.post(f"{API_BASE}/voice_inactive")
        requests.post(f"{API_BASE}/pause")
        print("Voice commands stopped")
        return

    if not voice_enabled:
        return

    try:
        # ========== PRIORITY 1 : SPOTIFY ==========
        if "spotify next" in command:
            requests.post(f"{API_BASE}/spotify/next")
            print("Spotify Next")
            return

        if "spotify previous" in command or "spotify prev" in command:
            requests.post(f"{API_BASE}/spotify/prev")
            print("Spotify Previous")
            return

        if "spotify play" in command:
            requests.post(f"{API_BASE}/spotify/play")
            print("Spotify Play")
            return

        if "spotify stop" in command:
            requests.post(f"{API_BASE}/spotify/stop")
            print("Spotify Stop")
            return


        # ========== PRIORITY 2 : LOCAL CONTROLS ==========

        if "next song" in command or command.strip() == "next":
            requests.post(f"{API_BASE}/next")
            print("Local Next")
            return

        if "previous song" in command or "prev" in command:
            requests.post(f"{API_BASE}/prev")
            print("Local Previous")
            return

        if "pause song" in command or "stop" in command or command.strip() == "pause":
            requests.post(f"{API_BASE}/pause")
            print("Local Pause")
            return


        # ========== PRIORITY 3 : SONG NAME ==========
        if "play" in command:
            name = command.replace("play", "").strip()

            # agar user ne sirf “play” bola
            if not name:
                requests.post(f"{API_BASE}/play")
                return

            # 👉 SMART NAME API
            requests.post(
                f"{API_BASE}/play_by_name",
                json={"name": name}
            )
            print("🎵 Playing:", name)

    except Exception as e:
        print("Voice API error:", e)



def voice_loop():
    global listening, voice_enabled

    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    print("🎤 Voice Control Active")
    print("Say: player play sitaare, player next song, player spotify play")

    while listening:
        try:
            with mic as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source, phrase_time_limit=4)

            text = recognizer.recognize_google(audio).lower()
            print("Heard:", text)

            # ✅ Wake word + command in SAME sentence
            if "kiki" in text:
                voice_enabled = True
                requests.post(f"{API_BASE}/voice_active")

                command = text.replace("kiki", "").strip()

                if command:
                    voice_callback(command)

        except sr.UnknownValueError:
            continue
        except sr.RequestError as e:
            print("Speech API error:", e)
        except Exception:
            continue

def start_voice():
    global listening
    if listening:
        return
    listening = True
    print("🎤 Voice STARTED") 
    threading.Thread(target=voice_loop, daemon=True).start()



def stop_voice():
    global listening
    listening = False
    voice_enabled = False
    print("🛑 Voice COMPLETELY STOPPED")



if __name__ == "__main__":
    start_voice()
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        stop_voice()
