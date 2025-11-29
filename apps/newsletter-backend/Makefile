.PHONY: install dev build lint format test clean

# Install dependencies
install:
	uv sync

# Run development server
dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Build (compile Python)
build:
	python -m compileall app/

# Lint code
lint:
	ruff check .

# Fix linting issues
lint-fix:
	ruff check --fix .

# Format code
format:
	ruff format .

# Initialize database
db-init:
	python -c 'from app.database import init_db; init_db()'

# Run tests
test:
	pytest

# Clean cache and build artifacts
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -f newsletter.db
