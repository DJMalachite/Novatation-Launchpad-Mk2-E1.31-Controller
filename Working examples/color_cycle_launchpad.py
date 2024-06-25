import time
import rtmidi

# Open the MIDI output port for the Launchpad MK2
midi_out = rtmidi.RtMidiOut()
midi_out.openPort(1)  # Replace with the correct index of your Launchpad MK2 port

def send_sysex_message(pad, red, green, blue):
    sysex = [
        0xF0, 0x00, 0x20, 0x29, 0x02, 0x18, 0x0B,  # SysEx header for Launchpad MK2
        pad,                                       # Pad number (0-99)
        red, green, blue,                          # RGB values (0-63)
        0xF7                                       # End of SysEx
    ]
    sysex_bytes = bytes(sysex)
    message = rtmidi.MidiMessage(sysex_bytes)
    midi_out.sendMessage(message)
    print({sysex_bytes})

def cycle_colors():
    try:
        while True:
            # Red to Green
            for intensity in range(0, 64):
                send_sysex_message(11, 63 - intensity, intensity, 0)
                time.sleep(0.05)
            
            # Green to Blue
            for intensity in range(0, 64):
                send_sysex_message(11, 0, 63 - intensity, intensity)
                time.sleep(0.05)
            
            # Blue to Red
            for intensity in range(0, 64):
                send_sysex_message(11, intensity, 0, 63 - intensity)
                time.sleep(0.05)
    
    except KeyboardInterrupt:
        # Handle Ctrl+C to exit gracefully
        print("\nStopping the color cycle.")

# Start cycling colors
cycle_colors()
