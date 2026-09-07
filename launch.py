#!/usr/bin/env python
"""
Script de lancement de l'application Fluent Profile Generator
À exécuter depuis la racine du projet
"""

import sys
import os

# Ajouter le répertoire src au path
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

# Importer et lancer l'application
from gui.app import run

if __name__ == "__main__":
    run()
