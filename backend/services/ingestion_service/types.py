from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import json

class MetadataType(BaseModel):
    filename: str
    type: str
    size: str
    loader: str 
    parser: Optional[str] = None
    uploadedAt: str
    file_path: str

    def dict(self, *args, **kwargs):
        # Override dict method to ensure all fields are JSON serializable
        return {
            "filename": self.filename,
            "type": self.type,
            "size": self.size,
            "loader": self.loader,
            "parser": self.parser or 'no parser',
            "uploadedAt": self.uploadedAt,
            "file_path": self.file_path
        }

class IngestedDocument(BaseModel):
    id: str
    page_content: str
    metadata: MetadataType

    def dict(self, *args, **kwargs):
        return {
            "id": self.id,
            "page_content": self.page_content,
            "metadata": self.metadata.dict()
        }

    def json(self, *args, **kwargs):
        """Convert the document to a JSON string"""
        return json.dumps(self.dict())

    @classmethod
    def from_dict(cls, data: dict):
        """Create an IngestedDocument from a dictionary"""
        return cls(
            id=data["id"],
            page_content=data["page_content"],
            metadata=MetadataType(**data["metadata"])
        )


