"""
Étape 1 : Sélection des fichiers CSV
"""

import tkinter as tk
from tkinter import ttk, filedialog

from core.constants import FILE_KEYS, FILE_LABELS, DEFAULT_INLET_NAMES


class Step1Files(ttk.Frame):
    """Interface de sélection des 4 fichiers CSV avec noms personnalisés."""
    
    def __init__(self, parent, app_state):
        super().__init__(parent)
        self.app_state = app_state
        self.file_entries = {}
        self.name_entries = {}
        self._build_ui()
    
    def _build_ui(self):
        """Construction de l'interface."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        
        # Instructions
        instructions = ttk.Label(
            self,
            text="Format attendu pour chaque fichier : 2 colonnes (temps en ms, valeur)\n"
                 "Vous pouvez personnaliser les noms des inlets pour l'export .prof",
            font=("Segoe UI", 10)
        )
        instructions.grid(row=0, column=0, sticky="w", pady=(0, 20))
        
        # Grid pour les fichiers et noms
        grid = ttk.Frame(self)
        grid.grid(row=1, column=0, sticky="nsew")
        grid.columnconfigure(1, weight=1)
        
        # Groupe Inlet 1
        ttk.Label(grid, text="═══ Inlet 1 ═══", font=("Segoe UI", 11, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 5)
        )
        
        # Nom personnalisé Inlet 1
        row_idx = 1
        ttk.Label(grid, text="Nom pour l'export :", font=("Segoe UI", 9)).grid(
            row=row_idx, column=0, sticky="w", pady=5, padx=(20, 10)
        )
        name_entry_1 = ttk.Entry(grid, width=20)
        name_entry_1.insert(0, DEFAULT_INLET_NAMES[0])
        name_entry_1.grid(row=row_idx, column=1, sticky="w", pady=5)
        self.name_entries["inlet1"] = name_entry_1
        ttk.Label(grid, text="(ex: tulipe, main, primary...)", font=("Segoe UI", 8), foreground="gray").grid(
            row=row_idx, column=2, sticky="w", padx=(10, 0)
        )
        
        # Fichiers Inlet 1
        row_idx = 2
        self._add_file_row(grid, row_idx, "Q_inlet1")
        row_idx = 3
        self._add_file_row(grid, row_idx, "T_inlet1")
        
        # Séparateur
        ttk.Separator(grid, orient="horizontal").grid(
            row=4, column=0, columnspan=3, sticky="ew", pady=15
        )
        
        # Groupe Inlet 2
        ttk.Label(grid, text="═══ Inlet 2 ═══", font=("Segoe UI", 11, "bold")).grid(
            row=5, column=0, columnspan=3, sticky="w", pady=(0, 5)
        )
        
        # Nom personnalisé Inlet 2
        row_idx = 6
        ttk.Label(grid, text="Nom pour l'export :", font=("Segoe UI", 9)).grid(
            row=row_idx, column=0, sticky="w", pady=5, padx=(20, 10)
        )
        name_entry_2 = ttk.Entry(grid, width=20)
        name_entry_2.insert(0, DEFAULT_INLET_NAMES[1])
        name_entry_2.grid(row=row_idx, column=1, sticky="w", pady=5)
        self.name_entries["inlet2"] = name_entry_2
        ttk.Label(grid, text="(ex: tige, secondary, aux...)", font=("Segoe UI", 8), foreground="gray").grid(
            row=row_idx, column=2, sticky="w", padx=(10, 0)
        )
        
        # Fichiers Inlet 2
        row_idx = 7
        self._add_file_row(grid, row_idx, "Q_inlet2")
        row_idx = 8
        self._add_file_row(grid, row_idx, "T_inlet2")
        
        # Restaurer les fichiers et noms déjà sélectionnés
        self._restore_files()
        self._restore_names()
    
    def _add_file_row(self, parent, row, key):
        """Ajoute une ligne pour la sélection d'un fichier."""
        ttk.Label(
            parent,
            text=FILE_LABELS[key] + " :",
            font=("Segoe UI", 10)
        ).grid(row=row, column=0, sticky="w", pady=8, padx=(20, 10))
        
        entry = ttk.Entry(parent, state="readonly")
        entry.grid(row=row, column=1, sticky="ew", pady=8)
        self.file_entries[key] = entry
        
        btn = ttk.Button(
            parent,
            text="Parcourir...",
            command=lambda k=key: self._select_file(k)
        )
        btn.grid(row=row, column=2, sticky="w", pady=8, padx=(10, 0))
    
    def _select_file(self, file_key):
        """Sélectionne un fichier CSV."""
        filename = filedialog.askopenfilename(
            parent=self,
            title=f"Sélectionner {file_key}",
            filetypes=[("CSV", "*.csv"), ("Tous fichiers", "*.*")]
        )
        
        if filename:
            self.app_state["files"][file_key] = filename
            self._update_entry(file_key, filename)
    
    def _update_entry(self, key, filename):
        """Met à jour l'affichage d'un fichier sélectionné."""
        entry = self.file_entries[key]
        entry.config(state="normal")
        entry.delete(0, "end")
        entry.insert(0, filename)
        entry.config(state="readonly")
    
    def _restore_files(self):
        """Restaure les fichiers déjà sélectionnés dans l'état."""
        for key in FILE_KEYS:
            if self.app_state["files"].get(key):
                self._update_entry(key, self.app_state["files"][key])
    
    def _restore_names(self):
        """Restaure les noms personnalisés depuis l'état."""
        if "inlet_names" in self.app_state:
            for key, entry in self.name_entries.items():
                if key in self.app_state["inlet_names"]:
                    entry.delete(0, "end")
                    entry.insert(0, self.app_state["inlet_names"][key])
    
    def _save_names(self):
        """Sauvegarde les noms personnalisés dans l'état."""
        if "inlet_names" not in self.app_state:
            self.app_state["inlet_names"] = {}
        
        for key, entry in self.name_entries.items():
            name = entry.get().strip()
            if not name:
                name = DEFAULT_INLET_NAMES[0] if key == "inlet1" else DEFAULT_INLET_NAMES[1]
            # Nettoyer le nom (pas d'espaces, caractères spéciaux)
            name = name.replace(" ", "_").replace("-", "_")
            self.app_state["inlet_names"][key] = name
    
    def validate(self) -> tuple[bool, str]:
        """
        Valide que tous les fichiers sont sélectionnés et sauvegarde les noms.
        
        Returns:
            (is_valid, error_message)
        """
        for key in FILE_KEYS:
            if not self.app_state["files"].get(key):
                return False, f"Veuillez sélectionner tous les fichiers requis.\nManquant : {FILE_LABELS[key]}"
        
        # Sauvegarder les noms
        self._save_names()
        
        return True, ""
