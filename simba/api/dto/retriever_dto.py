from pydantic import BaseModel


class RetrieverConfig(BaseModel):
    strategy: str = "similarity"
    k: int = 5