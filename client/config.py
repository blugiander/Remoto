# client/config.py
import uuid

SERVER_HOST = '188.245.238.160'  # Sostituisci con l'indirizzo IP del tuo server
SERVER_PORT = 8765               # La porta su cui il server è in ascolto

# Genera un CLIENT_ID unico ogni volta che il file viene importato/eseguito
CLIENT_ID = f'cliente-{uuid.uuid4()}'

# Il PIN del client viene generato dinamicamente per ogni sessione
# Non deve iniziare con '0' se contiene cifre non ottali (8, 9)
# Assicurati che sia una stringa se vuoi mantenerlo flessibile
# Se vuoi un PIN numerico, puoi semplicemente usare int(random.randint(100000, 999999))
# Ma per il tuo caso, una stringa è più sicura per evitare interpretazioni numeriche
# Il tuo errore probabilmente era qui se avevi un numero come 0922273
CLIENT_PIN = str(uuid.uuid4().int % 1000000).zfill(6) # Genera un PIN di 6 cifre come stringa