"""
Universal preference enums shared across all projects.
"""

from enum import StrEnum


class Language(StrEnum):
    ZH_CN = "zh-CN"
    EN = "en"
    JA = "ja"


class Theme(StrEnum):
    SYSTEM = "system"
    LIGHT = "light"
    DARK = "dark"


class HourCycle(StrEnum):
    AUTO = "auto"
    H12 = "h12"
    H23 = "h23"
