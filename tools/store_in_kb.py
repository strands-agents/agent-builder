"""
Tool for storing data in Bedrock Knowledge Base
"""

import json
import logging
import os
import time
import uuid

import boto3
from strands import tool

# Set up logging
logger = logging.getLogger(__name__)


@tool
def store_in_kb(content: str, title: str = None, knowledge_base_id: str = None) -> dict:
    """
    Store content in a Bedrock Knowledge Base using real-time ingestion.

    Args:
        content: The text content to store in the knowledge base.
        title: Optional title for the content. If not provided, a timestamp will be used.
        knowledge_base_id: Optional knowledge base ID. If not provided, will use the KNOWLEDGE_BASE_ID env variable.

    Returns:
        A dictionary containing the result of the operation.
    """
    # Get knowledge base ID from parameter or environment variable
    kb_id = knowledge_base_id or os.getenv("KNOWLEDGE_BASE_ID")

    # Validate required inputs
    if not kb_id:
        return {
            "status": "error",
            "content": [
                {"text": "❌ No knowledge base ID provided or found in environment variables KNOWLEDGE_BASE_ID"}
            ],
        }

    if not content or not content.strip():
        return {"status": "error", "content": [{"text": "❌ Content cannot be empty"}]}

    try:
        # Generate document ID with timestamp for traceability
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        doc_id = f"memory_{timestamp}_{str(uuid.uuid4())[:8]}"

        # Create a document title if not provided
        doc_title = title or f"Strands Memory {timestamp}"

        region_name = os.getenv("AWS_REGION", "us-west-2")

        # Initialize Bedrock agent client
        bedrock_agent_client = boto3.client("bedrock-agent", region_name=region_name)

        # Get the data source ID associated with the knowledge base
        data_sources = bedrock_agent_client.list_data_sources(knowledgeBaseId=kb_id)

        if not data_sources.get("dataSourceSummaries"):
            return {
                "status": "error",
                "content": [{"text": f"❌ No data sources found for knowledge base {kb_id}, region {region_name}."}],
            }

        data_source_id = data_sources["dataSourceSummaries"][0]["dataSourceId"]

        # Package content with title for better organization
        content_with_metadata = {
            "title": doc_title,
            "action": "store",
            "content": content,
        }

        # Prepare document for ingestion
        ingest_request = {
            "knowledgeBaseId": kb_id,
            "dataSourceId": data_source_id,
            "documents": [
                {
                    "content": {
                        "dataSourceType": "CUSTOM",
                        "custom": {
                            "customDocumentIdentifier": {"id": doc_id},
                            "inlineContent": {
                                "textContent": {"data": json.dumps(content_with_metadata)},
                                "type": "TEXT",
                            },
                            "sourceType": "IN_LINE",
                        },
                    }
                }
            ],
        }

        # Ingest document into knowledge base
        _ = bedrock_agent_client.ingest_knowledge_base_documents(**ingest_request)

        # Log success
        logger.debug(f"Successfully ingested document into knowledge base {kb_id}: {doc_id}")

        # Return in standard Strands format
        return {
            "status": "success",
            "content": [
                {"text": "✅ Successfully stored content in knowledge base:"},
                {"text": f"📝 Title: {doc_title}"},
                {"text": f"🔑 Document ID: {doc_id}"},
                {"text": f"🗄️ Knowledge Base ID: {kb_id}"},
            ],
        }

    except Exception as e:
        logger.error(f"Error ingesting into knowledge base: {str(e)}")
        return {
            "status": "error",
            "content": [{"text": f"❌ Failed to store content in knowledge base: {str(e)}"}],
        }
