import time
import os
import json
import asyncio

VERSION = "0.0.1"
SETTINGS_LOCATION = "~/.config/settings.json"
LOG_LOCATION = "/tmp/ayaneoptools.log"
FANTASTIC_INSTALL_DIR = "~/homebrew/plugins/Fantastic"

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

    async def set_gpu_power(self, value: int, power_number: int) -> bool:
        self.modified_settings = True
        write_gpu_ppt(power_number, value)
        return True

    async def get_gpu_power(self, power_number: int) -> int:
        power = read_gpu_ppt(power_number)
        print("GPU "+power_number+" Level: ", power)
        return(power)
    # Battery stuff

    async def get_charge_now(self) -> int:
        now =int(read_from_sys("/sys/class/hwmon/hwmon2/device/energy_now", amount=-1).strip())
        print("Charge now: ", now)
        return now

    async def get_charge_full(self) -> int:
        full = int(read_from_sys("/sys/class/hwmon/hwmon2/device/energy_full", amount=-1).strip())
        print("Full Charge: ", full)
        return full

    async def get_charge_design(self) -> int:
        design = int(read_from_sys("/sys/class/hwmon/hwmon2/device/energy_full_design", amount=-1).strip())
        print("Design Power: ", design)
        return design


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
            write_gpu_ppt(1, settings["gpu"]["slowppt"])
            write_gpu_ppt(2, settings["gpu"]["fastppt"])
            

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
        settings["slowppt"] = read_gpu_ppt(1)
        settings["fastppt"] = read_gpu_ppt(2)
        return settings

    def save_settings(self):
        settings = self.current_settings(self)
        logging.info(f"Saving settings to file: {settings}")
        write_json(SETTINGS_LOCATION, settings)



# these are stateless (well, the state is not saved internally) functions, so there's no need for these to be called like a class method

def gpu_power_path(power_number: int) -> str:
    return f"/sys/class/hwmon/hwmon4/power{power_number}_cap"

def read_gpu_ppt(power_number: int) -> int:
    return read_sys_int(gpu_power_path(power_number))

def write_gpu_ppt(power_number:int, value: int):
    write_to_sys(gpu_power_path(power_number), value)
    
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
