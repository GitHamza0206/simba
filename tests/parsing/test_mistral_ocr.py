import os
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from langchain.schema import Document

from simba.models.simbadoc import MetadataType, SimbaDoc
from simba.parsing.mistral_ocr import MistralOCR


class TestMistralOCR:
    """Tests for the MistralOCR parser."""

    @pytest.fixture
    def sample_simbadoc(self):
        """Create a sample SimbaDoc for testing."""
        metadata = MetadataType(
            filename="test_document.pdf",
            type="application/pdf",
            file_path="/path/to/test_document.pdf",
            parsing_status="PENDING",
        )
        return SimbaDoc(id="test-doc-123", documents=[], metadata=metadata)

    @pytest.fixture
    def mock_mistral_response(self):
        """Create a mock response from Mistral OCR API."""
        # This mimics the structure from the provided example
        response = MagicMock()

        # Create two pages
        page1 = MagicMock()
        page1.index = 1
        page1.markdown = "# First page content\n\nThis is the first page of the document."

        page2 = MagicMock()
        page2.index = 2
        page2.markdown = "## Second page content\n\nThis is the second page of the document with a list:\n- Item 1\n- Item 2"

        # Set up the pages attribute
        response.pages = [page1, page2]

        return response

    def test_parse_with_no_api_key(self):
        """Test parsing behavior when no API key is set."""
        with patch.dict(os.environ, {}, clear=True):
            parser = MistralOCR()
            doc = SimbaDoc(
                id="test-doc-123",
                documents=[],
                metadata=MetadataType(file_path="/path/to/test.pdf"),
            )

            # Process should return the original document unchanged
            result = parser.parse(doc)

            assert result == doc
            assert not hasattr(result.metadata, "parsed_at")

    def test_successful_parsing(self, sample_simbadoc, mock_mistral_response):
        """Test successful document parsing with Mistral OCR."""
        with patch.dict(os.environ, {"MISTRAL_API_KEY": "fake-api-key"}):
            parser = MistralOCR()

            # Mock the OCR client and its response
            parser.client = MagicMock()
            parser.client.ocr.process.return_value = mock_mistral_response

            # Process the document
            result = parser.parse(sample_simbadoc)

            # Verify the OCR client was called correctly
            parser.client.ocr.process.assert_called_once_with(
                model="mistral-ocr-latest",
                document={"type": "document_url", "document_url": "/path/to/test_document.pdf"},
                include_image_base64=True,
            )

            # Verify the results
            assert result.id == "test-doc-123"
            assert len(result.documents) == 2

            # Check the first document
            assert (
                result.documents[0].page_content
                == "# First page content\n\nThis is the first page of the document."
            )
            assert result.documents[0].metadata["page_number"] == 1

            # Check the second document
            assert (
                result.documents[1].page_content
                == "## Second page content\n\nThis is the second page of the document with a list:\n- Item 1\n- Item 2"
            )
            assert result.documents[1].metadata["page_number"] == 2

            # Check metadata updates
            assert result.metadata.parser == "mistral_ocr"
            assert result.metadata.parsing_status == "SUCCESS"
            assert hasattr(result.metadata, "parsed_at")

    def test_api_error_handling(self, sample_simbadoc):
        """Test error handling during API calls."""
        with patch.dict(os.environ, {"MISTRAL_API_KEY": "fake-api-key"}):
            parser = MistralOCR()

            # Make the API call raise an exception
            parser.client = MagicMock()
            parser.client.ocr.process.side_effect = Exception("API error")

            # Process should return original document when errors occur
            result = parser.parse(sample_simbadoc)

            assert result == sample_simbadoc
            # Parsing status should not be updated
            assert result.metadata.parsing_status == "PENDING"

    def test_missing_or_empty_pages(self, sample_simbadoc):
        """Test handling of responses with missing or empty pages."""
        with patch.dict(os.environ, {"MISTRAL_API_KEY": "fake-api-key"}):
            parser = MistralOCR()

            # Create a response without pages attribute
            empty_response = MagicMock()
            # Note: intentionally not setting 'pages' attribute

            parser.client = MagicMock()
            parser.client.ocr.process.return_value = empty_response

            # Process the document
            result = parser.parse(sample_simbadoc)

            # Should handle gracefully and return empty documents list
            assert result.id == "test-doc-123"
            assert len(result.documents) == 0
            assert result.metadata.parser == "mistral_ocr"
            assert result.metadata.parsing_status == "SUCCESS"
