import pyautogui
import asyncio
import logging
import subprocess
import pytesseract
from PIL import ImageGrab
from livekit.agents import function_tool

# Enable tesseract path (Adjust if installed in custom location)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# ========================= HELPERS ==========================

KEY_MAP = {
    "enter": "enter", "space": "space",
    "tab": "tab", "esc": "esc", "escape": "esc",
    "backspace": "backspace", "delete": "delete",
    "up": "up", "down": "down", "left": "left", "right": "right"
}

def normalize_key(key: str):
    key = key.strip().lower()
    return KEY_MAP.get(key, key)


def speak(msg):
    print(f"🎤 JARVIS: {msg}")
    return f"JARVIS: {msg}"


# ========================= CORE TOOLS ==========================

@function_tool()
async def type_text(text: str, fast: bool = False, interval: float = 0.05) -> str:
    speed = 0 if fast else interval
    await asyncio.to_thread(pyautogui.typewrite, text, interval=speed)
    return speak(f"Typed '{text}'")


@function_tool()
async def press_key(key: str) -> str:
    k = normalize_key(key)
    await asyncio.to_thread(pyautogui.press, k)
    return speak(f"Pressed {key}")


@function_tool()
async def hotkey(keys: str) -> str:
    key_list = [normalize_key(k) for k in keys.split("+")]
    await asyncio.to_thread(pyautogui.hotkey, *key_list)
    return speak(f"Executed '{keys}' shortcut")


@function_tool()
async def move_mouse(x: int, y: int, duration: float = 0.2) -> str:
    await asyncio.to_thread(pyautogui.moveTo, x, y, duration=duration)
    return speak(f"Moved mouse to {x},{y}")


@function_tool()
async def click_mouse(x: int = None, y: int = None, button: str = "left") -> str: # type: ignore
    await asyncio.to_thread(pyautogui.click, x, y, button=button) if x and y else await asyncio.to_thread(pyautogui.click, button=button)
    return speak(f"Clicked {button} button")


@function_tool()
async def scroll(amount: int = 500) -> str:
    await asyncio.to_thread(pyautogui.scroll, amount)
    direction = "down" if amount < 0 else "up"
    return speak(f"Scrolled {direction}")


# ========================= AI EYES (OCR) ==========================

@function_tool()
async def read_screen(region: str = "full") -> str:
    """
    region example: "0,0,800,600" or "full"
    """
    if region == "full":
        img = ImageGrab.grab()
    else:
        x, y, w, h = map(int, region.split(","))
        img = ImageGrab.grab(bbox=(x, y, w, h))

    text = pytesseract.image_to_string(img)
    return speak(f"Screen text detected: {text.strip()[:200]}")


# ========================= MACRO COMMANDS ==========================

@function_tool()
async def open_app(app: str) -> str:
    known = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "cmd": "cmd.exe",
        "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "spotify": r"C:\Users\%USERNAME%\AppData\Roaming\Spotify\Spotify.exe",
    }

    exe = known.get(app.lower())
    if not exe:
        return speak(f"Unknown app: {app}")

    try:
        subprocess.Popen(exe)
        return speak(f"Opening {app}")
    except Exception:
        return speak(f"Failed to open {app}")


@function_tool()
async def macro(command: str) -> str:
    """
    Smart AI Tasks - natural language
    examples:
      - "open notepad and write hello world"
      - "open chrome and search AI news"
      - "open cmd and type ipconfig"
    """

    text = command.lower()

    if "open notepad" in text:
        await open_app("notepad")
        await asyncio.sleep(1)
        to_type = text.split("write")[-1].strip() if "write" in text else ""
        if to_type:
            await type_text(to_type)
        return speak("Task completed")

    if "open chrome" in text and "search" in text:
        query = text.split("search")[-1].strip()
        await open_app("chrome")
        await asyncio.sleep(2)
        await type_text(query)
        await press_key("enter")
        return speak("Search completed")

    return speak("Macro understood but not programmed yet")
