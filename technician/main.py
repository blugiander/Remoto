# remoto/technician/main.py

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
import numpy as np
import cv2
import logging

# Configurazione del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Assicurati che i tuoi import siano corretti e che i percorsi siano validi
# NOTA: Se config.py è nella radice del progetto, non in technician/, allora sarebbe 'from config import ...'
# Ma dalle tue screenshot, sembra che sia in technician/.
from .config import SERVER_HOST, SERVER_PORT, TECHNICIAN_ID
from .control import create_command_message # Usare .control per import relativo

class TechnicianApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"Tecnico Remoto - ID: {TECHNICIAN_ID}")
        self.geometry("1024x768")

        self.websocket = None
        self.is_connected = False
        self.connected_client_pin = None

        # UI Elements
        self.status_label = ctk.CTkLabel(self, text="Status: Disconnesso", font=("Arial", 16))
        self.status_label.pack(pady=10)

        self.pin_entry_frame = ctk.CTkFrame(self)
        self.pin_entry_frame.pack(pady=10)

        self.pin_label = ctk.CTkLabel(self.pin_entry_frame, text="PIN Cliente:")
        self.pin_label.pack(side="left", padx=5)

        self.pin_entry = ctk.CTkEntry(self.pin_entry_frame, width=150, placeholder_text="Inserisci PIN Cliente")
        self.pin_entry.pack(side="left", padx=5)

        # Il comando del bottone chiama un wrapper per gestire async/sync
        self.connect_button = ctk.CTkButton(self.pin_entry_frame, text="Connetti al Cliente", command=self.connect_to_client_async_wrapper)
        self.connect_button.pack(side="left", padx=5)

        # Inizializza con dimensioni di fallback che CustomTkinter userà se non è ancora impacchettato
        # Queste dimensioni iniziali sono importanti per evitare un "label_width/height = 1" iniziale
        self.screen_label = ctk.CTkLabel(self, text="Attendere schermata...", width=800, height=600, fg_color="gray20")
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
        self.screen_label.bind("<B1-Motion>", self.on_mouse_drag_left)
        self.screen_label.bind("<B3-Motion>", self.on_mouse_drag_right)
        self.screen_label.bind("<MouseWheel>", self.on_mouse_scroll)

        # Bind keyboard events to the main window
        self.bind("<Key>", self.on_key_press_global)
        self.bind("<KeyPress>", self.on_key_down_global)
        self.bind("<KeyRelease>", self.on_key_up_global)

        self.bind("<Destroy>", self.on_closing)

        # Store the size of the last received original frame (width, height)
        # Inizializza con dimensioni placeholder per evitare divisione per zero o errori di proporzione all'avvio
        self.current_frame_size = (1280, 1024) # Imposta una dimensione di default sensata, eguaglia la dimensione dell'errore

    def connect_to_client_async_wrapper(self):
        """Wrapper per chiamare connect_to_client che è una coroutine."""
        asyncio.create_task(self.connect_to_client())

    async def connect_to_client(self):
        if self.is_connected:
            logging.info("Già connesso al server.")
            return

        client_pin = self.pin_entry.get()
        if not client_pin:
            self.status_label.configure(text="Errore: Inserisci il PIN del cliente!")
            return

        self.connected_client_pin = client_pin

        uri = f"ws://{SERVER_HOST}:{SERVER_PORT}"
        self.status_label.configure(text=f"Status: Connessione a {uri} per PIN {client_pin}...")
        try:
            self.websocket = await websockets.connect(uri)
            logging.info(f"Connesso al server: {uri}")
            self.is_connected = True
            self.status_label.configure(text="Status: Connesso al server!")

            # Invia messaggio di registrazione come tecnico
            registration_message = {
                "type": "register",
                "role": "technician",
                "id": TECHNICIAN_ID,
                "pin": self.connected_client_pin # Indica il PIN del client che vuoi controllare
            }
            await self.websocket.send(json.dumps(registration_message))
            logging.info(f"Inviato messaggio di registrazione tecnico: {registration_message}")

            # Avvia il loop di ricezione messaggi (frame e conferme)
            asyncio.create_task(self.receive_messages())

        except Exception as e:
            logging.error(f"Errore di connessione al server: {e}")
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
                        # Schedule display_screen_frame to run in the Tkinter main loop
                        self.after(0, self.display_screen_frame, base64_frame)
                elif message.get("type") == "status":
                    logging.info(f"Server Status: {message.get('message')}")
                    self.status_label.configure(text=f"Status: {message.get('message')}")
                elif message.get("type") == "notification":
                    logging.info(f"Server Notification: {message.get('message')}")
                    self.status_label.configure(text=f"Status: {message.get('message')}")
                    if "disconnesso" in message.get('message', '').lower() and self.is_connected:
                        logging.warning("Il client si è disconnesso o il server ha chiuso la connessione.")
                        self.is_connected = False
                        if self.websocket and not self.websocket.closed:
                            await self.websocket.close() # Chiudi esplicitamente il websocket
                        self.status_label.configure(text="Status: Client disconnesso. Riconnetti.")
                elif message.get("type") == "error":
                    logging.error(f"Server Error: {message.get('message')}")
                    self.status_label.configure(text=f"Status: Errore - {message.get('message')}")
                else:
                    logging.debug(f"Messaggio ricevuto (non frame): {message}")

            except websockets.exceptions.ConnectionClosedOK:
                logging.info("Connessione WebSocket chiusa normalmente.")
                self.is_connected = False
                self.status_label.configure(text="Status: Disconnesso.")
                break
            except websockets.exceptions.ConnectionClosedError as e:
                logging.error(f"Errore di connessione WebSocket: {e}")
                self.is_connected = False
                self.status_label.configure(text=f"Status: Disconnesso - {e}")
                break
            except json.JSONDecodeError as e:
                logging.error(f"Errore di decodifica JSON: {e} - Messaggio: {message_json[:200]}...")
            except Exception as e:
                logging.error(f"Errore durante la ricezione del messaggio: {e}", exc_info=True)
                await asyncio.sleep(1) # Wait a bit before retrying

    def display_screen_frame(self, base64_data):
        try:
            img_bytes = base64.b64decode(base64_data)
            np_arr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR) # Decodifica in BGR (3 canali)

            if frame is not None:
                # Controlla la forma del frame decodificato. Se ha 4 canali per qualche motivo, converti.
                # cv2.imdecode(..., cv2.IMREAD_COLOR) dovrebbe dare 3 canali.
                if len(frame.shape) == 3 and frame.shape[2] == 4:
                    logging.warning(f"Frame ricevuto con 4 canali (BGRA), convertendo in BGR: {frame.shape}")
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                elif len(frame.shape) == 3 and frame.shape[2] == 3:
                    # Questo è il caso atteso (BGR)
                    pass
                else:
                    logging.error(f"Formato frame inatteso dopo decodifica: {frame.shape}")
                    return

                # Store the original frame dimensions for scaling calculations
                # Usa shape[1] per la larghezza e shape[0] per l'altezza
                self.current_frame_size = (frame.shape[1], frame.shape[0]) 

                # Converti l'immagine da OpenCV (BGR) a PIL (RGB)
                # Assicurati che sia RGB (3 canali) per Pillow
                img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img_pil = Image.fromarray(img_rgb)
                
                # Ulteriore controllo per assicurarsi che Pillow riceva un'immagine RGB (3 canali)
                if img_pil.mode == 'RGBA':
                    logging.warning("PIL Image è in RGBA, convertendo in RGB per CustomTkinter.")
                    img_pil = img_pil.convert('RGB')


                label_width = self.screen_label.winfo_width()
                label_height = self.screen_label.winfo_height()

                # Fallback a dimensioni predefinite se la label non è ancora stata completamente renderizzata
                # Questo evita che label_width/height siano 1 o 0 all'inizio
                if label_width < 100 or label_height < 100: # Usare soglie ragionevoli invece di 1
                    label_width = self.screen_label.cget("width") # Ottieni le dimensioni iniziali impostate per la label
                    label_height = self.screen_label.cget("height")
                    if label_width < 100 or label_height < 100: # Se anche cget non dà dimensioni valide (es. prima di pack)
                        label_width = 800 # Fallback a valori hardcoded, devono corrispondere all'inizializzazione del widget
                        label_height = 600

                img_width, img_height = img_pil.size
                
                # Evita divisioni per zero se l'immagine è vuota o malformata
                if img_width == 0 or img_height == 0:
                    logging.error("L'immagine decodificata ha dimensioni zero, impossibile visualizzare.")
                    return

                aspect_ratio = img_width / img_height

                # Calculate new dimensions to fit label while maintaining aspect ratio
                if label_width / label_height > aspect_ratio:
                    new_height = label_height
                    new_width = int(new_height * aspect_ratio)
                else:
                    new_width = label_width
                    new_height = int(new_width / aspect_ratio)

                # Ensure dimensions are at least 1 to avoid errors
                new_width = max(1, new_width)
                new_height = max(1, new_height)

                img_pil = img_pil.resize((new_width, new_height), Image.LANCZOS)

                ctk_img = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=(new_width, new_height))

                self.screen_label.configure(image=ctk_img)
                self.screen_label.image = ctk_img # Keep a reference!

            else:
                logging.error("Errore: Impossibile decodificare il frame dall'array NumPy (frame is None).")
        except Exception as e:
            logging.error(f"Errore nella visualizzazione del frame: {e}", exc_info=True)

    async def send_command(self, command_type: str, data: dict):
        if self.websocket and self.is_connected and self.connected_client_pin:
            # Scale coordinates if it's a mouse command
            if command_type in ['mouse_click', 'mouse_move', 'mouse_drag']:
                x_on_label = data.get('x')
                y_on_label = data.get('y')

                if x_on_label is not None and y_on_label is not None:
                    label_width = self.screen_label.winfo_width()
                    label_height = self.screen_label.winfo_height()
                    frame_width, frame_height = self.current_frame_size

                    # Usa le dimensioni di fallback iniziali per la label se non sono ancora reali
                    if label_width < 100 or label_height < 100:
                        label_width = self.screen_label.cget("width")
                        label_height = self.screen_label.cget("height")
                        if label_width < 100 or label_height < 100:
                            label_width = 800
                            label_height = 600

                    if label_width > 1 and label_height > 1 and frame_width > 0 and frame_height > 0:
                        # Calculate the actual displayed image dimensions within the label
                        aspect_ratio = frame_width / frame_height
                        if label_width / label_height > aspect_ratio:
                            displayed_height = label_height
                            displayed_width = int(displayed_height * aspect_ratio)
                        else:
                            displayed_width = label_width
                            displayed_height = int(displayed_width / aspect_ratio)

                        # Calculate offset if the image is centered within the label
                        offset_x = (label_width - displayed_width) / 2
                        offset_y = (label_height - displayed_height) / 2

                        # Convert coordinates from label space to displayed image space
                        x_on_image = x_on_label - offset_x
                        y_on_image = y_on_label - offset_y

                        # Scale coordinates to the original frame resolution
                        if displayed_width > 0 and displayed_height > 0:
                            data['x'] = int(x_on_image * (frame_width / displayed_width))
                            data['y'] = int(y_on_image * (frame_height / displayed_height))
                            # logging.debug(f"Scaled ({x_on_label}, {y_on_label}) to ({data['x']}, {data['y']})")
                        else:
                            logging.warning("Displayed image dimensions are zero, cannot scale coordinates.")
                    else:
                        logging.warning("Label or frame dimensions not available for scaling, sending raw coordinates.")
                else:
                    logging.warning(f"Coordinate X o Y mancanti per il comando {command_type}.")

            message_json = create_command_message(self.connected_client_pin, command_type, data)
            try:
                await self.websocket.send(message_json)
            except Exception as e:
                logging.error(f"Errore nell'invio del comando '{command_type}': {e}")
        else:
            logging.warning("Non connesso o PIN cliente non impostato per inviare comandi.")

    def send_command_from_entry(self):
        """Prende il comando dall'input testuale e lo invia."""
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
                # Note: These are raw coordinates, scaling will happen in send_command
                asyncio.create_task(self.send_command('mouse_click', {'x': x, 'y': y, 'button': button}))
            except ValueError:
                logging.warning("Formato click: click <x> <y> [button]")
        elif command_type == 'keypress' and len(parts) >= 2:
            key = parts[1]
            asyncio.create_task(self.send_command('key_press', {'key': key}))
        elif command_type == 'move' and len(parts) >= 3:
            try:
                x = int(parts[1])
                y = int(parts[2])
                # Note: These are raw coordinates, scaling will happen in send_command
                asyncio.create_task(self.send_command('mouse_move', {'x': x, 'y': y}))
            except ValueError:
                logging.warning("Formato move: move <x> <y>")
        elif command_type == 'scroll' and len(parts) >= 2:
            direction = parts[1].lower()
            amount = int(parts[2]) if len(parts) > 2 else 1
            if direction in ['up', 'down']:
                asyncio.create_task(self.send_command('mouse_scroll', {'direction': direction, 'amount': amount}))
            else:
                logging.warning("Formato scroll: scroll <up|down> [amount]")
        else:
            logging.warning(f"Comando non riconosciuto o malformato: {command_text}")

        self.command_entry.delete(0, 'end') # Clear entry

    # Mouse Event Handlers for screen_label - pass event.x/y directly, scaling happens in send_command
    def on_left_click(self, event):
        asyncio.create_task(self.send_command('mouse_click', {'x': event.x, 'y': event.y, 'button': 'left'}))

    def on_right_click(self, event):
        asyncio.create_task(self.send_command('mouse_click', {'x': event.x, 'y': event.y, 'button': 'right'}))

    def on_mouse_move(self, event):
        asyncio.create_task(self.send_command('mouse_move', {'x': event.x, 'y': event.y}))

    def on_mouse_drag_left(self, event):
        asyncio.create_task(self.send_command('mouse_drag', {'x': event.x, 'y': event.y, 'button': 'left'}))

    def on_mouse_drag_right(self, event):
        asyncio.create_task(self.send_command('mouse_drag', {'x': event.x, 'y': event.y, 'button': 'right'}))

    def on_mouse_scroll(self, event):
        direction = 'up' if event.delta > 0 else 'down'
        amount = abs(event.delta) // 120 # Standard delta for one scroll "click" is 120
        asyncio.create_task(self.send_command('mouse_scroll', {'direction': direction, 'amount': amount}))

    # Keyboard Event Handlers
    def on_key_press_global(self, event):
        # event.char might be empty for special keys, event.keysym is more reliable
        key_name = event.keysym.lower() if event.char == '' else event.char
        if key_name:
            asyncio.create_task(self.send_command('key_press', {'key': key_name}))

    def on_key_down_global(self, event):
        key_name = event.keysym.lower() if event.char == '' else event.char
        if key_name:
            asyncio.create_task(self.send_command('key_down', {'key': key_name}))

    def on_key_up_global(self, event):
        key_name = event.keysym.lower() if event.char == '' else event.char
        if key_name:
            asyncio.create_task(self.send_command('key_up', {'key': key_name}))

    def on_closing(self, event=None):
        logging.info("Applicazione chiusa. Tentativo di disconnessione...")
        if self.websocket and self.is_connected:
            asyncio.create_task(self.websocket.close()) # Chiudi la connessione WebSocket
        self.destroy()

async def main():
    app = TechnicianApp()
    # Esegui il loop di asyncio in un thread separato
    # Questo è fondamentale perché CustomTkinter ha il suo mainloop bloccante.
    loop = asyncio.get_event_loop()
    threading.Thread(target=loop.run_forever, daemon=True).start()

    app.mainloop()

if __name__ == "__main__":
    # ctk.set_appearance_mode("System") # Themes can be set here if desired
    # ctk.set_default_color_theme("blue")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Tecnico interrotto da tastiera.")
    except Exception as e:
        logging.critical(f"Errore irreversibile durante l'avvio o l'esecuzione del tecnico: {e}", exc_info=True)