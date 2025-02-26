from typing import List, Union

from simba.models.simbadoc import SimbaDoc
from simba.parsing.base import BaseParser


class MarkitdownParser(BaseParser):
    def parse(self, document: SimbaDoc) -> Union[SimbaDoc, List[SimbaDoc]]:
        raise NotImplementedError("Markitdown parser is not implemented yet.")
