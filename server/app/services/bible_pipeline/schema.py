from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class Segment(BaseModel):
    role: Literal["narrator", "character"]
    character_name: Optional[str] = None
    text: str


class Chunk(BaseModel):
    chunk_type: Literal["book_title", "chapter_number", "chapter_name", "section_title", "verse"]
    position: int
    references: Optional[str] = None
    verse_num: Optional[str] = None
    segments: list[Segment]

    @field_validator("verse_num")
    @classmethod
    def verse_has_num(cls, v, info):
        if info.data.get("chunk_type") == "verse" and (v is None or v == ""):
            raise ValueError("verse chunk must have verse_num")
        return v


class PipelineOutput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    reference: Optional[str] = Field(None, alias="_reference", serialization_alias="_reference")
    chunks: list[Chunk]

    @field_validator("chunks")
    @classmethod
    def positions_sequential(cls, chunks: list[Chunk]) -> list[Chunk]:
        for i, c in enumerate(chunks):
            if c.position != i + 1:
                raise ValueError(f"chunk position must be sequential: got {c.position} at index {i}, expected {i + 1}")
        return chunks
