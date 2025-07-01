from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ...core.database import get_db
from ...models.article import Article
from ...schemas.article import ArticleResponse, ArticleUpdate
from ...services.crud import article_crud

router = APIRouter()


@router.get("/", response_model=List[ArticleResponse])
@router.get("", response_model=List[ArticleResponse])  # Handle requests without trailing slash
async def get_articles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    source: Optional[str] = Query(None),
    ticker: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    return article_crud.get_articles(
        db=db, skip=skip, limit=limit, source=source, ticker=ticker, search=search
    )


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: UUID, db: Session = Depends(get_db)):
    article = article_crud.get_article(db=db, article_id=article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.patch("/{article_id}", response_model=ArticleResponse)
async def update_article(
    article_id: UUID, 
    article_update: ArticleUpdate, 
    db: Session = Depends(get_db)
):
    article = article_crud.update_article(
        db=db, article_id=article_id, article_update=article_update
    )
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.delete("/{article_id}")
async def delete_article(article_id: UUID, db: Session = Depends(get_db)):
    success = article_crud.delete_article(db=db, article_id=article_id)
    if not success:
        raise HTTPException(status_code=404, detail="Article not found")
    return {"message": "Article deleted successfully"}