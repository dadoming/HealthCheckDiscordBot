SHELL := /bin/bash

# Define variables
VENV_DIR := bot-env
PYTHON := python3

# Activate Virtual Environment
activate:
	@echo "Activating Virtual Environment"
	source bot-env/bin/activate

# Create Virtual Environment
create-venv:
	@echo "Creating Virtual Environment"
	$(PYTHON) -m venv bot-env

# Deactivate Virtual Environment
deactivate:
	@echo "Deactivating Virtual Environment"
	@deactivate || true

.PHONY: create-venv activate deactivate
