import json
import os
import uuid
from datetime import datetime, timedelta

FILE_PATH = "data/timers.json"

## Ser till att data/ - mappen finns
def _ensure_data_dir():
    os.makedirs(os.path.dirname(FILE_PATH), exist_ok=True)

## Läser in timers från sparfil / öppnar tom lista om filen saknas eller är korrupt.
def load_timers(path: str = FILE_PATH) -> list[dict]:
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r") as f:
            data = json.load(f)
            ## typ-säkring för att kolla om alla nycklar finns
            for t in data:
                t.setdefault("id", str(uuid.uuid4()))
                t.setdefault("name", "Timer")
                t.setdefault("hours", 0)
                t.setdefault("minutes", 0)
                total = t.get("total_seconds", t["hours"] * 3600 + t["minutes"] * 60)
                t["total_seconds"] = int(total)
                t.setdefault("remaining_seconds", int(total))
                t.setdefault("state", "stopped")
                t.setdefault("updated_at", datetime.now().isoformat(timespec="seconds"))
            return data
    except (json.JSONDecodeError, ValueError):
        print("Varning: Kunde inte läsa timers.json. Startar med en tom lista.")
        return []

## Sparar timers till sparfil
def save_timers(timers: list[dict], path: str = FILE_PATH) -> None:
    with open(path, "w") as f:
        json.dump(timers, f, ensure_ascii=False, indent=2)

def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")

## Hittar en timer i listan på id
def _find_timer(timers: list[dict], timer_id: str) -> dict | None:
    return next((t for t in timers if t["id"] == timer_id), None)

## Skapa ny timer
def create_timer(timers: list[dict], name: str, hours: int, minutes: int) -> dict:
    total = hours * 3600 + minutes * 60
    timer = {
        "id": str(uuid.uuid4()),
        "name": name or "Timer",
        "hours": int(hours),
        "minutes": int(minutes),
        "total_seconds": int(total),
        "remaining_seconds": int(total),
        "state": "stopped",
        "updated_at": _now_iso(),
        }
    timers.append(timer)
    return timer

## Starta timer
def start_timer(timer: dict) -> None:
    ## kollar om den är synkat med "total"
    if timer["state"] == "stopped":
        timer["remaining_seconds"] = timer["total_seconds"]
    timer["state"] = "running"
    timer["updated_at"] = _now_iso()

## Pausa timer
def pause_timer(timer: dict) -> None:
    if timer["state"] == "running":
        timer["state"] = "paused"
        timer["updated_at"] = _now_iso()

## stoppa timer / återställer timer
def stop_timer(timer: dict) -> None:
    timer["state"] = "stopped"
    timer["remaning_seconds"] = timer["total_seconds"]
    timer["updated_at"] = _now_iso()

## Återställer och restarta timer
def restart_timer(timer: dict) -> None:
    timer["remaining_seconds"] = timer["total_seconds"]
    timer["state"] = "running"
    timer["updated_at"] = _now_iso()

## Ta bort timer
def delete_timer(timers: list[dict], timer_id: str) -> dict | None:
    for i, t in enumerate(timers):
        if t["id"] == timer_id:
            return timers.pop(i)
    return None

## själva klock logik tick tick
def tick(timers: list[dict], delta_sec: int = 1) -> list[str]:
    done_ids = []
    for t in timers:
        if t["state"] != "running":
            continue
        if t["remaining_seconds"] > 0:
            t["remaining_seconds"] = max(0, t["remaning_seconds"] - delta_sec)
        if t["remaining_seconds"] == 0:           ## återställer timer när klar, kom tbx å ändra till att den blinkar?
            t["state"] = "stopped"
            t["updated_at"] = _now_iso()
            done_ids.append(t["id"])
    return done_ids