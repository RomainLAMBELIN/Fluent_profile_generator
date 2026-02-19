"""
Étape 2 : Paramétrage de l'interpolation avec configuration par courbe
"""

import re
import tkinter as tk
from tkinter import ttk, scrolledtext
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from core.constants import (
    DEFAULT_DT_US, DEFAULT_FLOW_EPS, DEFAULT_SMOOTH_Q, DEFAULT_SMOOTH_T,
    SMOOTH_MIN, SMOOTH_MAX, MAX_PREVIEW_POINTS,
    INTERP_METHODS, DEFAULT_INTERP_METHOD, INTERP_METHODS_HELP,
    DEFAULT_TREND_LAMBDA, TREND_LAMBDA_MIN, TREND_LAMBDA_MAX,
    generate_file_labels,
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

        # Clés dynamiques depuis app_state
        self.file_keys = list(app_state.get("file_keys", []))
        self.inlet_names = dict(app_state.get("inlet_names", {}))

        # Initialiser les paramètres
        self._init_params()

        # Variables Tkinter
        self.dt_us = tk.DoubleVar(value=self.app_state["params"]["dt_us"])
        self.flow_eps = tk.DoubleVar(value=self.app_state["params"]["flow_eps"])

        self.method_vars = {}
        self.smooth_vars = {}
        self.smooth_labels = {}
        self.smooth_scales = {}
        self.smooth_entries = {}
        self.lambda_vars = {}
        self.lambda_labels = {}
        self.lambda_scales = {}
        self.lambda_entries = {}
        self.lambda_frames = {}
        self.zones_labels = {}
        self.invert_vars = {}

        for key in self.file_keys:
            method_key = self.app_state["params"]["methods"][key]
            method_display = INTERP_METHODS.get(method_key, INTERP_METHODS[DEFAULT_INTERP_METHOD])
            self.method_vars[key] = tk.StringVar(value=method_display)
            self.smooth_vars[key] = tk.DoubleVar(value=self.app_state["params"]["smooth_params"][key])
            self.lambda_vars[key] = tk.DoubleVar(value=self.app_state["params"]["trend_lambda"][key])
            self.invert_vars[key] = tk.BooleanVar(value=self.app_state["params"]["inverted"].get(key, False))

        self._build_ui()
        self._update_zones_labels()
        self._update_preview()

    def _init_params(self):
        """Initialise les paramètres dans l'état."""
        if "params" not in self.app_state:
            self.app_state["params"] = {}

        params = self.app_state["params"]

        # Charger les derniers paramètres sauvegardés
        config_mgr = ConfigManager()
        last_params = config_mgr.get_last_step2_params()

        if "dt_us" not in params:
            params["dt_us"] = last_params.get("dt_us", DEFAULT_DT_US)
        if "flow_eps" not in params:
            params["flow_eps"] = last_params.get("flow_eps", DEFAULT_FLOW_EPS)

        # Méthodes par courbe
        if "methods" not in params:
            params["methods"] = {}
        saved_methods = last_params.get("methods", {})
        for key in self.file_keys:
            if key not in params["methods"]:
                params["methods"][key] = saved_methods.get(key, DEFAULT_INTERP_METHOD)

        # Lissage par courbe
        if "smooth_params" not in params:
            params["smooth_params"] = {}
        saved_smooth = last_params.get("smooth_params", {})
        for key in self.file_keys:
            if key not in params["smooth_params"]:
                if key in saved_smooth:
                    params["smooth_params"][key] = saved_smooth[key]
                else:
                    default = DEFAULT_SMOOTH_Q if key.startswith("Q_") else DEFAULT_SMOOTH_T
                    params["smooth_params"][key] = default

        # Zones par courbe
        if "unfiltered_zones" not in params:
            params["unfiltered_zones"] = {}
        for key in self.file_keys:
            if key not in params["unfiltered_zones"]:
                params["unfiltered_zones"][key] = []

        # Paramètre lambda pour Trend Filtering (par courbe)
        if "trend_lambda" not in params:
            params["trend_lambda"] = {}
        saved_lambda = last_params.get("trend_lambda", {})
        for key in self.file_keys:
            if key not in params["trend_lambda"]:
                if key in saved_lambda:
                    params["trend_lambda"][key] = saved_lambda[key]
                else:
                    params["trend_lambda"][key] = DEFAULT_TREND_LAMBDA

        # Inversion des courbes (par courbe)
        if "inverted" not in params:
            params["inverted"] = {}
        saved_inverted = last_params.get("inverted", {})
        for key in self.file_keys:
            if key not in params["inverted"]:
                params["inverted"][key] = saved_inverted.get(key, False)

    def _build_ui(self):
        """Construction de l'interface."""
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(1, weight=1)

        # Bandeau d'informations
        info_frame = ttk.Frame(self, padding=5)
        info_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        self.lbl_info = ttk.Label(
            info_frame, text="Chargement...", font=("Segoe UI", 9), foreground="blue"
        )
        self.lbl_info.pack(anchor="w")
        self._update_info_label()

        # Panneau gauche : Paramètres
        left_frame = ttk.Frame(self)
        left_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 10))

        scroll_canvas = tk.Canvas(left_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=scroll_canvas.yview)
        scrollable_frame = ttk.Frame(scroll_canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all")),
        )

        scroll_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        scroll_canvas.configure(yscrollcommand=scrollbar.set)

        scroll_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            scroll_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        scroll_canvas.bind("<MouseWheel>", _on_mousewheel)
        scrollable_frame.bind("<MouseWheel>", _on_mousewheel)

        # Paramètres globaux
        global_params = ttk.LabelFrame(scrollable_frame, text="Paramètres globaux", padding=10)
        global_params.pack(fill="x", padx=10, pady=10)

        # Pas de temps
        row = ttk.Frame(global_params)
        row.pack(fill="x", pady=5)
        ttk.Label(row, text="Pas de temps (µs) :").pack(side="left")
        ttk.Spinbox(row, from_=0.01, to=1000, textvariable=self.dt_us, width=10).pack(
            side="left", padx=10
        )

        # Flow eps
        row = ttk.Frame(global_params)
        row.pack(fill="x", pady=5)
        ttk.Label(row, text="Remplacement débits nuls :").pack(side="left")
        ttk.Entry(row, textvariable=self.flow_eps, width=10).pack(side="left", padx=10)

        # Bouton Aide
        ttk.Button(
            row, text="? Aide", command=self._show_help_dialog, width=8
        ).pack(side="right", padx=10)

        # Configuration par courbe
        curve_labels = generate_file_labels(self.inlet_names)

        for key in self.file_keys:
            label = curve_labels.get(key, key)
            self._build_curve_config(scrollable_frame, key, label)

        # Bouton rafraîchir
        ttk.Button(
            scrollable_frame, text="Rafraîchir prévisualisations", command=self._update_preview
        ).pack(fill="x", padx=10, pady=10)

        # Panneau droit : Prévisualisations
        right = ttk.Frame(self)
        right.grid(row=1, column=1, sticky="nsew")

        self.preview_notebook = ttk.Notebook(right)
        self.preview_notebook.pack(fill="both", expand=True)

        for key in self.file_keys:
            tab = ttk.Frame(self.preview_notebook)
            tab_label = curve_labels.get(key, key)
            self.preview_notebook.add(tab, text=tab_label)

            plot_frame = ttk.Frame(tab)
            plot_frame.pack(fill="both", expand=True)

            fig = Figure(figsize=(6, 4), dpi=100)
            canvas = FigureCanvasTkAgg(fig, plot_frame)
            canvas.get_tk_widget().pack(fill="both", expand=True)

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
            width=30,
        )
        combo.pack(side="left", padx=5)
        combo.bind("<<ComboboxSelected>>", lambda e, k=key: self._on_method_change(k))

        # Lissage (pour spline)
        smooth_row = ttk.Frame(frame)
        smooth_row.pack(fill="x", pady=2)
        ttk.Label(smooth_row, text="Lissage :", width=12).pack(side="left")

        smooth_entry = ttk.Entry(smooth_row, width=10)
        smooth_entry.insert(0, f"{self.smooth_vars[key].get():.4f}")
        smooth_entry.pack(side="left", padx=5)
        self.smooth_entries[key] = smooth_entry

        def on_smooth_entry_change(event, k=key, entry=smooth_entry):
            try:
                value = float(entry.get())
                value = max(SMOOTH_MIN, min(SMOOTH_MAX, value))
                self.smooth_vars[k].set(value)
                entry.delete(0, "end")
                entry.insert(0, f"{value:.4f}")
                self._on_smooth_change(k)
            except ValueError:
                pass

        smooth_entry.bind("<Return>", on_smooth_entry_change)
        smooth_entry.bind("<FocusOut>", on_smooth_entry_change)

        scale = ttk.Scale(
            smooth_row,
            from_=SMOOTH_MIN,
            to=SMOOTH_MAX,
            orient="horizontal",
            variable=self.smooth_vars[key],
            command=lambda v, k=key, entry=smooth_entry: self._on_smooth_slider_change(k, entry),
        )
        scale.pack(side="left", fill="x", expand=True, padx=5)
        self.smooth_scales[key] = scale

        lbl = ttk.Label(smooth_row, text=f"{self.smooth_vars[key].get():.4f}", width=8)
        lbl.pack(side="left")
        self.smooth_labels[key] = lbl

        # Lambda (pour Trend Filter)
        lambda_row = ttk.Frame(frame)
        lambda_row.pack(fill="x", pady=2)
        self.lambda_frames[key] = lambda_row

        ttk.Label(lambda_row, text="Lambda :", width=12).pack(side="left")

        lambda_entry = ttk.Entry(lambda_row, width=10)
        lambda_entry.insert(0, f"{self.lambda_vars[key].get():.2f}")
        lambda_entry.pack(side="left", padx=5)
        self.lambda_entries[key] = lambda_entry

        def on_lambda_entry_change(event, k=key, entry=lambda_entry):
            try:
                value = float(entry.get())
                value = max(TREND_LAMBDA_MIN, min(TREND_LAMBDA_MAX, value))
                self.lambda_vars[k].set(value)
                entry.delete(0, "end")
                entry.insert(0, f"{value:.2f}")
                self._on_lambda_change(k)
            except ValueError:
                pass

        lambda_entry.bind("<Return>", on_lambda_entry_change)
        lambda_entry.bind("<FocusOut>", on_lambda_entry_change)

        lambda_scale = ttk.Scale(
            lambda_row,
            from_=TREND_LAMBDA_MIN,
            to=TREND_LAMBDA_MAX,
            orient="horizontal",
            variable=self.lambda_vars[key],
            command=lambda v, k=key, entry=lambda_entry: self._on_lambda_slider_change(k, entry),
        )
        lambda_scale.pack(side="left", fill="x", expand=True, padx=5)
        self.lambda_scales[key] = lambda_scale

        lambda_lbl = ttk.Label(lambda_row, text=f"{self.lambda_vars[key].get():.2f}", width=8)
        lambda_lbl.pack(side="left")
        self.lambda_labels[key] = lambda_lbl

        # Afficher/cacher selon la méthode initiale
        self._update_param_visibility(key)

        # Inversion
        invert_row = ttk.Frame(frame)
        invert_row.pack(fill="x", pady=2)
        ttk.Checkbutton(
            invert_row, text="Inverser la courbe (×-1)",
            variable=self.invert_vars[key],
            command=lambda k=key: self._on_invert_change(k),
        ).pack(side="left")

        # Zones
        row = ttk.Frame(frame)
        row.pack(fill="x", pady=2)
        ttk.Button(
            row, text="Zones", command=lambda k=key: self._configure_zones(k), width=12
        ).pack(side="left")

        zones_lbl = ttk.Label(row, text="0 zone", font=("Segoe UI", 8), foreground="gray")
        zones_lbl.pack(side="left", padx=10)
        self.zones_labels[key] = zones_lbl

    def _on_method_change(self, key):
        """Callback quand la méthode change pour une courbe."""
        method_display = self.method_vars[key].get()
        method_key = _METHOD_DISPLAY_TO_KEY.get(method_display, DEFAULT_INTERP_METHOD)

        self.app_state["params"]["methods"][key] = method_key
        self._update_param_visibility(key)
        self._update_preview()

    def _update_param_visibility(self, key):
        """Met à jour la visibilité des paramètres selon la méthode."""
        method_display = self.method_vars[key].get()
        method_key = _METHOD_DISPLAY_TO_KEY.get(method_display, "pchip")

        is_spline = method_key == "spline"
        is_trend = method_key in ["trend_l2", "trend_l1"]

        # Lissage : actif uniquement pour spline
        if is_spline:
            self.smooth_scales[key].config(state="normal")
            if key in self.smooth_entries:
                self.smooth_entries[key].config(state="normal")
        else:
            self.smooth_scales[key].config(state="disabled")
            if key in self.smooth_entries:
                self.smooth_entries[key].config(state="disabled")

        # Lambda : actif uniquement pour trend filter
        if key in self.lambda_frames:
            if is_trend:
                self.lambda_scales[key].config(state="normal")
                if key in self.lambda_entries:
                    self.lambda_entries[key].config(state="normal")
            else:
                self.lambda_scales[key].config(state="disabled")
                if key in self.lambda_entries:
                    self.lambda_entries[key].config(state="disabled")

    def _on_smooth_change(self, key):
        """Callback quand le lissage change."""
        value = self.smooth_vars[key].get()
        self.smooth_labels[key].config(text=f"{value:.4f}")
        self.app_state["params"]["smooth_params"][key] = value
        self._update_info_label()
        self._update_preview()

    def _on_smooth_slider_change(self, key, entry):
        """Callback quand le slider de lissage change."""
        value = self.smooth_vars[key].get()
        entry.delete(0, "end")
        entry.insert(0, f"{value:.4f}")
        self._on_smooth_change(key)

    def _on_lambda_change(self, key):
        """Callback quand le paramètre lambda change."""
        value = self.lambda_vars[key].get()
        self.lambda_labels[key].config(text=f"{value:.2f}")
        self.app_state["params"]["trend_lambda"][key] = value
        self._update_preview()

    def _on_lambda_slider_change(self, key, entry):
        """Callback quand le slider de lambda change."""
        value = self.lambda_vars[key].get()
        entry.delete(0, "end")
        entry.insert(0, f"{value:.2f}")
        self._on_lambda_change(key)

    def _on_invert_change(self, key):
        """Callback quand l'inversion change pour une courbe."""
        self.app_state["params"]["inverted"][key] = self.invert_vars[key].get()
        self._update_preview()

    def _show_help_dialog(self):
        """Affiche la fenêtre d'aide sur les méthodes d'interpolation."""
        help_window = tk.Toplevel(self)
        help_window.title("Aide - Méthodes d'interpolation")
        help_window.geometry("700x600")
        help_window.transient(self.winfo_toplevel())

        main_frame = ttk.Frame(help_window, padding=10)
        main_frame.pack(fill="both", expand=True)

        title_label = ttk.Label(
            main_frame,
            text="Guide des méthodes d'interpolation",
            font=("Helvetica", 14, "bold"),
        )
        title_label.pack(pady=(0, 10))

        text_widget = scrolledtext.ScrolledText(
            main_frame, wrap=tk.WORD, width=80, height=30, font=("Consolas", 10)
        )
        text_widget.pack(fill="both", expand=True, pady=5)

        help_content = "MÉTHODES D'INTERPOLATION\n" + "=" * 60 + "\n\n"
        for method_key, method_name in INTERP_METHODS.items():
            help_content += f"--- {method_name} ---\n"
            help_content += INTERP_METHODS_HELP.get(method_key, "") + "\n\n"

        help_content += "\n" + "=" * 60 + "\n"
        help_content += "ZONES SPECIALES\n" + "=" * 60 + "\n\n"
        help_content += """Les zones spéciales permettent de définir des régions où l'interpolation
est différente du reste de la courbe.

Zone "Exacte" (PCHIP)
   Utilise PCHIP dans cette zone, passant exactement par les points.
   Utile pour préserver des variations importantes.

Zone "Linéaire"
   Trace une droite entre le premier et dernier point de la zone.
   Ignore les points intermédiaires.
   Utile pour simplifier une région ou créer une rampe.

"""
        help_content += "=" * 60 + "\n"
        help_content += "RECOMMANDATIONS CFD\n" + "=" * 60 + "\n\n"
        help_content += """Pour les simulations CFD (Ansys Fluent), les variations brusques
aux conditions aux limites peuvent causer des divergences.

Recommandations :
1. Commencer avec Trend Filter L2, lambda = 1 a 5
2. Si divergence, augmenter lambda (10, 20, 50...)
3. Pour données très bruitées : Trend Filter L1
4. Vérifier visuellement que les transitions sont douces
"""

        text_widget.insert("1.0", help_content)
        text_widget.config(state="disabled")

        ttk.Button(main_frame, text="Fermer", command=help_window.destroy).pack(pady=10)

    def _configure_zones(self, key):
        """Configure les zones non-filtrées pour une courbe."""
        sim_duration = self.app_state.get("sim_duration", 1.0)
        zones = self.app_state["params"]["unfiltered_zones"].get(key, [])

        m = re.search(r"inlet(\d+)", key)
        inlet_num = int(m.group(1)) if m else 1
        var_type = "Débit" if key.startswith("Q_") else "Température"
        custom_name = self.inlet_names.get(inlet_num, f"Inlet {inlet_num}")

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
            current_smooth=smooth,
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
                zones = self.app_state["params"]["unfiltered_zones"]
                total_zones = sum(len(z) for z in zones.values())

                info_text = f"Durée simulation : {sim_duration:.6f} s  |  "
                info_text += f"Pas de temps : {dt:.3e} s ({self.dt_us.get():.2f} µs)  |  "
                info_text += f"Points interpolés : {n_pts:,}  |  "
                info_text += f"Zones définies : {total_zones}"

                self.lbl_info.config(text=info_text)
            else:
                self.lbl_info.config(text="Chargement des paramètres...")
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

            if n_pts > MAX_PREVIEW_POINTS:
                times_preview = np.linspace(0, sim_duration, MAX_PREVIEW_POINTS)
            else:
                times_preview = np.linspace(0, sim_duration, n_pts)

            data_raw = self.app_state.get("data_raw", {})

            for key in self.file_keys:
                if key not in data_raw:
                    continue
                df = data_raw[key]
                method_display = self.method_vars[key].get()
                method = _METHOD_DISPLAY_TO_KEY.get(method_display, "pchip")

                smooth = self.smooth_vars[key].get()
                trend_lambda = self.lambda_vars[key].get()
                zones = self.app_state["params"]["unfiltered_zones"].get(key, [])

                try:
                    interp = interpolate(
                        df,
                        times_preview,
                        method=method,
                        smooth_factor=smooth,
                        unfiltered_zones=zones,
                        trend_lambda=trend_lambda,
                    )

                    # Appliquer l'inversion si activée
                    is_inverted = self.invert_vars.get(key, tk.BooleanVar(value=False)).get()
                    invert_coeff = -1.0 if is_inverted else 1.0

                    fig = self.preview_figs[key]
                    fig.clear()
                    ax = fig.add_subplot(111)

                    raw_values = df["Value"].values * invert_coeff
                    ax.plot(
                        df["Time_s"], raw_values, "-", color="black",
                        label="Linéaire", linewidth=0.8, alpha=0.3, zorder=1,
                    )
                    ax.plot(
                        df["Time_s"], raw_values, "o", label="Brut",
                        markersize=3, alpha=0.8, zorder=3, color="C0",
                    )

                    label = INTERP_METHODS[method]
                    if method == "spline":
                        label += f" (s={smooth:.4f})"
                    elif method in ["trend_l2", "trend_l1"]:
                        label += f" (λ={trend_lambda:.2f})"
                    ax.plot(
                        times_preview, interp * invert_coeff, "-", label=label,
                        linewidth=2.5, zorder=2, color="C1",
                    )

                    error = compute_interpolation_error(df, times_preview, interp)
                    error_text = format_error_text(error)

                    ax.set_xlabel("Temps (s)")
                    ax.set_ylabel("Valeur")

                    m = re.search(r"inlet(\d+)", key)
                    inlet_num = int(m.group(1)) if m else 1
                    var_type = "Q" if key.startswith("Q_") else "T"
                    custom_name = self.inlet_names.get(inlet_num, f"inlet{inlet_num}")
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

    def validate(self) -> tuple:
        """Valide les paramètres."""
        try:
            if self.dt_us.get() <= 0:
                return False, "Le pas de temps doit être > 0"
            if self.flow_eps.get() <= 0:
                return False, "FLOW_EPS doit être > 0"

            self.app_state["params"]["dt_us"] = self.dt_us.get()
            self.app_state["params"]["flow_eps"] = self.flow_eps.get()

            return True, ""
        except Exception as e:
            return False, f"Erreur : {e}"
