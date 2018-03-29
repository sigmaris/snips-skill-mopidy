# -*-: coding utf-8 -*-
""" Mopidy skill for Snips. """

from __future__ import unicode_literals

from mopidyclient import MopidyClient

GAIN = 4


class SnipsMopidy:
    """Mopidy skill for Snips.

    :param mopidy_host: The hostname of the Mopidy http server
    """

    def __init__(self, mopidy_host='127.0.0.1', locale=None):
        self.client = MopidyClient(mopidy_host)

    def get_client(self):
        return self.client

    def play(self):
        self.client.play()

    def stop(self):
        self.client.stop()

    def pause(self):
        self.client.pause()

    def volume_up(self, level):
        level = int(level) * 10 if level is not None else 10
        current_volume = self.client.get_volume()
        if current_volume is None:
            self.client.set_volume(50)
        else:
            self.client.set_volume(min(100, current_volume + GAIN * level))
        status = self.client.get_status()
        if status != 'playing':
            self.client.play()

    def volume_down(self, level):
        level = int(level) * 10 if level is not None else 10
        current_volume = self.client.get_volume()
        if current_volume is None:
            self.client.set_volume(50)
        else:
            self.client.set_volume(max(0, current_volume - GAIN * level))
        status = self.client.get_status()
        if status != 'playing':
            self.client.play()

    def set_to_low_volume(self):
        status = self.client.get_status()
        if status != 'playing':
            return None
        current_volume = self.client.get_volume()
        self.client.previous_volume = current_volume
        self.client.set_volume(min(30, current_volume))

    def set_to_previous_volume(self):
        if self.client.previous_volume is None:
            return None
        self.client.set_volume(self.client.previous_volume)
        status = self.client.get_status()
        if status != 'playing':
            self.client.play()

    def next_song(self):
        self.client.next_song()

    def previous_song(self):
        self.client.previous_song()

    def get_info(self):
        # Get info about currently playing tune
        track = self.client.get_current_track()
        title = track.name
        artist = [artist.name for artist in track.album.artists][0]
        album = track.album.name
        return title, artist, album

    def play_song(self, name, shuffle=False):
        is_set = self.client.set_search(self.client.search_track(name))
        if is_set:
            if shuffle:
                self.client.shuffle()
            self.client.play_first()

    def play_album(self, name, shuffle=False):
        is_set = self.client.set_search(self.client.search_album(name))
        if is_set:
            if shuffle:
                self.client.shuffle()
            self.client.play_first()

    def play_artist(self, name, shuffle=False):
        is_set = self.client.set_search(self.client.search_artist(name))
        if is_set:
            if shuffle:
                self.client.shuffle()
            self.client.play_first()

    def play_playlist(self, name, shuffle=False):
        is_set = self.client.set_playlist(self.client.search_playlist(name), name)
        if is_set:
            if shuffle:
                self.client.shuffle()
            self.client.play_first()

    def play_genre(self, name, shuffle=False):
        is_set = self.client.set_search(self.client.search_genre(name))
        if is_set:
            if shuffle:
                self.client.shuffle()
            self.client.play_first()

