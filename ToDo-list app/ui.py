## UI logik å dylikt

import tkinter as tk
from tkinter import simpledialog, messagebox
from tkinter import font as tkfont
import time
from datetime import datetime, timedelta

## Funktioner för deadlines samt parsar inmatningen utan år

def _parse_user_dt(s: str | None):
    if not s:
        return None
    s = s.strip().replace("T", " ")
    fmt = ("%m-%d %H:%M", "%m-%d")
    for fmt in fmt: ## fmts ska va ftm?
        try:
            partial = datetime.strptime(s, fmt)
            now = datetime.now()
            dt = partial.replace(year=now.year)
            return dt
        except ValueError:
            continue
    return None

def _parse_iso(s: str | None):
    if not s:
        return None
    s2 = s.replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s2, fmt)
        except ValueError:
            continue

    # Sista försök
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None

## Start appen med att visa klockan och uppgifter.
def run_app(tasks, on_toggle, on_delete, on_add):

    # skapa fönster
    root = tk.Tk()
    root.title("Daily To-Do app")

    ## Typsnitt för genomstrykning
    base_font = tkfont.Font(family="Helvetica", size=12)
    done_font = tkfont.Font(family="Helvetica", size=12)
    done_font.configure(overstrike=1)

    ## Lagra notifierade uppgifter för att undvika spam
    notified_ids = set()
    notify_window_min = 30

    # Laddar ikoner
    icons = {}
    try:
        icons["add"] = tk.PhotoImage(file="assets/add.png").subsample(2)
        icons["trash"] = tk.PhotoImage(file="assets/trash.png").subsample(18)
        icons["check"] = tk.PhotoImage(file="assets/check.png").subsample(18)
        icons["uncheck"] = tk.PhotoImage(file="assets/uncheck.png").subsample(18)
    except Exception as e:
        print("Kunde inte ladda en eller flera ikoner:", e)
        icons = None

    # Skapa label för klockan
    clock_label = tk.Label(root, font=("Helvetica", 16))
    clock_label.pack(pady=10)

    # Funktion för att uppdatera tiden varje sekund
    def update_clock():
        current_time = time.strftime("%H:%M")
        clock_label.config(text=current_time)
        root.after(1000, update_clock) # <- time loop för 1 sek

    update_clock()

    # Verktygsrad för ny uppgift
    toolbar = tk.Frame(root)
    toolbar.pack(fill="x", padx=10, pady=(0, 6))

    def ny_uppgift():
        title = simpledialog.askstring("Ny uppgift", "Vad vill du göra?", parent=root)
        if title is None:
            return
        title = title.strip()
        if not title:
            messagebox.showwarning("Fel uppstod:", "Titeln får inte vara tom.", parent=root)
            return

        due = simpledialog.askstring(
            "Deadline (valfri)", "Ange deadline (MM-DD HH:MM) eller lämna tomt:", parent=root
            )
        due_iso = None
        if due:
            dt = _parse_user_dt(due)
            if not dt:
                messagebox.showwarning("Fel uppstod: ", "Fel datumformat. Använd t.ex. 09-30 14:00", parent=root)
                return
            else:
                due_iso = dt.isoformat(timespec="minutes")

        repeat = simpledialog.askstring(
            "Återkommande (valfri)", "Välj: none / daily / weekly:", parent=root
            )
        if repeat:
            repeat = repeat.strip().lower()
            if repeat not in ("daily", "weekly"):
                messagebox.showwarning("Fel uppstod: ", "skriv daily / weekly eller lämna tomt.", parent=root)
                return
        else:
            repeat == None

        on_add(title, due_iso, repeat) # Ändrar signatur i main
        render_list() # Uppdaterar UI
        update_status() # uppdaterar status

    tk.Button(toolbar,
              text=" + Ny uppgift",
              image=(icons["add"] if icons else None),
              compound="left",
              padx=6,
              command=ny_uppgift
              ).pack(side="left")

    # Statusrad (klar/ej klar)
    status_label = tk.Label(root, font=("Helvetica", 11))
    status_label.pack(pady=(0, 6))

    def update_status():
        klara = sum(1 for t in tasks if t["done"])
        kvar = len(tasks) - klara
        status_label.config(text=f"klara: {klara} | kvar: {kvar}")

    # list-container
    tasks_frame = tk.Frame(root)
    tasks_frame.pack(fill="both", expand=True, padx=10, pady=10)

    ## Färg för deadlines
    def _due_style(task):
        if task.get("done"):
            return {"fg": "#777", "font": done_font}
        due = _parse_iso(task.get("due_at"))
        if not due:
            return {"fg": "#000", "font": base_font}
        now = datetime.now()
        if due < now:
            return {"fg": "#c0392b", "font": base_font} ## röd
        if due - now <= timedelta(minutes=notify_window_min):
            return {"fg": "#d35400", "font": base_font} ## orange för snart
        return {"fg": "#000", "font": base_font}

    # Ritar om hela listan utifrån 'tasks'
    def render_list():
        for w in tasks_frame.winfo_children():
            w.destroy()

        def sort_key(t):
            return (t["done"], _parse_iso(t.get("due_at")) or datetime.max)
        for task in sorted(tasks, key=sort_key):
            row = tk.Frame(tasks_frame)
            row.pack(fill="x", pady=2)

            # Toggle-knapp
            if icons:
                toggle_img = icons["check"] if task.get("done") else icons["uncheck"]
                toggle_text = ""
                width = 28
            else:
                toggle_img = None
                toggle_text = "✔" if task.get("done") else "❌"
                width = 2

            tk.Button(
                row,
                image=toggle_img,
                text=toggle_text,
                width=width,
                compound="center",
                command=lambda tid=task["id"]: (
                    on_toggle(tid),
                    render_list(),
                    update_status()
                )
            ).pack(side="left")

            # Titel + deadline
            style = _due_style(task)
            title = task.get("title", "")
            due = _parse_iso(task.get("due_at"))
            due_str = f" (⏰ {due.strftime('%m-%d %H:%M')})" if due else ""
            tk.Label(row, text=title + due_str, **style).pack(side="left", padx=8)

            # Ta bort-knappen
            del_img = icons["trash"] if icons else None
            tk.Button(
                row,
                image=del_img,
                text=(" Ta bort" if not icons else ""),
                compound="left",
                command=lambda tid=task["id"]: (
                    on_delete(tid),
                    render_list(),
                    update_status()
                )
            ).pack(side="right")

    ## Notiser - kollar deadlines var min
    def check_deadlines():
        now = datetime.now()
        window = timedelta(minutes=notify_window_min)
        for task in tasks:
            if task.get("done"):
                continue
            due = _parse_iso(task.get("due_at"))
            if not due:
                continue
            ## notifiera en gång om det är inom fönstered eller har passerat
            if (due <= now or (due - now) <= window) and task["id"] not in notified_ids:
                notified_ids.add(task["id"])
                when = "NU!" if due <= now else f"Om {(due - now).seconds // 60} min"
                messagebox.showinfo("Påminnelse:", f"{task['title']}\nDeadline: {due.strftime('%Y-%m-%d %H:%M')} ({when})")
        root.after(60_000, check_deadlines) # kollar igen om 1 min
            
    render_list()
    update_status()
    root.after(60_000, check_deadlines)

    # starta huvudloopen
    root.mainloop()