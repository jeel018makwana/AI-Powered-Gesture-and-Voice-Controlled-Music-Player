# backend/player.py
import pygame
from backend.spotify_control import SpotifyController

class MusicPlayer:
    def __init__(self, local_songs=[], spotify_controller=None):
        self.local_songs = local_songs
        self.current_index = 0
        self.is_playing = False
        self.volume = 0.5

        # Initialize pygame mixer
        pygame.mixer.init()
        self.spotify = spotify_controller
        
    # -------- Local song methods --------
    def play(self):
        if not self.local_songs:
            return
        pygame.mixer.music.load(self.local_songs[self.current_index])
        pygame.mixer.music.set_volume(self.volume)
        pygame.mixer.music.play()
        self.is_playing = True

    def pause(self):
        pygame.mixer.music.pause()
        self.is_playing = False

    def unpause(self):
        pygame.mixer.music.unpause()
        self.is_playing = True

    def next_song(self):
        if not self.local_songs:
            return
        self.current_index = (self.current_index + 1) % len(self.local_songs)
        self.play()

    def prev_song(self):
        if not self.local_songs:
            return
        self.current_index = (self.current_index - 1 + len(self.local_songs)) % len(self.local_songs)
        self.play()

    def volume_up(self):
        self.volume = min(1.0, self.volume + 0.1)
        pygame.mixer.music.set_volume(self.volume)

    def volume_down(self):
        self.volume = max(0.0, self.volume - 0.1)
        pygame.mixer.music.set_volume(self.volume)

    def like(self):
        print(f"Song liked: {self.local_songs[self.current_index]}")

    def dislike(self):
        print(f"Song disliked: {self.local_songs[self.current_index]}")

    # -------- Spotify methods --------
    def play_spotify(self):
        if self.spotify:
            self.spotify.play()

    def stop_spotify(self):
        if self.spotify:
            self.spotify.pause()

    def next_spotify(self):
        if self.spotify:
            self.spotify.next_song()

    def prev_spotify(self):
        if self.spotify:
            self.spotify.prev_song()
