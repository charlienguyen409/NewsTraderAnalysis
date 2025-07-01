from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ...core.database import get_db
from ...schemas.position import PositionResponse
from ...services.crud import position_crud

router = APIRouter()


@router.get("/", response_model=List[PositionResponse])
@router.get("", response_model=List[PositionResponse])  # Handle requests without trailing slash
async def get_positions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session_id: Optional[UUID] = Query(None),
    ticker: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    return position_crud.get_positions(
        db=db, skip=skip, limit=limit, session_id=session_id, ticker=ticker
    )


@router.get("/{position_id}", response_model=PositionResponse)
async def get_position(position_id: UUID, db: Session = Depends(get_db)):
    position = position_crud.get_position(db=db, position_id=position_id)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return position


@router.get("/session/{session_id}", response_model=List[PositionResponse])
async def get_positions_by_session(
    session_id: UUID, 
    db: Session = Depends(get_db)
):
    return position_crud.get_positions_by_session(db=db, session_id=session_id)