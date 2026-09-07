"""
Application principale avec workflow guidé et navigation flexible
"""

import tkinter as tk
from tkinter import ttk, messagebox

from core.io import extract_inlet_data, get_max_simulation_time
from core.interpolation import generate_time_array, interpolate_all_data
from core.config import ConfigManager
from core.i18n import (
    t, set_language, get_language, available_languages,
    language_display, language_code,
)
from gui.steps import Step1Files, Step2Parameters, Step3Preview, Step4Export


class FluentProfGenerator(tk.Tk):
    """Application principale de génération de profils Fluent."""

    STEPS = [
        {
            "title": "Import du fichier CSV",
            "subtitle": "Importez un fichier CSV multi-colonnes et configurez le mapping des inlets",
            "class": Step1Files,
        },
        {
            "title": "Paramètres d'interpolation",
            "subtitle": "Ajustez les paramètres et observez l'effet sur les courbes",
            "class": Step2Parameters,
        },
        {
            "title": "Prévisualisation finale",
            "subtitle": "Vérifiez les courbes interpolées avant l'export",
            "class": Step3Preview,
        },
        {
            "title": "Export du fichier .prof",
            "subtitle": "Enregistrez le profil Fluent",
            "class": Step4Export,
        },
    ]

    def __init__(self):
        super().__init__()

        # Gestionnaire de configuration
        self.config_manager = ConfigManager()

        # La langue doit être fixée avant toute construction de l'interface
        set_language(self.config_manager.get_language() or get_language())

        self.title(t("Générateur de profils Fluent (.prof)"))
        self.geometry("1200x800")
        self.minsize(1000, 700)

        # État global partagé entre toutes les étapes
        self.app_state = {
            "csv_file": None,
            "csv_df": None,
            "time_col": None,
            "column_mapping": None,
            "file_keys": [],
            "inlet_names": {},
            "data_raw": {},
            "data_interp": {},
            "times": None,
            "sim_duration": 0,
            "params": {},
        }

        # Restaurer le dernier fichier CSV et mapping depuis la config
        last_csv = self.config_manager.get_last_csv_file()
        if last_csv:
            import os
            if os.path.exists(last_csv):
                self.app_state["csv_file"] = last_csv

        # ConfigManager garantit la structure ou retourne un dict vide :
        # une configuration inutilisable n'empeche pas le demarrage.
        last_mapping = self.config_manager.get_last_column_mapping()
        inlets = last_mapping.get("inlets", [])
        if inlets:
            self.app_state["time_col"] = last_mapping.get("time_col", "")
            self.app_state["column_mapping"] = [
                (inlet["q_col"], inlet["t_col"], idx + 1)
                for idx, inlet in enumerate(inlets)
            ]
            self.app_state["inlet_names"] = {
                idx + 1: inlet["name"]
                for idx, inlet in enumerate(inlets)
            }

        # Charger les derniers noms d'inlets (override si présents)
        last_inlet_names = self.config_manager.get_last_inlet_names()
        if last_inlet_names:
            self.app_state["inlet_names"] = last_inlet_names

        self.current_step = 0
        # Indexé par numéro d'étape : la reconstruction après changement de
        # langue ne recrée que l'étape affichée, sans décaler les autres
        self.step_widgets = {}

        self._build_ui()
        self._show_step(0)

    def _build_ui(self):
        """Construction de l'interface principale."""
        main = ttk.Frame(self, padding=10)
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=1)
        main.rowconfigure(1, weight=1)

        # En-tête
        header = ttk.Frame(main)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header.columnconfigure(0, weight=1)

        titles = ttk.Frame(header)
        titles.grid(row=0, column=0, sticky="w")

        self.lbl_title = ttk.Label(titles, text="", font=("Segoe UI", 16, "bold"))
        self.lbl_title.pack(anchor="w")

        self.lbl_subtitle = ttk.Label(titles, text="", font=("Segoe UI", 10))
        self.lbl_subtitle.pack(anchor="w", pady=(4, 0))

        # Sélecteur de langue, accessible depuis toutes les étapes
        lang_frame = ttk.Frame(header)
        lang_frame.grid(row=0, column=1, sticky="ne")

        self.lbl_language = ttk.Label(lang_frame, text=t("Langue :"))
        self.lbl_language.pack(side="left", padx=(0, 5))

        self.language_var = tk.StringVar(value=language_display(get_language()))
        self.combo_language = ttk.Combobox(
            lang_frame,
            textvariable=self.language_var,
            values=list(available_languages().values()),
            state="readonly",
            width=10,
        )
        self.combo_language.pack(side="left")
        self.combo_language.bind("<<ComboboxSelected>>", self._on_language_change)

        # Zone de contenu
        self.content_frame = ttk.Frame(main)
        self.content_frame.grid(row=1, column=0, sticky="nsew")
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.rowconfigure(0, weight=1)

        # Navigation
        nav = ttk.Frame(main)
        nav.grid(row=2, column=0, sticky="ew", pady=(10, 0))

        self.btn_prev = ttk.Button(nav, text=t("← Précédent"), command=self._prev_step)
        self.btn_prev.pack(side="left", padx=(0, 5))

        self.btn_next = ttk.Button(nav, text=t("Suivant →"), command=self._next_step)
        self.btn_next.pack(side="left", padx=5)

        self.lbl_step_indicator = ttk.Label(nav, text="", font=("Segoe UI", 9))
        self.lbl_step_indicator.pack(side="right")

        self.btn_quit = ttk.Button(nav, text=t("Quitter"), command=self._confirm_quit)
        self.btn_quit.pack(side="right", padx=(5, 0))

    def _show_step(self, step_num):
        """Affiche l'étape spécifiée."""
        self.current_step = step_num
        step_info = self.STEPS[step_num]

        # Mise à jour des titres
        self.lbl_title.config(text=t(
            "Étape {n} : {title}", n=step_num + 1, title=t(step_info["title"])
        ))
        self.lbl_subtitle.config(text=t(step_info["subtitle"]))

        # Nettoyage du contenu
        for widget in self.content_frame.winfo_children():
            widget.pack_forget()

        # Créer ou réutiliser le widget de l'étape
        step_widget = self.step_widgets.get(step_num)
        if step_widget is None:
            step_widget = step_info['class'](self.content_frame, self.app_state)
            self.step_widgets[step_num] = step_widget

        # Afficher le widget
        step_widget.pack(fill="both", expand=True, padx=10, pady=10)

        # Rafraîchir si nécessaire (pour la prévisualisation)
        if hasattr(step_widget, "refresh"):
            step_widget.refresh()

        # Mise à jour des boutons
        self.btn_prev.config(state="normal" if step_num > 0 else "disabled")

        if step_num == len(self.STEPS) - 1:
            self.btn_next.config(text=t("Terminer"), command=self.destroy)
        else:
            self.btn_next.config(text=t("Suivant →"), command=self._next_step)

        # Indicateur
        self.lbl_step_indicator.config(text=t(
            "Étape {n} / {total}", n=step_num + 1, total=len(self.STEPS)
        ))

    def _invalidate_steps_from(self, step_num):
        """Détruit et supprime les widgets des étapes >= step_num."""
        for num in sorted(self.step_widgets):
            if num >= step_num:
                self.step_widgets.pop(num).destroy()

    def _on_language_change(self, event=None):
        """Applique la langue choisie et reconstruit l'interface."""
        code = language_code(self.language_var.get())
        if code == get_language():
            return

        # Conserver les saisies en cours avant de détruire les widgets
        for widget in self.step_widgets.values():
            if hasattr(widget, "snapshot"):
                try:
                    widget.snapshot()
                except Exception as exc:
                    print(f"Snapshot impossible avant changement de langue : {exc}")

        set_language(code)
        self.config_manager.save_language(code)

        current = self.current_step
        self._invalidate_steps_from(0)

        self.title(t("Générateur de profils Fluent (.prof)"))
        self.lbl_language.config(text=t("Langue :"))
        self.btn_prev.config(text=t("← Précédent"))
        self.btn_quit.config(text=t("Quitter"))
        self._show_step(current)

    def _next_step(self):
        """Passe à l'étape suivante après validation."""
        # Vérifier que le widget de l'étape actuelle existe
        current_widget = self.step_widgets.get(self.current_step)
        if current_widget is not None:
            # Validation de l'étape actuelle
            is_valid, error_msg = current_widget.validate()
            if not is_valid:
                messagebox.showwarning(t("Validation"), error_msg, parent=self)
                return

        # Actions spécifiques selon l'étape
        if self.current_step == 0:
            # Après sélection du CSV : extraire les données par inlet
            try:
                self._load_data()
                # Sauvegarder dans la config
                self.config_manager.save_last_csv_file(self.app_state.get("csv_file", ""))
                if self.app_state.get("inlet_names"):
                    self.config_manager.save_last_inlet_names(self.app_state["inlet_names"])
                # Sauvegarder le mapping
                mapping = self.app_state.get("column_mapping", [])
                inlet_names = self.app_state.get("inlet_names", {})
                if mapping:
                    mapping_data = {
                        "time_col": self.app_state.get("time_col", ""),
                        "inlets": [
                            {"q_col": q, "t_col": t, "name": inlet_names.get(idx, f"inlet{idx}")}
                            for q, t, idx in mapping
                        ],
                    }
                    self.config_manager.save_last_column_mapping(mapping_data)
            except Exception as e:
                messagebox.showerror(
                    t("Erreur"),
                    t("Erreur lors du chargement :\n\n{error}", error=e),
                    parent=self,
                )
                return

            # Le nombre d'inlets a pu changer : détruire les steps 1+ et recréer
            self._invalidate_steps_from(1)

        elif self.current_step == 1:
            # Après paramétrage : générer les données interpolées
            try:
                self._generate_interpolated_data()
                # Sauvegarder les paramètres step2
                self.config_manager.save_last_step2_params(self.app_state["params"])
            except Exception as e:
                messagebox.showerror(
                    t("Erreur"),
                    t("Erreur lors de l'interpolation :\n\n{error}", error=e),
                    parent=self,
                )
                return

        # Passer à l'étape suivante
        if self.current_step < len(self.STEPS) - 1:
            self._show_step(self.current_step + 1)

    def _prev_step(self):
        """Retourne à l'étape précédente."""
        if self.current_step > 0:
            self._show_step(self.current_step - 1)

    def _load_data(self):
        """Extrait les données par inlet depuis le CSV multi-colonnes."""
        csv_df = self.app_state.get("csv_df")
        time_col = self.app_state.get("time_col")
        column_mapping = self.app_state.get("column_mapping")

        if csv_df is None or time_col is None or not column_mapping:
            raise ValueError("Données CSV ou mapping non disponibles.")

        data_raw = extract_inlet_data(csv_df, time_col, column_mapping)
        self.app_state["data_raw"] = data_raw
        self.app_state["sim_duration"] = get_max_simulation_time(data_raw)

    def _generate_interpolated_data(self):
        """Génère les données interpolées avec les paramètres actuels."""
        params = self.app_state["params"]

        dt = params["dt_us"] * 1e-6  # Conversion µs → s
        times = generate_time_array(self.app_state["sim_duration"], dt)

        # Construire le dictionnaire de renommage inlet_names
        # Format attendu par interpolate_all_data : {"inlet1": "custom_name", ...}
        inlet_names_map = {}
        for idx, name in self.app_state.get("inlet_names", {}).items():
            inlet_names_map[f"inlet{idx}"] = name

        data_interp = interpolate_all_data(
            self.app_state["data_raw"],
            times,
            params.get("methods", {}),
            params.get("smooth_params", {}),
            params["flow_eps"],
            params.get("unfiltered_zones", {}),
            inlet_names_map,
            params.get("trend_lambda", {}),
            params.get("inverted", {}),
        )

        self.app_state["times"] = times
        self.app_state["data_interp"] = data_interp

    def _confirm_quit(self):
        """Confirme la fermeture de l'application."""
        if messagebox.askyesno(
            t("Quitter"), t("Voulez-vous vraiment quitter ?"), parent=self
        ):
            self.destroy()


def run():
    """Lance l'application."""
    app = FluentProfGenerator()
    app.mainloop()
