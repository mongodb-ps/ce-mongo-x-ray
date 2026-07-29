.DEFAULT_GOAL := build
.PHONY: build clean deps test check-lint minify help

# Project name
PROJECT_NAME = x-ray

# Detect OS and set Python path accordingly
ifeq ($(OS),Windows_NT)
	# Use forward slashes to be compatible with Git Bash and cmd
	PYTHON = .venv/Scripts/python.exe
	VENV_ACTIVATE = .venv/Scripts/activate
	RM = cmd /C rmdir /S /Q
	MKDIR = cmd /C mkdir
	DELIMITER = ;
else
	PYTHON = .venv/bin/python
	VENV_ACTIVATE = source .venv/bin/activate
	RM = rm -rf
	MKDIR = mkdir -p
	DELIMITER = :
endif

# Install dependencies
deps:
	@echo "Creating virtual environment..."
	python3 -m venv .venv
	@echo "Installing dependencies from pyproject.toml..."
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e ".[dev]" --config-settings editable_mode=compat
	@echo "Activate virtual environment: $(VENV_ACTIVATE)"

# Build executable
build:
	@echo "Building executable..."
	$(PYTHON) -m PyInstaller --onefile --name $(PROJECT_NAME) \
		--add-data="src/x_ray/templates$(DELIMITER)x_ray/templates" \
		--add-data="src/x_ray/config.json$(DELIMITER)x_ray" \
		--add-data="src/x_ray/compatibility_matrix.json$(DELIMITER)x_ray" \
		--additional-hooks-dir=hooks \
		--icon="misc/x-ray.ico" \
		src/x_ray/__main__.py
	@echo "\033[32m✓ Build complete: dist/x-ray\033[0m"

# Run tests 
test:
	@echo "Running tests..."
	$(PYTHON) -m pytest
	@echo "\033[32m✓ All tests passed!\033[0m"

# Run pylint and show only errors
check-lint:
	@echo "Running pylint (errors only)..."
	$(PYTHON) -m pylint src/x_ray/ --rcfile=.pylintrc --errors-only
	@echo "\033[32m✓ No errors found!\033[0m"

# Minify templates
minify:
	@echo "Minifying templates..."
	cd src/x_ray/templates && ./minify.sh
	@echo "\033[32m✓ Templates minified!\033[0m"

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
ifeq ($(OS),Windows_NT)
	@if exist build $(RM) build
	@if exist dist $(RM) dist
	@if exist __pycache__ $(RM) __pycache__
	@if exist $(PROJECT_NAME).spec del /F $(PROJECT_NAME).spec
	@for /d /r %%i in (__pycache__) do @if exist "%%i" $(RM) "%%i"
	@for /d /r %%i in (*.egg-info) do @if exist "%%i" $(RM) "%%i"
	@del /S /Q *.pyc 2>nul || exit 0
else
	rm -rf build/ dist/ __pycache__/
	[ -f $(PROJECT_NAME).spec ] && rm $(PROJECT_NAME).spec || true
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
endif

# Help information
help:
	@echo "X-Ray Project Makefile"
	@echo ""
	@echo "Available commands:"
	@echo "  make deps         - Install dev dependencies declared in pyproject.toml"
	@echo "  make build        - Build executable"
	@echo "  make minify       - Minify HTML/JS templates"
	@echo "  make test         - Run all tests"
	@echo "  make check-lint   - Run pylint (errors only)"
	@echo "  make clean        - Clean build artifacts"
	@echo "  make help         - Display this help information"
