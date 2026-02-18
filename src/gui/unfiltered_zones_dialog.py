"""
Dialogue pour configurer les zones non-filtrées
"""

import tkinter as tk
from tkinter import ttk, messagebox

from gui.zone_editor_dialog import ZoneEditorDialog


class UnfilteredZonesDialog(tk.Toplevel):
    """Dialogue pour définir les zones non-filtrées."""
    
    def __init__(self, parent, sim_duration, initial_zones=None, title="Zones non-filtrées",
                 df=None, current_method="pchip", current_smooth=0.0):
        super().__init__(parent)
        self.title(title)
        self.geometry("600x450")
        self.resizable(True, True)
        
        self.sim_duration = sim_duration
        self.zones = initial_zones.copy() if initial_zones else []
        self.result = None
        
        # Pour la prévisualisation
        self.df = df
        self.current_method = current_method
        self.current_smooth = current_smooth
        
        self._build_ui()
        
        # Modal
        self.transient(parent)
        self.grab_set()
        
    def _build_ui(self):
        """Construction de l'interface."""
        main = ttk.Frame(self, padding=15)
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=1)
        main.rowconfigure(1, weight=1)
        
        # Instructions
        ttk.Label(
            main,
            text=f"Définissez les plages de temps où l'interpolation doit être EXACTE (sans lissage)\n"
                 f"Durée de simulation : 0.0 à {self.sim_duration:.6f} s",
            font=("Segoe UI", 10)
        ).grid(row=0, column=0, sticky="w", pady=(0, 15))
        
        # Liste des zones
        list_frame = ttk.LabelFrame(main, text="Zones définies", padding=10)
        list_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Listbox avec scrollbar
        scroll_frame = ttk.Frame(list_frame)
        scroll_frame.grid(row=0, column=0, sticky="nsew")
        scroll_frame.columnconfigure(0, weight=1)
        scroll_frame.rowconfigure(0, weight=1)
        
        self.listbox = tk.Listbox(scroll_frame, height=8)
        scrollbar = ttk.Scrollbar(scroll_frame, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)
        
        self.listbox.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Boutons de gestion
        btn_frame = ttk.Frame(list_frame)
        btn_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        
        ttk.Button(btn_frame, text="➕ Ajouter", command=self._add_zone).pack(side="left", padx=(0, 5))
        ttk.Button(btn_frame, text="✏️ Modifier", command=self._edit_zone).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🗑️ Supprimer", command=self._remove_zone).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Vider tout", command=self._clear_all).pack(side="left", padx=(5, 0))
        
        # Boutons OK/Annuler
        bottom_frame = ttk.Frame(main)
        bottom_frame.grid(row=2, column=0, sticky="ew")
        
        ttk.Button(bottom_frame, text="OK", command=self._on_ok, width=12).pack(side="right", padx=(5, 0))
        ttk.Button(bottom_frame, text="Annuler", command=self._on_cancel, width=12).pack(side="right")
        
        # Remplir la liste
        self._refresh_list()
    
    def _refresh_list(self):
        """Rafraîchit la liste des zones."""
        self.listbox.delete(0, "end")
        for zone in sorted(self.zones, key=lambda z: z[0]):
            if len(zone) == 3:
                t_start, t_end, zone_type = zone
                type_label = "Exacte" if zone_type == "exact" else "Linéaire"
            else:
                # Ancienne version (rétrocompatibilité)
                t_start, t_end = zone
                type_label = "Exacte"
            self.listbox.insert("end", f"[{t_start:.6f} → {t_end:.6f}] {type_label}")
    
    def _add_zone(self):
        """Ajoute une nouvelle zone."""
        # Utiliser le nouveau dialogue avec prévisualisation si données disponibles
        if self.df is not None:
            dialog = ZoneEditorDialog(
                self,
                self.sim_duration,
                self.df,
                self.current_method,
                self.current_smooth
            )
        else:
            # Fallback sur l'ancien dialogue
            dialog = ZoneInputDialog(self, self.sim_duration)
        
        self.wait_window(dialog)
        
        if dialog.result:
            t_start, t_end, zone_type = dialog.result
            # Vérifier les chevauchements
            for zone in self.zones:
                existing_start = zone[0]
                existing_end = zone[1]
                if not (t_end <= existing_start or t_start >= existing_end):
                    messagebox.showwarning(
                        "Chevauchement",
                        f"Cette zone chevauche une zone existante:\n"
                        f"[{existing_start:.6f} → {existing_end:.6f}]",
                        parent=self
                    )
                    return
            
            self.zones.append((t_start, t_end, zone_type))
            self._refresh_list()
    
    def _edit_zone(self):
        """Modifie la zone sélectionnée."""
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showinfo("Info", "Sélectionnez une zone à modifier.", parent=self)
            return
        
        idx = selection[0]
        zone = self.zones[idx]
        
        if len(zone) == 3:
            t_start, t_end, zone_type = zone
        else:
            t_start, t_end = zone
            zone_type = "exact"
        
        # Utiliser le nouveau dialogue avec prévisualisation si données disponibles
        if self.df is not None:
            dialog = ZoneEditorDialog(
                self,
                self.sim_duration,
                self.df,
                self.current_method,
                self.current_smooth,
                t_start,
                t_end,
                zone_type
            )
        else:
            # Fallback sur l'ancien dialogue
            dialog = ZoneInputDialog(self, self.sim_duration, t_start, t_end, zone_type)
        
        self.wait_window(dialog)
        
        if dialog.result:
            new_start, new_end, new_type = dialog.result
            # Vérifier les chevauchements (sauf avec soi-même)
            for i, z in enumerate(self.zones):
                if i == idx:
                    continue
                existing_start = z[0]
                existing_end = z[1]
                if not (new_end <= existing_start or new_start >= existing_end):
                    messagebox.showwarning(
                        "Chevauchement",
                        f"Cette zone chevauche une zone existante:\n"
                        f"[{existing_start:.6f} → {existing_end:.6f}]",
                        parent=self
                    )
                    return
            
            self.zones[idx] = (new_start, new_end, new_type)
            self._refresh_list()
    
    def _remove_zone(self):
        """Supprime la zone sélectionnée."""
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showinfo("Info", "Sélectionnez une zone à supprimer.", parent=self)
            return
        
        idx = selection[0]
        self.zones.pop(idx)
        self._refresh_list()
    
    def _clear_all(self):
        """Vide toutes les zones."""
        if self.zones and messagebox.askyesno(
            "Confirmer",
            "Supprimer toutes les zones ?",
            parent=self
        ):
            self.zones = []
            self._refresh_list()
    
    def _on_ok(self):
        """Valide et ferme."""
        self.result = self.zones
        self.destroy()
    
    def _on_cancel(self):
        """Annule et ferme."""
        self.result = None
        self.destroy()


class ZoneInputDialog(tk.Toplevel):
    """Dialogue pour saisir une zone."""
    
    def __init__(self, parent, sim_duration, t_start=None, t_end=None, zone_type="exact"):
        super().__init__(parent)
        self.title("Définir une zone")
        self.geometry("520x360")
        self.resizable(False, False)
        
        self.sim_duration = sim_duration
        self.result = None
        
        main = ttk.Frame(self, padding=20)
        main.pack(fill="both", expand=True)
        
        ttk.Label(main, text=f"Plage de temps (0.0 à {sim_duration:.6f} s)").pack(anchor="w", pady=(0, 15))
        
        # Début
        row1 = ttk.Frame(main)
        row1.pack(fill="x", pady=5)
        ttk.Label(row1, text="Début (s) :", width=12).pack(side="left")
        self.entry_start = ttk.Entry(row1)
        self.entry_start.pack(side="left", fill="x", expand=True, padx=(10, 0))
        if t_start is not None:
            self.entry_start.insert(0, f"{t_start:.6f}")
        
        # Fin
        row2 = ttk.Frame(main)
        row2.pack(fill="x", pady=5)
        ttk.Label(row2, text="Fin (s) :", width=12).pack(side="left")
        self.entry_end = ttk.Entry(row2)
        self.entry_end.pack(side="left", fill="x", expand=True, padx=(10, 0))
        if t_end is not None:
            self.entry_end.insert(0, f"{t_end:.6f}")
        
        # Type de zone
        ttk.Separator(main, orient="horizontal").pack(fill="x", pady=15)
        ttk.Label(main, text="Type d'interpolation dans la zone :").pack(anchor="w", pady=(0, 5))
        
        self.zone_type = tk.StringVar(value=zone_type)
        
        row3 = ttk.Frame(main)
        row3.pack(fill="x", pady=2)
        ttk.Radiobutton(
            row3,
            text="Exacte (PCHIP - passe par tous les points)",
            variable=self.zone_type,
            value="exact"
        ).pack(anchor="w")
        
        row4 = ttk.Frame(main)
        row4.pack(fill="x", pady=2)
        ttk.Radiobutton(
            row4,
            text="Linéaire (droite entre les 2 points de borne - ignore les points intermédiaires)",
            variable=self.zone_type,
            value="linear"
        ).pack(anchor="w")
        
        # Note explicative
        note = ttk.Label(
            main,
            text="Note : Type 'Linéaire' trace une droite entre le premier et dernier point\n"
                 "de la zone, sautant ainsi tous les points intermédiaires problématiques.",
            font=("Segoe UI", 8),
            foreground="gray",
            wraplength=460
        )
        note.pack(anchor="w", pady=(5, 0))
        
        # Boutons
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill="x", pady=(20, 0))
        
        btn_cancel = ttk.Button(btn_frame, text="Annuler", command=self.destroy, width=12)
        btn_cancel.pack(side="right")
        
        btn_ok = ttk.Button(btn_frame, text="OK", command=self._on_ok, width=12)
        btn_ok.pack(side="right", padx=(5, 5))
        
        # Modal
        self.transient(parent)
        self.grab_set()
        
        # Centrer la fenêtre
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
        
        # Bind Entrée pour valider
        self.bind("<Return>", lambda e: self._on_ok())
        self.bind("<Escape>", lambda e: self.destroy())
        
        self.entry_start.focus()
    
    def _on_ok(self):
        """Valide la saisie."""
        try:
            t_start = float(self.entry_start.get())
            t_end = float(self.entry_end.get())
            
            if t_start < 0 or t_end > self.sim_duration:
                raise ValueError(f"Les temps doivent être entre 0 et {self.sim_duration:.6f}")
            
            if t_start >= t_end:
                raise ValueError("Le début doit être strictement inférieur à la fin")
            
            self.result = (t_start, t_end, self.zone_type.get())
            self.destroy()
            
        except ValueError as e:
            messagebox.showerror("Erreur", str(e), parent=self)
