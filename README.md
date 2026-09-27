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
  Ethernet control port reachable (default TCP port **4884** — the manual
  documents 4664, but 4884 is what actual AVE-5530 units ship with).
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
- **Port** — 4884 by default
- **Name** — a friendly name for the device

Setup validates the connection by reading the display's serial number, which also becomes the config entry's unique ID.

## Polling

Two `DataUpdateCoordinator`s poll the display at different rates, since
power/input can change from outside Home Assistant (a physical remote or IR
receiver) while everything else rarely does externally:

- **Fast (10s)** — power state and input source.
- **Slow (60s)** — volume, mute, picture mode, backlight/brightness/contrast/
  sharpness/hue/saturation, and freeze state.

Any change made *through* Home Assistant (e.g. `media_player.turn_on`,
`number.set_value`) triggers an immediate refresh of the relevant
coordinator, so the polling interval only affects how quickly HA notices a
change made some other way. Both intervals are constants in
[`const.py`](custom_components/avocor/const.py) (`FAST_SCAN_INTERVAL`,
`SLOW_SCAN_INTERVAL`) if you want to tune them.

## Protocol notes

The control protocol is documented in the AVE-5530 User Manual's "External
Control" chapter: a persistent TCP connection exchanging fixed-format
frames `[STX 0x07][Display ID][Type][3-letter ASCII command][value][ETX 0x08]`.
This integration's `custom_components/avocor/api.py` implements that framing
directly from the manual's command tables (power, input, volume, picture
settings, remote-key injection, freeze, factory reset, and read-only
identification commands).

Several details were confirmed against real hardware (three AVE units) and
differ from what the manual states, since this integration was originally
written from the manual alone:

- A *read/action* request (TYPE `0x01`) carries **no value byte at all** —
  the frame goes straight from the 3-letter command to `ETX`. Only a
  *write* request (TYPE `0x02`) includes a value byte.
- A response's TYPE byte **echoes the TYPE that was sent** (`0x01` for a
  read reply, `0x02` for a write ack) — not a fixed `0x00` as the manual
  states.
- The read-only identification commands' reply lengths don't match the
  manual either: `SER` (serial number) returned 14 bytes rather than 13,
  `MNA` (model name) returned 43 bytes rather than 13, and `GVE` (firmware)
  returned 8 bytes rather than 6. Those three replies are read up to the
  terminating `ETX` instead of a fixed length, which is safe there
  specifically because their payload is always printable ASCII text (never
  containing the `ETX` control byte).

`api.py` reflects all of the above.

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
