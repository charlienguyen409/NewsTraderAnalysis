from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_
from typing import List, Optional
from uuid import UUID

from ..models.article import Article
from ..models.position import Position
from ..models.analysis import Analysis
from ..schemas.article import ArticleCreate, ArticleUpdate
from ..schemas.position import PositionCreate
from ..schemas.analysis import AnalysisCreate


class ArticleCRUD:
    def get_articles(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        source: Optional[str] = None,
        ticker: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Article]:
        query = db.query(Article).options(joinedload(Article.analyses))
        
        if source:
            query = query.filter(Article.source == source)
        if ticker:
            query = query.filter(Article.ticker == ticker)
        if search:
            query = query.filter(
                or_(
                    Article.title.ilike(f"%{search}%"),
                    Article.content.ilike(f"%{search}%")
                )
            )
        
        return query.order_by(Article.scraped_at.desc()).offset(skip).limit(limit).all()

    def get_article(self, db: Session, article_id: UUID) -> Optional[Article]:
        return db.query(Article).options(joinedload(Article.analyses)).filter(Article.id == article_id).first()

    def create_article(self, db: Session, article: ArticleCreate) -> Article:
        db_article = Article(**article.dict())
        db.add(db_article)
        db.commit()
        db.refresh(db_article)
        return db_article

    def update_article(
        self, db: Session, article_id: UUID, article_update: ArticleUpdate
    ) -> Optional[Article]:
        db_article = db.query(Article).filter(Article.id == article_id).first()
        if not db_article:
            return None
        
        update_data = article_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_article, field, value)
        
        db.commit()
        db.refresh(db_article)
        return db_article

    def delete_article(self, db: Session, article_id: UUID) -> bool:
        db_article = db.query(Article).filter(Article.id == article_id).first()
        if not db_article:
            return False
        
        db.delete(db_article)
        db.commit()
        return True


class PositionCRUD:
    def get_positions(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        session_id: Optional[UUID] = None,
        ticker: Optional[str] = None
    ) -> List[Position]:
        query = db.query(Position)
        
        if session_id:
            query = query.filter(Position.analysis_session_id == session_id)
        if ticker:
            query = query.filter(Position.ticker == ticker)
        
        return query.order_by(Position.created_at.desc()).offset(skip).limit(limit).all()

    def get_position(self, db: Session, position_id: UUID) -> Optional[Position]:
        return db.query(Position).filter(Position.id == position_id).first()

    def get_positions_by_session(self, db: Session, session_id: UUID) -> List[Position]:
        return db.query(Position).filter(
            Position.analysis_session_id == session_id
        ).order_by(Position.confidence.desc()).all()

    def create_position(self, db: Session, position: PositionCreate) -> Position:
        db_position = Position(**position.dict())
        db.add(db_position)
        db.commit()
        db.refresh(db_position)
        return db_position


class AnalysisCRUD:
    def create_analysis(self, db: Session, analysis: AnalysisCreate) -> Analysis:
        db_analysis = Analysis(**analysis.dict())
        db.add(db_analysis)
        db.commit()
        db.refresh(db_analysis)
        return db_analysis

    def get_analysis_by_article(self, db: Session, article_id: UUID) -> List[Analysis]:
        return db.query(Analysis).filter(Analysis.article_id == article_id).all()


article_crud = ArticleCRUD()
position_crud = PositionCRUD()
analysis_crud = AnalysisCRUD()