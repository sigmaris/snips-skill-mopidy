import argparse
import json
import logging

from snipslistener import SnipsListener, hotword_detected, intent, session_ended

from .snipsmopidy import SnipsMopidy

LOG = logging.getLogger(__name__)


class SnipsMopidyListener(SnipsListener):

    def __init__(self, mqtt_host, mqtt_port=1883, mopidy_rooms={'default': {'host': '127.0.0.1', 'port': 6600}}):
        super().__init__(mqtt_host, mqtt_port)
        self.skill = SnipsMopidy(mopidy_rooms)

    @hotword_detected
    def set_to_low_volume(self, data):
        self.skill.set_to_low_volume(data.site_id)

    @session_ended
    def restore_volume(self, data):
        self.skill.set_to_previous_volume(data.site_id)

    @intent('speakerInterrupt')
    def pause(self, data):
        self.skill.pause(data.site_id)
        data.session_manager.end_session()

    @intent('volumeUp')
    def volume_up(self, data):
        self.skill.set_to_previous_volume(data.site_id)
        if 'volume_higher' in data.slots:
            volume_higher = data.slots['volume_higher'].value
            LOG.debug("volume_higher={}".format(volume_higher))
            self.skill.volume_up(data.site_id, volume_higher)
        else:
            self.skill.volume_up(data.site_id, None)
        data.session_manager.end_session()

    @intent('volumeDown')
    def volume_down(self, data):
        self.skill.set_to_previous_volume(data.site_id)
        if 'volume_lower' in data.slots:
            volume_lower = data.slots['volume_lower'].value
            LOG.debug("volume_lower={}".format(volume_lower))
            self.skill.volume_down(data.site_id, volume_lower)
        else:
            self.skill.volume_down(data.site_id, None)
        data.session_manager.end_session()

    @intent('playPlaylist')
    def play_playlist(self, data):
        playlist_name = data.slots['playlist_name'].value
        shuffle = ('playlist_lecture_mode' in data.slots
                   and data.slots['playlist_lecture_mode'] == 'shuffle')
        self.skill.play_playlist(data.site_id, playlist_name, shuffle=shuffle)
        data.session_manager.end_session()

    @intent('playArtist')
    def play_artist(self, data):
        artist_name = data.slots['artist_name'].value
        self.skill.play_artist(data.site_id, artist_name)
        data.session_manager.end_session()

    @intent('playSong')
    def play_song(self, data):
        self.skill.play_song(data.site_id, data.slots['song_name'])
        data.session_manager.end_session()

    @intent('playAlbum')
    def play_album(self, data):
        album_name = data.slots['album_name'].value
        shuffle = ('album_lecture_mode' in data.slots
                   and data.slots['album_lecture_mode'] == 'shuffle')
        self.skill.play_album(data.site_id, album_name, shuffle=shuffle)
        data.session_manager.end_session()

    @intent('resumeMusic')
    def resume(self, data):
        self.skill.play(data.site_id)
        data.session_manager.end_session()

    @intent('nextSong')
    def next_song(self, data):
        success = self.skill.play_next_item_in_queue(data.site_id)
        if success:
            data.session_manager.end_session()
        else:
            data.session_manager.end_session("There is no next song.")

    @intent('previousSong')
    def prev_song(self, data):
        success = self.skill.play_previous_item_in_queue(data.site_id)
        if success:
            data.session_manager.end_session()
        else:
            data.session_manager.end_session("There is no previous song.")

    @intent('addSong')
    def add_song(self, data):
        self.skill.add_song(data.site_id)
        data.session_manager.end_session()

    @intent('getInfos')
    def get_info(self, data):
        self.skill.set_to_previous_volume(data.site_id)
        data.session_manager.end_session(
            "This is {} by {} on the album {}".format(*self.skill.get_info(data.site_id))
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="Configuration JSON file", default="config.json")
    args = parser.parse_args()
    with open(args.config, 'r') as infile:
        config = json.load(infile)
        listener_args = {
            "mqtt_host": config["mqtt_host"]
        }
        if 'mqtt_port' in config:
            listener_args['mqtt_port'] = int(config['mqtt_port'])
        if 'mopidy_rooms' in config:
            assert isinstance(config['mopidy_rooms'], dict)
            listener_args['mopidy_rooms'] = config['mopidy_rooms']
        listener = SnipsMopidyListener(**listener_args)
        listener.loop_forever()
