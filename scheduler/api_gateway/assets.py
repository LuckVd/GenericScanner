"""Asset API routes."""


from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.models.target import Target
from common.utils.database import get_db
from scheduler.api_gateway.schemas import (
    AssetDetailResponse,
    AssetListResponse,
    AssetTagsUpdate,
)

router = APIRouter(prefix="/api/v1/assets", tags=["assets"])


@router.get("", response_model=AssetListResponse)
async def list_assets(
    tags: str | None = Query(None, description="Filter by tags"),
    service: str | None = Query(None, description="Filter by service"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_db),
) -> AssetListResponse:
    """Get asset list."""
    from sqlalchemy import func

    # Count total
    total_result = await db.execute(select(func.count()).select_from(Target))
    total = total_result.scalar() or 0

    # Query with pagination
    query = select(Target).order_by(Target.created_at.desc())
    query = query.offset((page - 1) * size).limit(size)

    if tags:
        query = query.where(Target.tags.contains(tags))
    if service:
        # Join with services would be needed for proper filtering
        pass

    result = await db.execute(query)
    assets = result.scalars().all()

    return AssetListResponse(
        total=total,
        page=page,
        size=size,
        items=[
            {
                "id": a.id,
                "ip": a.ip,
                "domain": a.domain,
                "ports": a.port_list,
                "tags": a.tag_list,
                "last_scan": a.last_scan.isoformat() if a.last_scan else None,
            }
            for a in assets
        ],
    )


@router.get("/{asset_id}", response_model=AssetDetailResponse)
async def get_asset(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
) -> AssetDetailResponse:
    """Get asset details."""
    result = await db.execute(select(Target).where(Target.id == asset_id))
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    return AssetDetailResponse(
        id=asset.id,
        ip=asset.ip,
        domain=asset.domain,
        ports=asset.port_list,
        services=[s.to_dict() for s in asset.services_rel],
        fingerprints=[f.to_dict() for f in asset.fingerprints_rel],
        tags=asset.tag_list,
        last_scan=asset.last_scan,
    )


@router.post("/{asset_id}/tags")
async def update_asset_tags(
    asset_id: str,
    tags_data: AssetTagsUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update asset tags."""
    result = await db.execute(select(Target).where(Target.id == asset_id))
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    current_tags = set(asset.tag_list)

    if tags_data.add:
        current_tags.update(tags_data.add)
    if tags_data.remove:
        current_tags.difference_update(tags_data.remove)

    asset.tag_list = list(current_tags)
    await db.flush()

    return {
        "id": asset.id,
        "tags": asset.tag_list,
    }
