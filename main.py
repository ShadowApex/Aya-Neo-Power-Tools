import time
import os
import json
import asyncio

from subprocess import Popen, PIPE, STDOUT

VERSION = "0.0.1"
SETTINGS_LOCATION = "~/.config/settings.json"
LOG_LOCATION = "/tmp/ayaneoptools.log"
FANTASTIC_INSTALL_DIR = "~/homebrew/plugins/Fantastic"
HOME_DIR = os.getenv('HOME')
import logging

logging.basicConfig(
    filename = LOG_LOCATION,
    format = '%(asctime)s %(levelname)s %(message)s',
    filemode = 'w',
    force = True)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logging.info(f"Aya Neo Power Tools v{VERSION} https://github.com/pastaq/Aya-Neo-Power-Tools")
startup_time = time.time()


class Plugin:
    
    persistent = True
    modified_settings = False
    
    async def get_version(self) -> str:
        return VERSION

    # GPU stuff
    async def set_gpu_prop(self, value: int, prop: str) -> bool:
        self.modified_settings = True
        write_gpu_prop(prop, value)
        return True

    async def get_gpu_prop(self, prop: str) -> int:
        return read_gpu_prop(prop)

    # Battery stuff
    async def get_charge_now(self) -> int:
        return int(read_from_sys("/sys/class/hwmon/hwmon2/device/energy_now", amount=-1).strip())

    async def get_charge_full(self) -> int:
        return int(read_from_sys("/sys/class/hwmon/hwmon2/device/energy_full", amount=-1).strip())

    async def get_charge_design(self) -> int:
        return int(read_from_sys("/sys/class/hwmon/hwmon2/device/energy_full_design", amount=-1).strip())

    # Asyncio-compatible long-running code, executed in a task when the plugin is loaded
    async def _main(self):
        # startup: load & apply settings
        if os.path.exists(SETTINGS_LOCATION):
            settings = read_json(SETTINGS_LOCATION)
            logging.debug(f"Loaded settings from {SETTINGS_LOCATION}: {settings}")
        else:
            settings = None
            logging.debug(f"Settings {SETTINGS_LOCATION} does not exist, skipped")
        if settings is None or settings["persistent"] == False:
            logging.debug("Ignoring settings from file")
            self.persistent = False

        else:
            # apply settings
            logging.debug("Restoring settings from file")
            self.persistent = True
            
            # GPU
            write_gpu_prop("b", settings["gpu"]["slowppt"])
            write_gpu_prop("c", settings["gpu"]["fastppt"])

    # called from main_view::onViewReady
    async def on_ready(self):
        delta = time.time() - startup_time
        logging.info(f"Front-end initialised {delta}s after startup")

    # persistence
    async def get_persistent(self) -> bool:
        return self.persistent

    async def set_persistent(self, enabled: bool):
        logging.debug(f"Persistence is now: {enabled}")
        self.persistent = enabled
        self.save_settings(self)

    def current_settings(self) -> dict:
        settings = dict()
        settings["gpu"] = self.current_gpu_settings(self)
        settings["persistent"] = self.persistent
        return settings

    def current_gpu_settings(self) -> dict:
        settings = dict()
        settings["slowppt"] = read_gpu_prop("PPT LIMIT SLOW")
        settings["fastppt"] = read_gpu_prop("PPT LIMIT FAST")
        return settings

    def save_settings(self):
        settings = self.current_settings(self)
        logging.info(f"Saving settings to file: {settings}")
        write_json(SETTINGS_LOCATION, settings)

def read_gpu_prop(prop: str) -> int:
    val = 0

    # Gets the current setting for the property requested
    args = ("sudo "+HOME_DIR+"/homebrew/plugins/Aya-Neo-Power-Tools/bin/ryzenadj --info")
    ryzenadj = Popen(args, shell=True, stdout=PIPE, stderr=STDOUT)
    output = ryzenadj.stdout.read()
    all_props = output.split(b'\n')

    for prop_row in all_props:
        current_row = str(prop_row)
        if prop in current_row:
            row_list = current_row.split("|")
            val = int(float(row_list[2].strip()))
            break

    return val

def write_gpu_prop(prop: str, value: int):
    args = ("sudo "+HOME_DIR+"/homebrew/plugins/Aya-Neo-Power-Tools/bin/ryzenadj -"+prop+" "+str(value))
    ryzenadj = Popen(args, shell=True, stdout=PIPE, stderr=STDOUT)
    output = ryzenadj.stdout.read()

def write_to_sys(path, value: int):
    with open(path, mode="w") as f:
        f.write(str(value))
    logging.debug(f"Wrote `{value}` to {path}")

def read_from_sys(path, amount=1):
    with open(path, mode="r") as f:
        value = f.read(amount)
        logging.debug(f"Read `{value}` from {path}")
        return value

def read_sys_int(path) -> int:
    return int(read_from_sys(path, amount=-1).strip())

def write_json(path, data):
    with open(path, mode="w") as f:
        json.dump(data, f) # I always guess which is which param and I hate it

def read_json(path):
    with open(path, mode="r") as f:
        return json.load(f)

os_release = read_from_sys("/etc/os-release", amount=-1).strip()
logging.info(f"/etc/os-release\n{os_release}")
