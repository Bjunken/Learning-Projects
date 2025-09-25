## Funktioner och annan core-logik

import json
import os
import uuid
from datetime import datetime, timedelta

file_path = "Data/tasks.json"

## Läs in json fil, (sparfilen)
def load_tasks(path=file_path):
    if not os.path.exists(path):
        return [] ## <- Detta gör att filen skapas om den inte finns

    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        print("Fel uppstod: Kunde inte läsa tasks.json. Startar med tom lista.")
        return []

## Sparar ner listan/uppgifter till json fil, (sparfilen)
def save_tasks(tasks, path=file_path):
    with open(path, "w") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2) ## <-- Ascii gör att det skrivs först i en temp fil, för att minska risk för korruption.

## Funktion för att kunna sätta deadline
def _iso(dt: datetime | None) -> str | None:
    return None if dt is None else dt.isoformat(timespec="minutes")

## Funktion för att tillåta år-månad-dag och iso
def _parse_iso(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        s2 = s.replace("T", " ") ### s = s2
        return datetime.strptime(s2, "%Y-%m-%d %H:%M")
    except ValueError:
        try:
            return datetime.fromisoformat(s)
        except ValueError:
            return None

## Funktion för att flytta fram deadline beroende på repeat
def _advance_due(due_at: str | None, repeat: str | None) -> str | None:
    if not due_at or not repeat:
        return None
    base = _parse_iso(due_at)
    if base is None:
        return None
    if repeat == "daily":
        nxt = base + timedelta(days=1)
    elif repeat == "weekly":
        nxt = base + timedelta(weeks=1)
    else:
        return None
    return _iso(nxt)

## Lägg till uppgifter i listan
def add_task(tasks, title, due_at=None, repeat=None):
    task = {
        "id": str(uuid.uuid4()),                        # Skapar unikt ID
        "title": title,                                 # Sjävla texten
        "done": False,                                  # Om den är klar eller ej
        "created_at": _iso(datetime.now()),             # När den skapades
        "due_at": due_at,                               # Om det finns deadline eller inte
        "repeat": repeat                                # None / "daily" / "weekly"
        }
    tasks.append(task)
    return task

## Uppgift toggle, (klar/ej klar)
def toggle_done(tasks, task_id):
    for task in tasks:
        if task["id"] == task_id:
            task["done"] = not task ["done"]
            ## Om uppgift är återkommande
            if task["done"] and task.get("repeat"):
                nxt_due = _advance_due(task.get("due_at"), task.get("repeat"))
                if nxt_due:
                    add_task(tasks, task["title"], due_at=nxt_due, repeat=task.get("repeat"))
            return task
    return None

## Ta bort uppgift
def delete_task(tasks, task_id):
    for i, task in enumerate(tasks):
        if task["id"] == task_id:
            return tasks.pop(i)
    return None