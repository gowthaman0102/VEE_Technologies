from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.company import CompanyCreate, CompanyResponse
from app.schemas.company_context import (
    CompanyContextCreate,
    CompanyContextResponse,
)
from app.services.client_service import get_client
from app.services.company_context_service import (
    create_company_context,
    get_company_context,
)
from app.services.company_service import (
    create_company,
    get_company,
    list_companies,
)


router = APIRouter(prefix="/companies", tags=["Companies"])


@router.post(
    "",
    response_model=CompanyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_company_endpoint(
    data: CompanyCreate,
    db: AsyncSession = Depends(get_db),
) -> CompanyResponse:
    client = await get_client(db, data.client_id)

    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found.",
        )

    try:
        return await create_company(db, data)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Unable to create company because of a data conflict.",
        )


@router.get(
    "",
    response_model=list[CompanyResponse],
)
async def list_companies_endpoint(
    db: AsyncSession = Depends(get_db),
) -> list[CompanyResponse]:
    return await list_companies(db)


@router.get(
    "/{company_id}",
    response_model=CompanyResponse,
)
async def get_company_endpoint(
    company_id: int,
    db: AsyncSession = Depends(get_db),
) -> CompanyResponse:
    company = await get_company(db, company_id)

    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found.",
        )

    return company


@router.post(
    "/{company_id}/context",
    response_model=CompanyContextResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_company_context_endpoint(
    company_id: int,
    data: CompanyContextCreate,
    db: AsyncSession = Depends(get_db),
) -> CompanyContextResponse:
    company = await get_company(db, company_id)

    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found.",
        )

    try:
        return await create_company_context(
            db,
            company_id,
            data,
        )
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="One or more context values already exist.",
        )


@router.get(
    "/{company_id}/context",
    response_model=CompanyContextResponse,
)
async def get_company_context_endpoint(
    company_id: int,
    db: AsyncSession = Depends(get_db),
) -> CompanyContextResponse:
    company = await get_company(db, company_id)

    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found.",
        )

    return await get_company_context(
        db,
        company_id,
    )
