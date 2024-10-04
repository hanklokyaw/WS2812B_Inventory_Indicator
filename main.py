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

# Paths to the mapping files
SKU_EXCEL_FILE_PATH = "/home/anapi01/Downloads/test_sku.xlsx"
SALES_ORDER_CSV_PATH = "/home/anapi01/Downloads/sales_order.csv"

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

# Threads and stop events for SKU and Sales Order breathing effects
sku_thread = None
sku_stop_event = threading.Event()

so_thread = None
so_stop_event = threading.Event()

# Lock to manage access to NeoPixel strip
pixels_lock = threading.Lock()

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
    with pixels_lock:
        for addr in address_list:
            if 0 <= addr < LED_COUNT:
                pixels[addr] = color
            else:
                print(f"[Warning] LED index {addr} is out of range (0 to {LED_COUNT - 1}).")

        # Update the LED strip to show the changes
        pixels.show()

def breathe_effect(color_name, address_list, duration=BREATH_DURATION, fps=FPS, stop_event=threading.Event()):
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
            with pixels_lock:
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
    print(f"\nBreathing effect for color '{color_name}' on LEDs {address_list} stopped and turned off.")

def reset_leds(address_list):
    """
    Turn off the specified LEDs.

    :param address_list: A list of LED indices to turn off.
    """
    with pixels_lock:
        for addr in address_list:
            if 0 <= addr < LED_COUNT:
                pixels[addr] = (0, 0, 0)
        pixels.show()

def find_addresses(sku_df, so_df, user_input):
    """
    Determine if the user input is a SKU or Sales Order ID and retrieve corresponding LED addresses.

    :param sku_df: DataFrame containing SKU to Address mappings.
    :param so_df: DataFrame containing Sales Order to SKU mappings.
    :param user_input: The input entered by the user.
    :return: Tuple (type, addresses) where type is 'sku' or 'so' and addresses is a list of LED indices.
    """
    # Check if input is a Sales Order ID (assuming it's all digits)
    if user_input.isdigit():
        # Treat as Sales Order ID
        matching_rows = so_df[so_df["id"] == user_input]
        if matching_rows.empty:
            print("[Info] No Sales Order match found.")
            return (None, None)
        else:
            # Retrieve all SKUs associated with this Sales Order
            skus = matching_rows["sku"].tolist()
            addresses = []
            for sku in skus:
                sku_match = sku_df[sku_df["Label"].str.lower() == sku.lower()]
                if not sku_match.empty:
                    addr = sku_match["Address"].tolist()
                    addresses.extend(addr)
                else:
                    print(f"[Warning] SKU '{sku}' in Sales Order '{user_input}' not found in SKU mapping.")
            if not addresses:
                print(f"[Info] No valid LED addresses found for Sales Order '{user_input}'.")
                return (None, None)
            return ('so', addresses)
    else:
        # Treat as SKU
        sku_match = sku_df[sku_df["Label"].str.lower() == user_input.lower()]
        if sku_match.empty:
            print("[Info] No SKU match found.")
            return (None, None)
        else:
            addresses = sku_match["Address"].tolist()
            return ('sku', addresses)

# ------------------------------
# Main Loop
# ------------------------------

def main():
    global sku_thread, sku_stop_event, so_thread, so_stop_event

    # Load the SKU and Sales Order files into DataFrames
    try:
        sku_df = pd.read_excel(SKU_EXCEL_FILE_PATH)
    except FileNotFoundError:
        print(f"[Error] SKU Excel file not found at path: {SKU_EXCEL_FILE_PATH}")
        return
    except Exception as e:
        print(f"[Error] An error occurred while reading the SKU Excel file: {e}")
        return

    try:
        so_df = pd.read_csv(SALES_ORDER_CSV_PATH)
    except FileNotFoundError:
        print(f"[Error] Sales Order CSV file not found at path: {SALES_ORDER_CSV_PATH}")
        return
    except Exception as e:
        print(f"[Error] An error occurred while reading the Sales Order CSV file: {e}")
        return

    print("=== WS2812B LED Control ===")
    print("Available colors:", ", ".join(COLOR_MAP.keys()))
    print("Type 'exit' to quit the program.\n")
    print("Instructions:")
    print("- To scan a SKU, enter the SKU code (e.g., ED-BB-TI-16g-D3).")
    print("- To scan a Sales Order ID, enter the numeric ID (e.g., 101536679).\n")

    while True:
        user_input = input("Enter SKU or Sales Order ID (or type 'exit' to quit): ").strip()

        if user_input.lower() == 'exit':
            print("Exiting program.")
            break

        input_type, addresses = find_addresses(sku_df, so_df, user_input)

        if addresses is None:
            continue  # Invalid input, prompt again

        if input_type == 'sku':
            # Handle SKU breathing effect
            breath_color = "White"  # You can modify this or make it dynamic

            # Stop existing SKU breathing effect if running
            if sku_thread and sku_thread.is_alive():
                print("[Info] Stopping the current SKU breathing effect...")
                sku_stop_event.set()
                sku_thread.join()
                sku_stop_event.clear()

            # Start new SKU breathing effect
            print(f"[Info] Starting breathing effect on SKU LEDs: {addresses} with color: {breath_color}")
            sku_thread = threading.Thread(
                target=breathe_effect,
                args=(breath_color, addresses, BREATH_DURATION, FPS, sku_stop_event),
                daemon=True
            )
            sku_thread.start()

        elif input_type == 'so':
            # Handle Sales Order breathing effect
            breath_color = "Blue"  # Assign a different color for Sales Orders

            # Stop existing Sales Order breathing effect if running
            if so_thread and so_thread.is_alive():
                print("[Info] Stopping the current Sales Order breathing effect...")
                so_stop_event.set()
                so_thread.join()
                so_stop_event.clear()

            # Start new Sales Order breathing effect
            print(f"[Info] Starting breathing effect on Sales Order LEDs: {addresses} with color: {breath_color}")
            so_thread = threading.Thread(
                target=breathe_effect,
                args=(breath_color, addresses, BREATH_DURATION, FPS, so_stop_event),
                daemon=True
            )
            so_thread.start()

    # After exiting the loop, ensure all breathing threads are stopped and LEDs are turned off
    print("[Info] Shutting down all breathing effects...")
    if sku_thread and sku_thread.is_alive():
        sku_stop_event.set()
        sku_thread.join()

    if so_thread and so_thread.is_alive():
        so_stop_event.set()
        so_thread.join()

    reset_leds([])  # Turn off all LEDs
    print("All LEDs turned off. Goodbye!")

if __name__ == "__main__":
    main()
