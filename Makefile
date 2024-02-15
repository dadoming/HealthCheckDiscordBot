
# Activate Virtual Environment
activate:
	@echo "Activating Virtual Environment"
	@source bot-env/bin/activate

# Deactivate Virtual Environment
deactivate:
	@echo "Deactivating Virtual Environment"
	@deactivate

.PHONY: activate deactivate
