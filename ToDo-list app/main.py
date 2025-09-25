## huvud program

from core import (load_tasks, save_tasks, add_task, toggle_done, delete_task)
from ui import run_app

def main():
    # läs in uppgifter / skapa fil om den ej finns.
    tasks = load_tasks()

    def on_toggle(task_id):
        toggle_done(tasks, task_id)
        save_tasks(tasks)

    def on_delete(task_id):
        delete_task(tasks, task_id)
        save_tasks(tasks)

    def on_add(title, due_iso=None, repeat=None):
        add_task(tasks, title, due_at=due_iso, repeat=repeat)
        save_tasks(tasks)

    # Läster in UI
    run_app(tasks, on_toggle, on_delete, on_add)

if __name__ == "__main__":
    main()