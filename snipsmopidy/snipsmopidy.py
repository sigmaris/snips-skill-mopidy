# -*-: coding utf-8 -*-
""" Mopidy skill for Snips. """

from __future__ import unicode_literals
from functools import wraps

from mpd import MPDClient
from mpd import ConnectionError
from spotify import SpotifyClient
import time

MAX_VOLUME = 100
GAIN = 4
MPD_PORT = 6600


def room_based(fn):
    @wraps(fn)
    def wrapper(self, site_id, *args, **kwargs):
        return fn(self, self.get_client(site_id), *args, **kwargs)
    return wrapper


class SnipsMopidy:
    """Mopidy skill for Snips.

    :param mopidy_host: The hostname of the Mopidy player
    """

    def __init__(self, mopidy_rooms={'default': {'host': '127.0.0.1', 'port': 6600}}, locale=None):
        self.mopidy_rooms = mopidy_rooms
        self.mopidy_instances = {}
        self.prev_volume = {}
        def connect_one_mopidy(name, details):
            while True:
                client = MPDClient()
                try:
                    client.connect(details['host'], details['port'])
                    self.prev_volume[name] = int(client.status().get('volume', MAX_VOLUME))
                    self.mopidy_instances[name] = client
                    break
                except Exception as ex:
                    print("Mopidy is not yet available on {}, retrying".format(name))
                    print("...")
                    time.sleep(5)

        connect_threads = [
            threading.Thread(target=connect_one_mopidy, args=(k, v))
            for k, v in mopidy_rooms.items()
        ]
        for t in connect_threads:
            t.start()
        for t in connect_threads:
            t.join()

        if spotify_refresh_token is not None:
            self.spotify = SpotifyClient(spotify_refresh_token, spotify_client_id, spotify_client_secret)

    def get_client(self, site_id):
        if site_id in self.mopidy_instances:
            return self.mopidy_instances[site_id]
        else:
            return self.mopidy_instances['default']

    @room_based
    def pause(self, client):
        client.pause(1)

    @room_based
    def volume_up(self, client, level):
        level = int(level)*10 if level is not None else 10
        status = client.status()
        current_volume = int(status.get('volume'))
        client.setvol(min(
            current_volume + GAIN * level,
            MAX_VOLUME))
        if status.get('state') != 'play':
            client.play()

    @room_based
    def volume_down(self, client, level):
        level = int(level)*10 if level is not None else 10
        status = client.status()
        current_volume = int(status.get('volume'))
        client.setvol(current_volume - GAIN * level)
        if status.get('state') != 'play':
            client.play()

    @room_based
    def set_volume(self, client, volume_value):
        client.setvol(volume_value)
        client.play()

    def set_to_low_volume(self, site_id):
        client = self.get_client(site_id)
        status = client.status()
        if status.get('state') != 'play':
            return None
        current_volume = int(status.get('volume'))
        self.prev_volume[site_id] = current_volume  # TODO: previous_volume no longer exists
        client.setvol(min(30, current_volume))
        if status.get('state') != 'play':
            client.play()

    def set_to_previous_volume(self, site_id):
        if site_id not in self.prev_volume:
            return None
        client = self.get_client(site_id)
        client.setvol(self.prev_volume[site_id])
        status = client.status()
        if status.get('state') != 'play':
            client.play()

    @room_based
    def stop(self, client):
        client.stop()

    @room_based
    def play_playlist(self, client, name, _shuffle=False):
        if self.spotify is not None:
            return self.play_spotify_playlist(client, name, _shuffle)
        mpd_pls = self.client.listplaylists()
        # TODO: recognise playlist

    def play_spotify_playlist(self, client, name, _shuffle=False):
        tracks = self.spotify.get_playlist(name)
        if tracks is None:
            return None
        client.stop()
        client.clear()
        for track in tracks:
            try:
                client.add(track['track']['uri'])
            except Exception:
                print("Song not available in catalogue")
        if _shuffle:
            client.shuffle()
        client.play()

    @room_based
    def play_artist(self, client, name):
        if self.spotify is None:
            return None
        tracks = self.spotify.get_top_tracks_from_artist(name)
        if tracks is None:
            return None
        client.stop()
        client.clear()
        for track in tracks:
            client.add(track['uri'])
        client.play()

    @room_based
    def play_album(self, client, album, _shuffle=False):
        if self.spotify is None:
            return
        tracks = self.spotify.get_tracks_from_album(album)
        if tracks is None:
            return None
        client.stop()
        client.clear()
        for track in tracks:
            client.add(track['uri'])
        if _shuffle:
            client.shuffle()
        client.play()

    @room_based
    def play_song(self, client, name):
        if self.spotify is None:
            return
        track = self.spotify.get_track(name)
        if track is None:
            return None
        client.stop()
        client.clear()
        client.add(track['uri'])
        client.play()

    @room_based
    def play_next_item_in_queue(self, client):
        try:
            client.next()
        except Exception:
            print("Failed to play next item, maybe last song?")

    @room_based
    def play_previous_item_in_queue(self, client):
        try:
            client.previous()
        except Exception:
            print("Failed to play previous item, maybe first song?")

    @room_based
    def get_info(self, client):
        # Get info about currently playing tune
        info = client.currentsong()
        return info['title'], info['artist'], info['album']

    @room_based
    def add_song(self, client):
        # TODO: Save song in spotify
        info = client.currentsong()
        self.spotify.add_song(info['artist'], info['title'])

    @room_based
    def play(self, client):
        client.play()
