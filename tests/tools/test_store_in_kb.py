#!/usr/bin/env python3
"""
Unit tests for the store_in_kb tool
"""

import json
import os
from unittest import mock

import pytest

from tools.store_in_kb import _store_in_kb_background, store_in_kb

# Save original env var to restore after tests
original_kb_id = os.environ.get("STRANDS_KNOWLEDGE_BASE_ID")


@pytest.fixture(autouse=True)
def clean_environ():
    """Reset environment variables between tests"""
    saved_environ = os.environ.copy()
    if "STRANDS_KNOWLEDGE_BASE_ID" in os.environ:
        del os.environ["STRANDS_KNOWLEDGE_BASE_ID"]
    yield
    os.environ.clear()
    os.environ.update(saved_environ)


class TestStoreInKbTool:
    """Test cases for the store_in_kb tool"""

    def test_missing_kb_id(self):
        """Test storing without knowledge base ID"""
        # For this test, explicitly ensure there's no KB ID in env
        if "STRANDS_KNOWLEDGE_BASE_ID" in os.environ:
            del os.environ["STRANDS_KNOWLEDGE_BASE_ID"]

        # Call the function with no KB ID parameter
        result = store_in_kb(content="Test content")

        # The implementation should return an error when KB ID is missing
        assert result["status"] == "error"
        assert "No knowledge base ID" in result["content"][0]["text"]

    def test_empty_content(self):
        """Test storing empty content"""
        # Set a test KB ID in the environment
        os.environ["STRANDS_KNOWLEDGE_BASE_ID"] = "test-kb-id"

        # Call with empty content
        result = store_in_kb(content="   ")  # Only whitespace

        # Should get an error
        assert result["status"] == "error"
        assert "Content cannot be empty" in result["content"][0]["text"]

    @mock.patch("threading.Thread")
    def test_successful_storage_env_kb(self, mock_thread):
        """Test successful storage using environment variable KB ID"""
        # Set the env var
        os.environ["STRANDS_KNOWLEDGE_BASE_ID"] = "env-kb-id"

        # Call the function
        result = store_in_kb(content="Test content")

        # Verify the thread was started
        mock_thread.assert_called_once()

        # Verify thread was initialized with daemon=True and the target function
        kwargs = mock_thread.call_args.kwargs
        assert kwargs.get("daemon") is True
        assert callable(kwargs.get("target"))

        # Verify the response
        assert result["status"] == "success"
        assert "Started background task" in result["content"][0]["text"]
        assert "Knowledge Base ID: env-kb-id" in result["content"][2]["text"]

    @mock.patch("threading.Thread")
    def test_successful_storage_param_kb(self, mock_thread):
        """Test successful storage using parameter KB ID"""
        # Call the function with explicit KB ID
        result = store_in_kb(content="Test content", title="Test Title", knowledge_base_id="param-kb-id")

        # Verify thread was started with the right parameters
        mock_thread.assert_called_once()

        # Check that the response shows the KB ID and title
        assert result["status"] == "success"
        assert "Title: Test Title" in result["content"][1]["text"]
        assert "Knowledge Base ID: param-kb-id" in result["content"][2]["text"]

    @mock.patch("threading.Thread")
    def test_custom_region(self, mock_thread):
        """Test using a custom AWS region"""
        # Setup environment variables
        os.environ["STRANDS_KNOWLEDGE_BASE_ID"] = "test-kb-id"
        os.environ["AWS_REGION"] = "us-east-1"

        # Call the function
        result = store_in_kb(content="Test content")

        # Verify thread was started
        mock_thread.assert_called_once()

        # We can't directly test the region here, but can verify success response
        assert result["status"] == "success"

    # NEW TESTS FOR BACKGROUND FUNCTION
    @mock.patch("boto3.client")
    @mock.patch("tools.store_in_kb.logger")
    def test_background_function_direct(self, mock_logger, mock_boto):
        """Test direct execution of the background function with all successful paths"""
        # Setup mock boto3 client and responses
        mock_bedrock = mock.MagicMock()
        mock_boto.return_value = mock_bedrock

        # Setup data source response
        mock_bedrock.list_data_sources.return_value = {"dataSourceSummaries": [{"dataSourceId": "test-ds-id"}]}
        mock_bedrock.get_data_source.return_value = {"dataSource": {"dataSourceConfiguration": {"type": "CUSTOM"}}}
        mock_bedrock.ingest_knowledge_base_documents.return_value = {"jobId": "test-job"}

        # Call background function directly
        _store_in_kb_background("Test content", "Test Title", "test-kb-id")

        # Verify correct API calls were made
        mock_bedrock.list_data_sources.assert_called_once_with(knowledgeBaseId="test-kb-id")
        mock_bedrock.get_data_source.assert_called_once()
        mock_bedrock.ingest_knowledge_base_documents.assert_called_once()

        # Verify success was logged
        mock_logger.info.assert_called_once()
        assert "Successfully ingested" in mock_logger.info.call_args[0][0]
        assert "test-kb-id" in mock_logger.info.call_args[0][0]

    @mock.patch("boto3.client")
    @mock.patch("tools.store_in_kb.logger")
    def test_background_no_kb_id(self, mock_logger, mock_boto):
        """Test background function with missing KB ID"""
        # Call function with no KB ID
        _store_in_kb_background("Test content", "Test Title", None)

        # Should not call boto3
        mock_boto.assert_not_called()

        # Should log warning
        mock_logger.debug.assert_called()
        debug_message = mock_logger.debug.call_args[0][0]
        assert "No knowledge base ID" in debug_message

    @mock.patch("boto3.client")
    @mock.patch("tools.store_in_kb.logger")
    def test_background_empty_content(self, mock_logger, mock_boto):
        """Test background function with empty content"""
        # Call function with empty content
        _store_in_kb_background("", "Test Title", "test-kb-id")

        # Should not call boto3
        mock_boto.assert_not_called()

        # Should log warning
        mock_logger.debug.assert_called()
        debug_message = mock_logger.debug.call_args[0][0]
        assert "Content cannot be empty" in debug_message

    @mock.patch("boto3.client")
    @mock.patch("tools.store_in_kb.logger")
    def test_background_custom_data_source_selection(self, mock_logger, mock_boto):
        """Test background function with multiple data sources and CUSTOM selection"""
        # Setup mock boto3 client and responses
        mock_bedrock = mock.MagicMock()
        mock_boto.return_value = mock_bedrock

        # Setup multiple data sources with different types
        mock_bedrock.list_data_sources.return_value = {
            "dataSourceSummaries": [{"dataSourceId": "s3-source-id"}, {"dataSourceId": "custom-source-id"}]
        }

        # Mock get_data_source to return different types based on dataSourceId
        def mock_get_data_source(**kwargs):
            if kwargs["dataSourceId"] == "s3-source-id":
                return {"dataSource": {"dataSourceConfiguration": {"type": "S3"}}}
            elif kwargs["dataSourceId"] == "custom-source-id":
                return {"dataSource": {"dataSourceConfiguration": {"type": "CUSTOM"}}}
            return {}

        mock_bedrock.get_data_source.side_effect = mock_get_data_source

        # Call background function
        _store_in_kb_background("Test content", "Test Title", "test-kb-id")

        # Verify CUSTOM type was selected and ingest was called
        mock_bedrock.ingest_knowledge_base_documents.assert_called_once()
        request = mock_bedrock.ingest_knowledge_base_documents.call_args[1]
        assert request["dataSourceId"] == "custom-source-id"

        # Verify success was logged
        mock_logger.info.assert_called_once()

    @mock.patch("boto3.client")
    @mock.patch("tools.store_in_kb.logger")
    def test_background_fallback_to_non_custom_source(self, mock_logger, mock_boto):
        """Test background function falling back to first data source when no CUSTOM source exists"""
        # Setup mock
        mock_bedrock = mock.MagicMock()
        mock_boto.return_value = mock_bedrock

        # Only provide S3 source
        mock_bedrock.list_data_sources.return_value = {"dataSourceSummaries": [{"dataSourceId": "s3-source-id"}]}
        mock_bedrock.get_data_source.return_value = {"dataSource": {"dataSourceConfiguration": {"type": "S3"}}}

        # Call background function
        _store_in_kb_background("Test content", "Test Title", "test-kb-id")

        # For S3 source, should log error and not call ingest
        mock_bedrock.ingest_knowledge_base_documents.assert_not_called()
        mock_logger.error.assert_called()
        error_message = mock_logger.error.call_args[0][0]
        assert "S3 data source type is not supported" in error_message

    @mock.patch("boto3.client")
    @mock.patch("tools.store_in_kb.logger")
    def test_background_unknown_source_type(self, mock_logger, mock_boto):
        """Test background function with unknown data source type"""
        # Setup mock
        mock_bedrock = mock.MagicMock()
        mock_boto.return_value = mock_bedrock

        # Provide unknown source type
        mock_bedrock.list_data_sources.return_value = {"dataSourceSummaries": [{"dataSourceId": "unknown-source-id"}]}
        mock_bedrock.get_data_source.return_value = {"dataSource": {"dataSourceConfiguration": {"type": "UNKNOWN"}}}

        # Call background function
        _store_in_kb_background("Test content", "Test Title", "test-kb-id")

        # Should log error about unsupported type and not call ingest
        mock_bedrock.ingest_knowledge_base_documents.assert_not_called()
        mock_logger.error.assert_called()
        error_message = mock_logger.error.call_args[0][0]
        assert "Unsupported data source type" in error_message

    @mock.patch("boto3.client")
    @mock.patch("tools.store_in_kb.logger")
    def test_background_no_data_sources(self, mock_logger, mock_boto):
        """Test background function without any data sources"""
        # Setup mock
        mock_bedrock = mock.MagicMock()
        mock_boto.return_value = mock_bedrock

        # Return empty data sources
        mock_bedrock.list_data_sources.return_value = {"dataSourceSummaries": []}

        # Call background function
        _store_in_kb_background("Test content", "Test Title", "test-kb-id")

        # Should not call get_data_source or ingest
        mock_bedrock.get_data_source.assert_not_called()
        mock_bedrock.ingest_knowledge_base_documents.assert_not_called()

        # Should log error
        mock_logger.error.assert_called_once()
        error_message = mock_logger.error.call_args[0][0]
        assert "No data sources found" in error_message

    @mock.patch("boto3.client")
    @mock.patch("tools.store_in_kb.logger")
    def test_background_no_datasourcesummaries_key(self, mock_logger, mock_boto):
        """Test background function with missing dataSourceSummaries key"""
        # Setup mock
        mock_bedrock = mock.MagicMock()
        mock_boto.return_value = mock_bedrock

        # Return response without dataSourceSummaries key
        mock_bedrock.list_data_sources.return_value = {}

        # Call background function
        _store_in_kb_background("Test content", "Test Title", "test-kb-id")

        # Should not call get_data_source or ingest
        mock_bedrock.get_data_source.assert_not_called()
        mock_bedrock.ingest_knowledge_base_documents.assert_not_called()

        # Should log error
        mock_logger.error.assert_called_once()
        error_message = mock_logger.error.call_args[0][0]
        assert "No data sources found" in error_message

    @mock.patch("boto3.client")
    @mock.patch("tools.store_in_kb.logger")
    def test_background_boto3_exception(self, mock_logger, mock_boto):
        """Test background function exception handling"""
        # Make boto3.client raise exception
        mock_boto.side_effect = Exception("AWS service error")

        # Call background function
        _store_in_kb_background("Test content", "Test Title", "test-kb-id")

        # Should log error
        mock_logger.error.assert_called_once()
        error_message = mock_logger.error.call_args[0][0]
        assert "Error ingesting into knowledge base" in error_message
        assert "AWS service error" in error_message

    @mock.patch("boto3.client")
    @mock.patch("tools.store_in_kb.logger")
    def test_background_list_data_sources_exception(self, mock_logger, mock_boto):
        """Test background function with exception during list_data_sources call"""
        # Setup mock boto3 client
        mock_bedrock = mock.MagicMock()
        mock_boto.return_value = mock_bedrock

        # Make list_data_sources raise exception
        mock_bedrock.list_data_sources.side_effect = Exception("List data sources failed")

        # Call background function
        _store_in_kb_background("Test content", "Test Title", "test-kb-id")

        # Should log error
        mock_logger.error.assert_called_once()
        error_message = mock_logger.error.call_args[0][0]
        assert "Error ingesting into knowledge base" in error_message
        assert "List data sources failed" in error_message

    @mock.patch("boto3.client")
    @mock.patch("tools.store_in_kb.logger")
    def test_background_auto_title(self, mock_logger, mock_boto):
        """Test background function with auto-generated title"""
        # Setup mocks for successful path
        mock_bedrock = mock.MagicMock()
        mock_boto.return_value = mock_bedrock
        mock_bedrock.list_data_sources.return_value = {"dataSourceSummaries": [{"dataSourceId": "test-ds-id"}]}
        mock_bedrock.get_data_source.return_value = {"dataSource": {"dataSourceConfiguration": {"type": "CUSTOM"}}}

        # Call background function with None title (should auto-generate)
        _store_in_kb_background("Test content", None, "test-kb-id")

        # Verify ingest was called with correct parameters
        mock_bedrock.ingest_knowledge_base_documents.assert_called_once()
        request = mock_bedrock.ingest_knowledge_base_documents.call_args[1]

        # Check the JSON data in the request includes an auto-generated title
        text_content = request["documents"][0]["content"]["custom"]["inlineContent"]["textContent"]["data"]
        data = json.loads(text_content)
        assert "title" in data
        assert "Strands Memory" in data["title"]

    @mock.patch("boto3.client")
    @mock.patch("tools.store_in_kb.logger")
    def test_background_custom_title(self, mock_logger, mock_boto):
        """Test background function with custom title"""
        # Setup mocks for successful path
        mock_bedrock = mock.MagicMock()
        mock_boto.return_value = mock_bedrock
        mock_bedrock.list_data_sources.return_value = {"dataSourceSummaries": [{"dataSourceId": "test-ds-id"}]}
        mock_bedrock.get_data_source.return_value = {"dataSource": {"dataSourceConfiguration": {"type": "CUSTOM"}}}

        # Call background function with custom title
        _store_in_kb_background("Test content", "My Custom Title", "test-kb-id")

        # Verify ingest was called with correct parameters
        mock_bedrock.ingest_knowledge_base_documents.assert_called_once()
        request = mock_bedrock.ingest_knowledge_base_documents.call_args[1]

        # Check the JSON data in the request includes the provided title
        text_content = request["documents"][0]["content"]["custom"]["inlineContent"]["textContent"]["data"]
        data = json.loads(text_content)
        assert data["title"] == "My Custom Title"

    @mock.patch("boto3.client")
    @mock.patch("tools.store_in_kb.logger")
    def test_background_env_region(self, mock_logger, mock_boto):
        """Test background function with region from environment"""
        # Set environment region
        with mock.patch.dict(os.environ, {"AWS_REGION": "us-east-1"}):
            # Setup successful mocks
            mock_bedrock = mock.MagicMock()
            mock_boto.return_value = mock_bedrock
            mock_bedrock.list_data_sources.return_value = {"dataSourceSummaries": [{"dataSourceId": "test-ds-id"}]}
            mock_bedrock.get_data_source.return_value = {"dataSource": {"dataSourceConfiguration": {"type": "CUSTOM"}}}

            # Call background function
            _store_in_kb_background("Test content", "Test Title", "test-kb-id")

            # Verify boto3 client was created with the right region
            mock_boto.assert_called_once_with("bedrock-agent", region_name="us-east-1")

    @mock.patch("boto3.client")
    @mock.patch("tools.store_in_kb.logger")
    def test_background_default_region(self, mock_logger, mock_boto):
        """Test background function with default region when env not set"""
        # Remove environment region if present
        with mock.patch.dict(os.environ, {}, clear=True):
            # Setup successful mocks
            mock_bedrock = mock.MagicMock()
            mock_boto.return_value = mock_bedrock
            mock_bedrock.list_data_sources.return_value = {"dataSourceSummaries": [{"dataSourceId": "test-ds-id"}]}
            mock_bedrock.get_data_source.return_value = {"dataSource": {"dataSourceConfiguration": {"type": "CUSTOM"}}}

            # Call background function
            _store_in_kb_background("Test content", "Test Title", "test-kb-id")

            # Verify boto3 client was created with default region
            mock_boto.assert_called_once_with("bedrock-agent", region_name="us-west-2")


@mock.patch("threading.Thread")
def test_store_in_kb_custom_region(mock_thread):
    """Test store_in_kb with custom AWS region from environment variable"""
    # Set environment variables
    os.environ["STRANDS_KNOWLEDGE_BASE_ID"] = "test-kb"
    os.environ["AWS_REGION"] = "ap-southeast-2"

    # Call function
    result = store_in_kb(content="Test content", title="Test title")

    # Verify thread was started
    mock_thread.assert_called_once()

    # Verify success response
    assert result["status"] == "success"
    # Verify title appears in response
    assert "Title: Test title" in result["content"][1]["text"]


@mock.patch("threading.Thread")
def test_store_in_kb_exception_path(mock_thread):
    """Test exception handling in store_in_kb"""
    # Our implementation starts a thread regardless of potential errors
    result = store_in_kb(content="Test content", title="Test title", knowledge_base_id="test-kb")

    # Verify thread was started
    mock_thread.assert_called_once()

    # Verify success response (main function succeeds even if background will fail)
    assert result["status"] == "success"


@mock.patch("threading.Thread")
def test_data_source_id_selection(mock_thread):
    """Test thread creation with the target function and proper args"""
    os.environ["STRANDS_KNOWLEDGE_BASE_ID"] = "test-kb-id"

    # Call the function
    result = store_in_kb(content="Test content")

    # Verify thread was initialized correctly
    mock_thread.assert_called_once()

    # Verify that args are passed to target function
    assert "args" in mock_thread.call_args.kwargs
    args = mock_thread.call_args.kwargs["args"]
    assert len(args) == 3  # content, title, knowledge_base_id
    assert args[0] == "Test content"  # First arg is content

    # Verify thread was started
    mock_thread.return_value.start.assert_called_once()

    # Verify success response
    assert result["status"] == "success"


@mock.patch("threading.Thread")
def test_auto_generated_title(mock_thread):
    """Test that title param is None when not provided"""
    os.environ["STRANDS_KNOWLEDGE_BASE_ID"] = "test-kb-id"

    # Call the function without a title
    result = store_in_kb(content="Test content")

    # Verify thread creation with None as title
    mock_thread.assert_called_once()
    args = mock_thread.call_args.kwargs["args"]
    assert len(args) >= 2
    assert args[0] == "Test content"  # First arg is content
    assert args[1] is None  # Second arg (title) should be None

    # Title format in response should include "Strands Memory"
    assert "Title: Strands Memory" in result["content"][1]["text"]
