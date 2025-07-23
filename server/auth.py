import random
import string
from config import PIN_LENGTH

def generate_pin():
    return ''.join(random.choices(string.digits, k=PIN_LENGTH))

class AuthManager:
    def __init__(self):
        self.active_sessions = {}

    def create_session(self, client_id):
        pin = generate_pin()
        self.active_sessions[pin] = client_id
        return pin

    def verify_pin(self, pin):
        return pin in self.active_sessions
