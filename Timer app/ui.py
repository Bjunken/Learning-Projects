import customtkinter as ctk
from tkinter import messagebox
from typing import Callable
import math

## formaterar sekunder som: HH:MM:SS
def format_hms(secs: int) -> str:
    if secs < 0:
        secs = 0
    h = secs // 3600
    m = (secs % 3600) // 60
    s = secs % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

## skapar UI
def run_app(
    timers: list[dict],
    *,
    on_create: Callable[[str, int, int], None],
    on_start: Callable[[str], None],
    on_pause: Callable[[str], None],
    on_stop: Callable[[str], None],
    on_restart: Callable[[str], None],
    on_delete: Callable[[str], None],
    on_tick: Callable[[int], list[str]],
    ):
    ## initierar customTkinter
    ctk.set_appearance_mode("dark") ## finns "light" | "dark" | "system"
    ctk.set_default_color_theme("blue") ## finns "blue" | "green" | "dark-blue"

    root = ctk.CTk()
    root.title("TimerApp")
    root.geometry("700x500")

    ## topbar med "ny timer" knapp
    topbar = ctk.CTkFrame(root)
    topbar.pack(fill="x", padx=12, pady=10)

    title_label = ctk.CTkLabel(topbar, text="Timrar", font=ctk.CTkFont(size=18, weight="bold"))
    title_label.pack(side="left", padx=(8, 12))

    ## Visar ett litet formulär i ett toplevel fönster för att skapa en timer
    def open_new_timer_dialog():
        dialog = ctk.CTkToplevel(root)
        dialog.title("Ny timer")
        dialog.geometry("300x280")
        dialog.transient(root) #håller den ovanför
        dialog.grab_set()
        dialog.focus_force()

        ## namn
        ctk.CTkLabel(dialog, text="namn").pack(anchor="w", padx=10, pady=(10, 0))
        name_entry = ctk.CTkEntry(dialog, placeholder_text="t.ex. Pasta")
        name_entry.pack(fill="x", padx=10, pady=4)
        name_entry.focus_set()

        ## Timmar / minuter
        ctk.CTkLabel(dialog, text="timmar").pack(anchor="w", padx=10, pady=(10, 0))
        hours_combo = ctk.CTkComboBox(dialog, values=[f"{i:02d}" for i in range(24)], width=80)
        hours_combo.set("00")
        hours_combo.pack(anchor="w", padx=10, pady=4)

        ctk.CTkLabel(dialog, text="Minuter").pack(anchor="w", padx=10, pady=(10, 0))
        minutes_combo = ctk.CTkComboBox(dialog, values=[f"{i:02d}" for i in range(60)], width=80)
        minutes_combo.set("00")
        minutes_combo.pack(anchor="w", padx=10, pady=4)

        ## Knappar: abryt / spara
        btns = ctk.CTkFrame(dialog)
        btns.pack(fill="x", padx=10, pady=12)

        def cancel():
            dialog.destroy()

        def accept():
            name = name_entry.get().strip()
            try:
                hours = int(hours_combo.get())
                minutes = int(minutes_combo.get())
            except ValueError:
                messagebox.showwarning("Fel:", "Välj timmar/minuter i listorna.")
                return
            if hours == 0 and minutes == 0:
                messagebox.showwarning("Fel:", "Tiden kan inte vara 00:00.")
                return
            on_create(name, hours, minutes)
            render_list()
            dialog.destroy()

        cancel_btn = ctk.CTkButton(btns, text="Avbryt", command=cancel)
        cancel_btn.pack(side="right", padx=5)
        ok_btn = ctk.CTkButton(btns, text="Spara", command=accept)
        ok_btn.pack(side="right")

    new_btn = ctk.CTkButton(topbar, text="Ny timer", command=open_new_timer_dialog)
    new_btn.pack(side="right", padx=10)

    ## scrollbar lista för timrar
    list_frame = ctk.CTkScrollableFrame(root, label_text="Mina timrar")
    list_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    ## sparar referenser till tids- labels för uppdatering varje sec
    time_labels: dict[str, ctk.CTkLabel] = {}
    state_labels: dict[str, ctk.CTkLabel] = {}

    ## ritar och uppdaterar display / listan
    def render_list():
        nonlocal time_labels, state_labels
        # rensa tidigare widgets
        for w in list_frame.winfo_children():
            if isinstance(w, ctk.CTkFrame):
                w.destroy()
        time_labels = {}
        state_labels = {}

        ## sorterar running överst, sedan paused, stopped
        order = {"running": 0, "paused": 1, "stopped": 2}
        def sort_key(t: dict):
            return (order.get(t["state"], 99), t["name"].casefold())

        for t in sorted(timers, key=sort_key):
            row = ctk.CTkFrame(list_frame)
            row.pack(fill="x", padx=8, pady=6)

            # namn
            name_lbl = ctk.CTkLabel(row, text=t["name"], width=180, anchor="w")
            name_lbl.pack(side="left", padx=6)

            # Återstående tid
            time_lbl = ctk.CtkLabel(row, text=format_hms(t["remaning_seconds"]), width=100)
            time_lbl.pack(side="left", padx=6)
            time_labels[t["id"]] = time_lbl

            # state label
            state_lbl = ctk.CTkLabel(row, text=t["state"].capitalize(), width=80)
            state_lbl.pack(side="left", padx=6)
            state_labels[t["id"]] = state_lbl

            ## knappar
            # start
            start_btn = ctk.CTkButton(row, text="start", width=70,
                                      command=lambda tid=t["id"]: (on_start(tid), render_list()))
            # pause
            pause_btn = ctk.CTkButton(row, text="Pausa", width=70,
                                      command=lambda tid=t["id"]: (on_pause(tid), render_list()))
            # stop / reset
            stop_btn = ctk.CTkButton(row, text="Stop/Reset", width=90,
                                     command=lambda tid=t["id"]: (on_stop(tid), render_list()))
            # restart
            restart_btn = ctk.CTkButton(row, text="Starta om", width=90,
                                        command=lambda tid=t["id"]: (on_restart(tid), render_list()))
            # Delete
            delete_btn = ctk.CTkButton(row, fg_color="#8e3b46", hover_color="#6e2f37",
                                       text="Ta bort", widt=70, command=lambda tid=t["id"]: (on_delete(tid), render_list()))

            ## aktivera/inaktivera beroende på state
            state = t["state"]
            start_btn.configure(state=("disabled" if state == "runing" else "normal"))
            pause_btn.configure(state=("normal" if state == "runing" else "disabled"))
            stop_btn.configure(state=("normal" if state != "stopped" else "disabled"))
            restart_btn.configure(state="normal")
            delete_btn.configure(state="normal")

            ## placera knappar
            restart_btn.pack(side="right", padx=4)
            delete_btn.pack(side="right", padx=4)
            stop_btn.pack(side="right", padx=4)
            pause_btn.pack(side="right", padx=4)
            start_btn.pack(side="right", padx=4)

    ## Tick-loop (1s) som kallar core.tick och uppdaterar tidsetiketter
    def tick_loop():
        done_ids = on_tick(1)
        for t in timers:
            lbl = time_labels.get(t["id"])
            if lbl:
                lbl.configure(text=format_hms(t["remaning_seconds"]))
            st = state_labels.get(t["id"])
            if st:
                st.configure(text=t["state"].capitalize())
        if done_ids:
            # pling meddelande här
            render_list()
        root.after(1000, tick_loop) ## kör igen om 1 sekund

    ## ritar listan och startar loop
    render_list()
    root.after(1000, tick_loop)
    root.mainloop()