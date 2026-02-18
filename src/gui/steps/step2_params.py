"""
Étape 2 : Paramétrage de l'interpolation avec configuration par courbe
"""

import tkinter as tk
from tkinter import ttk
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from core.constants import (
    DEFAULT_DT_US, DEFAULT_FLOW_EPS, DEFAULT_SMOOTH_Q, DEFAULT_SMOOTH_T,
    SMOOTH_MIN, SMOOTH_MAX, MAX_PREVIEW_POINTS, FILE_KEYS,
    INTERP_METHODS, DEFAULT_INTERP_METHOD, INTERP_METHODS_HELP,
    METHODS_WITH_SMOOTHING,
    DEFAULT_SAVGOL_WINDOW, DEFAULT_SAVGOL_POLYORDER, DEFAULT_TRANSITION_RATIO,
    TRANSITION_MIN, TRANSITION_MAX
)
from core.interpolation import interpolate, generate_time_array
from core.config import ConfigManager
from core.analysis import compute_interpolation_error, format_error_text
from gui.unfiltered_zones_dialog import UnfilteredZonesDialog

# Lookup inversé : affichage → clé de méthode
_METHOD_DISPLAY_TO_KEY = {v: k for k, v in INTERP_METHODS.items()}


class Step2Parameters(ttk.Frame):
    """Interface de paramétrage avec configuration par courbe."""
    
    def __init__(self, parent, app_state):
        super().__init__(parent)
        self.app_state = app_state
        self.preview_figs = {}
        self.preview_canvases = {}
        
        # Initialiser les paramètres
        self._init_params()
        
        # Variables Tkinter
        self.dt_us = tk.DoubleVar(value=self.app_state["params"]["dt_us"])
        self.flow_eps = tk.DoubleVar(value=self.app_state["params"]["flow_eps"])
        self.transition_ratio = tk.DoubleVar(value=self.app_state["params"]["transition_ratio"])
        
        self.method_vars = {}
        self.smooth_vars = {}
        self.smooth_labels = {}
        self.smooth_scales = {}
        self.zones_labels = {}
        
        for key in FILE_KEYS:
            self.method_vars[key] = tk.StringVar(value=self.app_state["params"]["methods"][key])
            self.smooth_vars[key] = tk.DoubleVar(value=self.app_state["params"]["smooth_params"][key])
        
        self._build_ui()
        self._update_zones_labels()
        self._update_preview()
    
    def _init_params(self):
        """Initialise les paramètres dans l'état."""
        if "params" not in self.app_state:
            self.app_state["params"] = {}

        params = self.app_state["params"]

        # Charger les derniers paramètres sauvegardés (si disponibles)
        config_mgr = ConfigManager()
        last_params = config_mgr.get_last_step2_params()
        
        # dt_us et flow_eps
        if "dt_us" not in params:
            params["dt_us"] = last_params.get("dt_us", DEFAULT_DT_US)
        if "flow_eps" not in params:
            params["flow_eps"] = last_params.get("flow_eps", DEFAULT_FLOW_EPS)
        
        # Méthodes par courbe
        if "methods" not in params:
            params["methods"] = last_params.get("methods", {key: DEFAULT_INTERP_METHOD for key in FILE_KEYS})
        
        # Lissage par courbe
        if "smooth_params" not in params:
            saved_smooth = last_params.get("smooth_params", {})
            params["smooth_params"] = {}
            for key in FILE_KEYS:
                if key in saved_smooth:
                    params["smooth_params"][key] = saved_smooth[key]
                else:
                    default = DEFAULT_SMOOTH_Q if key.startswith("Q_") else DEFAULT_SMOOTH_T
                    params["smooth_params"][key] = default
        
        # Zones par courbe (toujours vides au départ - trop spécifiques)
        if "unfiltered_zones" not in params:
            params["unfiltered_zones"] = {key: [] for key in FILE_KEYS}
        
        if "savgol_window" not in params:
            params["savgol_window"] = DEFAULT_SAVGOL_WINDOW
        if "savgol_polyorder" not in params:
            params["savgol_polyorder"] = DEFAULT_SAVGOL_POLYORDER
        
        # Ratio de transition Hermite
        if "transition_ratio" not in params:
            params["transition_ratio"] = last_params.get("transition_ratio", DEFAULT_TRANSITION_RATIO)
    
    def _build_ui(self):
        """Construction de l'interface."""
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(1, weight=1)
        
        # Bandeau d'informations en haut
        info_frame = ttk.Frame(self, padding=5)
        info_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        self.lbl_info = ttk.Label(
            info_frame,
            text="Chargement...",
            font=("Segoe UI", 9),
            foreground="blue"
        )
        self.lbl_info.pack(anchor="w")
        
        # Mettre à jour les infos
        self._update_info_label()
        
        # Panneau gauche : Paramètres
        left_frame = ttk.Frame(self)
        left_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        
        # Canvas avec scrollbar pour les paramètres
        scroll_canvas = tk.Canvas(left_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=scroll_canvas.yview)
        scrollable_frame = ttk.Frame(scroll_canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all"))
        )
        
        scroll_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        scroll_canvas.configure(yscrollcommand=scrollbar.set)
        
        scroll_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mouse wheel uniquement sur le panneau de paramètres
        def _on_mousewheel(event):
            scroll_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        scroll_canvas.bind("<MouseWheel>", _on_mousewheel)
        scrollable_frame.bind("<MouseWheel>", _on_mousewheel)
        
        # Paramètres globaux
        global_params = ttk.LabelFrame(scrollable_frame, text="Paramètres globaux", padding=10)
        global_params.pack(fill="x", padx=10, pady=10)
        
        # Pas de temps
        row = ttk.Frame(global_params)
        row.pack(fill="x", pady=5)
        ttk.Label(row, text="Pas de temps (µs) :").pack(side="left")
        ttk.Spinbox(row, from_=0.01, to=1000, textvariable=self.dt_us, width=10).pack(side="left", padx=10)
        
        # Flow eps
        row = ttk.Frame(global_params)
        row.pack(fill="x", pady=5)
        ttk.Label(row, text="Remplacement débits nuls :").pack(side="left")
        ttk.Entry(row, textvariable=self.flow_eps, width=10).pack(side="left", padx=10)
        
        # Transition Hermite
        row = ttk.Frame(global_params)
        row.pack(fill="x", pady=5)
        ttk.Label(row, text="Transition zones (%) :", width=22).pack(side="left")
        
        # Entry pour valeur numérique
        trans_entry = ttk.Entry(row, width=8)
        trans_entry.insert(0, f"{self.transition_ratio.get()*100:.1f}")
        trans_entry.pack(side="left", padx=5)
        
        def on_trans_entry_change(event):
            try:
                value = float(trans_entry.get()) / 100.0  # Convertir % en ratio
                value = max(TRANSITION_MIN, min(TRANSITION_MAX, value))
                self.transition_ratio.set(value)
                trans_entry.delete(0, "end")
                trans_entry.insert(0, f"{value*100:.1f}")
                self.app_state["params"]["transition_ratio"] = value
                self._update_preview()
            except ValueError:
                pass
        
        trans_entry.bind("<Return>", on_trans_entry_change)
        trans_entry.bind("<FocusOut>", on_trans_entry_change)
        
        # Slider
        trans_scale = ttk.Scale(
            row,
            from_=TRANSITION_MIN,
            to=TRANSITION_MAX,
            orient="horizontal",
            variable=self.transition_ratio,
            command=lambda v: self._on_transition_change(trans_entry)
        )
        trans_scale.pack(side="left", fill="x", expand=True, padx=5)
        
        # Label valeur
        self.trans_label = ttk.Label(row, text=f"{self.transition_ratio.get()*100:.1f}%", width=6)
        self.trans_label.pack(side="left")
        
        # Configuration par courbe
        inlet_names = self.app_state.get("inlet_names", {"inlet1": "inlet1", "inlet2": "inlet2"})
        curve_labels = {
            "Q_inlet1": f"Débit {inlet_names['inlet1']}",
            "T_inlet1": f"Température {inlet_names['inlet1']}",
            "Q_inlet2": f"Débit {inlet_names['inlet2']}",
            "T_inlet2": f"Température {inlet_names['inlet2']}",
        }
        
        for key in FILE_KEYS:
            self._build_curve_config(scrollable_frame, key, curve_labels[key])
        
        # Bouton rafraîchir
        ttk.Button(
            scrollable_frame,
            text="⟳ Rafraîchir prévisualisations",
            command=self._update_preview
        ).pack(fill="x", padx=10, pady=10)
        
        # Panneau droit : Prévisualisations
        right = ttk.Frame(self)
        right.grid(row=1, column=1, sticky="nsew")
        
        self.preview_notebook = ttk.Notebook(right)
        self.preview_notebook.pack(fill="both", expand=True)
        
        for key in FILE_KEYS:
            tab = ttk.Frame(self.preview_notebook)
            self.preview_notebook.add(tab, text=curve_labels[key])
            
            # Frame pour le canvas et la toolbar
            plot_frame = ttk.Frame(tab)
            plot_frame.pack(fill="both", expand=True)
            
            fig = Figure(figsize=(6, 4), dpi=100)
            canvas = FigureCanvasTkAgg(fig, plot_frame)
            canvas.get_tk_widget().pack(fill="both", expand=True)
            
            # Ajouter la toolbar de navigation (zoom, pan, etc.)
            from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
            toolbar = NavigationToolbar2Tk(canvas, plot_frame)
            toolbar.update()
            
            self.preview_figs[key] = fig
            self.preview_canvases[key] = canvas
    
    def _build_curve_config(self, parent, key, label):
        """Construit la configuration pour une courbe."""
        frame = ttk.LabelFrame(parent, text=label, padding=10)
        frame.pack(fill="x", padx=10, pady=5)
        
        # Méthode
        row = ttk.Frame(frame)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text="Méthode :", width=12).pack(side="left")
        combo = ttk.Combobox(
            row,
            textvariable=self.method_vars[key],
            values=list(INTERP_METHODS.values()),
            state="readonly",
            width=30
        )
        combo.pack(side="left", padx=5)
        combo.bind("<<ComboboxSelected>>", lambda e, k=key: self._on_method_change(k))
        
        # Lissage
        row = ttk.Frame(frame)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text="Lissage :", width=12).pack(side="left")
        
        # Entry pour valeur numérique
        smooth_entry = ttk.Entry(row, width=10)
        smooth_entry.insert(0, f"{self.smooth_vars[key].get():.4f}")
        smooth_entry.pack(side="left", padx=5)
        
        def on_smooth_entry_change(event, k=key, entry=smooth_entry):
            try:
                value = float(entry.get())
                value = max(SMOOTH_MIN, min(SMOOTH_MAX, value))  # Clamp
                self.smooth_vars[k].set(value)
                entry.delete(0, "end")
                entry.insert(0, f"{value:.4f}")
                self._on_smooth_change(k)
            except ValueError:
                pass
        
        smooth_entry.bind("<Return>", on_smooth_entry_change)
        smooth_entry.bind("<FocusOut>", on_smooth_entry_change)
        
        # Slider
        scale = ttk.Scale(
            row,
            from_=SMOOTH_MIN,
            to=SMOOTH_MAX,
            orient="horizontal",
            variable=self.smooth_vars[key],
            command=lambda v, k=key, entry=smooth_entry: self._on_smooth_slider_change(k, entry)
        )
        scale.pack(side="left", fill="x", expand=True, padx=5)
        self.smooth_scales[key] = scale
        
        lbl = ttk.Label(row, text=f"{self.smooth_vars[key].get():.4f}", width=8)
        lbl.pack(side="left")
        self.smooth_labels[key] = lbl
        
        # Zones
        row = ttk.Frame(frame)
        row.pack(fill="x", pady=2)
        ttk.Button(
            row,
            text="⚙️ Zones",
            command=lambda k=key: self._configure_zones(k),
            width=12
        ).pack(side="left")
        
        zones_lbl = ttk.Label(row, text="0 zone", font=("Segoe UI", 8), foreground="gray")
        zones_lbl.pack(side="left", padx=10)
        self.zones_labels[key] = zones_lbl
    
    def _on_method_change(self, key):
        """Callback quand la méthode change pour une courbe."""
        method_display = self.method_vars[key].get()
        method_key = _METHOD_DISPLAY_TO_KEY.get(method_display, DEFAULT_INTERP_METHOD)

        self.app_state["params"]["methods"][key] = method_key

        # Activer/désactiver le lissage selon la méthode
        if method_key in METHODS_WITH_SMOOTHING:
            self.smooth_scales[key].config(state="normal")
        else:
            self.smooth_scales[key].config(state="disabled")

        self._update_preview()
    
    def _on_smooth_change(self, key):
        """Callback quand le lissage change pour une courbe."""
        value = self.smooth_vars[key].get()
        self.smooth_labels[key].config(text=f"{value:.4f}")
        self.app_state["params"]["smooth_params"][key] = value
        self._update_info_label()
        self._update_preview()
    
    def _on_smooth_slider_change(self, key, entry):
        """Callback quand le slider de lissage change."""
        value = self.smooth_vars[key].get()
        # Mettre à jour l'Entry
        entry.delete(0, "end")
        entry.insert(0, f"{value:.4f}")
        self._on_smooth_change(key)
    
    def _on_transition_change(self, entry):
        """Callback quand le slider de transition change."""
        value = self.transition_ratio.get()
        # Mettre à jour l'Entry et le label
        entry.delete(0, "end")
        entry.insert(0, f"{value*100:.1f}")
        self.trans_label.config(text=f"{value*100:.1f}%")
        self.app_state["params"]["transition_ratio"] = value
        self._update_preview()
    
    def _configure_zones(self, key):
        """Configure les zones non-filtrées pour une courbe."""
        sim_duration = self.app_state.get("sim_duration", 1.0)
        zones = self.app_state["params"]["unfiltered_zones"].get(key, [])
        
        inlet_names = self.app_state.get("inlet_names", {"inlet1": "inlet1", "inlet2": "inlet2"})
        inlet_num = "1" if "inlet1" in key else "2"
        var_type = "Débit" if key.startswith("Q_") else "Température"
        custom_name = inlet_names.get(f"inlet{inlet_num}", f"Inlet {inlet_num}")
        
        # Récupérer les données et paramètres pour la prévisualisation
        df = self.app_state.get("data_raw", {}).get(key, None)
        method_display = self.method_vars[key].get()
        method = _METHOD_DISPLAY_TO_KEY.get(method_display, "pchip")
        
        smooth = self.smooth_vars[key].get()
        
        dialog = UnfilteredZonesDialog(
            self,
            sim_duration,
            zones,
            title=f"Zones - {var_type} {custom_name}",
            df=df,
            current_method=method,
            current_smooth=smooth
        )
        self.wait_window(dialog)
        
        if dialog.result is not None:
            self.app_state["params"]["unfiltered_zones"][key] = dialog.result
            self._update_zones_labels()
            self._update_preview()
    
    def _update_zones_labels(self):
        """Met à jour les labels de zones."""
        zones = self.app_state["params"]["unfiltered_zones"]
        
        for key, label in self.zones_labels.items():
            n_zones = len(zones.get(key, []))
            if n_zones > 0:
                label.config(text=f"{n_zones} zone(s)", foreground="green")
            else:
                label.config(text="0 zone", foreground="gray")
    
    def _update_info_label(self):
        """Met à jour le bandeau d'informations."""
        try:
            sim_duration = self.app_state.get("sim_duration", 0)
            dt = self.dt_us.get() * 1e-6
            
            if sim_duration > 0 and dt > 0:
                n_pts = int(sim_duration / dt) + 1
                
                # Compter les zones totales
                zones = self.app_state["params"]["unfiltered_zones"]
                total_zones = sum(len(z) for z in zones.values())
                
                info_text = f"📊 Durée simulation : {sim_duration:.6f} s  |  "
                info_text += f"⏱️ Pas de temps : {dt:.3e} s ({self.dt_us.get():.2f} µs)  |  "
                info_text += f"📈 Points interpolés : {n_pts:,}  |  "
                info_text += f"🎯 Zones définies : {total_zones}"
                
                self.lbl_info.config(text=info_text)
            else:
                self.lbl_info.config(text="⚠️ Chargement des paramètres...")
        except Exception as e:
            print(f"Erreur update info: {e}")
    
    def _update_preview(self):
        """Met à jour les graphiques de prévisualisation."""
        try:
            dt = self.dt_us.get() * 1e-6
            sim_duration = self.app_state.get("sim_duration", 0)
            
            if sim_duration <= 0:
                return
            
            n_pts = int(sim_duration / dt) + 1
            
            # Limiter pour la prévisualisation
            if n_pts > MAX_PREVIEW_POINTS:
                times_preview = np.linspace(0, sim_duration, MAX_PREVIEW_POINTS)
            else:
                times_preview = np.linspace(0, sim_duration, n_pts)
            
            data_raw = self.app_state.get("data_raw", {})
            
            for key, df in data_raw.items():
                method_display = self.method_vars[key].get()
                
                method = _METHOD_DISPLAY_TO_KEY.get(method_display, "pchip")
                
                smooth = self.smooth_vars[key].get()
                zones = self.app_state["params"]["unfiltered_zones"].get(key, [])
                
                try:
                    interp = interpolate(
                        df,
                        times_preview,
                        method=method,
                        smooth_factor=smooth,
                        unfiltered_zones=zones,
                        savgol_window=self.app_state["params"].get("savgol_window", DEFAULT_SAVGOL_WINDOW),
                        savgol_polyorder=self.app_state["params"].get("savgol_polyorder", DEFAULT_SAVGOL_POLYORDER),
                        transition_ratio=self.app_state["params"].get("transition_ratio", DEFAULT_TRANSITION_RATIO)
                    )
                    
                    # Tracer
                    fig = self.preview_figs[key]
                    fig.clear()
                    ax = fig.add_subplot(111)
                    
                    # Lignes linéaires (référence) en noir
                    ax.plot(df["Time_s"], df["Value"], "-", color="black",
                           label="Linéaire", linewidth=0.8, alpha=0.3, zorder=1)
                    
                    # Points bruts (plus fins)
                    ax.plot(df["Time_s"], df["Value"], "o", label="Brut",
                           markersize=3, alpha=0.8, zorder=3, color="C0")
                    
                    # Courbe interpolée (plus épaisse)
                    label = INTERP_METHODS[method]
                    if method == "spline":
                        label += f" (s={smooth:.4f})"
                    ax.plot(times_preview, interp, "-", label=label,
                           linewidth=2.5, zorder=2, color="C1")
                    
                    # Calculer l'erreur d'interpolation
                    error = compute_interpolation_error(df, times_preview, interp)
                    error_text = format_error_text(error)
                    
                    ax.set_xlabel("Temps (s)")
                    ax.set_ylabel("Valeur")
                    
                    # Titre avec nom personnalisé
                    inlet_names = self.app_state.get("inlet_names", {"inlet1": "inlet1", "inlet2": "inlet2"})
                    inlet_num = "1" if "inlet1" in key else "2"
                    var_type = "Q" if key.startswith("Q_") else "T"
                    custom_name = inlet_names.get(f"inlet{inlet_num}", f"inlet{inlet_num}")
                    title = f"{var_type}_{custom_name} - {error_text}"
                    ax.set_title(title)
                    ax.legend()
                    ax.grid(True, alpha=0.3)
                    
                    fig.tight_layout()
                    self.preview_canvases[key].draw()
                
                except Exception as e:
                    print(f"Erreur interpolation {key}: {e}")
        
        except Exception as e:
            print(f"Erreur prévisualisation: {e}")
    
    def validate(self) -> tuple[bool, str]:
        """Valide les paramètres."""
        try:
            if self.dt_us.get() <= 0:
                return False, "Le pas de temps doit être > 0"
            if self.flow_eps.get() <= 0:
                return False, "FLOW_EPS doit être > 0"
            
            # Sauvegarder
            self.app_state["params"]["dt_us"] = self.dt_us.get()
            self.app_state["params"]["flow_eps"] = self.flow_eps.get()
            
            return True, ""
        except Exception as e:
            return False, f"Erreur : {e}"
