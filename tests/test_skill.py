from unittest import TestCase
import mock

from snipsmopidy.snipsmopidy import SnipsMopidy
from snipsmopidy.mopidyclient import MopidyClient


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


class TestSkill(TestCase):
    def setUp(self, ):
        self.mopidy = self.init()
        pass

    @mock.patch.object(MopidyClient, 'get_current_track', autospec=True)
    @mock.patch.object(MopidyClient, 'get_volume', autospec=True)
    def init(self, mock_get_volume, mock_current_track):
        track_info = self.create_track_info()

        mock_get_volume.return_value = 50
        mock_current_track.return_value = track_info
        return SnipsMopidy()

    def asserts(self, mock_set_search, mock_play_first, mock_shuffle):
        self.assertTrue(mock_set_search.called)
        self.assertTrue(mock_play_first.called)
        self.assertFalse(mock_shuffle.called)

    @staticmethod
    def create_track_info():
        track_info = AttrDict()
        album = AttrDict()
        artist = AttrDict()
        artist.update({
            'name': 'Mounika'
        })
        album.update({
            'name': 'How Are You',
            'artists': [artist]
        })
        track_info.update({
            'name': 'Cut My Hair',
            'album': album
        })

        return track_info

    @mock.patch.object(MopidyClient, 'get_current_track', autospec=True)
    def test_get_current_track_info(self, mock_current_track):
        mock_current_track.return_value = self.create_track_info()
        assert self.mopidy.get_info()[0], 'Cut My Hair'
        assert self.mopidy.get_info()[1], 'How Are You'
        assert self.mopidy.get_info()[2], 'Mounika'
        self.assertTrue(mock_current_track.called)

    @mock.patch.object(MopidyClient, 'search_track', autospec=True)
    @mock.patch.object(MopidyClient, 'set_search', autospec=True)
    @mock.patch.object(MopidyClient, 'shuffle', autospec=True)
    @mock.patch.object(MopidyClient, 'play_first', autospec=True)
    def test_play_song(self, mock_play_first, mock_shuffle, mock_set_search, mock_search_track):
        mock_set_search.return_value = True

        self.mopidy.play_song('Black and White')
        mock_search_track.assert_called_with(self.mopidy.client, 'Black and White')

        self.asserts(mock_set_search, mock_play_first, mock_shuffle)

    @mock.patch.object(MopidyClient, 'search_album', autospec=True)
    @mock.patch.object(MopidyClient, 'set_search', autospec=True)
    @mock.patch.object(MopidyClient, 'shuffle', autospec=True)
    @mock.patch.object(MopidyClient, 'play_first', autospec=True)
    def test_play_album(self, mock_play_first, mock_shuffle, mock_set_search, mock_search_album):
        mock_set_search.return_value = True

        self.mopidy.play_album('How Are You')
        mock_search_album.assert_called_with(self.mopidy.client, 'How Are You')

        self.asserts(mock_set_search, mock_play_first, mock_shuffle)

    @mock.patch.object(MopidyClient, 'search_artist', autospec=True)
    @mock.patch.object(MopidyClient, 'set_search', autospec=True)
    @mock.patch.object(MopidyClient, 'shuffle', autospec=True)
    @mock.patch.object(MopidyClient, 'play_first', autospec=True)
    def test_play_artist(self, mock_play_first, mock_shuffle, mock_set_search, mock_search_artist):
        mock_set_search.return_value = True

        self.mopidy.play_artist('Kendrick Lamar')
        mock_search_artist.assert_called_with(self.mopidy.client, 'Kendrick Lamar')

        self.asserts(mock_set_search, mock_play_first, mock_shuffle)

    @mock.patch.object(MopidyClient, 'search_playlist', autospec=True)
    @mock.patch.object(MopidyClient, 'set_playlist', autospec=True)
    @mock.patch.object(MopidyClient, 'shuffle', autospec=True)
    @mock.patch.object(MopidyClient, 'play_first', autospec=True)
    def test_play_playlist(self, mock_play_first, mock_shuffle, mock_set_playlist, mock_search_playlist):
        mock_set_playlist.return_value = True

        self.mopidy.play_playlist('Summer Vibes')
        mock_search_playlist.assert_called_with(self.mopidy.client, 'Summer Vibes')

        self.asserts(mock_search_playlist, mock_play_first, mock_shuffle)

    @mock.patch.object(MopidyClient, 'search_genre', autospec=True)
    @mock.patch.object(MopidyClient, 'set_search', autospec=True)
    @mock.patch.object(MopidyClient, 'shuffle', autospec=True)
    @mock.patch.object(MopidyClient, 'play_first', autospec=True)
    def test_play_genre(self, mock_play_first, mock_shuffle, mock_set_search, mock_search_genre):
        mock_set_search.return_value = True

        self.mopidy.play_genre('Jazz')
        mock_search_genre.assert_called_with(self.mopidy.client, 'Jazz')

        self.asserts(mock_set_search, mock_play_first, mock_shuffle)
