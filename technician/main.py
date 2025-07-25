# technician/main.py

import asyncio
import base64
import json
import tkinter as tk
from tkinter import PhotoImage
from PIL import Image, ImageTk
import io
import websockets
import threading
import pynput
import cv2
import numpy

# --- CONFIGURAZIONE ---
SERVER_HOST = "188.245.238.160" # Assicurati che sia l'IP corretto del tuo server Hetzner
SERVER_PORT = 8765
TECH_ID = "tecnico-001"

websocket_client = None
asyncio_loop = None # Variabile globale per il loop asyncio
app_instance = None # Riferimento all'istanza dell'applicazione per accessibilità globale

# --- CLASSE DELL'APPLICAZIONE TECNICO ---
class TechnicianApp:
    def __init__(self, master, loop):
        self.master = master
        self.asyncio_loop = loop
        master.title(f"Schermo Remoto Tecnico - ID: {TECH_ID}") # Aggiunto ID nel titolo
        master.geometry("1024x768")
        
        self.canvas = tk.Canvas(master, bg="black", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.last_img = None
        
        self.is_connected = False # Flag di stato della connessione WebSocket attiva
        self.is_registered = False # Flag per indicare se il tecnico è registrato con PIN
        self.target_client_id = None # L'ID del client a cui questo tecnico è connesso

        # --- Listener pynput per mouse e tastiera locali (del tecnico) ---
        self.mouse_listener = pynput.mouse.Listener(
            on_click=self._on_click_local,
            on_scroll=self._on_scroll_local
        )
        self.keyboard_listener = pynput.keyboard.Listener(
            on_press=self._on_press_local,
            on_release=self._on_release_local
        )
        
        self.dragging = False
        self.start_x = 0
        self.start_y = 0

        # Bind degli eventi del mouse sul canvas (schermo remoto)
        self.canvas.bind("<Button-1>", self.on_left_click_canvas)
        self.canvas.bind("<Button-3>", self.on_right_click_canvas)
        self.canvas.bind("<ButtonRelease-1>", self.on_left_release_canvas)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag_canvas)
        self.canvas.bind("<MouseWheel>", self.on_mouse_scroll_canvas)

        master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def start_local_listeners(self):
        """Avvia i listener di pynput solo quando la connessione è pronta e registrata."""
        if not self.mouse_listener.running:
            try:
                self.mouse_listener.start()
                print("DEBUG TECNICO: Listener mouse locale avviato.")
            except Exception as e:
                print(f"ERRORE TECNICO: Impossibile avviare listener mouse: {e}")
        if not self.keyboard_listener.running:
            try:
                self.keyboard_listener.start()
                print("DEBUG TECNICO: Listener tastiera locale avviato.")
            except Exception as e:
                print(f"ERRORE TECNICO: Impossibile avviare listener tastiera: {e}")

    # --- METODI PER GESTIRE L'INPUT SUL CANVAS ---
    # Questi metodi inviano comandi al server, che poi li inoltra al client
    def on_left_click_canvas(self, event):
        if self.is_connected and self.is_registered and self.target_client_id and websocket_client and websocket_client.open:
            print(f"DEBUG TECNICO: Click sinistro sul canvas: x={event.x}, y={event.y}")
            self.asyncio_loop.call_soon_threadsafe(
                asyncio.create_task,
                _send_command_to_server("mouse_click", {"x": event.x, "y": event.y, "button": "left"}, self.target_client_id)
            )
            self.start_x = event.x
            self.start_y = event.y
            self.dragging = True
        else:
            print("AVVISO TECNICO: Click sinistro sul canvas ignorato - non connesso, non registrato o client target non definito.")

    def on_right_click_canvas(self, event):
        if self.is_connected and self.is_registered and self.target_client_id and websocket_client and websocket_client.open:
            print(f"DEBUG TECNICO: Click destro sul canvas: x={event.x}, y={event.y}")
            self.asyncio_loop.call_soon_threadsafe(
                asyncio.create_task,
                _send_command_to_server("mouse_click", {"x": event.x, "y": event.y, "button": "right"}, self.target_client_id)
            )
        else:
            print("AVVISO TECNICO: Click destro sul canvas ignorato - non connesso, non registrato o client target non definito.")

    def on_left_release_canvas(self, event):
        if self.dragging:
            self.dragging = False
            # Se fosse un drag-and-drop, qui invieresti l'evento di rilascio
            print(f"DEBUG TECNICO: Rilascio sinistro sul canvas: x={event.x}, y={event.y}")

    def on_mouse_drag_canvas(self, event):
        if self.dragging and self.is_connected and self.is_registered and self.target_client_id and websocket_client and websocket_client.open:
            # print(f"DEBUG TECNICO: Dragging mouse: x={event.x}, y={event.y}") # Molto verboso
            self.asyncio_loop.call_soon_threadsafe(
                asyncio.create_task,
                _send_command_to_server("mouse_move", {"x": event.x, "y": event.y}, self.target_client_id)
            )
        # else:
            # print("AVVISO TECNICO: Dragging ignorato - non connesso, non registrato o client target non definito.")

    def on_mouse_scroll_canvas(self, event):
        if self.is_connected and self.is_registered and self.target_client_id and websocket_client and websocket_client.open:
            # event.delta è specifico di Windows/macOS per la rotella del mouse
            # Su Linux potrebbe essere event.num == 4 (up) o 5 (down)
            direction = "up" if event.delta > 0 else "down"
            print(f"DEBUG TECNICO: Scroll {direction} sul canvas: x={event.x}, y={event.y}")
            self.asyncio_loop.call_soon_threadsafe(
                asyncio.create_task,
                _send_command_to_server("mouse_scroll", {"x": event.x, "y": event.y, "direction": direction}, self.target_client_id)
            )
        else:
            print("AVVISO TECNICO: Scroll ignorato - non connesso, non registrato o client target non definito.")

    # --- METODI PER GESTIRE L'INPUT LOCALE DEL TECNICO (pynput) ---
    # Questi metodi intercettano i tasti premuti dal tecnico sulla sua tastiera
    # e li inviano al server per essere inoltrati al client.
    def _on_click_local(self, x, y, button, pressed):
        pass # Non usiamo pynput per i click, ma il canvas

    def _on_scroll_local(self, x, y, dx, dy):
        pass # Non usiamo pynput per lo scroll, ma il canvas

    def _on_press_local(self, key):
        if self.is_connected and self.is_registered and self.target_client_id and websocket_client and websocket_client.open:
            key_char = None
            try:
                key_char = key.char # Caratteri normali
                if key_char is None:
                    raise AttributeError
            except AttributeError:
                # Tasti speciali (es. Shift, Ctrl, F1, ecc.)
                # Converte Key.ctrl_l in 'ctrl_l'
                key_char = str(key).replace('Key.', '').lower()
                # Rimuove eventuali angoli residui da alcuni tasti pynput (es. <96>)
                if key_char.startswith('<') and key_char.endswith('>'):
                    key_char = key_char.strip('<>')
            
            if key_char is not None and key_char != '':
                print(f"DEBUG TECNICO: Tasto inviato da tastiera locale: '{key_char}'")
                self.asyncio_loop.call_soon_threadsafe(
                    asyncio.create_task,
                    _send_command_to_server("key_press", {"key": key_char}, self.target_client_id)
                )
            else:
                print(f"AVVISO TECNICO: Tasto non riconosciuto o vuoto catturato: {key}, non inviato.")
        # else:
            # print(f"AVVISO TECNICO: Tasto '{key}' ignorato - non connesso, non registrato o client target non definito.")
            
    def _on_release_local(self, key):
        pass # Per semplicità, al momento non inviamo eventi di "key_release" separati.

    # --- METODO DI CHIUSURA DELL'APPLICAZIONE ---
    def on_closing(self):
        print("Tecnico: Chiusura dell'applicazione.")
        self.is_connected = False # Imposta il flag per interrompere i loop di ricezione
        self.is_registered = False # Anche la registrazione

        # Schedula la chiusura del websocket nel thread asyncio
        if websocket_client and websocket_client.open:
            self.asyncio_loop.call_soon_threadsafe(
                asyncio.create_task,
                websocket_client.close()
            )
        
        # Ferma i listener di pynput solo se sono in esecuzione
        if self.mouse_listener.running:
            self.mouse_listener.stop()
        if self.keyboard_listener.running:
            self.keyboard_listener.stop()
        print("DEBUG TECNICO: Listener mouse e tastiera locali fermati.")

        # Chiudi la finestra Tkinter
        self.master.quit()


# --- FUNZIONI DI SUPPORTO (esterne alla classe) ---

async def _send_command_to_server(command_type, data, target_client_id):
    global websocket_client
    if websocket_client and websocket_client.open:
        command_message = json.dumps({
            "type": "command",
            "role": "technician",
            "id": TECH_ID,
            "command_type": command_type,
            "data": data,
            "target_id": target_client_id # Indica al server a quale client inviare il comando
        })
        await websocket_client.send(command_message)
    else:
        print(f"AVVISO TECNICO: Tentativo di inviare comando '{command_type}' ma websocket non è aperto o connesso.")

async def receive_and_display_frames(ws, app_instance):
    try:
        while app_instance.is_connected:
            message = await ws.recv()
            
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                print(f"ERRORE TECNICO: Impossibile decodificare il JSON del messaggio: {message[:100]}...")
                continue
            
            # Logging più dettagliato per capire il problema del 'content_type'
            # print(f"DEBUG TECNICO: Ricevuto messaggio. Type: {data.get('type')}, Content_type: {data.get('content_type')}") # Molto verboso

            # Se il server invia un messaggio di successo registrazione
            if data.get('type') == 'status' and data.get('status') == 'registered' and data.get('role') == 'technician':
                app_instance.is_registered = True
                app_instance.target_client_id = data.get('target_client_id')
                print(f"✅ Tecnico: Registrazione al server completata e associato al client: {app_instance.target_client_id}. Input locale abilitato.")
                # Avvia i listener di pynput solo dopo la registrazione e l'associazione
                app_instance.start_local_listeners() 
                continue # Non è un frame, quindi continua al prossimo messaggio
            elif data.get('type') == 'status' and data.get('status') == 'invalid_pin':
                print("ERRORE TECNICO: PIN non valido o client non trovato. Connessione chiusa.")
                app_instance.is_connected = False
                app_instance.master.quit()
                break # Esce dal loop e dal task

            if data.get('type') == 'message' and data.get('content_type') == 'screen':
                encoded_frame = data['content']
                decoded_frame = base64.b64decode(encoded_frame)
                
                nparr = numpy.frombuffer(decoded_frame, numpy.uint8)
                img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                if img_np is None:
                    print("ERRORE TECNICO: Impossibile decodificare l'immagine. Frame corrotto o formato non supportato.")
                    continue

                # Converti l'immagine da BGR a RGB per PIL
                img_pil = Image.fromarray(cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB))
                
                current_width = app_instance.canvas.winfo_width()
                current_height = app_instance.canvas.winfo_height()
                
                # Previene divisione per zero o resize a 0
                if current_width <= 0: current_width = 1024
                if current_height <= 0: current_height = 768

                # Resize dell'immagine per adattarla al canvas
                img_pil = img_pil.resize((current_width, current_height), Image.LANCZOS)

                photo_image = ImageTk.PhotoImage(img_pil)
                
                # Aggiorna il canvas di Tkinter sul thread principale (programmazione GUI)
                app_instance.master.after(0, app_instance.canvas.create_image, 0, 0, anchor=tk.NW, image=photo_image)
                app_instance.last_img = photo_image # Mantiene un riferimento per evitare che venga deallocata

            else:
                # Logga l'intero messaggio JSON se non è del tipo atteso per debugging
                print(f"AVVISO TECNICO: Messaggio non di tipo schermo atteso o non riconosciuto: {json.dumps(data, indent=2)}")

    except websockets.exceptions.ConnectionClosedOK:
        print("Tecnico: Connessione al server chiusa normalmente (ricezione frame).")
    except Exception as e:
        print(f"ERRORE TECNICO: Errore durante la ricezione o visualizzazione frame: {e}")
    finally:
        app_instance.is_connected = False
        app_instance.is_registered = False

async def start_technician_async_task(tech_id):
    global websocket_client, app_instance
    uri = f"ws://{SERVER_HOST}:{SERVER_PORT}"
    
    reconnect_attempts = 5
    for attempt in range(reconnect_attempts):
        try:
            async with websockets.connect(uri) as ws:
                websocket_client = ws
                app_instance.is_connected = True
                print("✅ Tecnico: Connesso al server.")

                pin = input("🔑 Tecnico: Inserisci il PIN ricevuto dal cliente: ")
                
                registration_message = json.dumps({
                    "type": "register",
                    "role": "technician",
                    "id": tech_id,
                    "pin": pin
                })
                await ws.send(registration_message)
                print(f"📝 Tecnico: Inviato messaggio di registrazione (ID: {tech_id}, PIN: {pin}).")

                print("✅ Tecnico: In attesa di conferma registrazione e schermo...")
                # receive_and_display_frames ora gestisce anche la risposta di registrazione
                await receive_and_display_frames(ws, app_instance)

        except websockets.exceptions.ConnectionRefusedError:
            print(f"ERRORE TECNICO: Connessione rifiutata dal server ({uri}). Assicurati che il server sia in esecuzione e accessibile. Riprovo in 5 secondi... ({attempt + 1}/{reconnect_attempts})")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"ERRORE TECNICO: Errore generale nella connessione: {e}. Riprovo in 5 secondi... ({attempt + 1}/{reconnect_attempts})")
            await asyncio.sleep(5)
    
    print(f"Tecnico: Falliti {reconnect_attempts} tentativi di connessione. Uscita.")
    if app_instance: # Assicurati di chiudere Tkinter se non è già chiuso
        app_instance.master.quit()


def run_asyncio_loop_in_thread(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

# --- BLOCCO PRINCIPALE DI ESECUZIONE ---
if __name__ == "__main__":
    root = tk.Tk()
    
    asyncio_loop = asyncio.new_event_loop()
    
    app_instance = TechnicianApp(root, asyncio_loop) # Assegna all'istanza globale
    
    asyncio_thread = threading.Thread(target=run_asyncio_loop_in_thread, args=(asyncio_loop,))
    asyncio_thread.daemon = True # Il thread si chiude automaticamente con il programma principale
    asyncio_thread.start()

    asyncio_loop.call_soon_threadsafe(
        asyncio.create_task,
        start_technician_async_task(TECH_ID)
    )

    root.mainloop()

    # --- Codice eseguito dopo la chiusura della finestra Tkinter ---
    print("DEBUG TECNICO: Finestra Tkinter chiusa. Avvio procedura di cleanup.")
    
    if app_instance.mouse_listener.running:
        app_instance.mouse_listener.stop()
    if app_instance.keyboard_listener.running:
        app_instance.keyboard_listener.stop()
    print("DEBUG TECNICO: Listener mouse e tastiera fermati.")

    # Ferma il loop asyncio in modo sicuro
    asyncio_loop.call_soon_threadsafe(asyncio_loop.stop)
    asyncio_thread.join(timeout=5) # Attendi che il thread asyncio termini (con un timeout)
    
    if asyncio_thread.is_alive():
        print("AVVISO TECNICO: Il thread asyncio non è terminato in tempo. Potrebbe esserci un cleanup incompleto.")
    print("DEBUG TECNICO: Programma del tecnico terminato.")