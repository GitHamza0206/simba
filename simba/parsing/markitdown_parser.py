from simba.parsing.base import BaseParser
from simba.models.simbadoc import SimbaDoc
from typing import Union, List


class MarkitdownParser(BaseParser):
    def parse(self, document: SimbaDoc) -> Union[SimbaDoc, List[SimbaDoc]]:
        raise NotImplementedError("Markitdown parser is not implemented yet.")

    