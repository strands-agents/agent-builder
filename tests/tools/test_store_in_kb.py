#!/usr/bin/env python3
"""
Unit tests for the store_in_kb tool
"""

import json
import os
from unittest import mock

from tools.store_in_kb import store_in_kb


class TestStoreInKbTool:
    """Test cases for the store_in_kb tool"""

    def test_missing_kb_id(self):
        """Test storing without knowledge base ID"""
        with mock.patch.dict(os.environ, {}), mock.patch("boto3.client") as mock_boto:
            # Force boto client to raise an exception when no KB ID is provided
            mock_boto.side_effect = Exception("No knowledge base ID provided")

            result = store_in_kb(content="Test content")

            assert result["status"] == "error"
            assert "No knowledge base ID provided" in result["content"][0]["text"]

    def test_empty_content(self):
        """Test storing empty content"""
        with mock.patch.dict(os.environ, {"KNOWLEDGE_BASE_ID": "test-kb-id"}):
            result = store_in_kb(content="   ")  # Only whitespace

            assert result["status"] == "error"
            assert "Content cannot be empty" in result["content"][0]["text"]

    def test_successful_storage_env_kb(self):
        """Test successful storage using environment variable KB ID"""
        with mock.patch.dict(os.environ, {"KNOWLEDGE_BASE_ID": "env-kb-id"}), mock.patch("boto3.client") as mock_boto:
            # Mock the list_data_sources response
            mock_boto.return_value.list_data_sources.return_value = {
                "dataSourceSummaries": [{"dataSourceId": "test-data-source"}]
            }

            # Call the function
            result = store_in_kb(content="Test content")

            # Verify boto3 client was created correctly
            mock_boto.assert_called_once_with("bedrock-agent", region_name=mock.ANY)

            # Verify list_data_sources was called with correct KB ID
            mock_boto.return_value.list_data_sources.assert_called_once_with(knowledgeBaseId="env-kb-id")

            # Verify ingest_knowledge_base_documents was called with correct parameters
            mock_boto.return_value.ingest_knowledge_base_documents.assert_called_once()
            ingest_args = mock_boto.return_value.ingest_knowledge_base_documents.call_args.kwargs

            assert ingest_args["knowledgeBaseId"] == "env-kb-id"
            assert ingest_args["dataSourceId"] == "test-data-source"
            assert len(ingest_args["documents"]) == 1

            # Check content of document
            doc_content = ingest_args["documents"][0]["content"]["custom"]["inlineContent"]["textContent"]["data"]
            # Parse JSON content
            content_obj = json.loads(doc_content)
            assert content_obj["content"] == "Test content"
            assert "title" in content_obj

            # Verify success response
            assert result["status"] == "success"
            assert "Successfully stored content" in result["content"][0]["text"]

    def test_successful_storage_param_kb(self):
        """Test successful storage using parameter KB ID"""
        with mock.patch("boto3.client") as mock_boto:
            # Mock the list_data_sources response
            mock_boto.return_value.list_data_sources.return_value = {
                "dataSourceSummaries": [{"dataSourceId": "test-data-source"}]
            }

            # Call the function with explicit KB ID
            _ = store_in_kb(content="Test content", title="Test Title", knowledge_base_id="param-kb-id")

            # Verify list_data_sources was called with correct KB ID
            mock_boto.return_value.list_data_sources.assert_called_once_with(knowledgeBaseId="param-kb-id")

            # Verify ingest_knowledge_base_documents was called with correct parameters
            ingest_args = mock_boto.return_value.ingest_knowledge_base_documents.call_args.kwargs
            assert ingest_args["knowledgeBaseId"] == "param-kb-id"

            # Check content of document
            doc_content = ingest_args["documents"][0]["content"]["custom"]["inlineContent"]["textContent"]["data"]
            content_obj = json.loads(doc_content)
            assert content_obj["title"] == "Test Title"  # Custom title used

    def test_no_data_sources(self):
        """Test when no data sources are found"""
        with mock.patch.dict(os.environ, {"KNOWLEDGE_BASE_ID": "test-kb-id"}), mock.patch("boto3.client") as mock_boto:
            # Mock empty data sources response
            mock_boto.return_value.list_data_sources.return_value = {"dataSourceSummaries": []}

            # Call the function
            result = store_in_kb(content="Test content")

            # Verify error response
            assert result["status"] == "error"
            assert "No data sources found" in result["content"][0]["text"]

    def test_boto3_exception(self):
        """Test handling of boto3 exceptions"""
        with mock.patch.dict(os.environ, {"KNOWLEDGE_BASE_ID": "test-kb-id"}), mock.patch("boto3.client") as mock_boto:
            # Make list_data_sources raise an exception
            mock_boto.return_value.list_data_sources.side_effect = Exception("AWS API Error")

            # Call the function
            result = store_in_kb(content="Test content")

            # Verify error response
            assert result["status"] == "error"
            assert "Failed to store content" in result["content"][0]["text"]
            assert "AWS API Error" in result["content"][0]["text"]

    def test_custom_region(self):
        """Test using a custom AWS region"""
        with (
            mock.patch.dict(os.environ, {"KNOWLEDGE_BASE_ID": "test-kb-id", "AWS_REGION": "us-east-1"}),
            mock.patch("boto3.client") as mock_boto,
        ):
            # Mock successful data sources response
            mock_boto.return_value.list_data_sources.return_value = {
                "dataSourceSummaries": [{"dataSourceId": "test-data-source"}]
            }

            # Call the function
            store_in_kb(content="Test content")

            # Verify boto3 client was created with correct region
            mock_boto.assert_called_once_with("bedrock-agent", region_name="us-east-1")


def test_store_in_kb_custom_region():
    """Test store_in_kb with custom AWS region from environment variable"""

    # Mock responses
    mock_list_response = {"dataSourceSummaries": [{"dataSourceId": "test-data-source"}]}
    mock_ingest_response = {"status": "success"}

    # Set up mocks
    mock_client = mock.MagicMock()
    mock_client.list_data_sources.return_value = mock_list_response
    mock_client.ingest_knowledge_base_documents.return_value = mock_ingest_response

    with (
        mock.patch.dict(os.environ, {"AWS_REGION": "ap-southeast-2"}),
        mock.patch("boto3.client", return_value=mock_client) as mock_boto3,
    ):
        result = store_in_kb(content="Test content", title="Test title", knowledge_base_id="test-kb")

        # Verify boto3 client was created with the right region
        mock_boto3.assert_called_once_with("bedrock-agent", region_name="ap-southeast-2")

        # Verify success response
        assert result["status"] == "success"


def test_store_in_kb_exception_path():
    """Test exception handling in store_in_kb"""

    # Mock client to raise exception
    mock_client = mock.MagicMock()
    mock_client.list_data_sources.side_effect = Exception("Test boto3 error")

    with mock.patch("boto3.client", return_value=mock_client):
        result = store_in_kb(content="Test content", title="Test title", knowledge_base_id="test-kb")

        # Verify error response
        assert result["status"] == "error"
        assert "Test boto3 error" in result["content"][0]["text"]


def test_no_data_sources_empty_dict():
    """Test when data sources response is empty dict (no dataSourceSummaries key)"""
    with mock.patch.dict(os.environ, {"KNOWLEDGE_BASE_ID": "test-kb-id"}), mock.patch("boto3.client") as mock_boto:
        # Mock empty response (no dataSourceSummaries key)
        mock_boto.return_value.list_data_sources.return_value = {}

        # Call the function
        result = store_in_kb(content="Test content")

        # Verify error response
        assert result["status"] == "error"
        assert "No data sources found" in result["content"][0]["text"]


def test_data_source_id_selection():
    """Test that the first data source ID is selected when multiple are available"""
    with mock.patch.dict(os.environ, {"KNOWLEDGE_BASE_ID": "test-kb-id"}), mock.patch("boto3.client") as mock_boto:
        # Mock multiple data sources
        mock_boto.return_value.list_data_sources.return_value = {
            "dataSourceSummaries": [{"dataSourceId": "data-source-1"}, {"dataSourceId": "data-source-2"}]
        }

        # Call the function
        result = store_in_kb(content="Test content")

        # Verify the first data source was used
        ingest_args = mock_boto.return_value.ingest_knowledge_base_documents.call_args.kwargs
        assert ingest_args["dataSourceId"] == "data-source-1"
        assert result["status"] == "success"


def test_logging_functionality():
    """Test that logging functionality works properly"""
    with (
        mock.patch.dict(os.environ, {"KNOWLEDGE_BASE_ID": "test-kb-id"}),
        mock.patch("boto3.client") as mock_boto,
        mock.patch("tools.store_in_kb.logger") as mock_logger,
    ):
        # Mock successful data sources response
        mock_boto.return_value.list_data_sources.return_value = {
            "dataSourceSummaries": [{"dataSourceId": "test-data-source"}]
        }

        # Call the function
        store_in_kb(content="Test content")

        # Verify logger was called
        mock_logger.debug.assert_called_once()
        # The log message should contain "Successfully ingested document"
        assert "Successfully ingested document" in mock_logger.debug.call_args.args[0]


def test_exception_logging():
    """Test that exceptions are properly logged"""
    with (
        mock.patch.dict(os.environ, {"KNOWLEDGE_BASE_ID": "test-kb-id"}),
        mock.patch("boto3.client") as mock_boto,
        mock.patch("tools.store_in_kb.logger") as mock_logger,
    ):
        # Make the API call raise an exception
        mock_boto.return_value.list_data_sources.side_effect = Exception("API error")

        # Call the function
        store_in_kb(content="Test content")

        # Verify error was logged
        mock_logger.error.assert_called_once()
        # The log message should contain "Error ingesting"
        assert "Error ingesting" in mock_logger.error.call_args.args[0]


def test_content_metadata_format():
    """Test that the content metadata is properly formatted"""
    with mock.patch.dict(os.environ, {"KNOWLEDGE_BASE_ID": "test-kb-id"}), mock.patch("boto3.client") as mock_boto:
        # Mock successful data sources response
        mock_boto.return_value.list_data_sources.return_value = {
            "dataSourceSummaries": [{"dataSourceId": "test-data-source"}]
        }

        # Call the function with specific title
        custom_title = "My Custom Title"
        store_in_kb(content="Test content", title=custom_title)

        # Get the ingest request document content
        ingest_args = mock_boto.return_value.ingest_knowledge_base_documents.call_args.kwargs
        doc_content_json = ingest_args["documents"][0]["content"]["custom"]["inlineContent"]["textContent"]["data"]
        doc_content = json.loads(doc_content_json)

        # Verify metadata format
        assert doc_content["title"] == custom_title
        assert doc_content["action"] == "store"
        assert doc_content["content"] == "Test content"


def test_auto_generated_title():
    """Test that a title is auto-generated when not provided"""
    with mock.patch.dict(os.environ, {"KNOWLEDGE_BASE_ID": "test-kb-id"}), mock.patch("boto3.client") as mock_boto:
        # Mock successful data sources response
        mock_boto.return_value.list_data_sources.return_value = {
            "dataSourceSummaries": [{"dataSourceId": "test-data-source"}]
        }

        # Call the function without a title
        store_in_kb(content="Test content")

        # Get the ingest request document content
        ingest_args = mock_boto.return_value.ingest_knowledge_base_documents.call_args.kwargs
        doc_content_json = ingest_args["documents"][0]["content"]["custom"]["inlineContent"]["textContent"]["data"]
        doc_content = json.loads(doc_content_json)

        # Verify a title was generated (should start with "Strands Memory")
        assert doc_content["title"].startswith("Strands Memory")
