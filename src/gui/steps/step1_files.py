"""
Étape 1 : Import d'un fichier CSV multi-colonnes avec mapping dynamique des inlets
"""

import tkinter as tk
from tkinter import ttk, filedialog

from core.io import read_multi_column_csv, detect_columns
from core.constants import generate_file_keys


class Step1Files(ttk.Frame):
    """Interface d'import CSV multi-colonnes avec détection automatique et mapping dynamique."""

    def __init__(self, parent, app_state):
        super().__init__(parent)
        self.app_state = app_state
        self.csv_df = None
        self.all_columns = []
        self.inlet_rows = []  # Liste de dicts {frame, q_combo, t_combo, name_entry, idx}
        self._build_ui()
        self._restore_state()

    def _build_ui(self):
        """Construction de l'interface."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=0)  # preview
        self.rowconfigure(3, weight=1)  # mapping (scrollable)

        # --- Instructions ---
        instructions = ttk.Label(
            self,
            text="Importez un fichier CSV multi-colonnes avec header.\n"
                 "Les colonnes seront auto-détectées et vous pourrez configurer le mapping.",
            font=("Segoe UI", 10),
        )
        instructions.grid(row=0, column=0, sticky="w", pady=(0, 10))

        # --- Sélection fichier ---
        file_frame = ttk.Frame(self)
        file_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)

        ttk.Label(file_frame, text="Fichier CSV :", font=("Segoe UI", 10)).grid(
            row=0, column=0, sticky="w", padx=(0, 10)
        )

        self.file_entry = ttk.Entry(file_frame, state="readonly")
        self.file_entry.grid(row=0, column=1, sticky="ew")

        ttk.Button(
            file_frame, text="Parcourir...", command=self._select_file
        ).grid(row=0, column=2, sticky="w", padx=(10, 0))

        # --- Aperçu CSV (Treeview) ---
        preview_label = ttk.Label(
            self, text="Aperçu du fichier CSV :", font=("Segoe UI", 10, "bold")
        )
        preview_label.grid(row=2, column=0, sticky="w", pady=(5, 2))

        preview_frame = ttk.Frame(self, height=160)
        preview_frame.grid(row=3, column=0, sticky="nsew", pady=(0, 10))
        preview_frame.grid_propagate(False)
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(preview_frame, show="headings", height=6)
        tree_scroll_x = ttk.Scrollbar(preview_frame, orient="horizontal", command=self.tree.xview)
        tree_scroll_y = ttk.Scrollbar(preview_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(xscrollcommand=tree_scroll_x.set, yscrollcommand=tree_scroll_y.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        tree_scroll_y.grid(row=0, column=1, sticky="ns")
        tree_scroll_x.grid(row=1, column=0, sticky="ew")

        # --- Mapping des colonnes (scrollable) ---
        mapping_label = ttk.Label(
            self, text="Mapping des colonnes :", font=("Segoe UI", 10, "bold")
        )
        mapping_label.grid(row=4, column=0, sticky="w", pady=(5, 2))

        mapping_outer = ttk.Frame(self)
        mapping_outer.grid(row=5, column=0, sticky="nsew", pady=(0, 5))
        self.rowconfigure(5, weight=2)
        mapping_outer.columnconfigure(0, weight=1)
        mapping_outer.rowconfigure(0, weight=1)

        self.mapping_canvas = tk.Canvas(mapping_outer, highlightthickness=0)
        mapping_scrollbar = ttk.Scrollbar(mapping_outer, orient="vertical", command=self.mapping_canvas.yview)
        self.mapping_inner = ttk.Frame(self.mapping_canvas)

        self.mapping_inner.bind(
            "<Configure>",
            lambda e: self.mapping_canvas.configure(scrollregion=self.mapping_canvas.bbox("all")),
        )

        self.mapping_canvas.create_window((0, 0), window=self.mapping_inner, anchor="nw")
        self.mapping_canvas.configure(yscrollcommand=mapping_scrollbar.set)

        self.mapping_canvas.grid(row=0, column=0, sticky="nsew")
        mapping_scrollbar.grid(row=0, column=1, sticky="ns")

        # Mouse wheel scrolling
        def _on_mousewheel(event):
            self.mapping_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self.mapping_canvas.bind("<MouseWheel>", _on_mousewheel)
        self.mapping_inner.bind("<MouseWheel>", _on_mousewheel)

        # Colonne temps
        time_frame = ttk.Frame(self.mapping_inner)
        time_frame.pack(fill="x", padx=5, pady=(5, 10))

        ttk.Label(time_frame, text="Colonne temps :", font=("Segoe UI", 10)).pack(
            side="left", padx=(0, 10)
        )
        self.time_combo = ttk.Combobox(time_frame, state="readonly", width=25)
        self.time_combo.pack(side="left")

        # Séparateur
        ttk.Separator(self.mapping_inner, orient="horizontal").pack(fill="x", padx=5, pady=5)

        # Frame pour les lignes d'inlet
        self.inlets_frame = ttk.Frame(self.mapping_inner)
        self.inlets_frame.pack(fill="x", padx=5)

        # Bouton ajouter
        self.btn_add = ttk.Button(
            self.mapping_inner, text="+ Ajouter un inlet", command=self._add_inlet_row
        )
        self.btn_add.pack(anchor="w", padx=5, pady=(10, 5))

        # --- Status ---
        self.lbl_status = ttk.Label(
            self, text="Aucun fichier chargé", font=("Segoe UI", 9), foreground="gray"
        )
        self.lbl_status.grid(row=6, column=0, sticky="w", pady=(5, 0))

    def _select_file(self):
        """Ouvre le dialogue de sélection d'un fichier CSV."""
        filename = filedialog.askopenfilename(
            parent=self,
            title="Sélectionner le fichier CSV",
            filetypes=[("CSV", "*.csv"), ("Tous fichiers", "*.*")],
        )
        if filename:
            self._load_csv(filename)

    def _load_csv(self, filename):
        """Charge un fichier CSV et met à jour l'interface."""
        try:
            df = read_multi_column_csv(filename)
        except Exception as e:
            self.lbl_status.config(
                text=f"Erreur de lecture : {e}", foreground="red"
            )
            return

        self.csv_df = df
        self.all_columns = list(df.columns)
        self.app_state["csv_file"] = filename

        # Mettre à jour l'entry
        self.file_entry.config(state="normal")
        self.file_entry.delete(0, "end")
        self.file_entry.insert(0, filename)
        self.file_entry.config(state="readonly")

        # Mettre à jour l'aperçu
        self._update_preview(df)

        # Auto-détection
        detected = detect_columns(df)

        # Mettre à jour le combo temps
        self.time_combo["values"] = self.all_columns
        if detected["time_col"]:
            self.time_combo.set(detected["time_col"])

        # Supprimer les lignes d'inlet existantes
        self._clear_inlet_rows()

        # Auto-pairing : zip(q_cols triées, t_cols triées)
        q_cols = sorted(detected["q_cols"])
        t_cols = sorted(detected["t_cols"])

        n_pairs = max(len(q_cols), len(t_cols))
        if n_pairs == 0:
            # Pas de détection : créer un inlet vide
            self._add_inlet_row()
        else:
            for i in range(n_pairs):
                q = q_cols[i] if i < len(q_cols) else ""
                t = t_cols[i] if i < len(t_cols) else ""
                self._add_inlet_row(q_default=q, t_default=t)

        self._update_status()

    def _update_preview(self, df):
        """Met à jour le Treeview avec les 10 premières lignes."""
        # Nettoyer
        self.tree.delete(*self.tree.get_children())
        cols = list(df.columns)
        self.tree["columns"] = cols

        for col in cols:
            self.tree.heading(col, text=col)
            # Largeur adaptée
            max_width = max(len(str(col)) * 10, 80)
            self.tree.column(col, width=min(max_width, 150), minwidth=60)

        # Insérer les 10 premières lignes
        for _, row in df.head(10).iterrows():
            values = [str(row[c]) for c in cols]
            self.tree.insert("", "end", values=values)

    def _clear_inlet_rows(self):
        """Supprime toutes les lignes d'inlet."""
        for row_data in self.inlet_rows:
            row_data["frame"].destroy()
        self.inlet_rows.clear()

    def _add_inlet_row(self, q_default="", t_default="", name_default=""):
        """Ajoute une ligne de configuration d'inlet."""
        idx = len(self.inlet_rows) + 1

        frame = ttk.LabelFrame(
            self.inlets_frame, text=f"Inlet {idx}", padding=5
        )
        frame.pack(fill="x", pady=3)

        # Ligne 1 : Q et T
        row1 = ttk.Frame(frame)
        row1.pack(fill="x", pady=2)

        ttk.Label(row1, text="Colonne Q :", width=12).pack(side="left")
        q_combo = ttk.Combobox(row1, values=self.all_columns, state="readonly", width=20)
        q_combo.pack(side="left", padx=(0, 15))
        if q_default and q_default in self.all_columns:
            q_combo.set(q_default)

        ttk.Label(row1, text="Colonne T :", width=12).pack(side="left")
        t_combo = ttk.Combobox(row1, values=self.all_columns, state="readonly", width=20)
        t_combo.pack(side="left", padx=(0, 15))
        if t_default and t_default in self.all_columns:
            t_combo.set(t_default)

        # Ligne 2 : Nom + Supprimer
        row2 = ttk.Frame(frame)
        row2.pack(fill="x", pady=2)

        ttk.Label(row2, text="Nom export :", width=12).pack(side="left")
        name_entry = ttk.Entry(row2, width=20)
        name_entry.pack(side="left", padx=(0, 15))
        if name_default:
            name_entry.insert(0, name_default)
        else:
            name_entry.insert(0, f"inlet{idx}")

        btn_remove = ttk.Button(
            row2,
            text="X Supprimer",
            command=lambda: self._remove_inlet_row(row_data),
        )
        btn_remove.pack(side="right")

        row_data = {
            "frame": frame,
            "q_combo": q_combo,
            "t_combo": t_combo,
            "name_entry": name_entry,
            "idx": idx,
        }
        self.inlet_rows.append(row_data)
        # Bind mouse wheel on new widgets
        for w in (frame, row1, row2, q_combo, t_combo, name_entry, btn_remove):
            w.bind("<MouseWheel>", lambda e: self.mapping_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        self._update_status()

    def _remove_inlet_row(self, row_data):
        """Supprime une ligne d'inlet."""
        if len(self.inlet_rows) <= 1:
            return  # Au moins 1 inlet requis
        row_data["frame"].destroy()
        self.inlet_rows.remove(row_data)
        # Renuméroter
        for i, rd in enumerate(self.inlet_rows):
            rd["idx"] = i + 1
            rd["frame"].config(text=f"Inlet {i + 1}")
        self._update_status()

    def _update_status(self):
        """Met à jour le label de status."""
        n = len(self.inlet_rows)
        self.lbl_status.config(
            text=f"{n} inlet(s) configuré(s)", foreground="blue"
        )

    def _restore_state(self):
        """Restaure l'état depuis app_state (fichier et mapping précédents)."""
        csv_file = self.app_state.get("csv_file", "")
        if csv_file:
            import os
            if os.path.exists(csv_file):
                self._load_csv(csv_file)

                # Restaurer le mapping si disponible
                mapping = self.app_state.get("column_mapping")
                inlet_names = self.app_state.get("inlet_names", {})
                time_col = self.app_state.get("time_col", "")

                if time_col and time_col in self.all_columns:
                    self.time_combo.set(time_col)

                if mapping:
                    self._clear_inlet_rows()
                    for q_col, t_col, inlet_idx in mapping:
                        name = inlet_names.get(inlet_idx, f"inlet{inlet_idx}")
                        self._add_inlet_row(
                            q_default=q_col, t_default=t_col, name_default=name
                        )

    def _get_mapping(self):
        """
        Construit le column_mapping et inlet_names à partir de l'interface.

        Returns:
            (time_col, column_mapping, inlet_names, file_keys) ou lève ValueError
        """
        time_col = self.time_combo.get()
        if not time_col:
            raise ValueError("Veuillez sélectionner la colonne de temps.")

        column_mapping = []
        inlet_names = {}

        for i, row_data in enumerate(self.inlet_rows):
            idx = i + 1
            q_col = row_data["q_combo"].get()
            t_col = row_data["t_combo"].get()
            name = row_data["name_entry"].get().strip()

            if not q_col:
                raise ValueError(f"Inlet {idx} : colonne Q non sélectionnée.")
            if not t_col:
                raise ValueError(f"Inlet {idx} : colonne T non sélectionnée.")
            if not name:
                name = f"inlet{idx}"

            # Nettoyer le nom
            name = name.replace(" ", "_").replace("-", "_")

            column_mapping.append((q_col, t_col, idx))
            inlet_names[idx] = name

        if not column_mapping:
            raise ValueError("Aucun inlet configuré.")

        file_keys = generate_file_keys(len(column_mapping))

        return time_col, column_mapping, inlet_names, file_keys

    def validate(self) -> tuple:
        """
        Valide la configuration et stocke les données dans app_state.

        Returns:
            (is_valid, error_message)
        """
        if self.csv_df is None:
            return False, "Veuillez sélectionner un fichier CSV."

        try:
            time_col, column_mapping, inlet_names, file_keys = self._get_mapping()
        except ValueError as e:
            return False, str(e)

        # Vérifier les colonnes dupliquées
        all_selected = [time_col]
        for q_col, t_col, _ in column_mapping:
            if q_col in all_selected:
                return False, f"La colonne '{q_col}' est utilisée plusieurs fois."
            all_selected.append(q_col)
            if t_col in all_selected:
                return False, f"La colonne '{t_col}' est utilisée plusieurs fois."
            all_selected.append(t_col)

        # Stocker dans app_state
        self.app_state["csv_df"] = self.csv_df
        self.app_state["time_col"] = time_col
        self.app_state["column_mapping"] = column_mapping
        self.app_state["inlet_names"] = inlet_names
        self.app_state["file_keys"] = file_keys

        return True, ""
