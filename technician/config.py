# config.py
import uuid

SERVER_HOST = '188.245.238.160'  # Replace with your actual server IP address
SERVER_PORT = 8765               # The port your server is listening on

# Generates a unique TECHNICIAN_ID each time the file is imported/executed
TECHNICIAN_ID = f'tecnico-{uuid.uuid4()}' 

# CLIENT_PIN is NOT hardcoded here. It will be entered by the technician
# through the TechnicianApp's user interface.