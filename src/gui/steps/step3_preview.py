"""
Étape 3 : Prévisualisation finale de toutes les courbes
"""

import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from core.constants import FILE_KEYS


class Step3Preview(ttk.Frame):
    """Prévisualisation finale avant export."""
    
    def __init__(self, parent, app_state):
        super().__init__(parent)
        self.app_state = app_state
        self._build_ui()
    
    def _build_ui(self):
        """Construction de l'interface."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        
        # Info en haut
        self.info_frame = ttk.Frame(self)
        self.info_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        self.lbl_info = ttk.Label(self.info_frame, text="", font=("Segoe UI", 10))
        self.lbl_info.pack(anchor="w")
        
        # Zone graphique
        self.graph_frame = ttk.Frame(self)
        self.graph_frame.grid(row=1, column=0, sticky="nsew")
    
    def refresh(self):
        """Rafraîchit la prévisualisation avec les données interpolées."""
        # Nettoyer le frame graphique
        for widget in self.graph_frame.winfo_children():
            widget.destroy()
        
        # Récupérer les données
        times = self.app_state.get("times")
        data_interp = self.app_state.get("data_interp", {})
        data_raw = self.app_state.get("data_raw", {})
        params = self.app_state.get("params", {})
        inlet_names = self.app_state.get("inlet_names", {"inlet1": "inlet1", "inlet2": "inlet2"})
        
        if times is None or not data_interp:
            self.lbl_info.config(text="⚠️ Aucune donnée interpolée disponible")
            return
        
        # Info
        sim_duration = self.app_state.get("sim_duration", 0)
        dt = params.get("dt_us", 1.0) * 1e-6
        n_pts = len(times)
        
        # Compter zones
        zones = params.get("unfiltered_zones", {})
        total_zones = sum(len(z) for z in zones.values())
        
        info_text = f"Durée : {sim_duration:.6f} s  |  "
        info_text += f"Pas de temps : {dt:.3e} s  |  "
        info_text += f"Points : {n_pts:,}  |  "
        info_text += f"Zones totales : {total_zones}"
        
        self.lbl_info.config(text=info_text)
        
        # Graphique 2x2
        fig = Figure(figsize=(10, 8), dpi=100)
        
        for i, key in enumerate(FILE_KEYS):
            ax = fig.add_subplot(2, 2, i + 1)
            
            # Lignes linéaires entre points bruts (référence) en noir
            if key in data_raw:
                df = data_raw[key]
                ax.plot(
                    df["Time_s"],
                    df["Value"],
                    "-",
                    color="black",
                    label="Linéaire",
                    linewidth=0.8,
                    alpha=0.3,
                    zorder=1
                )
            
            # Points de données brutes
            if key in data_raw:
                df = data_raw[key]
                ax.plot(
                    df["Time_s"],
                    df["Value"],
                    "o",
                    label="Brut",
                    markersize=3,
                    alpha=0.8,
                    zorder=3,
                    color="C0"
                )
            
            # Données interpolées (avec clé renommée)
            # Convertir key original en key renommé
            key_renamed = key
            for old_name, new_name in inlet_names.items():
                key_renamed = key_renamed.replace(old_name, new_name)
            
            if key_renamed in data_interp:
                # Obtenir le nom de la méthode
                methods = params.get("methods", {})
                method_key = methods.get(key, "spline")
                
                # Label selon la méthode
                from core.constants import INTERP_METHODS
                if method_key in INTERP_METHODS:
                    method_label = INTERP_METHODS[method_key]
                else:
                    method_label = "Interpolé"
                
                # Ajouter paramètre de lissage si applicable
                if method_key == "spline":
                    smooth_params = params.get("smooth_params", {})
                    smooth = smooth_params.get(key, 0.01)
                    method_label += f" (s={smooth:.4f})"
                
                ax.plot(
                    times,
                    data_interp[key_renamed],
                    "-",
                    label=method_label,
                    linewidth=2.5,
                    zorder=2,
                    color="C1"
                )
            
            ax.set_xlabel("Temps (s)")
            ax.set_ylabel("Valeur")
            
            # Titre avec nom personnalisé
            inlet_num = "1" if "inlet1" in key else "2"
            var_type = "Débit" if key.startswith("Q_") else "Température"
            custom_name = inlet_names.get(f"inlet{inlet_num}", f"Inlet {inlet_num}")
            ax.set_title(f"{var_type} {custom_name}")
            ax.legend()
            ax.grid(True, alpha=0.3)
        
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, self.graph_frame)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        canvas.draw()
    
    def validate(self) -> tuple[bool, str]:
        """
        Validation (toujours vraie pour la prévisualisation).
        
        Returns:
            (is_valid, error_message)
        """
        return True, ""
