# ---------------------------------------------------------------------------
# The Molecular Coder: ORCA Workflow GUI v4.0 Master (Combined)
# Developer: Chaitanya Gadekar
# Copyright (c) 2026 Chaitanya09102001
# Licensed under the MIT License
#
# NOTE: This software is provided "as-is". Always verify your input files!
# ---------------------------------------------------------------------------

import os
import psutil
import subprocess
import threading
import json
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import orca_parser as op

# ---------------------------------------------------------------------------
# Dropdown option lists
# ---------------------------------------------------------------------------

FUNCTIONALS = [
    "HF", "MP2", "CCSD", "CCSD(T)",
    "BLYP", "PBE", "PBE0", "revPBE",
    "B3LYP", "B97-3C", "M06L", "M062X", "wB97X-D3",
]

BASIS_SETS = [
    "6-31G(d)",
    "cc-pVDZ", "cc-pVTZ", "cc-pVQZ",
    "aug-cc-pVDZ", "aug-cc-pVTZ", "aug-cc-pVQZ",
    "def2-SVP", "def2-TZVP", "def2-QZVP",
    "def2-TZVPP", "def2-QZVPP",
    "def2-TZVPPD", "def2-QZVPPD",
    "ma-def2-SVP", "ma-def2-TZVP", "ma-def2-QZVP",
]

# Display label -> ORCA keyword for job type
JOB_TYPE_DISPLAY = [
    "Single Point Energy",
    "Geometry Optimization",
    "Geometry Optimization + Frequency",
    "Frequency Analysis",
]
JOB_TYPE_KEYWORD = {
    "Single Point Energy":                  "SP",
    "Geometry Optimization":                "Opt",
    "Geometry Optimization + Frequency":    "Opt Freq",
    "Frequency Analysis":                   "Freq",
}

SCF_OPTIONS = ["LooseSCF", "NormalSCF", "TightSCF", "VeryTightSCF"]

RI_OPTIONS = ["None", "NORI", "RIK", "RIJONX", "RIJCOSX"]

# Solvation models
SOLV_MODEL_OPTIONS = ["None", "CPCM", "SMD"]

# Solvents (ORCA-recognised names)
SOLVENTS = [
    "None (gas)", "Water", "Acetonitrile", "Acetone",
    "Ethanol", "Methanol", "CCl4", "CH2Cl2",
    "Chloroform", "DMSO", "DMF", "Hexane",
    "Toluene", "Pyridine", "THF",
]

# Solvent display name -> ORCA keyword
SOLVENT_KEYWORDS = {
    "None (gas)":   None,
    "Water":        "Water",
    "Acetonitrile": "Acetonitrile",
    "Acetone":      "Acetone",
    "Ethanol":      "Ethanol",
    "Methanol":     "Methanol",
    "CCl4":         "CCl4",
    "CH2Cl2":       "CH2Cl2",
    "Chloroform":   "Chloroform",
    "DMSO":         "DMSO",
    "DMF":          "DMF",
    "Hexane":       "Hexane",
    "Toluene":      "Toluene",
    "Pyridine":     "Pyridine",
    "THF":          "THF",
}

# ---------------------------------------------------------------------------
# Settings persistence
# ---------------------------------------------------------------------------
SETTINGS_FILE = "orca_gui_settings.json"

def save_settings(settings: dict):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=2)
    except Exception as e:
        print(f"[Settings] Save error: {e}")

def load_settings() -> dict:
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"orca_path": "D:/ORCA/orca.exe"}

# ---------------------------------------------------------------------------
# Main Application
# ---------------------------------------------------------------------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class OrcaMasterGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.settings = load_settings()
        self.title("The Molecular Coder: ORCA Workflow v4.0 Master | Dev: Chaitanya Gadekar")
        self.geometry("1600x950")

        # Grid: two equal columns, row 1 = main content, row 2 = job bar, row 3 = launch
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=0)

        # State
        self.xyz_path      = ""
        self.file_dir      = os.getcwd()
        self.molecule_name = "molecule"
        self.coords        = ""
        self.output_path   = ""
        self.stop_flag     = threading.Event()

        self.setup_ui()
        self.log("Ready. Load an XYZ file or import an existing .inp file.")

    # =========================================================================
    # UI CONSTRUCTION
    # =========================================================================
    def setup_ui(self):
        self._build_top_bar()
        self._build_left_panel()
        self._build_right_panel()
        self._build_job_bar()
        self._build_launch_bar()

    # ── Top bar ───────────────────────────────────────────────────────────────
    def _build_top_bar(self):
        bar = ctk.CTkFrame(self, height=50)
        bar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=5)

        ctk.CTkLabel(bar, text="ORCA Path:").pack(side="left", padx=10)

        self.path_entry = ctk.CTkEntry(bar, width=480)
        self.path_entry.insert(0, self.settings.get("orca_path", ""))
        self.path_entry.pack(side="left", padx=5)

        ctk.CTkButton(bar, text="Browse", width=80,
                      command=self._browse_orca_path,
                      fg_color="#2b2b2b").pack(side="left", padx=2)

        ctk.CTkButton(bar, text="Save Path", width=90,
                      command=self.save_orca_path,
                      fg_color="#2b2b2b").pack(side="left", padx=5)

        ctk.CTkButton(bar, text="New Session", width=110,
                      command=self.reset_session,
                      fg_color="gray").pack(side="right", padx=10)

        self.status_lbl = ctk.CTkLabel(bar, text="Ready", text_color="yellow")
        self.status_lbl.pack(side="right", padx=20)

        # Use Full RAM toggle
        self.full_ram_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(bar, text="Use Full RAM",
                        variable=self.full_ram_var,
                        command=self._update_maxcore_from_ram).pack(side="left", padx=15)

    # ── Left panel ────────────────────────────────────────────────────────────
    def _build_left_panel(self):
        self.left_container = ctk.CTkFrame(self, fg_color="transparent")
        self.left_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.left_container.grid_columnconfigure(0, weight=1)
        self.left_container.grid_rowconfigure(0, weight=1)   # scrollable controls
        self.left_container.grid_rowconfigure(1, weight=1)   # input editor

        # Scrollable controls
        self.controls = ctk.CTkScrollableFrame(
            self.left_container, label_text="Generator Control")
        self.controls.grid(row=0, column=0, sticky="nsew", pady=(0, 5))

        # File loaders
        self.btn_xyz = ctk.CTkButton(
            self.controls, text="Load XYZ Molecule",
            command=self.load_xyz, fg_color="#3d5a80")
        self.btn_xyz.pack(fill="x", padx=10, pady=5)

        self.btn_import = ctk.CTkButton(
            self.controls, text="Import Existing .inp",
            command=self.import_input, fg_color="#d97706")
        self.btn_import.pack(fill="x", padx=10, pady=5)

        # Job type — full display names
        self.job_var = ctk.StringVar(value="Geometry Optimization")
        self._dropdown(self.controls, "Job Type:", JOB_TYPE_DISPLAY, self.job_var)

        # SCF Quality
        self.scf_var = ctk.StringVar(value="NormalSCF")
        self._dropdown(self.controls, "SCF Quality:", SCF_OPTIONS, self.scf_var)

        # Theory / Functional
        self.theory_var = ctk.StringVar(value="B3LYP")
        self._dropdown(self.controls, "Functional / Theory:", FUNCTIONALS, self.theory_var)

        self.d3bj_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            self.controls, text="Apply D3BJ Dispersion Correction",
            variable=self.d3bj_var).pack(anchor="w", padx=15, pady=2)

        # Basis set
        self.basis_var = ctk.StringVar(value="def2-SVP")
        self._dropdown(self.controls, "Basis Set:", BASIS_SETS, self.basis_var)

        # RI Approximation
        self.ri_var = ctk.StringVar(value="None")
        self._dropdown(self.controls, "RI Approximation:", RI_OPTIONS, self.ri_var)

        # Solvation model
        self.solv_model_var = ctk.StringVar(value="None")
        self._dropdown(self.controls, "Solvation Model:", SOLV_MODEL_OPTIONS, self.solv_model_var)

        # Solvent
        self.solvent_var = ctk.StringVar(value="None (gas)")
        self._dropdown(self.controls, "Solvent:", SOLVENTS, self.solvent_var)

        # Print Orbitals
        self.orb_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            self.controls, text="Print Molecular Orbitals  (print[p_mos] 1)",
            variable=self.orb_var).pack(anchor="w", padx=15, pady=2)

        # AutoAux
        self.autoaux_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            self.controls, text="AutoAux  (auto-generate auxiliary basis)",
            variable=self.autoaux_var).pack(anchor="w", padx=15, pady=2)

        # Charge and Multiplicity
        self.charge_var = ctk.StringVar(value="0")
        self.mult_var   = ctk.StringVar(value="1")
        self._entry(self.controls, "Charge:", self.charge_var)
        self._entry(self.controls, "Multiplicity:", self.mult_var)

        # CPU / Memory — default nprocs=1, memory = 75% available for 1 core
        detected_cores = psutil.cpu_count(logical=False) or 1
        avail_mb       = int(psutil.virtual_memory().available / (1024 ** 2))
        maxcore_mb     = int(avail_mb * 0.75)   # for nprocs=1

        self.nprocs_var  = ctk.StringVar(value="1")
        self.maxcore_var = ctk.StringVar(value=str(maxcore_mb))
        # Recalculate maxcore automatically when nprocs changes
        self.nprocs_var.trace_add("write", self._update_maxcore_from_ram)
        self._entry(self.controls,
                    f"Processor Cores  (detected: {detected_cores} physical):",
                    self.nprocs_var)
        self._entry(self.controls,
                    f"Memory per core MB  (auto-updated, editable):",
                    self.maxcore_var)

        ctk.CTkButton(
            self.controls, text="GENERATE / UPDATE INPUT",
            fg_color="darkgreen", height=40,
            command=self.generate_input).pack(fill="x", padx=10, pady=10)

        # Input file editor
        ctk.CTkLabel(
            self.left_container,
            text="Input File Editor  (editable before run)").grid(
            row=1, column=0, sticky="nw", padx=5)
        self.input_editor = ctk.CTkTextbox(
            self.left_container, font=("Consolas", 13))
        self.input_editor.grid(row=1, column=0, sticky="nsew", pady=(18, 5))

    # ── Right panel ───────────────────────────────────────────────────────────
    def _build_right_panel(self):
        self.right_container = ctk.CTkFrame(self)
        self.right_container.grid(row=1, column=1, sticky="nsew", padx=10, pady=5)
        self.right_container.grid_columnconfigure(0, weight=1)
        self.right_container.grid_rowconfigure(0, weight=0)   # live output label
        self.right_container.grid_rowconfigure(1, weight=2)   # live output box  (TOP, bigger)
        self.right_container.grid_rowconfigure(2, weight=0)   # parsed results label
        self.right_container.grid_rowconfigure(3, weight=1)   # parsed results box (BOTTOM)

        # Live output stream on TOP
        ctk.CTkLabel(
            self.right_container,
            text="Live Output  (.out file stream)",
            anchor="w").grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 0))
        self.live_out_box = ctk.CTkTextbox(
            self.right_container,
            fg_color="black", text_color="#00FF00",
            font=("Consolas", 11))
        self.live_out_box.grid(row=1, column=0, sticky="nsew", padx=5, pady=(4, 5))

        # Parsed results on BOTTOM
        ctk.CTkLabel(
            self.right_container,
            text="Status and Parsed Results",
            anchor="w").grid(row=2, column=0, sticky="ew", padx=10, pady=(8, 0))
        self.analysis_box = ctk.CTkTextbox(
            self.right_container,
            fg_color="#111111", text_color="orange",
            font=("Consolas", 12))
        self.analysis_box.grid(row=3, column=0, sticky="nsew", padx=5, pady=(4, 5))

    # ── Launch bar ────────────────────────────────────────────────────────────
    def _build_launch_bar(self):
        self.btn_run = ctk.CTkButton(
            self, text="LAUNCH ORCA CALCULATION",
            height=50, font=("Roboto", 16, "bold"),
            fg_color="#1e40af",
            command=self.start_run)
        self.btn_run.grid(row=3, column=0, columnspan=2,
                          sticky="ew", padx=10, pady=(0, 10))

    # ── Job bar (shown during/after run) ─────────────────────────────────────
    def _build_job_bar(self):
        self.job_bar = ctk.CTkFrame(self, height=40)
        self.job_bar.grid(row=2, column=0, columnspan=2,
                          sticky="ew", padx=10, pady=(2, 2))
        self.job_bar.grid_columnconfigure(1, weight=1)

        self.btn_new_job = ctk.CTkButton(
            self.job_bar, text="New Job  (reset generator)",
            width=200, fg_color="#7c3aed",
            command=self.new_job)
        self.btn_new_job.grid(row=0, column=0, padx=10, pady=5)

        self.job_status_lbl = ctk.CTkLabel(
            self.job_bar, text="", text_color="#aaaaaa",
            anchor="w")
        self.job_status_lbl.grid(row=0, column=1, sticky="w", padx=10)

        # Hidden until a run starts
        self.job_bar.grid_remove()

    def _lock_controls(self):
        """Disable all generator widgets while ORCA is running."""
        self.job_bar.grid()   # show the job bar
        self.job_status_lbl.configure(text="Calculation running...  Generator locked.")
        self.btn_new_job.configure(state="disabled")
        # Disable every widget inside the scrollable controls frame
        for widget in self._all_control_widgets():
            try:
                widget.configure(state="disabled")
            except Exception:
                pass
        self.input_editor.configure(state="disabled")

    def _unlock_controls(self):
        """Re-enable all generator widgets (called only by New Job)."""
        for widget in self._all_control_widgets():
            try:
                widget.configure(state="normal")
            except Exception:
                pass
        self.input_editor.configure(state="normal")
        self.job_status_lbl.configure(text="")
        self.job_bar.grid_remove()

    def _all_control_widgets(self):
        """Return all interactive widgets inside the scrollable controls frame."""
        widgets = []
        def collect(parent):
            for child in parent.winfo_children():
                if isinstance(child, (ctk.CTkButton, ctk.CTkOptionMenu,
                                      ctk.CTkEntry, ctk.CTkCheckBox)):
                    widgets.append(child)
                collect(child)
        collect(self.controls)
        return widgets

    def new_job(self):
        """Unlock the generator for a new calculation without clearing the output."""
        self._unlock_controls()
        self.btn_run.configure(state="normal")
        self.log("Generator unlocked. Set up your next job.")

    # =========================================================================
    # UI HELPERS
    # =========================================================================
    def _dropdown(self, parent, label, opts, var):
        ctk.CTkLabel(parent, text=label).pack(anchor="w", padx=15)
        ctk.CTkOptionMenu(parent, values=opts, variable=var).pack(
            fill="x", padx=10, pady=(0, 5))

    def _entry(self, parent, label, var):
        ctk.CTkLabel(parent, text=label).pack(anchor="w", padx=15)
        ctk.CTkEntry(parent, textvariable=var).pack(
            fill="x", padx=10, pady=(0, 5))

    # =========================================================================
    # ACTIONS
    # =========================================================================

    def _update_maxcore_from_ram(self, *args):
        """Recalculate maxcore whenever Full RAM toggle or nprocs changes."""
        try:
            nprocs = max(1, int(self.nprocs_var.get()))
        except ValueError:
            nprocs = 1
        total_mb = int(psutil.virtual_memory().total / (1024 ** 2))
        avail_mb = int(psutil.virtual_memory().available / (1024 ** 2))
        if self.full_ram_var.get():
            # Full RAM: total RAM divided equally across cores
            maxcore = int(total_mb / nprocs)
        else:
            # Default: 75% of available RAM divided equally across cores
            maxcore = int((avail_mb * 0.75) / nprocs)
        self.maxcore_var.set(str(maxcore))

    def _browse_orca_path(self):
        path = filedialog.askopenfilename(
            title="Locate orca.exe",
            filetypes=[("Executable", "*.exe"), ("All files", "*.*")])
        if path:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, path)

    def save_orca_path(self):
        self.settings["orca_path"] = self.path_entry.get().strip()
        save_settings(self.settings)
        self.log(f"ORCA path saved: {self.settings['orca_path']}")

    def reset_session(self):
        self.input_editor.delete("1.0", tk.END)
        self.analysis_box.delete("1.0", tk.END)
        self.live_out_box.delete("1.0", tk.END)
        self.coords        = ""
        self.xyz_path      = ""
        self.molecule_name = "molecule"
        self.btn_xyz.configure(text="Load XYZ Molecule")
        self.btn_import.configure(text="Import Existing .inp")
        self.status_lbl.configure(text="Ready", text_color="yellow")
        self.log("Session reset.")

    def log(self, msg: str):
        self.analysis_box.insert(tk.END, f"\n[STATUS] {msg}")
        self.analysis_box.see(tk.END)
        self.status_lbl.configure(text=msg[:70], text_color="white")

    def _stream_live(self, line: str):
        self.live_out_box.insert(tk.END, line)
        self.live_out_box.see(tk.END)

    # ── File loading ──────────────────────────────────────────────────────────
    def load_xyz(self):
        path = filedialog.askopenfilename(filetypes=[("XYZ files", "*.xyz")])
        if not path:
            return
        self.xyz_path      = path
        self.file_dir      = os.path.abspath(os.path.dirname(path))
        self.molecule_name = os.path.basename(path).replace(".xyz", "")

        with open(path, "r") as f:
            lines = f.readlines()

        # Deduplicate coordinate lines
        seen, unique = set(), []
        for ln in lines[2:]:
            stripped = ln.strip()
            if stripped and stripped not in seen:
                seen.add(stripped)
                unique.append(ln)
        self.coords = "".join(unique)

        self.btn_xyz.configure(text=f"Loaded: {os.path.basename(path)}")
        self.log(f"{os.path.basename(path)} loaded. Ready to generate input.")
        self.generate_input()

    def import_input(self):
        path = filedialog.askopenfilename(filetypes=[("ORCA Input", "*.inp")])
        if not path:
            return
        self.file_dir      = os.path.abspath(os.path.dirname(path))
        self.molecule_name = os.path.basename(path).replace(".inp", "")
        with open(path, "r") as f:
            text = f.read()
        self.input_editor.delete("1.0", tk.END)
        self.input_editor.insert("1.0", text)
        self.btn_import.configure(text=f"Imported: {os.path.basename(path)}")
        self.log(f"Imported {os.path.basename(path)}.")

    # ── Input generation ──────────────────────────────────────────────────────
    def generate_input(self):
        if not self.coords:
            messagebox.showwarning("XYZ Missing", "Please load an XYZ file first.")
            return

        # Resource values
        try:
            nprocs = max(1, int(self.nprocs_var.get()))
        except ValueError:
            nprocs = 1

        try:
            maxcore = int(self.maxcore_var.get())
        except ValueError:
            avail_mb = int(psutil.virtual_memory().available / (1024 ** 2))
            maxcore  = int(avail_mb * 0.75)

        # Job type keyword from display name
        job_keyword = JOB_TYPE_KEYWORD.get(self.job_var.get(), "SP")

        # Theory
        theory = self.theory_var.get()
        # D3BJ: skip for methods that already include dispersion or don't support it
        no_d3bj = {"HF", "MP2", "CCSD", "CCSD(T)", "B97-3C", "wB97X-D3"}
        if self.d3bj_var.get() and theory not in no_d3bj:
            theory += " D3BJ"

        ri_choice   = self.ri_var.get()
        ri_keyword  = f" {ri_choice}" if ri_choice != "None" else ""
        scf_keyword = f" {self.scf_var.get()}"
        autoaux_kw  = " AutoAux" if self.autoaux_var.get() else ""

        # Solvation model and solvent
        solv_model   = self.solv_model_var.get()          # "None", "CPCM", "SMD"
        solvent_name = self.solvent_var.get()
        solvent_kw   = SOLVENT_KEYWORDS.get(solvent_name)  # ORCA keyword string or None

        solv_inline = ""   # appended to the ! line
        solv_block  = ""   # separate %cpcm block if needed

        if solv_model == "CPCM" and solvent_kw:
            # CPCM is declared inline: ! ... CPCM(Solvent)
            solv_inline = f" CPCM({solvent_kw})"

        elif solv_model == "SMD" and solvent_kw:
            # SMD requires CPCM on the ! line plus a %cpcm block with smd true
            solv_inline = f" CPCM({solvent_kw})"
            solv_block  = f"%cpcm\n   smd true\n   SMDsolvent \"{solvent_kw}\"\nend"

        # Assemble keyword line
        line1 = (f"! {job_keyword} {theory} {self.basis_var.get()}"
                 f"{ri_keyword}{scf_keyword}{autoaux_kw}{solv_inline}")

        # Resource blocks
        line2 = f"%maxcore {maxcore}"
        line3 = f"%pal\n   nprocs {nprocs}\nend"

        # Optional orbital printing
        orb_block = "%output\n   print[p_mos] 1\nend" if self.orb_var.get() else ""

        # Coordinate block
        line4 = (f"* xyz {self.charge_var.get()} {self.mult_var.get()}\n"
                 f"{self.coords.strip()}\n*")

        parts = [line1, line2, line3]
        if orb_block:
            parts.append(orb_block)
        if solv_block:
            parts.append(solv_block)
        parts.append(line4)

        self.input_editor.delete("1.0", tk.END)
        self.input_editor.insert("1.0", "\n".join(parts))
        self.log("Input generated / updated.")

    # ── ORCA subprocess ───────────────────────────────────────────────────────
    def run_process(self):
        os.chdir(self.file_dir)
        inp_name = f"{self.molecule_name}.inp"
        out_name = f"{self.molecule_name}.out"
        self.output_path = os.path.join(self.file_dir, out_name)

        with open(os.path.join(self.file_dir, inp_name), "w") as f:
            f.write(self.input_editor.get("1.0", tk.END))

        orca_exe = self.settings.get("orca_path", "D:/ORCA/orca.exe")
        self.log(f"RUNNING: {self.molecule_name}  (ORCA: {orca_exe})")

        try:
            flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

            with open(self.output_path, "w") as out_file:
                process = subprocess.Popen(
                    [orca_exe, inp_name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=self.file_dir,
                    creationflags=flags,
                )
                for line in process.stdout:
                    out_file.write(line)
                    out_file.flush()
                    self.after(0, lambda ln=line: self._stream_live(ln))
                process.wait()

            with open(self.output_path, "r") as f:
                content = f.read()

            if "ORCA TERMINATED NORMALLY" in content:
                self.log("ORCA terminated normally. Parsing results...")
                self.after(0, self.parse_final_results)
            else:
                self.log("WARNING: ORCA may have encountered errors. Check live output.")

        except FileNotFoundError:
            self.log(f"ERROR: orca.exe not found at '{orca_exe}'. Update path and retry.")
        except Exception as e:
            self.log(f"ERROR during run: {e}")
        finally:
            self.stop_flag.set()
            # Do NOT unlock controls here — user clicks "New Job" to reset.
            # Just enable the New Job button so they can proceed when ready.
            self.after(0, lambda: self.btn_new_job.configure(state="normal"))
            self.after(0, lambda: self.job_status_lbl.configure(
                text="Calculation finished.  Click 'New Job' to set up another run."))

    def start_run(self):
        content = self.input_editor.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("Empty Input",
                                   "Generate or paste an input file first.")
            return
        self.stop_flag.clear()
        self.live_out_box.delete("1.0", tk.END)
        self.btn_run.configure(state="disabled")
        self._lock_controls()
        threading.Thread(target=self.run_process, daemon=True).start()

    # ── Post-calculation parser ───────────────────────────────────────────────
    def parse_final_results(self):
        if not self.output_path or not os.path.exists(self.output_path):
            self.log("No output file found to parse.")
            return

        summary_lines = []

        def record(msg: str):
            """Log to GUI status box and collect for summary file."""
            self.log(msg)
            summary_lines.append(msg)

        try:
            opt = op.ORCAParse(self.output_path)

            record("=" * 52)
            record(f"SUMMARY: {self.molecule_name}")
            record(f"Input file : {self.molecule_name}.inp")
            record(f"Output file: {self.molecule_name}.out")
            record("-" * 52)

            # Job settings read back from the first line of the editor
            inp_first_line = self.input_editor.get("1.0", "2.0").strip()
            record(f"Keywords   : {inp_first_line}")
            record(f"Charge     : {self.charge_var.get()}")
            record(f"Multiplicity: {self.mult_var.get()}")
            record(f"Solvation  : {self.solv_model_var.get()}  /  {self.solvent_var.get()}")
            record("-" * 52)

            # Timing
            try:
                elapsed = opt.seconds()
                record(f"Job time   : {elapsed:.1f} s  ({elapsed / 60:.2f} min)")
            except Exception:
                pass

            # Energies
            opt.parse_energies()
            energies_list = list(opt.energies)   # convert to plain list, avoids NumPy truth-value errors
            if len(energies_list) > 0:
                final_eh   = float(energies_list[-1])
                final_ev   = final_eh * 27.211386
                final_kcal = final_eh * 627.509
                record(f"Final energy: {final_eh:.8f} Eh")
                record(f"Final energy: {final_ev:.6f} eV")
                record(f"Final energy: {final_kcal:.4f} kcal/mol")
                if len(energies_list) > 1:
                    record(f"All SCF energies (Eh): {energies_list}")
            else:
                record("No energies found in output.")

            # Dipole
            try:
                dipole = opt.parse_dipole()
                record(f"Dipole moment: {dipole}")
            except Exception as e:
                record(f"Dipole: not available ({e})")

            # IR Frequencies — only for Freq jobs
            job_display = self.job_var.get()
            if "Frequency" in job_display:
                try:
                    opt.parse_IR()
                    record("IR Frequencies (cm-1):")
                    record(str(opt.IR))
                except Exception as e:
                    record(f"IR frequencies: not available ({e})")

            record("=" * 52)
            record("Parsing complete.")

            # Write human-readable summary file
            summary_path = os.path.join(
                self.file_dir, f"{self.molecule_name}_summary.txt")
            try:
                with open(summary_path, "w") as sf:
                    sf.write("\n".join(summary_lines) + "\n")
                self.log(f"Summary file written: {self.molecule_name}_summary.txt")
            except Exception as e:
                self.log(f"Could not write summary file: {e}")

        except Exception as e:
            self.log(f"Parser error: {e}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    OrcaMasterGUI().mainloop()
