"""Constants for the Avocor Interactive Display integration."""
from __future__ import annotations

from enum import IntEnum

DOMAIN = "avocor"

DEFAULT_PORT = 4664
DEFAULT_DISPLAY_ID = 0x01
DEFAULT_NAME = "Avocor Display"
DEFAULT_SCAN_INTERVAL = 30

CONF_DISPLAY_ID = "display_id"

MANUFACTURER = "Avocor"

# Frame delimiters (Command and Response Format, TCP/IP Control Configuration).
STX = 0x07
ETX = 0x08


class CommandType(IntEnum):
    """The [TYPE] byte of an Avocor control frame."""

    RESPONSE = 0x00
    READ = 0x01
    WRITE = 0x02


# 3-character ASCII command mnemonics, transmitted as their literal ASCII bytes.
CMD_POWER = "POW"
CMD_IPC = "IPC"
CMD_INPUT = "MIN"
CMD_BACKLIGHT_ONOFF = "BLC"
CMD_BACKLIGHT = "BRI"
CMD_BRIGHTNESS = "BRL"
CMD_CONTRAST = "CON"
CMD_HUE = "HUE"
CMD_SATURATION = "SAT"
CMD_NOISE_REDUCTION = "NOR"
CMD_RED_GAIN = "USR"
CMD_GREEN_GAIN = "USG"
CMD_BLUE_GAIN = "USB"
CMD_RED_OFFSET = "UOR"
CMD_GREEN_OFFSET = "UOG"
CMD_BLUE_OFFSET = "UOB"
CMD_SHARPNESS = "SHA"
CMD_ASPECT_RATIO = "ASP"
CMD_REMOTE_KEY = "RCU"
CMD_FACTORY_RESET = "ALL"
CMD_SERIAL_NUMBER = "SER"
CMD_MODEL_NAME = "MNA"
CMD_FIRMWARE_VERSION = "GVE"
CMD_VOLUME = "VOL"
CMD_BASS = "BAS"
CMD_TREBLE = "TRE"
CMD_BALANCE = "BAL"
CMD_VOLUME_DOWN = "VOD"
CMD_VOLUME_UP = "VOI"
CMD_MUTE = "MUT"
CMD_PICTURE_MODE = "SCM"
CMD_ECO_MODE = "WFS"
CMD_RTC_YEAR = "RTY"
CMD_RTC_MONTH = "RTM"
CMD_RTC_DAY = "RTD"
CMD_RTC_HOUR = "RTH"
CMD_RTC_MINUTE = "RTN"
CMD_FREEZE = "FRE"
CMD_AUTO_SCAN = "ATS"
CMD_EDID_ALL = "EDA"
CMD_EDID_HDMI = "EDH"
CMD_EDID_DISPLAYPORT = "EDP"
CMD_COLOR_RANGE = "HCR"
CMD_OSD_LANGUAGE = "OSL"
CMD_OSD_TIMEOUT = "OSO"
CMD_NETWORK_ENABLE = "NWE"
CMD_MAC_QUERY = "MAC"

# Reply payload length in bytes, for commands whose reply is not a single byte.
# Used to know exactly how many bytes to read for a response frame.
COMMAND_REPLY_LENGTH: dict[str, int] = {
    CMD_SERIAL_NUMBER: 13,
    CMD_MODEL_NAME: 13,
    CMD_FIRMWARE_VERSION: 6,
}

# Input Source Selection (MIN).
INPUT_SOURCE_VGA = "VGA"
INPUT_SOURCE_HDMI1 = "HDMI 1"
INPUT_SOURCE_HDMI2 = "HDMI 2"
INPUT_SOURCE_HDMI3_FRONT = "HDMI 3 (Front)"
INPUT_SOURCE_DISPLAYPORT = "DisplayPort"
INPUT_SOURCE_OPS = "OPS"

INPUT_SOURCES: dict[str, int] = {
    INPUT_SOURCE_VGA: 0x00,
    INPUT_SOURCE_HDMI1: 0x09,
    INPUT_SOURCE_HDMI2: 0x0A,
    INPUT_SOURCE_HDMI3_FRONT: 0x0B,
    INPUT_SOURCE_DISPLAYPORT: 0x0D,
    INPUT_SOURCE_OPS: 0x0E,
}
INPUT_SOURCES_REVERSE: dict[int, str] = {v: k for k, v in INPUT_SOURCES.items()}

# Scheme Selection / Picture Mode (SCM).
PICTURE_MODE_USER = "User"
PICTURE_MODE_VIVID = "Vivid"
PICTURE_MODE_CINEMA = "Cinema"
PICTURE_MODE_GAME = "Game"
PICTURE_MODE_SPORT = "Sport"

PICTURE_MODES: dict[str, int] = {
    PICTURE_MODE_USER: 0x00,
    PICTURE_MODE_VIVID: 0x01,
    PICTURE_MODE_CINEMA: 0x02,
    PICTURE_MODE_GAME: 0x03,
    PICTURE_MODE_SPORT: 0x04,
}
PICTURE_MODES_REVERSE: dict[int, str] = {v: k for k, v in PICTURE_MODES.items()}

# Scaling / Aspect Ratio (ASP).
ASPECT_RATIO_POINT_TO_POINT = "Point to Point"
ASPECT_RATIO_FULL_SCREEN = "Full Screen (16:9)"
ASPECT_RATIO_PILLARBOX = "Pillarbox (4:3)"
ASPECT_RATIO_LETTERBOX = "Letterbox"
ASPECT_RATIO_AUTO = "Auto"

ASPECT_RATIOS: dict[str, int] = {
    ASPECT_RATIO_POINT_TO_POINT: 0x00,
    ASPECT_RATIO_FULL_SCREEN: 0x01,
    ASPECT_RATIO_PILLARBOX: 0x02,
    ASPECT_RATIO_LETTERBOX: 0x03,
    ASPECT_RATIO_AUTO: 0x04,
}
ASPECT_RATIOS_REVERSE: dict[int, str] = {v: k for k, v in ASPECT_RATIOS.items()}

# Remote Control key injection (RCU), write-only.
REMOTE_KEYS: dict[str, int] = {
    "menu": 0x00,
    "info": 0x01,
    "up": 0x02,
    "down": 0x03,
    "left": 0x04,
    "right": 0x05,
    "ok": 0x06,
    "exit": 0x07,
    "hdmi1": 0x0A,
    "hdmi2": 0x0B,
    "hdmi_front": 0x1F,
    "displayport": 0x22,
    "type_c": 0x23,
    "ops": 0x21,
    "scaling": 0x17,
    "freeze": 0x18,
    "mute": 0x19,
    "auto": 0x1C,
    "volume_up": 0x1D,
    "volume_down": 0x1E,
}

# Freeze (FRE).
FREEZE_OFF = 0x00
FREEZE_ON = 0x01

# Factory Reset (ALL), write-only. RESET_ALL wipes communication settings too,
# which would immediately sever the very connection this integration relies
# on, so only the safer variant is exposed as an entity.
FACTORY_RESET_ALL = 0x00
FACTORY_RESET_KEEP_COMMUNICATION = 0x01
