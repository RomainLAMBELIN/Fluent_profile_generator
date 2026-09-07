"""
Utilitaires pour l'analyse des données interpolées
"""

import numpy as np
from scipy.integrate import trapezoid

from core.i18n import t


def compute_interpolation_error(df, times, interpolated_values):
    """
    Calcule l'erreur d'interpolation par intégrale.
    
    Compare l'aire sous la courbe des données brutes (interpolation linéaire)
    avec l'aire sous la courbe des données interpolées.
    
    Args:
        df: DataFrame avec colonnes 'Time_s' et 'Value'
        times: Array numpy des temps d'évaluation interpolée
        interpolated_values: Array numpy des valeurs interpolées
    
    Returns:
        dict avec:
            - 'relative_error_percent': Erreur relative en %
            - 'absolute_error': Erreur absolue
            - 'raw_integral': Intégrale des données brutes
            - 'interp_integral': Intégrale des données interpolées
    """
    x_raw = df["Time_s"].to_numpy()
    y_raw = df["Value"].to_numpy()
    
    # Intégrale des données brutes (interpolation linéaire entre points)
    raw_integral = trapezoid(y_raw, x_raw)
    
    # Intégrale des données interpolées
    interp_integral = trapezoid(interpolated_values, times)
    
    # Erreur absolue
    absolute_error = abs(interp_integral - raw_integral)
    
    # Erreur relative en %
    if abs(raw_integral) > 1e-10:
        relative_error_percent = (absolute_error / abs(raw_integral)) * 100
    else:
        relative_error_percent = 0.0 if absolute_error < 1e-10 else float('inf')
    
    return {
        'relative_error_percent': relative_error_percent,
        'absolute_error': absolute_error,
        'raw_integral': raw_integral,
        'interp_integral': interp_integral
    }


def format_error_text(error_dict):
    """Formate le dictionnaire d'erreur en texte lisible."""
    err_rel = error_dict['relative_error_percent']
    err_abs = error_dict['absolute_error']
    
    if err_rel == float('inf'):
        return t("Erreur abs: {absolute}", absolute=f"{err_abs:.2e}")
    return t(
        "Erreur: {percent}% (abs: {absolute})",
        percent=f"{err_rel:.3f}", absolute=f"{err_abs:.2e}",
    )


# ---------------------------------------------------------------------------
# Analyse des pentes (variations brusques)
# ---------------------------------------------------------------------------
#
# Les fortes variations d'une condition aux limites sont la principale cause
# de divergence dans Fluent. Comparer la pente maximale des donnees brutes a
# celle de la courbe traitee mesure directement l'effet du lissage.


def slopes_between_samples(x, y):
    """
    Pente entre points de mesure consecutifs.

    La derivee de donnees brutes reliees lineairement est constante par
    morceaux : slopes[i] s'applique sur l'intervalle [x[i], x[i+1]].

    Args:
        x: Array des temps (croissants)
        y: Array des valeurs

    Returns:
        Tuple (milieux, pentes), tableaux vides si moins de 2 points
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(x) < 2:
        return np.array([]), np.array([])

    dx = np.diff(x)
    slopes = np.where(dx > 0, np.diff(y) / np.where(dx > 0, dx, 1.0), 0.0)
    midpoints = (x[:-1] + x[1:]) / 2.0
    return midpoints, slopes


def slopes_along_curve(t, y):
    """
    Pente d'une courbe echantillonnee, par differences centrees.

    Args:
        t: Array des temps d'evaluation
        y: Array des valeurs interpolees

    Returns:
        Tuple (t, pentes) de meme longueur que l'entree
    """
    t = np.asarray(t, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(t) < 2:
        return t, np.zeros_like(t)
    return t, np.gradient(y, t)


def max_slope(positions, slopes):
    """
    Pente de plus grande amplitude et l'instant ou elle est atteinte.

    Args:
        positions: Array des instants associes aux pentes
        slopes: Array des pentes

    Returns:
        Dict avec 'value' (pente signee), 'magnitude' (valeur absolue)
        et 'time' (instant), ou None si aucune pente exploitable
    """
    slopes = np.asarray(slopes, dtype=float)
    positions = np.asarray(positions, dtype=float)
    if slopes.size == 0:
        return None

    finite = np.isfinite(slopes)
    if not finite.any():
        return None

    candidates = np.where(finite, np.abs(slopes), -np.inf)
    idx = int(np.argmax(candidates))
    return {
        "value": float(slopes[idx]),
        "magnitude": float(abs(slopes[idx])),
        "time": float(positions[idx]),
    }


def slope_reduction_percent(raw, processed):
    """
    Reduction de la pente maximale, en pourcentage.

    Une valeur positive signifie que le traitement a adouci la courbe, une
    valeur negative qu'il l'a durcie.

    Args:
        raw: Dict retourne par max_slope pour les donnees brutes
        processed: Dict retourne par max_slope pour la courbe traitee

    Returns:
        Pourcentage de reduction, ou None si non calculable
    """
    if not raw or not processed:
        return None
    if raw["magnitude"] <= 0:
        return None
    return (1.0 - processed["magnitude"] / raw["magnitude"]) * 100.0


def format_slope_value(value):
    """Formatage compact d'une pente, lisible quel que soit l'ordre de grandeur."""
    magnitude = abs(value)
    if magnitude == 0:
        return "0"
    if 1e-2 <= magnitude < 1e5:
        return f"{value:.4g}"
    return f"{value:.3e}"
