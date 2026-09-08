from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.client import ClientCreate, ClientResponse
from app.services.client_service import (
    create_client,
    get_client,
    list_clients,
)


router = APIRouter(prefix="/clients", tags=["Clients"])


@router.post(
    "",
    response_model=ClientResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_client_endpoint(
    data: ClientCreate,
    db: AsyncSession = Depends(get_db),
) -> ClientResponse:
    try:
        return await create_client(db, data)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A client with this name already exists.",
        )


@router.get(
    "",
    response_model=list[ClientResponse],
)
async def list_clients_endpoint(
    db: AsyncSession = Depends(get_db),
) -> list[ClientResponse]:
    return await list_clients(db)


@router.get(
    "/{client_id}",
    response_model=ClientResponse,
)
async def get_client_endpoint(
    client_id: int,
    db: AsyncSession = Depends(get_db),
) -> ClientResponse:
    client = await get_client(db, client_id)

    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found.",
        )

    return client
