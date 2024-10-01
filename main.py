import time
import board
import neopixel
import math
import pandas as pd
import threading

# ------------------------------
# Configuration Parameters
# ------------------------------

# Define the number of LEDs and the GPIO pin
LED_COUNT = 60          # Number of LED pixels.
LED_PIN = board.D18     # GPIO pin connected to the pixels (must support PWM!).

# Path to the Excel file containing SKU and Address mappings
EXCEL_FILE_PATH = "/home/anapi01/Downloads/test_sku.xlsx"

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
# Global Variables for Thread Management
# ------------------------------

current_effect_thread = None  # Reference to the current breathing thread
stop_event = threading.Event()  # Event to signal the breathing thread to stop

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

def breathe_effect(color_name, address_list, duration=BREATH_DURATION, fps=FPS, stop_event=stop_event):
    """
    Apply a breathing (fade in and out) effect to specified LEDs.

    :param color_name: The name of the color for the breathing effect.
    :param address_list: A list of LED indices to apply the effect on.
    :param duration: Total duration for one breath cycle (seconds).
    :param fps: Frames per second for smoothness.
    :param stop_event: threading.Event to signal stopping the effect.
    """
    # Validate color name
    if color_name not in COLOR_MAP:
        print(f"[Error] Color '{color_name}' not recognized. Available colors: {', '.join(COLOR_MAP.keys())}")
        return

    # Calculate the total number of steps for the breathing cycle
    total_steps = duration * fps

    while not stop_event.is_set():
        for step in range(total_steps):
            if stop_event.is_set():
                break

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

    # Once stop_event is set, ensure LEDs are turned off
    reset_leds(address_list)
    print("\nBreathing effect stopped and specified LEDs turned off.")

def reset_leds(address_list):
    """
    Turn off the specified LEDs.

    :param address_list: A list of LED indices to turn off.
    """
    for addr in address_list:
        if 0 <= addr < LED_COUNT:
            pixels[addr] = (0, 0, 0)
    pixels.show()

def find_address(df):
    """
    Prompt the user to enter a SKU and find the corresponding LED address.

    :param df: Pandas DataFrame containing SKU and Address mappings.
    :return: List of LED addresses if found, else None.
    """
    user_input = input("Enter SKU (or type 'exit' to quit): ").strip().lower()

    if user_input == 'exit':
        return 'exit'

    # Filter the dataframe to get the address(es)
    matching_rows = df[df["Label"].str.lower() == user_input]

    if matching_rows.empty:
        print("[Info] No SKU match found.")
        return None
    else:
        # Assuming 'Address' column contains integer indices
        addresses = matching_rows["Address"].tolist()
        print(f"[Info] Found address(es): {addresses}")
        return addresses

# ------------------------------
# Main Loop
# ------------------------------

def main():
    global current_effect_thread, stop_event

    # Load the Excel file into a DataFrame
    try:
        df = pd.read_excel(EXCEL_FILE_PATH)
    except FileNotFoundError:
        print(f"[Error] Excel file not found at path: {EXCEL_FILE_PATH}")
        return
    except Exception as e:
        print(f"[Error] An error occurred while reading the Excel file: {e}")
        return

    print("=== WS2812B LED Control ===")
    print("Available colors:", ", ".join(COLOR_MAP.keys()))
    print("Type 'exit' to quit the program.\n")

    while True:
        # Find address based on user input SKU
        addresses = find_address(df)

        if addresses == 'exit':
            print("Exiting program.")
            break

        if addresses is not None:
            target_leds = addresses

            # Define the color for the breathing effect
            breath_color = "White"  # You can modify this or make it dynamic

            # Stop the current breathing effect if it's running
            if current_effect_thread and current_effect_thread.is_alive():
                print("[Info] Stopping the current breathing effect...")
                stop_event.set()
                current_effect_thread.join()

                # Reset the stop_event for the next thread
                stop_event.clear()

            # Start a new breathing effect thread
            print(f"[Info] Starting breathing effect on LEDs: {target_leds} with color: {breath_color}")
            current_effect_thread = threading.Thread(
                target=breathe_effect,
                args=(breath_color, target_leds, BREATH_DURATION, FPS, stop_event),
                daemon=True  # Daemonize thread to exit when main program exits
            )
            current_effect_thread.start()

    # After exiting the loop, ensure all LEDs are turned off
    if current_effect_thread and current_effect_thread.is_alive():
        stop_event.set()
        current_effect_thread.join()
    reset_leds([])  # Pass an empty list to avoid turning off any specific LEDs
    print("All LEDs turned off. Goodbye!")

if __name__ == "__main__":
    main()
