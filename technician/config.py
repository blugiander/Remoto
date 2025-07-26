# remoto/technician/config.py
import uuid

SERVER_HOST = '188.245.238.160'  # Sostituisci con l'indirizzo IP reale del tuo server Hetzner
SERVER_PORT = 8765               # La porta su cui il server è in ascolto

# Genera un TECHNICIAN_ID unico ogni volta che il file viene importato/eseguito
TECHNICIAN_ID = f'tecnico-{uuid.uuid4()}'

# CLIENT_PIN is NOT hardcoded here. It will be entered by the technician
# through the TechnicianApp's user interface.