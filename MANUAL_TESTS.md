# Guide de tests manuels

Ce document décrit comment tester manuellement l'application sans pytest.

## Test 1 : Lecture de fichiers CSV

```python
import sys
sys.path.insert(0, 'src')

from core.io import read_csv_data
import os

# Test lecture fichier Q
q_file = "tests/fixtures/test_Q.csv"
df_q = read_csv_data(q_file, data_type="Q")
print("✓ Lecture fichier Q réussie")
print(f"  Lignes: {len(df_q)}, Première valeur: {df_q['Value'].iloc[0]}")

# Test lecture fichier T
t_file = "tests/fixtures/test_T.csv"
df_t = read_csv_data(t_file, data_type="T")
print("✓ Lecture fichier T réussie")
print(f"  Lignes: {len(df_t)}, Première valeur: {df_t['Value'].iloc[0]}")
```

## Test 2 : Interpolation

```python
import sys
sys.path.insert(0, 'src')

import numpy as np
from core.io import read_csv_data
from core.interpolation import interpolate_smooth

# Charger données
df = read_csv_data("tests/fixtures/test_Q.csv", data_type="Q")

# Interpoler
times = np.linspace(0, df['Time_s'].iloc[-1], 100)
result = interpolate_smooth(df, times, smooth_factor=0.001)

print("✓ Interpolation réussie")
print(f"  Points originaux: {len(df)}")
print(f"  Points interpolés: {len(result)}")
print(f"  Valeur min: {result.min():.3f}, max: {result.max():.3f}")
```

## Test 3 : Export .prof

```python
import sys
sys.path.insert(0, 'src')

import numpy as np
from core.io import export_prof

# Créer des données de test
times = np.array([0.0, 0.001, 0.002, 0.003])
data = {
    "Q_inlet1": np.array([0.0, 1.0, 2.0, 3.0]),
    "T_inlet1": np.array([300.0, 301.0, 302.0, 303.0]),
}

# Exporter
export_prof("test_output.prof", times, data)
print("✓ Export réussi: test_output.prof")

# Vérifier le contenu
with open("test_output.prof", "r") as f:
    content = f.read()
    print("\nContenu du fichier:")
    print(content[:200] + "...")
```

## Test 4 : Lancement de l'application

```bash
# Depuis la racine du projet
python src/main.py
```

L'application devrait se lancer avec l'interface graphique.

## Vérifications

### Étape 1 - Sélection des fichiers
- [ ] Les 4 boutons "Parcourir..." fonctionnent
- [ ] Les chemins s'affichent correctement
- [ ] Le bouton "Suivant" est désactivé tant que tous les fichiers ne sont pas sélectionnés
- [ ] Message d'erreur si on clique "Suivant" sans avoir sélectionné tous les fichiers

### Étape 2 - Paramètres
- [ ] Les sliders fonctionnent
- [ ] Les valeurs s'affichent et se mettent à jour
- [ ] Les graphiques se mettent à jour en temps réel
- [ ] Les onglets fonctionnent (Q_inlet1, T_inlet1, Q_inlet2, T_inlet2)
- [ ] Les courbes brutes et interpolées sont visibles
- [ ] Bouton "Précédent" ramène à l'étape 1 (fichiers toujours sélectionnés)

### Étape 3 - Prévisualisation
- [ ] Le graphique 2x2 s'affiche correctement
- [ ] Les informations (durée, nb points, etc.) sont affichées
- [ ] Bouton "Précédent" permet de revenir ajuster les paramètres
- [ ] Les paramètres sont conservés quand on revient

### Étape 4 - Export
- [ ] Le bouton "Exporter" ouvre le dialogue de sauvegarde
- [ ] Le fichier .prof est créé
- [ ] Le message de succès s'affiche avec les bonnes informations
- [ ] Le fichier .prof peut être ouvert et contient les bonnes données

## Tests de régression

### Navigation flexible
1. Aller jusqu'à l'étape 3 (Prévisualisation)
2. Retourner à l'étape 2 (Paramètres)
3. Modifier un paramètre (ex: smooth_Q)
4. Aller à l'étape 3
5. **Vérifier** : Les courbes ont été recalculées avec les nouveaux paramètres

### Conservation de l'état
1. Sélectionner les 4 fichiers
2. Aller à l'étape 2
3. Retourner à l'étape 1
4. **Vérifier** : Les fichiers sont toujours sélectionnés
5. Aller à l'étape 2
6. Configurer les paramètres
7. Retourner à l'étape 1, puis revenir à l'étape 2
8. **Vérifier** : Les paramètres sont conservés
