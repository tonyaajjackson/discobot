import re
import logging
import json

import spotipy
from spotipy import CacheHandler

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

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


class MongoCacheHandler(CacheHandler):
    def __init__(self,
                 client,
                 username,
                 private_key,
                 public_key):
        self.username = username
        self.client = client
        self.private_key = private_key
        self.public_key = public_key

    def get_cached_token(self):
        user = self.client.discobot.users.find_one({"username": self.username})
        encrypted_token = user['spotify_auth_token']

        if encrypted_token is None:
            # No cached token
            return None
                
        encrypted_fernet_key = user['encrypted_fernet_key']

        # Decrypt Fernet key using RSA private key
        fernet_key = self.private_key.decrypt(
            encrypted_fernet_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        # Decrypt token using fernet key
        f = Fernet(fernet_key)
        decrypted_token = f.decrypt(encrypted_token)
        
        return json.loads(decrypted_token)        

    def save_token_to_cache(self, token):
        # NOTE: RSA cannot encrypt content larger than the RSA key. The approach
        # listed to solve this problem is to create a symmetric key, use the
        # symmetric key to encrypt the data, then encrypt the symmetric key with
        # the RSA public key and send the encrypted data and encrypted symmetric 
        # key together to the recipient.
        # https://stackoverflow.com/questions/1199058/how-to-use-rsa-to-encrypt-files-huge-data-in-c-sharp
        
        # Make symmetric Fernet key
        fernet_key = Fernet.generate_key()
        f = Fernet(fernet_key)

        # Enecypt token with Fernet key
        raw_token = json.dumps(token).encode()
        encrypted_token = f.encrypt(raw_token)

        # Encrypt Fernet key with RSA public key
        encrypted_fernet_key = self.public_key.encrypt(
            fernet_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        # Push to MongoDB
        self.client.discobot.users.update_one(
            {
                "username": self.username
            },
            {
                "$set": 
                    {
                        "spotify_auth_token": encrypted_token,
                        "encrypted_fernet_key": encrypted_fernet_key
                    }
            }
        )

        return None