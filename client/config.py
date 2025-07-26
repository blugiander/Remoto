# remoto/client/config.py

# Indirizzo IP e porta del server WebSocket
# Se il server è sulla stessa macchina (o LAN), puoi usare l'IP locale (es. '127.0.0.1' o '192.168.1.X')
# Se il server è su Hetzner, usa il suo IP pubblico.
SERVER_HOST = '188.245.238.160' # Sostituisci con l'indirizzo IP reale del tuo server Hetzner
SERVER_PORT = 8765               # La porta su cui il server è in ascolto

# Prefisso per l'ID del client (il PIN sarà generato a runtime)
CLIENT_ID_PREFIX = 'client'