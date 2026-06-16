#!/usr/bin/env python3
"""
app.py - Social Diff GUI

A tiny Tkinter UI with two panels:
  - Instagram (top)
  - Twitter / X (bottom)

For each platform you:
  1) type your own username,
  2) click "Open browser" -> a Chrome window opens, you log in (2FA included),
  3) click "I'm logged in -> Fetch lists" -> the script visits your profile,
     scrolls the followers/following dialogs, collects handles and compares them.

Results (two-way mismatch) are shown on screen AND saved to .txt files.

No login is automated: you log in yourself. There is no time limit on the
login step - take as long as you need, then press the button.

Run it with the launchers (run.command on macOS, run.bat on Windows) or:
    python app.py
"""

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import scrolledtext, ttk

import compare
import scrape

HERE = Path(__file__).resolve().parent

PLATFORMS = {
    "instagram": {"title": "Instagram", "color": "#C13584"},
    "twitter": {"title": "Twitter / X", "color": "#1DA1F2"},
}

# Explicit light palette so the UI stays readable regardless of the OS theme
# (macOS dark mode otherwise renders everything dark-on-dark).
BG = "#f3f3f3"
PANEL_BG = "#ffffff"
FG = "#1a1a1a"
MUTED = "#555555"
FONT_MONO = ("Menlo", 11)


def apply_theme(root):
    style = ttk.Style(root)
    try:
        style.theme_use("clam")  # honors our colors on every platform
    except tk.TclError:
        pass
    root.configure(bg=BG)
    style.configure(".", background=BG, foreground=FG)
    style.configure("TFrame", background=BG)
    style.configure("TLabel", background=BG, foreground=FG)
    style.configure("Muted.TLabel", background=BG, foreground=MUTED)
    style.configure("TLabelframe", background=BG, foreground=FG)
    style.configure("TLabelframe.Label", background=BG, foreground=FG,
                    font=("Helvetica", 13, "bold"))
    style.configure("TButton", padding=6)
    style.configure("TEntry", fieldbackground=PANEL_BG)


class PlatformPanel(ttk.LabelFrame):
    """One self-contained panel for a single platform."""

    def __init__(self, master, platform):
        cfg = PLATFORMS[platform]
        super().__init__(master, text=f"  {cfg['title']}  ", padding=10)
        self.platform = platform
        self.queue = queue.Queue()
        self.ready_event = None
        self.worker = None

        # --- controls row ---------------------------------------------------
        top = ttk.Frame(self)
        top.pack(fill="x")

        ttk.Label(top, text="Your username:").pack(side="left")
        self.username_var = tk.StringVar()
        self.username_entry = ttk.Entry(top, textvariable=self.username_var, width=24)
        self.username_entry.pack(side="left", padx=(6, 12))

        self.open_btn = ttk.Button(top, text="1) Open browser", command=self.on_open)
        self.open_btn.pack(side="left")

        self.go_btn = ttk.Button(
            top, text="2) I'm logged in -> Fetch lists",
            command=self.on_go, state="disabled")
        self.go_btn.pack(side="left", padx=(8, 0))

        self.status_var = tk.StringVar(value="Idle.")
        ttk.Label(self, textvariable=self.status_var, foreground="#555").pack(
            anchor="w", pady=(6, 4))

        # --- body: log on the left, results on the right --------------------
        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)

        log_frame = ttk.Frame(body)
        log_frame.pack(side="left", fill="both", expand=True)
        ttk.Label(log_frame, text="Log").pack(anchor="w")
        self.log_text = scrolledtext.ScrolledText(
            log_frame, height=9, width=40, wrap="word", state="disabled",
            font=("Menlo", 10))
        self.log_text.pack(fill="both", expand=True)

        res_frame = ttk.Frame(body)
        res_frame.pack(side="left", fill="both", expand=True, padx=(10, 0))

        col_a = ttk.Frame(res_frame)
        col_a.pack(side="left", fill="both", expand=True)
        self.nfb_label = ttk.Label(col_a, text="Don't follow you back (0)")
        self.nfb_label.pack(anchor="w")
        self.nfb_list = self._make_listbox(col_a)

        col_b = ttk.Frame(res_frame)
        col_b.pack(side="left", fill="both", expand=True, padx=(8, 0))
        self.ydf_label = ttk.Label(col_b, text="You don't follow back (0)")
        self.ydf_label.pack(anchor="w")
        self.ydf_list = self._make_listbox(col_b)

        self.after(150, self._drain_queue)

    def _make_listbox(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)
        sb = ttk.Scrollbar(frame, orient="vertical")
        lb = tk.Listbox(frame, height=9, width=22, yscrollcommand=sb.set,
                        font=("Menlo", 10), activestyle="none")
        sb.config(command=lb.yview)
        sb.pack(side="right", fill="y")
        lb.pack(side="left", fill="both", expand=True)
        return lb

    # ---- logging helpers (thread-safe via queue) --------------------------

    def log(self, msg):
        self.queue.put(("log", str(msg)))

    def _append_log(self, msg):
        self.log_text.config(state="normal")
        self.log_text.insert("end", msg.rstrip("\n") + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    # ---- button handlers --------------------------------------------------

    def on_open(self):
        username = self.username_var.get().strip().lstrip("@")
        if not username:
            self.status_var.set("Please enter your username first.")
            return
        self.open_btn.config(state="disabled")
        self.username_entry.config(state="disabled")
        self.status_var.set("Opening browser... log in, then click button 2.")
        self._clear_results()

        self.ready_event = threading.Event()
        self.worker = threading.Thread(
            target=self._run, args=(username,), daemon=True)
        self.worker.start()

    def on_go(self):
        if self.ready_event:
            self.ready_event.set()
        self.go_btn.config(state="disabled")
        self.status_var.set("Fetching lists (scrolling)... please wait.")

    # ---- background worker ------------------------------------------------

    def _run(self, username):
        try:
            def on_browser_open(_driver):
                # browser is up -> let the user confirm login from the UI
                self.queue.put(("browser_ready", None))

            following, followers = scrape.collect(
                self.platform, username,
                profile_dir=str(HERE / "chrome-profile"),
                wait_for_ready=self.ready_event.wait,
                on_browser_open=on_browser_open,
                log=self.log,
            )

            # save raw lists
            scrape.save(following, str(HERE / f"{self.platform}_following.txt"))
            scrape.save(followers, str(HERE / f"{self.platform}_followers.txt"))

            result = compare.compare(following, followers)
            compare.save_lists(result, str(HERE / f"result_{self.platform}"))
            self.queue.put(("done", result))
        except Exception as exc:  # surface any failure in the UI, don't crash
            self.queue.put(("error", f"{type(exc).__name__}: {exc}"))

    # ---- queue pump (runs on the Tk main thread) --------------------------

    def _drain_queue(self):
        try:
            while True:
                kind, payload = self.queue.get_nowait()
                if kind == "log":
                    self._append_log(payload)
                elif kind == "browser_ready":
                    self.go_btn.config(state="normal")
                    self.status_var.set(
                        "Browser is open. Log in, then click button 2.")
                elif kind == "done":
                    self._render_result(payload)
                elif kind == "error":
                    self._append_log("ERROR: " + payload)
                    self.status_var.set("Error - see log.")
                    self._reset_buttons()
        except queue.Empty:
            pass
        self.after(150, self._drain_queue)

    # ---- results ----------------------------------------------------------

    def _clear_results(self):
        self.nfb_list.delete(0, "end")
        self.ydf_list.delete(0, "end")
        self.nfb_label.config(text="Don't follow you back (0)")
        self.ydf_label.config(text="You don't follow back (0)")

    def _render_result(self, r):
        nfb = r["not_following_back"]
        ydf = r["you_dont_follow_back"]
        self.nfb_list.delete(0, "end")
        for u in nfb:
            self.nfb_list.insert("end", "@" + u)
        self.ydf_list.delete(0, "end")
        for u in ydf:
            self.ydf_list.insert("end", "@" + u)
        self.nfb_label.config(text=f"Don't follow you back ({len(nfb)})")
        self.ydf_label.config(text=f"You don't follow back ({len(ydf)})")
        self.status_var.set(
            f"Done. Following {r['following_count']}, "
            f"followers {r['followers_count']}, mutuals {len(r['mutuals'])}. "
            f"Saved to result_{self.platform}/")
        self._reset_buttons()

    def _reset_buttons(self):
        self.open_btn.config(state="normal")
        self.username_entry.config(state="normal")
        self.go_btn.config(state="disabled")


def main():
    root = tk.Tk()
    root.title("Social Diff - follower / following mismatch")
    root.geometry("900x720")
    root.minsize(760, 600)

    header = ttk.Label(
        root,
        text=("Log in yourself in the browser (2FA included, no time limit), "
              "then click 'I'm logged in'."),
        foreground="#444", padding=(12, 8))
    header.pack(fill="x")

    ig = PlatformPanel(root, "instagram")
    ig.pack(fill="both", expand=True, padx=12, pady=(0, 6))

    tw = PlatformPanel(root, "twitter")
    tw.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    root.mainloop()


if __name__ == "__main__":
    main()
