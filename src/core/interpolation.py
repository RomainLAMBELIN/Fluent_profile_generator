"""
Module d'interpolation et de lissage des données
"""

import numpy as np
import pandas as pd
from scipy.interpolate import UnivariateSpline, PchipInterpolator, Akima1DInterpolator
from scipy.signal import savgol_filter
from typing import Tuple

from core.constants import MIN_POINTS_REQUIRED, SPLINE_DEGREE, DEFAULT_FLOW_EPS, DEFAULT_SAVGOL_WINDOW, DEFAULT_SAVGOL_POLYORDER


def apply_hermite_transitions(t_new: np.ndarray, interpolators: list, x: np.ndarray, y: np.ndarray, 
                             transition_ratio: float = 0.02) -> np.ndarray:
    """
    Applique des transitions de Hermite cubique aux jonctions entre segments.
    
    Assure continuité C1 (valeur + dérivée) pour des transitions douces.
    
    Args:
        t_new: Points d'évaluation
        interpolators: Liste de dicts avec 'start', 'end', 'func'
        x, y: Données brutes (pour fallback)
        transition_ratio: Ratio de transition (0.02 = 2%)
    
    Returns:
        Array des valeurs interpolées avec transitions
    """
    result = np.zeros_like(t_new)
    eps = 1e-10
    
    for i, t in enumerate(t_new):
        # Trouver le segment contenant t
        current_seg = None
        current_idx = None
        
        for idx, seg in enumerate(interpolators):
            if seg['start'] - eps <= t <= seg['end'] + eps:
                current_seg = seg
                current_idx = idx
                break
        
        if current_seg is None:
            # Fallback
            result[i] = np.interp(t, x, y)
            continue
        
        # Vérifier si on est dans une zone de transition avec le segment SUIVANT
        if current_idx < len(interpolators) - 1:
            next_seg = interpolators[current_idx + 1]
            junction_t = next_seg['start']
            seg_width = current_seg['end'] - current_seg['start']
            transition_width = max(transition_ratio * seg_width, eps * 100)
            
            # Distance à la jonction
            dist_to_junction = abs(t - junction_t)
            
            if dist_to_junction < transition_width and t <= junction_t + eps:
                # Dans zone de transition
                # t_norm : 0 au milieu du segment, 1 à la jonction
                t_norm = 1.0 - (junction_t - t) / transition_width
                t_norm = max(0.0, min(1.0, t_norm))
                
                try:
                    # Valeurs
                    v_curr = current_seg['func'](t)
                    v_next = next_seg['func'](junction_t + eps)
                    
                    # Dérivées (différences finies)
                    dt = transition_width * 0.01
                    if t - dt >= current_seg['start']:
                        d_curr = (v_curr - current_seg['func'](t - dt)) / dt
                    else:
                        d_curr = 0
                    
                    if junction_t + dt <= next_seg['end']:
                        d_next = (next_seg['func'](junction_t + dt) - v_next) / dt
                    else:
                        d_next = 0
                    
                    # Hermite cubique
                    h00 = 2*t_norm**3 - 3*t_norm**2 + 1
                    h10 = t_norm**3 - 2*t_norm**2 + t_norm
                    h01 = -2*t_norm**3 + 3*t_norm**2
                    h11 = t_norm**3 - t_norm**2
                    
                    result[i] = (h00 * v_curr + h10 * d_curr * transition_width +
                                h01 * v_next + h11 * d_next * transition_width)
                    continue
                except:
                    pass
        
        # Pas de transition, utiliser interpolateur normal
        try:
            result[i] = current_seg['func'](t)
        except:
            result[i] = np.interp(t, x, y)
    
    return result


def interpolate_pchip(df: pd.DataFrame, t_new: np.ndarray) -> np.ndarray:
    """
    Interpolation exacte avec PCHIP (Piecewise Cubic Hermite Interpolating Polynomial).
    
    PCHIP garantit :
    - Passage par tous les points de données (interpolation exacte)
    - Monotonie préservée (pas de dépassement/oscillations entre les points)
    - Continuité de la dérivée première
    
    Args:
        df: DataFrame avec colonnes 'Time_s' et 'Value'
        t_new: Array numpy des temps d'évaluation
    
    Returns:
        Array numpy des valeurs interpolées aux points t_new
    
    Raises:
        ValueError: Si le DataFrame contient trop peu de points
    
    Note:
        PCHIP ne permet pas de lissage - il passe exactement par tous les points.
        Pour du lissage, utilisez interpolate_smooth() à la place.
    """
    x = df["Time_s"].to_numpy()
    y = df["Value"].to_numpy()
    
    if len(x) < MIN_POINTS_REQUIRED:
        raise ValueError(
            f"Trop peu de points ({len(x)}), minimum {MIN_POINTS_REQUIRED} requis."
        )
    
    # PCHIP avec extrapolation
    interpolator = PchipInterpolator(x, y, extrapolate=True)
    return interpolator(t_new)


def interpolate_with_zones(df: pd.DataFrame, t_new: np.ndarray, method: str = "pchip",
                          smooth_factor: float = 0.01, unfiltered_zones: list = None,
                          transition_ratio: float = 0.02) -> np.ndarray:
    """
    Interpolation SEGMENTÉE avec zones spéciales.
    
    Fonctionne avec toutes les méthodes globales (pchip, spline, linear).
    L'interpolation globale est divisée en segments qui excluent les zones spéciales.
    
    Args:
        df: DataFrame avec colonnes 'Time_s' et 'Value'
        t_new: Array numpy des temps d'évaluation
        method: Méthode pour les segments globaux ("pchip", "spline", "linear")
        smooth_factor: Facteur de lissage (pour spline uniquement)
        unfiltered_zones: Liste de tuples (t_start, t_end, type)
    
    Returns:
        Array numpy des valeurs interpolées
    """
    # Si la méthode est "spline", utiliser interpolate_smooth
    if method == "spline":
        return interpolate_smooth(df, t_new, smooth_factor, unfiltered_zones)
    
    # Pour PCHIP et Linear avec zones, réutiliser la logique de segmentation
    x = df["Time_s"].to_numpy()
    y = df["Value"].to_numpy()
    
    if len(x) < MIN_POINTS_REQUIRED:
        raise ValueError(f"Trop peu de points ({len(x)}), minimum {MIN_POINTS_REQUIRED} requis.")
    
    # Préparer les zones triées
    zones_list = []
    for zone in unfiltered_zones:
        if len(zone) == 3:
            t_start, t_end, ztype = zone
        else:
            t_start, t_end = zone
            ztype = "exact"
        zones_list.append((t_start, t_end, ztype))
    zones_list.sort(key=lambda z: z[0])
    
    # Pour chaque zone, trouver les indices des points de borne les plus proches
    zone_boundaries = []
    for t_start, t_end, ztype in zones_list:
        idx_start = np.argmin(np.abs(x - t_start))
        idx_end = np.argmin(np.abs(x - t_end))
        zone_boundaries.append((idx_start, idx_end, t_start, t_end, ztype))
    
    # Créer segments basés sur les indices
    segments = []
    current_idx = 0
    
    for idx_start, idx_end, t_start, t_end, ztype in zone_boundaries:
        # Segment global avant cette zone (EXCLUSIF: s'arrête AVANT idx_start)
        if current_idx < idx_start:
            segments.append((method + "_global", current_idx, idx_start - 1))
        
        # La zone elle-même (marquer comme zone)
        segments.append((ztype + "_zone", idx_start, idx_end))
        current_idx = idx_end + 1
    
    # Segment global final
    if current_idx < len(x):
        segments.append((method + "_global", current_idx, len(x) - 1))
    
    # Créer un interpolateur pour chaque segment
    interpolators = []
    
    for seg_type, idx_start, idx_end in segments:
        idx_end_incl = min(idx_end, len(x) - 1)
        
        x_seg = x[idx_start:idx_end_incl+1]
        y_seg = y[idx_start:idx_end_incl+1]
        
        if len(x_seg) < 2:
            continue
        
        seg_t_start = x_seg[0]
        seg_t_end = x_seg[-1]
        
        # Créer l'interpolateur selon le type
        if seg_type == "pchip_global" or seg_type == "exact_zone":
            # PCHIP
            if len(x_seg) >= 2:
                interp = PchipInterpolator(x_seg, y_seg, extrapolate=False)
            else:
                interp = lambda t, val=y_seg[0]: val
        
        elif seg_type == "linear_global":
            # Linéaire global : interpolation linéaire entre TOUS les points du segment
            if len(x_seg) >= 2:
                # np.interp fait une interpolation linéaire entre tous les points
                interp = lambda t, xs=x_seg.copy(), ys=y_seg.copy(): np.interp(t, xs, ys)
            else:
                interp = lambda t, val=y_seg[0]: val
        
        elif seg_type == "linear_zone":
            # Linéaire zone : droite entre les 2 points de BORNE uniquement
            t1, y1 = x_seg[0], y_seg[0]
            t2, y2 = x_seg[-1], y_seg[-1]
            
            if t2 != t1:
                interp = lambda t, t1=t1, y1=y1, t2=t2, y2=y2: y1 + (y2 - y1) * (t - t1) / (t2 - t1)
            else:
                interp = lambda t, y1=y1: y1
        
        else:
            # Fallback: PCHIP
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
    
    # Interpoler chaque point avec transitions de Hermite
    result = apply_hermite_transitions(t_new, interpolators, x, y, transition_ratio)
    return result


def interpolate_smooth(df: pd.DataFrame, t_new: np.ndarray, smooth_factor: float = 0.01, unfiltered_zones: list = None,
                      transition_ratio: float = 0.02) -> np.ndarray:
    """
    Interpolation lissée avec spline cubique SEGMENTÉE.
    
    L'interpolation globale est divisée en segments qui excluent les zones spéciales.
    Cela évite les oscillations aux jonctions.
    """
    x = df["Time_s"].to_numpy()
    y = df["Value"].to_numpy()
    
    if len(x) < MIN_POINTS_REQUIRED:
        raise ValueError(f"Trop peu de points ({len(x)}), minimum {MIN_POINTS_REQUIRED} requis.")
    
    # Si pas de zones, interpolation simple sur tout
    if unfiltered_zones is None or len(unfiltered_zones) == 0:
        n = len(x)
        rng = float(np.max(y) - np.min(y))
        s = 0.0 if (smooth_factor <= 0 or rng == 0) else n * (smooth_factor * rng) ** 2
        spl = UnivariateSpline(x, y, k=SPLINE_DEGREE, s=s)
        return spl(t_new)
    
    # Préparer les zones triées
    zones_list = []
    for zone in unfiltered_zones:
        if len(zone) == 3:
            t_start, t_end, ztype = zone
        else:
            t_start, t_end = zone
            ztype = "exact"
        zones_list.append((t_start, t_end, ztype))
    zones_list.sort(key=lambda z: z[0])
    
    # Créer les segments avec points de données réels aux bornes
    segments = []
    t_min, t_max = x[0], x[-1]
    
    # Pour chaque zone, trouver les indices des points de borne les plus proches
    zone_boundaries = []
    for t_start, t_end, ztype in zones_list:
        idx_start = np.argmin(np.abs(x - t_start))
        idx_end = np.argmin(np.abs(x - t_end))
        zone_boundaries.append((idx_start, idx_end, t_start, t_end, ztype))
    
    # Créer segments basés sur les indices
    current_idx = 0
    
    for idx_start, idx_end, t_start, t_end, ztype in zone_boundaries:
        # Segment global avant cette zone (EXCLUSIF: s'arrête AVANT idx_start)
        if current_idx < idx_start:
            segments.append(('global', current_idx, idx_start - 1))
        
        # La zone elle-même
        segments.append((ztype, idx_start, idx_end))
        current_idx = idx_end + 1
    
    # Segment global final
    if current_idx < len(x):
        segments.append(('global', current_idx, len(x) - 1))
    
    # Créer un interpolateur pour chaque segment
    interpolators = []
    
    for seg_type, idx_start, idx_end in segments:
        # S'assurer que idx_end est inclus
        idx_end_incl = min(idx_end, len(x) - 1)
        
        x_seg = x[idx_start:idx_end_incl+1]
        y_seg = y[idx_start:idx_end_incl+1]
        
        if len(x_seg) < 2:
            continue
        
        seg_t_start = x_seg[0]
        seg_t_end = x_seg[-1]
        
        if seg_type == 'global':
            # Interpolation lissée sur les points du segment
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
            # PCHIP sur les points du segment
            if len(x_seg) >= 2:
                interp = PchipInterpolator(x_seg, y_seg, extrapolate=False)
            else:
                interp = lambda t, val=y_seg[0]: val
        
        elif seg_type == 'linear':
            # Droite entre les 2 points de borne
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
    
    # Interpoler chaque point avec transitions de Hermite
    result = apply_hermite_transitions(t_new, interpolators, x, y, transition_ratio)
    return result


def interpolate_akima(df: pd.DataFrame, t_new: np.ndarray) -> np.ndarray:
    """
    Interpolation Akima (cubique locale minimisant les oscillations).
    
    Akima utilise une approche locale qui évite les oscillations non physiques
    entre les points, contrairement aux splines cubiques globales.
    
    Args:
        df: DataFrame avec colonnes 'Time_s' et 'Value'
        t_new: Array numpy des temps d'évaluation
    
    Returns:
        Array numpy des valeurs interpolées
    
    Note:
        Akima est particulièrement adapté aux données avec des changements
        brusques de pente ou des discontinuités.
    """
    x = df["Time_s"].to_numpy()
    y = df["Value"].to_numpy()
    
    if len(x) < 5:  # Akima nécessite au moins 5 points
        # Fallback sur PCHIP si pas assez de points
        return interpolate_pchip(df, t_new)
    
    interpolator = Akima1DInterpolator(x, y)
    return interpolator(t_new)


def interpolate_makima(df: pd.DataFrame, t_new: np.ndarray) -> np.ndarray:
    """
    Interpolation Makima (Modified Akima - plus robuste aux valeurs aberrantes).
    
    Makima est une version améliorée d'Akima qui gère mieux les données
    avec des valeurs aberrantes ou des distributions non uniformes.
    
    Args:
        df: DataFrame avec colonnes 'Time_s' et 'Value'
        t_new: Array numpy des temps d'évaluation
    
    Returns:
        Array numpy des valeurs interpolées
    
    Note:
        Recommandé quand les données contiennent des pics isolés ou du bruit.
    """
    x = df["Time_s"].to_numpy()
    y = df["Value"].to_numpy()
    
    if len(x) < 5:
        return interpolate_pchip(df, t_new)
    
    # Makima utilise method=2 dans Akima1DInterpolator (si disponible)
    try:
        interpolator = Akima1DInterpolator(x, y, method="makima")
    except:
        # Fallback sur Akima standard si makima pas disponible
        interpolator = Akima1DInterpolator(x, y)
    
    return interpolator(t_new)


def interpolate_savgol(
    df: pd.DataFrame,
    t_new: np.ndarray,
    window_length: int = DEFAULT_SAVGOL_WINDOW,
    polyorder: int = DEFAULT_SAVGOL_POLYORDER
) -> np.ndarray:
    """
    Filtrage Savitzky-Golay suivi d'une interpolation PCHIP.
    
    Savitzky-Golay applique un filtre polynomial par fenêtre glissante,
    excellent pour éliminer le bruit haute fréquence tout en préservant
    les caractéristiques du signal (pics, pentes).
    
    Args:
        df: DataFrame avec colonnes 'Time_s' et 'Value'
        t_new: Array numpy des temps d'évaluation
        window_length: Taille de la fenêtre (doit être impair, ≥ polyorder+2)
        polyorder: Degré du polynôme (généralement 2 ou 3)
    
    Returns:
        Array numpy des valeurs filtrées et interpolées
    
    Note:
        - window_length plus grand = lissage plus fort
        - polyorder plus grand = meilleure préservation des pics
        - Très efficace pour les signaux bruités avec structure claire
    """
    x = df["Time_s"].to_numpy()
    y = df["Value"].to_numpy()
    
    if len(x) < window_length:
        # Pas assez de points pour Savitzky-Golay
        return interpolate_pchip(df, t_new)
    
    # Assurer que window_length est impair
    if window_length % 2 == 0:
        window_length += 1
    
    # Assurer que window_length > polyorder
    if window_length <= polyorder:
        window_length = polyorder + 2
        if window_length % 2 == 0:
            window_length += 1
    
    # Appliquer le filtre Savitzky-Golay
    y_filtered = savgol_filter(y, window_length, polyorder)
    
    # Interpoler les données filtrées avec PCHIP
    interpolator = PchipInterpolator(x, y_filtered, extrapolate=True)
    return interpolator(t_new)


def interpolate(
    df: pd.DataFrame,
    t_new: np.ndarray,
    method: str = "pchip",
    smooth_factor: float = 0.01,
    unfiltered_zones: list = None,
    savgol_window: int = DEFAULT_SAVGOL_WINDOW,
    savgol_polyorder: int = DEFAULT_SAVGOL_POLYORDER,
    transition_ratio: float = 0.02
) -> np.ndarray:
    """
    Interpolation avec choix de la méthode.
    
    Args:
        df: DataFrame avec colonnes 'Time_s' et 'Value'
        t_new: Array numpy des temps d'évaluation
        method: Méthode d'interpolation - "pchip", "spline", "linear"
        smooth_factor: Facteur de lissage (utilisé pour "spline")
        unfiltered_zones: Liste de tuples (t_start, t_end, type) pour zones
        savgol_window: Non utilisé (compatibilité)
        savgol_polyorder: Non utilisé (compatibilité)
        transition_ratio: Ratio de transition Hermite (0.02 = 2%)
    
    Returns:
        Array numpy des valeurs interpolées
    
    Raises:
        ValueError: Si la méthode est inconnue ou si trop peu de points
    """
    # Si pas de zones définies, utiliser la méthode simple
    if unfiltered_zones is None or len(unfiltered_zones) == 0:
        if method == "pchip":
            return interpolate_pchip(df, t_new)
        elif method == "spline":
            return interpolate_smooth(df, t_new, smooth_factor, None, transition_ratio)
        elif method == "linear":
            x = df["Time_s"].to_numpy()
            y = df["Value"].to_numpy()
            return np.interp(t_new, x, y)
        else:
            return interpolate_pchip(df, t_new)
    
    # Avec zones : utiliser l'interpolation segmentée pour TOUTES les méthodes
    return interpolate_with_zones(df, t_new, method, smooth_factor, unfiltered_zones, transition_ratio)


def sanitize_flow(values: np.ndarray, flow_eps: float = DEFAULT_FLOW_EPS) -> Tuple[np.ndarray, int]:
    """
    Remplace les valeurs nulles par flow_eps pour éviter les divergences dans Fluent.
    
    Args:
        values: Array numpy des valeurs de débit
        flow_eps: Valeur de remplacement pour les débits nuls
    
    Returns:
        Tuple (values_sanitized, n_replaced)
        - values_sanitized : array avec valeurs remplacées
        - n_replaced : nombre de valeurs remplacées
    
    Note:
        Les débits nuls peuvent causer des problèmes de convergence dans Fluent.
        On les remplace par une valeur très petite mais non nulle.
    """
    result = values.copy()
    zero_mask = (result == 0.0)
    n_replaced = int(zero_mask.sum())
    
    if n_replaced > 0:
        result[zero_mask] = flow_eps
    
    return result, n_replaced


def generate_time_array(sim_duration: float, dt: float) -> np.ndarray:
    """
    Génère un array de temps régulièrement espacé.
    
    Args:
        sim_duration: Durée totale de la simulation (en secondes)
        dt: Pas de temps (en secondes)
    
    Returns:
        Array numpy des temps de 0 à sim_duration
    
    Raises:
        ValueError: Si dt <= 0 ou sim_duration <= 0
    """
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
    savgol_params: dict = None
) -> dict:
    """
    Interpole toutes les données avec les paramètres spécifiés par courbe.
    
    Args:
        data_raw: Dictionnaire {clé: DataFrame}
        times: Array des temps d'évaluation
        methods: Dict {key: method} - Méthode par courbe
        smooth_params: Dict {key: smooth_factor} - Lissage par courbe
        flow_eps: Valeur de remplacement pour les débits nuls
        unfiltered_zones: Dict {key: [(t_start, t_end), ...]} zones par inlet
        inlet_names: Dictionnaire {"inlet1": "nom1", "inlet2": "nom2"}
        savgol_params: Dict {"window": int, "polyorder": int}
    
    Returns:
        Dictionnaire {clé_renommée: array_interpolé}
    
    Note:
        Les débits sont sanitizés après interpolation.
        Les clés sont renommées selon inlet_names si fourni.
    """
    result = {}
    
    # Noms par défaut
    if inlet_names is None:
        inlet_names = {"inlet1": "inlet1", "inlet2": "inlet2"}
    
    # Zones par défaut
    if unfiltered_zones is None:
        unfiltered_zones = {}
    
    # Paramètres Savitzky-Golay par défaut
    if savgol_params is None:
        savgol_params = {
            "window": DEFAULT_SAVGOL_WINDOW,
            "polyorder": DEFAULT_SAVGOL_POLYORDER
        }
    
    for key, df in data_raw.items():
        # Méthode et lissage spécifiques à cette courbe
        method = methods.get(key, "spline")
        smooth = smooth_params.get(key, 0.01)
        
        # Zones non-filtrées spécifiques à cette courbe
        zones_for_key = unfiltered_zones.get(key, [])
        
        # Interpolation
        interp = interpolate(
            df,
            times,
            method=method,
            smooth_factor=smooth,
            unfiltered_zones=zones_for_key,
            savgol_window=savgol_params["window"],
            savgol_polyorder=savgol_params["polyorder"]
        )
        
        # Sanitization pour les débits
        if key.startswith("Q_"):
            interp, n_replaced = sanitize_flow(interp, flow_eps)
            if n_replaced > 0:
                print(f"{key}: {n_replaced} valeurs nulles remplacées par {flow_eps}")
        
        # Renommer la clé selon les noms d'inlet fournis
        new_key = key
        for old_name, new_name in inlet_names.items():
            new_key = new_key.replace(old_name, new_name)
        
        result[new_key] = interp
    
    return result
