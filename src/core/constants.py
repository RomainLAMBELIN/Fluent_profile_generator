"""
Constantes de l'application
"""

# Paramètres par défaut
DEFAULT_DT_US = 1.0  # Pas de temps par défaut en µs
DEFAULT_FLOW_EPS = 1e-5  # Remplacement des débits nuls (évite divergence Fluent)
DEFAULT_SMOOTH_Q = 0.001  # Facteur de lissage pour les débits
DEFAULT_SMOOTH_T = 0.01   # Facteur de lissage pour les températures

# Méthodes d'interpolation disponibles
INTERP_METHODS = {
    "pchip": "PCHIP (monotone, exacte)",
    "spline": "Spline lissée (contrôle du lissage)",
    "linear": "Linéaire (segments droits)",
    "akima": "Akima (cubique locale, peu d'oscillations)",
    "makima": "Makima (Akima modifié, robuste aux aberrations)",
    "savgol": "Savitzky-Golay (filtre polynomial)",
}
DEFAULT_INTERP_METHOD = "pchip"

# Méthodes nécessitant un paramètre de lissage
METHODS_WITH_SMOOTHING = {"spline", "savgol"}

# Descriptions détaillées des méthodes
INTERP_METHODS_HELP = {
    "pchip": "Interpolation exacte préservant la monotonie. Idéal pour données propres.",
    "spline": "Spline cubique avec lissage ajustable. Le plus flexible.",
    "linear": "Segments de droites entre chaque point. Simple et rapide.",
    "akima": "Interpolation cubique locale minimisant les oscillations. Idéal pour changements brusques.",
    "makima": "Akima modifié, plus robuste aux valeurs aberrantes et pics isolés.",
    "savgol": "Filtre polynomial par fenêtre glissante. Excellent pour bruit haute fréquence.",
}

# Noms par défaut des inlets
DEFAULT_INLET_NAMES = ["inlet1", "inlet2"]

# Paramètres d'interpolation
MIN_POINTS_REQUIRED = 4  # Nombre minimum de points pour l'interpolation
SPLINE_DEGREE = 3  # Degré de la spline cubique

# Transitions entre segments
TRANSITION_MIN = 0.0
TRANSITION_MAX = 0.10  # Maximum 10%
DEFAULT_TRANSITION_RATIO = 0.02  # Ratio de transition par défaut (2%)

# Paramètres Savitzky-Golay
DEFAULT_SAVGOL_WINDOW = 11  # Taille de fenêtre (impair)
DEFAULT_SAVGOL_POLYORDER = 3  # Degré du polynôme

# Clés des fichiers d'entrée
FILE_KEYS = ["Q_inlet1", "T_inlet1", "Q_inlet2", "T_inlet2"]

# Labels pour l'interface
FILE_LABELS = {
    "Q_inlet1": "Débit Inlet 1 (Q)",
    "T_inlet1": "Température Inlet 1 (T)",
    "Q_inlet2": "Débit Inlet 2 (Q)",
    "T_inlet2": "Température Inlet 2 (T)",
}

# Limites pour les paramètres de lissage
SMOOTH_MIN = 0.0
SMOOTH_MAX = 0.1

# Performance - limite de points pour la prévisualisation
MAX_PREVIEW_POINTS = 5000
