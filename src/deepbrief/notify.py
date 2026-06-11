from __future__ import annotations

import getpass
import json
import os
import plistlib
import subprocess
from pathlib import Path

from deepbrief.config import Config


def install_launchd(config: Config) -> None:
    user = getpass.getuser()
    uid = os.getuid()
    label = launchd_label(user)
    launch_agents = Path.home() / "Library" / "LaunchAgents"
    launch_agents.mkdir(parents=True, exist_ok=True)
    config.state_dir.mkdir(parents=True, exist_ok=True)
    log_dir = config.state_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    plist_path = launch_agents / f"{label}.plist"
    python = config.repo_root / ".venv" / "bin" / "python"
    if not python.exists():
        raise RuntimeError(f"missing project venv python: {python}")
    plist = {
        "Label": label,
        "ProgramArguments": [
            str(python),
            "-m",
            "deepbrief.cli",
            "run",
        ],
        "WorkingDirectory": str(config.repo_root),
        "EnvironmentVariables": {
            "PYTHONPATH": "src",
            "PATH": os.environ.get("PATH", ""),
            "PUPPETEER_CACHE_DIR": str(config.repo_root / ".cache" / "puppeteer"),
        },
        "StartCalendarInterval": {
            "Hour": config.schedule["hour"],
            "Minute": config.schedule["minute"],
        },
        "StandardOutPath": str(log_dir / "deepbrief.out.log"),
        "StandardErrorPath": str(log_dir / "deepbrief.err.log"),
        "ProcessType": "Background",
    }
    plist_path.write_bytes(plistlib.dumps(plist))
    bootout(uid, label)
    bootstrap = run_launchctl(["bootstrap", f"gui/{uid}", str(plist_path)], check=False)
    if bootstrap.returncode != 0 and "already bootstrapped" not in bootstrap.stderr:
        raise RuntimeError(f"launchctl bootstrap failed: {bootstrap.stderr.strip()}")
    enable = run_launchctl(["enable", f"gui/{uid}/{label}"], check=False)
    if enable.returncode != 0:
        raise RuntimeError(f"launchctl enable failed: {enable.stderr.strip()}")
    print(
        json.dumps(
            {
                "status": "ok",
                "action": "install",
                "label": label,
                "plist": str(plist_path),
                "stdout_log": str(log_dir / "deepbrief.out.log"),
                "stderr_log": str(log_dir / "deepbrief.err.log"),
            },
            sort_keys=True,
        )
    )


def uninstall_launchd(config: Config) -> None:
    user = getpass.getuser()
    uid = os.getuid()
    label = launchd_label(user)
    plist_path = Path.home() / "Library" / "LaunchAgents" / f"{label}.plist"
    bootout(uid, label)
    removed = False
    if plist_path.exists():
        plist_path.unlink()
        removed = True
    print(json.dumps({"status": "ok", "action": "uninstall", "label": label, "plist_removed": removed}, sort_keys=True))


def notify_ready(pdf: str) -> dict[str, str | int]:
    script = 'display notification "DeepBrief ready - 1 deep dive, 5 skims (~2 h). Feedback file ready." with title "DeepBrief ready"'
    completed = subprocess.run(["/usr/bin/osascript", "-e", script], text=True, capture_output=True)
    return {"returncode": completed.returncode, "stderr": completed.stderr.strip()}


def open_pdf(pdf: str) -> dict[str, str | int]:
    completed = subprocess.run(["/usr/bin/open", pdf], text=True, capture_output=True)
    return {"returncode": completed.returncode, "stderr": completed.stderr.strip()}


def launchd_label(user: str) -> str:
    safe = "".join(ch if ch.isalnum() else "-" for ch in user)
    return f"com.{safe}.deepbrief"


def bootout(uid: int, label: str) -> subprocess.CompletedProcess[str]:
    return run_launchctl(["bootout", f"gui/{uid}/{label}"], check=False)


def run_launchctl(args: list[str], *, check: bool) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(["/bin/launchctl", *args], text=True, capture_output=True)
    if check and completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip())
    return completed
