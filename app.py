#!/usr/bin/env python3
"""
app.py - Social Diff GUI

Home screen with two platform cards (Instagram / Twitter). Pick one and a
step-by-step screen opens:

  Step 1  Log in (you open the browser and log in yourself; 2FA included).
  Step 2  You open your FOLLOWERS list in the browser, then click "collect"
          and the program scrolls it and gathers the handles.
  Step 3  Same for your FOLLOWING list.
  Result  Two-way mismatch shown on screen and saved to .txt files.

The program never navigates for you — you drive the browser, it only scrolls
the open list and compares. "Stop" / "Back" close the browser at any time.

Run it with the launchers (run.command / run.bat / run.sh) or:  python app.py
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
WIN_BG = "#0f1320"
CARD = "#1a2030"
CARD_2 = "#222a3d"
INK = "#eef1f7"
SUB = "#9aa4ba"
LINE = "#2c3550"

IG = "#e1306c"
IG_HOVER = "#f04d83"
TW = "#1d9bf0"
TW_HOVER = "#3aabf5"
GO = "#22c55e"
GO_HOVER = "#34d36e"
NEUTRAL = "#2c3550"
NEUTRAL_HOVER = "#3a466a"
NFB = "#ff7a90"
YDF = "#5ec9ff"

PLATFORMS = {
    "instagram": {"title": "Instagram", "color": IG, "hover": IG_HOVER},
    "twitter": {"title": "Twitter / X", "color": TW, "hover": TW_HOVER},
}


# ---------------------------------------------------------------- logos (canvas-drawn)

def _round_rect_points(x1, y1, x2, y2, r):
    return [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
    ]


def make_logo(parent, platform, size=72, bg=CARD, fg="#ffffff"):
    c = tk.Canvas(parent, width=size, height=size, bg=bg,
                  highlightthickness=0, bd=0)
    s = size
    if platform == "instagram":
        pad = s * 0.13
        r = s * 0.26
        w = max(2, int(s * 0.085))
        c.create_polygon(_round_rect_points(pad, pad, s - pad, s - pad, r),
                         smooth=True, fill="", outline=fg, width=w)
        cr = s * 0.20  # lens
        cx = cy = s / 2
        c.create_oval(cx - cr, cy - cr, cx + cr, cy + cr,
                      outline=fg, width=w)
        dot = s * 0.045  # top-right dot
        dx, dy = s - pad - s * 0.11, pad + s * 0.11
        c.create_oval(dx - dot, dy - dot, dx + dot, dy + dot, fill=fg, outline=fg)
    else:  # twitter / x  -> the X glyph
        pad = s * 0.20
        w = max(3, int(s * 0.14))
        c.create_line(pad, pad, s - pad, s - pad, fill=fg, width=w,
                      capstyle="round")
        c.create_line(s - pad, pad, pad, s - pad, fill=fg, width=w,
                      capstyle="round")
    return c


# ---------------------------------------------------------------- theme

def apply_theme(root):
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
    style.configure("Step.TLabel", background=WIN_BG, foreground=SUB,
                    font=("Helvetica", 12, "bold"))
    style.configure("Instr.TLabel", background=WIN_BG, foreground=INK,
                    font=("Helvetica", 20, "bold"))

    style.configure("TEntry", fieldbackground=CARD_2, foreground=INK,
                    insertcolor=INK, bordercolor=LINE, lightcolor=LINE,
                    darkcolor=LINE, padding=8)

    def button_style(name, bg, hover, fg="#ffffff", font=("Helvetica", 13, "bold")):
        style.configure(name, background=bg, foreground=fg, font=font,
                        padding=(18, 11), borderwidth=0)
        style.map(name,
                  background=[("active", hover), ("pressed", hover),
                              ("disabled", "#39415a")],
                  foreground=[("disabled", "#7b87a3")])

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
        Card(row, "instagram", on_select).pack(side="left", padx=14)
        Card(row, "twitter", on_select).pack(side="left", padx=14)


class Card(tk.Frame):
    """A big, clickable platform card with its logo."""

    def __init__(self, parent, platform, on_select):
        cfg = PLATFORMS[platform]
        super().__init__(parent, bg=cfg["color"], cursor="hand2",
                         highlightthickness=0, width=210, height=190)
        self.pack_propagate(False)
        self.cfg = cfg
        self.platform = platform

        self.logo = make_logo(self, platform, 78, bg=cfg["color"])
        self.logo.pack(pady=(34, 12))
        self.lbl = tk.Label(self, text=cfg["title"], bg=cfg["color"],
                            fg="#ffffff", font=("Helvetica", 18, "bold"))
        self.lbl.pack()

        for w in (self, self.logo, self.lbl):
            w.bind("<Button-1>", lambda _e: on_select(platform))
            w.bind("<Enter>", lambda _e: self._tint(cfg["hover"]))
            w.bind("<Leave>", lambda _e: self._tint(cfg["color"]))

    def _tint(self, color):
        self.config(bg=color)
        self.logo.config(bg=color)
        self.lbl.config(bg=color)


# ---------------------------------------------------------------- platform screen

class PlatformScreen(ttk.Frame):
    def __init__(self, master, platform, on_back):
        super().__init__(master, style="TFrame")
        cfg = PLATFORMS[platform]
        self.platform = platform
        self._on_back = on_back
        self.queue = queue.Queue()
        self.cancel_event = None
        self.driver = None
        self.followers = None
        self.following = None

        # --- top bar --------------------------------------------------------
        bar = ttk.Frame(self, style="TFrame")
        bar.pack(fill="x", padx=18, pady=(16, 6))
        ttk.Button(bar, text="←  Back", style="Back.TButton",
                   command=self._go_back).pack(side="left")
        make_logo(bar, platform, 26, bg=WIN_BG, fg=cfg["color"]).pack(
            side="left", padx=(10, 6))
        ttk.Label(bar, text=cfg["title"], style="TLabel",
                  font=("Helvetica", 18, "bold")).pack(side="left")
        self.step_var = tk.StringVar(value="Step 1 / 3")
        ttk.Label(bar, textvariable=self.step_var, style="Step.TLabel").pack(
            side="right")

        # --- instruction card ----------------------------------------------
        card = tk.Frame(self, bg=CARD, highlightthickness=0)
        card.pack(fill="x", padx=18, pady=(4, 10))
        inner = ttk.Frame(card, style="Card.TFrame")
        inner.pack(fill="x", padx=18, pady=16)

        self.instr_var = tk.StringVar()
        ttk.Label(inner, textvariable=self.instr_var, style="Card.TLabel",
                  font=("Helvetica", 19, "bold")).pack(anchor="w")
        self.hint_var = tk.StringVar()
        ttk.Label(inner, textvariable=self.hint_var, style="CardSub.TLabel",
                  font=("Helvetica", 13), wraplength=820, justify="left").pack(
            anchor="w", pady=(8, 14))

        btnrow = ttk.Frame(inner, style="Card.TFrame")
        btnrow.pack(anchor="w")
        self.primary_btn = ttk.Button(btnrow, text="Open browser",
                                      style="Neutral.TButton")
        self.primary_btn.pack(side="left")
        self.stop_btn = ttk.Button(btnrow, text="■ Stop", style="Stop.TButton",
                                   command=self.stop, state="disabled")
        self.stop_btn.pack(side="left", padx=(10, 0))

        self.status_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.status_var, style="Sub.TLabel").pack(
            anchor="w", padx=20)

        # --- body: results (left) + log (right) -----------------------------
        self.body = ttk.Frame(self, style="TFrame")
        self.body.pack(fill="both", expand=True, padx=18, pady=(8, 18))

        self.results = ttk.Frame(self.body, style="TFrame")  # packed at result step
        col_a = ttk.Frame(self.results, style="TFrame")
        col_a.pack(side="left", fill="both", expand=True, padx=(0, 6))
        self.nfb_label = self._col_header(col_a, "Don't follow you back (0)", NFB)
        self.nfb_list = self._make_listbox(col_a)
        col_b = ttk.Frame(self.results, style="TFrame")
        col_b.pack(side="left", fill="both", expand=True, padx=(6, 0))
        self.ydf_label = self._col_header(col_b, "You don't follow back (0)", YDF)
        self.ydf_list = self._make_listbox(col_b)

        log_frame = ttk.Frame(self.body, style="TFrame")
        log_frame.pack(side="right", fill="both", expand=True)
        ttk.Label(log_frame, text="Log", style="Sub.TLabel").pack(anchor="w")
        self.log_text = scrolledtext.ScrolledText(
            log_frame, height=12, width=40, wrap="word", state="disabled",
            font=("Menlo", 11), bg=CARD_2, fg=SUB, insertbackground=INK,
            relief="flat", borderwidth=0, highlightthickness=1,
            highlightbackground=LINE, highlightcolor=LINE, padx=8, pady=8)
        self.log_text.pack(fill="both", expand=True)

        self._set_step("login")
        self.after(150, self._drain_queue)

    # ---- small builders ----
    def _col_header(self, parent, text, accent):
        lbl = tk.Label(parent, text=text, bg=accent, fg="#10141f",
                       font=("Helvetica", 12, "bold"), anchor="w", padx=10, pady=6)
        lbl.pack(fill="x")
        return lbl

    def _make_listbox(self, parent):
        frame = tk.Frame(parent, bg=LINE, highlightthickness=0)
        frame.pack(fill="both", expand=True)
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

    # ---- logging ----
    def log(self, msg):
        self.queue.put(("log", str(msg)))

    def _append_log(self, msg):
        self.log_text.config(state="normal")
        self.log_text.insert("end", msg.rstrip("\n") + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    # ---- step machine ----
    def _primary(self, text, command, style, disabled=False):
        self.primary_btn.config(text=text, command=(command or (lambda: None)),
                                style=style,
                                state=("disabled" if disabled else "normal"))

    def _open_hint(self, which):
        if self.platform == "instagram":
            return (f"On your profile page, click “{which}” so the popup list "
                    f"opens and shows the names. Then click the button below.")
        return (f"Go to your {which} page (x.com/<your-username>/{which}) so the "
                f"list is visible. Then click the button below.")

    def _set_step(self, step):
        self.step = step
        self._show_results(step == "result")
        if step == "login":
            self.step_var.set("Step 1 / 3")
            self.instr_var.set("Log in to your account")
            self.hint_var.set("Click below to open the browser, then log in "
                              "(2FA / checkpoint included — take your time).")
            self._primary("Open browser", self.on_open_browser, "Neutral.TButton")
        elif step == "followers":
            self.step_var.set("Step 2 / 3")
            self.instr_var.set("Open your FOLLOWERS list")
            self.hint_var.set(self._open_hint("followers"))
            self._primary("I opened it  →  Collect followers",
                          lambda: self.on_collect("followers"), "Go.TButton")
        elif step == "following":
            self.step_var.set("Step 3 / 3")
            self.instr_var.set("Open your FOLLOWING list")
            self.hint_var.set(self._open_hint("following"))
            self._primary("I opened it  →  Collect following",
                          lambda: self.on_collect("following"), "Go.TButton")
        elif step == "result":
            self.step_var.set("Done")
            self.instr_var.set("Result")
            self.hint_var.set(f"Saved to result_{self.platform}/. "
                              f"Press Back to start over.")
            self._primary("Done", None, "Neutral.TButton", disabled=True)

    def _show_results(self, show):
        if show:
            self.results.pack(side="left", fill="both", expand=True, padx=(0, 12))
        else:
            self.results.pack_forget()

    # ---- actions ----
    def on_open_browser(self):
        self.primary_btn.config(state="disabled")
        self.cancel_event = threading.Event()
        self.stop_btn.config(state="normal")
        self.status_var.set("Opening browser…")
        threading.Thread(target=self._open_worker, daemon=True).start()

    def _open_worker(self):
        try:
            self.driver = scrape.open_browser(
                self.platform, profile_dir=str(HERE / "chrome-profile"),
                log=self.log)
            self.queue.put(("browser_ready", None))
        except Exception as exc:
            self.queue.put(("error", f"{type(exc).__name__}: {exc}"))

    def on_collect(self, kind):
        self.primary_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status_var.set(f"Collecting {kind}… scrolling, please wait.")
        threading.Thread(target=self._collect_worker, args=(kind,),
                         daemon=True).start()

    def _collect_worker(self, kind):
        try:
            handles = scrape.harvest_open_list(
                self.driver, self.platform, log=self.log,
                should_stop=lambda: self.cancel_event.is_set())
            if self.cancel_event.is_set():
                self.queue.put(("stopped", None))
            else:
                self.queue.put(("collected", (kind, handles)))
        except Exception as exc:
            if self.cancel_event and self.cancel_event.is_set():
                self.queue.put(("stopped", None))
            else:
                self.queue.put(("error", f"{type(exc).__name__}: {exc}"))

    def stop(self):
        if self.cancel_event:
            self.cancel_event.set()
        scrape.close_browser(self.driver)
        self.driver = None
        self.followers = self.following = None
        self.stop_btn.config(state="disabled")
        self._set_step("login")
        self.status_var.set("Stopped. Browser closed.")

    def _go_back(self):
        self.stop()
        self._on_back()

    # ---- queue pump ----
    def _drain_queue(self):
        try:
            while True:
                kind, payload = self.queue.get_nowait()
                if kind == "log":
                    self._append_log(payload)
                elif kind == "browser_ready":
                    self.status_var.set("Logged in? Click Continue to start.")
                    self._primary("I'm logged in  →  Continue",
                                  lambda: self._set_step("followers"),
                                  "Go.TButton")
                elif kind == "collected":
                    self._on_collected(*payload)
                elif kind == "stopped":
                    self.status_var.set("Stopped. Browser closed.")
                elif kind == "error":
                    self._append_log("ERROR: " + payload)
                    self.status_var.set("Error — see log. You can retry.")
                    self.primary_btn.config(state="normal")
                    self.stop_btn.config(state="disabled")
        except queue.Empty:
            pass
        self.after(150, self._drain_queue)

    def _on_collected(self, kind, handles):
        if not handles:
            self.status_var.set(
                f"No users found — make sure the {kind} list is open and "
                f"visible, then try again.")
            self.primary_btn.config(state="normal")
            return
        self.log(f"   → {len(handles)} {kind} collected.")
        if kind == "followers":
            self.followers = handles
            self._set_step("following")
            self.status_var.set(f"{len(handles)} followers collected. "
                                f"Now open your following list.")
        else:
            self.following = handles
            self._finish()

    def _finish(self):
        scrape.save(self.following, str(HERE / f"{self.platform}_following.txt"))
        scrape.save(self.followers, str(HERE / f"{self.platform}_followers.txt"))
        result = compare.compare(self.following, self.followers)
        compare.save_lists(result, str(HERE / f"result_{self.platform}"))
        scrape.close_browser(self.driver)
        self.driver = None
        self.stop_btn.config(state="disabled")
        self._set_step("result")
        self._render_result(result)

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
    root.geometry("980x700")
    root.minsize(880, 620)
    apply_theme(root)
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
