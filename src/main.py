"""
Point d'entrée principal de l'application Fluent Profile Generator
"""

import sys
import os

# Ajouter le répertoire src au path pour permettre les imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.app import run


def main():
    """Lance l'application graphique."""
    run()


if __name__ == "__main__":
    main()
