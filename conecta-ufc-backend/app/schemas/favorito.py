from pydantic import BaseModel, Field
from pydantic_core import ConfigDict

class FavoritoCreate(BaseModel):
    oportunidade_id: int

class FavoritoResponse(BaseModel):
    id: int
    usuario_id: str
    oportunidade_id: int

    model_config = ConfigDict(from_attributes=True)

