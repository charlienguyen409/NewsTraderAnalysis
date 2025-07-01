from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID


class ArticleBase(BaseModel):
    title: str
    content: Optional[str] = None
    summary: Optional[str] = None
    source: str
    ticker: Optional[str] = None
    published_at: Optional[datetime] = None
    article_metadata: Optional[Dict[str, Any]] = {}


class ArticleCreate(ArticleBase):
    url: str


class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    ticker: Optional[str] = None
    is_processed: Optional[bool] = None
    article_metadata: Optional[Dict[str, Any]] = None


class ArticleResponse(ArticleBase):
    id: UUID
    url: str
    scraped_at: datetime
    is_processed: bool

    class Config:
        from_attributes = True