# config.py
import uuid

SERVER_HOST = '188.245.238.160'  # Sostituisci con l'indirizzo IP del tuo server
SERVER_PORT = 8765               # La porta su cui il server è in ascolto

# Genera un CLIENT_ID unico ogni volta che il file viene importato/eseguito
CLIENT_ID = f'cliente-{uuid.uuid4()}'