"""
Étape 4 : Export du fichier .prof
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from core.io import export_prof
from core.i18n import t


class Step4Export(ttk.Frame):
    """Interface d'export du fichier .prof."""
    
    def __init__(self, parent, app_state):
        super().__init__(parent)
        self.app_state = app_state
        self.export_done = False
        self._build_ui()
    
    def _build_ui(self):
        """Construction de l'interface."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        # Frame central
        center = ttk.Frame(self)
        center.grid(row=0, column=0)
        
        ttk.Label(
            center,
            text=t("Prêt à exporter le fichier .prof"),
            font=("Segoe UI", 12, "bold")
        ).pack(pady=(40, 10))
        
        ttk.Label(
            center,
            text=t("Cliquez sur 'Exporter' pour sauvegarder le profil Fluent"),
            font=("Segoe UI", 10)
        ).pack(pady=(0, 30))
        
        # Bouton export
        self.btn_export = ttk.Button(
            center,
            text=t("📁 Exporter vers .prof..."),
            command=self._export_prof
        )
        self.btn_export.pack(pady=10, ipadx=20, ipady=10)
        
        # Status
        self.lbl_status = ttk.Label(center, text="", font=("Segoe UI", 10), justify="center")
        self.lbl_status.pack(pady=20)
    
    def _export_prof(self):
        """Sauvegarde le fichier .prof."""
        output_file = filedialog.asksaveasfilename(
            parent=self,
            title=t("Enregistrer le fichier .prof"),
            defaultextension=".prof",
            filetypes=[(t("Profil Fluent"), "*.prof"), (t("Tous fichiers"), "*.*")]
        )
        
        if not output_file:
            return
        
        try:
            times = self.app_state.get("times")
            data_interp = self.app_state.get("data_interp", {})
            
            if times is None or not data_interp:
                raise ValueError(t("Aucune donnée interpolée disponible"))
            
            export_prof(output_file, times, data_interp)
            
            self.export_done = True
            self.lbl_status.config(
                text=t(
                    "✅ Export réussi !\n\n{path}\n\n{columns} colonnes × {points} points",
                    path=output_file, columns=len(data_interp), points=f"{len(times):,}",
                ),
                foreground="green"
            )
            
            messagebox.showinfo(
                t("Export terminé"),
                t(
                    "Le fichier .prof a été créé avec succès :\n\n{path}\n\n"
                    "{columns} colonnes × {points} points",
                    path=output_file, columns=len(data_interp), points=f"{len(times):,}",
                ),
                parent=self
            )
        
        except Exception as e:
            self.lbl_status.config(
                text=t("❌ Erreur lors de l'export :\n\n{error}", error=e),
                foreground="red"
            )
            messagebox.showerror(
                t("Erreur"),
                t("Erreur lors de l'export :\n\n{error}", error=e),
                parent=self
            )
    
    def validate(self) -> tuple[bool, str]:
        """
        Validation (toujours vraie, l'export n'est pas obligatoire).
        
        Returns:
            (is_valid, error_message)
        """
        return True, ""
