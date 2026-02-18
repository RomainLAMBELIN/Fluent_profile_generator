.PHONY: help install install-dev test test-cov run clean format lint

help:
	@echo "Commandes disponibles:"
	@echo "  make install      - Installer les dépendances de production"
	@echo "  make install-dev  - Installer les dépendances de développement"
	@echo "  make test         - Lancer les tests"
	@echo "  make test-cov     - Lancer les tests avec couverture"
	@echo "  make run          - Lancer l'application"
	@echo "  make format       - Formater le code avec black"
	@echo "  make lint         - Vérifier le code avec flake8"
	@echo "  make clean        - Nettoyer les fichiers temporaires"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=src --cov-report=html --cov-report=term

run:
	python launch.py

format:
	black src/ tests/

lint:
	flake8 src/ tests/ --max-line-length=120

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage build/ dist/
