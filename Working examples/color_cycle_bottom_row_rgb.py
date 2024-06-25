import time
import rtmidi

# Open the MIDI output port for the Launchpad MK2
midi_out = rtmidi.RtMidiOut()
midi_out.openPort(1)  # Replace with the correct index of your Launchpad MK2 port

# Function to send SysEx message for setting LED color on Launchpad MK2
def send_sysex_message(led, red, green, blue):
    sysex = [
        0xF0, 0x00, 0x20, 0x29, 0x02, 0x18, 0x0B,  # SysEx header for Launchpad MK2
        led,                                       # LED index (11 to 19 for bottom row)
        red, green, blue,                          # RGB values (0-63)
        0xF7                                       # End of SysEx
    ]
    sysex_bytes = bytes(sysex)
    message = rtmidi.MidiMessage(sysex_bytes)  # Create MidiMessage object
    midi_out.sendMessage(message)              # Send the message

# Function to cycle full RGB colors on bottom row (pads 11 to 19) of Launchpad MK2
def cycle_full_rgb_colors():
    pads = list(range(11, 20))  # Pads 11 to 19 (bottom row)
    try:
        while True:
            for color_value in range(64):  # 0 to 63 (0 to 100% brightness)
                for pad in pads:
                    # Calculate RGB values for current color_value
                    red = color_value
                    green = (color_value + 21) % 64
                    blue = (color_value + 42) % 64

                    # Send SysEx message to set pad color
                    send_sysex_message(pad, red, green, blue)
                    time.sleep(0.002)  # Adjust sleep time for desired speed
    
    except KeyboardInterrupt:
        # Handle Ctrl+C to exit gracefully
        print("\nStopping the color cycle.")
        # Turn off all pads before exiting
        for pad in pads:
            send_sysex_message(pad, 0, 0, 0)
        midi_out.close()

# Start cycling full RGB colors on bottom row (pads 11 to 19) of Launchpad MK2
cycle_full_rgb_colors()
