import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import requests
import time
import csv
import os
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

#  THEME & COLOR CONSTANTS  (dark professional palette)

BG_DARK       = "#0d1117"   # Main window background
BG_PANEL      = "#161b22"   # Panel / card background
BG_INPUT      = "#21262d"   # Input fields
BG_HEADER     = "#010409"   # Header bar
BORDER_COLOR  = "#30363d"   # Subtle borders

ACCENT_BLUE   = "#58a6ff"   # Primary accent (buttons, highlights)
ACCENT_GREEN  = "#3fb950"   # Online / success
ACCENT_CYAN   = "#79c0ff"   # Redirected
ACCENT_YELLOW = "#d29922"   # Client error / warning
ACCENT_RED    = "#f85149"   # Server error
ACCENT_PURPLE = "#bc8cff"   # Connection error
ACCENT_GRAY   = "#8b949e"   # Muted / disabled text

TEXT_PRIMARY   = "#e6edf3"  # Main readable text
TEXT_SECONDARY = "#8b949e"  # Subtitles, labels
TEXT_MUTED     = "#484f58"  # Placeholder text

# Font definitions
FONT_TITLE    = ("Segoe UI", 18, "bold")
FONT_SUBTITLE = ("Segoe UI", 10)
FONT_LABEL    = ("Segoe UI", 9)
FONT_MONO     = ("Consolas", 9)
FONT_BOLD     = ("Segoe UI", 9, "bold")
FONT_BUTTON   = ("Segoe UI", 9, "bold")

#  CORE URL CHECKING LOGIC  (same engine as CLI version)

DEFAULT_TIMEOUT = 10
MAX_RETRIES     = 2
MAX_THREADS     = 10
REPORTS_DIR     = "reports"


def is_valid_url(url: str) -> bool:
    """Validate a URL with a regex before sending any network request."""
    pattern = re.compile(
        r'^(https?://)?'
        r'([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}'
        r'(:\d+)?'
        r'(/[^\s]*)?$',
        re.IGNORECASE
    )
    return bool(pattern.match(url.strip()))


def normalize_url(url: str) -> str:
    """Prepend https:// if the URL has no scheme."""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def classify_status(status_code: int) -> tuple:
    """
    Map an HTTP status code to (emoji, hex_color, label, category).
    Used to color rows in the results table.
    """
    if 200 <= status_code < 300:
        return ("✅", ACCENT_GREEN,  "Online",       "online")
    elif 300 <= status_code < 400:
        return ("🔄", ACCENT_CYAN,   "Redirected",   "redirected")
    elif 400 <= status_code < 500:
        return ("⚠️",  ACCENT_YELLOW, "Client Error", "client_error")
    elif 500 <= status_code < 600:
        return ("❌", ACCENT_RED,    "Server Error", "server_error")
    else:
        return ("❓", ACCENT_GRAY,   "Unknown",      "unknown")


def check_url(url: str, timeout: int = DEFAULT_TIMEOUT,
              retries: int = MAX_RETRIES) -> dict:
    """
    Send an HTTP GET to the given URL and return a result dict.
    Retries on connection error up to `retries` times.
    """
    original_url = url

    if not is_valid_url(url):
        return {
            "url":          original_url,
            "status_code":  "INVALID",
            "status_label": "Invalid URL",
            "category":     "error",
            "emoji":        "🚫",
            "color":        ACCENT_PURPLE,
            "response_ms":  None,
            "error":        "URL failed validation",
            "checked_at":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    url = normalize_url(url)
    attempt    = 0
    last_error = None

    while attempt < retries:
        attempt += 1
        try:
            start = time.time()
            resp  = requests.get(
                url,
                timeout=timeout,
                allow_redirects=True,
                headers={"User-Agent": "URLStatusChecker-GUI/2.0"}
            )
            elapsed_ms = round((time.time() - start) * 1000, 2)
            emoji, color, label, category = classify_status(resp.status_code)
            return {
                "url":          original_url,
                "status_code":  resp.status_code,
                "status_label": label,
                "category":     category,
                "emoji":        emoji,
                "color":        color,
                "response_ms":  elapsed_ms,
                "error":        None,
                "checked_at":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        except requests.exceptions.ConnectionError as e:
            last_error = f"Connection Error"
        except requests.exceptions.Timeout:
            last_error = f"Timeout ({timeout}s)"
        except requests.exceptions.TooManyRedirects:
            last_error = "Too Many Redirects"
            break
        except Exception as e:
            last_error = f"Error: {str(e)[:50]}"

        if attempt < retries:
            time.sleep(1)

    return {
        "url":          original_url,
        "status_code":  "ERROR",
        "status_label": "Unreachable",
        "category":     "error",
        "emoji":        "💥",
        "color":        ACCENT_RED,
        "response_ms":  None,
        "error":        last_error,
        "checked_at":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


#  EXPORT HELPERS

def ensure_reports_dir():
    os.makedirs(REPORTS_DIR, exist_ok=True)


def save_as_csv(results: list, filepath: str) -> str:
    fieldnames = ["url", "status_code", "status_label",
                  "category", "response_ms", "error", "checked_at"]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({k: r.get(k, "") for k in fieldnames})
    return filepath


def save_as_txt(results: list, filepath: str) -> str:
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("URL STATUS CHECKER — REPORT\n")
        f.write(f"Generated : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 70 + "\n\n")
        for r in results:
            f.write(f"URL          : {r['url']}\n")
            f.write(f"Status Code  : {r['status_code']}\n")
            f.write(f"Status Label : {r['status_label']}\n")
            f.write(f"Response Time: {r['response_ms']} ms\n")
            f.write(f"Checked At   : {r['checked_at']}\n")
            if r.get("error"):
                f.write(f"Error        : {r['error']}\n")
            f.write("-" * 70 + "\n")
    return filepath


#  CUSTOM WIDGETS

class StatCard(tk.Frame):
    """
    A small card widget that displays a stat (number + label + colored dot).
    Used in the summary bar at the bottom.
    """
    def __init__(self, parent, label: str, color: str, **kwargs):
        super().__init__(parent, bg=BG_PANEL, **kwargs)
        self.configure(
            padx=14, pady=10,
            relief="flat",
            highlightbackground=BORDER_COLOR,
            highlightthickness=1
        )

        # Colored dot
        dot = tk.Label(self, text="●", fg=color, bg=BG_PANEL,
                       font=("Segoe UI", 11))
        dot.pack(side="left", padx=(0, 6))

        # Value (big number)
        self.value_var = tk.StringVar(value="0")
        value_label = tk.Label(self, textvariable=self.value_var,
                               fg=TEXT_PRIMARY, bg=BG_PANEL,
                               font=("Segoe UI", 16, "bold"))
        value_label.pack(side="left", padx=(0, 5))

        # Label text
        tk.Label(self, text=label, fg=TEXT_SECONDARY, bg=BG_PANEL,
                 font=FONT_LABEL).pack(side="left")

    def set(self, value):
        self.value_var.set(str(value))


class PlaceholderText(tk.Text):
    """
    A Text widget with placeholder (hint) text support.
    The placeholder clears on first focus.
    """
    def __init__(self, parent, placeholder: str, **kwargs):
        super().__init__(parent, **kwargs)
        self.placeholder      = placeholder
        self.placeholder_color = TEXT_MUTED
        self.default_fg       = kwargs.get("fg", TEXT_PRIMARY)
        self._showing_placeholder = False

        self.bind("<FocusIn>",  self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        self._show_placeholder()

    def _show_placeholder(self):
        self.insert("1.0", self.placeholder)
        self.config(fg=self.placeholder_color)
        self._showing_placeholder = True

    def _on_focus_in(self, _):
        if self._showing_placeholder:
            self.delete("1.0", "end")
            self.config(fg=self.default_fg)
            self._showing_placeholder = False

    def _on_focus_out(self, _):
        if not self.get("1.0", "end").strip():
            self._show_placeholder()

    def get_real_text(self) -> str:
        """Return text without the placeholder."""
        if self._showing_placeholder:
            return ""
        return self.get("1.0", "end").strip()


#  MAIN APPLICATION CLASS

class URLCheckerApp(tk.Tk):
    """
    The main Tkinter application window.

    Layout (top → bottom):
      1. Header bar     — logo, title, subtitle
      2. Input panel    — URL textarea + settings row
      3. Action toolbar — Check / Stop / Clear / Export buttons
      4. Progress bar   — animated during checks
      5. Results table  — scrollable Treeview with color-coded rows
      6. Log panel      — live status messages
      7. Summary bar    — stat cards (Total / Online / Errors etc.)
    """

    def __init__(self):
        super().__init__()

        # ── Window setup ───────────────────────────────────────────────────────
        self.title("🌐 URL Status Checker v2.0")
        self.geometry("1050x780")
        self.minsize(860, 640)
        self.configure(bg=BG_DARK)
        self._center_window()
        self._apply_style()

        # ── State ──────────────────────────────────────────────────────────────
        self.results:         list = []          # All check results so far
        self.is_checking:     bool = False       # True while a check is running
        self._stop_event           = threading.Event()
        self._continuous_job       = None        # After() job id for continuous mode

        # ── Build UI ───────────────────────────────────────────────────────────
        self._build_header()
        self._build_input_panel()
        self._build_toolbar()
        self._build_progress()
        self._build_results_table()
        self._build_log_panel()
        self._build_summary_bar()

        # ── Welcome log message ────────────────────────────────────────────────
        self._log("👋  Welcome! Enter URLs above and click  Check URLs  to begin.", ACCENT_BLUE)

    #  WINDOW HELPERS

    def _center_window(self):
        """Center the window on screen."""
        self.update_idletasks()
        w, h = 1050, 780
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x  = (sw - w) // 2
        y  = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _apply_style(self):
        """Configure ttk styles for the dark theme."""
        style = ttk.Style(self)
        style.theme_use("clam")

        # ── Treeview (results table) ───────────────────────────────────────────
        style.configure("Results.Treeview",
            background    = BG_PANEL,
            foreground    = TEXT_PRIMARY,
            fieldbackground = BG_PANEL,
            rowheight     = 28,
            borderwidth   = 0,
            font          = FONT_MONO,
        )
        style.configure("Results.Treeview.Heading",
            background    = BG_DARK,
            foreground    = ACCENT_BLUE,
            borderwidth   = 0,
            font          = FONT_BOLD,
            relief        = "flat",
        )
        style.map("Results.Treeview",
            background=[("selected", "#1f2937")],
            foreground=[("selected", TEXT_PRIMARY)],
        )
        style.map("Results.Treeview.Heading",
            background=[("active", BG_INPUT)],
        )

        # ── Progressbar ───────────────────────────────────────────────────────
        style.configure("Accent.Horizontal.TProgressbar",
            troughcolor = BG_INPUT,
            background  = ACCENT_BLUE,
            borderwidth = 0,
            thickness   = 4,
        )

        # ── Scrollbar ─────────────────────────────────────────────────────────
        style.configure("Dark.Vertical.TScrollbar",
            troughcolor = BG_PANEL,
            background  = BORDER_COLOR,
            borderwidth = 0,
            arrowcolor  = ACCENT_GRAY,
        )

    #  HEADER

    def _build_header(self):
        """Top header bar with logo, title, and subtitle."""
        header = tk.Frame(self, bg=BG_HEADER, height=70)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        # Left side — logo + title
        left = tk.Frame(header, bg=BG_HEADER)
        left.pack(side="left", padx=22, pady=14)

        tk.Label(left, text="🌐", bg=BG_HEADER,
                 font=("Segoe UI", 22)).pack(side="left", padx=(0, 10))

        title_block = tk.Frame(left, bg=BG_HEADER)
        title_block.pack(side="left")

        tk.Label(title_block, text="URL Status Checker",
                 fg=TEXT_PRIMARY, bg=BG_HEADER,
                 font=FONT_TITLE).pack(anchor="w")
        tk.Label(title_block, text="Check websites · Multithreaded · Export reports",
                 fg=TEXT_SECONDARY, bg=BG_HEADER,
                 font=FONT_SUBTITLE).pack(anchor="w")

        # Right side — version badge
        badge = tk.Frame(header, bg="#1f2937",
                         highlightbackground=BORDER_COLOR,
                         highlightthickness=1)
        badge.pack(side="right", padx=22, pady=20)
        tk.Label(badge, text=" v2.0  GUI ", fg=ACCENT_BLUE, bg="#1f2937",
                 font=("Segoe UI", 8, "bold"),
                 padx=6, pady=3).pack()

        # Bottom separator
        tk.Frame(self, bg=BORDER_COLOR, height=1).pack(fill="x")

    #  INPUT PANEL

    def _build_input_panel(self):
        """URL textarea + settings row (timeout, threads, retry)."""
        outer = tk.Frame(self, bg=BG_DARK, padx=16, pady=12)
        outer.pack(fill="x")

        # ── URL Input card ─────────────────────────────────────────────────────
        card = tk.Frame(outer, bg=BG_PANEL,
                        highlightbackground=BORDER_COLOR,
                        highlightthickness=1)
        card.pack(fill="x")

        # Card header row
        hdr = tk.Frame(card, bg=BG_PANEL)
        hdr.pack(fill="x", padx=14, pady=(10, 4))

        tk.Label(hdr, text="URLs to Check",
                 fg=TEXT_PRIMARY, bg=BG_PANEL,
                 font=FONT_BOLD).pack(side="left")
        tk.Label(hdr, text="one per line  •  or comma-separated",
                 fg=TEXT_SECONDARY, bg=BG_PANEL,
                 font=FONT_LABEL).pack(side="left", padx=10)

        # Import file button
        btn_import = tk.Button(
            hdr, text="📂  Import from file",
            bg=BG_INPUT, fg=ACCENT_BLUE,
            activebackground=BORDER_COLOR, activeforeground=ACCENT_BLUE,
            relief="flat", cursor="hand2", font=FONT_LABEL,
            padx=10, pady=3,
            command=self._import_from_file
        )
        btn_import.pack(side="right")

        # URL Text area
        self.url_input = PlaceholderText(
            card,
            placeholder=(
                "https://www.google.com\n"
                "https://www.github.com\n"
                "https://www.wikipedia.org\n"
                "# Lines starting with # are ignored"
            ),
            bg=BG_INPUT, fg=TEXT_PRIMARY,
            insertbackground=ACCENT_BLUE,
            relief="flat", font=FONT_MONO,
            height=6, padx=10, pady=8,
            selectbackground="#2d3748",
            wrap="none",
        )
        self.url_input.pack(fill="x", padx=14, pady=(0, 12))

        # ── Settings row ───────────────────────────────────────────────────────
        settings = tk.Frame(outer, bg=BG_DARK, pady=8)
        settings.pack(fill="x")

        def _make_setting(parent, label, default, width=5):
            """Helper to create a label + spinbox pair."""
            f = tk.Frame(parent, bg=BG_DARK)
            f.pack(side="left", padx=(0, 20))
            tk.Label(f, text=label, fg=TEXT_SECONDARY, bg=BG_DARK,
                     font=FONT_LABEL).pack(side="left", padx=(0, 6))
            var = tk.StringVar(value=str(default))
            sb = tk.Spinbox(
                f, from_=1, to=120, textvariable=var,
                bg=BG_INPUT, fg=TEXT_PRIMARY,
                insertbackground=ACCENT_BLUE,
                buttonbackground=BG_INPUT,
                relief="flat", font=FONT_MONO,
                width=width, highlightthickness=1,
                highlightbackground=BORDER_COLOR,
            )
            sb.pack(side="left")
            return var

        self.timeout_var  = _make_setting(settings, "Timeout (s)",  DEFAULT_TIMEOUT, 4)
        self.threads_var  = _make_setting(settings, "Threads",       MAX_THREADS, 4)
        self.retries_var  = _make_setting(settings, "Retries",       MAX_RETRIES, 4)

        # Continuous mode toggle
        cont_frame = tk.Frame(settings, bg=BG_DARK)
        cont_frame.pack(side="left", padx=(20, 0))

        self.continuous_var = tk.BooleanVar(value=False)
        chk = tk.Checkbutton(
            cont_frame, text="Continuous",
            variable=self.continuous_var,
            bg=BG_DARK, fg=TEXT_SECONDARY,
            activebackground=BG_DARK, activeforeground=TEXT_PRIMARY,
            selectcolor=BG_INPUT,
            relief="flat", font=FONT_LABEL,
            cursor="hand2",
            command=self._toggle_interval_field,
        )
        chk.pack(side="left", padx=(0, 6))

        self.interval_var = tk.StringVar(value="30")
        self.interval_spin = tk.Spinbox(
            cont_frame, from_=5, to=3600,
            textvariable=self.interval_var,
            bg=BG_INPUT, fg=TEXT_MUTED,
            buttonbackground=BG_INPUT,
            relief="flat", font=FONT_MONO,
            width=5, state="disabled",
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
        )
        self.interval_spin.pack(side="left")
        tk.Label(cont_frame, text="s", fg=TEXT_SECONDARY, bg=BG_DARK,
                 font=FONT_LABEL).pack(side="left", padx=(4, 0))

    def _toggle_interval_field(self):
        """Enable/disable the interval spinbox based on continuous checkbox."""
        if self.continuous_var.get():
            self.interval_spin.config(state="normal", fg=TEXT_PRIMARY)
        else:
            self.interval_spin.config(state="disabled", fg=TEXT_MUTED)
            if self._continuous_job:
                self.after_cancel(self._continuous_job)
                self._continuous_job = None

    #  TOOLBAR

    def _build_toolbar(self):
        """Action buttons: Check, Stop, Clear, Export CSV, Export TXT."""
        bar = tk.Frame(self, bg=BG_DARK, padx=16, pady=4)
        bar.pack(fill="x")

        def _btn(parent, text, color, cmd, side="left", padx=(0, 8)):
            b = tk.Button(
                parent, text=text,
                bg=color, fg=BG_DARK if color != BG_INPUT else TEXT_SECONDARY,
                activebackground=color, activeforeground=BG_DARK,
                relief="flat", cursor="hand2", font=FONT_BUTTON,
                padx=14, pady=6, command=cmd
            )
            b.pack(side=side, padx=padx)
            return b

        self.btn_check  = _btn(bar, "▶  Check URLs",  ACCENT_BLUE,   self._start_check)
        self.btn_stop   = _btn(bar, "⏹  Stop",        ACCENT_YELLOW, self._stop_check)
        self.btn_clear  = _btn(bar, "🗑  Clear",       BG_INPUT,      self._clear_all)

        # Export buttons (right side)
        _btn(bar, "📄  Export CSV", ACCENT_GREEN,  self._export_csv, side="right", padx=(8, 0))
        _btn(bar, "📝  Export TXT", ACCENT_CYAN,   self._export_txt, side="right", padx=(8, 0))

        self.btn_stop.config(state="disabled")

    #  PROGRESS BAR

    def _build_progress(self):
        """Thin animated progress bar + status label."""
        pf = tk.Frame(self, bg=BG_DARK, padx=16)
        pf.pack(fill="x", pady=(2, 0))

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            pf, variable=self.progress_var,
            style="Accent.Horizontal.TProgressbar",
            mode="determinate", length=400
        )
        self.progress_bar.pack(fill="x", pady=(0, 2))

        self.status_label_var = tk.StringVar(value="Ready")
        tk.Label(
            pf, textvariable=self.status_label_var,
            fg=TEXT_MUTED, bg=BG_DARK, font=FONT_LABEL, anchor="w"
        ).pack(fill="x")

    #  RESULTS TABLE

    def _build_results_table(self):
        """
        Scrollable Treeview showing: #, Status, URL, Code, Response Time,
        Category, Checked At.
        Rows are color-tagged by category.
        """
        frame = tk.Frame(self, bg=BG_DARK, padx=16, pady=8)
        frame.pack(fill="both", expand=True)

        # Table header label
        lbl_frame = tk.Frame(frame, bg=BG_DARK)
        lbl_frame.pack(fill="x", pady=(0, 6))
        tk.Label(lbl_frame, text="Results",
                 fg=TEXT_PRIMARY, bg=BG_DARK,
                 font=FONT_BOLD).pack(side="left")
        self.row_count_var = tk.StringVar(value="0 rows")
        tk.Label(lbl_frame, textvariable=self.row_count_var,
                 fg=TEXT_MUTED, bg=BG_DARK,
                 font=FONT_LABEL).pack(side="left", padx=8)

        # Container with border
        container = tk.Frame(frame, bg=BG_PANEL,
                              highlightbackground=BORDER_COLOR,
                              highlightthickness=1)
        container.pack(fill="both", expand=True)

        # Columns definition
        columns = ("num", "status", "url", "code", "time", "category", "checked_at")
        self.tree = ttk.Treeview(
            container, columns=columns, show="headings",
            style="Results.Treeview", selectmode="browse"
        )

        # Column headings & widths
        col_config = [
            ("num",        "#",           42,  "center"),
            ("status",     "Status",      70,  "center"),
            ("url",        "URL",         330, "w"),
            ("code",       "Code",        60,  "center"),
            ("time",       "Time (ms)",   90,  "center"),
            ("category",   "Category",    110, "center"),
            ("checked_at", "Checked At",  148, "center"),
        ]
        for col_id, heading, width, anchor in col_config:
            self.tree.heading(col_id, text=heading)
            self.tree.column(col_id, width=width, anchor=anchor, minwidth=40)

        # Color tags for each status category
        self.tree.tag_configure("online",       foreground=ACCENT_GREEN)
        self.tree.tag_configure("redirected",   foreground=ACCENT_CYAN)
        self.tree.tag_configure("client_error", foreground=ACCENT_YELLOW)
        self.tree.tag_configure("server_error", foreground=ACCENT_RED)
        self.tree.tag_configure("error",        foreground=ACCENT_PURPLE)
        self.tree.tag_configure("unknown",      foreground=ACCENT_GRAY)
        # Alternating row backgrounds
        self.tree.tag_configure("odd_row",      background="#0d1117")
        self.tree.tag_configure("even_row",     background="#111720")

        # Scrollbars
        vsb = ttk.Scrollbar(container, orient="vertical",
                            command=self.tree.yview,
                            style="Dark.Vertical.TScrollbar")
        hsb = ttk.Scrollbar(container, orient="horizontal",
                            command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        self._row_index = 0  # Incremented for each result added

    #  LOG PANEL

    def _build_log_panel(self):
        """Small collapsible log area showing live status messages."""
        frame = tk.Frame(self, bg=BG_DARK, padx=16)
        frame.pack(fill="x")

        # Toggle header
        toggle_frame = tk.Frame(frame, bg=BG_DARK)
        toggle_frame.pack(fill="x", pady=(0, 4))

        self._log_visible = tk.BooleanVar(value=True)
        tk.Button(
            toggle_frame, text="▼  Live Log",
            bg=BG_DARK, fg=TEXT_SECONDARY,
            activebackground=BG_DARK, activeforeground=TEXT_PRIMARY,
            relief="flat", font=FONT_LABEL,
            cursor="hand2", command=self._toggle_log
        ).pack(side="left")

        # Log text widget
        self.log_frame = tk.Frame(frame, bg=BG_DARK)
        self.log_frame.pack(fill="x")

        self.log_text = tk.Text(
            self.log_frame, height=4,
            bg=BG_INPUT, fg=TEXT_SECONDARY,
            insertbackground=ACCENT_BLUE,
            relief="flat", font=FONT_MONO,
            state="disabled", wrap="word",
            padx=10, pady=6,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1,
        )
        self.log_text.pack(fill="x")

        # Color tags for log messages
        self.log_text.tag_configure("info",    foreground=ACCENT_BLUE)
        self.log_text.tag_configure("success", foreground=ACCENT_GREEN)
        self.log_text.tag_configure("warning", foreground=ACCENT_YELLOW)
        self.log_text.tag_configure("error",   foreground=ACCENT_RED)
        self.log_text.tag_configure("muted",   foreground=TEXT_MUTED)

    def _toggle_log(self):
        """Show or hide the log panel."""
        if self._log_visible.get():
            self.log_frame.pack_forget()
            self._log_visible.set(False)
        else:
            self.log_frame.pack(fill="x")
            self._log_visible.set(True)

    #  SUMMARY BAR

    def _build_summary_bar(self):
        """Bottom row of StatCards showing count totals."""
        bar = tk.Frame(self, bg=BG_DARK, padx=16, pady=10)
        bar.pack(fill="x", side="bottom")

        tk.Frame(self, bg=BORDER_COLOR, height=1).pack(fill="x", side="bottom")

        cards_config = [
            ("total",       "Total",          TEXT_PRIMARY),
            ("online",      "Online",         ACCENT_GREEN),
            ("redirected",  "Redirected",     ACCENT_CYAN),
            ("client_err",  "Client Errors",  ACCENT_YELLOW),
            ("server_err",  "Server Errors",  ACCENT_RED),
            ("conn_err",    "Unreachable",    ACCENT_PURPLE),
            ("avg_time",    "Avg ms",         ACCENT_BLUE),
        ]

        self._stat_cards = {}
        for key, label, color in cards_config:
            card = StatCard(bar, label=label, color=color)
            card.pack(side="left", padx=(0, 8), fill="y")
            self._stat_cards[key] = card

    #  LOG HELPER

    def _log(self, message: str, color: str = None):
        """
        Append a timestamped line to the log widget.
        `color` should be one of the ACCENT_* hex strings.
        """
        tag_map = {
            ACCENT_BLUE:   "info",
            ACCENT_GREEN:  "success",
            ACCENT_YELLOW: "warning",
            ACCENT_RED:    "error",
            TEXT_MUTED:    "muted",
        }
        tag = tag_map.get(color, "info")
        ts  = datetime.now().strftime("%H:%M:%S")

        self.log_text.config(state="normal")
        self.log_text.insert("end", f"[{ts}]  {message}\n", tag)
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    #  URL PARSING

    def _get_urls(self) -> list:
        """
        Parse URLs from the text input.
        Skips blank lines and comment lines (starting with #).
        Supports comma-separated URLs on one line.
        Deduplicates while preserving order.
        """
        raw  = self.url_input.get_real_text()
        urls = []
        for line in raw.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split(",") if p.strip()]
            urls.extend(parts)

        # Deduplicate preserving order
        seen   = set()
        unique = []
        for u in urls:
            if u not in seen:
                seen.add(u)
                unique.append(u)
        return unique

    def _import_from_file(self):
        """Open a file dialog to load URLs from a .txt file."""
        path = filedialog.askopenfilename(
            title="Select URL file",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not path:
            return

        urls = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    parts = [p.strip() for p in line.split(",") if p.strip()]
                    urls.extend(parts)

        if urls:
            # Replace textarea content
            self.url_input.config(state="normal")
            self.url_input._showing_placeholder = False
            self.url_input.config(fg=TEXT_PRIMARY)
            self.url_input.delete("1.0", "end")
            self.url_input.insert("1.0", "\n".join(urls))
            self._log(f"📂  Loaded {len(urls)} URL(s) from: {os.path.basename(path)}", ACCENT_BLUE)
        else:
            messagebox.showwarning("Empty File", "No valid URLs found in the selected file.")

    #  ADD RESULT ROW TO TABLE

    def _add_row(self, result: dict):
        """
        Insert one result into the Treeview with appropriate color tags.
        Called from the main thread via `after()`.
        """
        self._row_index += 1
        row_tag = "odd_row" if self._row_index % 2 == 0 else "even_row"

        time_str = f"{result['response_ms']} ms" if result["response_ms"] else "—"

        self.tree.insert(
            "", "end",
            values=(
                self._row_index,
                result["emoji"],
                result["url"],
                result["status_code"],
                time_str,
                result["status_label"],
                result["checked_at"],
            ),
            tags=(result["category"], row_tag)
        )
        self.tree.yview_moveto(1)  # Auto-scroll to bottom

        # Update row count label
        self.row_count_var.set(f"{self._row_index} row{'s' if self._row_index != 1 else ''}")

    #  SUMMARY UPDATE

    def _update_summary(self):
        """Recompute and refresh all StatCards from self.results."""
        r    = self.results
        vals = [x["response_ms"] for x in r if x["response_ms"] is not None]
        avg  = round(sum(vals) / len(vals), 1) if vals else "—"

        self._stat_cards["total"].set(len(r))
        self._stat_cards["online"].set(sum(1 for x in r if x["category"] == "online"))
        self._stat_cards["redirected"].set(sum(1 for x in r if x["category"] == "redirected"))
        self._stat_cards["client_err"].set(sum(1 for x in r if x["category"] == "client_error"))
        self._stat_cards["server_err"].set(sum(1 for x in r if x["category"] == "server_error"))
        self._stat_cards["conn_err"].set(sum(1 for x in r if x["category"] == "error"))
        self._stat_cards["avg_time"].set(avg)

    #  CHECKING ENGINE

    def _start_check(self):
        """Parse URLs, validate, and launch the background check thread."""
        if self.is_checking:
            return

        urls = self._get_urls()
        if not urls:
            messagebox.showwarning("No URLs", "Please enter at least one URL to check.")
            return

        # Read settings
        try:
            timeout = int(self.timeout_var.get())
            threads = min(int(self.threads_var.get()), 20)
            retries = int(self.retries_var.get())
        except ValueError:
            messagebox.showerror("Invalid Settings", "Timeout, Threads, and Retries must be integers.")
            return

        # Reset progress
        self.progress_var.set(0)
        self.progress_bar.config(maximum=len(urls))

        self.is_checking = True
        self._stop_event.clear()
        self.btn_check.config(state="disabled")
        self.btn_stop.config(state="normal")

        self._log(f"🚀  Starting check for {len(urls)} URL(s) — {threads} threads, {timeout}s timeout", ACCENT_BLUE)

        # Run in background thread so the GUI stays responsive
        t = threading.Thread(
            target=self._check_worker,
            args=(urls, timeout, threads, retries),
            daemon=True
        )
        t.start()

    def _check_worker(self, urls: list, timeout: int,
                      threads: int, retries: int):
        """
        Background thread: checks all URLs using ThreadPoolExecutor,
        posts each result back to the main thread via `after()`.
        """
        completed = 0
        batch_results = []

        with ThreadPoolExecutor(max_workers=threads) as executor:
            future_to_url = {
                executor.submit(check_url, url, timeout, retries): url
                for url in urls
            }

            for future in as_completed(future_to_url):
                if self._stop_event.is_set():
                    executor.shutdown(wait=False, cancel_futures=True)
                    break

                result = future.result()
                batch_results.append(result)
                completed += 1

                # Schedule GUI update on the main thread (thread-safe)
                self.after(0, self._on_result, result, completed, len(urls))

        # Schedule completion handler
        self.after(0, self._on_complete, batch_results)

    def _on_result(self, result: dict, completed: int, total: int):
        """
        Called on the main thread for each completed URL.
        Updates the table, log, and progress bar.
        """
        self.results.append(result)
        self._add_row(result)
        self._update_summary()

        # Update progress bar and status label
        self.progress_var.set(completed)
        self.status_label_var.set(
            f"Checking...  {completed} / {total}  —  {result['url']}"
        )

        # Log color based on category
        color_map = {
            "online":       ACCENT_GREEN,
            "redirected":   ACCENT_CYAN,
            "client_error": ACCENT_YELLOW,
            "server_error": ACCENT_RED,
            "error":        ACCENT_PURPLE,
        }
        color = color_map.get(result["category"], TEXT_MUTED)
        t = f"{result['response_ms']} ms" if result["response_ms"] else "N/A"
        self._log(
            f"{result['emoji']}  [{result['status_code']}]  {result['url']}  —  {t}",
            color
        )

    def _on_complete(self, batch_results: list):
        """Called on the main thread when the full batch finishes."""
        self.is_checking = False
        self.btn_check.config(state="normal")
        self.btn_stop.config(state="disabled")
        self.progress_var.set(self.progress_bar["maximum"])

        if self._stop_event.is_set():
            self.status_label_var.set("⏹  Stopped by user.")
            self._log("⏹  Check stopped by user.", ACCENT_YELLOW)
        else:
            total   = len(batch_results)
            online  = sum(1 for r in batch_results if r["category"] == "online")
            self.status_label_var.set(
                f"✅  Done — {total} URLs checked  |  {online} online"
            )
            self._log(
                f"✅  Completed — {total} URLs  |  {online} online",
                ACCENT_GREEN
            )

        # Schedule next cycle if continuous mode is on
        if self.continuous_var.get() and not self._stop_event.is_set():
            try:
                interval_ms = int(float(self.interval_var.get()) * 1000)
            except ValueError:
                interval_ms = 30_000

            self._log(
                f"🔁  Next check in {interval_ms // 1000}s…", TEXT_MUTED
            )
            self._continuous_job = self.after(
                interval_ms, self._start_continuous_cycle
            )

    def _start_continuous_cycle(self):
        """Re-run check for the same URLs (continuous mode)."""
        self._continuous_job = None
        # Clear table for a fresh cycle
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.results = []
        self._row_index = 0
        self._start_check()

    def _stop_check(self):
        """Signal the worker thread to stop after the current batch."""
        self._stop_event.set()
        if self._continuous_job:
            self.after_cancel(self._continuous_job)
            self._continuous_job = None
        self.btn_stop.config(state="disabled")
        self._log("⏹  Stop requested — finishing current requests…", ACCENT_YELLOW)

    #  CLEAR

    def _clear_all(self):
        """Clear the results table, log, and summary cards."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.results    = []
        self._row_index = 0
        self.row_count_var.set("0 rows")
        self.progress_var.set(0)
        self.status_label_var.set("Ready")

        for card in self._stat_cards.values():
            card.set(0)
        self._stat_cards["avg_time"].set("—")

        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.config(state="disabled")
        self._log("🗑  Results cleared.", TEXT_MUTED)

    #  EXPORT

    def _export_csv(self):
        """Open save dialog and write CSV report."""
        if not self.results:
            messagebox.showinfo("Nothing to Export", "Run a check first.")
            return
        default = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=default,
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if path:
            save_as_csv(self.results, path)
            self._log(f"📄  CSV exported → {path}", ACCENT_GREEN)
            messagebox.showinfo("Exported", f"CSV saved to:\n{path}")

    def _export_txt(self):
        """Open save dialog and write TXT report."""
        if not self.results:
            messagebox.showinfo("Nothing to Export", "Run a check first.")
            return
        default = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=default,
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if path:
            save_as_txt(self.results, path)
            self._log(f"📝  TXT exported → {path}", ACCENT_GREEN)
            messagebox.showinfo("Exported", f"TXT saved to:\n{path}")


#  ENTRY POINT

if __name__ == "__main__":
    app = URLCheckerApp()
    app.mainloop()