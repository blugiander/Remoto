# technician/main.py - Esempio (adattalo al tuo codice reale)
# Supponendo che la riga 203 sia dove hai un numero problematico.

import asyncio
import websockets
import json
import base64
import time
import threading
import sys
import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk

# Assicurati che i tuoi import siano corretti e che i percorsi siano validi
from config import SERVER_HOST, SERVER_PORT, TECHNICIAN_ID
from technician.control import create_command_message # Abbiamo unificato le funzioni di controllo

class TechnicianApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"Tecnico Remoto - ID: {TECHNICIAN_ID}")
        self.geometry("1024x768") # Risoluzione tipica per visualizzazione schermo

        self.websocket = None
        self.is_connected = False
        self.connected_client_pin = None # PIN del client attualmente connesso

        # UI Elements
        self.status_label = ctk.CTkLabel(self, text="Status: Disconnesso", font=("Arial", 16))
        self.status_label.pack(pady=10)

        self.pin_entry_frame = ctk.CTkFrame(self)
        self.pin_entry_frame.pack(pady=10)

        self.pin_label = ctk.CTkLabel(self.pin_entry_frame, text="PIN Cliente:")
        self.pin_label.pack(side="left", padx=5)

        self.pin_entry = ctk.CTkEntry(self.pin_entry_frame, width=150, placeholder_text="Inserisci PIN Cliente")
        self.pin_entry.pack(side="left", padx=5)

        self.connect_button = ctk.CTkButton(self.pin_entry_frame, text="Connetti al Cliente", command=self.connect_to_client)
        self.connect_button.pack(side="left", padx=5)

        self.screen_label = ctk.CTkLabel(self, text="Attendere schermata...", width=800, height=450, fg_color="gray20")
        self.screen_label.pack(pady=10, expand=True, fill="both")

        # Command input
        self.command_frame = ctk.CTkFrame(self)
        self.command_frame.pack(pady=10)

        self.command_entry = ctk.CTkEntry(self.command_frame, placeholder_text="Comando (es. click 100 200)", width=400)
        self.command_entry.pack(side="left", padx=5)

        self.send_button = ctk.CTkButton(self.command_frame, text="Invia Comando", command=self.send_command_from_entry)
        self.send_button.pack(side="left", padx=5)

        # Bind mouse events to the screen_label
        self.screen_label.bind("<Button-1>", self.on_left_click)
        self.screen_label.bind("<Button-3>", self.on_right_click)
        self.screen_label.bind("<Motion>", self.on_mouse_move)
        self.screen_label.bind("<B1-Motion>", self.on_mouse_drag_left) # Mouse drag with left button
        self.screen_label.bind("<B3-Motion>", self.on_mouse_drag_right) # Mouse drag with right button
        self.screen_label.bind("<MouseWheel>", self.on_mouse_scroll) # For Windows/macOS scroll wheel

        # Bind keyboard events to the main window
        self.bind("<Key>", self.on_key_press_global)
        self.bind("<KeyPress>", self.on_key_down_global)
        self.bind("<KeyRelease>", self.on_key_up_global)


        self.bind("<Destroy>", self.on_closing)

    async def connect_to_client(self):
        if self.is_connected:
            print("Già connesso al server.")
            return

        client_pin = self.pin_entry.get()
        if not client_pin:
            self.status_label.configure(text="Errore: Inserisci il PIN del cliente!")
            return

        self.connected_client_pin = client_pin # Store the target PIN

        uri = f"ws://{SERVER_HOST}:{SERVER_PORT}"
        self.status_label.configure(text=f"Status: Connessione a {uri} per PIN {client_pin}...")
        try:
            self.websocket = await websockets.connect(uri)
            print(f"Connesso al server: {uri}")
            self.is_connected = True
            self.status_label.configure(text="Status: Connesso al server!")

            # Invia messaggio di registrazione come tecnico
            registration_message = {
                "type": "register",
                "role": "technician",
                "id": TECHNICIAN_ID,
                "target_pin": self.connected_client_pin # Indica il PIN del client che vuoi controllare
            }
            await self.websocket.send(json.dumps(registration_message))
            print(f"Inviato messaggio di registrazione tecnico: {registration_message}")

            # Avvia il loop di ricezione messaggi (frame e conferme)
            asyncio.create_task(self.receive_messages())

        except Exception as e:
            print(f"Errore di connessione al server: {e}")
            self.status_label.configure(text=f"Status: Errore di connessione - {e}")
            self.is_connected = False

    async def receive_messages(self):
        while self.is_connected:
            try:
                message_json = await self.websocket.recv()
                message = json.loads(message_json)

                # Gestione dei frame dello schermo
                if message.get("type") == "frame" and message.get("sender_id") == self.connected_client_pin:
                    base64_frame = message.get("content")
                    if base64_frame:
                        self.display_screen_frame(base64_frame)
                elif message.get("type") == "status":
                    print(f"Server Status: {message.get('content')}")
                elif message.get("type") == "error":
                    print(f"Server Error: {message.get('content')}")
                else:
                    print(f"Messaggio ricevuto (non frame): {message}")

            except websockets.exceptions.ConnectionClosedOK:
                print("Connessione WebSocket chiusa normalmente.")
                self.is_connected = False
                self.status_label.configure(text="Status: Disconnesso.")
                break
            except websockets.exceptions.ConnectionClosedError as e:
                print(f"Errore di connessione WebSocket: {e}")
                self.is_connected = False
                self.status_label.configure(text=f"Status: Disconnesso - {e}")
                break
            except json.JSONDecodeError:
                print(f"Errore di decodifica JSON: {message_json}")
            except Exception as e:
                print(f"Errore durante la ricezione del messaggio: {e}")
                await asyncio.sleep(1) # Wait a bit before retrying

    def display_screen_frame(self, base64_data):
        try:
            img_bytes = base64.b64decode(base64_data)
            np_arr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if frame is not None:
                # Converti l'immagine da OpenCV (BGR) a PIL (RGB)
                img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img_pil = Image.fromarray(img_rgb)

                # Ridimensiona l'immagine per adattarla alla label mantenendo le proporzioni
                # Ottieni le dimensioni attuali della label per il ridimensionamento dinamico
                label_width = self.screen_label.winfo_width()
                label_height = self.screen_label.winfo_height()

                if label_width == 1 or label_height == 1: # Default values before actual sizing
                    label_width = 800 # Fallback to initial size
                    label_height = 450
                
                # Calcola le nuove dimensioni mantenendo le proporzioni
                img_width, img_height = img_pil.size
                aspect_ratio = img_width / img_height

                if label_width / label_height > aspect_ratio:
                    new_height = label_height
                    new_width = int(new_height * aspect_ratio)
                else:
                    new_width = label_width
                    new_height = int(new_width / aspect_ratio)

                img_pil = img_pil.resize((new_width, new_height), Image.LANCZOS)
                
                # Converti PIL Image in CTkImage
                ctk_img = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=(new_width, new_height))
                
                # Aggiorna la label nel thread principale di Tkinter
                self.screen_label.configure(image=ctk_img)
                self.screen_label.image = ctk_img # Mantieni un riferimento per evitare che venga eliminata

            else:
                print("Errore: Impossibile decodificare il frame dall'array NumPy.")
        except Exception as e:
            print(f"Errore nella visualizzazione del frame: {e}")

    async def send_command(self, command_type: str, data: dict):
        if self.websocket and self.is_connected and self.connected_client_pin:
            message_json = create_command_message(self.connected_client_pin, command_type, data)
            try:
                await self.websocket.send(message_json)
                # print(f"Comando '{command_type}' inviato per PIN {self.connected_client_pin}")
            except Exception as e:
                print(f"Errore nell'invio del comando: {e}")
        else:
            print("Non connesso o PIN cliente non impostato per inviare comandi.")

    def send_command_from_entry(self):
        command_text = self.command_entry.get().strip()
        if not command_text:
            return

        parts = command_text.split(' ')
        command_type = parts[0].lower()
        
        # Simple parsing for demo, expand for robust command handling
        if command_type == 'click' and len(parts) >= 3:
            try:
                x = int(parts[1])
                y = int(parts[2])
                button = parts[3] if len(parts) > 3 else 'left'
                asyncio.create_task(self.send_command('mouse_click', {'x': x, 'y': y, 'button': button}))
            except ValueError:
                print("Formato click: click <x> <y> [button]")
        elif command_type == 'keypress' and len(parts) >= 2:
            key = parts[1]
            asyncio.create_task(self.send_command('key_press', {'key': key}))
        elif command_type == 'move' and len(parts) >= 3:
            try:
                x = int(parts[1])
                y = int(parts[2])
                asyncio.create_task(self.send_command('mouse_move', {'x': x, 'y': y}))
            except ValueError:
                print("Formato move: move <x> <y>")
        elif command_type == 'scroll' and len(parts) >= 2:
            direction = parts[1].lower()
            amount = int(parts[2]) if len(parts) > 2 else 1
            if direction in ['up', 'down']:
                asyncio.create_task(self.send_command('mouse_scroll', {'direction': direction, 'amount': amount}))
            else:
                print("Formato scroll: scroll <up|down> [amount]")
        else:
            print(f"Comando non riconosciuto o malformato: {command_text}")
        
        self.command_entry.delete(0, 'end') # Clear entry

    # Mouse Event Handlers for screen_label
    def on_left_click(self, event):
        # Scale coordinates from label to original frame if necessary, or send as is for now
        # You'll need to implement scaling based on actual image dimensions vs label dimensions
        # For simplicity, sending raw coordinates from the label
        # The client side's pyautogui will click at these coordinates relative to its screen
        x_on_label = event.x
        y_on_label = event.y
        # TODO: Implement proper scaling if client's screen resolution differs from technician's view
        # Example: scale_x = client_screen_width / label_width
        #          scaled_x = x_on_label * scale_x
        asyncio.create_task(self.send_command('mouse_click', {'x': x_on_label, 'y': y_on_label, 'button': 'left'}))
        # print(f"Left Click at ({x_on_label}, {y_on_label})")

    def on_right_click(self, event):
        x_on_label = event.x
        y_on_label = event.y
        asyncio.create_task(self.send_command('mouse_click', {'x': x_on_label, 'y': y_on_label, 'button': 'right'}))
        # print(f"Right Click at ({x_on_label}, {y_on_label})")

    def on_mouse_move(self, event):
        x_on_label = event.x
        y_on_label = event.y
        # print(f"Mouse Move to ({x_on_label}, {y_on_label})")
        asyncio.create_task(self.send_command('mouse_move', {'x': x_on_label, 'y': y_on_label}))

    def on_mouse_drag_left(self, event):
        x_on_label = event.x
        y_on_label = event.y
        asyncio.create_task(self.send_command('mouse_drag', {'x': x_on_label, 'y': y_on_label, 'button': 'left'}))
        # print(f"Left Drag to ({x_on_label}, {y_on_label})")

    def on_mouse_drag_right(self, event):
        x_on_label = event.x
        y_on_label = event.y
        asyncio.create_task(self.send_command('mouse_drag', {'x': x_on_label, 'y': y_on_label, 'button': 'right'}))
        # print(f"Right Drag to ({x_on_label}, {y_on_label})")

    def on_mouse_scroll(self, event):
        # event.delta provides the scroll amount (e.g., 120 for scroll up, -120 for scroll down)
        # Normalize to a simple 'up'/'down' direction with a generic amount
        direction = 'up' if event.delta > 0 else 'down'
        amount = abs(event.delta) // 120 # Convert delta to "clicks" (usually 1 per notch)
        asyncio.create_task(self.send_command('mouse_scroll', {'direction': direction, 'amount': amount}))
        # print(f"Mouse Scroll: {direction} by {amount}")

    # Keyboard Event Handlers
    def on_key_press_global(self, event):
        # This captures a single key press (char for printable, keysym for special)
        # Note: pyautogui.press expects actual key names (e.g., 'enter', 'shift', 'a')
        # event.char might be empty for special keys, event.keysym is more reliable
        key_name = event.keysym.lower() if event.char == '' else event.char
        if key_name:
            asyncio.create_task(self.send_command('key_press', {'key': key_name}))
            # print(f"Key Press: {key_name}")

    def on_key_down_global(self, event):
        # This captures when a key is pressed down
        key_name = event.keysym.lower() if event.char == '' else event.char
        if key_name:
            asyncio.create_task(self.send_command('key_down', {'key': key_name}))
            # print(f"Key Down: {key_name}")

    def on_key_up_global(self, event):
        # This captures when a key is released
        key_name = event.keysym.lower() if event.char == '' else event.char
        if key_name:
            asyncio.create_task(self.send_command('key_up', {'key': key_name}))
            # print(f"Key Up: {key_name}")


    def on_closing(self, event=None):
        print("Applicazione chiusa. Tentativo di disconnessione...")
        if self.websocket:
            asyncio.create_task(self.websocket.close())
        self.destroy()

async def main():
    app = TechnicianApp()
    # Esegui il loop di asyncio in un thread separato
    loop = asyncio.get_event_loop()
    threading.Thread(target=loop.run_forever, daemon=True).start()
    
    # Collega il metodo di connessione al button (sarà chiamato in un task asyncio)
    app.connect_button.configure(command=lambda: asyncio.create_task(app.connect_to_client()))

    app.mainloop()

if __name__ == "__main__":
    # ctk.set_appearance_mode("System")
    # ctk.set_default_color_theme("blue")
    asyncio.run(main())