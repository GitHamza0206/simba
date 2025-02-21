from abc import ABC, abstractmethod
from typing import Union, List
from simba.models.simbadoc import SimbaDoc
from simba.core.config import settings
from simba.core.factories.vector_store_factory import VectorStoreFactory


class BaseParser(ABC):

    def __init__(self):
        self.store = VectorStoreFactory.get_vector_store()


    @abstractmethod
    def parse(self, document: SimbaDoc) -> Union[SimbaDoc, List[SimbaDoc]]:
        """
        Parse the given SimbaDoc and return a modified SimbaDoc or list of SimbaDoc.
        Must be overridden by subclasses.
        """
        pass 