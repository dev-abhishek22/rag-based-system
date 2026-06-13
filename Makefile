dev:
	uv run uvicorn src.main:app --reload

chunks:
	uv run python -m src.commands.build_chunkings $(CAR_ID)