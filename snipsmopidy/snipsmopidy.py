# -*-: coding utf-8 -*-
""" Mopidy skill for Snips. """

from __future__ import unicode_literals

from mpd import MPDClient
from mpd import ConnectionError
from spotify import SpotifyClient
import time

MAX_VOLUME = 100
GAIN = 4
MPD_PORT = 6600


class SnipsMopidy:
    """Mopidy skill for Snips.

    :param mopidy_host: The hostname of the Mopidy player
    """

    def __init__(self, spotify_refresh_token=None, mopidy_host='127.0.0.1', locale=None):
        self.host = mopidy_host
        self.client = MPDClient()
        self.client.connect(self.host, MPD_PORT)
        status = self.client.status()
        self.previous_volume = int(status.get('volume'))
        self.max_volume = MAX_VOLUME
        if spotify_refresh_token is not None:
            self.spotify = SpotifyClient(spotify_refresh_token)

    def pause_mopidy(self):
        self.client.pause(1)

    def volume_up(self, level):
        if self.client is None:
            return
        level = int(level)*10 if level is not None else 10
        status = self.client.status()
        current_volume = int(status.get('volume'))
        self.client.setvol(min(
            current_volume + GAIN * level,
            self.max_volume))
        if status.get('state') != 'play':
            self.client.play()

    def volume_down(self, level):
        if self.client is None:
            return
        level = int(level)*10 if level is not None else 10
        status = self.client.status()
        current_volume = int(status.get('volume'))
        self.client.setvol(current_volume - GAIN * level)
        if status.get('state') != 'play':
            self.client.play()

    def set_volume(self, volume_value):
        if self.client is None:
            return
        self.client.setvol(volume_value)
        self.client.play()

    def set_to_low_volume(self):
        try:
            if self.client is None:
                return
            status = self.client.status()
            if status.get('state') != 'play':
                return None
            current_volume = int(status.get('volume'))
            self.previous_volume = current_volume
            self.client.setvol(min(30, current_volume))
            if status.get('state') != 'play':
                self.client.play()
        except ConnectionError:
            print("Connection Error. Trying to reconnect with mpd")
            self.client.connect(self.host, MPD_PORT)
            self.set_to_low_volume()

    def set_to_previous_volume(self):
        if self.client is None:
            return
        if self.previous_volume is None:
            return None
        self.client.setvol(self.previous_volume)
        status = self.client.status()
        if status.get('state') != 'play':
            self.client.play()

    def stop_mopidy(self):
        if self.client is None:
            return
        self.client.stop()

    def play_playlist(self, name, _shuffle=False):
        if self.client is None:
            return None
        if self.spotify is None:
            return None
        tracks = self.spotify.get_playlist(name)
        if tracks is None:
            return None
        self.client.stop()
        self.client.clear()
        for track in tracks:
            try:
                self.client.add(track['track']['uri'])
            except Exception:
                print("Song not available in catalogue")
        if _shuffle:
            self.client.shuffle()
        self.client.play()

    def play_artist(self, name):
        if self.client is None:
            return None
        if self.spotify is None:
            return None
        tracks = self.spotify.get_top_tracks_from_artist(name)
        if tracks is None:
            return None
        self.client.stop()
        self.client.clear()
        for track in tracks:
            self.client.add(track['uri'])
        self.client.play()

    def play_album(self, album, _shuffle=False):
        if self.client is None:
            return
        if self.spotify is None:
            return
        tracks = self.spotify.get_tracks_from_album(album)
        if tracks is None:
            return None
        self.client.stop()
        self.client.clear()
        for track in tracks:
            self.client.add(track['uri'])
        if _shuffle:
            self.client.shuffle()
        self.client.play()

    def play_song(self, name):
        if self.client is None:
            return
        if self.spotify is None:
            return
        track = self.spotify.get_track(name)
        if track is None:
            return None
        self.client.stop()
        self.client.clear()
        self.client.add(track['uri'])
        self.client.play()

    def play_next_item_in_queue(self):
        if self.client is None:
            return
        try:
            self.client.next()
        except Exception:
            print("Failed to play next item, maybe last song?")

    def play_previous_item_in_queue(self):
        if self.client is None:
            return
        try:
            self.client.previous()
        except Exception:
            print("Failed to play previous item, maybe first song?")

    def get_info(self):
        # Get info about currently playing tune
        info = self.client.currentsong()
        return info['title'], info['artist'], info['album']

    def add_song(self):
        # Save song in spotify
        info = self.client.currentsong()
        self.spotify.add_song(info['artist'], info['title'])

    def play(self):
        self.client.play()
