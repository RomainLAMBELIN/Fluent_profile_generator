"""
Dialogue de configuration des zones spéciales avec prévisualisation interactive.

Une zone force localement l'interpolation :
- "exact"  : PCHIP passant par tous les points de mesure de la zone
- "linear" : droite entre les deux bornes (points intermédiaires ignorés)

Les bornes sont ajustées aux points de mesure les plus proches. La plage peut
être sélectionnée par cliquer-glisser sur le graphique ou saisie au clavier.
"""

import tkinter as tk
from tkinter import ttk, messagebox

import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib.widgets import SpanSelector

from core.interpolation import interpolate, zones_to_index_ranges, prepare_xy
from core.analysis import compute_interpolation_error, format_error_text
from core.constants import INTERP_METHODS
from core.i18n import t

#: Libellés sources des types de zone, traduits à l'affichage
ZONE_TYPE_LABELS = {"exact": "Exacte", "linear": "Linéaire"}
ZONE_COLORS = {"exact": "tab:green", "linear": "tab:purple"}
PENDING_COLOR = "tab:red"


class UnfilteredZonesDialog(tk.Toplevel):
    """Dialogue de définition des zones spéciales d'une courbe."""

    def __init__(self, parent, sim_duration, initial_zones=None, title="Zones spéciales",
                 df=None, current_method="pchip", current_smooth=0.0,
                 trend_lambda=1.0, inverted=False):
        super().__init__(parent)
        if df is None or len(df) < 2:
            raise ValueError("Données de courbe requises pour configurer les zones.")

        self.title(title)
        self.geometry("1150x700")
        self.minsize(950, 600)

        self.df = df
        self.x, self.y = prepare_xy(df)
        self.sim_duration = sim_duration
        self.method = current_method
        self.smooth = current_smooth
        self.trend_lambda = trend_lambda
        self.sign = -1.0 if inverted else 1.0

        # Zones validées : liste de (t_start, t_end, type), bornes ajustées
        self.zones = self._snap_zones(initial_zones)
        self.result = None
        self.selected_idx = None
        self.pending = None  # (i_start, i_end) de la zone en cours d'édition
        self.zone_type_var = tk.StringVar(value="exact")
        self._span = None

        self._build_ui()
        self._refresh_table()
        self._update_preview()

        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.bind("<Escape>", lambda e: self._on_cancel())

    # ------------------------------------------------------------------
    # Utilitaires
    # ------------------------------------------------------------------

    def _snap_index(self, value):
        return int(np.argmin(np.abs(self.x - float(value))))

    def _zone_indices(self, zone):
        return self._snap_index(zone[0]), self._snap_index(zone[1])

    def _snap_zones(self, zones):
        ranges = zones_to_index_ranges(self.x, zones)
        return [(float(self.x[i0]), float(self.x[i1]), zt) for i0, i1, zt in ranges]

    def _set_entries(self, t0, t1):
        self.entry_start.delete(0, "end")
        self.entry_start.insert(0, f"{t0:.6f}")
        self.entry_end.delete(0, "end")
        self.entry_end.insert(0, f"{t1:.6f}")

    def _interp(self, times, zones):
        return interpolate(
            self.df, times, method=self.method, smooth_factor=self.smooth,
            unfiltered_zones=zones, trend_lambda=self.trend_lambda,
        )

    # ------------------------------------------------------------------
    # Interface
    # ------------------------------------------------------------------

    def _build_ui(self):
        main = ttk.Frame(self, padding=10)
        main.pack(fill="both", expand=True)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(1, weight=1)

        info = t(
            "Cliquez-glissez sur le graphique pour sélectionner une plage, ou saisissez "
            "les bornes. Les bornes sont ajustées aux points de mesure les plus proches. "
            "Méthode globale : {method}. Données : {start} → {end} s ({points} points).",
            method=t(INTERP_METHODS.get(self.method, self.method)),
            start=f"{self.x[0]:.6f}", end=f"{self.x[-1]:.6f}", points=len(self.x),
        )
        ttk.Label(main, text=info, wraplength=1100, justify="left").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 8)
        )

        # ---- Panneau gauche ----
        left = ttk.Frame(main)
        left.grid(row=1, column=0, sticky="ns", padx=(0, 10))
        left.rowconfigure(0, weight=1)

        list_frame = ttk.LabelFrame(left, text=t("Zones définies"), padding=8)
        list_frame.grid(row=0, column=0, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        cols = ("num", "start", "end", "type", "pts")
        self.tree = ttk.Treeview(
            list_frame, columns=cols, show="headings", height=8, selectmode="browse"
        )
        for col, text, width, anchor in (
            ("num", "#", 30, "center"),
            ("start", t("Début (s)"), 90, "e"),
            ("end", t("Fin (s)"), 90, "e"),
            ("type", t("Type"), 70, "w"),
            ("pts", t("Points"), 55, "center"),
        ):
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor=anchor, stretch=False)
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        btns = ttk.Frame(list_frame)
        btns.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        self.btn_delete = ttk.Button(
            btns, text=t("Supprimer"), command=self._delete_selected, state="disabled"
        )
        self.btn_delete.pack(side="left")
        ttk.Button(btns, text=t("Tout supprimer"), command=self._clear_all).pack(
            side="left", padx=(5, 0)
        )

        edit_frame = ttk.LabelFrame(left, text=t("Zone en cours d'édition"), padding=8)
        edit_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        edit_frame.columnconfigure(1, weight=1)

        ttk.Label(edit_frame, text=t("Début (s) :")).grid(row=0, column=0, sticky="w", pady=2)
        self.entry_start = ttk.Entry(edit_frame, width=14)
        self.entry_start.grid(row=0, column=1, sticky="w", pady=2)
        ttk.Label(edit_frame, text=t("Fin (s) :")).grid(row=1, column=0, sticky="w", pady=2)
        self.entry_end = ttk.Entry(edit_frame, width=14)
        self.entry_end.grid(row=1, column=1, sticky="w", pady=2)
        for entry in (self.entry_start, self.entry_end):
            entry.bind("<Return>", lambda ev: self._on_entry_change())
            entry.bind("<FocusOut>", lambda ev: self._on_entry_change())

        ttk.Label(edit_frame, text=t("Type :")).grid(row=2, column=0, sticky="nw", pady=(6, 2))
        type_frame = ttk.Frame(edit_frame)
        type_frame.grid(row=2, column=1, sticky="w", pady=(6, 2))
        ttk.Radiobutton(
            type_frame, text=t("Exacte (PCHIP par tous les points)"),
            variable=self.zone_type_var, value="exact", command=self._update_preview,
        ).pack(anchor="w")
        ttk.Radiobutton(
            type_frame, text=t("Linéaire (droite entre les bornes)"),
            variable=self.zone_type_var, value="linear", command=self._update_preview,
        ).pack(anchor="w")

        self.lbl_edit_info = ttk.Label(
            edit_frame, text=t("Aucune plage sélectionnée."), foreground="gray",
            wraplength=300, justify="left",
        )
        self.lbl_edit_info.grid(row=3, column=0, columnspan=2, sticky="w", pady=(6, 2))

        action = ttk.Frame(edit_frame)
        action.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        self.btn_add = ttk.Button(action, text=t("Ajouter"), command=self._add_zone)
        self.btn_add.pack(side="left")
        self.btn_apply = ttk.Button(
            action, text=t("Appliquer"), command=self._apply_zone, state="disabled"
        )
        self.btn_apply.pack(side="left", padx=(5, 0))
        ttk.Button(action, text=t("Nouvelle"), command=self._new_zone).pack(
            side="left", padx=(5, 0)
        )

        legend = t(
            "Vert : zone exacte · Violet : zone linéaire · Rouge hachuré : zone en édition.\n"
            "Les zones ne peuvent pas se chevaucher (elles peuvent se toucher).\n"
            "Le raccord avec le reste de la courbe est continu."
        )
        ttk.Label(
            left, text=legend, foreground="gray", wraplength=330,
            justify="left", font=("Segoe UI", 8),
        ).grid(row=2, column=0, sticky="w", pady=(10, 0))

        # ---- Panneau droit : graphique ----
        right = ttk.LabelFrame(main, text=t("Prévisualisation"), padding=5)
        right.grid(row=1, column=1, sticky="nsew")
        self.fig = Figure(figsize=(7, 4.5), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, right)
        toolbar = NavigationToolbar2Tk(self.canvas, right, pack_toolbar=False)
        toolbar.update()
        toolbar.pack(side="bottom", fill="x")
        self.canvas.get_tk_widget().pack(side="top", fill="both", expand=True)

        # ---- Bas ----
        bottom = ttk.Frame(main)
        bottom.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        ttk.Button(bottom, text="OK", command=self._on_ok, width=12).pack(side="right", padx=(5, 0))
        ttk.Button(bottom, text=t("Annuler"), command=self._on_cancel, width=12).pack(side="right")
        self.lbl_status = ttk.Label(bottom, text="", foreground="gray")
        self.lbl_status.pack(side="left")

    # ------------------------------------------------------------------
    # Liste des zones
    # ------------------------------------------------------------------

    def _refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        for i, zone in enumerate(self.zones):
            t0, t1, zt = zone
            i0, i1 = self._zone_indices(zone)
            self.tree.insert(
                "", "end", iid=str(i),
                values=(i + 1, f"{t0:.6f}", f"{t1:.6f}",
                        t(ZONE_TYPE_LABELS.get(zt, zt)), i1 - i0 + 1),
            )
        if self.selected_idx is not None and 0 <= self.selected_idx < len(self.zones):
            self.tree.selection_set(str(self.selected_idx))
        else:
            self.selected_idx = None
        has_sel = self.selected_idx is not None
        self.btn_delete.config(state="normal" if has_sel else "disabled")
        self.btn_apply.config(state="normal" if has_sel else "disabled")
        self.lbl_status.config(text=t("{n} zone(s) définie(s)", n=len(self.zones)))

    def _on_tree_select(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        if idx >= len(self.zones):
            return
        self.selected_idx = idx
        t0, t1, zt = self.zones[idx]
        self._set_entries(t0, t1)
        self.zone_type_var.set(zt)
        self.pending = self._zone_indices(self.zones[idx])
        self.btn_delete.config(state="normal")
        self.btn_apply.config(state="normal")
        self._update_edit_info()
        self._update_preview()

    def _delete_selected(self):
        if self.selected_idx is None or self.selected_idx >= len(self.zones):
            return
        self.zones.pop(self.selected_idx)
        self._new_zone()

    def _clear_all(self):
        if not self.zones:
            return
        if messagebox.askyesno(
            t("Confirmer"), t("Supprimer toutes les zones ?"), parent=self
        ):
            self.zones = []
            self._new_zone()

    # ------------------------------------------------------------------
    # Édition
    # ------------------------------------------------------------------

    def _new_zone(self):
        """Désélectionne et vide la zone en cours d'édition."""
        self.tree.selection_remove(self.tree.selection())
        self.selected_idx = None
        self.pending = None
        self.entry_start.delete(0, "end")
        self.entry_end.delete(0, "end")
        self._refresh_table()
        self._update_edit_info()
        self._update_preview()

    def _on_span_select(self, vmin, vmax):
        """Sélection d'une plage par cliquer-glisser sur le graphique."""
        if vmax - vmin <= 0:
            return
        i0 = self._snap_index(vmin)
        i1 = self._snap_index(vmax)
        if i1 <= i0:
            i1 = min(i0 + 1, len(self.x) - 1)
        if i1 <= i0:
            return
        self.pending = (i0, i1)
        self._set_entries(self.x[i0], self.x[i1])
        self._update_edit_info()
        # Redessiner hors du callback du SpanSelector (qui est recréé au redraw)
        self.after_idle(self._update_preview)

    def _on_entry_change(self):
        s0 = self.entry_start.get().strip().replace(",", ".")
        s1 = self.entry_end.get().strip().replace(",", ".")
        if not s0 and not s1:
            return
        try:
            t0 = float(s0)
            t1 = float(s1)
        except ValueError:
            self.lbl_edit_info.config(
                text=t("Bornes invalides : saisir deux nombres."), foreground="red"
            )
            return
        i0 = self._snap_index(t0)
        i1 = self._snap_index(t1)
        if i1 < i0:
            i0, i1 = i1, i0
        if i1 == i0:
            i1 = min(i0 + 1, len(self.x) - 1)
        if i1 <= i0:
            self.lbl_edit_info.config(
                text=t("La zone doit contenir au moins 2 points de mesure."), foreground="red"
            )
            return
        if self.pending == (i0, i1):
            return
        self.pending = (i0, i1)
        self._set_entries(self.x[i0], self.x[i1])
        self._update_edit_info()
        self._update_preview()

    def _update_edit_info(self):
        if self.pending is None:
            self.lbl_edit_info.config(text=t("Aucune plage sélectionnée."), foreground="gray")
            return
        i0, i1 = self.pending
        self.lbl_edit_info.config(
            text=t(
                "Plage ajustée : {start} → {end} s ({points} points de mesure)",
                start=f"{self.x[i0]:.6f}", end=f"{self.x[i1]:.6f}",
                points=i1 - i0 + 1,
            ),
            foreground="gray",
        )

    def _validated_pending(self, skip_idx=None):
        """Retourne (i0, i1) si la zone en édition est valide, sinon None (avec message)."""
        if self.pending is None:
            messagebox.showinfo(
                t("Zone"),
                t(
                    "Définissez d'abord une plage : cliquez-glissez sur le graphique "
                    "ou saisissez les bornes."
                ),
                parent=self,
            )
            return None
        i0, i1 = self.pending
        for j, zone in enumerate(self.zones):
            if j == skip_idx:
                continue
            j0, j1 = self._zone_indices(zone)
            if i0 < j1 and i1 > j0:
                messagebox.showwarning(
                    t("Chevauchement"),
                    t(
                        "La plage chevauche la zone {n} [{start} → {end}].",
                        n=j + 1, start=f"{zone[0]:.6f}", end=f"{zone[1]:.6f}",
                    ),
                    parent=self,
                )
                return None
        return i0, i1

    def _commit_zone(self, zone, replace_idx=None):
        if replace_idx is not None:
            self.zones[replace_idx] = zone
        else:
            self.zones.append(zone)
        self.zones.sort(key=lambda z: z[0])
        self.selected_idx = self.zones.index(zone)
        self.pending = self._zone_indices(zone)
        self._refresh_table()
        self._update_edit_info()
        self._update_preview()

    def _add_zone(self):
        v = self._validated_pending(skip_idx=None)
        if v is None:
            return
        i0, i1 = v
        self._commit_zone((float(self.x[i0]), float(self.x[i1]), self.zone_type_var.get()))

    def _apply_zone(self):
        if self.selected_idx is None or self.selected_idx >= len(self.zones):
            return
        v = self._validated_pending(skip_idx=self.selected_idx)
        if v is None:
            return
        i0, i1 = v
        self._commit_zone(
            (float(self.x[i0]), float(self.x[i1]), self.zone_type_var.get()),
            replace_idx=self.selected_idx,
        )

    # ------------------------------------------------------------------
    # Prévisualisation
    # ------------------------------------------------------------------

    def _update_preview(self):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        n = len(self.x)
        times = np.linspace(self.x[0], self.x[-1], int(min(3000, max(300, 10 * n))))
        s = self.sign
        title_parts = []
        errors = []

        ax.plot(self.x, s * self.y, "o", markersize=3, color="C0", alpha=0.8,
                label=t("Mesures"), zorder=4)

        try:
            y_ref = self._interp(times, [])
            ax.plot(times, s * y_ref, "-", color="black", linewidth=1.2, alpha=0.35,
                    label=t("Sans zone"), zorder=1)
            title_parts.append(t(
                "Sans zone : {error}",
                error=format_error_text(
                    compute_interpolation_error(self.df, times, y_ref)
                ),
            ))
        except Exception as e:
            errors.append(t("référence : {error}", error=e))

        if self.zones:
            try:
                y_z = self._interp(times, self.zones)
                ax.plot(times, s * y_z, "-", color="C1", linewidth=2.2,
                        label=t("Avec {n} zone(s)", n=len(self.zones)), zorder=2)
                title_parts.append(t(
                    "Avec zones : {error}",
                    error=format_error_text(
                        compute_interpolation_error(self.df, times, y_z)
                    ),
                ))
            except Exception as e:
                errors.append(t("zones : {error}", error=e))

        pending_zone = None
        if self.pending is not None:
            i0, i1 = self.pending
            pending_zone = (float(self.x[i0]), float(self.x[i1]), self.zone_type_var.get())
            preview_zones = [z for j, z in enumerate(self.zones) if j != self.selected_idx]
            preview_zones.append(pending_zone)
            try:
                y_p = self._interp(times, preview_zones)
                ax.plot(times, s * y_p, "--", color=PENDING_COLOR, linewidth=1.8,
                        label=t("Aperçu avec la zone en édition"), zorder=3)
            except Exception as e:
                errors.append(t("aperçu : {error}", error=e))

        for j, (t0, t1, zt) in enumerate(self.zones):
            color = ZONE_COLORS.get(zt, "gray")
            is_selected = (j == self.selected_idx)
            ax.axvspan(t0, t1, color=color, alpha=0.30 if is_selected else 0.12, linewidth=0)
            ax.text((t0 + t1) / 2, 0.98, str(j + 1), transform=ax.get_xaxis_transform(),
                    ha="center", va="top", fontsize=8, color=color)
        if pending_zone is not None:
            ax.axvspan(pending_zone[0], pending_zone[1], facecolor="none",
                       edgecolor=PENDING_COLOR, hatch="//", alpha=0.5, linewidth=1.2)

        ax.set_xlabel(t("Temps (s)"))
        ax.set_ylabel(t("Valeur"))
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8, loc="best")
        if title_parts:
            ax.set_title("\n".join(title_parts), fontsize=9)
        if errors:
            self.lbl_status.config(
                text=t("Erreur : ") + " | ".join(errors), foreground="red"
            )
        else:
            self.lbl_status.config(
                text=t("{n} zone(s) définie(s)", n=len(self.zones)), foreground="gray"
            )

        self.fig.tight_layout()

        if self._span is not None:
            self._span.disconnect_events()
        self._span = self._make_span_selector(ax)
        self.canvas.draw_idle()

    def _make_span_selector(self, ax):
        """Crée le sélecteur de plage (compatible matplotlib >= 3.4)."""
        style = dict(alpha=0.2, facecolor=PENDING_COLOR)
        try:
            return SpanSelector(
                ax, self._on_span_select, "horizontal", useblit=False,
                props=style, interactive=False,
            )
        except TypeError:
            # matplotlib < 3.5 : ancien nom d'argument
            return SpanSelector(
                ax, self._on_span_select, "horizontal", useblit=False,
                rectprops=style,
            )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _on_ok(self):
        self.result = sorted(self.zones, key=lambda z: z[0])
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.destroy()
