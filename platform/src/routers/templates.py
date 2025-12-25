"""
Template management endpoints for the Muppet Platform.

This module provides REST API endpoints for template discovery and information.
"""

from typing import List

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ..logging_config import get_logger
from ..managers.template_manager import TemplateManager

logger = get_logger(__name__)
router = APIRouter()


class TemplateInfo(BaseModel):
    """Template information model."""

    name: str = Field(..., description="Template name")
    version: str = Field(..., description="Template version")
    language: str = Field(..., description="Programming language")
    framework: str = Field(..., description="Framework used")
    description: str = Field(..., description="Template description")
    port: int = Field(..., description="Default port")
    terraform_modules: List[str] = Field(..., description="Required Terraform modules")
    required_variables: List[str] = Field(
        ..., description="Required template variables"
    )
    supported_features: List[str] = Field(..., description="Supported features")


@router.get(
    "/",
    response_model=List[TemplateInfo],
    status_code=status.HTTP_200_OK,
    summary="List available templates",
    description="Get a list of all available muppet templates",
)
async def list_templates() -> List[TemplateInfo]:
    """
    List all available muppet templates.

    Returns:
        List of available templates with their metadata

    Raises:
        HTTPException: If template discovery fails
    """
    try:
        logger.debug("Listing available templates")

        # Initialize template manager
        template_manager = TemplateManager()

        # Discover templates
        templates = template_manager.discover_templates()

        # Convert to response model
        template_list = []
        for template in templates:
            template_info = TemplateInfo(
                name=template.name,
                version=template.version,
                language=template.language,
                framework=template.framework,
                description=template.description,
                port=template.port,
                terraform_modules=template.terraform_modules,
                required_variables=template.required_variables,
                supported_features=template.supported_features,
            )
            template_list.append(template_info)

        logger.info(f"Found {len(template_list)} available templates")
        return template_list

    except Exception as e:
        logger.exception("Failed to list templates")
        raise HTTPException(
            status_code=500, detail=f"Failed to list templates: {str(e)}"
        )


@router.get(
    "/{template_name}",
    response_model=TemplateInfo,
    status_code=status.HTTP_200_OK,
    summary="Get template details",
    description="Get detailed information about a specific template",
)
async def get_template(template_name: str) -> TemplateInfo:
    """
    Get detailed information about a specific template.

    Args:
        template_name: Name of the template to retrieve

    Returns:
        Template information

    Raises:
        HTTPException: If template is not found or retrieval fails
    """
    try:
        logger.debug(f"Getting template details: {template_name}")

        # Initialize template manager
        template_manager = TemplateManager()

        # Get specific template
        template = template_manager.get_template(template_name)

        if not template:
            logger.warning(f"Template not found: {template_name}")
            raise HTTPException(
                status_code=404, detail=f"Template '{template_name}' not found"
            )

        # Convert to response model
        template_info = TemplateInfo(
            name=template.name,
            version=template.version,
            language=template.language,
            framework=template.framework,
            description=template.description,
            port=template.port,
            terraform_modules=template.terraform_modules,
            required_variables=template.required_variables,
            supported_features=template.supported_features,
        )

        logger.info(f"Retrieved template details: {template_name}")
        return template_info

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get template {template_name}")
        raise HTTPException(status_code=500, detail=f"Failed to get template: {str(e)}")
