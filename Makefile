dev:
	uv run uvicorn src.main:app --reload

chunks:
	uv run python -m src.commands.build_chunkings $(CAR_ID)

validate-chunks:
	uv run python -m src.commands.validate_chunks --file data/chunks/car_$(CAR_ID)_chunks.json