# Avocor Interactive Display for Home Assistant

A custom Home Assistant integration for Avocor interactive displays (tested
against the AVE-5530), controlled over the display's TCP/IP control port.

## What it exposes

One config entry represents one physical display and creates a single HA
device with these entities:

| Platform | Entity | Notes |
|---|---|---|
| `media_player` | Display | Power, input source, volume, mute |
| `select` | Picture mode | User / Vivid / Cinema / Game / Sport |
| `number` | Backlight, Brightness, Contrast, Sharpness, Hue, Saturation | 0-100, under "Configuration" |
| `switch` | Freeze image | Freezes the current picture (e.g. for whiteboard use) |
| `remote` | Remote | Sends key presses via `remote.send_command` (menu, up/down/left/right, ok, exit, source keys, etc.) |
| `button` | Restore picture/audio defaults | Factory-resets picture/audio/OSD settings only — never touches network/RS232 settings, so it can't cut off its own connection |
| `sensor` | Serial number, Firmware version | Diagnostic, read once at startup |

## Requirements

- The display must be on the same network as Home Assistant, with its
  Ethernet control port reachable (default TCP port **4664**).
- Network/TCP control must be enabled on the display.
- To turn the display on remotely over TCP, its EcoMode (`WFS` command in
  the manual) must be set to keep RS232/network control alive in standby
  ("Set DIGITAL, RS232, Ethernet") rather than "Never Sleep" — otherwise the
  Ethernet controller itself may power down and become unreachable.

## Installation

### HACS (custom repository)

1. HACS → Integrations → ⋮ → Custom repositories → add this repository URL, category "Integration".
2. Install "Avocor Interactive Display", then restart Home Assistant.

### Manual

Copy `custom_components/avocor` into your Home Assistant `config/custom_components/` directory, then restart Home Assistant.

## Setup

Settings → Devices & Services → Add Integration → "Avocor Interactive Display", then enter:

- **Host** — the display's IP address or hostname
- **Port** — 4664 by default
- **Display ID** — 1 by default (the manual documents this as fixed for direct TCP control)
- **Name** — a friendly name for the device

Setup validates the connection by reading the display's serial number, which also becomes the config entry's unique ID.

## Protocol notes

The control protocol is documented in the AVE-5530 User Manual's "External
Control" chapter: a persistent TCP connection exchanging fixed-format
frames `[STX 0x07][Display ID][Type][3-letter ASCII command][value][ETX 0x08]`.
This integration's `custom_components/avocor/api.py` implements that framing
directly from the manual's command tables (power, input, volume, picture
settings, remote-key injection, freeze, factory reset, and read-only
identification commands).

Since this was implemented from the manual rather than against a live unit,
one detail is an educated inference rather than a documented certainty: the
manual doesn't spell out what value byte a *read* request should carry, so
this integration sends a dummy `0x00`. If reads fail against your actual
display, that's the first thing to adjust in `api.py` — enable debug logging
(see below) and compare the raw bytes sent/received against what the display
expects.

## Debug logging

```yaml
logger:
  logs:
    custom_components.avocor: debug
```

## Known limitations

- Power-on over TCP depends on the display keeping its network controller
  alive in standby (see EcoMode above); if the panel fully powers down its
  Ethernet chip, TCP wake isn't possible.
- Only "reset all but communication" is exposed for factory reset, by
  design — resetting communication settings would sever the very
  connection this integration uses.
