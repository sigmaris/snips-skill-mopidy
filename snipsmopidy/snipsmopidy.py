# -*-: coding utf-8 -*-
""" Mopidy skill for Snips. """

from __future__ import unicode_literals
from functools import wraps
import threading
import time
import traceback

from fuzzywuzzy import fuzz
from mpd import MPDClient
from mpd import ConnectionError

from .spotify import SpotifyClient

MAX_VOLUME = 100
GAIN = 4
MPD_PORT = 6600
FUZZ_RATIO = 80
LOW_VOLUME = 10


def capwords(in_str):
    return ' '.join(s[:1].upper() + s[1:] for s in in_str.split())


def room_based(fn):
    @wraps(fn)
    def wrapper(self, site_id, *args, **kwargs):
        try:
            client = self.get_client(site_id)
            client.ping()
            return fn(self, site_id, client, *args, **kwargs)
        except ConnectionError:
            self.connect_one_mopidy(site_id, self.mopidy_rooms[site_id])
            return fn(self, site_id, self.get_client(site_id), *args, **kwargs)
    return wrapper


class SnipsMopidy:
    """Mopidy skill for Snips.

    :param mopidy_host: The hostname of the Mopidy player
    """

    def __init__(self, mopidy_rooms={'default': {'host': '127.0.0.1', 'port': 6600}}, locale=None):
        self.mopidy_rooms = mopidy_rooms
        self.mopidy_instances = {}
        self.prev_volume = {}

        connect_threads = [
            threading.Thread(target=self.connect_one_mopidy, args=(k, v))
            for k, v in mopidy_rooms.items()
        ]
        for t in connect_threads:
            t.start()
        for t in connect_threads:
            t.join()

        self.spotify = None
        # if spotify_refresh_token is not None:
        #     self.spotify = SpotifyClient(spotify_refresh_token, spotify_client_id, spotify_client_secret)

    def connect_one_mopidy(self, site_id, details):
        while True:
            client = MPDClient()
            try:
                client.connect(details['host'], details['port'])
                self.mopidy_instances[site_id] = client
                break
            except Exception:
                traceback.print_exc()
                print("Mopidy is not yet available on {}, retrying".format(details['host']))
                print("...")
                time.sleep(5)

    def get_client(self, site_id):
        if site_id in self.mopidy_instances:
            return self.mopidy_instances[site_id]
        else:
            return self.mopidy_instances['default']

    @room_based
    def pause(self, site_id, client):
        client.pause(1)

    @room_based
    def volume_up(self, site_id, client, level):
        level = int(level)*10 if level is not None else 10
        status = client.status()
        current_volume = int(status.get('volume'))
        new_volume = min(current_volume - GAIN * level, MAX_VOLUME)
        client.setvol(new_volume)

    @room_based
    def volume_down(self, site_id, client, level):
        level = int(level)*10 if level is not None else 10
        status = client.status()
        current_volume = int(status.get('volume'))
        new_volume = max(current_volume - GAIN * level, 0)
        client.setvol(new_volume)

    @room_based
    def set_volume(self, site_id, client, volume_value):
        client.setvol(volume_value)

    @room_based
    def set_to_low_volume(self, site_id, client):
        status = client.status()
        if status.get('state') != 'play':
            return None
        current_volume = int(status.get('volume'))
        self.prev_volume[site_id] = current_volume
        client.setvol(min(LOW_VOLUME, current_volume))

    @room_based
    def set_to_previous_volume(self, site_id, client):
        if site_id not in self.prev_volume:
            return None
        client.setvol(self.prev_volume[site_id])
        del self.prev_volume[site_id]

    @room_based
    def stop(self, site_id, client):
        client.stop()

    @room_based
    def play_playlist(self, site_id, client, name, shuffle=False):
        if self.spotify is not None:
            return self.play_spotify_playlist(client, name, shuffle)
        mpd_pls = client.listplaylists()
        for pls in mpd_pls:
            if fuzz.token_sort_ratio(pls['playlist'], name) > FUZZ_RATIO:
                client.clear()
                client.load(pls['playlist'])
                if shuffle:
                    client.shuffle()
                client.play()
                break
        else:
            # TODO TTS playlist not found
            pass

    def play_spotify_playlist(self, site_id, client, name, shuffle=False):
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
        if shuffle:
            client.shuffle()
        client.play()

    @room_based
    def play_artist(self, site_id, client, name):
        if self.spotify is not None:
            return self.play_spotify_artist(client, name)
        self.play_by_tag(client, 'artist', name)

    def play_by_tag(self, client, tag, name):
        if len(client.find(tag, capwords(name))) > 0:
            client.stop()
            client.clear()
            client.findadd(tag, capwords(name))
        elif len(client.search(tag, name)) > 0:
            client.stop()
            client.clear()
            client.searchadd(tag, name)
        else:
            return False
        client.play()
        return True

    def play_spotify_artist(self, client, name):
        tracks = self.spotify.get_top_tracks_from_artist(name)
        if tracks is None:
            return None
        client.stop()
        client.clear()
        for track in tracks:
            client.add(track['uri'])
        client.play()

    @room_based
    def play_album(self, site_id, client, album, shuffle=False):
        if self.spotify is not None:
            return self.play_spotify_album(client, album, shuffle)
        self.play_by_tag(client, 'album', album)

    def play_spotify_album(self, client, album, shuffle):
        tracks = self.spotify.get_tracks_from_album(album)
        if tracks is None:
            return None
        client.stop()
        client.clear()
        for track in tracks:
            client.add(track['uri'])
        if shuffle:
            client.shuffle()
        client.play()

    @room_based
    def play_song(self, site_id, client, name):
        if self.spotify is not None:
            return self.play_spotify_song(client, name)
        self.play_by_tag(client, 'title', name)

    def play_spotify_song(self, client, name):
        track = self.spotify.get_track(name)
        if track is None:
            return None
        client.stop()
        client.clear()
        client.add(track['uri'])
        client.play()

    @room_based
    def play_next_item_in_queue(self, site_id, client):
        try:
            client.next()
            return True
        except Exception:
            return False

    @room_based
    def play_previous_item_in_queue(self, site_id, client):
        try:
            client.previous()
            return True
        except Exception:
            return False

    @room_based
    def get_info(self, site_id, client):
        # Get info about currently playing tune
        info = client.currentsong()
        return info['title'], info['artist'], info['album']

    @room_based
    def add_song(self, site_id, client):
        # TODO: Save song in spotify
        info = client.currentsong()
        self.spotify.add_song(info['artist'], info['title'])

    @room_based
    def play(self, site_id, client):
        client.play()
