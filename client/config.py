# config.py
<<<<<<< HEAD
import uuid

SERVER_HOST = '188.245.238.160'  # Sostituisci con l'indirizzo IP del tuo server
SERVER_PORT = 8765               # La porta su cui il server è in ascolto

# Genera un CLIENT_ID unico ogni volta che il file viene importato/eseguito
CLIENT_ID = f'cliente-{uuid.uuid4()}'
=======

# Configurazione del Server
SERVER_HOST = "188.245.238.160"  # L'IP pubblico del tuo server Hetzner
SERVER_PORT = 8765               # Porta per le connessioni WebSocket

# Configurazione del Client
CLIENT_ID = "cliente-001"        # Identificativo unico per questo client

# Configurazione del Tecnico
# TECH_ID non è più strettamente necessario per la connessione al server,
# ma utile per identificazione interna se necessaria in futuro.
# TECH_ID = "tecnico-001"
>>>>>>> 413ff6f04e84f437222564744ceed3974a03307d
