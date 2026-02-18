"""
Étape 3 : Prévisualisation finale de toutes les courbes (grille dynamique)
"""

import re
import math
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from core.constants import INTERP_METHODS


class Step3Preview(ttk.Frame):
    """Prévisualisation finale avant export avec grille dynamique N inlets."""

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
        file_keys = self.app_state.get("file_keys", [])
        inlet_names = self.app_state.get("inlet_names", {})

        if times is None or not data_interp:
            self.lbl_info.config(text="Aucune donnée interpolée disponible")
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

        # Déterminer le layout de la grille
        # Séparer les clés Q et T
        q_keys = [k for k in file_keys if k.startswith("Q_")]
        t_keys = [k for k in file_keys if k.startswith("T_")]
        n_inlets = max(len(q_keys), len(t_keys))

        if n_inlets == 0:
            return

        # Grille : 2 lignes (Q en haut, T en bas) x N colonnes (1 par inlet)
        n_rows = 2
        n_cols = n_inlets
        fig_width = max(5 * n_cols, 10)
        fig_height = 8

        fig = Figure(figsize=(fig_width, fig_height), dpi=100)

        # Construire le mapping de renommage pour retrouver les clés dans data_interp
        inlet_names_map = {}
        for idx, name in inlet_names.items():
            inlet_names_map[f"inlet{idx}"] = name

        all_keys_ordered = []
        for i in range(n_inlets):
            if i < len(q_keys):
                all_keys_ordered.append(q_keys[i])
            if i < len(t_keys):
                all_keys_ordered.append(t_keys[i])

        for col_idx in range(n_inlets):
            for row_idx, (prefix, keys_list) in enumerate([("Q_", q_keys), ("T_", t_keys)]):
                if col_idx >= len(keys_list):
                    continue

                key = keys_list[col_idx]
                subplot_idx = row_idx * n_cols + col_idx + 1
                ax = fig.add_subplot(n_rows, n_cols, subplot_idx)

                # Points bruts - linéaire de référence
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
                        zorder=1,
                    )
                    ax.plot(
                        df["Time_s"],
                        df["Value"],
                        "o",
                        label="Brut",
                        markersize=3,
                        alpha=0.8,
                        zorder=3,
                        color="C0",
                    )

                # Données interpolées (clé renommée)
                key_renamed = key
                for old_name, new_name in inlet_names_map.items():
                    key_renamed = key_renamed.replace(old_name, new_name)

                if key_renamed in data_interp:
                    methods = params.get("methods", {})
                    method_key = methods.get(key, "spline")

                    if method_key in INTERP_METHODS:
                        method_label = INTERP_METHODS[method_key]
                    else:
                        method_label = "Interpolé"

                    if method_key == "spline":
                        smooth_params = params.get("smooth_params", {})
                        smooth = smooth_params.get(key, 0.01)
                        method_label += f" (s={smooth:.4f})"
                    elif method_key in ("trend_l2", "trend_l1"):
                        trend_lambda = params.get("trend_lambda", {})
                        lam = trend_lambda.get(key, 1.0)
                        method_label += f" (\u03bb={lam:.2f})"

                    ax.plot(
                        times,
                        data_interp[key_renamed],
                        "-",
                        label=method_label,
                        linewidth=2.5,
                        zorder=2,
                        color="C1",
                    )

                ax.set_xlabel("Temps (s)")
                ax.set_ylabel("Valeur")

                # Titre avec nom personnalisé
                m = re.search(r"inlet(\d+)", key)
                inlet_num = int(m.group(1)) if m else col_idx + 1
                var_type = "Débit" if key.startswith("Q_") else "Température"
                custom_name = inlet_names.get(inlet_num, f"Inlet {inlet_num}")
                ax.set_title(f"{var_type} {custom_name}")
                ax.legend(fontsize=7)
                ax.grid(True, alpha=0.3)

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, self.graph_frame)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        canvas.draw()

    def validate(self) -> tuple:
        """
        Validation (toujours vraie pour la prévisualisation).

        Returns:
            (is_valid, error_message)
        """
        return True, ""
