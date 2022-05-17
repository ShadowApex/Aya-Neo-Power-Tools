# Aya Neo Power Tools

This is a [SteamOS Plugin Loader](https://github.com/SteamDeckHomebrew/PluginLoader) plugin forked from [NGnius/PowerTools](https://github.com/NGnius/PowerTools)that provides TDP control for the Aya Neo line of handheld devices. We utilize the [RyzenAdj](https://github.com/FlyGoat/RyzenAdj) utility to interface with the hardware. 

## What does it do?

- Enable & disable CPU threads & SMT
- Set CPU max frequency and toggle boost
- Set some GPU power parameters (fastPPT & slowPPT)
- Set the fan RPM (unsupported on SteamOS beta)
- Display supplementary battery info
- Keep settings between restarts (stored in `~/.config/powertools.json`)

## License

This is licensed under GNU GPLv3.

## Disclaimer

No guarentee is given by the author that this tool will not damage your device, and your voluntary use of this tool forgoes any liability for damage that may come from this tool, irrespective of its intended use.
While this utility will technically function for all Ryzen Mobile Processors, it is specifically tuned for with the Thermal Design and Power Limits of the Aya Neo family of devices in mind.
This tool is not officially licensed by or directly associated with AYA NEO or any of its employees.  

