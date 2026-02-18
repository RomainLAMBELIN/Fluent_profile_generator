"""
Module de gestion des entrées/sorties (lecture CSV, export .prof)
"""

import os
import pandas as pd
import numpy as np
from typing import Dict

from core.constants import DEFAULT_FLOW_EPS


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
