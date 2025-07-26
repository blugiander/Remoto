# config.py

<<<<<<< HEAD
SERVER_HOST = "188.245.238.160" # O "0.0.0.0" sul server stesso se è in ascolto su tutte le interfacce
SERVER_PORT = 8765 # Questa sarà l'unica porta usata per entrambi
CLIENT_ID = "cliente-001"
# Rimuovi SERVER_PORT_TECHNICIAN se esisteva
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
>>>>>>> eca790dbd18d1d079932fc777f4b03728e90bf58
