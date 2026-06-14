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


INDEX_CARS_ARGS :=

ifdef START_AFTER_CAR_ID
INDEX_CARS_ARGS += --start-after-car-id $(START_AFTER_CAR_ID)
endif

ifdef LIMIT
INDEX_CARS_ARGS += --limit $(LIMIT)
endif

ifdef BATCH_SIZE
INDEX_CARS_ARGS += --batch-size $(BATCH_SIZE)
endif

ifdef QDRANT_BATCH_SIZE
INDEX_CARS_ARGS += --qdrant-batch-size $(QDRANT_BATCH_SIZE)
endif

ifdef EMBEDDING_BATCH_SIZE
INDEX_CARS_ARGS += --embedding-batch-size $(EMBEDDING_BATCH_SIZE)
endif

ifdef DRY_RUN
INDEX_CARS_ARGS += --dry-run
endif

.PHONY: index-all-cars
index-all-cars:
	uv run python -m src.commands.bulk_index_cars $(INDEX_CARS_ARGS)


RETRIEVE_ARGS :=

ifdef QUERY
RETRIEVE_ARGS += "$(QUERY)"
endif

ifdef TOP_K
RETRIEVE_ARGS += --top-k $(TOP_K)
endif

ifdef BRAND_NAME
RETRIEVE_ARGS += --brand-name "$(BRAND_NAME)"
endif

ifdef MODEL_NAME
RETRIEVE_ARGS += --model-name "$(MODEL_NAME)"
endif

ifdef SUBMODEL_NAME
RETRIEVE_ARGS += --submodel-name "$(SUBMODEL_NAME)"
endif

ifdef CHUNK_TYPE
RETRIEVE_ARGS += --chunk-type "$(CHUNK_TYPE)"
endif

ifdef FUEL_TYPE
RETRIEVE_ARGS += --fuel-type "$(FUEL_TYPE)"
endif

ifdef IS_EV
RETRIEVE_ARGS += --is-ev
endif

ifdef MIN_PRICE
RETRIEVE_ARGS += --min-price $(MIN_PRICE)
endif

ifdef MAX_PRICE
RETRIEVE_ARGS += --max-price $(MAX_PRICE)
endif


.PHONY: test-retrieval
test-retrieval:
	uv run python -m src.commands.test_retrieval $(RETRIEVE_ARGS)


.PHONY: rag-cli
rag-cli:
	uv run python -m src.commands.rag_cli