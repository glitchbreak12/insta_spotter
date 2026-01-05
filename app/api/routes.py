from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Annotated

from app.database import get_db, get_or_create_technical_user, TechnicalUser

router = APIRouter(
    prefix="/api/v1",
    tags=["API"]
)

# --- Pydantic Models ---

class IdentityRequest(BaseModel):
    technical_user_id: str | None = Field(None, description="L'ID tecnico attuale dell'utente, se esistente.")

class IdentityResponse(BaseModel):
    technical_user_id: str = Field(..., description="L'ID tecnico nuovo o confermato dell'utente.")
    created: bool = Field(..., description="Indica se un nuovo ID è stato creato.")

# --- API Endpoint ---

@router.post("/identity", response_model=IdentityResponse)
def manage_identity(
    request_data: Annotated[IdentityRequest, Body(embed=True)],
    db: Session = Depends(get_db)
):
    """
    Gestisce l'identità tecnica anonima di un utente.
    Recupera un utente esistente o ne crea uno nuovo se l'ID non è valido o non fornito.
    """
    user, created = get_or_create_technical_user(db, request_data.technical_user_id)
    
    return IdentityResponse(
        technical_user_id=user.id,
        created=created
    )
