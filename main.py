import time
import board
import neopixel
import math
import pandas as pd
import threading
import re

# ------------------------------
# Configuration Parameters
# ------------------------------

# Define the number of LEDs and the GPIO pin
LED_COUNT = 60          # Number of LED pixels.
LED_PIN = board.D18     # GPIO pin connected to the pixels (must support PWM!).

# Paths to the data files
SKU_EXCEL_FILE_PATH = "/home/anapi01/Downloads/test_sku.xlsx"
SALES_ORDER_CSV_PATH = "/home/anapi01/WS2812B_test/sales_order.csv"

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

# Dictionary to keep track of active breathing threads
active_threads = {}
thread_lock = threading.Lock()

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

def breathe_effect(color_name, address_list, duration=BREATH_DURATION, fps=FPS, stop_event=None, thread_id=None):
    """
    Apply a breathing (fade in and out) effect to specified LEDs.

    :param color_name: The name of the color for the breathing effect.
    :param address_list: A list of LED indices to apply the effect on.
    :param duration: Total duration for one breath cycle (seconds).
    :param fps: Frames per second for smoothness.
    :param stop_event: threading.Event to signal stopping the effect.
    :param thread_id: Unique identifier for the thread.
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
    reset_leds(address_list, thread_id)
    print(f"\n[Info] Breathing effect for Thread ID {thread_id} stopped and specified LEDs turned off.")

def reset_leds(address_list, thread_id=None):
    """
    Turn off the specified LEDs.

    :param address_list: A list of LED indices to turn off.
    :param thread_id: Unique identifier for the thread (optional).
    """
    for addr in address_list:
        if 0 <= addr < LED_COUNT:
            pixels[addr] = (0, 0, 0)
    pixels.show()
    if thread_id is not None:
        print(f"[Info] LEDs {address_list} turned off by Thread ID {thread_id}.")

def find_address_by_sku(df_sku, sku_input):
    """
    Find LED addresses corresponding to a given SKU.

    :param df_sku: Pandas DataFrame containing SKU and Address mappings.
    :param sku_input: SKU string entered by the user.
    :return: List of LED addresses if found, else None.
    """
    sku_input_lower = sku_input.lower()
    matching_rows = df_sku[df_sku["Label"].str.lower() == sku_input_lower]

    if matching_rows.empty:
        print("[Info] No SKU match found.")
        return None
    else:
        # Assuming 'Address' column contains integer indices
        addresses = matching_rows["Address"].tolist()
        print(f"[Info] Found address(es) for SKU '{sku_input}': {addresses}")
        return addresses

def find_skus_by_sales_order(df_order, sales_order_id):
    """
    Find SKUs corresponding to a given Sales Order ID.

    :param df_order: Pandas DataFrame containing Sales Order ID and SKU mappings.
    :param sales_order_id: Sales Order ID entered by the user.
    :return: List of SKUs if found, else None.
    """
    matching_rows = df_order[df_order["id"].astype(str) == str(sales_order_id)]

    if matching_rows.empty:
        print("[Info] No Sales Order match found.")
        return None
    else:
        skus = matching_rows["sku"].tolist()
        print(f"[Info] Found SKU(s) for Sales Order ID '{sales_order_id}': {skus}")
        return skus

def handle_input(df_sku, df_order):
    """
    Handle user input, determine if it's a SKU or Sales Order ID, and initiate breathing effects accordingly.

    :param df_sku: Pandas DataFrame containing SKU and Address mappings.
    :param df_order: Pandas DataFrame containing Sales Order ID and SKU mappings.
    """
    global active_threads, thread_lock

    user_input = input("Enter SKU or Sales Order ID (or type 'exit' to quit): ").strip()

    if user_input.lower() == 'exit':
        print("Exiting program.")
        return 'exit'

    # Determine if input is Sales Order ID (numeric) or SKU (alphanumeric)
    if user_input.isdigit():
        # Input is Sales Order ID
        sales_order_id = user_input
        skus = find_skus_by_sales_order(df_order, sales_order_id)

        if skus is None:
            return None

        # Find all LED addresses for the SKUs in this sales order
        all_addresses = []
        for sku in skus:
            addresses = find_address_by_sku(df_sku, sku)
            if addresses:
                all_addresses.extend(addresses)

        if not all_addresses:
            print("[Info] No LED addresses found for the SKUs in this Sales Order.")
            return None

        # Start breathing effect for each unique SKU with its own color
        # Assuming each SKU has a unique color, else assign a default color
        for sku in skus:
            addresses = find_address_by_sku(df_sku, sku)
            if addresses:
                # You can define a default color or map SKU to specific colors if needed
                # Here, we'll use "White" for sales order breathing
                breath_color = "White"
                with thread_lock:
                    # Generate a unique thread ID
                    thread_id = len(active_threads) + 1
                    # Create stop event for the thread
                    stop_event = threading.Event()
                    # Start the breathing effect thread
                    thread = threading.Thread(
                        target=breathe_effect,
                        args=(breath_color, addresses, BREATH_DURATION, FPS, stop_event, thread_id),
                        daemon=True
                    )
                    thread.start()
                    # Store thread information
                    active_threads[thread_id] = {
                        'thread': thread,
                        'stop_event': stop_event
                    }
                    print(f"[Info] Started breathing effect Thread ID {thread_id} for Sales Order ID {sales_order_id}.")

    else:
        # Input is SKU
        sku_input = user_input
        addresses = find_address_by_sku(df_sku, sku_input)

        if addresses is None:
            return None

        # Define the color for the breathing effect
        breath_color = "White"  # You can modify this or make it dynamic

        # Start breathing effect for the SKU
        with thread_lock:
            # Generate a unique thread ID
            thread_id = len(active_threads) + 1
            # Create stop event for the thread
            stop_event = threading.Event()
            # Start the breathing effect thread
            thread = threading.Thread(
                target=breathe_effect,
                args=(breath_color, addresses, BREATH_DURATION, FPS, stop_event, thread_id),
                daemon=True
            )
            thread.start()
            # Store thread information
            active_threads[thread_id] = {
                'thread': thread,
                'stop_event': stop_event
            }
            print(f"[Info] Started breathing effect Thread ID {thread_id} for SKU '{sku_input}'.")

def stop_all_breathing_effects():
    """
    Stop all active breathing effect threads and turn off their LEDs.
    """
    global active_threads, thread_lock

    with thread_lock:
        for thread_id, info in active_threads.items():
            print(f"[Info] Stopping breathing effect Thread ID {thread_id}...")
            info['stop_event'].set()

        # Wait for all threads to finish
        for thread_id, info in active_threads.items():
            info['thread'].join()
            reset_leds([])  # Ensure all LEDs are turned off

        # Clear the active_threads dictionary
        active_threads.clear()
        print("[Info] All breathing effects stopped.")

def main():
    global active_threads, thread_lock

    # Load the SKU Excel file into a DataFrame
    try:
        df_sku = pd.read_excel(SKU_EXCEL_FILE_PATH)
    except FileNotFoundError:
        print(f"[Error] Excel file not found at path: {SKU_EXCEL_FILE_PATH}")
        return
    except Exception as e:
        print(f"[Error] An error occurred while reading the Excel file: {e}")
        return

    # Load the Sales Order CSV file into a DataFrame
    try:
        df_order = pd.read_csv(SALES_ORDER_CSV_PATH, dtype={'id': str, 'sku': str})
    except FileNotFoundError:
        print(f"[Error] CSV file not found at path: {SALES_ORDER_CSV_PATH}")
        return
    except Exception as e:
        print(f"[Error] An error occurred while reading the CSV file: {e}")
        return

    print("=== WS2812B LED Control ===")
    print("Available colors:", ", ".join(COLOR_MAP.keys()))
    print("Type 'exit' to quit the program.\n")

    try:
        while True:
            handle = handle_input(df_sku, df_order)
            if handle == 'exit':
                break
    except KeyboardInterrupt:
        print("\n[Info] KeyboardInterrupt received. Exiting...")
    finally:
        # Stop all breathing effects and turn off LEDs
        stop_all_breathing_effects()

if __name__ == "__main__":
    main()
