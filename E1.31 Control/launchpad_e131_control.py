import socket
import time
import threading
import rtmidi  # Assuming rtmidi library is installed
import tkinter as tk
from tkinter.scrolledtext import ScrolledText

# Constants
LAUNCHPAD_PORT_INDEX = 1
E131_PORT = 5568
UNIVERSE_START = 5
TOTAL_PADS = 112
CHUNK_SIZE = 32  # Adjust chunk size as needed

# Initialize MIDI output
midi_out = rtmidi.RtMidiOut()
midi_out.openPort(LAUNCHPAD_PORT_INDEX)

# Global variables
log_messages = []
is_listening = False
listener_thread = None  # Store thread object for listener

def scale_rgb(value):
    # Scale value from 0-255 to 0-63
    return int(value * 63 / 255)

def send_sysex_message_chunk(pad_values):
    try:
        for chunk_start in range(0, len(pad_values), CHUNK_SIZE):
            chunk = pad_values[chunk_start:chunk_start + CHUNK_SIZE]
            
            sysex_data = [
                0xF0, 0x00, 0x20, 0x29, 0x02, 0x18, 0x0B  # SysEx header for Launchpad MK2
            ]
            
            for pad, red_scaled, green_scaled, blue_scaled in chunk:
                sysex_data.extend([
                    pad,                                       # Pad number (0-99)
                    red_scaled, green_scaled, blue_scaled       # RGB values (0-63)
                ])
            
            sysex_data.append(0xF7)  # End of SysEx
            sysex_bytes = bytes(sysex_data)
            message = rtmidi.MidiMessage(sysex_bytes)
            midi_out.sendMessage(message)
            
            log_message(f"Sent {len(chunk)} SysEx messages in one chunk")
    except Exception as e:
        log_message(f"Failed to send SysEx messages: {e}")

def handle_e131_data(universe, data):
    if universe == UNIVERSE_START:
        pad_values = []

        # Custom mapping of LED data to Launchpad pads, top to bottom
        led_to_pad_mapping = {
            0: 11,  1: 12,  2: 13,  3: 14,  4: 15,  5: 16,  6: 17,  7: 18,  8: 19,   # Row 1
            9: 21, 10: 22, 11: 23, 12: 24, 13: 25, 14: 26, 15: 27, 16: 28, 17: 29,   # Row 2
            18: 31, 19: 32, 20: 33, 21: 34, 22: 35, 23: 36, 24: 37, 25: 38, 26: 39,   # Row 3
            27: 41, 28: 42, 29: 43, 30: 44, 31: 45, 32: 46, 33: 47, 34: 48, 35: 49,   # Row 4
            36: 51, 37: 52, 38: 53, 39: 54, 40: 55, 41: 56, 42: 57, 43: 58, 44: 59,   # Row 5
            45: 61, 46: 62, 47: 63, 48: 64, 49: 65, 50: 66, 51: 67, 52: 68, 53: 69,   # Row 6
            54: 71, 55: 72, 56: 73, 57: 74, 58: 75, 59: 76, 60: 77, 61: 78, 62: 79,   # Row 7
            63: 81, 64: 82, 65: 83, 66: 84, 67: 85, 68: 86, 69: 87, 70: 88, 71: 89,   # Row 8
            72: 104, 73: 105, 74: 106, 75: 107, 76: 108, 77: 109, 78: 110, 79: 111   # Top row
        }

        # Iterate over the available LED data indices
        for led_index in led_to_pad_mapping:
            pad_number = led_to_pad_mapping[led_index]
            if led_index * 3 + 2 < len(data):
                red = data[led_index * 3]
                green = data[led_index * 3 + 1]
                blue = data[led_index * 3 + 2]
                red_scaled = scale_rgb(red)
                green_scaled = scale_rgb(green)
                blue_scaled = scale_rgb(blue)
                
                pad_values.append((pad_number, red_scaled, green_scaled, blue_scaled))
            else:
                log_message(f"Insufficient data for LED index {led_index}")

        # Send SysEx messages in chunks
        send_sysex_message_chunk(pad_values)

def e131_listener(log_message):
    global is_listening
    is_listening = True

    # Create E1.31 listener
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.setblocking(False)  # Non-blocking mode
    server.bind(('0.0.0.0', E131_PORT))
    log_message(f"Listening for E1.31 data on port {E131_PORT}...")

    while is_listening:
        try:
            data, addr = server.recvfrom(1024)
            universe = int.from_bytes(data[113:115], byteorder='big')
            dmx_data = data[126:462]  # Extracting DMX data from the packet (112 pads * 3 channels)
            handle_e131_data(universe, dmx_data)
        
        except BlockingIOError:
            continue  # No data received, continue to next iteration
        except Exception as e:
            log_message(f"Exception in E1.31 listener: {e}")
        
        time.sleep(0.01)  # Adjust sleep time to manage CPU usage

    server.close()

def start_listener(log_message):
    global is_listening, listener_thread
    if not is_listening:
        is_listening = True
        listener_thread = threading.Thread(target=e131_listener, args=(log_message,))
        listener_thread.start()
        log_message("Listener started.")

def stop_listener(log_message):
    global is_listening, listener_thread
    if is_listening:
        is_listening = False
        if listener_thread:
            listener_thread.join()  # Wait for listener thread to complete
        log_message("Stopping listener...")

def gui_update(log_message):
    global root
    root = tk.Tk()
    root.title("Launchpad Control")
    root.protocol("WM_DELETE_WINDOW", on_close)  # Handle window close event

    log_label = ScrolledText(root, height=10, width=50)
    log_label.pack(padx=10, pady=10)

    start_button = tk.Button(root, text="Start Listener", command=lambda: start_listener(log_message))
    start_button.pack(pady=5)

    stop_button = tk.Button(root, text="Stop Listener", command=lambda: stop_listener(log_message))
    stop_button.pack(pady=5)

    # Start listener automatically
    start_listener(log_message)

    def update_gui():
        while True:
            log_label.delete(1.0, tk.END)
            for msg in log_messages[-4:]:  # Display last 4 log messages
                log_label.insert(tk.END, msg + "\n")
            time.sleep(0.1)

    thread = threading.Thread(target=update_gui)
    thread.start()

    root.mainloop()

def on_close():
    global root, is_listening
    if is_listening:
        stop_listener(log_message)
    if root:
        root.destroy()

    # Exit the script
    import sys
    sys.exit()

def log_message(message):
    global log_messages
    log_messages.append(message)
    if len(log_messages) > 100:  # Limit number of log messages
        log_messages = log_messages[-100:]

def main():
    gui_thread = threading.Thread(target=gui_update, args=(log_message,))
    gui_thread.start()

if __name__ == "__main__":
    main()
