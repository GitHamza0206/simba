from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
import json
from langchain.schema import Document
from pydantic import Field

class MetadataType(BaseModel):
    filename: str = Field(default='')
    type: str = Field(default='')
    chunk_number: int = Field(default=0)
    page_number: int = Field(default=0)
    enabled: bool = Field(default=False)
    parsing_status: str = Field(default='')
    size: str = Field(default='')
    loader: str = Field(default='')
    parser: Optional[str] = Field(default=None)
    uploadedAt: str = Field(default='')
    file_path: str = Field(default='')

    def dict(self, *args, **kwargs):
        # Override dict method to ensure all fields are JSON serializable
        return {
            "filename": self.filename,
            "type": self.type,
            "page_number": self.page_number,
            "chunk_number": self.chunk_number,
            "enabled": self.enabled,
            "parsing_status": self.parsing_status,
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
    
    def to_document(self):
        return Document(page_content=self.page_content, metadata=self.metadata.dict())

class SimbaDoc(BaseModel):
    id: str
    documents: List[Document]
    metadata: MetadataType
    
    def to_documents(self) -> List[Document]:
        """Convert SimbaDoc to a list of Documents with shared metadata"""
        for doc in self.documents:
            doc.metadata.update(self.metadata.dict())
        return self.documents
    
    @classmethod
    def from_documents(cls, id: str, documents: List[Document], metadata: MetadataType) -> "SimbaDoc":
        """Create SimbaDoc from a list of Documents and metadata"""
        return cls(id=id, documents=documents, metadata=metadata)



