"""
Module d'interpolation et de lissage des données

Ce module fournit plusieurs méthodes d'interpolation pour lisser les données
de conditions aux limites destinées aux simulations CFD (Ansys Fluent).

Méthodes disponibles :
- PCHIP : Interpolation exacte monotone
- Spline lissée : Contrôle du lissage via paramètre s
- Trend Filtering L2 / L1 : Lissage global robuste anti-oscillations
- Linéaire : Segments droits entre les points

Zones spéciales :
Une zone (t_start, t_end, type) force localement une interpolation "exact"
(PCHIP passant par tous les points) ou "linear" (droite entre les deux bornes).
Les bornes sont ajustées aux points de mesure les plus proches. Les segments
globaux adjacents à une zone sont raccordés en valeur (continuité C0) : la
valeur lissée à la borne partagée est remplacée par la valeur brute.

Garanties :
- Les temps d'évaluation sont bornés à la plage des données (pas
  d'extrapolation polynomiale : prolongement constant).
- Les différences finies du trend filtering tiennent compte de l'espacement
  réel des temps (données non uniformes, points quasi dupliqués).
"""

import numpy as np
import pandas as pd
from scipy.interpolate import UnivariateSpline, PchipInterpolator
from scipy.sparse import diags, identity
from scipy.sparse.linalg import spsolve, splu
from typing import Tuple, List, Optional

from core.constants import (
    MIN_POINTS_REQUIRED, SPLINE_DEGREE, DEFAULT_FLOW_EPS,
    DEFAULT_TREND_LAMBDA, DEFAULT_TREND_PADDING, INTERP_METHODS,
)

ZONE_TYPES = ("exact", "linear")
TREND_METHODS = ("trend_l2", "trend_l1")


# =============================================================================
# Préparation des données
# =============================================================================

def prepare_xy(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extrait (x, y) propres depuis un DataFrame 'Time_s' / 'Value' :
    sans NaN, triés par temps, sans temps dupliqués (premier conservé).
    """
    x = pd.to_numeric(df["Time_s"], errors="coerce").to_numpy(dtype=float)
    y = pd.to_numeric(df["Value"], errors="coerce").to_numpy(dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    x, y = x[mask], y[mask]
    order = np.argsort(x, kind="stable")
    x, y = x[order], y[order]
    if len(x) > 1:
        keep = np.concatenate([[True], np.diff(x) > 0])
        x, y = x[keep], y[keep]
    return x, y


def _check_min_points(n: int, method: str) -> None:
    min_pts = 2 if method == "linear" else MIN_POINTS_REQUIRED
    if n < min_pts:
        raise ValueError(f"Trop peu de points ({n}), minimum {min_pts} requis.")


# =============================================================================
# Trend filtering (L2 / L1) sur grille non uniforme
# =============================================================================

def _apply_padding(x: np.ndarray, y: np.ndarray, n_pad: int = 3,
                   method: str = "linear") -> Tuple[np.ndarray, np.ndarray, int, int]:
    """
    Applique un padding aux extrémités pour stabiliser le lissage aux bords.

    Args:
        x: Array des temps (strictement croissants)
        y: Array des valeurs
        n_pad: Nombre de points de padding de chaque côté
        method: "linear" (prolongement de la pente), "constant" (valeur de bord)

    Returns:
        (x_padded, y_padded, n_left, n_right)
    """
    if n_pad <= 0 or len(x) < 2:
        return x, y, 0, 0

    dx_start = float(np.mean(np.diff(x[:min(3, len(x))])))
    dx_end = float(np.mean(np.diff(x[-min(3, len(x)):])))

    if method == "linear":
        slope_start = (y[1] - y[0]) / (x[1] - x[0])
        slope_end = (y[-1] - y[-2]) / (x[-1] - x[-2])
    else:
        slope_start = 0.0
        slope_end = 0.0

    k = np.arange(n_pad, 0, -1)
    x_left = x[0] - k * dx_start
    y_left = y[0] - k * dx_start * slope_start

    k = np.arange(1, n_pad + 1)
    x_right = x[-1] + k * dx_end
    y_right = y[-1] + k * dx_end * slope_end

    return (np.concatenate([x_left, x, x_right]),
            np.concatenate([y_left, y, y_right]),
            n_pad, n_pad)


def _difference_matrix(x: np.ndarray, order: int = 2):
    """
    Matrice creuse de différences finies d'ordre 1 ou 2 sur grille non uniforme.

    Les coefficients sont normalisés par l'espacement moyen de sorte que, sur
    une grille uniforme, on retrouve exactement (-1, 1) ou (1, -2, 1). Le
    paramètre lambda conserve donc sa signification, tout en pénalisant
    correctement la courbure mesurée en temps physique sur grille irrégulière.
    """
    n = len(x)
    h = np.diff(x).astype(float)
    if np.any(h <= 0):
        raise ValueError("Les temps doivent être strictement croissants.")
    h_mean = float(np.mean(h))

    if order == 1:
        w = h_mean / h
        return diags([-w, w], [0, 1], shape=(n - 1, n), format="csc")
    if order == 2:
        h1, h2 = h[:-1], h[1:]
        s = h_mean ** 2
        a = s * 2.0 / (h1 * (h1 + h2))
        b = -s * 2.0 / (h1 * h2)
        c = s * 2.0 / (h2 * (h1 + h2))
        return diags([a, b, c], [0, 1, 2], shape=(n - 2, n), format="csc")
    raise ValueError(f"Ordre {order} non supporté")


def _trend_filter_l2(y: np.ndarray, x: np.ndarray, lambda_param: float,
                     order: int = 2) -> np.ndarray:
    """
    Trend Filtering avec pénalité L2 (Ridge) :
        min_z ||y - z||² + lambda ||D z||²
    """
    y = np.asarray(y, dtype=float)
    n = len(y)
    if n < order + 2 or lambda_param <= 0:
        return y.copy()
    D = _difference_matrix(x, order)
    A = (identity(n, format="csc") + lambda_param * (D.T @ D)).tocsc()
    return np.asarray(spsolve(A, y), dtype=float)


def _trend_filter_l1(y: np.ndarray, x: np.ndarray, lambda_param: float,
                     order: int = 2, max_iter: int = 3000, tol: float = 1e-5) -> np.ndarray:
    """
    Trend Filtering avec pénalité L1 (Total Variation) via ADMM :
        min_z ½||y - z||² + lambda_abs ||D z||_1

    lambda_param est relatif à la courbure typique des données (moyenne de
    |D y|). Contrairement au cas L2, où fidélité et pénalité sont toutes deux
    quadratiques, la pénalité L1 croît linéairement avec l'amplitude alors
    que la fidélité croît quadratiquement. Sans normalisation, une même
    valeur de lambda lisse fortement un débit de quelques unités et laisse
    quasi intacte une température de plusieurs centaines de kelvins.
    """
    y = np.asarray(y, dtype=float)
    n = len(y)
    if n < order + 2 or lambda_param <= 0:
        return y.copy()

    D = _difference_matrix(x, order)
    DT = D.T.tocsc()

    curvature_scale = float(np.mean(np.abs(D @ y)))
    if curvature_scale <= 0:
        # Données déjà linéaires : rien à lisser
        return y.copy()
    lam = lambda_param * curvature_scale

    rho = max(1.0, lam)
    A = (identity(n, format="csc") + rho * (DT @ D)).tocsc()
    lu = splu(A)

    m = D.shape[0]
    z = y.copy()
    u = np.zeros(m)
    w = np.zeros(m)
    threshold = lam / rho
    # Tolérance relative à l'échelle des données : un seuil absolu rendrait
    # l'arrêt lui aussi dépendant de l'ordre de grandeur des valeurs
    stop = tol * np.sqrt(n) * curvature_scale

    for _ in range(max_iter):
        z = lu.solve(y + rho * (DT @ (w - u)))
        Dz = D @ z
        v = Dz + u
        w_new = np.sign(v) * np.maximum(np.abs(v) - threshold, 0.0)
        # Les deux résidus sont requis : le seul résidu primal peut être
        # petit bien avant que la solution soit stabilisée
        primal = np.linalg.norm(Dz - w_new)
        dual = rho * np.linalg.norm(DT @ (w_new - w))
        w = w_new
        u = u + Dz - w
        if primal < stop and dual < stop:
            break
    return z


def _smooth_trend_values(x: np.ndarray, y: np.ndarray, lambda_param: float,
                         penalty: str = "l2", use_padding: bool = True,
                         padding_points: int = DEFAULT_TREND_PADDING) -> np.ndarray:
    """
    Valeurs lissées (trend filtering) aux points de mesure x.

    Le padding est linéaire, sauf si cela ferait passer une grandeur positive
    (débit, température) sous zéro : padding constant dans ce cas.
    """
    if use_padding and padding_points > 0 and len(x) >= 2:
        pad_method = "linear"
        if np.min(y) >= 0:
            slope = (y[1] - y[0]) / (x[1] - x[0])
            if y[0] - padding_points * abs(slope) * (x[1] - x[0]) < 0:
                pad_method = "constant"
        xw, yw, n_left, n_right = _apply_padding(x, y, padding_points, pad_method)
    else:
        xw, yw, n_left, n_right = x, y, 0, 0

    if penalty == "l1":
        ys = _trend_filter_l1(yw, xw, lambda_param, order=2)
    else:
        ys = _trend_filter_l2(yw, xw, lambda_param, order=2)

    return ys[n_left:len(ys) - n_right]


# =============================================================================
# Spline lissée
# =============================================================================

def _fit_spline(x: np.ndarray, y: np.ndarray, smooth_factor: float) -> UnivariateSpline:
    """Spline cubique lissée ; s est relatif à l'amplitude des données."""
    n = len(x)
    rng = float(np.max(y) - np.min(y))
    s = 0.0 if (smooth_factor <= 0 or rng == 0) else n * (smooth_factor * rng) ** 2
    k = min(SPLINE_DEGREE, n - 1)
    return UnivariateSpline(x, y, k=k, s=s)


# =============================================================================
# Zones spéciales
# =============================================================================

def normalize_zones(zones) -> List[Tuple[float, float, str]]:
    """
    Normalise une liste de zones en tuples (t_start, t_end, type) triés.
    Accepte les tuples/listes à 2 éléments (type "exact" par défaut).
    """
    out = []
    for z in zones or []:
        if len(z) >= 3:
            t0, t1, ztype = float(z[0]), float(z[1]), str(z[2])
        else:
            t0, t1 = float(z[0]), float(z[1])
            ztype = "exact"
        if ztype not in ZONE_TYPES:
            ztype = "exact"
        if t1 < t0:
            t0, t1 = t1, t0
        out.append((t0, t1, ztype))
    out.sort(key=lambda z: (z[0], z[1]))
    return out


def zones_to_index_ranges(x: np.ndarray, zones) -> List[Tuple[int, int, str]]:
    """
    Convertit les zones en plages d'indices inclusives (i_start, i_end, type)
    sur les points de mesure x.

    - Chaque borne est ajustée au point de mesure le plus proche.
    - Une zone contient au moins 2 points ; les zones ne se chevauchent pas
      (elles peuvent partager un point frontière).
    - Une zone qui ne peut pas être placée (ex. au-delà du dernier point)
      est ignorée.
    """
    x = np.asarray(x, dtype=float)
    n = len(x)
    ranges = []
    prev_end = 0
    for t0, t1, ztype in normalize_zones(zones):
        i0 = int(np.argmin(np.abs(x - t0)))
        i1 = int(np.argmin(np.abs(x - t1)))
        i0 = max(i0, prev_end)
        if i1 <= i0:
            i1 = i0 + 1
        if i1 > n - 1:
            i1 = n - 1
        if i1 <= i0:
            continue
        ranges.append((i0, i1, ztype))
        prev_end = i1
    return ranges


def _build_segments(n: int, zone_ranges: List[Tuple[int, int, str]]) -> List[Tuple[str, int, int]]:
    """
    Découpe [0, n-1] en segments contigus ("global" ou type de zone).
    Les segments consécutifs partagent leur point frontière.
    """
    segments = []
    cur = 0
    for i0, i1, ztype in zone_ranges:
        if i0 > cur:
            segments.append(("global", cur, i0))
        segments.append((ztype, i0, i1))
        cur = i1
    if cur < n - 1:
        segments.append(("global", cur, n - 1))
    return segments


def _smoothed_samples(x: np.ndarray, y: np.ndarray, method: str,
                      smooth_factor: float, trend_lambda: float) -> np.ndarray:
    """Valeurs "lissées" aux points de mesure x selon la méthode globale."""
    n = len(x)
    if method in TREND_METHODS and n >= MIN_POINTS_REQUIRED:
        penalty = "l1" if method == "trend_l1" else "l2"
        return _smooth_trend_values(x, y, trend_lambda, penalty)
    if method == "spline" and n >= MIN_POINTS_REQUIRED:
        return np.asarray(_fit_spline(x, y, smooth_factor)(x), dtype=float)
    return y.copy()


def _interpolate_global(x, y, t, method, smooth_factor, trend_lambda) -> np.ndarray:
    """Interpolation sur toute la courbe (sans zone). t doit être dans [x0, xN]."""
    if method == "linear":
        return np.interp(t, x, y)
    if method == "spline":
        return np.asarray(_fit_spline(x, y, smooth_factor)(t), dtype=float)
    if method in TREND_METHODS:
        penalty = "l1" if method == "trend_l1" else "l2"
        ys = _smooth_trend_values(x, y, trend_lambda, penalty)
        return PchipInterpolator(x, ys, extrapolate=True)(t)
    return PchipInterpolator(x, y, extrapolate=True)(t)


def _interpolate_segmented(x, y, t, method, smooth_factor, trend_lambda,
                           zone_ranges) -> np.ndarray:
    """Interpolation par segments avec zones. t doit être dans [x0, xN]."""
    n = len(x)
    segments = _build_segments(n, zone_ranges)
    result = np.empty(t.shape, dtype=float)
    assigned = np.zeros(t.shape, dtype=bool)

    for kind, i0, i1 in segments:
        xs = x[i0:i1 + 1]
        ys = y[i0:i1 + 1]

        if kind == "global":
            vals = _smoothed_samples(xs, ys, method, smooth_factor, trend_lambda)
            # Continuité C0 aux frontières partagées avec une zone
            if i0 > 0:
                vals[0] = ys[0]
            if i1 < n - 1:
                vals[-1] = ys[-1]
            if method == "linear":
                func = lambda tt, xs=xs, vs=vals: np.interp(tt, xs, vs)
            else:
                func = PchipInterpolator(xs, vals, extrapolate=True)
        elif kind == "linear":
            func = lambda tt, xs=xs, ys=ys: np.interp(
                tt, [xs[0], xs[-1]], [ys[0], ys[-1]]
            )
        else:  # "exact"
            func = PchipInterpolator(xs, ys, extrapolate=True)

        mask = (t >= xs[0]) & (t <= xs[-1]) & ~assigned
        if mask.any():
            result[mask] = func(t[mask])
            assigned |= mask

    if not assigned.all():
        # Sécurité (ne devrait pas arriver : les segments couvrent [x0, xN])
        result[~assigned] = np.interp(t[~assigned], x, y)
    return result


# =============================================================================
# API publique
# =============================================================================

def interpolate(
    df: pd.DataFrame,
    t_new: np.ndarray,
    method: str = "pchip",
    smooth_factor: float = 0.01,
    unfiltered_zones: list = None,
    trend_lambda: float = 1.0
) -> np.ndarray:
    """
    Interpolation avec choix de la méthode et zones spéciales.

    Args:
        df: DataFrame avec colonnes 'Time_s' et 'Value'
        t_new: Array numpy des temps d'évaluation
        method: "pchip", "spline", "linear", "trend_l2", "trend_l1"
        smooth_factor: Facteur de lissage (pour "spline")
        unfiltered_zones: Liste de tuples (t_start, t_end, type) pour zones
        trend_lambda: Paramètre lambda pour trend filtering

    Returns:
        Array numpy des valeurs interpolées (même forme que t_new)
    """
    if method not in INTERP_METHODS:
        method = "pchip"

    x, y = prepare_xy(df)
    _check_min_points(len(x), method)

    t = np.asarray(t_new, dtype=float)
    # Pas d'extrapolation : prolongement constant hors de la plage des données
    t_eval = np.clip(t, x[0], x[-1])

    zone_ranges = zones_to_index_ranges(x, unfiltered_zones)
    if not zone_ranges:
        return _interpolate_global(x, y, t_eval, method, smooth_factor, trend_lambda)
    return _interpolate_segmented(x, y, t_eval, method, smooth_factor,
                                  trend_lambda, zone_ranges)


def interpolate_pchip(df: pd.DataFrame, t_new: np.ndarray) -> np.ndarray:
    """Interpolation exacte avec PCHIP."""
    return interpolate(df, t_new, method="pchip")


def interpolate_smooth(df: pd.DataFrame, t_new: np.ndarray, smooth_factor: float = 0.01,
                       unfiltered_zones: list = None) -> np.ndarray:
    """Interpolation lissée avec spline cubique (segmentée si zones)."""
    return interpolate(df, t_new, method="spline", smooth_factor=smooth_factor,
                       unfiltered_zones=unfiltered_zones)


def interpolate_trend(df: pd.DataFrame, t_new: np.ndarray, lambda_param: float = 1.0,
                      method: str = "trend_l2", unfiltered_zones: list = None) -> np.ndarray:
    """Interpolation avec lissage Trend Filtering (L2 ou L1)."""
    if method not in TREND_METHODS:
        method = "trend_l2"
    return interpolate(df, t_new, method=method, unfiltered_zones=unfiltered_zones,
                       trend_lambda=lambda_param)


def interpolate_with_zones(df: pd.DataFrame, t_new: np.ndarray, method: str = "pchip",
                           smooth_factor: float = 0.01, unfiltered_zones: list = None,
                           trend_lambda: float = 1.0) -> np.ndarray:
    """Alias de interpolate() (conservé pour compatibilité)."""
    return interpolate(df, t_new, method, smooth_factor, unfiltered_zones, trend_lambda)


def compute_smoothness_metrics(x: np.ndarray, y: np.ndarray) -> dict:
    """
    Calcule des métriques de "violence" d'une courbe pour diagnostic CFD.

    Returns:
        Dict avec max_slope, mean_slope, max_curvature, mean_curvature,
        slope_variation, severity (0-100)
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(x) < 3:
        return {
            "max_slope": 0, "mean_slope": 0,
            "max_curvature": 0, "mean_curvature": 0,
            "slope_variation": 0, "severity": 0
        }

    h = np.diff(x)
    slopes = np.diff(y) / h
    slopes = np.where(np.isfinite(slopes), slopes, 0)

    h1, h2 = h[:-1], h[1:]
    curvatures = 2 * (np.diff(y)[1:] / h2 - np.diff(y)[:-1] / h1) / (h1 + h2)
    curvatures = np.where(np.isfinite(curvatures), curvatures, 0)

    max_slope = float(np.max(np.abs(slopes)))
    mean_slope = float(np.mean(np.abs(slopes)))
    max_curvature = float(np.max(np.abs(curvatures)))
    mean_curvature = float(np.mean(np.abs(curvatures)))
    slope_variation = float(np.std(slopes))

    y_range = float(np.max(y) - np.min(y)) or 1.0
    x_range = float(np.max(x) - np.min(x)) or 1.0

    normalized_slope = max_slope * x_range / y_range
    normalized_curv = max_curvature * x_range ** 2 / y_range

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
# Utilitaires
# =============================================================================

def sanitize_flow(values: np.ndarray, flow_eps: float = DEFAULT_FLOW_EPS) -> Tuple[np.ndarray, int]:
    """Remplace les valeurs nulles par flow_eps pour éviter les divergences dans Fluent."""
    result = np.asarray(values, dtype=np.float64).copy()
    zero_mask = (result == 0.0)
    n_replaced = int(zero_mask.sum())

    if n_replaced > 0:
        result[zero_mask] = flow_eps

    return result, n_replaced


def generate_time_array(sim_duration: float, dt: float) -> np.ndarray:
    """
    Génère un array de temps de 0 à sim_duration avec un pas EXACTEMENT égal à dt.

    Le dernier instant est le plus grand multiple de dt inférieur ou égal à
    sim_duration (à une tolérance numérique près).
    """
    if dt <= 0:
        raise ValueError(f"Le pas de temps doit être > 0, reçu : {dt}")
    if sim_duration <= 0:
        raise ValueError(f"La durée de simulation doit être > 0, reçue : {sim_duration}")

    n_pts = int(np.floor(sim_duration / dt + 1e-9)) + 1
    return np.arange(n_pts, dtype=float) * dt


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
        unfiltered_zones: Dict {key: [(t_start, t_end, type), ...]}
        inlet_names: Dictionnaire {"inlet1": "nom1", ...}
        trend_lambda_params: Dict {key: lambda_value}
        inverted: Dict {key: bool} - courbes à inverser (coefficient ×-1
                  appliqué à toute la courbe, y compris au remplacement
                  des débits nuls)

    Returns:
        Dictionnaire {clé_renommée: array_interpolé}
    """
    result = {}

    inlet_names = inlet_names or {}
    unfiltered_zones = unfiltered_zones or {}
    trend_lambda_params = trend_lambda_params or {}
    inverted = inverted or {}

    for key, df in data_raw.items():
        method = methods.get(key, "pchip")
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

        if key.startswith("Q_"):
            interp, n_replaced = sanitize_flow(interp, flow_eps)
            if n_replaced > 0:
                print(f"{key}: {n_replaced} valeurs nulles remplacées par {flow_eps}")

        if inverted.get(key, False):
            interp = -interp

        new_key = key
        for old_name, new_name in inlet_names.items():
            new_key = new_key.replace(old_name, new_name)

        result[new_key] = interp

    return result
