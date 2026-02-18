"""
Gestion de la configuration utilisateur (derniers fichiers, etc.)
"""

import json
import os
from pathlib import Path


class ConfigManager:
    """Gestionnaire de configuration utilisateur."""
    
    def __init__(self):
        # Fichier de configuration dans le répertoire home de l'utilisateur
        self.config_dir = Path.home() / ".fluent_prof_generator"
        self.config_file = self.config_dir / "config.json"
        self.config = self._load_config()
    
    def _load_config(self):
        """Charge la configuration depuis le fichier."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Erreur chargement config: {e}")
                return {}
        return {}
    
    def _save_config(self):
        """Sauvegarde la configuration dans le fichier."""
        try:
            # Créer le répertoire si nécessaire
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur sauvegarde config: {e}")
    
    def get_last_files(self):
        """Récupère les derniers fichiers utilisés."""
        return self.config.get("last_files", {})
    
    def save_last_files(self, files):
        """Sauvegarde les derniers fichiers utilisés."""
        # Ne sauvegarder que si tous les fichiers existent
        existing_files = {}
        for key, path in files.items():
            if path and os.path.exists(path):
                existing_files[key] = path
        
        if existing_files:
            self.config["last_files"] = existing_files
            self._save_config()
    
    def get_last_inlet_names(self):
        """Récupère les derniers noms d'inlets utilisés."""
        return self.config.get("last_inlet_names", {})
    
    def save_last_inlet_names(self, inlet_names):
        """Sauvegarde les derniers noms d'inlets utilisés."""
        if inlet_names:
            self.config["last_inlet_names"] = inlet_names
            self._save_config()
    
    def get_last_step2_params(self):
        """Récupère les derniers paramètres de l'étape 2."""
        return self.config.get("last_step2_params", {})
    
    def save_last_step2_params(self, params):
        """Sauvegarde les derniers paramètres de l'étape 2."""
        if params:
            # Ne sauvegarder que les paramètres sérialisables
            saveable = {
                "dt_us": params.get("dt_us"),
                "flow_eps": params.get("flow_eps"),
                "methods": params.get("methods", {}),
                "smooth_params": params.get("smooth_params", {}),
                "trend_lambda": params.get("trend_lambda", {}),
                # Ne pas sauvegarder les zones (trop spécifiques aux données)
            }
            self.config["last_step2_params"] = saveable
            self._save_config()
    
    def get_last_export_dir(self):
        """Récupère le dernier répertoire d'export utilisé."""
        return self.config.get("last_export_dir", "")
    
    def save_last_export_dir(self, export_dir):
        """Sauvegarde le dernier répertoire d'export utilisé."""
        if export_dir and os.path.exists(export_dir):
            self.config["last_export_dir"] = export_dir
            self._save_config()

    def get_last_csv_file(self):
        """Récupère le dernier fichier CSV multi-colonnes utilisé."""
        return self.config.get("last_csv_file", "")

    def save_last_csv_file(self, csv_file):
        """Sauvegarde le dernier fichier CSV multi-colonnes utilisé."""
        if csv_file and os.path.exists(csv_file):
            self.config["last_csv_file"] = csv_file
            self._save_config()

    def get_last_column_mapping(self):
        """Récupère le dernier mapping de colonnes utilisé."""
        return self.config.get("last_column_mapping", {})

    def save_last_column_mapping(self, mapping_data):
        """
        Sauvegarde le dernier mapping de colonnes utilisé.

        Args:
            mapping_data: Dict avec les clés:
                - time_col: nom de la colonne temps
                - inlets: liste de dicts {q_col, t_col, name}
        """
        if mapping_data:
            self.config["last_column_mapping"] = mapping_data
            self._save_config()
