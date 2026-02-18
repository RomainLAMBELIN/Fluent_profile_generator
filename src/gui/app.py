"""
Application principale avec workflow guidé et navigation flexible
"""

import tkinter as tk
from tkinter import ttk, messagebox

from core.constants import FILE_KEYS
from core.io import load_all_files, get_max_simulation_time
from core.interpolation import generate_time_array, interpolate_all_data
from core.config import ConfigManager
from gui.steps import Step1Files, Step2Parameters, Step3Preview, Step4Export


class FluentProfGenerator(tk.Tk):
    """Application principale de génération de profils Fluent."""
    
    STEPS = [
        {
            "title": "Sélection des fichiers",
            "subtitle": "Sélectionnez les 4 fichiers CSV (2 débits Q, 2 températures T)",
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
        self.title("Générateur de profils Fluent (.prof)")
        self.geometry("1200x800")
        self.minsize(1000, 700)
        
        # Gestionnaire de configuration
        self.config_manager = ConfigManager()
        
        # État global partagé entre toutes les étapes
        self.app_state = {
            "files": {key: None for key in FILE_KEYS},
            "data_raw": {},
            "data_interp": {},
            "times": None,
            "sim_duration": 0,
            "params": {},
        }
        
        # Charger les derniers fichiers utilisés
        last_files = self.config_manager.get_last_files()
        if last_files:
            for key, path in last_files.items():
                if key in self.app_state["files"]:
                    self.app_state["files"][key] = path
        
        # Charger les derniers noms d'inlets
        last_inlet_names = self.config_manager.get_last_inlet_names()
        if last_inlet_names:
            self.app_state["inlet_names"] = last_inlet_names
        
        self.current_step = 0
        self.step_widgets = []
        
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
        
        self.lbl_title = ttk.Label(header, text="", font=("Segoe UI", 16, "bold"))
        self.lbl_title.pack(anchor="w")
        
        self.lbl_subtitle = ttk.Label(header, text="", font=("Segoe UI", 10))
        self.lbl_subtitle.pack(anchor="w", pady=(4, 0))
        
        # Zone de contenu
        self.content_frame = ttk.Frame(main)
        self.content_frame.grid(row=1, column=0, sticky="nsew")
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.rowconfigure(0, weight=1)
        
        # Navigation
        nav = ttk.Frame(main)
        nav.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        
        self.btn_prev = ttk.Button(nav, text="← Précédent", command=self._prev_step)
        self.btn_prev.pack(side="left", padx=(0, 5))
        
        self.btn_next = ttk.Button(nav, text="Suivant →", command=self._next_step)
        self.btn_next.pack(side="left", padx=5)
        
        self.lbl_step_indicator = ttk.Label(nav, text="", font=("Segoe UI", 9))
        self.lbl_step_indicator.pack(side="right")
        
        ttk.Button(nav, text="Quitter", command=self._confirm_quit).pack(side="right", padx=(5, 0))
    
    def _show_step(self, step_num):
        """Affiche l'étape spécifiée."""
        self.current_step = step_num
        step_info = self.STEPS[step_num]
        
        # Mise à jour des titres
        self.lbl_title.config(text=f"Étape {step_num + 1} : {step_info['title']}")
        self.lbl_subtitle.config(text=step_info['subtitle'])
        
        # Nettoyage du contenu
        for widget in self.content_frame.winfo_children():
            widget.pack_forget()
        
        # Créer ou réutiliser le widget de l'étape
        if step_num >= len(self.step_widgets):
            step_widget = step_info['class'](self.content_frame, self.app_state)
            self.step_widgets.append(step_widget)
        else:
            step_widget = self.step_widgets[step_num]
        
        # Afficher le widget
        step_widget.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Rafraîchir si nécessaire (pour la prévisualisation)
        if hasattr(step_widget, "refresh"):
            step_widget.refresh()
        
        # Mise à jour des boutons
        self.btn_prev.config(state="normal" if step_num > 0 else "disabled")
        
        if step_num == len(self.STEPS) - 1:
            self.btn_next.config(text="Terminer", command=self.destroy)
        else:
            self.btn_next.config(text="Suivant →", command=self._next_step)
        
        # Indicateur
        self.lbl_step_indicator.config(text=f"Étape {step_num + 1} / {len(self.STEPS)}")
    
    def _next_step(self):
        """Passe à l'étape suivante après validation."""
        # Vérifier que le widget de l'étape actuelle existe
        if self.current_step < len(self.step_widgets):
            current_widget = self.step_widgets[self.current_step]
            
            # Validation de l'étape actuelle
            is_valid, error_msg = current_widget.validate()
            if not is_valid:
                messagebox.showwarning("Validation", error_msg, parent=self)
                return
        
        # Actions spécifiques selon l'étape
        if self.current_step == 0:
            # Après sélection des fichiers : charger les données
            try:
                self._load_data()
                # Sauvegarder les fichiers et noms d'inlets dans la config
                self.config_manager.save_last_files(self.app_state["files"])
                if "inlet_names" in self.app_state:
                    self.config_manager.save_last_inlet_names(self.app_state["inlet_names"])
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors du chargement:\n\n{e}", parent=self)
                return
        
        elif self.current_step == 1:
            # Après paramétrage : générer les données interpolées
            try:
                self._generate_interpolated_data()
                # Sauvegarder les paramètres step2
                self.config_manager.save_last_step2_params(self.app_state["params"])
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'interpolation:\n\n{e}", parent=self)
                return
        
        # Passer à l'étape suivante
        if self.current_step < len(self.STEPS) - 1:
            self._show_step(self.current_step + 1)
    
    def _prev_step(self):
        """Retourne à l'étape précédente."""
        if self.current_step > 0:
            self._show_step(self.current_step - 1)
    
    def _load_data(self):
        """Charge les données CSV."""
        self.app_state["data_raw"] = load_all_files(self.app_state["files"])
        self.app_state["sim_duration"] = get_max_simulation_time(self.app_state["data_raw"])
    
    def _generate_interpolated_data(self):
        """Génère les données interpolées avec les paramètres actuels."""
        params = self.app_state["params"]
        
        dt = params["dt_us"] * 1e-6  # Conversion µs → s
        times = generate_time_array(self.app_state["sim_duration"], dt)
        
        # Préparer les paramètres Savitzky-Golay
        savgol_params = {
            "window": params.get("savgol_window", 11),
            "polyorder": params.get("savgol_polyorder", 3)
        }
        
        data_interp = interpolate_all_data(
            self.app_state["data_raw"],
            times,
            params.get("methods", {}),
            params.get("smooth_params", {}),
            params["flow_eps"],
            params.get("unfiltered_zones", {}),
            self.app_state.get("inlet_names", {"inlet1": "inlet1", "inlet2": "inlet2"}),
            savgol_params
        )
        
        self.app_state["times"] = times
        self.app_state["data_interp"] = data_interp
    
    def _confirm_quit(self):
        """Confirme la fermeture de l'application."""
        if messagebox.askyesno("Quitter", "Voulez-vous vraiment quitter ?", parent=self):
            self.destroy()


def run():
    """Lance l'application."""
    app = FluentProfGenerator()
    app.mainloop()
