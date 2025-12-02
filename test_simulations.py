import asyncio
import logging
import os
import shutil
import subprocess
from typing import Optional, List
from livekit.agents import function_tool

try:
    import psutil
except Exception:
    psutil = None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def _run_subprocess(cmd: List[str], shell: bool = False, capture_output: bool = True, text: bool = True):
    """
    Run subprocess and return (returncode, stdout, stderr). Logs command.
    """
    logger.info(f"[subprocess] Running command: {cmd} (shell={shell})")
    try:
        proc = subprocess.run(cmd, shell=shell, capture_output=capture_output, text=text, check=False)
        logger.info(f"[subprocess] returncode={proc.returncode}")
        if proc.stdout:
            logger.info(f"[subprocess] stdout: {proc.stdout.strip()}")
        if proc.stderr:
            logger.info(f"[subprocess] stderr: {proc.stderr.strip()}")
        return proc.returncode, proc.stdout, proc.stderr
    except Exception as e:
        logger.exception("[subprocess] Exception while running command.")
        return -1, "", str(e)


@function_tool
async def create_folder(path: str) -> str:
    """
    Create a new folder at `path`. If already exists, informs the user.
    """
    try:
        logger.info(f"[create_folder] Requested path: {path}")
        os.makedirs(path, exist_ok=True)
        return f"Folder created or already exists: {path}"
    except Exception as e:
        logger.exception("[create_folder] Error creating folder")
        return f"Error creating folder {path}: {e}"


@function_tool
async def list_folder_items(path: str = ".") -> str:
    """
    List items in the specified folder (non-recursive).
    """
    try:
        logger.info(f"[list_folder_items] Listing path: {path}")
        if not os.path.exists(path):
            return f"Path does not exist: {path}"
        items = os.listdir(path)
        logger.info(f"[list_folder_items] {len(items)} items found.")
        # Return a concise string; LiveKit tools should return serializable simple text/JSON
        if not items:
            return f"No items in {path}"
        return f"Items in {path}:\n" + "\n".join(items[:200])  # limit length in response
    except Exception as e:
        logger.exception("[list_folder_items] Error listing folder")
        return f"Error listing folder {path}: {e}"


@function_tool
async def run_application(name_or_path: str) -> str:
    """
    Try to run an application by name or full path. If not found, says not available.
    Uses shutil.which and common Windows Program Files locations.
    """
    try:
        logger.info(f"[run_application] Request to run: {name_or_path}")

        # If a full path provided and exists, run it
        if os.path.isabs(name_or_path) and os.path.exists(name_or_path):
            logger.info("[run_application] Running absolute path.")
            # Use startfile or subprocess depending on platform
            if os.name == "nt":
                os.startfile(name_or_path)
                return f"Launched {name_or_path}"
            else:
                # POSIX fallback
                _run_subprocess([name_or_path])
                return f"Launched {name_or_path}"

        # Try to locate via PATH
        exe_path = shutil.which(name_or_path)
        if exe_path:
            logger.info(f"[run_application] Found in PATH: {exe_path}")
            if os.name == "nt":
                os.startfile(exe_path)
            else:
                _run_subprocess([exe_path])
            return f"Launched {name_or_path}"
        
        # Try common Windows program directories (best-effort, Windows specific)
        if os.name == "nt":
            program_files = [os.environ.get("ProgramFiles", r"C:\Program Files"), os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")]
            for base in program_files:
                candidate = os.path.join(base, name_or_path)
                if os.path.exists(candidate):
                    logger.info(f"[run_application] Found candidate: {candidate}")
                    os.startfile(candidate)
                    return f"Launched {candidate}"
                # try with exe suffix
                candidate_exe = candidate + ".exe"
                if os.path.exists(candidate_exe):
                    logger.info(f"[run_application] Found candidate exe: {candidate_exe}")
                    os.startfile(candidate_exe)
                    return f"Launched {candidate_exe}"

        logger.warning("[run_application] Application not found")
        return f"Application not available: {name_or_path}"
    except Exception as e:
        logger.exception("[run_application] Error launching application")
        return f"Error launching {name_or_path}: {e}"


@function_tool
async def play_media_file(file_path: str) -> str:
    """
    Play MP3/MP4 (or any file) with the default OS player.
    On Windows uses os.startfile; on POSIX uses 'xdg-open' or 'open' for macOS.
    """
    try:
        logger.info(f"[play_media_file] Requested file: {file_path}")
        if not os.path.exists(file_path):
            return f"File not found: {file_path}"

        if os.name == "nt":
            os.startfile(file_path)
            return f"Playing {file_path} with default application."
        else:
            # POSIX
            opener = shutil.which("xdg-open") or shutil.which("open")
            if opener:
                _run_subprocess([opener, file_path])
                return f"Playing {file_path} with {opener}"
            else:
                return "No system opener found on this OS to play media."
    except Exception as e:
        logger.exception("[play_media_file] Error attempting to play file")
        return f"Error playing {file_path}: {e}"

@function_tool
async def get_battery_percentage() -> str:
    """
    Return battery percentage if available. Uses psutil if installed, otherwise platform fallback on Windows.
    """
    try:
        logger.info("[get_battery_percentage] Called")
        
        # Preferred: psutil
        if psutil:
            batt = psutil.sensors_battery()
            if batt is None:
                logger.warning("No battery detected (possibly a desktop PC).")
                return "Battery info not available on this system (no battery detected)."
            percent = int(batt.percent)
            charging = "charging" if batt.power_plugged else "not charging"
            return f"Battery: {percent}% ({charging})"
        
        # Fallback: Windows WMIC
        if os.name == "nt":
            rc, out, err = _run_subprocess(["wmic", "path", "Win32_Battery", "get", "EstimatedChargeRemaining"], shell=False)
            if rc == 0 and out:
                # Parse the output (WMIC returns a table; extract the number)
                lines = out.strip().split('\n')
                for line in lines[1:]:  # Skip header
                    line = line.strip()
                    if line.isdigit():
                        percent = int(line)
                        return f"Battery: {percent}% (via WMIC)"
            logger.warning(f"WMIC failed: rc={rc}, out='{out}', err='{err}'")
            return "Battery info not available via WMIC (check permissions or try installing psutil)."
        
        # Other OS: No fallback
        return "Battery info not available on this OS (install psutil for support)."
    
    except Exception as e:
        logger.exception("[get_battery_percentage] Error fetching battery info")
        return f"Error fetching battery info: {e}"


@function_tool
async def open_settings() -> str:
    """
    Open system Settings (Windows) or System Preferences (macOS) or try xdg-settings for Linux.
    """
    try:
        logger.info("[open_settings] Opening system settings")
        if os.name == "nt":
            # ms-settings: URI opens Windows Settings
            _run_subprocess(["start", "ms-settings:"], shell=True)
            return "Opening Windows Settings..."
        else:
            opener = shutil.which("gnome-control-center") or shutil.which("systemsettings") or shutil.which("xdg-open")
            if opener:
                _run_subprocess([opener])
                return f"Opening settings via {opener}..."
            return "Could not find a settings application on this system."
    except Exception as e:
        logger.exception("[open_settings] Error opening settings")
        return f"Error opening settings: {e}"


@function_tool
async def get_system_info() -> str:
    """
    Return system configuration information. On Windows uses systeminfo. On POSIX uses uname and lsb_release if available.
    """
    try:
        logger.info("[get_system_info] Gathering system information")
        if os.name == "nt":
            rc, out, err = _run_subprocess(["systeminfo"])
            if rc == 0:
                # Limit the size of returned text
                return out[:8000] if out else "No systeminfo output"
            return f"systeminfo failed: {err}"
        else:
            # POSIX fallback
            uname_rc, uname_out, _ = _run_subprocess(["uname", "-a"])
            lsb = ""
            if shutil.which("lsb_release"):
                _, lsb_out, _ = _run_subprocess(["lsb_release", "-a"])
                lsb = "\n" + (lsb_out or "")
            return (uname_out or "") + lsb
    except Exception as e:
        logger.exception("[get_system_info] Error fetching system info")
        return f"Error fetching system info: {e}"


# ---------------------------
# Unsafe operations: placeholders (NOT ENABLED)
# ---------------------------
# The following are intentionally provided as commented examples only.
# I DO NOT EXECUTE or provide runnable code to:
# - automatically enter passwords / unlock the screen
# - programmatically toggle Wi-Fi/Bluetooth system-wide
# - force wake-from-sleep / forcibly reboot / shutdown without explicit user consent

# Example (COMMENTED) — Windows shutdown via subprocess (requires admin):
# subprocess.run(["shutdown", "/s", "/t", "0"], shell=False)

# Example (COMMENTED) — Windows restart:
# subprocess.run(["shutdown", "/r", "/t", "0"], shell=False)

# Example (COMMENTED) — Sleep (suspend) on Windows can be done via PowerShell:
# subprocess.run(["powershell", "-Command", "Start-Sleep -Seconds 1; (Add-Type -AssemblyName System.Windows.Forms); [System.Windows.Forms.Application]::SetSuspendState('Suspend', $false, $false)"])

# These commands can be dangerous and require admin rights. Do NOT run unless you understand them and run with appropriate privileges.

# ---------------------------
# Simple async test runner (when executed directly)
# ---------------------------
if __name__ == "__main__":
    async def main_test():
        print(await create_folder(r"C:\Temp\livekit_test_folder" if os.name == "nt" else "/tmp/livekit_test_folder"))
        print(await list_folder_items("."))
        print(await run_application("notepad" if os.name == "nt" else "gedit"))
        # Replace with a path to an mp3/mp4 on your machine to test
        # print(await play_media_file(r"C:\path\to\sample.mp3"))
        print(await get_battery_percentage())
        print(await open_settings())
        print((await get_system_info())[:1000])  # print first 1000 chars

    asyncio.run(main_test())


