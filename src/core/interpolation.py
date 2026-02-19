"""
Module d'interpolation et de lissage des données

Ce module fournit plusieurs méthodes d'interpolation pour lisser les données
de conditions aux limites destinées aux simulations CFD (Ansys Fluent).

Méthodes disponibles :
- PCHIP : Interpolation exacte monotone
- Spline lissée : Contrôle du lissage via paramètre s
- Trend Filtering : Lissage global robuste anti-oscillations (recommandé pour CFD)
- Linéaire : Segments droits entre les points
"""

import numpy as np
import pandas as pd
from scipy.interpolate import UnivariateSpline, PchipInterpolator, Akima1DInterpolator
from scipy.signal import savgol_filter
from scipy.optimize import minimize
from scipy.sparse import diags, csc_matrix
from scipy.sparse.linalg import spsolve
from typing import Tuple, Optional

from core.constants import MIN_POINTS_REQUIRED, SPLINE_DEGREE, DEFAULT_FLOW_EPS, DEFAULT_SAVGOL_WINDOW, DEFAULT_SAVGOL_POLYORDER, DEFAULT_TREND_LAMBDA


# =============================================================================
# MÉTHODES D'INTERPOLATION ANTI-OSCILLATIONS POUR CFD
# =============================================================================

def _apply_padding(x: np.ndarray, y: np.ndarray, n_pad: int = 3,
                   method: str = "linear") -> Tuple[np.ndarray, np.ndarray, int, int]:
    """
    Applique un padding intelligent aux extrémités pour stabiliser l'interpolation.

    Args:
        x: Array des temps (non-uniforme accepté)
        y: Array des valeurs
        n_pad: Nombre de points de padding de chaque côté
        method: Méthode de padding ("linear", "constant", "reflect")

    Returns:
        Tuple (x_padded, y_padded, n_left, n_right)
    """
    if n_pad <= 0:
        return x, y, 0, 0

    dx_start = np.mean(np.diff(x[:min(3, len(x))]))
    dx_end = np.mean(np.diff(x[-min(3, len(x)):]))

    x_left = []
    y_left = []
    x_right = []
    y_right = []

    if method == "linear":
        if len(x) >= 2:
            slope_start = (y[1] - y[0]) / (x[1] - x[0]) if x[1] != x[0] else 0
            slope_start = np.clip(slope_start, -abs(y[0]) * 10, abs(y[0]) * 10) if y[0] != 0 else slope_start

            for i in range(n_pad, 0, -1):
                x_new = x[0] - i * dx_start
                y_new = y[0] - i * dx_start * slope_start
                x_left.append(x_new)
                y_left.append(y_new)

            slope_end = (y[-1] - y[-2]) / (x[-1] - x[-2]) if x[-1] != x[-2] else 0
            slope_end = np.clip(slope_end, -abs(y[-1]) * 10, abs(y[-1]) * 10) if y[-1] != 0 else slope_end

            for i in range(1, n_pad + 1):
                x_new = x[-1] + i * dx_end
                y_new = y[-1] + i * dx_end * slope_end
                x_right.append(x_new)
                y_right.append(y_new)

    elif method == "constant":
        for i in range(n_pad, 0, -1):
            x_left.append(x[0] - i * dx_start)
            y_left.append(y[0])

        for i in range(1, n_pad + 1):
            x_right.append(x[-1] + i * dx_end)
            y_right.append(y[-1])

    elif method == "reflect":
        for i in range(n_pad, 0, -1):
            idx = min(i, len(x) - 1)
            x_left.append(x[0] - (x[idx] - x[0]))
            y_left.append(2 * y[0] - y[idx])

        for i in range(1, n_pad + 1):
            idx = max(len(x) - 1 - i, 0)
            x_right.append(x[-1] + (x[-1] - x[idx]))
            y_right.append(2 * y[-1] - y[idx])

    x_padded = np.concatenate([x_left, x, x_right])
    y_padded = np.concatenate([y_left, y, y_right])

    return x_padded, y_padded, len(x_left), len(x_right)


def _build_difference_matrix(n: int, order: int = 2) -> np.ndarray:
    """
    Construit la matrice de différences finies d'ordre donné.

    Args:
        n: Nombre de points
        order: Ordre de la différence (1 ou 2)

    Returns:
        Matrice de différences (n-order) x n
    """
    if order == 1:
        diagonals = [-np.ones(n-1), np.ones(n-1)]
        return diags(diagonals, [0, 1], shape=(n-1, n)).toarray()
    elif order == 2:
        diagonals = [np.ones(n-2), -2*np.ones(n-2), np.ones(n-2)]
        return diags(diagonals, [0, 1, 2], shape=(n-2, n)).toarray()
    else:
        raise ValueError(f"Ordre {order} non supporté")


def _trend_filter_l2(y: np.ndarray, x: np.ndarray, lambda_param: float,
                     order: int = 2) -> np.ndarray:
    """
    Trend Filtering avec pénalité L2 (Ridge) sur les différences.

    Résout : min_z ||y - z||_2^2 + lambda * ||D^(order) z||_2^2

    Args:
        y: Valeurs à lisser
        x: Points temporels
        lambda_param: Paramètre de régularisation (plus grand = plus lisse)
        order: Ordre du trend filtering (1 ou 2)

    Returns:
        Valeurs lissées
    """
    n = len(y)
    if n < order + 2:
        return y.copy()

    D = _build_difference_matrix(n, order)

    I = np.eye(n)
    DTD = D.T @ D

    A = I + lambda_param * DTD

    z = np.linalg.solve(A, y)

    return z


def _trend_filter_l1(y: np.ndarray, x: np.ndarray, lambda_param: float,
                     order: int = 2, max_iter: int = 100, tol: float = 1e-6) -> np.ndarray:
    """
    Trend Filtering avec pénalité L1 (Total Variation) via ADMM.

    Résout : min_z ||y - z||_2^2 + lambda * ||D^(order) z||_1

    Args:
        y: Valeurs à lisser
        x: Points temporels
        lambda_param: Paramètre de régularisation
        order: Ordre du trend filtering
        max_iter: Nombre maximum d'itérations ADMM
        tol: Tolérance de convergence

    Returns:
        Valeurs lissées
    """
    n = len(y)
    if n < order + 2:
        return y.copy()

    D = _build_difference_matrix(n, order)

    rho = max(1.0, lambda_param)

    z = y.copy()
    u = np.zeros(n - order)
    w = np.zeros(n - order)

    I = np.eye(n)
    DTD = D.T @ D
    A = I + rho * DTD

    try:
        L = np.linalg.cholesky(A)
        use_cholesky = True
    except np.linalg.LinAlgError:
        use_cholesky = False
        A_inv = np.linalg.inv(A)

    for iteration in range(max_iter):
        z_old = z.copy()

        rhs = y + rho * D.T @ (w - u)
        if use_cholesky:
            z = np.linalg.solve(L.T, np.linalg.solve(L, rhs))
        else:
            z = A_inv @ rhs

        Dz = D @ z
        v = Dz + u
        threshold = lambda_param / rho
        w = np.sign(v) * np.maximum(np.abs(v) - threshold, 0)

        u = u + Dz - w

        primal_residual = np.linalg.norm(Dz - w)

        if primal_residual < tol * np.sqrt(n):
            break

    return z


def interpolate_trend_filter(df: pd.DataFrame, t_new: np.ndarray,
                            lambda_param: float = 1.0,
                            penalty_type: str = "l2",
                            order: int = 2,
                            use_padding: bool = True,
                            padding_points: int = 3,
                            padding_method: str = "linear",
                            clip_to_data_range: bool = False) -> np.ndarray:
    """
    Interpolation avec Trend Filtering - méthode recommandée pour CFD.

    Args:
        df: DataFrame avec colonnes 'Time_s' et 'Value'
        t_new: Array numpy des temps d'évaluation
        lambda_param: Paramètre de régularisation (0.01 à 100)
        penalty_type: "l2" (Ridge) ou "l1" (Total Variation)
        order: Ordre du filtering (1 ou 2)
        use_padding: Appliquer le padding intelligent aux bords
        padding_points: Nombre de points de padding
        padding_method: Méthode de padding
        clip_to_data_range: Si True, borne les résultats à [min(y), max(y)]

    Returns:
        Array numpy des valeurs interpolées aux points t_new
    """
    x = df["Time_s"].to_numpy()
    y = df["Value"].to_numpy()

    if len(x) < MIN_POINTS_REQUIRED:
        raise ValueError(
            f"Trop peu de points ({len(x)}), minimum {MIN_POINTS_REQUIRED} requis."
        )

    y_min, y_max = np.min(y), np.max(y)

    if use_padding and padding_points > 0:
        actual_padding_method = padding_method
        if padding_method == "linear" and y_min >= 0:
            if len(x) >= 2:
                slope_start = (y[1] - y[0]) / (x[1] - x[0]) if x[1] != x[0] else 0
                if y[0] - padding_points * abs(slope_start) * (x[1] - x[0]) < 0:
                    actual_padding_method = "constant"

        x_work, y_work, n_left, n_right = _apply_padding(
            x, y, padding_points, actual_padding_method
        )
    else:
        x_work, y_work = x, y
        n_left, n_right = 0, 0

    if penalty_type == "l1":
        y_smooth = _trend_filter_l1(y_work, x_work, lambda_param, order)
    else:
        y_smooth = _trend_filter_l2(y_work, x_work, lambda_param, order)

    if n_left > 0 or n_right > 0:
        if n_right > 0:
            y_smooth = y_smooth[n_left:-n_right]
            x_work = x_work[n_left:-n_right]
        else:
            y_smooth = y_smooth[n_left:]
            x_work = x_work[n_left:]

    interpolator = PchipInterpolator(x_work, y_smooth, extrapolate=True)
    result = interpolator(t_new)

    if clip_to_data_range:
        result = np.clip(result, y_min, y_max)

    return result


def compute_smoothness_metrics(x: np.ndarray, y: np.ndarray) -> dict:
    """
    Calcule des métriques de "violence" d'une courbe pour diagnostic CFD.

    Args:
        x: Array des temps
        y: Array des valeurs

    Returns:
        Dict avec les métriques (max_slope, mean_slope, max_curvature, etc.)
    """
    if len(x) < 3:
        return {
            "max_slope": 0, "mean_slope": 0,
            "max_curvature": 0, "mean_curvature": 0,
            "slope_variation": 0, "severity": 0
        }

    slopes = np.diff(y) / np.diff(x)
    slopes = np.where(np.isfinite(slopes), slopes, 0)

    curvatures = []
    for i in range(len(x) - 2):
        h1 = x[i+1] - x[i]
        h2 = x[i+2] - x[i+1]
        if h1 > 0 and h2 > 0:
            curv = 2 * ((y[i+2] - y[i+1])/h2 - (y[i+1] - y[i])/h1) / (h1 + h2)
            curvatures.append(curv)
    curvatures = np.array(curvatures) if curvatures else np.array([0])
    curvatures = np.where(np.isfinite(curvatures), curvatures, 0)

    max_slope = float(np.max(np.abs(slopes)))
    mean_slope = float(np.mean(np.abs(slopes)))
    max_curvature = float(np.max(np.abs(curvatures)))
    mean_curvature = float(np.mean(np.abs(curvatures)))
    slope_variation = float(np.std(slopes))

    y_range = np.max(y) - np.min(y) if np.max(y) != np.min(y) else 1
    x_range = np.max(x) - np.min(x) if np.max(x) != np.min(x) else 1

    normalized_slope = max_slope * x_range / y_range if y_range > 0 else 0
    normalized_curv = max_curvature * x_range**2 / y_range if y_range > 0 else 0

    severity = min(100, 20 * np.log10(1 + normalized_slope) +
                   30 * np.log10(1 + normalized_curv) +
                   10 * np.log10(1 + slope_variation * x_range / y_range))
    severity = max(0, severity)

    return {
        "max_slope": max_slope,
        "mean_slope": mean_slope,
        "max_curvature": max_curvature,
        "mean_curvature": mean_curvature,
        "slope_variation": slope_variation,
        "severity": float(severity)
    }


# =============================================================================
# FONCTIONS D'INTERPOLATION EXISTANTES
# =============================================================================

def apply_segment_interpolation(t_new: np.ndarray, interpolators: list, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """
    Applique l'interpolation par segments.

    Args:
        t_new: Points d'évaluation
        interpolators: Liste de dicts avec 'start', 'end', 'func'
        x, y: Données brutes (pour fallback)

    Returns:
        Array des valeurs interpolées
    """
    result = np.zeros_like(t_new)
    eps = 1e-10

    for i, t in enumerate(t_new):
        current_seg = None

        for seg in interpolators:
            if seg['start'] - eps <= t <= seg['end'] + eps:
                current_seg = seg
                break

        if current_seg is None:
            result[i] = np.interp(t, x, y)
            continue

        try:
            result[i] = current_seg['func'](t)
        except:
            result[i] = np.interp(t, x, y)

    return result


def interpolate_pchip(df: pd.DataFrame, t_new: np.ndarray) -> np.ndarray:
    """Interpolation exacte avec PCHIP."""
    x = df["Time_s"].to_numpy()
    y = df["Value"].to_numpy()

    if len(x) < MIN_POINTS_REQUIRED:
        raise ValueError(
            f"Trop peu de points ({len(x)}), minimum {MIN_POINTS_REQUIRED} requis."
        )

    interpolator = PchipInterpolator(x, y, extrapolate=True)
    return interpolator(t_new)


def interpolate_with_zones(df: pd.DataFrame, t_new: np.ndarray, method: str = "pchip",
                          smooth_factor: float = 0.01, unfiltered_zones: list = None,
                          trend_lambda: float = 1.0) -> np.ndarray:
    """
    Interpolation SEGMENTÉE avec zones spéciales.

    Fonctionne avec toutes les méthodes (pchip, spline, linear, trend_l2, trend_l1).

    Args:
        df: DataFrame avec colonnes 'Time_s' et 'Value'
        t_new: Array numpy des temps d'évaluation
        method: Méthode pour les segments globaux
        smooth_factor: Facteur de lissage (pour spline)
        unfiltered_zones: Liste de tuples (t_start, t_end, type)
        trend_lambda: Paramètre lambda pour trend filtering

    Returns:
        Array numpy des valeurs interpolées
    """
    if method == "spline":
        return interpolate_smooth(df, t_new, smooth_factor, unfiltered_zones)

    x = df["Time_s"].to_numpy()
    y = df["Value"].to_numpy()

    if len(x) < MIN_POINTS_REQUIRED:
        raise ValueError(f"Trop peu de points ({len(x)}), minimum {MIN_POINTS_REQUIRED} requis.")

    zones_list = []
    for zone in unfiltered_zones:
        if len(zone) == 3:
            t_start, t_end, ztype = zone
        else:
            t_start, t_end = zone
            ztype = "exact"
        zones_list.append((t_start, t_end, ztype))
    zones_list.sort(key=lambda z: z[0])

    zone_boundaries = []
    for t_start, t_end, ztype in zones_list:
        idx_start = np.argmin(np.abs(x - t_start))
        idx_end = np.argmin(np.abs(x - t_end))
        zone_boundaries.append((idx_start, idx_end, t_start, t_end, ztype))

    segments = []
    current_idx = 0

    for idx_start, idx_end, t_start, t_end, ztype in zone_boundaries:
        if current_idx < idx_start:
            segments.append((method + "_global", current_idx, idx_start - 1))
        segments.append((ztype + "_zone", idx_start, idx_end))
        current_idx = idx_end + 1

    if current_idx < len(x):
        segments.append((method + "_global", current_idx, len(x) - 1))

    interpolators = []

    for seg_type, idx_start, idx_end in segments:
        idx_end_incl = min(idx_end, len(x) - 1)

        x_seg = x[idx_start:idx_end_incl+1]
        y_seg = y[idx_start:idx_end_incl+1]

        if len(x_seg) < 2:
            continue

        seg_t_start = x_seg[0]
        seg_t_end = x_seg[-1]

        if seg_type == "pchip_global" or seg_type == "exact_zone":
            if len(x_seg) >= 2:
                interp = PchipInterpolator(x_seg, y_seg, extrapolate=False)
            else:
                interp = lambda t, val=y_seg[0]: val

        elif seg_type == "linear_global":
            if len(x_seg) >= 2:
                interp = lambda t, xs=x_seg.copy(), ys=y_seg.copy(): np.interp(t, xs, ys)
            else:
                interp = lambda t, val=y_seg[0]: val

        elif seg_type == "linear_zone":
            t1, y1 = x_seg[0], y_seg[0]
            t2, y2 = x_seg[-1], y_seg[-1]

            if t2 != t1:
                interp = lambda t, t1=t1, y1=y1, t2=t2, y2=y2: y1 + (y2 - y1) * (t - t1) / (t2 - t1)
            else:
                interp = lambda t, y1=y1: y1

        elif seg_type in ["trend_l2_global", "trend_l1_global"]:
            if len(x_seg) >= MIN_POINTS_REQUIRED:
                penalty_type = "l2" if "l2" in seg_type else "l1"
                if penalty_type == "l2":
                    y_smooth = _trend_filter_l2(y_seg, x_seg, trend_lambda, order=2)
                else:
                    y_smooth = _trend_filter_l1(y_seg, x_seg, trend_lambda, order=2)
                interp = PchipInterpolator(x_seg, y_smooth, extrapolate=False)
            elif len(x_seg) >= 2:
                interp = PchipInterpolator(x_seg, y_seg, extrapolate=False)
            else:
                interp = lambda t, val=y_seg[0]: val

        else:
            if len(x_seg) >= 2:
                interp = PchipInterpolator(x_seg, y_seg, extrapolate=False)
            else:
                interp = lambda t, val=y_seg[0]: val

        interpolators.append({
            'type': seg_type,
            'start': seg_t_start,
            'end': seg_t_end,
            'func': interp
        })

    result = apply_segment_interpolation(t_new, interpolators, x, y)
    return result


def interpolate_smooth(df: pd.DataFrame, t_new: np.ndarray, smooth_factor: float = 0.01, unfiltered_zones: list = None) -> np.ndarray:
    """Interpolation lissée avec spline cubique SEGMENTÉE."""
    x = df["Time_s"].to_numpy()
    y = df["Value"].to_numpy()

    if len(x) < MIN_POINTS_REQUIRED:
        raise ValueError(f"Trop peu de points ({len(x)}), minimum {MIN_POINTS_REQUIRED} requis.")

    if unfiltered_zones is None or len(unfiltered_zones) == 0:
        n = len(x)
        rng = float(np.max(y) - np.min(y))
        s = 0.0 if (smooth_factor <= 0 or rng == 0) else n * (smooth_factor * rng) ** 2
        spl = UnivariateSpline(x, y, k=SPLINE_DEGREE, s=s)
        return spl(t_new)

    zones_list = []
    for zone in unfiltered_zones:
        if len(zone) == 3:
            t_start, t_end, ztype = zone
        else:
            t_start, t_end = zone
            ztype = "exact"
        zones_list.append((t_start, t_end, ztype))
    zones_list.sort(key=lambda z: z[0])

    zone_boundaries = []
    for t_start, t_end, ztype in zones_list:
        idx_start = np.argmin(np.abs(x - t_start))
        idx_end = np.argmin(np.abs(x - t_end))
        zone_boundaries.append((idx_start, idx_end, t_start, t_end, ztype))

    segments = []
    current_idx = 0

    for idx_start, idx_end, t_start, t_end, ztype in zone_boundaries:
        if current_idx < idx_start:
            segments.append(('global', current_idx, idx_start - 1))
        segments.append((ztype, idx_start, idx_end))
        current_idx = idx_end + 1

    if current_idx < len(x):
        segments.append(('global', current_idx, len(x) - 1))

    interpolators = []

    for seg_type, idx_start, idx_end in segments:
        idx_end_incl = min(idx_end, len(x) - 1)

        x_seg = x[idx_start:idx_end_incl+1]
        y_seg = y[idx_start:idx_end_incl+1]

        if len(x_seg) < 2:
            continue

        seg_t_start = x_seg[0]
        seg_t_end = x_seg[-1]

        if seg_type == 'global':
            if len(x_seg) >= MIN_POINTS_REQUIRED:
                n_seg = len(x_seg)
                rng_seg = float(np.max(y_seg) - np.min(y_seg)) if len(y_seg) > 1 else 1.0
                s_seg = 0.0 if rng_seg == 0 else n_seg * (smooth_factor * rng_seg) ** 2
                interp = UnivariateSpline(x_seg, y_seg, k=min(3, len(x_seg)-1), s=s_seg)
            elif len(x_seg) >= 2:
                interp = PchipInterpolator(x_seg, y_seg, extrapolate=False)
            else:
                interp = lambda t, val=y_seg[0]: val

        elif seg_type == 'exact':
            if len(x_seg) >= 2:
                interp = PchipInterpolator(x_seg, y_seg, extrapolate=False)
            else:
                interp = lambda t, val=y_seg[0]: val

        elif seg_type == 'linear':
            t1, y1 = x_seg[0], y_seg[0]
            t2, y2 = x_seg[-1], y_seg[-1]

            if t2 != t1:
                interp = lambda t, t1=t1, y1=y1, t2=t2, y2=y2: y1 + (y2 - y1) * (t - t1) / (t2 - t1)
            else:
                interp = lambda t, y1=y1: y1

        interpolators.append({
            'type': seg_type,
            'start': seg_t_start,
            'end': seg_t_end,
            'func': interp
        })

    result = apply_segment_interpolation(t_new, interpolators, x, y)
    return result


def interpolate_trend(
    df: pd.DataFrame,
    t_new: np.ndarray,
    lambda_param: float = 1.0,
    method: str = "trend_l2",
    use_padding: bool = True,
    padding_points: int = 3
) -> np.ndarray:
    """Interpolation avec lissage Trend Filtering."""
    if len(df) < MIN_POINTS_REQUIRED:
        raise ValueError(
            f"Trop peu de points ({len(df)}), minimum {MIN_POINTS_REQUIRED} requis."
        )

    penalty_type = "l1" if method == "trend_l1" else "l2"

    return interpolate_trend_filter(
        df=df,
        t_new=t_new,
        lambda_param=lambda_param,
        penalty_type=penalty_type,
        order=2,
        use_padding=use_padding,
        padding_points=padding_points,
        padding_method="linear"
    )


def interpolate(
    df: pd.DataFrame,
    t_new: np.ndarray,
    method: str = "pchip",
    smooth_factor: float = 0.01,
    unfiltered_zones: list = None,
    trend_lambda: float = 1.0
) -> np.ndarray:
    """
    Interpolation avec choix de la méthode.

    Args:
        df: DataFrame avec colonnes 'Time_s' et 'Value'
        t_new: Array numpy des temps d'évaluation
        method: "pchip", "spline", "linear", "trend_l2", "trend_l1"
        smooth_factor: Facteur de lissage (pour "spline")
        unfiltered_zones: Liste de tuples (t_start, t_end, type) pour zones
        trend_lambda: Paramètre lambda pour trend filtering

    Returns:
        Array numpy des valeurs interpolées
    """
    if unfiltered_zones is None or len(unfiltered_zones) == 0:
        if method == "pchip":
            return interpolate_pchip(df, t_new)
        elif method == "spline":
            return interpolate_smooth(df, t_new, smooth_factor, None)
        elif method == "linear":
            x = df["Time_s"].to_numpy()
            y = df["Value"].to_numpy()
            return np.interp(t_new, x, y)
        elif method in ["trend_l2", "trend_l1"]:
            return interpolate_trend(df, t_new, lambda_param=trend_lambda, method=method)
        else:
            return interpolate_pchip(df, t_new)

    if method in ["trend_l2", "trend_l1"]:
        return interpolate_with_zones(df, t_new, method, smooth_factor, unfiltered_zones, trend_lambda)

    return interpolate_with_zones(df, t_new, method, smooth_factor, unfiltered_zones)


# =============================================================================
# Utilitaires
# =============================================================================

def sanitize_flow(values: np.ndarray, flow_eps: float = DEFAULT_FLOW_EPS) -> Tuple[np.ndarray, int]:
    """Remplace les valeurs nulles par flow_eps pour éviter les divergences dans Fluent."""
    result = values.astype(np.float64)
    zero_mask = (result == 0.0)
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
    unfiltered_zones: dict = None,
    inlet_names: dict = None,
    trend_lambda_params: dict = None,
    inverted: dict = None
) -> dict:
    """
    Interpole toutes les données avec les paramètres spécifiés par courbe.

    Args:
        data_raw: Dictionnaire {clé: DataFrame}
        times: Array des temps d'évaluation
        methods: Dict {key: method}
        smooth_params: Dict {key: smooth_factor}
        flow_eps: Valeur de remplacement pour les débits nuls
        unfiltered_zones: Dict {key: [(t_start, t_end), ...]}
        inlet_names: Dictionnaire {"inlet1": "nom1", ...}
        trend_lambda_params: Dict {key: lambda_value}
        inverted: Dict {key: bool} - courbes à inverser (coefficient ×-1)

    Returns:
        Dictionnaire {clé_renommée: array_interpolé}
    """
    result = {}

    if inlet_names is None:
        inlet_names = {}
    if unfiltered_zones is None:
        unfiltered_zones = {}
    if trend_lambda_params is None:
        trend_lambda_params = {}
    if inverted is None:
        inverted = {}

    for key, df in data_raw.items():
        method = methods.get(key, "spline")
        smooth = smooth_params.get(key, 0.01)
        trend_lambda = trend_lambda_params.get(key, DEFAULT_TREND_LAMBDA)
        zones_for_key = unfiltered_zones.get(key, [])

        interp = interpolate(
            df,
            times,
            method=method,
            smooth_factor=smooth,
            unfiltered_zones=zones_for_key,
            trend_lambda=trend_lambda
        )

        # Appliquer l'inversion si activée
        if inverted.get(key, False):
            interp = interp * -1.0

        if key.startswith("Q_"):
            interp, n_replaced = sanitize_flow(interp, flow_eps)
            if n_replaced > 0:
                print(f"{key}: {n_replaced} valeurs nulles remplacées par {flow_eps}")

        new_key = key
        for old_name, new_name in inlet_names.items():
            new_key = new_key.replace(old_name, new_name)

        result[new_key] = interp

    return result
