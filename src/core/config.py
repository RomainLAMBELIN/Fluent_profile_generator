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
                    data = json.load(f)
                # Un fichier corrompu ou d'un autre format ne doit pas
                # empecher l'application de demarrer
                return data if isinstance(data, dict) else {}
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
        """
        Récupère les derniers noms d'inlets, avec des index entiers.

        JSON ne stocke que des clés textuelles. Sans cette conversion, les
        recherches par index entier échouent et les noms personnalisés sont
        perdus silencieusement.

        Returns:
            Dict {index_entier: nom}
        """
        raw = self.config.get("last_inlet_names")
        if not isinstance(raw, dict):
            return {}

        names = {}
        for key, value in raw.items():
            try:
                idx = int(key)
            except (TypeError, ValueError):
                continue
            if isinstance(value, str) and value.strip():
                names[idx] = value
        return names
    
    def save_last_inlet_names(self, inlet_names):
        """Sauvegarde les derniers noms d'inlets utilisés."""
        if inlet_names:
            self.config["last_inlet_names"] = inlet_names
            self._save_config()
    
    def get_last_step2_params(self):
        """
        Récupère les derniers paramètres de l'étape 2, filtrés par type.

        Seules les valeurs exploitables sont retournées : une entrée d'un
        type inattendu est écartée au lieu de provoquer une erreur plus
        loin dans l'interface.
        """
        raw = self.config.get("last_step2_params")
        if not isinstance(raw, dict):
            return {}

        params = {}
        for key in ("dt_us", "flow_eps"):
            value = raw.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                params[key] = float(value)
        for key in ("methods", "smooth_params", "trend_lambda"):
            value = raw.get(key)
            if isinstance(value, dict):
                params[key] = value
        return params
    
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
    
    def get_language(self):
        """
        Code de langue mémorisé, ou None si aucun choix n'a été fait.

        La validation revient au module i18n : une valeur périmée ne doit
        pas empêcher le démarrage.
        """
        code = self.config.get("language")
        return code if isinstance(code, str) and code else None

    def save_language(self, code):
        """Mémorise la langue choisie."""
        if isinstance(code, str) and code:
            self.config["language"] = code
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
        """
        Récupère le dernier mapping de colonnes, après validation.

        Une configuration écrite par une version antérieure peut avoir une
        autre structure. Elle est alors ignorée plutôt que de faire échouer
        le démarrage. La validation est globale : un mapping partiellement
        valide serait trompeur, car il restituerait moins d'inlets que ceux
        réellement configurés.

        Returns:
            Dict {"time_col": str, "inlets": [{"q_col", "t_col", "name"}]}
            ou {} si la configuration est absente ou inutilisable
        """
        raw = self.config.get("last_column_mapping")
        if not isinstance(raw, dict):
            return {}

        inlets = raw.get("inlets")
        if not isinstance(inlets, list) or not inlets:
            return {}

        validated = []
        for entry in inlets:
            if not isinstance(entry, dict):
                return {}
            q_col = entry.get("q_col")
            t_col = entry.get("t_col")
            if not isinstance(q_col, str) or not q_col:
                return {}
            if not isinstance(t_col, str) or not t_col:
                return {}
            name = entry.get("name")
            if not isinstance(name, str) or not name.strip():
                name = f"inlet{len(validated) + 1}"
            validated.append({"q_col": q_col, "t_col": t_col, "name": name})

        time_col = raw.get("time_col")
        return {
            "time_col": time_col if isinstance(time_col, str) else "",
            "inlets": validated,
        }

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
