"""
Publisher domain model for managing publishing companies.

A Publisher represents a publishing company (like Big Five Killer LLC) that owns
multiple imprints. Publishers have their own persona (like Thaumette), branding,
and operational settings that cascade to child imprints.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

from .publisher_persona import PublisherPersona


class PublisherType(Enum):
    """Type of publishing entity."""
    INDEPENDENT = "independent"
    AI_ENHANCED = "ai_enhanced"
    TRADITIONAL = "traditional"
    HYBRID = "hybrid"


@dataclass
class Publisher:
    """
    Publisher domain model representing a publishing company.

    A Publisher owns multiple Imprints, has a guiding persona (e.g., Thaumette for B5K),
    and provides shared infrastructure (LSI accounts, branding, quality standards).
    """

    # Core identity
    name: str
    legal_name: str
    publisher_type: PublisherType = PublisherType.AI_ENHANCED

    # Publisher persona (e.g., Thaumette for B5K)
    persona: Optional[PublisherPersona] = None
    persona_name: str = ""
    persona_glyph: str = ""

    # Business information
    founded_year: str = ""
    headquarters: str = ""
    website: str = ""
    contact_email: str = ""
    phone: str = ""
    tax_id: str = ""

    # Child imprints
    imprint_ids: List[str] = field(default_factory=list)
    total_imprints_target: int = 0

    # Distribution
    lightning_source_account: str = ""
    distribution_model: str = "hybrid"

    # Branding defaults (inherited by imprints)
    brand_colors: Dict[str, str] = field(default_factory=dict)
    default_fonts: Dict[str, str] = field(default_factory=dict)
    visual_identity: str = ""

    # Business model
    philosophy: str = ""
    tagline: str = ""
    competitive_positioning: str = ""
    target_market_share: str = ""
    annual_titles_target: int = 0

    # Quality standards (cascade to imprints)
    editorial_standards: List[str] = field(default_factory=list)
    min_resolution_dpi: int = 400
    pdf_version: str = "PDF/X-4"
    quality_tier: str = "premium"

    # Pricing strategy (defaults for imprints)
    default_wholesale_discount: int = 45
    default_markup_percentage: int = 120
    pricing_philosophy: str = ""

    # Territory configurations
    territorial_configs: Dict[str, Dict] = field(default_factory=dict)

    # LSI/Distribution settings
    lsi_account_settings: Dict[str, Any] = field(default_factory=dict)
    ftp_credentials: Dict[str, str] = field(default_factory=dict)

    # AI capabilities
    ai_enhanced: bool = True
    ai_capabilities: Dict[str, bool] = field(default_factory=dict)

    # Legal/compliance
    copyright_notice_template: str = ""
    legal_disclaimer: str = ""
    litigation_status: str = ""

    # Integration
    api_endpoints: Dict[str, str] = field(default_factory=dict)
    webhook_urls: List[str] = field(default_factory=list)

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    config_version: str = "1.0"

    def add_imprint(self, imprint_id: str):
        """Register a child imprint."""
        if imprint_id not in self.imprint_ids:
            self.imprint_ids.append(imprint_id)
            self.updated_at = datetime.now().isoformat()

    def remove_imprint(self, imprint_id: str):
        """Unregister a child imprint."""
        if imprint_id in self.imprint_ids:
            self.imprint_ids.remove(imprint_id)
            self.updated_at = datetime.now().isoformat()

    def get_imprint_count(self) -> int:
        """Get current number of child imprints."""
        return len(self.imprint_ids)

    def get_progress_to_target(self) -> float:
        """Get progress toward imprint target (0.0 to 1.0)."""
        if self.total_imprints_target == 0:
            return 0.0
        return min(1.0, len(self.imprint_ids) / self.total_imprints_target)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "legal_name": self.legal_name,
            "publisher_type": self.publisher_type.value,
            "persona_name": self.persona_name,
            "persona_glyph": self.persona_glyph,
            "founded_year": self.founded_year,
            "headquarters": self.headquarters,
            "website": self.website,
            "contact_email": self.contact_email,
            "phone": self.phone,
            "tax_id": self.tax_id,
            "imprint_ids": self.imprint_ids,
            "total_imprints_target": self.total_imprints_target,
            "imprint_count": len(self.imprint_ids),
            "progress_to_target": self.get_progress_to_target(),
            "lightning_source_account": self.lightning_source_account,
            "distribution_model": self.distribution_model,
            "brand_colors": self.brand_colors,
            "default_fonts": self.default_fonts,
            "visual_identity": self.visual_identity,
            "philosophy": self.philosophy,
            "tagline": self.tagline,
            "competitive_positioning": self.competitive_positioning,
            "target_market_share": self.target_market_share,
            "annual_titles_target": self.annual_titles_target,
            "editorial_standards": self.editorial_standards,
            "min_resolution_dpi": self.min_resolution_dpi,
            "pdf_version": self.pdf_version,
            "quality_tier": self.quality_tier,
            "default_wholesale_discount": self.default_wholesale_discount,
            "default_markup_percentage": self.default_markup_percentage,
            "pricing_philosophy": self.pricing_philosophy,
            "territorial_configs": self.territorial_configs,
            "lsi_account_settings": self.lsi_account_settings,
            "ai_enhanced": self.ai_enhanced,
            "ai_capabilities": self.ai_capabilities,
            "copyright_notice_template": self.copyright_notice_template,
            "legal_disclaimer": self.legal_disclaimer,
            "litigation_status": self.litigation_status,
            "api_endpoints": self.api_endpoints,
            "webhook_urls": self.webhook_urls,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "config_version": self.config_version
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Publisher':
        """Create Publisher instance from dictionary."""
        return cls(
            name=data["name"],
            legal_name=data["legal_name"],
            publisher_type=PublisherType(data.get("publisher_type", "ai_enhanced")),
            persona_name=data.get("persona_name", ""),
            persona_glyph=data.get("persona_glyph", ""),
            founded_year=data.get("founded_year", ""),
            headquarters=data.get("headquarters", ""),
            website=data.get("website", ""),
            contact_email=data.get("contact_email", ""),
            phone=data.get("phone", ""),
            tax_id=data.get("tax_id", ""),
            imprint_ids=data.get("imprint_ids", []),
            total_imprints_target=data.get("total_imprints_target", 0),
            lightning_source_account=data.get("lightning_source_account", ""),
            distribution_model=data.get("distribution_model", "hybrid"),
            brand_colors=data.get("brand_colors", {}),
            default_fonts=data.get("default_fonts", {}),
            visual_identity=data.get("visual_identity", ""),
            philosophy=data.get("philosophy", ""),
            tagline=data.get("tagline", ""),
            competitive_positioning=data.get("competitive_positioning", ""),
            target_market_share=data.get("target_market_share", ""),
            annual_titles_target=data.get("annual_titles_target", 0),
            editorial_standards=data.get("editorial_standards", []),
            min_resolution_dpi=data.get("min_resolution_dpi", 400),
            pdf_version=data.get("pdf_version", "PDF/X-4"),
            quality_tier=data.get("quality_tier", "premium"),
            default_wholesale_discount=data.get("default_wholesale_discount", 45),
            default_markup_percentage=data.get("default_markup_percentage", 120),
            pricing_philosophy=data.get("pricing_philosophy", ""),
            territorial_configs=data.get("territorial_configs", {}),
            lsi_account_settings=data.get("lsi_account_settings", {}),
            ai_enhanced=data.get("ai_enhanced", True),
            ai_capabilities=data.get("ai_capabilities", {}),
            copyright_notice_template=data.get("copyright_notice_template", ""),
            legal_disclaimer=data.get("legal_disclaimer", ""),
            litigation_status=data.get("litigation_status", ""),
            api_endpoints=data.get("api_endpoints", {}),
            webhook_urls=data.get("webhook_urls", []),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            config_version=data.get("config_version", "1.0")
        )

    def __repr__(self) -> str:
        return f"Publisher(name='{self.name}', imprints={len(self.imprint_ids)}/{self.total_imprints_target})"
