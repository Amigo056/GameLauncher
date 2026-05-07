# GameLauncher — Makefile
.PHONY: help install install-dev test test-cov lint format type-check clean run check ci

PYTHON := python
PIP := pip

help:
	@echo "GameLauncher — Comandos disponíveis:"
	@echo "  make install      — Instala dependências de produção"
	@echo "  make install-dev  — Instala dependências de desenvolvimento"
	@echo "  make test         — Corre testes unitários"
	@echo "  make test-cov     — Corre testes com cobertura"
	@echo "  make lint         — Corre linter (ruff)"
	@echo "  make format       — Formata código (ruff format)"
	@echo "  make type-check   — Verifica tipos (mypy)"
	@echo "  make check        — Corre lint + type-check + testes"
	@echo "  make ci           — Comando para CI (check completo)"
	@echo "  make clean        — Limpa ficheiros temporários"
	@echo "  make run          — Corre a aplicação"
	@echo "  make pre-commit   — Instala git hooks"

install:
	$(PIP) install -r requirements.txt

install-dev:
	$(PIP) install -r requirements-dev.txt
	pre-commit install

test:
	pytest tests/unit -v

test-cov:
	pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html

test-integration:
	pytest tests/integration -v

lint:
	ruff check src/ tests/

lint-fix:
	ruff check src/ tests/ --fix

format:
	ruff format src/ tests/

type-check:
	mypy src/

check: lint type-check test

ci: format lint type-check test-cov
	@echo "✅ CI check completo"

clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache htmlcov .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete

run:
	$(PYTHON) main.py

pre-commit:
	pre-commit install
	pre-commit run --all-files