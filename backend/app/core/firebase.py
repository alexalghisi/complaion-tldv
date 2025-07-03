"""
Configurazione Firebase
"""

import firebase_admin
from firebase_admin import credentials, firestore, storage
from .config import settings

class FirebaseService:
    """Servizio Firebase singleton"""

    _instance = None
    _db = None
    _bucket = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialize_firebase()
            self._initialized = True

    def _initialize_firebase(self):
        """Inizializza Firebase Admin SDK"""
        try:
            # Usa il file JSON completo delle credenziali
            cred = credentials.Certificate(settings.firebase_credentials_file)

            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred, {
                    'storageBucket': f"{settings.storage_bucket}"
                })

            self._db = firestore.client()
            self._bucket = storage.bucket()

        except Exception as e:
            raise Exception(f"Errore inizializzazione Firebase: {str(e)}")

    @property
    def db(self):
        """Client Firestore"""
        return self._db

    @property
    def bucket(self):
        """Bucket Storage"""
        return self._bucket

# Istanza globale del servizio Firebase
firebase_service = FirebaseService()
