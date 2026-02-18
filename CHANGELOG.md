# Changelog

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

## [2.0.0] - 2026-01-30

### Ajouté
- Interface guidée en 4 étapes avec navigation flexible
- Visualisation interactive en temps réel lors du paramétrage
- Paramètres de lissage séparés pour débits (Q) et températures (T)
- Possibilité de revenir en arrière pour ajuster les paramètres
- Tests unitaires complets pour les modules core
- Documentation complète (README, CONTRIBUTING, MANUAL_TESTS)
- Configuration CI/CD avec GitHub Actions
- Scripts de lancement rapide (run.sh, run.bat)
- Makefile pour automatiser les tâches courantes

### Modifié
- Refactoring complet de l'architecture en modules séparés
- Amélioration de la lecture CSV avec détection automatique du format
- Utilisation de UnivariateSpline au lieu de PCHIP pour un meilleur contrôle du lissage
- Interface plus moderne et intuitive

### Supprimé
- Gestion de la mobilité (mob.csv) - fonctionnalité obsolète
- Gestion multi-dossiers remplacée par sélection directe des fichiers

## [1.0.0] - 2025-XX-XX

### Ajouté
- Version initiale avec interface basique
- Support des fichiers Q et T
- Interpolation PCHIP
- Export au format .prof
- Gestion de la mobilité
