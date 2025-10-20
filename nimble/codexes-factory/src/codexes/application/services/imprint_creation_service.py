"""
Application service for imprint creation and management.

This service coordinates between the domain models and repositories,
providing high-level operations for imprint management.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path

from ...domain.models.imprint import (
    Imprint,
    BrandingSpecification,
    PublishingFocus,
    ImprintStatus,
)
from ...domain.models.publisher_persona import PublisherPersona
from ...infrastructure.repositories.imprint_repository import ImprintRepository


class ImprintCreationService:
    """
    Service for creating and managing imprints.

    Coordinates between domain models and persistence layer, providing
    business logic for imprint creation workflows.
    """

    def __init__(self, repository: ImprintRepository, ai_generator: Optional[Any] = None):
        """
        Initialize the imprint creation service.

        Args:
            repository: Repository for imprint persistence
            ai_generator: Optional AI generator for automated creation
        """
        self.repository = repository
        self.ai_generator = ai_generator

    def create_from_wizard(
        self,
        name: str,
        publisher: str,
        charter: str,
        branding: BrandingSpecification,
        publishing_focus: PublishingFocus,
        persona: Optional[PublisherPersona] = None,
        auto_activate: bool = False,
    ) -> Imprint:
        """
        Create an imprint from wizard-collected information.

        Args:
            name: Imprint name
            publisher: Parent publisher name
            charter: Mission statement
            branding: Branding specification
            publishing_focus: Editorial focus
            persona: Optional publisher persona
            auto_activate: Whether to automatically activate if valid

        Returns:
            Imprint: The created imprint

        Raises:
            ValueError: If imprint with same name already exists
            IOError: If save operation fails
        """
        # Create the imprint
        imprint = Imprint(
            name=name,
            publisher=publisher,
            charter=charter,
            branding=branding,
            publishing_focus=publishing_focus,
            persona=persona,
        )

        # Check if slug already exists and auto-deduplicate
        original_slug = imprint.slug
        counter = 1
        while self.repository.exists(imprint.slug):
            imprint.slug = f"{original_slug}_{counter}"
            counter += 1
            if counter > 100:  # Safety limit
                raise ValueError(
                    f"Cannot create unique slug for imprint '{name}'. "
                    "Too many variants already exist."
                )

        # Auto-activate if requested and valid
        if auto_activate and imprint.is_valid():
            imprint.activate()

        # Save to repository
        self.repository.save(imprint)

        return imprint

    def create_from_ai(
        self,
        description: str,
        model: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0.7,
        partial_config: Optional[Dict[str, Any]] = None,
    ) -> Imprint:
        """
        Create an imprint using AI generation.

        Args:
            description: Natural language description of desired imprint
            model: LLM model to use for generation
            temperature: Temperature for generation (0.0-1.0)
            partial_config: Optional partial configuration to merge with AI output

        Returns:
            Imprint: The created imprint

        Raises:
            ValueError: If AI generator not configured or generation fails
            IOError: If save operation fails
        """
        if not self.ai_generator:
            raise ValueError(
                "AI generator not configured. Please provide an AI generator "
                "to use AI-based imprint creation."
            )

        # Generate imprint configuration using AI
        # This is a placeholder - actual implementation would call LLM
        generated_config = self._generate_imprint_config(
            description=description,
            model=model,
            temperature=temperature,
        )

        # Merge with partial config if provided
        if partial_config:
            generated_config.update(partial_config)

        # Extract imprint name - could be 'imprint', 'name', or in branding
        imprint_name = (
            generated_config.get('imprint') or
            generated_config.get('name') or
            generated_config.get('branding', {}).get('display_name', 'Generated Imprint')
        )

        # Extract branding info
        branding_data = generated_config.get('branding', {})
        brand_colors = branding_data.get('brand_colors', {})

        branding = BrandingSpecification(
            display_name=branding_data.get('display_name', imprint_name),
            tagline=branding_data.get('tagline'),
            mission_statement=generated_config.get('mission_statement') or generated_config.get('charter', ''),
            brand_values=generated_config.get('brand_values', []),
            primary_color=brand_colors.get('primary'),
            secondary_color=brand_colors.get('secondary'),
            font_family=generated_config.get('fonts', {}).get('body'),
        )

        # Extract publishing focus
        pub_focus_data = generated_config.get('publishing_focus', {})
        publishing_focus = PublishingFocus(
            primary_genres=pub_focus_data.get('primary_genres', []),
            target_audience=pub_focus_data.get('target_audience'),
            price_point=generated_config.get('pricing_defaults', {}).get('price_point'),
            books_per_year=generated_config.get('books_per_year'),
        )

        # Extract publisher persona if present
        persona = None
        persona_data = generated_config.get('publisher_persona') or generated_config.get('persona')
        if persona_data:
            try:
                # Map the persona data to our domain model
                from ...domain.models.publisher_persona import RiskTolerance, DecisionStyle

                # Parse risk tolerance
                risk_str = persona_data.get('risk_tolerance', 'moderate').lower()
                risk_tolerance = {
                    'low': RiskTolerance.CONSERVATIVE,
                    'conservative': RiskTolerance.CONSERVATIVE,
                    'medium': RiskTolerance.MODERATE,
                    'moderate': RiskTolerance.MODERATE,
                    'high': RiskTolerance.AGGRESSIVE,
                    'aggressive': RiskTolerance.AGGRESSIVE,
                }.get(risk_str, RiskTolerance.MODERATE)

                # Parse decision style
                decision_str = persona_data.get('decision_style', 'collaborative').lower()
                decision_style = {
                    'data': DecisionStyle.DATA_DRIVEN,
                    'data-driven': DecisionStyle.DATA_DRIVEN,
                    'data driven': DecisionStyle.DATA_DRIVEN,
                    'intuitive': DecisionStyle.INTUITIVE,
                    'collaborative': DecisionStyle.COLLABORATIVE,
                    'authoritative': DecisionStyle.AUTHORITATIVE,
                    'analytical': DecisionStyle.DATA_DRIVEN,  # Map analytical to data-driven
                    'traditional': DecisionStyle.AUTHORITATIVE,  # Map traditional to authoritative
                    'balanced': DecisionStyle.COLLABORATIVE,  # Map balanced to collaborative
                }.get(decision_str, DecisionStyle.COLLABORATIVE)

                persona = PublisherPersona(
                    name=persona_data.get('persona_name', 'Editorial AI'),
                    bio=persona_data.get('persona_bio', ''),
                    risk_tolerance=risk_tolerance,
                    decision_style=decision_style,
                    preferred_topics=persona_data.get('preferred_topics', '').split(', ') if persona_data.get('preferred_topics') else [],
                    target_demographics=persona_data.get('target_demographics', '').split(', ') if persona_data.get('target_demographics') else [],
                    vulnerabilities=persona_data.get('vulnerabilities', '').split(', ') if persona_data.get('vulnerabilities') else [],
                )
            except Exception as e:
                # Log the error but don't fail the entire imprint creation
                import logging
                logging.getLogger(__name__).warning(f"Failed to create publisher persona: {e}")

        # Create imprint using wizard method
        return self.create_from_wizard(
            name=imprint_name,
            publisher=generated_config.get('publisher', 'Nimble Books LLC'),
            charter=generated_config.get('charter') or generated_config.get('mission_statement', 'AI Generated Charter'),
            branding=branding,
            publishing_focus=publishing_focus,
            persona=persona,
            auto_activate=False,
        )

    def get_by_slug(self, slug: str) -> Optional[Imprint]:
        """
        Retrieve an imprint by its slug.

        Args:
            slug: Imprint slug

        Returns:
            Imprint or None if not found
        """
        return self.repository.get_by_slug(slug)

    def get_all(self) -> List[Imprint]:
        """
        Retrieve all imprints.

        Returns:
            List of all imprints
        """
        return self.repository.get_all()

    def get_all_active(self) -> List[Imprint]:
        """
        Retrieve all active imprints.

        Returns:
            List of active imprints
        """
        return self.repository.get_active()

    def update(self, imprint: Imprint) -> None:
        """
        Update an existing imprint.

        Args:
            imprint: Imprint to update

        Raises:
            ValueError: If imprint doesn't exist
            IOError: If save operation fails
        """
        if not self.repository.exists(imprint.slug):
            raise ValueError(f"Imprint '{imprint.slug}' does not exist")

        self.repository.save(imprint)

    def activate(self, slug: str) -> Imprint:
        """
        Activate an imprint.

        Args:
            slug: Slug of imprint to activate

        Returns:
            Activated imprint

        Raises:
            ValueError: If imprint not found or invalid
            IOError: If save operation fails
        """
        imprint = self.repository.get_by_slug(slug)
        if not imprint:
            raise ValueError(f"Imprint '{slug}' not found")

        imprint.activate()
        self.repository.save(imprint)

        return imprint

    def delete(self, slug: str) -> bool:
        """
        Delete an imprint.

        Args:
            slug: Slug of imprint to delete

        Returns:
            bool: True if deleted, False if not found

        Raises:
            IOError: If delete operation fails
        """
        return self.repository.delete(slug)

    def _generate_imprint_config(
        self,
        description: str,
        model: str,
        temperature: float,
    ) -> Dict[str, Any]:
        """
        Generate imprint configuration using AI.

        Args:
            description: Natural language description
            model: Model to use
            temperature: Generation temperature

        Returns:
            Dict containing imprint configuration
        """
        # Import the one-shot generator
        try:
            from ...modules.imprints.generate_oneshot_imprint import (
                load_template_and_exemplar,
                create_oneshot_prompt,
                generate_imprint_config as gen_config
            )
        except ImportError:
            from src.codexes.modules.imprints.generate_oneshot_imprint import (
                load_template_and_exemplar,
                create_oneshot_prompt,
                generate_imprint_config as gen_config
            )

        # Load template and exemplar
        template, exemplar = load_template_and_exemplar()

        # Create prompt with correct parameter name
        prompt = create_oneshot_prompt(
            template=template,
            exemplar=exemplar,
            imprint_description=description,
            partial_config=None
        )

        # Generate configuration using AI
        # Note: generate_imprint_config uses call_model_with_prompt internally
        config = gen_config(
            prompt=prompt,
            model=model,
            temperature=temperature
        )

        return config

    def __repr__(self) -> str:
        return f"ImprintCreationService(repository={self.repository})"
