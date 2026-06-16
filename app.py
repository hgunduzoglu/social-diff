#!/usr/bin/env python3
"""
app.py - Social Diff GUI

Home screen with two big buttons (Instagram / Twitter). Pick one and its own
screen opens; "Back" returns to the home screen.

For a platform you:
  1) type your own username,
  2) click "Open browser" -> a Chrome window opens, you log in (2FA included,
     no time limit),
  3) click "I'm logged in -> Fetch lists" -> the script visits your profile,
     scrolls the followers/following dialogs, collects handles and compares them.

Results (two-way mismatch) are shown on screen AND saved to .txt files.

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

# ---------------------------------------------------------------- palette
WIN_BG = "#0f1320"      # app background (deep navy)
CARD = "#1a2030"        # card / panel surface
CARD_2 = "#222a3d"      # inputs / list surfaces
INK = "#eef1f7"         # primary text
SUB = "#9aa4ba"         # muted text
LINE = "#2c3550"        # borders

IG = "#e1306c"
IG_HOVER = "#f04d83"
TW = "#1d9bf0"
TW_HOVER = "#3aabf5"
GO = "#22c55e"
GO_HOVER = "#34d36e"
NEUTRAL = "#2c3550"
NEUTRAL_HOVER = "#3a466a"
NFB = "#ff7a90"         # "don't follow you back" accent
YDF = "#5ec9ff"         # "you don't follow back" accent

PLATFORMS = {
    "instagram": {"title": "Instagram", "icon": "📷", "color": IG, "hover": IG_HOVER},
    "twitter": {"title": "Twitter / X", "icon": "𝕏", "color": TW, "hover": TW_HOVER},
}


def apply_theme(root):
    """A dark, modern, deterministic look (ignores the OS theme)."""
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    root.configure(bg=WIN_BG)

    style.configure(".", background=WIN_BG, foreground=INK, borderwidth=0)
    style.configure("TFrame", background=WIN_BG)
    style.configure("Card.TFrame", background=CARD)
    style.configure("TLabel", background=WIN_BG, foreground=INK)
    style.configure("Card.TLabel", background=CARD, foreground=INK)
    style.configure("Sub.TLabel", background=WIN_BG, foreground=SUB)
    style.configure("CardSub.TLabel", background=CARD, foreground=SUB)
    style.configure("Title.TLabel", background=WIN_BG, foreground=INK,
                    font=("Helvetica", 30, "bold"))
    style.configure("H2.TLabel", background=CARD, foreground=INK,
                    font=("Helvetica", 18, "bold"))

    # entry
    style.configure("TEntry", fieldbackground=CARD_2, foreground=INK,
                    insertcolor=INK, bordercolor=LINE, lightcolor=LINE,
                    darkcolor=LINE, padding=8)

    # buttons — one helper per accent
    def button_style(name, bg, hover, fg="#ffffff", font=("Helvetica", 13, "bold")):
        style.configure(name, background=bg, foreground=fg, font=font,
                        padding=(16, 10), borderwidth=0)
        style.map(name,
                  background=[("active", hover), ("pressed", hover),
                              ("disabled", "#39415a")],
                  foreground=[("disabled", "#7b87a3")])

    button_style("IG.TButton", IG, IG_HOVER, font=("Helvetica", 17, "bold"))
    button_style("TW.TButton", TW, TW_HOVER, font=("Helvetica", 17, "bold"))
    button_style("Go.TButton", GO, GO_HOVER)
    button_style("Stop.TButton", "#ef4444", "#f6635c")
    button_style("Neutral.TButton", NEUTRAL, NEUTRAL_HOVER, fg=INK)
    button_style("Back.TButton", WIN_BG, NEUTRAL, fg=SUB, font=("Helvetica", 13))


# ---------------------------------------------------------------- home screen

class HomeScreen(ttk.Frame):
    def __init__(self, master, on_select):
        super().__init__(master, style="TFrame")
        wrap = ttk.Frame(self, style="TFrame")
        wrap.place(relx=0.5, rely=0.5, anchor="center")

        ttk.Label(wrap, text="Social Diff", style="Title.TLabel").pack()
        ttk.Label(wrap, text="Find who doesn't follow you back — both ways.",
                  style="Sub.TLabel", font=("Helvetica", 14)).pack(pady=(6, 30))

        row = ttk.Frame(wrap, style="TFrame")
        row.pack()
        self._card(row, "instagram", on_select).pack(side="left", padx=12)
        self._card(row, "twitter", on_select).pack(side="left", padx=12)

    def _card(self, parent, platform, on_select):
        cfg = PLATFORMS[platform]
        btn = ttk.Button(
            parent, text=f"{cfg['icon']}\n{cfg['title']}",
            style=f"{'IG' if platform == 'instagram' else 'TW'}.TButton",
            width=14, command=lambda: on_select(platform))
        return btn


# ---------------------------------------------------------------- platform screen

class PlatformScreen(ttk.Frame):
    def __init__(self, master, platform, on_back):
        super().__init__(master, style="TFrame")
        cfg = PLATFORMS[platform]
        self.platform = platform
        self._on_back = on_back
        self.queue = queue.Queue()
        self.ready_event = None
        self.cancel_event = None
        self.driver = None
        self.worker = None

        # --- top bar --------------------------------------------------------
        bar = ttk.Frame(self, style="TFrame")
        bar.pack(fill="x", padx=18, pady=(16, 8))
        ttk.Button(bar, text="←  Back", style="Back.TButton",
                   command=self._go_back).pack(side="left")
        ttk.Label(bar, text=f"{cfg['icon']}  {cfg['title']}",
                  style="TLabel", font=("Helvetica", 20, "bold")).pack(side="left",
                                                                       padx=(10, 0))

        # --- controls card --------------------------------------------------
        card = tk.Frame(self, bg=CARD, highlightthickness=0)
        card.pack(fill="x", padx=18)
        inner = ttk.Frame(card, style="Card.TFrame")
        inner.pack(fill="x", padx=16, pady=14)

        ttk.Label(inner, text="Your username", style="CardSub.TLabel").grid(
            row=0, column=0, sticky="w")
        self.username_var = tk.StringVar()
        self.username_entry = ttk.Entry(inner, textvariable=self.username_var,
                                        width=26, font=("Helvetica", 14))
        self.username_entry.grid(row=1, column=0, sticky="w", pady=(4, 0))

        self.open_btn = ttk.Button(inner, text="1) Open browser",
                                   style="Neutral.TButton", command=self.on_open)
        self.open_btn.grid(row=1, column=1, padx=(12, 8))

        self.go_btn = ttk.Button(inner, text="2) I'm logged in  →  Fetch lists",
                                 style="Go.TButton", command=self.on_go,
                                 state="disabled")
        self.go_btn.grid(row=1, column=2)

        self.stop_btn = ttk.Button(inner, text="■ Stop", style="Stop.TButton",
                                   command=self.cancel, state="disabled")
        self.stop_btn.grid(row=1, column=3, padx=(8, 0))

        self.status_var = tk.StringVar(value="Enter your username and open the browser.")
        ttk.Label(self, textvariable=self.status_var, style="Sub.TLabel").pack(
            anchor="w", padx=20, pady=(10, 6))

        # --- body: results (left) + log (right) -----------------------------
        body = ttk.Frame(self, style="TFrame")
        body.pack(fill="both", expand=True, padx=18, pady=(0, 18))

        res = ttk.Frame(body, style="TFrame")
        res.pack(side="left", fill="both", expand=True)

        col_a = ttk.Frame(res, style="TFrame")
        col_a.pack(side="left", fill="both", expand=True, padx=(0, 6))
        self.nfb_label = self._col_header(col_a, "Don't follow you back (0)", NFB)
        self.nfb_list = self._make_listbox(col_a)

        col_b = ttk.Frame(res, style="TFrame")
        col_b.pack(side="left", fill="both", expand=True, padx=(6, 0))
        self.ydf_label = self._col_header(col_b, "You don't follow back (0)", YDF)
        self.ydf_list = self._make_listbox(col_b)

        log_frame = ttk.Frame(body, style="TFrame")
        log_frame.pack(side="left", fill="both", expand=True, padx=(12, 0))
        ttk.Label(log_frame, text="Log", style="Sub.TLabel").pack(anchor="w")
        self.log_text = scrolledtext.ScrolledText(
            log_frame, height=10, width=34, wrap="word", state="disabled",
            font=("Menlo", 11), bg=CARD_2, fg=SUB, insertbackground=INK,
            relief="flat", borderwidth=0, highlightthickness=1,
            highlightbackground=LINE, highlightcolor=LINE, padx=8, pady=8)
        self.log_text.pack(fill="both", expand=True)

        self.after(150, self._drain_queue)

    # ---- small builders ----
    def _col_header(self, parent, text, accent):
        lbl = tk.Label(parent, text=text, bg=accent, fg="#10141f",
                       font=("Helvetica", 12, "bold"), anchor="w", padx=10, pady=6)
        lbl.pack(fill="x")
        return lbl

    def _make_listbox(self, parent):
        frame = tk.Frame(parent, bg=LINE, highlightthickness=0)
        frame.pack(fill="both", expand=True, pady=(0, 0))
        sb = ttk.Scrollbar(frame, orient="vertical")
        lb = tk.Listbox(frame, height=12, width=20, yscrollcommand=sb.set,
                        font=("Menlo", 12), activestyle="none",
                        bg=CARD_2, fg=INK, relief="flat", borderwidth=0,
                        highlightthickness=0, selectbackground="#3a466a",
                        selectforeground=INK)
        sb.config(command=lb.yview)
        sb.pack(side="right", fill="y")
        lb.pack(side="left", fill="both", expand=True)
        return lb

    # ---- logging (thread-safe) ----
    def log(self, msg):
        self.queue.put(("log", str(msg)))

    def _append_log(self, msg):
        self.log_text.config(state="normal")
        self.log_text.insert("end", msg.rstrip("\n") + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    # ---- handlers ----
    def on_open(self):
        username = self.username_var.get().strip().lstrip("@")
        if not username:
            self.status_var.set("Please enter your username first.")
            return
        self.open_btn.config(state="disabled")
        self.username_entry.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status_var.set("Opening browser… log in, then click button 2.")
        self._clear_results()

        self.ready_event = threading.Event()
        self.cancel_event = threading.Event()
        self.worker = threading.Thread(target=self._run, args=(username,), daemon=True)
        self.worker.start()

    def on_go(self):
        if self.ready_event:
            self.ready_event.set()
        self.go_btn.config(state="disabled")
        self.status_var.set("Fetching lists (scrolling)… please wait.")

    def _wait_for_ready(self):
        """Block until the user confirms login, or returns False if cancelled."""
        while not self.ready_event.wait(0.2):
            if self.cancel_event.is_set():
                return False
        return not self.cancel_event.is_set()

    def cancel(self):
        """Stop the current run and close the browser, at any stage."""
        if self.cancel_event:
            self.cancel_event.set()
        if self.ready_event:
            self.ready_event.set()  # unblock the login wait
        d, self.driver = self.driver, None
        if d:
            try:
                d.quit()
            except Exception:
                pass
        self.stop_btn.config(state="disabled")
        self.status_var.set("Stopping…")

    def _go_back(self):
        self.cancel()
        self._on_back()

    # ---- worker ----
    def _run(self, username):
        try:
            def on_browser_open(driver):
                self.driver = driver
                self.queue.put(("browser_ready", None))

            following, followers = scrape.collect(
                self.platform, username,
                profile_dir=str(HERE / "chrome-profile"),
                wait_for_ready=self._wait_for_ready,
                on_browser_open=on_browser_open,
                log=self.log,
            )
            self.driver = None  # collect() has already closed it
            if following is None:  # cancelled during login wait
                self.queue.put(("cancelled", None))
                return

            scrape.save(following, str(HERE / f"{self.platform}_following.txt"))
            scrape.save(followers, str(HERE / f"{self.platform}_followers.txt"))

            result = compare.compare(following, followers)
            compare.save_lists(result, str(HERE / f"result_{self.platform}"))
            self.queue.put(("done", result))
        except Exception as exc:
            self.driver = None
            if self.cancel_event and self.cancel_event.is_set():
                self.queue.put(("cancelled", None))
            else:
                self.queue.put(("error", f"{type(exc).__name__}: {exc}"))

    # ---- queue pump ----
    def _drain_queue(self):
        try:
            while True:
                kind, payload = self.queue.get_nowait()
                if kind == "log":
                    self._append_log(payload)
                elif kind == "browser_ready":
                    self.go_btn.config(state="normal")
                    self.status_var.set("Browser is open. Log in, then click button 2.")
                elif kind == "done":
                    self._render_result(payload)
                elif kind == "cancelled":
                    self._append_log("Stopped. Browser closed.")
                    self.status_var.set("Stopped.")
                    self._reset_buttons()
                elif kind == "error":
                    self._append_log("ERROR: " + payload)
                    self.status_var.set("Error — see log.")
                    self._reset_buttons()
        except queue.Empty:
            pass
        self.after(150, self._drain_queue)

    # ---- results ----
    def _clear_results(self):
        self.nfb_list.delete(0, "end")
        self.ydf_list.delete(0, "end")
        self.nfb_label.config(text="Don't follow you back (0)")
        self.ydf_label.config(text="You don't follow back (0)")

    def _render_result(self, r):
        nfb, ydf = r["not_following_back"], r["you_dont_follow_back"]
        self.nfb_list.delete(0, "end")
        for u in nfb:
            self.nfb_list.insert("end", "  @" + u)
        self.ydf_list.delete(0, "end")
        for u in ydf:
            self.ydf_list.insert("end", "  @" + u)
        self.nfb_label.config(text=f"Don't follow you back ({len(nfb)})")
        self.ydf_label.config(text=f"You don't follow back ({len(ydf)})")
        self.status_var.set(
            f"Done. Following {r['following_count']}, followers "
            f"{r['followers_count']}, mutuals {len(r['mutuals'])}. "
            f"Saved to result_{self.platform}/")
        self._reset_buttons()

    def _reset_buttons(self):
        self.open_btn.config(state="normal")
        self.username_entry.config(state="normal")
        self.go_btn.config(state="disabled")
        self.stop_btn.config(state="disabled")


# ---------------------------------------------------------------- app shell

class App:
    def __init__(self, root):
        self.root = root
        self.container = ttk.Frame(root, style="TFrame")
        self.container.pack(fill="both", expand=True)

        self.home = HomeScreen(self.container, on_select=self.show_platform)
        self.screens = {
            p: PlatformScreen(self.container, p, on_back=self.show_home)
            for p in PLATFORMS
        }
        self.show_home()

    def _hide_all(self):
        self.home.pack_forget()
        for s in self.screens.values():
            s.pack_forget()

    def show_home(self):
        self._hide_all()
        self.home.pack(fill="both", expand=True)

    def show_platform(self, platform):
        self._hide_all()
        self.screens[platform].pack(fill="both", expand=True)


def main():
    root = tk.Tk()
    root.title("Social Diff")
    root.geometry("980x680")
    root.minsize(860, 600)
    apply_theme(root)
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
