"""
Module d'interpolation et de lissage des données
"""

import numpy as np
import pandas as pd
from scipy.interpolate import UnivariateSpline, PchipInterpolator, Akima1DInterpolator
from scipy.signal import savgol_filter
from typing import Tuple, List, Optional

from core.constants import (
    MIN_POINTS_REQUIRED, SPLINE_DEGREE, DEFAULT_FLOW_EPS,
    DEFAULT_SAVGOL_WINDOW, DEFAULT_SAVGOL_POLYORDER,
)


# ---------------------------------------------------------------------------
# Méthodes d'interpolation simples (sans zones)
# ---------------------------------------------------------------------------

def interpolate_pchip(df: pd.DataFrame, t_new: np.ndarray) -> np.ndarray:
    """
    Interpolation exacte avec PCHIP (Piecewise Cubic Hermite Interpolating Polynomial).

    PCHIP garantit :
    - Passage par tous les points de données
    - Monotonie préservée
    - Continuité de la dérivée première
    """
    x = df["Time_s"].to_numpy()
    y = df["Value"].to_numpy()

    if len(x) < MIN_POINTS_REQUIRED:
        raise ValueError(
            f"Trop peu de points ({len(x)}), minimum {MIN_POINTS_REQUIRED} requis."
        )

    interpolator = PchipInterpolator(x, y, extrapolate=True)
    return interpolator(t_new)


def interpolate_akima(df: pd.DataFrame, t_new: np.ndarray) -> np.ndarray:
    """Interpolation Akima (cubique locale minimisant les oscillations)."""
    x = df["Time_s"].to_numpy()
    y = df["Value"].to_numpy()

    if len(x) < 5:
        return interpolate_pchip(df, t_new)

    interpolator = Akima1DInterpolator(x, y)
    return interpolator(t_new)


def interpolate_makima(df: pd.DataFrame, t_new: np.ndarray) -> np.ndarray:
    """Interpolation Makima (Modified Akima, robuste aux valeurs aberrantes)."""
    x = df["Time_s"].to_numpy()
    y = df["Value"].to_numpy()

    if len(x) < 5:
        return interpolate_pchip(df, t_new)

    try:
        interpolator = Akima1DInterpolator(x, y, method="makima")
    except TypeError:
        # Fallback si cette version de scipy ne supporte pas method="makima"
        interpolator = Akima1DInterpolator(x, y)

    return interpolator(t_new)


def interpolate_savgol(
    df: pd.DataFrame,
    t_new: np.ndarray,
    window_length: int = DEFAULT_SAVGOL_WINDOW,
    polyorder: int = DEFAULT_SAVGOL_POLYORDER,
) -> np.ndarray:
    """Filtrage Savitzky-Golay suivi d'une interpolation PCHIP."""
    x = df["Time_s"].to_numpy()
    y = df["Value"].to_numpy()

    if len(x) < window_length:
        return interpolate_pchip(df, t_new)

    # Assurer que window_length est impair et > polyorder
    if window_length % 2 == 0:
        window_length += 1
    if window_length <= polyorder:
        window_length = polyorder + 2
        if window_length % 2 == 0:
            window_length += 1

    y_filtered = savgol_filter(y, window_length, polyorder)
    interpolator = PchipInterpolator(x, y_filtered, extrapolate=True)
    return interpolator(t_new)


def _interpolate_simple_spline(
    x: np.ndarray, y: np.ndarray, t_new: np.ndarray, smooth_factor: float
) -> np.ndarray:
    """Interpolation spline cubique simple (sans zones)."""
    n = len(x)
    rng = float(np.max(y) - np.min(y))
    s = 0.0 if (smooth_factor <= 0 or rng == 0) else n * (smooth_factor * rng) ** 2
    spl = UnivariateSpline(x, y, k=SPLINE_DEGREE, s=s)
    return spl(t_new)


# ---------------------------------------------------------------------------
# Création d'interpolateurs par segment
# ---------------------------------------------------------------------------

def _make_segment_interpolator(
    seg_type: str,
    x_seg: np.ndarray,
    y_seg: np.ndarray,
    method: str,
    smooth_factor: float,
):
    """
    Crée un interpolateur callable pour un segment donné.

    Args:
        seg_type: "global" ou type de zone ("exact", "linear")
        x_seg, y_seg: données du segment
        method: méthode globale (pour segments "global")
        smooth_factor: facteur de lissage (pour spline)

    Returns:
        callable(t) -> valeur interpolée
    """
    if len(x_seg) < 2:
        val = y_seg[0] if len(y_seg) > 0 else 0.0
        return lambda t, v=val: np.full_like(np.atleast_1d(t), v, dtype=float)

    # --- Zones spéciales ---
    if seg_type == "exact":
        interp = PchipInterpolator(x_seg, y_seg, extrapolate=False)
        return lambda t, f=interp: f(t)

    if seg_type == "linear":
        t1, y1 = x_seg[0], y_seg[0]
        t2, y2 = x_seg[-1], y_seg[-1]
        if t2 != t1:
            return lambda t, _t1=t1, _y1=y1, _t2=t2, _y2=y2: _y1 + (_y2 - _y1) * (t - _t1) / (_t2 - _t1)
        return lambda t, v=y1: np.full_like(np.atleast_1d(t), v, dtype=float)

    # --- Segments globaux ---
    if method == "pchip":
        interp = PchipInterpolator(x_seg, y_seg, extrapolate=False)
        return lambda t, f=interp: f(t)

    if method == "spline":
        if len(x_seg) >= MIN_POINTS_REQUIRED:
            n_seg = len(x_seg)
            rng_seg = float(np.max(y_seg) - np.min(y_seg)) if n_seg > 1 else 1.0
            s_seg = 0.0 if rng_seg == 0 else n_seg * (smooth_factor * rng_seg) ** 2
            interp = UnivariateSpline(x_seg, y_seg, k=min(3, len(x_seg) - 1), s=s_seg)
            return lambda t, f=interp: f(t)
        interp = PchipInterpolator(x_seg, y_seg, extrapolate=False)
        return lambda t, f=interp: f(t)

    if method == "linear":
        xs, ys = x_seg.copy(), y_seg.copy()
        return lambda t, _xs=xs, _ys=ys: np.interp(np.atleast_1d(t), _xs, _ys)

    if method == "akima":
        if len(x_seg) >= 5:
            interp = Akima1DInterpolator(x_seg, y_seg)
            return lambda t, f=interp: f(t)
        interp = PchipInterpolator(x_seg, y_seg, extrapolate=False)
        return lambda t, f=interp: f(t)

    if method == "makima":
        if len(x_seg) >= 5:
            try:
                interp = Akima1DInterpolator(x_seg, y_seg, method="makima")
            except TypeError:
                interp = Akima1DInterpolator(x_seg, y_seg)
            return lambda t, f=interp: f(t)
        interp = PchipInterpolator(x_seg, y_seg, extrapolate=False)
        return lambda t, f=interp: f(t)

    if method == "savgol":
        wl = DEFAULT_SAVGOL_WINDOW
        po = DEFAULT_SAVGOL_POLYORDER
        if len(x_seg) >= wl:
            if wl % 2 == 0:
                wl += 1
            y_filt = savgol_filter(y_seg, wl, po)
        else:
            y_filt = y_seg
        interp = PchipInterpolator(x_seg, y_filt, extrapolate=False)
        return lambda t, f=interp: f(t)

    # Fallback: PCHIP
    interp = PchipInterpolator(x_seg, y_seg, extrapolate=False)
    return lambda t, f=interp: f(t)


# ---------------------------------------------------------------------------
# Interpolation segmentée unifiée (avec zones)
# ---------------------------------------------------------------------------

def _build_segments(
    x: np.ndarray, y: np.ndarray,
    method: str, smooth_factor: float,
    zones: List[tuple],
) -> list:
    """
    Construit la liste des segments interpolateurs à partir des zones.

    Returns:
        Liste de dicts {'start': float, 'end': float, 'func': callable}
    """
    # Parser et trier les zones
    zones_parsed = []
    for zone in zones:
        if len(zone) == 3:
            t_start, t_end, ztype = zone
        else:
            t_start, t_end = zone
            ztype = "exact"
        zones_parsed.append((t_start, t_end, ztype))
    zones_parsed.sort(key=lambda z: z[0])

    # Trouver les indices de borne pour chaque zone
    zone_boundaries = []
    for t_start, t_end, ztype in zones_parsed:
        idx_start = int(np.argmin(np.abs(x - t_start)))
        idx_end = int(np.argmin(np.abs(x - t_end)))
        zone_boundaries.append((idx_start, idx_end, ztype))

    # Créer les segments (indices)
    raw_segments = []
    current_idx = 0

    for idx_start, idx_end, ztype in zone_boundaries:
        if current_idx < idx_start:
            raw_segments.append(("global", current_idx, idx_start - 1))
        raw_segments.append((ztype, idx_start, idx_end))
        current_idx = idx_end + 1

    if current_idx < len(x):
        raw_segments.append(("global", current_idx, len(x) - 1))

    # Construire les interpolateurs
    interpolators = []
    for seg_type, idx_s, idx_e in raw_segments:
        idx_e = min(idx_e, len(x) - 1)
        x_seg = x[idx_s:idx_e + 1]
        y_seg = y[idx_s:idx_e + 1]

        if len(x_seg) < 2:
            continue

        func = _make_segment_interpolator(seg_type, x_seg, y_seg, method, smooth_factor)
        interpolators.append({
            "start": x_seg[0],
            "end": x_seg[-1],
            "func": func,
        })

    return interpolators


def _apply_hermite_transitions(
    t_new: np.ndarray,
    interpolators: list,
    x: np.ndarray,
    y: np.ndarray,
    transition_ratio: float = 0.02,
) -> np.ndarray:
    """
    Interpole t_new segment par segment avec transitions Hermite C1 aux jonctions.

    Vectorisé par segment pour de meilleures performances.
    """
    result = np.interp(t_new, x, y)  # fallback par défaut
    eps = 1e-10

    if not interpolators:
        return result

    # Pré-calculer les zones de transition pour chaque jonction
    n_seg = len(interpolators)
    transitions = []  # (junction_t, trans_start, trans_end, seg_idx_prev, seg_idx_next)

    for k in range(n_seg - 1):
        seg_curr = interpolators[k]
        seg_next = interpolators[k + 1]
        junction_t = seg_next["start"]
        seg_width = seg_curr["end"] - seg_curr["start"]
        tw = max(transition_ratio * seg_width, eps * 100)
        trans_start = junction_t - tw
        trans_end = junction_t + eps
        transitions.append((junction_t, trans_start, trans_end, tw, k, k + 1))

    # Remplir segment par segment (vectorisé)
    for idx, seg in enumerate(interpolators):
        mask = (t_new >= seg["start"] - eps) & (t_new <= seg["end"] + eps)
        if not np.any(mask):
            continue
        t_seg = t_new[mask]
        try:
            vals = np.atleast_1d(seg["func"](t_seg))
            result[mask] = vals
        except Exception:
            pass  # garde le fallback linéaire

    # Appliquer les transitions Hermite aux jonctions
    for junction_t, trans_start, trans_end, tw, idx_prev, idx_next in transitions:
        mask = (t_new >= trans_start) & (t_new <= trans_end + eps)
        if not np.any(mask):
            continue

        t_trans = t_new[mask]
        seg_prev = interpolators[idx_prev]
        seg_next = interpolators[idx_next]

        try:
            t_norm = np.clip((t_trans - trans_start) / tw, 0.0, 1.0)

            # Valeurs aux bords
            v_prev = np.atleast_1d(seg_prev["func"](t_trans))
            v_next_at_junction = float(np.atleast_1d(seg_next["func"](junction_t + eps))[0])

            # Dérivées par différences finies
            dt_deriv = tw * 0.01
            if junction_t - dt_deriv >= seg_prev["start"]:
                v_before = np.atleast_1d(seg_prev["func"](junction_t - dt_deriv))
                v_at = np.atleast_1d(seg_prev["func"](junction_t - eps))
                d_prev = float(((v_at - v_before) / dt_deriv)[0])
            else:
                d_prev = 0.0

            if junction_t + dt_deriv <= seg_next["end"]:
                v_after = np.atleast_1d(seg_next["func"](junction_t + dt_deriv))
                d_next = float(((v_after - v_next_at_junction) / dt_deriv)[0])
            else:
                d_next = 0.0

            # Hermite cubique (vectorisé)
            t2 = t_norm * t_norm
            t3 = t2 * t_norm
            h00 = 2 * t3 - 3 * t2 + 1
            h10 = t3 - 2 * t2 + t_norm
            h01 = -2 * t3 + 3 * t2
            h11 = t3 - t2

            result[mask] = (
                h00 * v_prev
                + h10 * d_prev * tw
                + h01 * v_next_at_junction
                + h11 * d_next * tw
            )
        except Exception:
            pass  # garde les valeurs déjà calculées

    return result


def _interpolate_segmented(
    df: pd.DataFrame,
    t_new: np.ndarray,
    method: str,
    smooth_factor: float,
    zones: list,
    transition_ratio: float = 0.02,
) -> np.ndarray:
    """
    Interpolation segmentée unifiée. Gère toutes les méthodes avec zones.
    """
    x = df["Time_s"].to_numpy()
    y = df["Value"].to_numpy()

    if len(x) < MIN_POINTS_REQUIRED:
        raise ValueError(
            f"Trop peu de points ({len(x)}), minimum {MIN_POINTS_REQUIRED} requis."
        )

    interpolators = _build_segments(x, y, method, smooth_factor, zones)
    return _apply_hermite_transitions(t_new, interpolators, x, y, transition_ratio)


# ---------------------------------------------------------------------------
# Point d'entrée principal
# ---------------------------------------------------------------------------

def interpolate(
    df: pd.DataFrame,
    t_new: np.ndarray,
    method: str = "pchip",
    smooth_factor: float = 0.01,
    unfiltered_zones: Optional[list] = None,
    savgol_window: int = DEFAULT_SAVGOL_WINDOW,
    savgol_polyorder: int = DEFAULT_SAVGOL_POLYORDER,
    transition_ratio: float = 0.02,
) -> np.ndarray:
    """
    Interpolation avec choix de la méthode.

    Args:
        df: DataFrame avec colonnes 'Time_s' et 'Value'
        t_new: Array numpy des temps d'évaluation
        method: "pchip", "spline", "linear", "akima", "makima", "savgol"
        smooth_factor: Facteur de lissage (pour "spline")
        unfiltered_zones: Liste de tuples (t_start, t_end, type) pour zones
        savgol_window: Taille de fenêtre Savitzky-Golay
        savgol_polyorder: Degré polynomial Savitzky-Golay
        transition_ratio: Ratio de transition Hermite (0.02 = 2%)
    """
    has_zones = unfiltered_zones is not None and len(unfiltered_zones) > 0

    # Avec zones → interpolation segmentée pour toutes les méthodes
    if has_zones:
        return _interpolate_segmented(
            df, t_new, method, smooth_factor, unfiltered_zones, transition_ratio
        )

    # Sans zones → méthode directe
    if method == "pchip":
        return interpolate_pchip(df, t_new)
    if method == "spline":
        x = df["Time_s"].to_numpy()
        y = df["Value"].to_numpy()
        return _interpolate_simple_spline(x, y, t_new, smooth_factor)
    if method == "linear":
        x = df["Time_s"].to_numpy()
        y = df["Value"].to_numpy()
        return np.interp(t_new, x, y)
    if method == "akima":
        return interpolate_akima(df, t_new)
    if method == "makima":
        return interpolate_makima(df, t_new)
    if method == "savgol":
        return interpolate_savgol(df, t_new, savgol_window, savgol_polyorder)

    # Fallback
    return interpolate_pchip(df, t_new)


# ---------------------------------------------------------------------------
# Utilitaires
# ---------------------------------------------------------------------------

def sanitize_flow(values: np.ndarray, flow_eps: float = DEFAULT_FLOW_EPS) -> Tuple[np.ndarray, int]:
    """
    Remplace les valeurs nulles par flow_eps pour éviter les divergences dans Fluent.
    """
    result = values.copy()
    zero_mask = result == 0.0
    n_replaced = int(zero_mask.sum())

    if n_replaced > 0:
        result[zero_mask] = flow_eps

    return result, n_replaced


def generate_time_array(sim_duration: float, dt: float) -> np.ndarray:
    """Génère un array de temps régulièrement espacé."""
    if dt <= 0:
        raise ValueError(f"Le pas de temps doit être > 0, reçu : {dt}")
    if sim_duration <= 0:
        raise ValueError(f"La durée de simulation doit être > 0, reçue : {sim_duration}")

    n_pts = int(sim_duration / dt) + 1
    return np.linspace(0, sim_duration, n_pts)


def interpolate_all_data(
    data_raw: dict,
    times: np.ndarray,
    methods: dict,
    smooth_params: dict,
    flow_eps: float = DEFAULT_FLOW_EPS,
    unfiltered_zones: Optional[dict] = None,
    inlet_names: Optional[dict] = None,
    savgol_params: Optional[dict] = None,
) -> dict:
    """
    Interpole toutes les données avec les paramètres spécifiés par courbe.
    """
    result = {}

    if inlet_names is None:
        inlet_names = {"inlet1": "inlet1", "inlet2": "inlet2"}
    if unfiltered_zones is None:
        unfiltered_zones = {}
    if savgol_params is None:
        savgol_params = {"window": DEFAULT_SAVGOL_WINDOW, "polyorder": DEFAULT_SAVGOL_POLYORDER}

    for key, df in data_raw.items():
        method = methods.get(key, "spline")
        smooth = smooth_params.get(key, 0.01)
        zones_for_key = unfiltered_zones.get(key, [])

        interp = interpolate(
            df,
            times,
            method=method,
            smooth_factor=smooth,
            unfiltered_zones=zones_for_key,
            savgol_window=savgol_params["window"],
            savgol_polyorder=savgol_params["polyorder"],
        )

        # Sanitization pour les débits
        if key.startswith("Q_"):
            interp, _ = sanitize_flow(interp, flow_eps)

        # Renommer la clé selon les noms d'inlet
        new_key = key
        for old_name, new_name in inlet_names.items():
            new_key = new_key.replace(old_name, new_name)

        result[new_key] = interp

    return result
