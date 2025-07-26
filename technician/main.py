# technician/main.py

import asyncio
import websockets
import json
import base64
import cv2
import numpy as np
import customtkinter as ctk
from PIL import Image, ImageTk
import io
<<<<<<< HEAD
import threading # Per lo scroll (anche se ora lo gestiamo diversamente)
import sys # Per sys.exit()

# Importa dalla tua config.py (assicurati che config.py esista nella stessa directory)
# Esempio di config.py:
# SERVER_HOST = "188.245.238.160"
# SERVER_PORT = 8765
from config import SERVER_HOST, SERVER_PORT

# Variabili globali per la gestione della connessione e dell'interfaccia
websocket_connection = None
screen_frame_queue = asyncio.Queue(maxsize=1) # Coda per i frame dello schermo
current_client_pin = None
screen_label = None # Riferimento al widget label dell'immagine (assegnato nella classe)

# Inizializzazione CustomTkinter
ctk.set_appearance_mode("System")  # Modes: "System" (default), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (default), "green", "dark-blue"

class TechnicianApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Tecnico - Controllo Remoto")
        self.geometry("1024x768")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Frame Superiore per input PIN e stato
        self.top_frame = ctk.CTkFrame(self, corner_radius=0)
        self.top_frame.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)
        self.top_frame.grid_columnconfigure(0, weight=0)
        self.top_frame.grid_columnconfigure(1, weight=1)
        self.top_frame.grid_columnconfigure(2, weight=0)
        self.top_frame.grid_columnconfigure(3, weight=0)

        self.pin_label = ctk.CTkLabel(self.top_frame, text="Inserisci PIN Cliente:", font=("Arial", 16))
        self.pin_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.pin_entry = ctk.CTkEntry(self.top_frame, width=150, font=("Arial", 16))
        self.pin_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.pin_entry.bind("<Return>", self.connect_button_callback) # Permette di connettersi premendo Invio

        self.connect_button = ctk.CTkButton(self.top_frame, text="Connetti", command=self.connect_button_callback, font=("Arial", 16))
        self.connect_button.grid(row=0, column=2, padx=10, pady=10, sticky="e")

        self.status_label = ctk.CTkLabel(self.top_frame, text="Stato: Disconnesso", text_color="red", font=("Arial", 16))
        self.status_label.grid(row=0, column=3, padx=10, pady=10, sticky="e")

        # Frame Principale per lo schermo del client
        self.screen_frame = ctk.CTkFrame(self, corner_radius=0)
        self.screen_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.screen_frame.grid_rowconfigure(0, weight=1)
        self.screen_frame.grid_columnconfigure(0, weight=1)

        # Etichetta per visualizzare lo schermo (inizialmente vuota)
        global screen_label # Riferimento alla variabile globale
        self.screen_label = ctk.CTkLabel(self.screen_frame, text="")
        self.screen_label.grid(row=0, column=0, sticky="nsew")
        screen_label = self.screen_label # Assegna alla variabile globale

        # Variabili per memorizzare le dimensioni originali del client
        self.client_screen_width = 0
        self.client_screen_height = 0

        # Bind eventi mouse e tastiera sullo screen_label
        self.screen_label.bind("<Button-1>", self.on_mouse_click) # Click sinistro
        self.screen_label.bind("<Button-2>", self.on_mouse_click) # Click centrale
        self.screen_label.bind("<Button-3>", self.on_mouse_click) # Click destro
        self.screen_label.bind("<Motion>", self.on_mouse_move) # Movimento mouse
        self.screen_label.bind("<MouseWheel>", self.on_mouse_scroll) # Scroll mouse (Windows/macOS)
        
        # Bind tastiera a livello di finestra root per catturare tutti i tasti
        self.bind_all("<KeyPress>", self.on_key_down)
        self.bind_all("<KeyRelease>", self.on_key_up)

        self.loop = asyncio.get_event_loop()
        self.connection_task = None
        self.display_task = None
        self.receive_task = None

        self.protocol("WM_DELETE_WINDOW", self.on_closing) # Gestione chiusura finestra

        # Set di tasti attualmente premuti per gestire key_press e key_release
        self._pressed_keys = set()
        self._last_mouse_pos = (0, 0) # Per ottimizzare l'invio di eventi mouse_move


    def update_status(self, text, color="black"):
        self.status_label.configure(text=text, text_color=color)

    async def connect_to_server(self):
        global websocket_connection, current_client_pin
        current_client_pin = self.pin_entry.get()
        if not current_client_pin:
            self.update_status("Errore: Inserisci un PIN.", "orange")
            return

        uri = f"ws://{SERVER_HOST}:{SERVER_PORT}"
        self.update_status(f"Connessione a {uri}...", "blue")
        self.connect_button.configure(state="disabled", text="Connesso")

=======
import threading # Per lo scroll
from config import SERVER_HOST, SERVER_PORT # Importa dalla tua config.py

# Variabili globali per la gestione della connessione e dell'interfaccia
websocket_connection = None
screen_frame_queue = asyncio.Queue(maxsize=1) # Coda per i frame dello schermo
current_client_pin = None
screen_label = None # Riferimento al widget label dell'immagine

# Inizializzazione CustomTkinter
ctk.set_appearance_mode("System")  # Modes: "System" (default), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (default), "green", "dark-blue"

class TechnicianApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Tecnico - Controllo Remoto")
        self.geometry("1024x768")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Frame Superiore per input PIN e stato
        self.top_frame = ctk.CTkFrame(self, corner_radius=0)
        self.top_frame.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)
        self.top_frame.grid_columnconfigure(0, weight=0)
        self.top_frame.grid_columnconfigure(1, weight=1)
        self.top_frame.grid_columnconfigure(2, weight=0)
        self.top_frame.grid_columnconfigure(3, weight=0)

        self.pin_label = ctk.CTkLabel(self.top_frame, text="Inserisci PIN Cliente:", font=("Arial", 16))
        self.pin_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.pin_entry = ctk.CTkEntry(self.top_frame, width=150, font=("Arial", 16))
        self.pin_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.pin_entry.bind("<Return>", self.connect_button_callback) # Permette di connettersi premendo Invio

        self.connect_button = ctk.CTkButton(self.top_frame, text="Connetti", command=self.connect_button_callback, font=("Arial", 16))
        self.connect_button.grid(row=0, column=2, padx=10, pady=10, sticky="e")

        self.status_label = ctk.CTkLabel(self.top_frame, text="Stato: Disconnesso", text_color="red", font=("Arial", 16))
        self.status_label.grid(row=0, column=3, padx=10, pady=10, sticky="e")

        # Frame Principale per lo schermo del client
        self.screen_frame = ctk.CTkFrame(self, corner_radius=0)
        self.screen_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.screen_frame.grid_rowconfigure(0, weight=1)
        self.screen_frame.grid_columnconfigure(0, weight=1)

        # Etichetta per visualizzare lo schermo (inizialmente vuota)
        global screen_label
        self.screen_label = ctk.CTkLabel(self.screen_frame, text="")
        self.screen_label.grid(row=0, column=0, sticky="nsew")
        screen_label = self.screen_label # Assegna alla variabile globale

        # Bind eventi mouse e tastiera sullo screen_label
        self.screen_label.bind("<Button-1>", self.on_mouse_click) # Click sinistro
        self.screen_label.bind("<Button-2>", self.on_mouse_click) # Click centrale
        self.screen_label.bind("<Button-3>", self.on_mouse_click) # Click destro
        self.screen_label.bind("<Motion>", self.on_mouse_move) # Movimento mouse
        self.screen_label.bind("<MouseWheel>", self.on_mouse_scroll) # Scroll mouse (Windows/macOS)
        self.bind_all("<Key>", self.on_key_press) # Cattura tutti i tasti premuti
        self.bind_all("<KeyPress>", self.on_key_down) # Per gestione tasti press/release (se necessario)
        self.bind_all("<KeyRelease>", self.on_key_up) # Per gestione tasti press/release (se necessario)


        self.loop = asyncio.get_event_loop()
        self.connection_task = None
        self.display_task = None
        self.receive_task = None

        self.protocol("WM_DELETE_WINDOW", self.on_closing) # Gestione chiusura finestra

    def update_status(self, text, color="black"):
        self.status_label.configure(text=text, text_color=color)

    async def connect_to_server(self):
        global websocket_connection, current_client_pin
        current_client_pin = self.pin_entry.get()
        if not current_client_pin:
            self.update_status("Errore: Inserisci un PIN.", "orange")
            return

        uri = f"ws://{SERVER_HOST}:{SERVER_PORT}"
        self.update_status(f"Connessione a {uri}...", "blue")
        self.connect_button.configure(state="disabled", text="Connesso")

>>>>>>> 413ff6f04e84f437222564744ceed3974a03307d
        try:
            websocket_connection = await websockets.connect(uri, ping_interval=20, ping_timeout=10)
            print("✅ TECNICO: Connesso al server.")
            self.update_status("Connesso al server. Registrazione...", "green")

            registration_message = json.dumps({
                "type": "register",
                "role": "technician",
                "id": f"tecnico-{int(time.time())}", # ID unico basato sul timestamp
                "pin": current_client_pin
            })
            await websocket_connection.send(registration_message)
            print(f"📝 TECNICO: Inviato messaggio di registrazione (PIN: {current_client_pin}).")

            registration_response_str = await websocket_connection.recv()
            registration_response = json.loads(registration_response_str)

            if registration_response.get("status") == "registered":
                self.update_status(f"Registrazione completata! {registration_response.get('message', '')}", "green")
                print("✅ TECNICO: Registrazione al server completata.")
                
                # Avvia i task per la ricezione e la visualizzazione dello schermo
                self.receive_task = asyncio.create_task(self.receive_messages())
                self.display_task = asyncio.create_task(self.display_screen_frames())
<<<<<<< HEAD

                # Attendi che uno dei task (receive o display) si completi (es. per disconnessione)
                done, pending = await asyncio.wait([self.receive_task, self.display_task], return_when=asyncio.FIRST_COMPLETED)
                
                # Logga eventuali eccezioni dai task completati
                for task in done:
                    if task.exception():
                        print(f"ERRORE TECNICO: Un task parallelo è terminato con un'eccezione: {task.exception()}")
                
                # Cancella i task che sono ancora in esecuzione
                for task in pending:
                    task.cancel()
                    try:
                        await task # Attende che il task cancellato si fermi pulitamente
                    except asyncio.CancelledError:
                        print(f"TECNICO: Task {task.get_name() if hasattr(task, 'get_name') else ''} è stato cancellato.")

                print(f"TECNICO: Sessione WebSocket per PIN {current_client_pin} terminata. Riconnessione...")
=======

                # Keep connection alive until closed (or an error occurs)
                await asyncio.gather(self.receive_task, self.display_task)
>>>>>>> 413ff6f04e84f437222564744ceed3974a03307d

            else:
                error_msg = registration_response.get("message", "Registrazione fallita.")
                self.update_status(f"Errore registrazione: {error_msg}", "red")
                print(f"ERRORE TECNICO: Registrazione fallita: {error_msg}")
                await websocket_connection.close() # Chiudi la connessione
                websocket_connection = None
                self.connect_button.configure(state="normal", text="Connetti")

        except websockets.exceptions.ConnectionRefusedError:
            self.update_status(f"Errore: Connessione rifiutata dal server {uri}.", "red")
            print(f"ERRORE TECNICO: Connessione rifiutata dal server {uri}.")
        except websockets.exceptions.ConnectionClosed as e:
            self.update_status(f"Connessione chiusa: {e}", "red")
            print(f"ERRORE TECNICO: Connessione chiusa: {e}")
        except Exception as e:
            self.update_status(f"Errore generale: {e}", "red")
            print(f"ERRORE TECNICO: Errore durante la connessione: {e}")
        finally:
            if websocket_connection and not websocket_connection.closed:
                await websocket_connection.close()
            websocket_connection = None
            self.update_status("Disconnesso", "red")
            self.connect_button.configure(state="normal", text="Connetti")
            print("TECNICO: Connessione terminata o fallita. Reset.")

    def connect_button_callback(self, event=None):
<<<<<<< HEAD
        # Questo metodo viene chiamato dal bottone o da <Return> sull'entry PIN
        # Deve schedulare il task asyncio nel loop corrente
=======
>>>>>>> 413ff6f04e84f437222564744ceed3974a03307d
        if self.connection_task and not self.connection_task.done():
            print("TECNICO: Tentativo di connessione già in corso.")
            return
        if websocket_connection and not websocket_connection.closed:
            print("TECNICO: Già connesso. Disconnetto...")
            # Schedule disconnection
            asyncio.create_task(websocket_connection.close())
        else:
            self.connection_task = asyncio.create_task(self.connect_to_server())

    async def receive_messages(self):
        global websocket_connection
        print("TECNICO: Avvio loop di ricezione messaggi.")
        while websocket_connection and not websocket_connection.closed:
            try:
                message_str = await websocket_connection.recv()
                message = json.loads(message_str)

                msg_type = message.get("type")
                content_type = message.get("content_type")

                if msg_type == "message" and content_type == "screen":
                    encoded_frame = message.get("content")
                    if encoded_frame:
                        try:
                            # Metti il frame nella coda per il task di visualizzazione
                            if not screen_frame_queue.full():
                                await screen_frame_queue.put(encoded_frame)
                            # else:
                                # print("TECNICO DEBUG: Coda frame piena, scartato un frame.")
                        except Exception as e:
                            print(f"TECNICO ERRORE: Fallito l'inserimento del frame nella coda: {e}")
                    else:
                        print("TECNICO ERRORE: Frame schermo ricevuto ma contenuto vuoto.")
                elif msg_type == "notification":
                    print(f"TECNICO NOTIFICA: {message.get('message')}")
                    self.update_status(f"Notifica: {message.get('message')}", "orange")
                else:
                    print(f"TECNICO: Messaggio ricevuto (tipo: {msg_type}, contenuto_tipo: {content_type})")

            except websockets.exceptions.ConnectionClosedOK:
                print("TECNICO: Connessione chiusa normalmente durante ricezione.")
                break
            except websockets.exceptions.ConnectionClosedError as e:
                print(f"TECNICO ERRORE: Connessione chiusa inaspettatamente durante ricezione: {e}")
                break
            except json.JSONDecodeError:
                print(f"TECNICO ERRORE: JSON non valido ricevuto: {message_str[:100]}...")
            except Exception as e:
                print(f"TECNICO ERRORE: Errore durante ricezione messaggi: {e}")
<<<<<<< HEAD
                break # Esci dal loop di ricezione in caso di errore grave
        print("TECNICO: Loop di ricezione messaggi terminato.")

        # Quando il loop di ricezione termina, assicurati di pulire lo stato della connessione
        if websocket_connection and not websocket_connection.closed:
            await websocket_connection.close()
        websocket_connection = None
        self.update_status("Disconnesso", "red")
        self.connect_button.configure(state="normal", text="Connetti")
    
    async def display_screen_frames(self):
        global screen_label
        print("TECNICO: Avvio loop di visualizzazione schermo.")
        while True: # Loop indefinito, interrotto solo se il task viene cancellato
            try:
                encoded_frame = await screen_frame_queue.get()
                decoded_frame = base64.b64decode(encoded_frame)
                np_arr = np.frombuffer(decoded_frame, np.uint8)
                frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

                if frame is not None:
                    # Salva le dimensioni originali del frame
                    self.client_screen_height, self.client_screen_width, _ = frame.shape

                    # Ottieni le dimensioni attuali del widget di visualizzazione
                    widget_width = screen_label.winfo_width()
                    widget_height = screen_label.winfo_height()

                    if widget_width == 1 or widget_height == 1: # Se l'app non è ancora renderizzata o è troppo piccola
                        # Usa dimensioni di fallback o attendi il prossimo ciclo
                        target_width = 800 # Dimensione base se non c'è ancora un widget
                        target_height = int(frame.shape[0] * (target_width / frame.shape[1]))
                        if target_height > 600: # Limita altezza massima
                            target_height = 600
                            target_width = int(frame.shape[1] * (target_height / frame.shape[0]))
                    else:
                        target_width = widget_width
                        target_height = widget_height

                    # Mantieni le proporzioni dell'immagine
                    original_height, original_width, _ = frame.shape
                    ratio = min(target_width / original_width, target_height / original_height)
                    new_width = int(original_width * ratio)
                    new_height = int(original_height * ratio)

                    # Ridimensiona l'immagine
                    resized_frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)

                    # Converti in formato PIL (RGB) e poi in ImageTk
                    img_rgb = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
                    img_pil = Image.fromarray(img_rgb)
                    img_tk = ImageTk.PhotoImage(image=img_pil)

                    # Aggiorna il widget di visualizzazione
                    screen_label.configure(image=img_tk)
                    screen_label.image = img_tk # Mantiene un riferimento per evitare che l'immagine venga deallocata

                else:
                    print("TECNICO ERRORE: Impossibile decodificare il frame.")

            except asyncio.CancelledError:
                print("TECNICO: Loop di visualizzazione schermo cancellato.")
                break # Termina il loop se il task viene cancellato
            except Exception as e:
                print(f"TECNICO ERRORE durante visualizzazione frame: {e}")
                await asyncio.sleep(0.1) # Attendi un po' prima di riprovare

        print("TECNICO: Loop di visualizzazione schermo terminato.")

    # --- Gestione Eventi Mouse e Tastiera ---

    def _map_coords(self, event):
        # Mappa le coordinate dell'evento (rispetto al widget) alle coordinate originali dello schermo client
        if screen_label.image and self.client_screen_width > 0 and self.client_screen_height > 0:
            img_width = screen_label.image.width()
            img_height = screen_label.image.height()
            
            # Calcola il rapporto di scala applicato
            x_scale = self.client_screen_width / img_width
            y_scale = self.client_screen_height / img_height

=======
                break
        print("TECNICO: Loop di ricezione messaggi terminato.")

    if websocket_connection and not websocket_connection.closed:
        await websocket_connection.close()
    websocket_connection = None
    self.update_status("Disconnesso", "red")
    self.connect_button.configure(state="normal", text="Connetti")


    
    
async def display_screen_frames():
    global screen_label
    print("TECNICO: Avvio loop di visualizzazione schermo.")
    while True: # Loop indefinito, interrotto solo se il task viene cancellato
        try:
            encoded_frame = await screen_frame_queue.get()
            decoded_frame = base64.b64decode(encoded_frame)
            np_arr = np.frombuffer(decoded_frame, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if frame is not None:
                # Ottieni le dimensioni attuali del widget di visualizzazione
                widget_width = screen_label.winfo_width()
                widget_height = screen_label.winfo_height()

                if widget_width == 1 or widget_height == 1: # Se l'app non è ancora renderizzata o è troppo piccola
                    # Usa dimensioni di fallback o attendi il prossimo ciclo
                    target_width = 800 # Dimensione base se non c'è ancora un widget
                    target_height = int(frame.shape[0] * (target_width / frame.shape[1]))
                    if target_height > 600: # Limita altezza massima
                        target_height = 600
                        target_width = int(frame.shape[1] * (target_height / frame.shape[0]))
                else:
                    target_width = widget_width
                    target_height = widget_height

                # Mantieni le proporzioni dell'immagine
                original_height, original_width, _ = frame.shape
                ratio = min(target_width / original_width, target_height / original_height)
                new_width = int(original_width * ratio)
                new_height = int(original_height * ratio)

                # Ridimensiona l'immagine
                resized_frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)

                # Converti in formato PIL (RGB) e poi in ImageTk
                img_rgb = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
                img_pil = Image.fromarray(img_rgb)
                img_tk = ImageTk.PhotoImage(image=img_pil)

                # Aggiorna il widget di visualizzazione
                screen_label.configure(image=img_tk)
                screen_label.image = img_tk # Mantiene un riferimento per evitare che l'immagine venga deallocata

            else:
                print("TECNICO ERRORE: Impossibile decodificare il frame.")

        except asyncio.CancelledError:
            print("TECNICO: Loop di visualizzazione schermo cancellato.")
            break # Termina il loop se il task viene cancellato
        except Exception as e:
            print(f"TECNICO ERRORE durante visualizzazione frame: {e}")
            await asyncio.sleep(0.1) # Attendi un po' prima di riprovare

    print("TECNICO: Loop di visualizzazione schermo terminato.")

    
    # --- Gestione Eventi Mouse e Tastiera ---

    def _map_coords(event):
        # Mappa le coordinate dell'evento (rispetto al widget) alle coordinate originali dello schermo client
        if screen_label.image:
            img_width = screen_label.image.width()
            img_height = screen_label.image.height()
            
            # Recupera le dimensioni originali del frame (le ultime che sono state elaborate)
            # Questo è un workaround, sarebbe meglio passarle direttamente
            if hasattr(screen_label, '_last_original_dims'):
                orig_width, orig_height = screen_label._last_original_dims
            else:
                # Fallback se non ci sono ancora dimensioni originali (dovrebbe essere raro)
                return event.x, event.y # Ritorna le coordinate non mappate

            # Calcola il rapporto di scala applicato
            x_scale = orig_width / img_width
            y_scale = orig_height / img_height

>>>>>>> 413ff6f04e84f437222564744ceed3974a03307d
            # Mappa le coordinate del click/movimento alle dimensioni originali
            mapped_x = int(event.x * x_scale)
            mapped_y = int(event.y * y_scale)
            return mapped_x, mapped_y
<<<<<<< HEAD
        return event.x, event.y # Se non c'è immagine o dimensioni, ritorna le coordinate senza mappa


    async def send_command(self, command_type, data):
=======
        return event.x, event.y # Se non c'è immagine, ritorna le coordinate senza mappa


    async def send_command(command_type, data):
>>>>>>> 413ff6f04e84f437222564744ceed3974a03307d
        global websocket_connection
        if websocket_connection and not websocket_connection.closed:
            command_message = json.dumps({
                "type": "command",
                "command_type": command_type,
                "data": data
            })
<<<<<<< HEAD
            try:
                await websocket_connection.send(command_message)
                # print(f"TECNICO DEBUG: Inviato comando: {command_type} con dati: {data}")
            except websockets.exceptions.ConnectionClosed:
                print(f"TECNICO AVVISO: Connessione chiusa durante l'invio del comando {command_type}.")
            except Exception as e:
                print(f"TECNICO ERRORE: Impossibile inviare comando {command_type}: {e}")
=======
            await websocket_connection.send(command_message)
            # print(f"TECNICO DEBUG: Inviato comando: {command_type} con dati: {data}")
>>>>>>> 413ff6f04e84f437222564744ceed3974a03307d
        else:
            print("TECNICO AVVISO: Non connesso al client, impossibile inviare comando.")

    def on_mouse_click(self, event):
<<<<<<< HEAD
        x_mapped, y_mapped = self._map_coords(event)
=======
        x_mapped, y_mapped = _map_coords(event)
>>>>>>> 413ff6f04e84f437222564744ceed3974a03307d
        
        button_map = {
            1: "left",    # Button-1 è il click sinistro
            2: "middle",  # Button-2 è il click centrale (rotellina)
            3: "right"    # Button-3 è il click destro
        }
        button_name = button_map.get(event.num)
        if button_name:
<<<<<<< HEAD
            # Schedula il task asyncio nel loop corrente
            asyncio.create_task(self.send_command("mouse_click", {"x": x_mapped, "y": y_mapped, "button": button_name}))
            print(f"TECNICO: Click {button_name} a ({x_mapped}, {y_mapped})")

    def on_mouse_move(self, event):
        x_mapped, y_mapped = self._map_coords(event)
        # Invia solo se il mouse si è mosso di una quantità significativa per evitare spam
        if abs(x_mapped - self._last_mouse_pos[0]) > 2 or abs(y_mapped - self._last_mouse_pos[1]) > 2:
            asyncio.create_task(self.send_command("mouse_move", {"x": x_mapped, "y": y_mapped}))
=======
            asyncio.create_task(send_command("mouse_click", {"x": x_mapped, "y": y_mapped, "button": button_name}))
            print(f"TECNICO: Click {button_name} a ({x_mapped}, {y_mapped})")

    def on_mouse_move(self, event):
        x_mapped, y_mapped = _map_coords(event)
        # Invia solo se il mouse si è mosso di una quantità significativa per evitare spam
        if not hasattr(self, '_last_mouse_pos') or abs(x_mapped - self._last_mouse_pos[0]) > 2 or abs(y_mapped - self._last_mouse_pos[1]) > 2:
            asyncio.create_task(send_command("mouse_move", {"x": x_mapped, "y": y_mapped}))
>>>>>>> 413ff6f04e84f437222564744ceed3974a03307d
            self._last_mouse_pos = (x_mapped, y_mapped)
            # print(f"TECNICO: Mouse mosso a ({x_mapped}, {y_mapped})") # Troppo verboso


<<<<<<< HEAD
    def on_mouse_scroll(self, event):
        direction = "up" if event.delta > 0 else "down"
        # Schedula il task asyncio nel loop corrente
        asyncio.create_task(self.send_command("mouse_scroll", {"direction": direction}))
        print(f"TECNICO: Scroll mouse {direction}")
    
    def on_key_down(self, event):
=======
    # Threading per lo scroll per non bloccare l'interfaccia
    def _scroll_worker(direction):
        asyncio.run(send_command("mouse_scroll", {"direction": direction}))

    def on_mouse_scroll(self, event):
        direction = "up" if event.delta > 0 else "down"
        threading.Thread(target=_scroll_worker, args=(direction,), daemon=True).start()
        print(f"TECNICO: Scroll mouse {direction}")
    
    # Set di tasti attualmente premuti per gestire key_press e key_release (se necessario)
    self._pressed_keys = set()

    def on_key_press(self, event):
>>>>>>> 413ff6f04e84f437222564744ceed3974a03307d
        # Ignore modifier keys pressed alone
        if event.keysym in ["Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R", "Meta_L", "Meta_R"]:
            return
        
        # Ignora i tasti ripetuti se il tasto è già "premuto" logicamente
        if event.keysym in self._pressed_keys:
            return
        
        # Mappa i nomi dei tasti di Tkinter a nomi comuni o a quelli di pyautogui se diversi
        key_map = {
            'space': ' ', 'Return': 'enter', 'BackSpace': 'backspace', 'Tab': 'tab',
            'Caps_Lock': 'capslock', 'Num_Lock': 'numlock', 'Scroll_Lock': 'scrolllock',
            'Up': 'up', 'Down': 'down', 'Left': 'left', 'Right': 'right',
            'Home': 'home', 'End': 'end', 'Prior': 'page_up', 'Next': 'page_down', # Prior=PgUp, Next=PgDown
            'Insert': 'insert', 'Delete': 'delete',
            'PrintScreen': 'prntscrn', 'Pause': 'pause',
            'Control_L': 'ctrl_l', 'Control_R': 'ctrl_r',
            'Alt_L': 'alt_l', 'Alt_R': 'alt_r',
            'Shift_L': 'shift_l', 'Shift_R': 'shift_r',
            'Win_L': 'cmd_l', 'Win_R': 'cmd_r', # Tasto Windows
            'Escape': 'esc'
        }
        
        key_to_send = key_map.get(event.keysym, event.char if event.char else event.keysym)
        
        # Gestisci i casi speciali in cui event.char è vuoto per tasti non stampabili
        if not event.char and event.keysym.startswith('F') and len(event.keysym) <=3: # F1, F2...F12
            key_to_send = event.keysym.lower() # es. 'f1'
        elif not event.char and event.keysym == 'plus': # Gestisce il tasto '+' del tastierino numerico
            key_to_send = '+'
        elif not event.char and event.keysym == 'minus': # Gestisce il tasto '-' del tastierino numerico
            key_to_send = '-'
        elif not event.char and event.keysym == 'asterisk': # Gestisce il tasto '*' del tastierino numerico
            key_to_send = '*'
        elif not event.char and event.keysym == 'slash': # Gestisce il tasto '/' del tastierino numerico
            key_to_send = '/'
        elif not event.char and event.keysym.isdigit(): # Per numeri del tastierino numerico se non in event.char
            key_to_send = event.keysym

        # Considera il tasto premuto
        self._pressed_keys.add(event.keysym)
        
        # Invia solo se il tasto non è un modificatore o se il carattere è stampabile
        if key_to_send:
<<<<<<< HEAD
            asyncio.create_task(self.send_command("key_press", {"key": key_to_send}))
            print(f"TECNICO: Tasto premuto: {key_to_send} (keysym: {event.keysym})")

=======
            asyncio.create_task(send_command("key_press", {"key": key_to_send}))
            print(f"TECNICO: Tasto premuto: {key_to_send} (keysym: {event.keysym})")

    def on_key_down(self, event):
        # Utilizzato per gestire la pressione iniziale (es. per tenere premuto)
        # Per ora, `on_key_press` è sufficiente per la maggior parte dei casi.
        # Se hai bisogno di simulare `keyDown` separato da `keyUp`, questa è la funzione.
        pass

>>>>>>> 413ff6f04e84f437222564744ceed3974a03307d
    def on_key_up(self, event):
        # Rimuove il tasto dal set dei tasti premuti
        if event.keysym in self._pressed_keys:
            self._pressed_keys.remove(event.keysym)
        # Se hai bisogno di simulare `keyUp` separato da `keyDown`, questa è la funzione.
        pass

    def on_closing(self):
        print("TECNICO: Chiusura applicazione. Disconnessione...")
        # Cancella i task asyncio
        if self.connection_task and not self.connection_task.done():
            self.connection_task.cancel()
        if self.receive_task and not self.receive_task.done():
            self.receive_task.cancel()
        if self.display_task and not self.display_task.done():
            self.display_task.cancel()

        # Chiudi la connessione WebSocket se aperta
        global websocket_connection
        if websocket_connection and not websocket_connection.closed:
            asyncio.create_task(websocket_connection.close()) # Chiudi in modo asincrono

        # Avvia un timer per distruggere l'app dopo un breve ritardo per permettere la chiusura async
        self.after(200, self.destroy) # Distrugge la finestra dopo 200ms

# --- BLOCCO PRINCIPALE DI ESECUZIONE ---
async def main_async():
    app = TechnicianApp()
<<<<<<< HEAD
    
    def tkinter_periodic_update():
        # Questo metodo viene chiamato periodicamente per aggiornare la GUI
        try:
            app.update_idletasks()
            app.update()
        except tk.TclError as e:
            # Cattura l'errore se la finestra è già stata distrutta durante la chiusura
            if "main window has been destroyed" not in str(e):
                print(f"TECNICO ERRORE: Tkinter update_idletasks/update ha incontrato un errore: {e}")
            return # Ferma il richiamo periodico
        
=======
    # Esegui il loop di asyncio e il loop principale di Tkinter in parallelo
    # Tkinter ha bisogno del suo thread principale.
    # Usiamo app.after per schedulare una funzione che pompa gli eventi asyncio
    
    def run_tkinter():
        try:
            app.mainloop()
        except KeyboardInterrupt:
            print("TECNICO: Tkinter mainloop interrotto.")
        except Exception as e:
            print(f"TECNICO ERRORE: Tkinter mainloop ha incontrato un errore: {e}")
        finally:
            # Assicurati che il loop asyncio sia fermato quando Tkinter si chiude
            if app.loop and app.loop.is_running():
                app.loop.stop()

    # Avvia Tkinter in un thread separato o gestisci i suoi eventi dal loop asyncio
    # Questo è un modo comune per farli convivere, sebbene non sia una soluzione perfettamente integrata
    # Se il sistema lo permette, è meglio un Tkinter loop integrato con asyncio (es. tkinter-asyncio)
    # Per semplicità, ci affidiamo a app.update_idletasks() e app.update()
    
    # Invece di un thread separato, integriamo Tkinter nel loop asyncio
    def tkinter_periodic_update():
        app.update_idletasks()
        app.update()
>>>>>>> 413ff6f04e84f437222564744ceed3974a03307d
        if app.winfo_exists(): # Continua solo se la finestra esiste
            app.after(10, tkinter_periodic_update) # Richiama se stesso dopo 10ms

    app.after(10, tkinter_periodic_update)
    
<<<<<<< HEAD
    try:
        # Questo Future bloccherà finché il loop asyncio non verrà fermato (es. alla chiusura dell'app)
=======
    # L'applicazione Tkinter ora viene aggiornata periodicamente all'interno del loop di asyncio.
    # Attendiamo indefinitamente qui per mantenere il loop asyncio in esecuzione.
    try:
        # Questo bloccherà finché il loop asyncio non verrà fermato (es. alla chiusura dell'app)
>>>>>>> 413ff6f04e84f437222564744ceed3974a03307d
        await asyncio.Future() 
    except asyncio.CancelledError:
        print("TECNICO: Asyncio loop del tecnico cancellato.")
    finally:
        print("TECNICO: Uscita dal main_async.")


if __name__ == "__main__":
    print("TECNICO: Avvio del programma tecnico...")
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("TECNICO: Programma interrotto dall'utente.")
    except Exception as e:
        print(f"TECNICO ERRORE CRITICO: {e}")
<<<<<<< HEAD
        sys.exit(1) # Termina con codice di errore
=======
>>>>>>> 413ff6f04e84f437222564744ceed3974a03307d
    finally:
        print("TECNICO: Programma tecnico terminato.")