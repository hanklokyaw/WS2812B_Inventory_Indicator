import time
import board
import neopixel
import math

# ------------------------------
# Configuration Parameters
# ------------------------------

# Define the number of LEDs and the GPIO pin
LED_COUNT = 55          # Number of LED pixels.
LED_PIN = board.D18     # GPIO pin connected to the pixels (must support PWM!).

# Initialize the NeoPixel strip.
pixels = neopixel.NeoPixel(
    LED_PIN, LED_COUNT, brightness=1.0, auto_write=False, pixel_order=neopixel.GRB
)

# Color dictionary for easy color lookup
COLOR_MAP = {
    "Orange": (255, 165, 0),
    "White": (255, 255, 255),
    "Blue": (0, 0, 255),
    "Green": (0, 255, 0),
    "Red": (255, 0, 0),
    "Purple": (128, 0, 128)
}

# Breathing effect parameters
FPS = 30              # Frames per second for smoothness
BREATH_DURATION = 5   # Duration for one complete breath cycle (seconds)

# ------------------------------
# Function Definitions
# ------------------------------

def set_led_color(color_name, address_list):
    """
    Set specified LEDs to a given color.

    :param color_name: The name of the color (e.g., "Orange", "White", "Blue", "Green", "Red", "Purple").
    :param address_list: A list of LED indices to set the color on.
    """
    # Validate color name
    if color_name not in COLOR_MAP:
        print(f"[Error] Color '{color_name}' not recognized. Available colors: {', '.join(COLOR_MAP.keys())}")
        return

    # Retrieve the RGB tuple for the given color
    color = COLOR_MAP[color_name]

    # Apply the color to each specified LED
    for addr in address_list:
        if 0 <= addr < LED_COUNT:
            pixels[addr] = color
        else:
            print(f"[Warning] LED index {addr} is out of range (0 to {LED_COUNT - 1}).")

    # Update the LED strip to show the changes
    pixels.show()

def breathe_effect(color_name, address_list, duration=BREATH_DURATION, fps=FPS):
    """
    Apply a breathing (fade in and out) effect to specified LEDs.

    :param color_name: The name of the color for the breathing effect.
    :param address_list: A list of LED indices to apply the effect on.
    :param duration: Total duration for one breath cycle (seconds).
    :param fps: Frames per second for smoothness.
    """
    # Validate color name
    if color_name not in COLOR_MAP:
        print(f"[Error] Color '{color_name}' not recognized. Available colors: {', '.join(COLOR_MAP.keys())}")
        return

    # Calculate the total number of steps for the breathing cycle
    total_steps = duration * fps

    try:
        while True:
            for step in range(total_steps):
                # Calculate brightness using a sine wave for smooth transitions
                brightness = (math.sin(math.pi * step / (total_steps / 2)) + 1) / 2  # Normalized between 0 and 1

                # Calculate the current color with adjusted brightness
                base_color = COLOR_MAP[color_name]
                current_color = tuple(int(c * brightness) for c in base_color)

                # Apply the current color to the specified LEDs
                for addr in address_list:
                    if 0 <= addr < LED_COUNT:
                        pixels[addr] = current_color
                    else:
                        print(f"[Warning] LED index {addr} is out of range (0 to {LED_COUNT - 1}).")

                # Update the LED strip to show the changes
                pixels.show()

                # Control the update rate
                time.sleep(1 / fps)

    except KeyboardInterrupt:
        # Gracefully turn off the specified LEDs on exit
        for addr in address_list:
            if 0 <= addr < LED_COUNT:
                pixels[addr] = (0, 0, 0)
        pixels.show()
        print("\nBreathing effect stopped and specified LEDs turned off.")

# ------------------------------
# Example Usage
# ------------------------------

if __name__ == "__main__":
    # Define the LEDs you want to apply the breathing effect to
    target_leds = [10, 12]

    # Define the color for the breathing effect
    breath_color = "Green"

    # Start the breathing effect
    breathe_effect(breath_color, target_leds, duration=5, fps=30)
    
