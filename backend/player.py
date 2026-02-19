# backend/player.py

class MusicPlayer:
    def __init__(self, local_songs=[], spotify_controller=None):
        self.local_songs = local_songs
        self.current_index = 0
        self.is_playing = False
        self.volume = 50
        self.spotify = spotify_controller

    def play(self):
        self.is_playing = True

    def pause(self):
        self.is_playing = False

    def next_song(self):
        if not self.local_songs:
            return
        self.current_index = (self.current_index + 1) % len(self.local_songs)

    def prev_song(self):
        if not self.local_songs:
            return
        self.current_index = (self.current_index - 1 + len(self.local_songs)) % len(self.local_songs)

    def volume_up(self):
        self.volume = min(100, self.volume + 10)

    def volume_down(self):
        self.volume = max(0, self.volume - 10)

    def like(self):
        print("Liked")

    def dislike(self):
        print("Disliked")

    # Spotify
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
