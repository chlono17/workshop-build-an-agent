"""Read-only memory checks for running the GPU-heavy lessons on a DGX Spark.

A DGX Spark has 128 GB of unified memory shared by the CPU and the GPU. In the
local-first fork the chat model (Qwen3.8 27B, started from NVIDIA Sync -> Models)
keeps about 114 GB of it while it runs, so a lesson that loads another large model
(Module 4 GRPO training, the Module 2 local NIM) must stop it first. These helpers
only read /proc/meminfo and ask the gateway which models it serves; they never stop
or start anything.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path

from . import get_api_key, get_base_url, get_model, is_local

CHAT_MODEL_GB = 114  # what the 27B keeps while it runs (measured on the Spark)
STOP_CHAT_MODEL = ("Stop the 27B first: NVIDIA Sync -> Models -> Stop, then wait until it "
                   "shows as stopped. Every other lesson needs it, so start it again afterwards.")
START_CHAT_MODEL = ("Afterwards, start it again: NVIDIA Sync -> Models -> Start, and wait until "
                    "Workshop Health's endpoint checks pass.")


def available_memory_gb(meminfo_path: str | Path = "/proc/meminfo") -> float | None:
    """MemAvailable in GB, or None if it cannot be read."""
    try:
        for line in Path(meminfo_path).read_text().splitlines():
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) / 1024 ** 2
    except (OSError, ValueError, IndexError):
        pass
    return None


def chat_model_running(timeout: float = 3) -> bool | None:
    """True if the local gateway lists the chat model, False if not, None if unknown.

    Hosted mode returns None: the hosted model uses no memory on this machine.
    """
    if not is_local():
        return None
    request = urllib.request.Request(f"{get_base_url()}/models",
                                     headers={"Authorization": f"Bearer {get_api_key()}"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            listed = {m.get("id") for m in json.load(response).get("data", [])}
    except (OSError, ValueError, AttributeError):
        return None
    return get_model("chat") in listed


def check_memory_for(task: str, needed_gb: float, *, meminfo_path: str | Path = "/proc/meminfo",
                     chat_running: bool | None = ...) -> bool:
    """Print whether `task` fits in free memory now, and what to do if not. Returns True if it fits."""
    if chat_running is ...:
        chat_running = chat_model_running()
    free = available_memory_gb(meminfo_path)
    if free is None:
        print(f"Could not read free memory. {task} needs about {needed_gb:.0f} GB.")
    else:
        print(f"Free memory: {free:.0f} GB. {task} needs about {needed_gb:.0f} GB.")
    fits = free is not None and free >= needed_gb
    if chat_running:
        print(f"The local chat model ({get_model('chat')}) is running and keeps about {CHAT_MODEL_GB} GB.")
        if not fits:
            print(STOP_CHAT_MODEL)
    elif chat_running is False:
        print("The local chat model is stopped, so its memory is free. " + START_CHAT_MODEL)
    if fits:
        print("OK: enough free memory for this step.")
    elif not chat_running:
        print("Not enough free memory. Shut down other notebook kernels and GPU services, then rerun this cell.")
    return fits
