"""
Module de gestion des entrées/sorties (lecture CSV, export .prof)
"""

import os
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional

from core.constants import (
    DEFAULT_FLOW_EPS,
    TIME_COLUMN_PATTERNS, FLOW_COLUMN_PATTERNS, TEMP_COLUMN_PATTERNS,
)


def _is_numeric_series(s: pd.Series) -> bool:
    """
    Vérifie si une série pandas peut être convertie en valeurs numériques.

    Args:
        s: Série pandas à vérifier

    Returns:
        True si au moins 90% des valeurs sont numériques et valides
    """
    ss = pd.to_numeric(s, errors="coerce")
    if len(ss) == 0:
        return False
    valid = ss.notna().sum()
    return valid >= max(2, int(0.9 * len(ss))) and valid > 0


def read_two_cols_csv(filename: str, names=("Time_ms", "Value")) -> pd.DataFrame:
    """
    Lit un fichier CSV à 2 colonnes en détectant automatiquement le format.

    Détection automatique de :
    - Séparateur : tabulation, point-virgule, virgule, espaces multiples
    - Format décimal : '.' ou ','

    Les lignes commençant par '#' sont ignorées (commentaires).

    Args:
        filename: Chemin du fichier CSV
        names: Tuple avec les noms des 2 colonnes

    Returns:
        DataFrame avec les 2 colonnes nommées

    Raises:
        ValueError: Si le fichier ne peut pas être lu ou n'a pas le bon format
    """
    candidates = [
        {"sep": "\t", "decimal": "."},
        {"sep": ";", "decimal": ","},
        {"sep": ";", "decimal": "."},
        {"sep": ",", "decimal": "."},
        {"sep": r"\s+", "decimal": ".", "engine": "python"},
    ]
    last_err = None

    for opts in candidates:
        try:
            kw = dict(header=None, names=list(names), comment="#")
            kw["sep"] = opts["sep"]
            kw["decimal"] = opts["decimal"]
            if "engine" in opts:
                kw["engine"] = opts["engine"]

            df = pd.read_csv(filename, **kw)

            # Validation : exactement 2 colonnes numériques
            if df.shape[1] != 2:
                continue
            if not (_is_numeric_series(df[names[0]]) and _is_numeric_series(df[names[1]])):
                continue

            return df.dropna().reset_index(drop=True)

        except Exception as e:
            last_err = e
            continue

    raise ValueError(
        f"Impossible de lire '{os.path.basename(filename)}'. "
        f"Format attendu: 2 colonnes (temps_ms, valeur). "
        f"Dernière erreur: {last_err}"
    )


def read_csv_data(filename: str, data_type: str = "Q") -> pd.DataFrame:
    """
    Lit un fichier CSV et retourne un DataFrame normalisé.

    Args:
        filename: Chemin du fichier CSV
        data_type: Type de données - "Q" (débit) ou "T" (température)

    Returns:
        DataFrame avec colonnes ['Time_s', 'Value']
        - Time_s : temps en secondes
        - Value : valeur (débit ou température)

    Raises:
        ValueError: Si le fichier est vide ou invalide

    Note:
        Pour les débits (Q), la valeur initiale est forcée à 0.
    """
    df = read_two_cols_csv(filename, names=("Time_ms", "Value"))

    if df.empty:
        raise ValueError(f"Fichier vide: {filename}")

    # Conversion ms → s
    df["Time_s"] = pd.to_numeric(df["Time_ms"], errors="coerce").astype(float) / 1000.0
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce").astype(float)

    # Pour les débits, forcer la valeur initiale à 0
    if data_type == "Q":
        if df["Time_s"].iloc[0] > 0:
            # Ajouter un point à t=0 avec valeur 0
            df = pd.concat(
                [pd.DataFrame([{"Time_ms": 0.0, "Value": 0.0, "Time_s": 0.0}]), df],
                ignore_index=True,
            )
        else:
            # Forcer la première valeur à 0
            df.loc[df.index[0], "Value"] = 0.0

    # Nettoyage et tri
    return (
        df[["Time_s", "Value"]]
        .dropna()
        .drop_duplicates("Time_s")
        .sort_values("Time_s")
        .reset_index(drop=True)
    )


# ---------------------------------------------------------------------------
# Nouvelles fonctions pour CSV multi-colonnes
# ---------------------------------------------------------------------------

def read_multi_column_csv(filename: str) -> pd.DataFrame:
    """
    Lit un fichier CSV multi-colonnes avec header.

    Auto-détection du séparateur et du format décimal
    (même logique que read_two_cols_csv).

    Args:
        filename: Chemin du fichier CSV

    Returns:
        DataFrame complet avec toutes les colonnes

    Raises:
        ValueError: Si le fichier ne peut pas être lu
    """
    candidates = [
        {"sep": "\t", "decimal": "."},
        {"sep": ";", "decimal": ","},
        {"sep": ";", "decimal": "."},
        {"sep": ",", "decimal": "."},
        {"sep": r"\s+", "decimal": ".", "engine": "python"},
    ]
    last_err = None

    for opts in candidates:
        try:
            kw = dict(header=0, comment="#")
            kw["sep"] = opts["sep"]
            kw["decimal"] = opts["decimal"]
            if "engine" in opts:
                kw["engine"] = opts["engine"]

            df = pd.read_csv(filename, **kw)

            # Validation : au moins 3 colonnes (temps + Q + T minimum)
            if df.shape[1] < 3:
                continue

            # Vérifier qu'au moins 2 colonnes sont numériques
            numeric_count = sum(1 for col in df.columns if _is_numeric_series(df[col]))
            if numeric_count < 2:
                continue

            # Convertir les colonnes numériques
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

            return df.dropna(how="all").reset_index(drop=True)

        except Exception as e:
            last_err = e
            continue

    raise ValueError(
        f"Impossible de lire '{os.path.basename(filename)}'. "
        f"Format attendu: CSV multi-colonnes avec header. "
        f"Dernière erreur: {last_err}"
    )


def _match_column(col_name: str, patterns: list) -> bool:
    """Vérifie si un nom de colonne correspond à l'un des patterns regex."""
    for pattern in patterns:
        if pattern.search(col_name):
            return True
    return False


def detect_columns(df: pd.DataFrame) -> dict:
    """
    Auto-détection des rôles des colonnes par regex sur les noms.

    Priorité : temps d'abord, puis Q (débit), puis T (température).

    Args:
        df: DataFrame avec header

    Returns:
        {
            "time_col": str or None,
            "q_cols": [str, ...],
            "t_cols": [str, ...],
            "unmapped_cols": [str, ...]
        }
    """
    result = {
        "time_col": None,
        "q_cols": [],
        "t_cols": [],
        "unmapped_cols": [],
    }

    remaining = list(df.columns)

    # 1. Détecter la colonne de temps
    for col in remaining:
        if _match_column(col, TIME_COLUMN_PATTERNS):
            result["time_col"] = col
            remaining.remove(col)
            break

    # Si pas trouvé, prendre la première colonne comme temps
    if result["time_col"] is None and remaining:
        result["time_col"] = remaining[0]
        remaining.remove(remaining[0])

    # 2. Détecter les colonnes de débit
    for col in list(remaining):
        if _match_column(col, FLOW_COLUMN_PATTERNS):
            result["q_cols"].append(col)
            remaining.remove(col)

    # 3. Détecter les colonnes de température
    for col in list(remaining):
        if _match_column(col, TEMP_COLUMN_PATTERNS):
            result["t_cols"].append(col)
            remaining.remove(col)

    # 4. Tout le reste
    result["unmapped_cols"] = remaining

    return result


def extract_inlet_data(
    df: pd.DataFrame,
    time_col: str,
    column_mapping: List[Tuple[str, str, int]],
) -> Dict[str, pd.DataFrame]:
    """
    Extrait les données par inlet à partir du DataFrame multi-colonnes.

    Args:
        df: DataFrame source (multi-colonnes)
        time_col: Nom de la colonne de temps
        column_mapping: Liste de tuples (q_col, t_col, inlet_idx)
                        ex: [("Q1", "T1", 1), ("Q2", "T2", 2)]

    Returns:
        Dict {clé: DataFrame} avec clés comme "Q_inlet1", "T_inlet1", etc.
        Chaque DataFrame a les colonnes ['Time_s', 'Value'].
        Conversion ms->s appliquée, Q forcé à 0 à t=0.
    """
    result = {}
    time_values = pd.to_numeric(df[time_col], errors="coerce").astype(float)
    # Conversion ms → s
    time_s = time_values / 1000.0

    for q_col, t_col, inlet_idx in column_mapping:
        # --- Débit ---
        q_key = f"Q_inlet{inlet_idx}"
        q_values = pd.to_numeric(df[q_col], errors="coerce").astype(float)
        q_df = pd.DataFrame({"Time_s": time_s, "Value": q_values})
        q_df = q_df.dropna().drop_duplicates("Time_s").sort_values("Time_s").reset_index(drop=True)

        # Forcer Q=0 à t=0
        if not q_df.empty:
            if q_df["Time_s"].iloc[0] > 0:
                q_df = pd.concat(
                    [pd.DataFrame([{"Time_s": 0.0, "Value": 0.0}]), q_df],
                    ignore_index=True,
                )
            else:
                q_df.loc[q_df.index[0], "Value"] = 0.0

        result[q_key] = q_df

        # --- Température ---
        t_key = f"T_inlet{inlet_idx}"
        t_values = pd.to_numeric(df[t_col], errors="coerce").astype(float)
        t_df = pd.DataFrame({"Time_s": time_s, "Value": t_values})
        t_df = t_df.dropna().drop_duplicates("Time_s").sort_values("Time_s").reset_index(drop=True)

        result[t_key] = t_df

    return result


# ---------------------------------------------------------------------------
# Fonctions existantes (compatibilité)
# ---------------------------------------------------------------------------

def export_prof(filename: str, times: np.ndarray, data_dict: Dict[str, np.ndarray]) -> None:
    """
    Exporte les données au format .prof tabulaire de Fluent.

    Format attendu par Fluent (2D axisymétrique) :
        profile N_cols N_points 0
        time Q_inlet1 T_inlet1 Q_inlet2 T_inlet2
        0.0000000000 0.000010 299.624093 -0.022578 300.000000
        0.0000010000 -0.008357 299.625100 -0.022629 300.000000
        ...

    Args:
        filename: Chemin du fichier de sortie
        times: Array numpy des temps (en secondes)
        data_dict: Dictionnaire {nom_colonne: array_valeurs}
                   Les clés sont déjà renommées (ex: Q_Pin, T_Pin, Q_Tul, T_Tul)

    Raises:
        IOError: Si l'écriture échoue
    """
    n_points = len(times)
    n_cols = 1 + len(data_dict)  # time + toutes les colonnes de données

    # Trier les colonnes : Q et T alternés par inlet pour lisibilité
    # Format attendu: Q_inlet1, T_inlet1, Q_inlet2, T_inlet2, ...
    col_names = sorted(data_dict.keys(), key=lambda k: (k.split('_')[-1], k[0]))

    # Construire la matrice de données pour écriture vectorisée
    matrix = np.column_stack([times] + [data_dict[c] for c in col_names])

    with open(filename, "w") as f:
        # Ligne 1: profile N_cols N_points 0
        f.write(f"profile {n_cols} {n_points} 0\n")

        # Ligne 2: noms des colonnes
        f.write("time " + " ".join(col_names) + "\n")

        # Écriture vectorisée avec np.savetxt
        fmt = ["%.10f"] + ["%.6f"] * len(col_names)
        np.savetxt(f, matrix, fmt=fmt, delimiter=" ")


def load_all_files(file_paths: Dict[str, str]) -> Dict[str, pd.DataFrame]:
    """
    Charge tous les fichiers CSV et retourne les DataFrames.

    Args:
        file_paths: Dictionnaire {clé: chemin_fichier}
                    Les clés doivent commencer par "Q_" ou "T_"

    Returns:
        Dictionnaire {clé: DataFrame}

    Raises:
        ValueError: Si un fichier ne peut pas être chargé
    """
    data = {}

    for key, filepath in file_paths.items():
        if not filepath:
            raise ValueError(f"Aucun fichier sélectionné pour {key}")

        data_type = "Q" if key.startswith("Q_") else "T"
        data[key] = read_csv_data(filepath, data_type=data_type)

    return data


def get_max_simulation_time(data_dict: Dict[str, pd.DataFrame]) -> float:
    """
    Détermine la durée maximale de simulation à partir des données.

    Args:
        data_dict: Dictionnaire {clé: DataFrame}

    Returns:
        Durée maximale en secondes

    Raises:
        ValueError: Si aucune donnée n'est disponible
    """
    if not data_dict:
        raise ValueError("Aucune donnée disponible")

    max_time = 0.0
    for df in data_dict.values():
        if not df.empty:
            max_time = max(max_time, df["Time_s"].iloc[-1])

    if max_time <= 0:
        raise ValueError("Durée de simulation invalide (≤ 0)")

    return max_time
