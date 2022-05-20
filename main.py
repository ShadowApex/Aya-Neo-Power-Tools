import time
import os
import json
import asyncio

from pathlib import Path
from subprocess import Popen, PIPE, STDOUT

VERSION = "0.0.1"
HOME_DIR = os.getenv('HOME')
SETTINGS_LOCATION = HOME_DIR+"/.config/neo_power_settings.json"
LOG_LOCATION = "/tmp/neo_power_tools.log"
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
    tdp_notches = {}
    sys_id = None

    async def get_tdp_notches(self):

        if not self.sys_id:
            self.sys_id = read_sys_id()

        # Founders & 2021 MAX TDP 25W, increment by 3W
        if self.sys_id in [
                "AYANEO 2021",
                "AYA NEO 2021",
                "AYANEO FOUNDERS",
                "AYA NEO FOUNDERS",
                "AYANEO FOUNDER",
                "AYA NEO FOUNDER",
                ]:
            self.tdp_notches["tdp_notch0_val"] = 7
            self.tdp_notches["tdp_notch1_val"] = 10
            self.tdp_notches["tdp_notch2_val"] = 13
            self.tdp_notches["tdp_notch3_val"] = 16
            self.tdp_notches["tdp_notch4_val"] = 19
            self.tdp_notches["tdp_notch5_val"] = 22
            self.tdp_notches["tdp_notch6_val"] = 25

        # 2021 Pro MAX TDP 30W, increment by 3/4W
        elif self.sys_id in [
                "AYANEO 2021 Pro Retro Power",
                "AYA NEO 2021 Pro Retro Power",
                "AYANEO 2021 Pro",
                "AYA NEO 2021 Pro",
                ]:
            self.tdp_notches["tdp_notch0_val"] = 7
            self.tdp_notches["tdp_notch1_val"] = 10
            self.tdp_notches["tdp_notch2_val"] = 14
            self.tdp_notches["tdp_notch3_val"] = 18
            self.tdp_notches["tdp_notch4_val"] = 22
            self.tdp_notches["tdp_notch5_val"] = 26
            self.tdp_notches["tdp_notch6_val"] = 30

        # NEXT max TDP 32W, increment by 6/4W
        elif self.sys_id in [
                "NEXT",
                "AYANEO NEXT",
                "AYA NEO NEXT",
                "NEXT Pro",
                "AYANEO NEXT Pro",
                "AYA NEO NEXT Pro",
                ]:
            self.tdp_notches["tdp_notch0_val"] = 7
            self.tdp_notches["tdp_notch1_val"] = 10
            self.tdp_notches["tdp_notch2_val"] = 14
            self.tdp_notches["tdp_notch3_val"] = 18
            self.tdp_notches["tdp_notch4_val"] = 22
            self.tdp_notches["tdp_notch5_val"] = 28
            self.tdp_notches["tdp_notch6_val"] = 32

        return self.tdp_notches

    # Label Stuff
    async def get_version(self) -> str:
        return VERSION

    async def get_sys_id(self) -> str:
        if not self.sys_id:
            self.sys_id = read_sys_id()
        return self.sys_id

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
            logging.info(f"Loaded settings from {SETTINGS_LOCATION}: {settings}")
        else:
            settings = None
            logging.info(f"Settings {SETTINGS_LOCATION} does not exist, skipped")

        if settings is None or settings["persistent"] == False:
            logging.info("Ignoring settings from file")
            self.persistent = False

        else:
            # apply settings
            logging.info("Restoring settings from file")
            self.persistent = True
            logging.info(settings)
            # GPU
            write_gpu_prop("b", settings["gpu"]["slowppt"])
            write_gpu_prop("c", settings["gpu"]["fastppt"])

    # called from main_view::onViewReady
    async def on_ready(self):
        delta = time.time() - startup_time
        logging.info(f"Front-end initialised {delta}s after startup")

    # persistence
    async def get_persistent(self) -> bool:
        print("We are persistent: ", self.persistent)
        return self.persistent

    async def set_persistent(self, enabled: bool):
        logging.info(f"Persistence is now: {enabled}")
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
        if not os.path.exists(SETTINGS_LOCATION):
            settings_file = Path(SETTINGS_LOCATION)
            settings_file.touch()

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

    # Protect against exploits from JS at runtime.
    if type(value) != int:
        raise TypeError("TypeError. value is of type " +type(value)+", not 'int'")
        return

    value *= 1000
    args = ("sudo "+HOME_DIR+"/homebrew/plugins/Aya-Neo-Power-Tools/bin/ryzenadj -"+prop+" "+str(value))
    ryzenadj = Popen(args, shell=True, stdout=PIPE, stderr=STDOUT)
    output = ryzenadj.stdout.read()

def write_to_sys(path, value: int):
    with open(path, mode="w") as f:
        f.write(str(value))
    logging.info(f"Wrote `{value}` to {path}")

def read_from_sys(path, amount=1):
    with open(path, mode="r") as f:
        value = f.read(amount)
        logging.info(f"Read `{value}` from {path}")
        return value

def read_sys_id() -> str:
        return open("/sys/devices/virtual/dmi/id/product_name", "r").read().strip()

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
