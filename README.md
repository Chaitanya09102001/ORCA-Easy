# ORCA-Easy
A GUI platform for easy input generation, running and parsing the ORCA quantum chemistry job. Features include convenient selection of job parameters from dropdown menus and live streaming of updating output file with a special analysis window for grabbing essential values from the output files. 
# ORCA-Easy v1.0
### Designed and Developed by Chaitanya Gadekar
**Project Initiative:** *The Molecular Coder* **Application Core License:** MIT License  
**Parser Component License:** Sourced under Public Domain / The Unlicense

---

## 🌟 1. Overview & Vision
**ORCA-Easy** is a graphical user interface platform designed for easy input generation, running, and parsing of ORCA quantum chemistry jobs. Built in Python using `customtkinter`, it streamlines the entire computational workflow into a seamless, dark-themed dashboard. 

By translating raw molecular coordinates and researcher intent into strict, error-free ORCA syntax, the application completely eliminates command-line friction. Key highlights include:
* **Convenient Parameter Selection:** Quickly configure complex quantum mechanical calculations using intuitive drop-down menus for methods, basis sets, solvation, and hardware resources.
* **Live Stream Processing:** Monitor background computational runs in real-time with an active updating output terminal stream.
* **Specialized Analysis Window:** Automatically parse and isolate essential physical and thermodynamic values from finalized log outputs into a clean data visualizer pane.

This project is dedicated to democratizing scientific computing tools and accelerating laboratory research infrastructure across regional academic nodes.

---

## ⚠️ 2. Mandatory Requirement: Independent ORCA Setup
This software utility is **not** bundled, packaged, or distributed with the ORCA quantum chemistry program binaries. 

* **User Obligation:** Users must independently register, download, and license their own copy of ORCA from the official **Max-Planck-Institut für Kohlenforschung** portal.
* **Licensing Compliance:** ORCA is free for academic use, but users must adhere strictly to its End User License Agreement (EULA).
* **Path Alignment:** Upon initial boot of ORCA-Easy, navigate to the top bar, click **Browse** to locate your local `orca.exe` binary, and click **Save Path**. This permanently creates a local `orca_gui_settings.json` file so you do not have to map it on subsequent sessions.

---

## 🚀 3. Core Technical Features

### 💻 Auto-Adaptive Hardware Allocator
The application interacts directly with system hardware through the `psutil` library. It reads the total physical cores available and evaluates your active system memory.
* **Standard Mode:** Automatically restricts memory distribution to **75% of your available RAM**, dividing it cleanly by your chosen processor cores to determine the `%maxcore` value safely.
* **Max Performance Mode ("Use Full RAM"):** Overrides standard safety limits to divide **100% of your total physical RAM** equally across your designated parallel processor threads (`nprocs`), forcing the host computer to run at raw maximum performance capacity during calculation execution windows.

### 🧪 Advanced Chemistry Presets & Inline Solvation
The program features hardcoded dictionaries matching exact ORCA subroutines:
* **Functionals Supported:** From fundamental methods (`HF`, `MP2`) up to advanced density functionals (`B3LYP`, `M062X`, `wB97X-D3`).
* **Basis Sets:** Comprehensive suite including standard Pople split-valence sets (`6-31G(d)`) and advanced Karlsruhe types (`def2-SVP`, `def2-TZVP`, `def2-QZVP`, `def2-TZVPP`).
* **Resolution of Identity (RI):** Native toggles for `None`, `NORI`, `RIK`, `RIJONX`, and `RIJCOSX`.
* **Solvation Architecture:** Supports both **CPCM** (inline initialization: `! CPCM(Solvent)`) and **SMD** methods. Selecting SMD automatically builds an additional specialized, multi-line structural constraint block:
  ```text
  %cpcm
     smd true
     SMDsolvent "SolventName"
  end
* **About Dependencies** : ORCA-Easy v1.0 is built using Python (v3.8–v3.11) and relies on the following open-source frameworks:
customtkinter – Powers the modern, responsive, dark-themed User Interface.
psutil – Handles real-time system hardware profiling (CPU threads & RAM allocation metrics).
matplotlib – Manages data visualization components.
orca_parser – Acts as the external analytical parser engine to extract essential values from .out log files.
tkinter – Handles core native windowing and file dialog subroutines (built into Python).
