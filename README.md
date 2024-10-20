# Inventory Tipout Bin Indicator

This project is an inventory tipout bin indicator system using a WS2812B addressable LED strip and a barcode scanner. The system is designed to work with a Raspberry Pi 4 and uses Python to light up the corresponding bin when a barcode is scanned.

## Requirements

1. **Hardware:**
   - Raspberry Pi 4
   - WS2812B addressable LED strip
   - Barcode scanner
   - Power supply suitable for both the Raspberry Pi and LED strip

2. **Software:**
   - Raspbian OS (latest version)
   - Python 3.x
   - Virtual environment setup for Python

## Libraries and Dependencies

Ensure that you have the following libraries installed in your virtual environment:

- `neopixel`
- `board`
- `pandas`
- `openpyxl` (required for reading Excel files)
- `RPi.GPIO`
- `threading` (built-in)
- `time` (built-in)
- `math` (built-in)

## Installation Steps

### 1. Set up the virtual environment
```bash
sudo apt-get update
sudo apt-get upgrade
sudo apt-get install python3-venv
```

### Create and activate the virtual environment:
```bash
python3 -m venv env
source env/bin/activate
```

### 2. Install required Python libraries
Install the dependencies using pip:
```bash
pip install neopixel rpi_ws281x pandas openpyxl
```

### 3. Enable SPI on your Raspberry Pi
Ensure that SPI is enabled on your Raspberry Pi. You can enable it using:
```bash
sudo raspi-config
```
Navigate to Interfacing Options > SPI and enable it.

## Hardware Setup
1. **Connect the WS2812B LED strip:**
   - Connect the data pin of the LED strip to the GPIO pin defined in your code (board.D18).
   - Provide a proper power supply to the LED strip.
2. **Barcode Scanner:**
   - Connect the barcode scanner to your Raspberry Pi (either via USB or GPIO).

## Running the Application
1. **Ensure the virtual environment is active:**
```bash
source env/bin/activate
```

2. **Run the script:**
```bash
python your_script_name.py
```

## How to Use
1. **Input Instructions:**
   - To scan a SKU, enter the SKU code (e.g., ED-BB-TI-16g-D3).
   - To scan a Sales Order ID, enter the numeric ID (e.g., 101536679).

2. The corresponding bin (LEDs) will light up according to the SKU or Sales Order scanned.
3. **Exit the Application:**
   - Type exit to stop the program.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Troubleshooting
- If you face issues with LED lighting, check the connections and ensure that the correct GPIO pin is defined in the script.
- Ensure the SKU and Sales Order files are in the correct path as mentioned in the code.
