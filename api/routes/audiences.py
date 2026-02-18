"""受众管理 API"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import DBAudience
from api.schemas import AudienceOut, AudienceUpdate
from src.audiences import AUDIENCES

router = APIRouter(prefix="/audiences", tags=["Audiences"])


@router.get("/", response_model=list[AudienceOut])
def list_audiences(db: Session = Depends(get_db)):
    """列出所有受众（数据库 + 内置）"""
    db_audiences = db.query(DBAudience).all()
    db_ids = {a.id for a in db_audiences}

    result = []
    for a in db_audiences:
        out = AudienceOut.model_validate(a)
        out.keyword_count = len(a.core_keywords or []) + len(a.extended_keywords or [])
        result.append(out)

    for aid, audience in AUDIENCES.items():
        if aid not in db_ids:
            result.append(AudienceOut(
                id=audience.id,
                name=audience.name,
                description=audience.description,
                core_keywords=audience.core_keywords,
                extended_keywords=audience.extended_keywords,
                subreddits=audience.subreddits,
                is_active=True,
                keyword_count=len(audience.all_keywords),
            ))

    return result


@router.get("/{audience_id}", response_model=AudienceOut)
def get_audience(audience_id: str, db: Session = Depends(get_db)):
    db_aud = db.query(DBAudience).filter(DBAudience.id == audience_id).first()
    if db_aud:
        out = AudienceOut.model_validate(db_aud)
        out.keyword_count = len(db_aud.core_keywords or []) + len(db_aud.extended_keywords or [])
        return out

    if audience_id in AUDIENCES:
        a = AUDIENCES[audience_id]
        return AudienceOut(
            id=a.id, name=a.name, description=a.description,
            core_keywords=a.core_keywords, extended_keywords=a.extended_keywords,
            subreddits=a.subreddits, is_active=True,
            keyword_count=len(a.all_keywords),
        )

    raise HTTPException(404, "Audience not found")


@router.put("/{audience_id}", response_model=AudienceOut)
def update_audience(
    audience_id: str,
    payload: AudienceUpdate,
    db: Session = Depends(get_db),
):
    """更新受众（自动从内置复制到数据库后修改）"""
    db_aud = db.query(DBAudience).filter(DBAudience.id == audience_id).first()

    if not db_aud:
        if audience_id not in AUDIENCES:
            raise HTTPException(404, "Audience not found")
        a = AUDIENCES[audience_id]
        db_aud = DBAudience(
            id=a.id, name=a.name, description=a.description,
            core_keywords=a.core_keywords, extended_keywords=a.extended_keywords,
            subreddits=a.subreddits,
        )
        db.add(db_aud)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(db_aud, field, value)

    db.commit()
    db.refresh(db_aud)

    out = AudienceOut.model_validate(db_aud)
    out.keyword_count = len(db_aud.core_keywords or []) + len(db_aud.extended_keywords or [])
    return out
