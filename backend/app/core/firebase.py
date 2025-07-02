"""
Configurazione Firebase
"""

import json
from typing import Dict, Any
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
            # Crea le credenziali dal service account
            cred_dict = {
                "type": "service_account",
                "project_id": settings.firebase_project_id,
                "private_key": settings.firebase_private_key.replace('\\n', '\n'),
                "client_email": settings.firebase_client_email,
            }

            cred = credentials.Certificate(cred_dict)

            # Inizializza l'app se non già fatto
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred, {
                    'storageBucket': f"{settings.firebase_project_id}.appspot.com"
                })

            # Inizializza i servizi
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