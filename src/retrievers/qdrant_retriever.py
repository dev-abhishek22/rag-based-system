from typing import Any, Dict, List, Optional

from qdrant_client.http.models import (
    FieldCondition,
    Filter,
    MatchAny,
    MatchValue,
    Range,
)

from src.database.qdrant_connection import qdrant_client
from src.embeddings.embedding_service import EmbeddingService, get_embedding_service
from src.schemas.retrieval_schema import (
    RetrievedChunk,
    RetrievalFilter,
    RetrievalResponse,
)


class QdrantRetriever:
    def __init__(
        self,
        collection_name: str = "car_chunks",
        embedding_service: Optional[EmbeddingService] = None,
    ):
        self.collection_name = collection_name
        self.embedding_service = embedding_service or EmbeddingService()
        self.client = qdrant_client

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[RetrievalFilter | Dict[str, Any]] = None,
        format_results: bool = False,
    ):
        query_vector = self.embedding_service.embed_query(query)
        qdrant_filter = self._build_filter(filters)

        search_results = self.vector_search(
            query_vector=query_vector,
            top_k=top_k,
            qdrant_filter=qdrant_filter,
        )

        if not format_results:
            return search_results

        formatted_results = self._format_results(search_results)

        return RetrievalResponse(
            query=query,
            top_k=top_k,
            total_results=len(formatted_results),
            results=formatted_results,
        )

    def vector_search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        qdrant_filter: Optional[Filter] = None,
    ):
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=qdrant_filter,
            limit=top_k,
            with_payload=True,
            with_vectors=False,
        )

        return response.points

    def _build_filter(
        self,
        filters: Optional[RetrievalFilter | Dict[str, Any]],
    ) -> Optional[Filter]:
        if not filters:
            return None

        if isinstance(filters, dict):
            filters = RetrievalFilter(**filters)

        must_conditions = []

        exact_match_fields = [
            "car_id",
            "car_name",
            "brand_id",
            "brand_name",
            "model_id",
            "model_name",
            "submodel_id",
            "submodel_name",
            "trim_id",
            "trim_name",
            "chunk_type",
            "fuel_type",
            "is_popular",
            "is_trending",
            "is_upcoming",
        ]

        for field in exact_match_fields:
            value = getattr(filters, field, None)

            if value is not None:
                must_conditions.append(
                    FieldCondition(
                        key=field,
                        match=MatchValue(value=value),
                    )
                )

        if getattr(filters, "chunk_types", None):
            must_conditions.append(
                FieldCondition(
                    key="chunk_type",
                    match=MatchAny(any=filters.chunk_types),
                )
            )

        if filters.min_price is not None or filters.max_price is not None:
            must_conditions.append(
                FieldCondition(
                    key="min_price",
                    range=Range(
                        gte=filters.min_price,
                        lte=filters.max_price,
                    ),
                )
            )

        if filters.min_mileage is not None or filters.max_mileage is not None:
            must_conditions.append(
                FieldCondition(
                    key="min_mileage",
                    range=Range(
                        gte=filters.min_mileage,
                        lte=filters.max_mileage,
                    ),
                )
            )

        if (
            filters.min_engine_displacement is not None
            or filters.max_engine_displacement is not None
        ):
            must_conditions.append(
                FieldCondition(
                    key="min_engine_displacement",
                    range=Range(
                        gte=filters.min_engine_displacement,
                        lte=filters.max_engine_displacement,
                    ),
                )
            )

        if (
            filters.min_no_of_airbags is not None
            or filters.max_no_of_airbags is not None
        ):
            must_conditions.append(
                FieldCondition(
                    key="min_no_of_airbags",
                    range=Range(
                        gte=filters.min_no_of_airbags,
                        lte=filters.max_no_of_airbags,
                    ),
                )
            )

        if filters.min_rating is not None or filters.max_rating is not None:
            must_conditions.append(
                FieldCondition(
                    key="overall_rating",
                    range=Range(
                        gte=filters.min_rating,
                        lte=filters.max_rating,
                    ),
                )
            )

        if not must_conditions:
            return None

        return Filter(must=must_conditions)

    def _payload_value(self, payload: Dict[str, Any], key: str):
        metadata = payload.get("metadata") or {}

        if payload.get(key) is not None:
            return payload.get(key)

        return metadata.get(key)

    def _format_results(self, search_results) -> List[RetrievedChunk]:
        results: List[RetrievedChunk] = []

        for point in search_results:
            payload = point.payload or {}
            metadata = payload.get("metadata") or {}

            result = RetrievedChunk(
                id=str(point.id),
                score=float(point.score),
                chunk_id=self._payload_value(payload, "chunk_id"),
                chunk_type=self._payload_value(payload, "chunk_type"),
                content=payload.get("content", ""),
                car_id=self._payload_value(payload, "car_id"),
                car_name=self._payload_value(payload, "car_name"),
                url=self._payload_value(payload, "url"),
                brand_id=self._payload_value(payload, "brand_id"),
                brand_name=self._payload_value(payload, "brand_name"),
                brand_slug=self._payload_value(payload, "brand_slug"),
                brand_url=self._payload_value(payload, "brand_url"),
                model_id=self._payload_value(payload, "model_id"),
                model_name=self._payload_value(payload, "model_name"),
                model_slug=self._payload_value(payload, "model_slug"),
                submodel_id=self._payload_value(payload, "submodel_id"),
                submodel_name=self._payload_value(payload, "submodel_name"),
                submodel_slug=self._payload_value(payload, "submodel_slug"),
                min_price=self._payload_value(payload, "min_price"),
                max_price=self._payload_value(payload, "max_price"),
                price=self._payload_value(payload, "price"),
                absolute_price=self._payload_value(payload, "absolute_price"),
                fuel_type=self._payload_value(payload, "fuel_type"),
                min_mileage=self._payload_value(payload, "min_mileage"),
                max_mileage=self._payload_value(payload, "max_mileage"),
                min_engine_displacement=self._payload_value(
                    payload, "min_engine_displacement"
                ),
                max_engine_displacement=self._payload_value(
                    payload, "max_engine_displacement"
                ),
                min_no_of_airbags=self._payload_value(payload, "min_no_of_airbags"),
                max_no_of_airbags=self._payload_value(payload, "max_no_of_airbags"),
                overall_rating=self._payload_value(payload, "overall_rating"),
                is_popular=self._payload_value(payload, "is_popular"),
                is_trending=self._payload_value(payload, "is_trending"),
                is_upcoming=self._payload_value(payload, "is_upcoming"),
                trim_id=self._payload_value(payload, "trim_id"),
                trim_name=self._payload_value(payload, "trim_name"),
                is_base=self._payload_value(payload, "is_base"),
                is_top=self._payload_value(payload, "is_top"),
                is_new=self._payload_value(payload, "is_new"),
                image_page_url=self._payload_value(payload, "image_page_url"),
                news_url=self._payload_value(payload, "news_url"),
                comparison_url=self._payload_value(payload, "comparison_url"),
                compare_car_id=self._payload_value(payload, "compare_car_id"),
                compare_car_name=self._payload_value(payload, "compare_car_name"),
                compare_brand_name=self._payload_value(payload, "compare_brand_name"),
                compare_car_url=self._payload_value(payload, "compare_car_url"),
                faq_index=self._payload_value(payload, "faq_index"),
                question=self._payload_value(payload, "question"),
                metadata=metadata,
                raw_payload=payload,
            )

            results.append(result)

        return results
