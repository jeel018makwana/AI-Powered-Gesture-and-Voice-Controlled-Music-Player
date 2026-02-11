# backend/spotify_control.py
import spotipy
from spotipy.oauth2 import SpotifyOAuth

class SpotifyController:
    def __init__(self, client_id, client_secret, redirect_uri):
        self.oauth = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope="user-modify-playback-state user-read-playback-state user-read-currently-playing"
        )
        self.sp = None   # ❗ login ke baad set hoga

    def set_token(self, token_info):
        self.sp = spotipy.Spotify(auth=token_info["access_token"])
        

    def is_ready(self):
        return self.sp is not None

    def play(self):
        if self.sp:
            self.sp.start_playback()

    def pause(self):
        if self.sp:
            self.sp.pause_playback()

    def next_song(self):
        if self.sp:
            self.sp.next_track()

    def prev_song(self):
        if self.sp:
            self.sp.previous_track()

    def stop_spotify(self):
        if self.sp:
            self.sp.pause_playback()
