# Guide de contribution

Merci de votre intérêt pour contribuer à Fluent Profile Generator !

## Installation pour le développement

```bash
# Cloner le dépôt
git clone <repo-url>
cd fluent-prof-generator

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Installer les dépendances de développement
pip install -r requirements-dev.txt
```

## Workflow de développement

1. **Créer une branche** pour votre fonctionnalité ou correction
   ```bash
   git checkout -b feature/ma-nouvelle-fonctionnalite
   ```

2. **Développer** en suivant les bonnes pratiques :
   - Écrire des tests pour toute nouvelle fonctionnalité
   - Maintenir la couverture de code > 80%
   - Suivre le style PEP 8

3. **Tester** votre code
   ```bash
   make test
   make test-cov  # Avec rapport de couverture
   ```

4. **Formater** le code
   ```bash
   make format
   ```

5. **Vérifier** la qualité du code
   ```bash
   make lint
   ```

6. **Commiter** vos changements
   ```bash
   git add .
   git commit -m "feat: description de la fonctionnalité"
   ```

7. **Pousser** et créer une Pull Request
   ```bash
   git push origin feature/ma-nouvelle-fonctionnalite
   ```

## Standards de code

### Style
- Suivre PEP 8
- Utiliser Black pour le formatage automatique
- Longueur maximale de ligne : 120 caractères

### Tests
- Tous les modules `core` doivent avoir une couverture > 90%
- Utiliser pytest pour tous les tests
- Nommer les tests de manière descriptive : `test_<fonction>_<cas>`

### Documentation
- Documenter toutes les fonctions publiques avec des docstrings
- Format : Google style docstrings
- Inclure les types dans les signatures de fonction

### Commits
Format des messages de commit :
- `feat:` Nouvelle fonctionnalité
- `fix:` Correction de bug
- `docs:` Documentation
- `test:` Ajout/modification de tests
- `refactor:` Refactoring sans changement de fonctionnalité
- `style:` Formatage, point-virgules manquants, etc.

## Structure du projet

```
src/
├── core/           # Logique métier (IO, interpolation)
├── gui/            # Interface graphique
│   └── steps/      # Modules pour chaque étape
└── main.py         # Point d'entrée

tests/              # Tests unitaires
├── fixtures/       # Données de test
├── test_io.py
└── test_interpolation.py
```

## Ajouter une nouvelle fonctionnalité

1. **Core** : Ajouter la logique dans `src/core/`
2. **Tests** : Créer `tests/test_<module>.py`
3. **GUI** : Modifier ou créer un step dans `src/gui/steps/`
4. **Documentation** : Mettre à jour README.md si nécessaire

## Questions ?

N'hésitez pas à ouvrir une issue pour toute question !
