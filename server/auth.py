# server/auth.py

import random
import string
import time
# Non importare Relay qui direttamente, riceverà l'istanza tramite set_relay

class AuthManager:
    def __init__(self):
        self.sessions = {} # pin -> client_id
        self.relay = None # Verrà impostato da set_relay

    def set_relay(self, relay_instance):
        self.relay = relay_instance
        print("AUTH DEBUG: Relay istanza impostata in AuthManager.")

    def create_session(self, client_id):
        pin = ''.join(random.choices(string.digits, k=6))
        self.sessions[pin] = {'client_id': client_id, 'timestamp': time.time()}
        print(f"AUTH DEBUG: Sessione creata: PIN {pin} per client {client_id}.")
        return pin

    def verify_pin(self, pin, technician_id=None):
        session_info = self.sessions.get(pin)
        if session_info:
            client_id = session_info['client_id']
            # Puoi aggiungere una logica di scadenza qui se vuoi
            
            # Se il PIN è valido e c'è un technician_id, crea l'abbinamento
            if technician_id and self.relay: # Assicurati che relay sia stato impostato
                if self.relay.add_pairing(client_id, technician_id):
                    print(f"AUTH DEBUG: PIN {pin} verificato per tecnico {technician_id}. Abbinato a client {client_id}.")
                    del self.sessions[pin] # Rimuovi il PIN dopo l'uso
                    return True
                else:
                    print(f"AUTH DEBUG: Fallito abbinamento con PIN {pin} per tecnico {technician_id}. Client/Tecnico WS non trovati.")
                    return False
            elif not technician_id:
                # Se non c'è technician_id, è solo una verifica generica del PIN (es. per debug o logica futura)
                print(f"AUTH DEBUG: PIN {pin} verificato, ma nessun tecnico per abbinamento.")
                # Non cancellare il PIN qui se non c'è abbinamento
                return True
            else: # relay is None
                print("AUTH DEBUG: Relay non impostato in AuthManager. Impossibile creare abbinamento.")
                return False
        print(f"AUTH DEBUG: PIN {pin} non trovato o non valido.")
        return False