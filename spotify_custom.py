import re
import logging

import spotipy


class SpotifyCustom(spotipy.Spotify):
    def add_if_unique_tracks(self, playlist_uri, track_ids):
        assert type(playlist_uri) == str
        assert type(track_ids) == list

        try:
            playlist_tracks = []
            offset = 0

            while playlist_temp := self.playlist_items(playlist_uri, offset=offset)['items']:
                playlist_tracks += playlist_temp
                offset += 100
            
        except spotipy.exceptions.SpotifyException:
            logging.exception("Error in getting tracks from playlist ID: " + playlist_uri, exc_info=True)
            return

        playlist_track_ids = set(item['track']['id'] for item in playlist_tracks)
        unique_track_ids = set(id for id in track_ids if id not in playlist_track_ids)
        if unique_track_ids:
            try:
                self.playlist_add_items(playlist_uri, list(unique_track_ids))
            except spotipy.exceptions.SpotifyException:
                logging.exception("Error in adding tracks to playlist ID: " + playlist_uri, exc_info=True)
                return


    def wipe_playlist(self, playlist_uri):
        try:
            while track_ids := [item['track']['id'] for item in self.playlist_tracks(playlist_uri)['items']]:
                self.playlist_remove_all_occurrences_of_items(playlist_uri, track_ids)
        except spotipy.exceptions.SpotifyException:
            logging.exception("Error in wiping playlist: " + playlist_uri, exc_info=True)
            return

    def copy_all_playlist_tracks(self, source_id, dest_id):
        offset = 0
        try:
            while track_ids := [item['track']['id'] for item in self.playlist_tracks(source_id, offset=offset)['items']]:
                self.playlist_add_items(dest_id, track_ids)
                offset += 100
        except spotipy.exceptions.SpotifyException:
            logging.exception("Error in copying tracks from playlist: " + source_id + " to playlist: " + dest_id, exc_info=True)
            return