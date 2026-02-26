"""
Desktop application for viewing and printing route data from Excel sheets.
Filters by service day, service tech, and cycle frequency.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import os
from pathlib import Path
from datetime import datetime
import webbrowser
import tempfile
import urllib.request
import re
import json
import subprocess
import threading
import sys
import ctypes as ct

# Cursor/VS Code dark theme colors
THEME = {
    "bg": "#1e1e1e",
    "bg_panel": "#252526",
    "bg_input": "#3c3c3c",
    "fg": "#d4d4d4",
    "fg_muted": "#858585",
    "accent": "#007acc",
    "accent_hover": "#1a8ad4",
    "border": "#3c3c3c",
    "border_visible": "#505050",   # stronger border for inputs/panels
    "panel_border": "#2d5a7b",    # subtle blue tint for section frames
    "select_bg": "#094771",
    "menu_bg": "#252526",
    "menu_fg": "#cccccc",
    "menu_active_bg": "#094771",
    "menu_active_fg": "#ffffff",
    "status_bg": "#007acc",
    "status_fg": "#ffffff",
}


def _dark_button(parent, text, command, primary=False, **kwargs):
    """Create a dark-themed tk.Button. Set primary=True for accent blue (main actions)."""
    t = THEME
    bg = t["accent"] if primary else t["bg_input"]
    abg = t["accent_hover"] if primary else t["accent"]
    return tk.Button(
        parent,
        text=text,
        command=command,
        bg=bg,
        fg=t["status_fg"] if primary else t["fg"],
        activebackground=abg,
        activeforeground=t["status_fg"] if primary else t["fg"],
        highlightthickness=1,
        highlightbackground=t["border_visible"],
        highlightcolor=t["accent"],
        relief=tk.FLAT,
        font=("Segoe UI", 9),
        cursor="hand2",
        padx=12,
        pady=6,
        **kwargs,
    )


def _dark_entry(parent, textvariable=None, width=None, **kwargs):
    """Create a dark-themed tk.Entry with a visible border."""
    t = THEME
    opts = dict(
        bg=t["bg_input"],
        fg=t["fg"],
        insertbackground=t["fg"],
        highlightthickness=1,
        highlightbackground=t["border_visible"],
        highlightcolor=t["accent"],
        relief=tk.FLAT,
        font=("Segoe UI", 9),
    )
    if width is not None:
        opts["width"] = width
    if textvariable is not None:
        opts["textvariable"] = textvariable
    opts.update(kwargs)
    return tk.Entry(parent, **opts)


class DarkCombobox(tk.Frame):
    """A dark-themed dropdown that behaves like a readonly combobox."""
    
    def __init__(self, parent, textvariable=None, width=20, **kwargs):
        t = THEME
        super().__init__(parent, **kwargs)
        self._var = textvariable if textvariable is not None else tk.StringVar()
        self._choices = []  # avoid _options: shadows tkinter Widget._options used by grid()
        self._popup = None
        
        self.entry = tk.Entry(
            self,
            textvariable=self._var,
            state="disabled",
            bg=t["bg_input"],
            fg=t["fg"],
            disabledbackground=t["bg_input"],
            disabledforeground=t["fg"],
            font=("Segoe UI", 9),
            highlightthickness=1,
            highlightbackground=t["border_visible"],
            relief=tk.FLAT,
            width=width,
        )
        self.entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 0))
        
        self._arrow_btn = tk.Button(
            self,
            text="\u25BC",
            command=self._open_dropdown,
            bg=t["bg_input"],
            fg=t["fg"],
            activebackground=t["accent"],
            activeforeground=t["fg"],
            highlightthickness=1,
            highlightbackground=t["border_visible"],
            relief=tk.FLAT,
            font=("Segoe UI", 8),
            cursor="hand2",
            width=2,
        )
        self._arrow_btn.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.entry.bind("<Button-1>", lambda e: self._open_dropdown())
    
    def set_options(self, options):
        self._choices = list(options) if options else []
    
    def get(self):
        return self._var.get()
    
    def set(self, value):
        self._var.set(value)
    
    def _open_dropdown(self):
        if not self._choices:
            return
        t = THEME
        if self._popup and self._popup.winfo_exists():
            self._popup.destroy()
        
        self._popup = tk.Toplevel(self)
        self._popup.overrideredirect(True)
        self._popup.configure(bg=t["border"])
        try:
            self._popup.attributes("-topmost", True)
        except tk.TclError:
            pass
        
        # Close dropdown when app loses focus or when user clicks outside the dropdown
        root = self.winfo_toplevel()
        self._focus_out_after_id = None
        def _on_root_focus_out(evt=None):
            if self._focus_out_after_id:
                try:
                    root.after_cancel(self._focus_out_after_id)
                except Exception:
                    pass
            self._focus_out_after_id = root.after(150, self._close_popup_if_app_lost_focus)
        self._focus_out_handler = _on_root_focus_out
        root.bind("<FocusOut>", _on_root_focus_out, add="+")
        
        def _on_click_anywhere(evt):
            if not self._popup or not self._popup.winfo_exists():
                return
            try:
                w = evt.widget
                top = w.winfo_toplevel()
                if top == self._popup:
                    return  # click was inside the dropdown
                _unbind_focus_out()
            except Exception:
                pass
            if self._popup and self._popup.winfo_exists():
                self._popup.destroy()
            self._popup = None
        self._click_out_handler = _on_click_anywhere
        root.bind("<Button-1>", _on_click_anywhere, add="+")
        
        def _unbind_focus_out():
            if getattr(self, "_focus_out_after_id", None):
                try:
                    root.after_cancel(self._focus_out_after_id)
                except Exception:
                    pass
                self._focus_out_after_id = None
            try:
                root.unbind("<FocusOut>", self._focus_out_handler)
            except Exception:
                pass
            try:
                root.unbind("<Button-1>", self._click_out_handler)
            except Exception:
                pass
        
        lb_frame = tk.Frame(self._popup, bg=t["bg_input"], highlightthickness=1, highlightbackground=t["border"])
        lb_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        scrollbar = tk.Scrollbar(lb_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(
            lb_frame,
            bg=t["bg_input"],
            fg=t["fg"],
            selectbackground=t["select_bg"],
            selectforeground=t["fg"],
            font=("Segoe UI", 9),
            highlightthickness=0,
            relief=tk.FLAT,
            yscrollcommand=scrollbar.set,
        )
        for o in self._choices:
            listbox.insert(tk.END, o)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        
        def on_select(evt=None):
            sel = listbox.curselection()
            if sel:
                self._var.set(listbox.get(sel[0]))
            _unbind_focus_out()
            if self._popup and self._popup.winfo_exists():
                self._popup.destroy()
            self._popup = None
        
        def on_escape(evt=None):
            _unbind_focus_out()
            if self._popup and self._popup.winfo_exists():
                self._popup.destroy()
            self._popup = None
        
        self._popup.bind("<Escape>", on_escape)
        listbox.bind("<<ListboxSelect>>", lambda e: self._popup.after(50, on_select))
        listbox.bind("<Double-Button-1>", on_select)
        
        # Position below the combobox
        self.update_idletasks()
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        w = max(self.winfo_width(), 120)
        h = min(200, max(80, len(self._choices) * 22))
        self._popup.geometry(f"{w}x{h}+{x}+{y}")
        
        # Select current value in listbox
        try:
            idx = self._choices.index(self._var.get())
            listbox.selection_set(idx)
            listbox.see(idx)
        except ValueError:
            pass
        
        self._popup.focus_set()
        listbox.focus_set()
    
    def _maybe_close_popup(self):
        if self._popup and self._popup.winfo_exists():
            self._popup.destroy()
            self._popup = None
    
    def _close_popup_if_app_lost_focus(self):
        """On Windows: close the dropdown only if another app's window has focus (not our main window and not our dropdown)."""
        if not self._popup or not self._popup.winfo_exists():
            return
        if sys.platform != "win32":
            return
        try:
            root = self.winfo_toplevel()
            tid = root.winfo_id()
            our_hwnd = ct.windll.user32.GetParent(tid) or tid
            popup_tid = self._popup.winfo_id()
            popup_hwnd = ct.windll.user32.GetParent(popup_tid) or popup_tid
            fg_hwnd = ct.windll.user32.GetForegroundWindow()
            # Keep dropdown open if focus is on our main window or on the dropdown popup itself
            if fg_hwnd == our_hwnd or fg_hwnd == popup_hwnd:
                return
            if getattr(self, "_focus_out_after_id", None):
                try:
                    root.after_cancel(self._focus_out_after_id)
                except Exception:
                    pass
                self._focus_out_after_id = None
            for bind_id, evt in [(getattr(self, "_focus_out_handler", None), "<FocusOut>"),
                                 (getattr(self, "_click_out_handler", None), "<Button-1>")]:
                if bind_id is not None:
                    try:
                        root.unbind(evt, bind_id)
                    except Exception:
                        pass
            if self._popup and self._popup.winfo_exists():
                self._popup.destroy()
            self._popup = None
        except Exception:
            pass
    
    @property
    def config(self):
        return self.entry.config  # for compatibility if anything uses combobox.config


class RouteViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Route Viewer - Demand Sheet Generator")
        self.root.geometry("800x700")
        
        self.data = None
        self.filtered_data = None
        self.favorites = {}  # Dictionary: alias -> path/URL
        self.favorites_file = Path.home() / ".demand_sheet_favorites.json"
        self._app_dir = Path(__file__).resolve().parent
        
        self._setup_theme()
        self.setup_ui()
    
    def _setup_theme(self):
        """Apply Cursor/VS Code–style dark theme."""
        root = self.root
        t = THEME
        root.configure(bg=t["bg"])
        
        # Menu bar (tk.Menu)
        root.option_add("*Menu.background", t["menu_bg"])
        root.option_add("*Menu.foreground", t["menu_fg"])
        root.option_add("*Menu.activeBackground", t["menu_active_bg"])
        root.option_add("*Menu.activeForeground", t["menu_active_fg"])
        root.option_add("*Menu.selectColor", t["accent"])
        
        # Use 'clam' so ttk respects our colors on Windows
        style = ttk.Style()
        style.theme_use("clam")
        
        # Frames (visible border on panels for contrast)
        style.configure("TFrame", background=t["bg"])
        style.configure("TLabelframe", background=t["bg"], foreground=t["fg"], bordercolor=t["panel_border"])
        style.configure("TLabelframe.Label", background=t["bg"], foreground=t["accent"], font=("Segoe UI", 9, "bold"))
        
        # Labels
        style.configure("TLabel", background=t["bg"], foreground=t["fg"], font=("Segoe UI", 9))
        style.configure("Muted.TLabel", background=t["bg"], foreground=t["fg_muted"], font=("Segoe UI", 9))
        
        # Buttons
        style.configure("TButton", background=t["bg_input"], foreground=t["fg"], font=("Segoe UI", 9), padding=(12, 6))
        style.map("TButton", background=[("active", t["accent"]), ("pressed", t["accent"])], foreground=[("active", t["fg"])])
        
        # Entry
        style.configure("TEntry", fieldbackground=t["bg_input"], foreground=t["fg"], insertcolor=t["fg"], padding=6)
        
        # Combobox
        style.configure("TCombobox", fieldbackground=t["bg_input"], foreground=t["fg"], background=t["bg_input"], arrowcolor=t["fg"], padding=6)
        style.map("TCombobox", fieldbackground=[("readonly", t["bg_input"])], foreground=[("readonly", t["fg"])])
        
        # Status bar style (sunken label)
        style.configure("Status.TLabel", background=t["status_bg"], foreground=t["status_fg"], font=("Segoe UI", 9), padding=(8, 4))
        
        # Dark title bar on Windows 10/11 (apply after window is shown)
        if sys.platform == "win32":
            root.after(100, self._apply_dark_title_bar)
    
    def _apply_dark_title_bar(self):
        """Use Windows DWM to draw the title bar in dark mode."""
        try:
            root = self.root
            root.update()  # ensure window is realized and has a valid hwnd
            tid = root.winfo_id()
            # Try both: sometimes Tk gives client area (GetParent = frame), sometimes the frame directly
            for hwnd in (ct.windll.user32.GetParent(tid) or tid, tid):
                if not hwnd:
                    continue
                DWMWA_USE_IMMERSIVE_DARK_MODE = 20
                for value in (ct.c_int(2), ct.c_int(1)):  # 2 = Win11, 1 = some Win10
                    try:
                        ret = ct.windll.dwmapi.DwmSetWindowAttribute(
                            ct.c_void_p(hwnd), DWMWA_USE_IMMERSIVE_DARK_MODE, ct.byref(value), ct.sizeof(value)
                        )
                        if ret == 0:
                            break
                    except Exception:
                        pass
                else:
                    continue
                break
            # Force redraw (needed on many Windows 10 systems)
            root.after(50, self._force_dark_title_bar_redraw)
        except Exception:
            pass
    
    def _force_dark_title_bar_redraw(self):
        """Iconify/deiconify to force Windows to redraw the title bar in dark mode."""
        try:
            root = self.root
            root.iconify()
            root.after(10, root.deiconify)
        except Exception:
            pass
        
    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        t = THEME
        # No menu bar — removes the white bar; "Check for updates" is a button at the bottom
        self.root.config(menu="")
        
        # File & Favorites — one label column (left), one control column (right) for clear UX
        file_section_frame = ttk.LabelFrame(main_frame, text="File & Favorites", padding="10")
        file_section_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        file_section_frame.columnconfigure(0, minsize=200)   # fixed width so all labels align
        file_section_frame.columnconfigure(1, weight=1)
        
        # Row 0: File / URL with label directly to the left
        ttk.Label(file_section_frame, text="Excel file or Google Sheets URL:").grid(row=0, column=0, sticky=tk.W, pady=(0, 8))
        self.file_path = tk.StringVar()
        row0_frame = ttk.Frame(file_section_frame)
        row0_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 8))
        row0_frame.columnconfigure(0, weight=1)
        file_entry = _dark_entry(row0_frame, textvariable=self.file_path)
        file_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        file_entry.bind('<Return>', lambda e: self.load_from_path())
        _dark_button(row0_frame, text="Browse", command=self.browse_file).grid(row=0, column=1)
        _dark_button(row0_frame, text="Load", command=self.load_from_path, primary=True).grid(row=0, column=2, padx=(5, 0))

        # Row 1: Favorites dropdown with label
        ttk.Label(file_section_frame, text="Saved favorites:").grid(row=1, column=0, sticky=tk.W, pady=(0, 8))
        self.favorites_var = tk.StringVar()
        self.favorite_alias_var = tk.StringVar()
        row1_frame = ttk.Frame(file_section_frame)
        row1_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(0, 8))
        row1_frame.columnconfigure(0, weight=1)
        self.favorites_combo = DarkCombobox(row1_frame, textvariable=self.favorites_var, width=50)
        self.favorites_combo.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        _dark_button(row1_frame, text="Load Favorite", command=self.load_selected_favorite).grid(row=0, column=1)

        # Row 2: Alias for saving, with label
        ttk.Label(file_section_frame, text="Save current as (alias):").grid(row=2, column=0, sticky=tk.W, pady=(0, 8))
        row2_frame = ttk.Frame(file_section_frame)
        row2_frame.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=(0, 8))
        row2_frame.columnconfigure(0, weight=1)
        _dark_entry(row2_frame, textvariable=self.favorite_alias_var, width=35).grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        _dark_button(row2_frame, text="Save as Favorite", command=self.save_current_to_favorites).grid(row=0, column=1)

        # Row 3: Remove favorite (label for clarity)
        ttk.Label(file_section_frame, text="Remove a favorite:").grid(row=3, column=0, sticky=tk.W, pady=(0, 0))
        _dark_button(file_section_frame, text="Remove Favorite", command=self.remove_selected_favorite).grid(row=3, column=1, sticky=tk.W, pady=(0, 0))
        
        # After file/favorites UI is built, load any saved favorites
        self.load_favorites()

        # Filters — same label column width for alignment with File section
        filter_frame = ttk.LabelFrame(main_frame, text="Filters", padding="10")
        filter_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        filter_frame.columnconfigure(0, minsize=200)
        filter_frame.columnconfigure(1, weight=1)
        
        ttk.Label(filter_frame, text="Service day:").grid(row=0, column=0, sticky=tk.W, pady=(0, 8))
        self.service_day_var = tk.StringVar(value="All")
        self.service_day_combo = DarkCombobox(filter_frame, textvariable=self.service_day_var, width=30)
        self.service_day_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 8), padx=(0, 5))
        self.service_day_combo.set_options(["All"])
        
        ttk.Label(filter_frame, text="Service tech:").grid(row=1, column=0, sticky=tk.W, pady=(0, 8))
        self.service_tech_var = tk.StringVar(value="All")
        self.service_tech_combo = DarkCombobox(filter_frame, textvariable=self.service_tech_var, width=30)
        self.service_tech_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(0, 8), padx=(0, 5))
        self.service_tech_combo.set_options(["All"])
        
        ttk.Label(filter_frame, text="Cycle frequency (hold Ctrl to pick several):").grid(row=2, column=0, sticky=tk.W, pady=(0, 8))
        self.cycle_freq_var = tk.StringVar(value="All")
        # Use a multi-select listbox for cycle frequency so multiple options can be chosen
        t = THEME
        self.cycle_freq_listbox = tk.Listbox(
            filter_frame,
            selectmode=tk.MULTIPLE,
            exportselection=False,
            height=9,
            bg=t["bg_input"],
            fg=t["fg"],
            selectbackground=t["select_bg"],
            selectforeground=t["fg"],
            font=("Segoe UI", 9),
            highlightthickness=1,
            highlightbackground=t["border_visible"],
            highlightcolor=t["accent"],
            borderwidth=0,
            relief=tk.FLAT,
        )
        self.cycle_freq_listbox.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=(0, 0), padx=(0, 5))
        self.cycle_freq_listbox.bind('<<ListboxSelect>>', lambda event: self.apply_filters())
        
        # Bind filter changes
        self.service_day_var.trace_add("write", lambda *args: self.apply_filters())
        self.service_tech_var.trace_add("write", lambda *args: self.apply_filters())
        
        # Main actions (clear grouping)
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=(4, 12))
        ttk.Label(button_frame, text="Actions:").pack(side=tk.LEFT, padx=(0, 10))
        _dark_button(button_frame, text="Preview Route", command=self.preview_route, primary=True).pack(side=tk.LEFT, padx=5)
        _dark_button(button_frame, text="Print/Export", command=self.print_route, primary=True).pack(side=tk.LEFT, padx=5)
        _dark_button(button_frame, text="Clear Filters", command=self.clear_filters).pack(side=tk.LEFT, padx=5)
        
        # Sheet status (what’s loaded and detected)
        confirmation_frame = ttk.LabelFrame(main_frame, text="Sheet Status", padding="10")
        confirmation_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        confirmation_frame.columnconfigure(0, minsize=200)
        confirmation_frame.columnconfigure(1, weight=1)
        ttk.Label(confirmation_frame, text="Status:").grid(row=0, column=0, sticky=tk.NW, pady=(0, 4))
        self.confirmation_var = tk.StringVar(value="No data loaded. Choose a file or URL above and click Load.")
        confirmation_label = ttk.Label(confirmation_frame, textvariable=self.confirmation_var, style="Muted.TLabel", wraplength=700)
        confirmation_label.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 4))
        
        # Check for updates button and status bar
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 0))
        bottom_frame.columnconfigure(0, weight=1)
        _dark_button(bottom_frame, text="Check for updates", command=self._start_update_check).pack(side=tk.RIGHT, padx=(5, 0))
        self.status_var = tk.StringVar(value="Ready - Please select an Excel file")
        status_label = ttk.Label(bottom_frame, textvariable=self.status_var, style="Status.TLabel")
        status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def _start_update_check(self):
        """Start update check in a background thread so the UI stays responsive."""
        self.status_var.set("Checking for updates...")
        def run():
            result = self._do_update_check()
            self.root.after(0, lambda: self._on_update_check_done(result))
        threading.Thread(target=run, daemon=True).start()
    
    def _do_update_check(self):
        """
        Check for updates via git. Runs in background thread.
        Returns (ok, message, behind_count) where:
          ok: False = error/not applicable, True = check succeeded
          message: user-facing text
          behind_count: number of commits behind remote (0 if not applicable or error)
        """
        app_dir = self._app_dir
        git_dir = app_dir / ".git"
        if not git_dir.is_dir():
            return (False, "Updates not available. This copy was not installed from a git repository.", 0)
        
        def run_git(*args, timeout=15):
            try:
                r = subprocess.run(
                    [ "git" ] + list(args),
                    cwd=app_dir,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
                return (r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip())
            except FileNotFoundError:
                return (-1, "", "Git not found")
            except subprocess.TimeoutExpired:
                return (-1, "", "Timed out")
        
        # Fetch latest from remote (does not modify working tree)
        code, _, err = run_git("fetch", "origin", timeout=30)
        if code != 0:
            return (False, "Could not check for updates. Is Git installed? Is this folder a git clone? Try checking your network.", 0)
        
        # Only allow update when working tree is clean (no uncommitted changes)
        code, out, _ = run_git("status", "--porcelain")
        if code != 0:
            return (False, "Could not check repository status.", 0)
        if out:
            return (True, "You have local changes. Updates are only applied when the working tree is clean. Commit or discard changes first.", 0)
        
        # Current branch
        code, branch, _ = run_git("rev-parse", "--abbrev-ref", "HEAD")
        if code != 0 or not branch:
            return (True, "You are up to date.", 0)
        
        # Prefer origin/main, then origin/master
        for remote_ref in [f"origin/{branch}", "origin/main", "origin/master"]:
            code, count_str, _ = run_git("rev-list", "--count", f"HEAD..{remote_ref}")
            if code == 0 and count_str.isdigit():
                behind = int(count_str)
                if behind > 0:
                    return (True, f"An update is available ({behind} new commit(s)).\n\nDo you want to update now?", behind)
                return (True, "You are up to date.", 0)
        
        return (True, "You are up to date.", 0)
    
    def _on_update_check_done(self, result):
        ok, message, behind_count = result
        self.status_var.set("Ready - Please select an Excel file")
        if not ok:
            messagebox.showinfo("Check for updates", message)
            return
        if behind_count > 0:
            if messagebox.askyesno("Update available", message, default=tk.YES):
                self._start_update_pull()
            return
        messagebox.showinfo("Check for updates", message)
    
    def _start_update_pull(self):
        """Run git pull in a background thread."""
        self.status_var.set("Updating...")
        def run():
            result = self._do_update_pull()
            self.root.after(0, lambda: self._on_update_pull_done(result))
        threading.Thread(target=run, daemon=True).start()
    
    def _do_update_pull(self):
        """Pull latest changes. Runs in background thread. Returns (success, message)."""
        app_dir = self._app_dir
        try:
            r = subprocess.run(
                ["git", "pull", "origin"],
                cwd=app_dir,
                capture_output=True,
                text=True,
                timeout=60,
            )
            if r.returncode == 0:
                return (True, "Update complete. Please restart the application to use the new version.")
            return (False, (r.stderr or r.stdout or "Update failed.").strip() or "Update failed.")
        except FileNotFoundError:
            return (False, "Git not found.")
        except subprocess.TimeoutExpired:
            return (False, "Update timed out.")
    
    def _on_update_pull_done(self, result):
        success, message = result
        self.status_var.set("Ready - Please select an Excel file")
        messagebox.showinfo("Update" if success else "Update failed", message)
        
    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if filename:
            self.file_path.set(filename)
            self.load_from_path()

    # ----- Favorites handling -----

    def get_default_favorites(self):
        """Return default favorites for new users"""
        return {
            "Main Sheet": ""  # User needs to set the URL/path
        }
    
    def load_favorites(self):
        """Load favorites from disk into memory and refresh the UI"""
        try:
            if self.favorites_file.exists():
                with open(self.favorites_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # Handle migration from old list format to new dict format
                if isinstance(data, list):
                    # Convert old format: list of paths/URLs -> dict with paths as both key and value
                    self.favorites = {path: path for path in data}
                elif isinstance(data, dict):
                    self.favorites = {str(k): str(v) for k, v in data.items()}
                else:
                    self.favorites = {}
            else:
                # File doesn't exist - initialize with defaults for new users
                self.favorites = self.get_default_favorites()
                self.save_favorites()
        except Exception:
            # If anything goes wrong, initialize with defaults
            self.favorites = self.get_default_favorites()
        
        # If favorites dict is empty, initialize with defaults
        if not self.favorites:
            self.favorites = self.get_default_favorites()
            self.save_favorites()
        
        self.refresh_favorites_ui()

    def save_favorites(self):
        """Persist favorites dictionary to disk"""
        try:
            with open(self.favorites_file, "w", encoding="utf-8") as f:
                json.dump(self.favorites, f, indent=2)
        except Exception as e:
            messagebox.showwarning("Favorites", f"Failed to save favorites:\n{e}")

    def refresh_favorites_ui(self):
        """Update the favorites dropdown with current aliases"""
        if hasattr(self, "favorites_combo"):
            aliases = sorted(self.favorites.keys())
            self.favorites_combo.set_options(aliases)
            # Keep selection if still valid
            current = self.favorites_var.get()
            if current in aliases:
                self.favorites_combo.set(current)
            elif aliases:
                self.favorites_combo.set(aliases[0])
            else:
                self.favorites_combo.set("")

    def save_current_to_favorites(self):
        """Save current path/URL as a favorite with an alias"""
        path_value = self.file_path.get().strip()
        if not path_value:
            messagebox.showwarning("Favorites", "Nothing to save. Enter a file path or URL first.")
            return
        
        alias = self.favorite_alias_var.get().strip()
        if not alias:
            messagebox.showwarning("Favorites", "Please enter an alias/name for this favorite.")
            return
        
        if alias in self.favorites:
            # Ask if user wants to overwrite
            if not messagebox.askyesno("Favorites", f"Alias '{alias}' already exists. Overwrite?"):
                return
        
        self.favorites[alias] = path_value
        self.save_favorites()
        self.refresh_favorites_ui()
        self.favorites_var.set(alias)
        self.favorite_alias_var.set("")  # Clear alias field
        messagebox.showinfo("Favorites", f"Saved '{alias}' to favorites.")

    def load_selected_favorite(self):
        """Load the currently selected favorite"""
        selected_alias = self.favorites_var.get().strip()
        if not selected_alias and self.favorites:
            selected_alias = sorted(self.favorites.keys())[0]
        if not selected_alias:
            messagebox.showwarning("Favorites", "No favorite selected.")
            return
        if selected_alias not in self.favorites:
            messagebox.showwarning("Favorites", f"Alias '{selected_alias}' not found.")
            return
        path_value = self.favorites[selected_alias]
        self.file_path.set(path_value)
        self.load_from_path()

    def remove_selected_favorite(self):
        """Remove the currently selected favorite"""
        selected_alias = self.favorites_var.get().strip()
        if not selected_alias:
            messagebox.showwarning("Favorites", "No favorite selected.")
            return
        if selected_alias in self.favorites:
            if messagebox.askyesno("Favorites", f"Remove '{selected_alias}' from favorites?"):
                del self.favorites[selected_alias]
                self.save_favorites()
                self.refresh_favorites_ui()
        else:
            messagebox.showwarning("Favorites", f"Alias '{selected_alias}' not found.")
    
    def is_google_sheets_url(self, url):
        """Check if the given string is a Google Sheets URL"""
        if not isinstance(url, str):
            return False
        patterns = [
            r'https?://docs\.google\.com/spreadsheets/.*',
            r'https?://drive\.google\.com/file/d/.*',
        ]
        return any(re.match(pattern, url.strip()) for pattern in patterns)
    
    def convert_google_sheets_url(self, url):
        """Convert Google Sheets URL to CSV export URL"""
        url = url.strip()
        
        # Handle different Google Sheets URL formats
        # Format 1: https://docs.google.com/spreadsheets/d/{ID}/edit#gid={GID}
        # Format 2: https://docs.google.com/spreadsheets/d/{ID}/edit?usp=sharing
        # Format 3: https://drive.google.com/file/d/{ID}/view?usp=sharing
        
        # Extract spreadsheet ID
        match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', url)
        if not match:
            # Try drive.google.com format
            match = re.search(r'/file/d/([a-zA-Z0-9-_]+)', url)
        
        if not match:
            raise ValueError("Could not extract spreadsheet ID from URL")
        
        spreadsheet_id = match.group(1)
        
        # Extract GID if present
        gid_match = re.search(r'[#&]gid=(\d+)', url)
        gid = gid_match.group(1) if gid_match else '0'
        
        # Convert to CSV export URL
        export_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={gid}"
        return export_url
    
    def download_google_sheets(self, url):
        """Download Google Sheets as CSV and return the file path"""
        export_url = self.convert_google_sheets_url(url)
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False)
        temp_path = temp_file.name
        temp_file.close()
        
        try:
            # Download the file
            urllib.request.urlretrieve(export_url, temp_path)
            return temp_path
        except Exception as e:
            os.unlink(temp_path)  # Clean up on error
            raise Exception(f"Failed to download Google Sheets: {str(e)}")
    
    def load_from_path(self):
        """Load data from file path or Google Sheets URL"""
        path = self.file_path.get().strip()
        if not path:
            messagebox.showwarning("No Path", "Please enter a file path or Google Sheets URL")
            return
        
        self.load_data(path)
    
    def load_data(self, filepath):
        try:
            temp_file = None
            
            # Check if it's a Google Sheets URL
            if self.is_google_sheets_url(filepath):
                self.status_var.set("Downloading Google Sheets...")
                self.root.update()  # Update UI to show status
                temp_file = self.download_google_sheets(filepath)
                filepath = temp_file
                display_name = "Google Sheets"
            else:
                display_name = os.path.basename(filepath)
            
            # Try to read Excel/CSV file
            if filepath.endswith('.csv'):
                self.data = pd.read_csv(filepath)
            else:
                self.data = pd.read_excel(filepath)
            
            # Update status
            self.status_var.set(f"Loaded {len(self.data)} records from {display_name}")
            
            # Update filter dropdowns
            self.update_filters()
            
            # Show confirmation
            self.show_confirmation()
            
            # Clean up temp file if it was created
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except:
                    pass  # Ignore cleanup errors
            
        except Exception as e:
            error_msg = str(e)
            messagebox.showerror("Error", f"Failed to load file:\n{error_msg}")
            self.status_var.set("Error loading file")
            # Clean up temp file on error
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except:
                    pass
    
    def update_filters(self):
        if self.data is None:
            return
        
        # Get unique values for each filter column
        # Try common column name variations
        service_day_col = self.find_column(['Service Day', 'service_day', 'ServiceDay', 'Day', 'day'])
        service_tech_col = self.find_column(['Service Tech', 'service_tech', 'ServiceTech', 'Tech', 'tech', 'Technician'])
        cycle_freq_col = self.find_column(['Cycle Frequency', 'cycle_frequency', 'CycleFrequency', 'Frequency', 'frequency', 'Cycle'])
        
        # Update Service Day
        if service_day_col:
            values = ['All'] + sorted(self.data[service_day_col].dropna().unique().tolist())
            self.service_day_combo.set_options(values)
        else:
            self.service_day_combo.set_options(['All'])
        
        # Update Service Tech
        if service_tech_col:
            values = ['All'] + sorted(self.data[service_tech_col].dropna().unique().tolist())
            self.service_tech_combo.set_options(values)
        else:
            self.service_tech_combo.set_options(['All'])
        
        # Update Cycle Frequency (column C fallback if name not found)
        if cycle_freq_col is None and self.data is not None and len(self.data.columns) >= 3:
            cycle_freq_col = self.data.columns[2]

        # Populate cycle frequency multi-select listbox
        self.cycle_freq_listbox.delete(0, tk.END)
        if cycle_freq_col:
            values = sorted(self.data[cycle_freq_col].dropna().unique().tolist())
            for v in values:
                self.cycle_freq_listbox.insert(tk.END, v)
            # Select all by default -> behaves like "All"
            if values:
                self.cycle_freq_listbox.select_set(0, tk.END)
            self.cycle_freq_var.set("All")
        else:
            self.cycle_freq_var.set("All")
    
    def find_column(self, possible_names):
        """Find a column by trying multiple possible names (case-insensitive)"""
        if self.data is None:
            return None
        
        for name in possible_names:
            # Try exact match first
            if name in self.data.columns:
                return name
            # Try case-insensitive match
            for col in self.data.columns:
                if str(col).lower() == name.lower():
                    return col
        return None

    def get_selected_cycle_freqs(self):
        """
        Return a list of selected cycle frequency values from the multi-select
        listbox. If all (or none) are selected, returns None to mean "All".
        Also keeps self.cycle_freq_var in sync for header text.
        """
        if not hasattr(self, "cycle_freq_listbox"):
            return None

        size = self.cycle_freq_listbox.size()
        if size == 0:
            self.cycle_freq_var.set("All")
            return None

        indices = list(self.cycle_freq_listbox.curselection())
        if not indices:
            # Nothing explicitly selected -> treat as "All"
            self.cycle_freq_var.set("All")
            return None

        all_indices = list(range(size))
        if len(indices) == len(all_indices):
            # All selected -> same as "All"
            self.cycle_freq_var.set("All")
            return None

        selected_values = [self.cycle_freq_listbox.get(i) for i in indices]

        if len(selected_values) == 1:
            self.cycle_freq_var.set(str(selected_values[0]))
        else:
            self.cycle_freq_var.set("Multiple")

        return selected_values
    
    def apply_filters(self):
        if self.data is None:
            return
        
        filtered = self.data.copy()
        
        # Apply Service Day filter
        service_day_col = self.find_column(['Service Day', 'service_day', 'ServiceDay', 'Day', 'day'])
        if service_day_col and self.service_day_var.get() != "All":
            filtered = filtered[filtered[service_day_col] == self.service_day_var.get()]
        
        # Apply Service Tech filter
        service_tech_col = self.find_column(['Service Tech', 'service_tech', 'ServiceTech', 'Tech', 'tech', 'Technician'])
        if service_tech_col and self.service_tech_var.get() != "All":
            filtered = filtered[filtered[service_tech_col] == self.service_tech_var.get()]
        
        # Apply Cycle Frequency filter (supports multi-select, column C fallback)
        cycle_freq_col = self.find_column(['Cycle Frequency', 'cycle_frequency', 'CycleFrequency', 'Frequency', 'frequency', 'Cycle'])
        if cycle_freq_col is None and self.data is not None and len(self.data.columns) >= 3:
            cycle_freq_col = self.data.columns[2]

        if cycle_freq_col:
            selected_freqs = self.get_selected_cycle_freqs()
            # If some (but not all) options are selected, filter by them
            if selected_freqs:
                filtered = filtered[filtered[cycle_freq_col].isin(selected_freqs)]
        
        self.filtered_data = filtered
        self.status_var.set(f"Showing {len(filtered)} of {len(self.data)} records")
        self.show_confirmation()
    
    def clear_filters(self):
        self.service_day_var.set("All")
        self.service_tech_var.set("All")
        self.cycle_freq_var.set("All")
        # Reset cycle frequency multi-select to "all selected"
        if hasattr(self, "cycle_freq_listbox"):
            self.cycle_freq_listbox.selection_clear(0, tk.END)
            if self.cycle_freq_listbox.size() > 0:
                self.cycle_freq_listbox.select_set(0, tk.END)
        if self.data is not None:
            self.filtered_data = self.data.copy()
            self.status_var.set(f"Showing all {len(self.data)} records")
            self.show_confirmation()
    
    def show_confirmation(self):
        """Show confirmation that data is loaded and format is correct"""
        if self.data is None or self.data.empty:
            self.confirmation_var.set("No data loaded")
            return
        
        # Find key columns to verify format
        service_day_col = self.find_column(['Service Day', 'service_day', 'ServiceDay', 'Day', 'day'])
        service_tech_col = self.find_column(['Service Tech', 'service_tech', 'ServiceTech', 'Tech', 'tech', 'Technician'])
        cycle_freq_col = self.find_column(['Cycle Frequency', 'cycle_frequency', 'CycleFrequency', 'Frequency', 'frequency', 'Cycle'])
        if cycle_freq_col is None and len(self.data.columns) >= 3:
            cycle_freq_col = self.data.columns[2]
        
        # Build confirmation message
        total_records = len(self.filtered_data) if self.filtered_data is not None else len(self.data)
        total_cols = len(self.data.columns)
        
        msg_parts = [f"✓ Sheet loaded successfully: {total_records} record(s), {total_cols} column(s)"]
        
        # Check for expected columns
        found_cols = []
        if service_day_col:
            found_cols.append("Service Day")
        if service_tech_col:
            found_cols.append("Service Tech")
        if cycle_freq_col:
            found_cols.append("Cycle Frequency")
        
        if found_cols:
            msg_parts.append(f"✓ Found filter columns: {', '.join(found_cols)}")
        else:
            msg_parts.append("⚠ Warning: Could not find expected filter columns")
        
        # Show column names
        col_names = list(self.data.columns)[:10]  # Show first 10 columns
        if len(self.data.columns) > 10:
            col_names.append(f"... and {len(self.data.columns) - 10} more")
        msg_parts.append(f"Columns: {', '.join(str(c) for c in col_names)}")
        
        self.confirmation_var.set("\n".join(msg_parts))
    
    def preview_route(self):
        data = self.filtered_data if self.filtered_data is not None else self.data
        if data is None or data.empty:
            messagebox.showwarning("No Data", "Please load data and apply filters first.")
            return
        
        html_content = self.generate_html(data)
        
        # Save to temp file and open in browser
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(html_content)
            temp_path = f.name
        
        webbrowser.open(f'file://{temp_path}')
        self.status_var.set("Preview opened in browser")
    
    def print_route(self):
        data = self.filtered_data if self.filtered_data is not None else self.data
        if data is None or data.empty:
            messagebox.showwarning("No Data", "Please load data and apply filters first.")
            return
        
        # Ask for save location
        filename = filedialog.asksaveasfilename(
            title="Save Printable Route",
            defaultextension=".html",
            filetypes=[("HTML files", "*.html"), ("All files", "*.*")]
        )
        
        if filename:
            html_content = self.generate_html(data)
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Open in browser for printing
            webbrowser.open(f'file://{os.path.abspath(filename)}')
            self.status_var.set(f"Route saved to {os.path.basename(filename)} - Use browser print function")
            messagebox.showinfo("Success", f"Route saved!\n\nOpen the file in your browser and use File > Print or Ctrl+P to print.")
    
    def generate_html(self, df):
        """Generate printable HTML from filtered data"""
        # Find column names
        service_day_col = self.find_column(['Service Day', 'service_day', 'ServiceDay', 'Day', 'day'])
        service_tech_col = self.find_column(['Service Tech', 'service_tech', 'ServiceTech', 'Tech', 'tech', 'Technician'])
        cycle_freq_col = self.find_column(['Cycle Frequency', 'cycle_frequency', 'CycleFrequency', 'Frequency', 'frequency', 'Cycle'])
        if cycle_freq_col is None and self.data is not None and len(self.data.columns) >= 3:
            cycle_freq_col = self.data.columns[2]

        # Get filter values for header. If "All" is selected but the data only
        # contains a single unique value for that field, show that value
        # instead of "All ...".
        if self.service_day_var.get() != "All":
            service_day = self.service_day_var.get()
        elif service_day_col and not df.empty:
            unique_days = df[service_day_col].dropna().unique()
            service_day = str(unique_days[0]) if len(unique_days) == 1 else "All Days"
        else:
            service_day = "All Days"

        if self.service_tech_var.get() != "All":
            service_tech = self.service_tech_var.get()
        elif service_tech_col and not df.empty:
            unique_techs = df[service_tech_col].dropna().unique()
            service_tech = str(unique_techs[0]) if len(unique_techs) == 1 else "All Techs"
        else:
            service_tech = "All Techs"

        # Cycle frequency header reflects multi-select: list selected items,
        # or "All Frequencies" when all/none are explicitly chosen.
        selected_cycle_freqs = self.get_selected_cycle_freqs()
        if not selected_cycle_freqs:
            if cycle_freq_col and not df.empty:
                unique_freqs = df[cycle_freq_col].dropna().unique()
                cycle_freq = str(unique_freqs[0]) if len(unique_freqs) == 1 else "All Frequencies"
            else:
                cycle_freq = "All Frequencies"
        else:
            if len(selected_cycle_freqs) == 1:
                cycle_freq = str(selected_cycle_freqs[0])
            else:
                cycle_freq = ", ".join(str(v) for v in selected_cycle_freqs)

        # Work on a copy where we drop columns that have no data (only headers)
        working_df = df.copy()
        non_empty_columns = []
        for col in working_df.columns:
            series = working_df[col]
            # Treat NaN and empty/whitespace-only strings as empty
            non_empty_mask = series.notna() & series.astype(str).str.strip().ne("")
            if non_empty_mask.any():
                non_empty_columns.append(col)

        # If all columns are empty for some reason, keep the original columns
        # so the table is still structurally valid.
        if non_empty_columns:
            working_df = working_df[non_empty_columns]

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Route Demand Sheet</title>
    <style>
        @media print {{
            @page {{
                size: letter landscape;
                margin: 0.3in;
            }}
            body {{
                margin: 0;
                padding: 0;
            }}
            .no-print {{
                display: none;
            }}
            /* Scale content to fit page */
            html {{
                width: 100%;
                height: 100%;
            }}
            body {{
                width: 100%;
                transform-origin: top left;
            }}
            /* Monochrome-friendly print styles */
            * {{
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
            .header {{
                margin-bottom: 10px !important;
                padding-bottom: 5px !important;
            }}
            .header h1 {{
                font-size: 18px !important;
            }}
            .header-info {{
                font-size: 11px !important;
            }}
            .filters {{
                background-color: white !important;
                border: 2px solid #000 !important;
                padding: 8px !important;
                margin-bottom: 10px !important;
                font-size: 11px !important;
            }}
            table {{
                width: 100% !important;
                table-layout: auto !important;
                font-size: 9px !important;
                page-break-inside: auto;
            }}
            th {{
                background-color: #e0e0e0 !important;
                color: #000 !important;
                border: 1px solid #000 !important;
                padding: 6px 4px !important;
                font-size: 9px !important;
            }}
            td {{
                padding: 4px !important;
                font-size: 9px !important;
                word-wrap: break-word;
            }}
            tr {{
                page-break-inside: avoid;
                page-break-after: auto;
            }}
            tr:nth-child(even) {{
                background-color: #f5f5f5 !important;
            }}
            .summary {{
                background-color: white !important;
                border: 2px solid #000 !important;
                border-left: 4px solid #000 !important;
                padding: 8px !important;
                margin-top: 10px !important;
                font-size: 11px !important;
            }}
        }}
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            color: #000;
        }}
        .header {{
            border-bottom: 3px solid #000;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
            color: #000;
        }}
        .header-info {{
            margin-top: 10px;
            font-size: 14px;
            color: #000;
        }}
        .filters {{
            background-color: #f5f5f5;
            padding: 10px;
            margin-bottom: 20px;
            border-radius: 5px;
            border: 2px solid #666;
        }}
        .filters strong {{
            margin-right: 10px;
            color: #000;
        }}
        table {{
            width: 100%;
            max-width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            border: 1px solid #000;
            table-layout: auto;
        }}
        th {{
            background-color: #e0e0e0;
            color: #000;
            padding: 10px;
            text-align: left;
            font-weight: bold;
            border: 1px solid #000;
            word-wrap: break-word;
        }}
        td {{
            padding: 8px;
            border: 1px solid #666;
            border-bottom: 1px solid #666;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }}
        tr:nth-child(even) {{
            background-color: #f5f5f5;
        }}
        tr:hover {{
            background-color: #f0f0f0;
        }}
        .summary {{
            margin-top: 20px;
            padding: 10px;
            background-color: white;
            border: 2px solid #000;
            border-left: 4px solid #000;
        }}
        .summary strong {{
            color: #000;
        }}
        .no-print {{
            margin-bottom: 20px;
            padding: 10px;
            background-color: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 5px;
        }}
    </style>
</head>
<body>
    <div class="no-print">
        <strong>Print Instructions:</strong> Use your browser's print function (Ctrl+P or Cmd+P) to print this page.
    </div>
    
    <div class="header">
        <h1>Route Demand Sheet</h1>
        <div class="header-info">
            Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
            Total Records: {len(df)}
        </div>
    </div>
    
    <div class="filters">
        <strong>Filters Applied:</strong>
        Service Day: {service_day} | 
        Service Tech: {service_tech} | 
        Cycle Frequency: {cycle_freq}
    </div>
    
    <table>
        <thead>
            <tr>
"""
        
        # Add table headers (only for columns that have data)
        for col in working_df.columns:
            html += f"                <th>{col}</th>\n"
        
        html += """            </tr>
        </thead>
        <tbody>
"""
        
        # Add table rows for the filtered, non-empty columns
        for idx, row in working_df.iterrows():
            html += "            <tr>\n"
            for val in row:
                display_val = str(val) if pd.notna(val) else ""
                html += f"                <td>{display_val}</td>\n"
            html += "            </tr>\n"
        
        html += """        </tbody>
    </table>
"""

        # Build a chemical pick summary based on numeric columns.
        # We treat any remaining numeric columns (after filtering out the
        # obvious non-chemical fields) as "chemicals" and total them.
        numeric_df = working_df.select_dtypes(include="number")

        # Try to drop obvious non-chemical numeric columns if they exist.
        non_chemical_candidates = [
            service_day_col,
            service_tech_col,
            cycle_freq_col,
        ]
        for col in non_chemical_candidates:
            if col is not None and col in numeric_df.columns:
                numeric_df = numeric_df.drop(columns=[col])

        if not numeric_df.empty and len(numeric_df.columns) > 0:
            totals = numeric_df.sum(numeric_only=True)
            html += '    <div class="summary">\n'
            html += '        <strong>Chemical Pick Summary:</strong><br>\n'
            for chem_name, total in totals.items():
                html += f"        {chem_name}: {total}<br>\n"
            html += "    </div>\n"

        html += "</body>\n</html>"
        
        return html


def main():
    root = tk.Tk()
    app = RouteViewerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

