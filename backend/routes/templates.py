"""Article Templates Routes - CRUD operations only"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from datetime import datetime, timezone
from typing import Optional, List
import uuid

from database import get_database
from routes.auth import get_current_user

router = APIRouter(prefix="/templates", tags=["Templates"])


class ArticleTemplateCreate(BaseModel):
    name: str
    description: str
    default_tone: str = "professional"
    default_length: str = "medium"
    prompt_template: str
    keywords_hint: Optional[str] = ""


class ArticleTemplateResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    description: str
    default_tone: str
    default_length: str
    prompt_template: str
    keywords_hint: str
    user_id: str
    created_at: str


# Default templates to create for new users
DEFAULT_TEMPLATES = [
    {
        "name": "Ghid Complet",
        "description": "Articol detaliat tip ghid pas cu pas",
        "default_tone": "professional",
        "default_length": "long",
        "prompt_template": "Scrie un ghid complet și detaliat despre {topic}. Include: introducere, pași clari, exemple practice, sfaturi pro, și o concluzie cu call-to-action.",
        "keywords_hint": "ghid, tutorial, cum să, pași"
    },
    {
        "name": "Listicle (Top X)",
        "description": "Articol în format listă cu puncte",
        "default_tone": "casual",
        "default_length": "medium",
        "prompt_template": "Scrie un articol în format listă despre {topic}. Include minim 7-10 puncte, fiecare cu titlu și descriere detaliată. Adaugă introducere captivantă și concluzie.",
        "keywords_hint": "top, cele mai bune, listă, recomandări"
    },
    {
        "name": "Comparație Produse",
        "description": "Articol comparativ între opțiuni",
        "default_tone": "authoritative",
        "default_length": "long",
        "prompt_template": "Scrie o comparație detaliată despre {topic}. Include: criterii de evaluare, avantaje și dezavantaje pentru fiecare opțiune, tabel comparativ, și recomandare finală.",
        "keywords_hint": "vs, comparație, care e mai bun, diferențe"
    },
    {
        "name": "How-To Rapid",
        "description": "Tutorial scurt și la obiect",
        "default_tone": "friendly",
        "default_length": "short",
        "prompt_template": "Scrie un tutorial scurt și practic despre {topic}. Mergi direct la subiect cu pași simpli și clari. Include sfaturi rapide la final.",
        "keywords_hint": "cum să, rapid, simplu, ușor"
    },
    {
        "name": "Recenzie Expert",
        "description": "Review detaliat cu analiză",
        "default_tone": "authoritative",
        "default_length": "medium",
        "prompt_template": "Scrie o recenzie expertă despre {topic}. Include: prezentare generală, caracteristici cheie, pro și contra, pentru cine e potrivit, verdict final cu scor.",
        "keywords_hint": "recenzie, review, părere, experiență"
    }
]


@router.post("", response_model=ArticleTemplateResponse)
async def create_template(template: ArticleTemplateCreate, user: dict = Depends(get_current_user)):
    """Create a new article template"""
    db = get_database()
    template_id = str(uuid.uuid4())
    template_doc = {
        "id": template_id,
        "name": template.name,
        "description": template.description,
        "default_tone": template.default_tone,
        "default_length": template.default_length,
        "prompt_template": template.prompt_template,
        "keywords_hint": template.keywords_hint or "",
        "user_id": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.article_templates.insert_one(template_doc)
    return ArticleTemplateResponse(**template_doc)


@router.get("", response_model=List[ArticleTemplateResponse])
async def get_templates(user: dict = Depends(get_current_user)):
    """Get all article templates for user"""
    db = get_database()
    templates = await db.article_templates.find({"user_id": user["id"]}, {"_id": 0}).to_list(100)
    
    # Add default templates if user has none
    if not templates:
        default_templates = []
        for t in DEFAULT_TEMPLATES:
            template_doc = {
                "id": str(uuid.uuid4()),
                **t,
                "user_id": user["id"],
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            default_templates.append(template_doc)
        
        await db.article_templates.insert_many(default_templates)
        templates = default_templates
    
    return [ArticleTemplateResponse(**t) for t in templates]


@router.get("/{template_id}", response_model=ArticleTemplateResponse)
async def get_template(template_id: str, user: dict = Depends(get_current_user)):
    """Get a specific template"""
    db = get_database()
    template = await db.article_templates.find_one({"id": template_id, "user_id": user["id"]}, {"_id": 0})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return ArticleTemplateResponse(**template)


@router.delete("/{template_id}")
async def delete_template(template_id: str, user: dict = Depends(get_current_user)):
    """Delete a template"""
    db = get_database()
    result = await db.article_templates.delete_one({"id": template_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"message": "Template deleted"}
