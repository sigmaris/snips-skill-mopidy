# -*-: coding utf-8 -*-
""" Mopidy skill for Snips. """

from __future__ import unicode_literals

import requests
import mopidy.models
import json
from requests import ConnectionError
import time

MAX_VOLUME = 100
GAIN = 4
HTTP_PORT = 6680
MOPIDY_RELATIVE = '/mopidy/rpc'


class SnipsMopidy:
    """Mopidy skill for Snips.

    :param mopidy_host: The hostname of the Mopidy http server
    """

    def __init__(self, mopidy_host='127.0.0.1', locale=None):
        self.host = mopidy_host
        self.url = "http://{}:{}{}".format(mopidy_host, HTTP_PORT, MOPIDY_RELATIVE)
        connexion_established = False
        while not connexion_established:
            try:
                self.get_current_track()
                connexion_established = True
            except ConnectionError:
                print("Mopidy is not yet available, please wait or be sure it is running typing: "
                      "systemctl status mopidy")
                print("...")
                time.sleep(5)

        self.previous_volume = self.get_volume()
        self.max_volume = MAX_VOLUME

    def run(self, method, params=None):
        json_rpc = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': method
        }

        if params is not None:
            json_rpc['params'] = params

        response = requests.post(
            self.url,
            data=json.dumps(
                json_rpc,
                cls=mopidy.models.ModelJSONEncoder
            )
        )

        decoded = json.loads(
            response.text,
            object_hook=mopidy.models.model_json_decoder
        )

        if 'error' in decoded:
            print(decoded['error'])
            return None
        return decoded['result']

    def get_current_track(self):
        return self.run('core.playback.get_current_track')

    def get_tl_tracks(self):
        return self.run('core.tracklist.get_tl_tracks')

    def play(self, tl_track=None, tlid=None):
        return self.run(
            'core.playback.play',
            {
                'tl_track': tl_track,
                'tlid': tlid
            }
        )

    def play_first(self):
        tracklist = self.get_tl_tracks()
        return self.play_tlid(tracklist[0].tlid)

    def play_tlid(self, tlid):
        return self.play(tlid=tlid)

    def pause(self):
        return self.run('core.playback.pause')

    def stop(self):
        return self.run('core.playback.stop')

    def get_status(self):
        """
        Get the current state of the playback
        :return: String either playing, paused, or stopped
        """
        return self.run('core.playback.get_state')

    def set_volume(self, percent):
        return self.run(
            'core.mixer.set_volume',
            {'volume': percent}
        )

    def get_volume(self):
        return self.run('core.mixer.get_volume')

    def volume_up(self):
        volume = self.get_volume()
        if volume is None:
            self.set_volume(50)
        else:
            self.set_volume(min(100, volume + 10))
        status = self.get_status()
        if status != 'playing':
            self.play()

    def volume_down(self):
        volume = self.get_volume()
        if volume is None:
            self.set_volume(50)
        else:
            self.set_volume(max(0, volume - 10))
        status = self.get_status()
        if status != 'playing':
            self.play()

    def set_to_low_volume(self):
        status = self.get_status()
        if status != 'playing':
            return None
        current_volume = self.get_volume()
        print(current_volume)
        self.previous_volume = current_volume
        self.set_volume(min(30, current_volume))
        current_volume = int(self.get_volume())
        print(current_volume)
        self.play()

    def set_to_previous_volume(self):
        if self.previous_volume is None:
            return None
        self.set_volume(self.previous_volume)
        status = self.get_status()
        if status != 'playing':
            self.play()

    def next_song(self):
        return self.run('core.playback.next')

    def previous_song(self):
        return self.run('core.playback.previous')

    def mute(self):
        mute_state = self.run('core.mixer.get_mute')

        if mute_state is None:
            mute_state = True

        return self.run(
            'core.mixer.set_mute',
            {'mute': not mute_state}
        )

    def shuffle(self):
        return self.run('core.tracklist.shuffle')

    def search(self, parameters):
        return self.run('core.library.search', parameters)

    def search_spotify(self, parameters):
        spotify = parameters.copy()
        spotify['uris'] = ['spotify:']
        return self.search(spotify)

    def search_any(self, search_term):
        return self.search_spotify({'any': [search_term]})

    def search_genre(self, genre):
        return self.search_spotify({'genre': [genre]})

    def search_artist(self, artist):
        return self.search_spotify({'artist': [artist]})

    def search_album(self, album):
        search_results = self.search_spotify({'album': [album]})
        album_uri = search_results[0].albums[0].uri
        return self.search_spotify({'uri': [album_uri]})

    def search_track(self, track):
        return self.search_spotify({'track_name': [track]})

    def add_to_tracklist(self, tracks=None, uris=None):
        if tracks is not None:
            return self.run(
                'core.tracklist.add',
                {'tracks': tracks}
            )
        elif uris is not None:
            return self.run(
                'core.tracklist.add',
                {'uris': uris}
            )
        else:
            return None

    def clear_tracklist(self):
        return self.run('core.tracklist.clear')

    def set_tracks(self, new_tracks):
        if 0 < len(new_tracks):
            self.clear_tracklist()
            self.pause()
            self.add_to_tracklist(tracks=new_tracks)
            return True
        else:
            print('Empty tracklist')
            return False

    def set_uris(self, new_track_uris):
        if 0 < len(new_track_uris):
            self.clear_tracklist()
            self.pause()
            self.add_to_tracklist(uris=new_track_uris)
            return True
        else:
            print('Empty tracklist')
            return False

    def set_search(self, search_results):
        tracks = [
            track
            for result in search_results
            for track in result.tracks
        ]
        return self.set_tracks(tracks)

    def find_similar_playlist(self, name):
        # TODO send to TTS bus
        print("No playlists found, trying to find a similar playlist...".format(name))
        return self.set_search(music.search_genre(name))

    def search_playlist(self, name):
        playlists = self.run('core.playlists.as_list')

        if playlists is None:
            return self.find_similar_playlist(name)
        playlists = filter(
            lambda playlist: playlist.name.lower().startswith(name.lower()),
            playlists
        )
        return playlists

    def set_playlist(self, playlists, name):
        if 0 == len(playlists):
            return self.find_similar_playlist(name)

        refs = self.run(
            'core.playlists.get_items',
            {'uri': playlists[0].uri}
        )

        return self.set_uris([ref.uri for ref in refs])

    def get_info(self):
        # Get info about currently playing tune
        track = self.get_current_track()
        title = track.name
        artist = [artist.name for artist in track.album.artists][0]
        album = track.album.name
        return title, artist, album

    def play_song(self, name, shuffle=False):
        is_set = self.set_search(self.search_track(name))
        if is_set:
            if shuffle:
                self.shuffle()
            self.play_first()

    def play_album(self, name, shuffle=False):
        is_set = self.set_search(self.search_album(name))
        if is_set:
            if shuffle:
                self.shuffle()
            self.play_first()

    def play_artist(self, name, shuffle=False):
        is_set = self.set_search(self.search_artist(name))
        if is_set:
            if shuffle:
                self.shuffle()
            self.play_first()

    def play_playlist(self, name, shuffle=False):
        is_set = self.set_playlist(self.search_playlist(name), name)
        if is_set:
            if shuffle:
                self.shuffle()
            self.play_first()

    def play_genre(self, name, shuffle=False):
        is_set = self.set_search(self.search_artist(name))
        if is_set:
            if shuffle:
                self.shuffle()
            self.play_first()
