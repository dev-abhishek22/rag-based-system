# RevSearch

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)]()
[![Vector
DB](https://img.shields.io/badge/Qdrant-Vector%20Database-red.svg)]()
[![Embeddings](https://img.shields.io/badge/Embeddings-BAAI%2Fbge--small--en--v1.5-orange.svg)]()

**A domain-specific semantic search engine for automotive
intelligence.**

Repository: https://github.com/dev-abhishek22/revsearch

## Overview

RevSearch is a domain-specific RAG-based semantic search system built
for automotive data. It extracts structured car data from a relational
database, cleans and validates it, converts it into meaningful
domain-specific chunks, generates embeddings, stores them in Qdrant, and
allows semantic search through a terminal-based CLI.

## Architecture

``` text
MySQL Database
     ↓
ETL Layer
     ↓
Cleaning & Validation
     ↓
Domain-Specific Chunking
     ↓
Embedding Generation
     ↓
Qdrant Vector Database
     ↓
Semantic Retrieval
     ↓
RevSearch CLI
```

## Features

-   MySQL-based automotive data extraction
-   ETL service layer
-   Payload cleaning and validation
-   Domain-specific chunking
-   Multiple chunk types:
    -   Car overview
    -   Variants / trims
    -   Pricing
    -   FAQs
    -   Comparisons
    -   Images
    -   News
    -   Features and specifications
-   Embedding service using `BAAI/bge-small-en-v1.5`
-   Batch embedding support
-   Qdrant vector storage
-   Metadata-rich payload indexing
-   Bulk indexing pipeline
-   Semantic retrieval engine
-   Metadata filtering
-   Interactive RevSearch CLI
-   CLI themes
-   Slash commands
-   Search history
-   Source display
-   Raw result mode
-   Configurable top-k retrieval

## Tech Stack

  Component         Technology
  ----------------- ------------------------
  Language          Python 3.12
  Package Manager   uv
  Embedding Model   BAAI/bge-small-en-v1.5
  Vector Database   Qdrant
  Source Database   MySQL
  Interface         Terminal CLI

## Prerequisites

-   Python 3.12
-   uv
-   Docker
-   MySQL database
-   Automotive dataset

## Installation

``` bash
git clone https://github.com/dev-abhishek22/revsearch.git
cd revsearch

uv sync
cp .env.example .env
```

## Environment Variables

``` env
DB_HOST=
DB_PORT=
DB_USERNAME=
DB_PASSWORD=
DB_DATABASE=

APP_NAME=RevSearch
SQL_LOGGING=false

HF_HUB_DISABLE_PROGRESS_BARS=1
TOKENIZERS_PARALLELISM=false

QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
QDRANT_COLLECTION_NAME=car_chunks
QDRANT_VECTOR_SIZE=384
QDRANT_DISTANCE=Cosine
```

## Qdrant Setup

``` bash
docker run -d   --name qdrant   -p 6333:6333   -p 6334:6334   qdrant/qdrant
```

## Indexing

``` bash
make index-all-cars
```

Pipeline:

``` text
Fetch Data
     ↓
Clean Payload
     ↓
Validate Data
     ↓
Generate Chunks
     ↓
Generate Embeddings
     ↓
Store in Qdrant
```

## Running the CLI

``` bash
make rag-cli
```

## CLI Commands

``` text
/help
/topk 10
/theme ocean
/raw
/sources
/history
/clear
/exit
```

## Example Queries

``` text
Best Tata SUV under 15 lakh
Safest automatic car under 20 lakh
Compare Hyundai Creta with Kia Seltos
Latest launched cars in India
Cars with good mileage and 6 airbags
```

## Project Status

-   Core semantic search engine: \~80% complete
-   Full production RAG platform: \~60% complete

## Roadmap

-   [ ] Complete full dataset indexing
-   [ ] Improve retrieval evaluation
-   [ ] Add LLM answer generation
-   [ ] Add hybrid search
-   [ ] Add reranking
-   [ ] Add REST API layer
-   [ ] Add Dockerized deployment
-   [ ] Add monitoring and observability

## Dataset Notice

> This repository does not include the private automotive dataset. Users
> must connect their own compatible data source.

## Contributing

Contributions, discussions, and feedback are welcome.

1.  Fork the repository
2.  Create a feature branch
3.  Commit your changes
4.  Open a pull request

## License

Distributed under the MIT License.
