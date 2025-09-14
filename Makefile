# Discord Mod Mail Bot Makefile

.PHONY: help install setup run build up down logs clean test lint format

# Default target
help:
	@echo "Discord Mod Mail Bot - Available Commands:"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  setup     - Set up the project (create directories, copy env template)"
	@echo "  install   - Install Python dependencies"
	@echo "  check-python - Check if Python version is compatible"
	@echo ""
	@echo "Development:"
	@echo "  run       - Run the bot in development mode"
	@echo "  test      - Run tests (placeholder)"
	@echo "  lint      - Run linting checks"
	@echo "  format    - Format code with black"
	@echo ""
	@echo "Docker:"
	@echo "  build     - Build Docker image"
	@echo "  up        - Start the bot with Docker Compose"
	@echo "  down      - Stop the bot and remove containers"
	@echo "  logs      - View bot logs"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean     - Clean up temporary files and database"
	@echo ""

# Setup project
setup:
	@echo "Setting up Discord Mod Mail Bot..."
	@mkdir -p data
	@if [ ! -f .env ]; then \
		cp .env.template .env; \
		echo "Created .env file from template. Please edit it with your configuration."; \
	fi
	@echo "Setup complete!"

# Install dependencies
install:
	@echo "Installing Python dependencies..."
	@if [ -d .venv ]; then \
		echo "Activating virtual environment..."; \
		. .venv/bin/activate; \
	fi
	@if python -c "import sys; exit(0 if sys.version_info[:2] == (3, 13) else 1)" 2>/dev/null; then \
		echo "Python 3.13 detected, using development discord.py..."; \
		pip install -r requirements-py313.txt; \
	else \
		pip install -r requirements.txt; \
	fi
	@echo "Dependencies installed!"

# Check Python version
check-python:
	@echo "Checking Python version..."
	@python check_python.py

# Run bot in development mode
run: check-python install
	@echo "Starting Discord Mod Mail Bot..."
	@if [ -d .venv ]; then \
		echo "Activating virtual environment..."; \
		. .venv/bin/activate; \
	fi
	python bot.py

# Build Docker image
build:
	@echo "Building Docker image..."
	docker build -t discord-modmail-bot .

# Start with Docker Compose
up:
	@echo "Starting Discord Mod Mail Bot with Docker Compose..."
	docker-compose up -d

# Stop Docker Compose
down:
	@echo "Stopping Discord Mod Mail Bot..."
	docker-compose down

# View logs
logs:
	@echo "Viewing bot logs..."
	docker-compose logs -f

# Run tests (placeholder)
test:
	@echo "Running tests..."
	@echo "No tests implemented yet."

# Lint code
lint:
	@echo "Running linting checks..."
	@if command -v flake8 >/dev/null 2>&1; then \
		flake8 bot.py; \
	else \
		echo "flake8 not installed. Install with: pip install flake8"; \
	fi

# Format code
format:
	@echo "Formatting code..."
	@if command -v black >/dev/null 2>&1; then \
		black bot.py; \
	else \
		echo "black not installed. Install with: pip install black"; \
	fi

# Clean up
clean:
	@echo "Cleaning up..."
	@rm -rf __pycache__/
	@rm -rf *.pyc
	@rm -rf .pytest_cache/
	@rm -rf data/*.db
	@echo "Cleanup complete!"

# Development setup
dev: setup install
	@echo "Development environment ready!"
	@echo "Edit .env file with your Discord bot token and channel ID, then run 'make run'"

# Production deployment
deploy: build up
	@echo "Bot deployed! Check logs with 'make logs'"

# Quick restart
restart: down up
	@echo "Bot restarted!"

# Show status
status:
	@echo "Checking bot status..."
	@docker-compose ps
