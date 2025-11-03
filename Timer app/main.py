from core import (
    load_timers, save_timers, create_timer,
    start_timer, pause_timer, stop_timer,
    restart_timer, delete_timer, tick
    )
from ui import run_app

def main():
    ## Läser in timers
    timers = load_timers()

    ## hittar timers i listan
    def _get(tid: str):
        return next((t for t in timers if t["id"] == tid), None)

    ## ballbacks för UI
    def on_create(name: str, hours: int, minutes: int):
        create_timer(timers, name, hours, minutes)
        save_timers(timers)

    ## starta timer
    def on_start(tid: str):
        t = _get(tid)
        if t:
            start_timer(t)
            save_timers(timers)

    ## Pausa timer
    def on_pause(tid: str):
        t = _get(tid)
        if t:
            pause_timer(t)
            save_timers(timers)

    ## stoppa timer
    def on_stop(tid: str):
        t = _get(tid)
        if t:
            stop_timer(t)
            save_timers(timers)

    ## restarta timer
    def on_restart(tid: str):
        t = _get(tid)
        if t:
            restart_timer(t)
            save_timers(timers)

    ## Delete timer
    def on_delete(tid: str):
        delete_timer(timers, tid)
        save_timers(timers)

    ## kallas från UI varje sekond för att ticka timern
    def on_tick(delta: int = 1) -> list[str]:
        done_ids = tick(timers, delta)
        save_timers(timers)
        return done_ids

    ## kör UI:t
    run_app(
        timers,
        on_create=on_create,
        on_start=on_start,
        on_pause=on_pause,
        on_stop=on_stop,
        on_restart=on_restart,
        on_delete=on_delete,
        on_tick=on_tick,
        )

## Starta app
if __name__ == "__main__":
    main()