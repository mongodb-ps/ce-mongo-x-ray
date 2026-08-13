.DEFAULT_GOAL := build
.PHONY: build clean deps test cluster-setup full-test lint minify help

# Project name
PROJECT_NAME = x-ray

# MongoDB binary used to start the test replica set (full-test target).
MONGOD ?= $(shell command -v mongod)

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
	$(PYTHON) -m pytest -m "not integration"
	@echo "\033[32m✓ All tests passed!\033[0m"

# Prepare the test cluster: stop any existing cluster, start a fresh replica
# set, seed it, and generate the getMongoData report.
cluster-setup:
	@echo "Stopping any existing test cluster..."
	@if [ -d .tests/mongo ]; then (cd .tests/mongo && mlaunch stop) 2>/dev/null || true; sleep 5; rm -rf .tests/mongo; fi
	@echo "Starting MongoDB replica set..."
	bash tests/prepare_rs.sh $(MONGOD)
	@echo "Seeding test data..."
	mongosh --quiet mongodb://localhost:47017 misc/redundant_index.js
	mongosh --quiet mongodb://localhost:47017 misc/slow_query_generator.js
	@echo "Generating getMongoData report..."
	mongosh --quiet mongodb://localhost:47017 misc/getMongoData.js > .tests/mongo/getMongoData-output.json
	@echo "Copying an FTDC sample to a stable path..."
	@FTDC_FILE="$$(find .tests/mongo -path '*diagnostic.data*' -name 'metrics.*' -not -name '*.interim' -not -name '*.tmp' | head -1)"; \
		if [ -n "$$FTDC_FILE" ]; then cp "$$FTDC_FILE" .tests/mongo/metrics.final; else echo "WARNING: no finalized FTDC file found" >&2; fi

# Full test: prepare the cluster, then run all tests (including the
# integration-marked UI tests).
full-test: cluster-setup
	@echo "Running all tests..."
	HC_URI="mongodb://localhost:47017" \
		GMD_SAMPLE="$(CURDIR)/.tests/mongo/getMongoData-output.json" \
		LOG_SAMPLE="$(CURDIR)/.tests/mongo/data/replset/rs1/mongod.log" \
		FTDC_SAMPLE="$(CURDIR)/.tests/mongo/metrics.final" \
		$(PYTHON) -m pytest
	@echo "\033[32m✓ All tests passed!\033[0m"

# Run ruff lint
lint:
	@echo "Running ruff check..."
	$(PYTHON) -m ruff check src tests
	@echo "\033[32m✓ No lint errors found!\033[0m"

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
	@echo "  make test         - Run non-integration tests"
	@echo "  make cluster-setup - Start and seed a test cluster"
	@echo "  make full-test    - Start a test cluster and run all tests"
	@echo "  make lint         - Run ruff check (lint)"
	@echo "  make clean        - Clean build artifacts"
	@echo "  make help         - Display this help information"
