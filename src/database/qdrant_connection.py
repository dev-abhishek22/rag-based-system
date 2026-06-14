from qdrant_client import QdrantClient

from src.config.settings import settings
from src.logger.logger_service import logger_service


def get_qdrant_url() -> str:
    return settings.QDRANT_URL


def create_qdrant_client() -> QdrantClient:
    if settings.QDRANT_API_KEY:
        return QdrantClient(
            url=get_qdrant_url(),
            api_key=settings.QDRANT_API_KEY,
        )

    return QdrantClient(
        url=get_qdrant_url(),
    )


qdrant_client = create_qdrant_client()


def get_qdrant_client() -> QdrantClient:
    return qdrant_client


def qdrant_connection():
    try:
        collections = qdrant_client.get_collections()

        logger_service.log(
            "Qdrant connected successfully",
            "Qdrant",
        )

        return collections

    except Exception as error:
        logger_service.error(
            "Qdrant connection failed",
            str(error),
            "Qdrant",
        )
        raise