import time
import rtmidi

# Open the MIDI output port for the Launchpad MK2
midi_out = rtmidi.RtMidiOut()
midi_out.openPort(1)  # Replace with the correct index of your Launchpad MK2 port

# Function to send SysEx message for setting LED color on Launchpad MK2
def send_sysex_message(pad, red, green, blue):
    sysex = [
        0xF0, 0x00, 0x20, 0x29, 0x02, 0x18, 0x0B,  # SysEx header for Launchpad MK2
        pad,                                       # Pad number (11 to 19 for bottom row)
        red, green, blue,                          # RGB values (0-63)
        0xF7                                       # End of SysEx
    ]
    sysex_bytes = bytes(sysex)
    message = rtmidi.MidiMessage(sysex_bytes)  # Create MidiMessage object
    midi_out.sendMessage(message)              # Send the message

# Function to blink LEDs on bottom row (pads 11 to 19) of Launchpad MK2
def blink_bottom_row():
    pads = list(range(11, 20))  # Pads 11 to 19 (bottom row)
    try:
        while True:
            # Turn on all LEDs
            for pad in pads:
                send_sysex_message(pad, 63, 63, 63)
            time.sleep(0.5)  # LED on time

            # Turn off all LEDs
            for pad in pads:
                send_sysex_message(pad, 0, 0, 0)
            time.sleep(0.5)  # LED off time
    
    except KeyboardInterrupt:
        # Handle Ctrl+C to exit gracefully
        print("\nStopping the LED blink.")
        # Turn off all pads before exiting
        for pad in pads:
            send_sysex_message(pad, 0, 0, 0)
        midi_out.close()

# Start blinking LEDs on bottom row (pads 11 to 19) of Launchpad MK2
blink_bottom_row()
