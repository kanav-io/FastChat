import base64
from nacl.public import PrivateKey, PublicKey, Box

class E2E:
    def __init__(self, my_private_key: bytes, db):
        """
        my_private_key: 32-byte X25519 private key
        db:             object with get_public_key(username)->bytes
        """
        self._sk = PrivateKey(my_private_key)
        self._pk = self._sk.public_key
        self._db = db
        self._sessions = {}  # username -> Box

    def export_public_key(self) -> str:
        """Return your long-term public key (Base64) for registration."""
        return base64.b64encode(bytes(self._pk)).decode()

    def init_session(self, user: str):
        """
        Lookup user’s public key, build a Box for that peer.
        Call once (lazily) before encrypt/decrypt.
        """
        if user in self._sessions:
            return
        peer_pk_bytes = self._db.get_public_key(user)
        if not peer_pk_bytes:
            raise ValueError(f"No public key for {user}")
        peer_pk = PublicKey(peer_pk_bytes)
        self._sessions[user] = Box(self._sk, peer_pk)

    def encrypt(self, user: str, plaintext: bytes) -> bytes:
        """
        Encrypt plaintext for `user`. Automatically does the one-time
        DH handshake under the hood.
        """
        self.init_session(user)
        box = self._sessions[user]
        return box.encrypt(plaintext)

    def decrypt(self, user: str, ciphertext: bytes) -> bytes:
        """
        Decrypt ciphertext received from `user`. Must have init_session run
        (will run lazily if you’ve already ever encrypted to them).
        """
        self.init_session(user)
        box = self._sessions[user]
        return box.decrypt(ciphertext)
