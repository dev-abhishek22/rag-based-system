dev:
	uv run uvicorn src.main:app --reload

chunks:
	uv run python -m src.commands.build_chunkings $(CAR_ID)

validate-chunks:
	uv run python -m src.commands.validate_chunks --file data/chunks/car_$(CAR_ID)_chunks.json

embed-car:
	uv run python -m src.commands.embed_car_chunks --car-id $(CAR_ID)

vectors-into-qdrant:
	uv run python -m src.commands.vectors_into_qdrant --car-id $(CAR_ID)

index-all-cars:
	uv run python -m src.commands.bulk_index_cars \
		$(if $(START_AFTER_CAR_ID),--start-after-car-id $(START_AFTER_CAR_ID),) \
		$(if $(LIMIT),--limit $(LIMIT),) \
		$(if $(BATCH_SIZE),--batch-size $(BATCH_SIZE),) \
		$(if $(DRY_RUN),--dry-run,)