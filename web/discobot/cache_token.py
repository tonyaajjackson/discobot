import os
import json

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

RSA_PUBLIC_KEY = serialization.load_pem_public_key(
        os.environb[b"RSA_PUBLIC_KEY"],
        backend=default_backend()
    )

def save_token_to_cache(token, profile):
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
        encrypted_fernet_key = RSA_PUBLIC_KEY.encrypt(
            fernet_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        # Push to database
        profile.spotify_auth_token = encrypted_token
        profile.encrypted_fernet_key = encrypted_fernet_key
        profile.spotify_state = None
        profile.save()

        return None