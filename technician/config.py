# config.py
<<<<<<< HEAD
import uuid

SERVER_HOST = '188.245.238.160'  # Replace with your actual server IP address
SERVER_PORT = 8765               # The port your server is listening on

# Generates a unique TECHNICIAN_ID each time the file is imported/executed
TECHNICIAN_ID = f'tecnico-{uuid.uuid4()}' 

# CLIENT_PIN is NOT hardcoded here. It will be entered by the technician
# through the TechnicianApp's user interface.
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
