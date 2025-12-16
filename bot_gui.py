import tkinter as tk
from tkinter import messagebox, scrolledtext
import subprocess
import time
import os
import threading

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON = os.path.join(BASE_DIR, ".venv", "Scripts", "python.exe")
BOT_SCRIPT = os.path.join(BASE_DIR, "Shark-Tank.py")
LOG_FILE = os.path.join(BASE_DIR, "bot.log")

process = None
start_time = None
auto_restart = True
stop_requested = False


def start_bot():
    global process, start_time, stop_requested

    if process and process.poll() is None:
        messagebox.showinfo("Bot Running", "Bot is already running.")
        return

    stop_requested = False
    start_time = time.time()
    status_label.config(text="Status: Running", fg="green")

    threading.Thread(target=run_bot, daemon=True).start()


def run_bot():
    global process

    while not stop_requested:
        with open(LOG_FILE, "a", encoding="utf-8") as log:
            process = subprocess.Popen(
                [PYTHON, BOT_SCRIPT],
                cwd=BASE_DIR,
                stdout=log,
                stderr=log
            )
            process.wait()

        if not auto_restart or stop_requested:
            break

        time.sleep(3)  # delay before restart


def stop_bot():
    global stop_requested, process, start_time

    stop_requested = True

    if process and process.poll() is None:
        process.terminate()

    process = None
    start_time = None
    status_label.config(text="Status: Stopped", fg="red")
    uptime_label.config(text="Uptime: 00:00:00")


def update_uptime():
    if start_time:
        elapsed = int(time.time() - start_time)
        h, r = divmod(elapsed, 3600)
        m, s = divmod(r, 60)
        uptime_label.config(text=f"Uptime: {h:02}:{m:02}:{s:02}")
    root.after(1000, update_uptime)


def update_logs():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
            log_box.delete("1.0", tk.END)
            log_box.insert(tk.END, f.read())
            log_box.see(tk.END)
    root.after(2000, update_logs)


# ---- GUI ----
root = tk.Tk()
root.title("Shark Tank Bot Controller")
root.geometry("520x420")
root.resizable(False, False)

status_label = tk.Label(root, text="Status: Stopped", fg="red", font=("Segoe UI", 11))
status_label.pack(pady=5)

uptime_label = tk.Label(root, text="Uptime: 00:00:00", font=("Segoe UI", 10))
uptime_label.pack(pady=5)

btn_frame = tk.Frame(root)
btn_frame.pack(pady=5)

tk.Button(btn_frame, text="Start Bot", width=15, command=start_bot).grid(row=0, column=0, padx=5)
tk.Button(btn_frame, text="Stop Bot", width=15, command=stop_bot).grid(row=0, column=1, padx=5)

log_box = scrolledtext.ScrolledText(root, width=62, height=18, font=("Consolas", 9))
log_box.pack(pady=10)

update_uptime()
update_logs()
root.mainloop()
