#!/usr/bin/env python3

import os
import time
from datetime import datetime
from rpi_ws281x import Adafruit_NeoPixel, Color
from picamera2 import Picamera2, Preview

# === Constants ===
PHYSICAL_GRID_SIZE = 8
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_INVERT = False
LED_CHANNEL = 0
DEFAULT_BRIGHTNESS = 100
DEFAULT_LED_GRID = 4
DEFAULT_EXPOSURE = 10000
DEFAULT_COLOR = "green"
FOCUS_LED_INDEX = 27  # center of 8x8

# === Globals ===
current_brightness = DEFAULT_BRIGHTNESS
current_led_count = DEFAULT_LED_GRID
current_exposure = DEFAULT_EXPOSURE
current_color = DEFAULT_COLOR
base_path = "/home/fpm/camera_capture2"
current_folder_name = None  # User can set folder name manually

# === Helpers ===
def index(row, col):
    return row * PHYSICAL_GRID_SIZE + col

def get_color(name):
    colors = {
        "white": Color(255, 255, 255),
        "red": Color(255, 0, 0),
        "green": Color(0, 255, 0),
        "blue": Color(0, 0, 255),
        "off": Color(0, 0, 0),
    }
    return colors.get(name.lower(), Color(255, 255, 255))

def turn_off_all_leds():
    for i in range(PHYSICAL_GRID_SIZE ** 2):
        strip.setPixelColor(i, get_color("off"))
    strip.show()

def focus_led_on():
    turn_off_all_leds()
    strip.setBrightness(current_brightness)
    strip.setPixelColor(FOCUS_LED_INDEX, get_color(current_color))
    strip.show()

def capture_sequence():
    turn_off_all_leds()
    n = int(current_led_count ** 0.5)
    start = (PHYSICAL_GRID_SIZE - n) // 2

    global current_folder_name
    if current_folder_name:
        save_dir = os.path.join(base_path, current_folder_name)
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        save_dir = os.path.join(base_path, timestamp)

    os.makedirs(save_dir, exist_ok=True)

    print(f"Saving images to: {save_dir}")
    for row in range(start, start + n):
        for col in range(start, start + n):
            idx = index(row, col)
            print(f"Lighting LED at row {row}, col {col} (index {idx})")

            strip.setBrightness(current_brightness)
            strip.setPixelColor(idx, get_color(current_color))
            strip.show()
            time.sleep(0.3)

            filename = os.path.join(save_dir, f"led_r{row}_c{col}.jpg")
            picam2.capture_file(filename)
            print(f"Captured {filename}")

            strip.setPixelColor(idx, get_color("off"))
            strip.show()
            time.sleep(0.1)

    print("Capture complete.")
    focus_led_on()

# === Init strip ===
LED_COUNT = PHYSICAL_GRID_SIZE ** 2
strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA,
                          LED_INVERT, DEFAULT_BRIGHTNESS, LED_CHANNEL)
strip.begin()

# === Init camera ===
picam2 = Picamera2()
picam2.start_preview(Preview.QT)
picam2.start()
time.sleep(1)
picam2.set_controls({
    "AeEnable": False,
    "ExposureTime": current_exposure,
    "AnalogueGain": 1.0
})

focus_led_on()

# === Command loop ===
print("Live preview active.")
print("Commands:")
print("  brightness <0–255>")
print("  leds <1, 4, 9, ...>")
print("  exposure <μs>")
print("  color <red|green|blue|white>")
print("  folder <folder_name>")
print("  capture")
print("  exit")

while True:
    try:
        user_input = input("> ").strip().lower()

        if user_input in ["exit", "quit"]:
            break

        elif user_input.startswith("brightness"):
            try:
                val = int(user_input.split()[1])
                if 0 <= val <= 255:
                    current_brightness = val
                    focus_led_on()
                else:
                    print("Brightness must be 0–255.")
            except:
                print("Usage: brightness <value>")

        elif user_input.startswith("leds"):
            try:
                val = int(user_input.split()[1])
                n = int(val ** 0.5)
                if n * n == val and n <= PHYSICAL_GRID_SIZE:
                    current_led_count = val
                    print(f"LED grid for capture: {val}")
                else:
                    print("Must be square number ≤ 64.")
            except:
                print("Usage: leds <value>")

        elif user_input.startswith("exposure"):
            try:
                val = int(user_input.split()[1])
                if val > 0:
                    current_exposure = val
                    picam2.set_controls({"ExposureTime": current_exposure})
                    print(f"Exposure set to {val} µs.")
                else:
                    print("Must be positive.")
            except:
                print("Usage: exposure <μs>")

        elif user_input.startswith("color"):
            try:
                val = user_input.split()[1]
                if val in ["red", "green", "blue", "white"]:
                    current_color = val
                    focus_led_on()
                    print(f"Color set to {val}")
                else:
                    print("Invalid color.")
            except:
                print("Usage: color <name>")

        elif user_input.startswith("folder"):
            parts = user_input.split(maxsplit=1)
            if len(parts) == 2 and parts[1].strip():
                current_folder_name = parts[1].strip()
                print(f"Folder name set to: {current_folder_name}")
            else:
                print("Usage: folder <folder_name>")

        elif user_input == "capture":
            capture_sequence()

        else:
            print("Unknown command.")

    except KeyboardInterrupt:
        break

# === Cleanup ===
turn_off_all_leds()
picam2.stop_preview()
picam2.stop()
print("Done.")
