"""
Utilitaires pour l'analyse des données interpolées
"""

import numpy as np
from scipy.integrate import trapezoid


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
        return f"Erreur abs: {err_abs:.2e}"
    else:
        return f"Erreur: {err_rel:.3f}% (abs: {err_abs:.2e})"
