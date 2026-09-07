"""
Constantes de l'application
"""

import re

# Paramètres par défaut
DEFAULT_DT_US = 1.0  # Pas de temps par défaut en µs
DEFAULT_FLOW_EPS = 1e-5  # Remplacement des débits nuls (évite divergence Fluent)
DEFAULT_SMOOTH_Q = 0.001  # Facteur de lissage pour les débits
DEFAULT_SMOOTH_T = 0.01   # Facteur de lissage pour les températures

# Méthodes d'interpolation disponibles
INTERP_METHODS = {
    "pchip": "PCHIP",
    "spline": "Spline lissée",
    "trend_l2": "Trend Filter L2",
    "trend_l1": "Trend Filter L1",
    "linear": "Linéaire",
}
DEFAULT_INTERP_METHOD = "pchip"

# Descriptions détaillées des méthodes (pour l'aide)
INTERP_METHODS_HELP = {
    "pchip": """PCHIP (Piecewise Cubic Hermite Interpolating Polynomial)

Interpolation exacte qui passe par tous les points de données.
Préserve la monotonie locale (pas d'oscillations entre points).

Avantages : Exacte, stable, préserve la monotonie
Inconvénients : Peut amplifier le bruit si données bruitées

Recommandé pour : Données propres et précises""",

    "spline": """Spline Cubique Lissée

Spline cubique avec paramètre de lissage ajustable.
Ne passe pas exactement par les points (compromis fidélité/lissage).

Avantages : Contrôle fin du lissage
Inconvénients : Peut osciller aux extrémités

Paramètre : Plus le facteur est grand, plus la courbe est lissée.
Recommandé pour : Données légèrement bruitées""",

    "trend_l2": """Trend Filter L2 (Ridge / HP Filter)

Minimise : ||données - résultat||² + lambda ||courbure||²

Produit une courbe globalement lissée en pénalisant les courbures.
Très efficace pour réduire les variations "violentes".

Avantages : Réduit oscillations, stable numériquement
Inconvénients : Peut trop lisser les détails fins

Paramètre lambda : Plus grand = plus lisse (typique: 1-50)
Recommandé pour : Simulations CFD, conditions aux limites""",

    "trend_l1": """Trend Filter L1 (Total Variation)

Minimise : ||données - résultat||² + lambda ||courbure||_1

Produit une courbe simplifiée avec segments de courbure constante.
Préserve mieux les changements brusques légitimes.

Avantages : Très robuste au bruit, préserve les transitions
Inconvénients : Peut créer des "plateaux"

Paramètre lambda : Plus grand = plus simple (typique: 1-20)
Recommandé pour : Données très bruitées avec transitions nettes""",

    "linear": """Interpolation Linéaire

Segments de droites entre chaque paire de points consécutifs.
La méthode la plus simple et la plus rapide.

Avantages : Simple, rapide, pas d'oscillations
Inconvénients : Discontinuités de pente aux points

Recommandé pour : Validation rapide, données peu nombreuses""",
}

# Paramètres par défaut pour Trend Filtering
DEFAULT_TREND_LAMBDA = 1.0  # Paramètre de régularisation par défaut
TREND_LAMBDA_MIN = 0.01
TREND_LAMBDA_MAX = 100.0
DEFAULT_TREND_PADDING = 3  # Nombre de points de padding

# Paramètres d'interpolation
MIN_POINTS_REQUIRED = 4  # Nombre minimum de points pour l'interpolation
SPLINE_DEGREE = 3  # Degré de la spline cubique

# Paramètres Savitzky-Golay (conservés pour compatibilité)
DEFAULT_SAVGOL_WINDOW = 11  # Taille de fenêtre (impair)
DEFAULT_SAVGOL_POLYORDER = 3  # Degré du polynôme

# Limites pour les paramètres de lissage
SMOOTH_MIN = 0.0
SMOOTH_MAX = 0.1

# Performance - limite de points pour la prévisualisation
MAX_PREVIEW_POINTS = 5000

# Nombre d'inlets proposés par défaut, tant qu'aucune colonne n'est détectée
DEFAULT_INLET_COUNT = 2

# ---------------------------------------------------------------------------
# Patterns regex pour auto-détection des colonnes CSV
# ---------------------------------------------------------------------------

# Colonnes de temps : "time", "t", "temps", "Time_ms", etc.
# Note: "t" seul = temps (pas température)
TIME_COLUMN_PATTERNS = [
    re.compile(r"^time[_\s]?.*$", re.IGNORECASE),
    re.compile(r"^t$", re.IGNORECASE),
    re.compile(r"^temps$", re.IGNORECASE),
    re.compile(r"^time$", re.IGNORECASE),
]

# Colonnes de débit : "q", "q1", "q_inlet1", "debit", "flow", etc.
FLOW_COLUMN_PATTERNS = [
    re.compile(r"^q\d*$", re.IGNORECASE),
    re.compile(r"^q[_\s]", re.IGNORECASE),
    re.compile(r"^debit", re.IGNORECASE),
    re.compile(r"^flow", re.IGNORECASE),
]

# Colonnes de température : "t1", "t2", "temp", "temperature", etc.
# Note: "t" seul est reconnu comme temps, pas température
TEMP_COLUMN_PATTERNS = [
    re.compile(r"^t\d+$", re.IGNORECASE),
    re.compile(r"^t[_\s]", re.IGNORECASE),
    re.compile(r"^temp", re.IGNORECASE),
    re.compile(r"^temperature", re.IGNORECASE),
]

# ---------------------------------------------------------------------------
# Fonctions utilitaires pour génération dynamique de clés/labels
# ---------------------------------------------------------------------------


def generate_file_keys(n_inlets: int) -> list:
    """
    Génère la liste des clés de fichiers pour N inlets.

    Args:
        n_inlets: Nombre d'inlets

    Returns:
        Liste de clés, ex: ["Q_inlet1", "T_inlet1", "Q_inlet2", "T_inlet2"]
    """
    keys = []
    for i in range(1, n_inlets + 1):
        keys.append(f"Q_inlet{i}")
        keys.append(f"T_inlet{i}")
    return keys


def generate_file_labels(inlet_names: dict) -> dict:
    """
    Génère les labels d'affichage pour l'interface.

    Args:
        inlet_names: Dict {inlet_idx: nom_personnalisé}, ex: {1: "tulipe", 2: "tige"}

    Returns:
        Dict {clé: label}, ex: {"Q_inlet1": "Débit tulipe (Q)", ...}
    """
    labels = {}
    for idx, name in inlet_names.items():
        labels[f"Q_inlet{idx}"] = f"Débit {name} (Q)"
        labels[f"T_inlet{idx}"] = f"Température {name} (T)"
    return labels
