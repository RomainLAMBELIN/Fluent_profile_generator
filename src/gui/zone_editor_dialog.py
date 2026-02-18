"""
Dialogue avancé pour définir une zone avec prévisualisation en temps réel
"""

import tkinter as tk
from tkinter import ttk
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from core.interpolation import interpolate
from core.analysis import compute_interpolation_error, format_error_text
from core.constants import DEFAULT_SAVGOL_WINDOW, DEFAULT_SAVGOL_POLYORDER


class ZoneEditorDialog(tk.Toplevel):
    """Dialogue avancé avec sliders et prévisualisation temps réel."""
    
    def __init__(self, parent, sim_duration, df, current_method, current_smooth, 
                 t_start=None, t_end=None, zone_type="exact"):
        super().__init__(parent)
        self.title("Définir une zone - Prévisualisation temps réel")
        self.geometry("900x600")
        self.resizable(True, True)
        
        self.sim_duration = sim_duration
        self.df = df  # DataFrame des données brutes
        self.current_method = current_method
        self.current_smooth = current_smooth
        self.result = None
        
        # Variables
        self.t_start_var = tk.DoubleVar(value=t_start if t_start is not None else 0.0)
        self.t_end_var = tk.DoubleVar(value=t_end if t_end is not None else sim_duration * 0.1)
        self.zone_type_var = tk.StringVar(value=zone_type)
        
        self._build_ui()
        self._update_preview()
        
        # Modal
        self.transient(parent)
        self.grab_set()
        
        # Centrer
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{max(0,x)}+{max(0,y)}")
    
    def _build_ui(self):
        """Construction de l'interface."""
        # Frame principal
        main = ttk.Frame(self, padding=10)
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=1)
        main.rowconfigure(1, weight=1)
        
        # Panneau de contrôle en haut
        control_frame = ttk.LabelFrame(main, text="Paramètres de la zone", padding=10)
        control_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        control_frame.columnconfigure(1, weight=1)
        
        # Début avec slider
        row = 0
        ttk.Label(control_frame, text="Début (s) :", width=12).grid(row=row, column=0, sticky="w", pady=5)
        
        # Entry SANS textvariable pour éviter conflits
        self.entry_start = ttk.Entry(control_frame, width=12)
        self.entry_start.grid(row=row, column=1, sticky="w", padx=5)
        self.entry_start.insert(0, f"{self.t_start_var.get():.6f}")
        self.entry_start.bind("<Return>", lambda e: self._on_entry_change())
        self.entry_start.bind("<FocusOut>", lambda e: self._on_entry_change())
        
        self.slider_start = ttk.Scale(
            control_frame,
            from_=0,
            to=self.sim_duration,
            orient="horizontal",
            variable=self.t_start_var,
            command=lambda v: self._on_slider_change()
        )
        self.slider_start.grid(row=row, column=2, sticky="ew", padx=5)
        
        # Fin avec slider
        row = 1
        ttk.Label(control_frame, text="Fin (s) :", width=12).grid(row=row, column=0, sticky="w", pady=5)
        
        # Entry SANS textvariable pour éviter conflits
        self.entry_end = ttk.Entry(control_frame, width=12)
        self.entry_end.grid(row=row, column=1, sticky="w", padx=5)
        self.entry_end.insert(0, f"{self.t_end_var.get():.6f}")
        self.entry_end.bind("<Return>", lambda e: self._on_entry_change())
        self.entry_end.bind("<FocusOut>", lambda e: self._on_entry_change())
        
        self.slider_end = ttk.Scale(
            control_frame,
            from_=0,
            to=self.sim_duration,
            orient="horizontal",
            variable=self.t_end_var,
            command=lambda v: self._on_slider_change()
        )
        self.slider_end.grid(row=row, column=2, sticky="ew", padx=5)
        
        # Type
        row = 2
        ttk.Label(control_frame, text="Type :", width=12).grid(row=row, column=0, sticky="w", pady=5)
        
        type_frame = ttk.Frame(control_frame)
        type_frame.grid(row=row, column=1, columnspan=2, sticky="w", padx=5)
        
        ttk.Radiobutton(
            type_frame,
            text="Exacte (PCHIP)",
            variable=self.zone_type_var,
            value="exact",
            command=self._update_preview
        ).pack(side="left", padx=5)
        
        ttk.Radiobutton(
            type_frame,
            text="Linéaire (2 pts)",
            variable=self.zone_type_var,
            value="linear",
            command=self._update_preview
        ).pack(side="left", padx=5)
        
        # Graphique de prévisualisation
        preview_frame = ttk.LabelFrame(main, text="Prévisualisation (mise à jour automatique)", padding=10)
        preview_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        
        self.fig = Figure(figsize=(8, 4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, preview_frame)
        self.canvas.get_tk_widget().pack(side="top", fill="both", expand=True)
        
        # Toolbar de navigation pour zoom (utiliser pack dans le même parent)
        from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
        toolbar = NavigationToolbar2Tk(self.canvas, preview_frame)
        toolbar.update()
        toolbar.pack(side="bottom", fill="x")
        
        # Boutons
        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Annuler", command=self.destroy, width=12).pack(side="right")
        ttk.Button(btn_frame, text="OK", command=self._on_ok, width=12).pack(side="right", padx=(5, 5))
        
        # Bind touches
        self.bind("<Return>", lambda e: self._on_ok())
        self.bind("<Escape>", lambda e: self.destroy())
    
    def _on_slider_change(self):
        """Callback quand un slider bouge."""
        try:
            # Récupérer les valeurs des sliders (pas des Entry)
            t_start = self.slider_start.get()
            t_end = self.slider_end.get()
            
            # Mettre à jour les Entry de manière sûre
            self.entry_start.delete(0, "end")
            self.entry_start.insert(0, f"{t_start:.6f}")
            
            self.entry_end.delete(0, "end")
            self.entry_end.insert(0, f"{t_end:.6f}")
            
            # Mettre à jour les variables
            self.t_start_var.set(t_start)
            self.t_end_var.set(t_end)
            
            self._update_preview()
        except Exception as e:
            print(f"Erreur slider change: {e}")
    
    def _on_entry_change(self):
        """Callback quand un Entry change (Return ou FocusOut)."""
        try:
            # Lire depuis les Entry
            t_start = float(self.entry_start.get())
            t_end = float(self.entry_end.get())
            
            # Mettre à jour les variables (qui mettront à jour les sliders)
            self.t_start_var.set(t_start)
            self.t_end_var.set(t_end)
            
            self._update_preview()
        except ValueError as e:
            print(f"Valeur invalide dans Entry: {e}")
    
    def _update_preview(self):
        """Met à jour le graphique de prévisualisation."""
        try:
            t_start = float(self.t_start_var.get())
            t_end = float(self.t_end_var.get())
            zone_type = self.zone_type_var.get()
            
            # Validation
            if t_start >= t_end:
                return
            
            # Données brutes
            x = self.df["Time_s"].to_numpy()
            y = self.df["Value"].to_numpy()
            
            # Temps pour interpolation
            times = np.linspace(x[0], x[-1], min(1000, len(x) * 10))
            
            # Interpolation SANS zone (référence)
            interp_no_zone = interpolate(
                self.df,
                times,
                method=self.current_method,
                smooth_factor=self.current_smooth,
                unfiltered_zones=[],
                savgol_window=DEFAULT_SAVGOL_WINDOW,
                savgol_polyorder=DEFAULT_SAVGOL_POLYORDER,
                transition_ratio=0.02  # Valeur par défaut
            )
            
            # Interpolation AVEC zone
            interp_with_zone = interpolate(
                self.df,
                times,
                method=self.current_method,
                smooth_factor=self.current_smooth,
                unfiltered_zones=[(t_start, t_end, zone_type)],
                savgol_window=DEFAULT_SAVGOL_WINDOW,
                savgol_polyorder=DEFAULT_SAVGOL_POLYORDER,
                transition_ratio=0.02  # Valeur par défaut
            )
            
            # Tracer
            self.fig.clear()
            ax = self.fig.add_subplot(111)
            
            # Points bruts
            ax.plot(x, y, 'o', label="Données brutes", markersize=4, alpha=0.7, color="C0", zorder=3)
            
            # Sans zone (référence en noir)
            ax.plot(times, interp_no_zone, '-', label="Sans zone (référence)", 
                   linewidth=1.5, alpha=0.4, color="black", zorder=1)
            
            # Avec zone (couleur)
            ax.plot(times, interp_with_zone, '-', label=f"Avec zone {zone_type}", 
                   linewidth=2.5, color="C1", zorder=2)
            
            # Marquer la zone
            ax.axvline(t_start, color='red', linestyle='--', alpha=0.7, linewidth=1)
            ax.axvline(t_end, color='red', linestyle='--', alpha=0.7, linewidth=1)
            ax.axvspan(t_start, t_end, alpha=0.1, color='red')
            
            # Calculer les erreurs
            error_no_zone = compute_interpolation_error(self.df, times, interp_no_zone)
            error_with_zone = compute_interpolation_error(self.df, times, interp_with_zone)
            
            ax.set_xlabel("Temps (s)")
            ax.set_ylabel("Valeur")
            title = f"Effet de la zone (rouge) sur l'interpolation\n"
            title += f"Sans zone: {format_error_text(error_no_zone)} | "
            title += f"Avec zone: {format_error_text(error_with_zone)}"
            ax.set_title(title, fontsize=10)
            ax.legend(loc="best")
            ax.grid(True, alpha=0.3)
            
            self.fig.tight_layout()
            self.canvas.draw()
        
        except Exception as e:
            print(f"Erreur prévisualisation: {e}")
    
    def _on_ok(self):
        """Valide et ferme."""
        try:
            t_start = float(self.t_start_var.get())
            t_end = float(self.t_end_var.get())
            
            if t_start < 0 or t_end > self.sim_duration:
                from tkinter import messagebox
                messagebox.showerror("Erreur", 
                    f"Les temps doivent être entre 0 et {self.sim_duration:.6f}", 
                    parent=self)
                return
            
            if t_start >= t_end:
                from tkinter import messagebox
                messagebox.showerror("Erreur", 
                    "Le début doit être strictement inférieur à la fin", 
                    parent=self)
                return
            
            self.result = (t_start, t_end, self.zone_type_var.get())
            self.destroy()
        
        except ValueError as e:
            from tkinter import messagebox
            messagebox.showerror("Erreur", str(e), parent=self)
