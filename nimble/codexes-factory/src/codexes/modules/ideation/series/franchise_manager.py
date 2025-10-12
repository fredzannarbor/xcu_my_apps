"""
Franchise management for extended book series and universes.
Manages multi-series franchises with shared elements and branding.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional

from ..core.codex_object import CodexObject
from .series_generator import SeriesBlueprint

logger = logging.getLogger(__name__)


class FranchiseStatus(Enum):
    """Status of a franchise."""
    PLANNING = "planning"
    ACTIVE = "active"
    EXPANDING = "expanding"
    MATURE = "mature"
    DECLINING = "declining"
    REBOOTING = "rebooting"


@dataclass
class FranchiseConfiguration:
    """Configuration for franchise management."""
    franchise_name: str = ""
    brand_consistency_level: float = 0.8  # How consistent branding should be
    cross_series_consistency: float = 0.6  # Consistency between different series
    expansion_strategy: str = "organic"  # organic, aggressive, conservative
    target_series_count: int = 3
    shared_universe: bool = True
    brand_elements: List[str] = field(default_factory=list)
    franchise_themes: List[str] = field(default_factory=list)


@dataclass
class FranchiseMetrics:
    """Performance metrics for a franchise."""
    total_books: int = 0
    total_series: int = 0
    average_series_consistency: float = 0.0
    brand_recognition_score: float = 0.0
    expansion_potential: float = 0.0
    market_penetration: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "total_books": self.total_books,
            "total_series": self.total_series,
            "average_series_consistency": self.average_series_consistency,
            "brand_recognition_score": self.brand_recognition_score,
            "expansion_potential": self.expansion_potential,
            "market_penetration": self.market_penetration
        }


@dataclass
class FranchiseBlueprint:
    """Blueprint for a book franchise."""
    franchise_uuid: str = field(default_factory=lambda: str(uuid.uuid4()))
    franchise_name: str = ""
    status: FranchiseStatus = FranchiseStatus.PLANNING
    configuration: FranchiseConfiguration = field(default_factory=FranchiseConfiguration)
    series_blueprints: List[SeriesBlueprint] = field(default_factory=list)
    shared_elements: Dict[str, Any] = field(default_factory=dict)
    brand_guidelines: Dict[str, str] = field(default_factory=dict)
    created_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "franchise_uuid": self.franchise_uuid,
            "franchise_name": self.franchise_name,
            "status": self.status.value,
            "configuration": {
                "franchise_name": self.configuration.franchise_name,
                "brand_consistency_level": self.configuration.brand_consistency_level,
                "cross_series_consistency": self.configuration.cross_series_consistency,
                "expansion_strategy": self.configuration.expansion_strategy,
                "target_series_count": self.configuration.target_series_count,
                "shared_universe": self.configuration.shared_universe,
                "brand_elements": self.configuration.brand_elements,
                "franchise_themes": self.configuration.franchise_themes
            },
            "series_count": len(self.series_blueprints),
            "shared_elements": self.shared_elements,
            "brand_guidelines": self.brand_guidelines,
            "created_timestamp": self.created_timestamp,
            "last_updated": self.last_updated
        }


class FranchiseManager:
    """
    Manages book franchises with multiple series and shared universes.
    Implements franchise-level consistency and branding management.
    """
    
    def __init__(self):
        """Initialize franchise manager."""
        self.franchises: Dict[str, FranchiseBlueprint] = {}
        self.franchise_metrics: Dict[str, FranchiseMetrics] = {}
        logger.info("FranchiseManager initialized")
    
    def create_franchise(self, base_series: SeriesBlueprint, 
                        config: FranchiseConfiguration) -> FranchiseBlueprint:
        """
        Create a new franchise from a base series.
        
        Args:
            base_series: The founding series for the franchise
            config: Franchise configuration
            
        Returns:
            FranchiseBlueprint for the new franchise
        """
        try:
            # Create franchise blueprint
            franchise = FranchiseBlueprint(
                franchise_name=config.franchise_name or f"{base_series.series_name} Universe",
                status=FranchiseStatus.PLANNING,
                configuration=config,
                series_blueprints=[base_series]
            )
            
            # Extract shared elements from base series
            franchise.shared_elements = self._extract_shared_elements(base_series, config)
            
            # Create brand guidelines
            franchise.brand_guidelines = self._create_brand_guidelines(base_series, config)
            
            # Store franchise
            self.franchises[franchise.franchise_uuid] = franchise
            self.franchise_metrics[franchise.franchise_uuid] = FranchiseMetrics(
                total_books=base_series.books_generated,
                total_series=1
            )
            
            logger.info(f"Created franchise: {franchise.franchise_name}")
            return franchise
            
        except Exception as e:
            logger.error(f"Error creating franchise: {e}")
            raise
    
    def add_series_to_franchise(self, franchise_uuid: str, 
                               new_series: SeriesBlueprint) -> bool:
        """
        Add a new series to an existing franchise.
        
        Args:
            franchise_uuid: UUID of the franchise
            new_series: Series to add to the franchise
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if franchise_uuid not in self.franchises:
                logger.error(f"Franchise not found: {franchise_uuid}")
                return False
            
            franchise = self.franchises[franchise_uuid]
            
            # Validate series compatibility with franchise
            compatibility_score = self._calculate_series_compatibility(franchise, new_series)
            
            if compatibility_score < franchise.configuration.cross_series_consistency:
                logger.warning(f"Series compatibility too low: {compatibility_score:.2f}")
                return False
            
            # Add series to franchise
            franchise.series_blueprints.append(new_series)
            franchise.last_updated = datetime.now().isoformat()
            
            # Update franchise status
            if len(franchise.series_blueprints) >= 2 and franchise.status == FranchiseStatus.PLANNING:
                franchise.status = FranchiseStatus.ACTIVE
            elif len(franchise.series_blueprints) >= franchise.configuration.target_series_count:
                franchise.status = FranchiseStatus.EXPANDING
            
            # Update metrics
            metrics = self.franchise_metrics[franchise_uuid]
            metrics.total_series = len(franchise.series_blueprints)
            metrics.total_books += new_series.books_generated
            
            logger.info(f"Added series {new_series.series_name} to franchise {franchise.franchise_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding series to franchise: {e}")
            return False
    
    def _extract_shared_elements(self, base_series: SeriesBlueprint, 
                                config: FranchiseConfiguration) -> Dict[str, Any]:
        """Extract elements that should be shared across the franchise."""
        shared_elements = {}
        
        # Extract high-consistency elements from base series
        for element in base_series.consistent_elements:
            if element.consistency_level >= config.brand_consistency_level:
                shared_elements[element.element_name] = {
                    "type": element.element_type,
                    "description": element.description,
                    "consistency_level": element.consistency_level,
                    "franchise_wide": True
                }
        
        # Add franchise-specific elements
        for brand_element in config.brand_elements:
            shared_elements[f"brand_{brand_element}"] = {
                "type": "brand",
                "description": f"Franchise brand element: {brand_element}",
                "consistency_level": config.brand_consistency_level,
                "franchise_wide": True
            }
        
        return shared_elements
    
    def _create_brand_guidelines(self, base_series: SeriesBlueprint, 
                               config: FranchiseConfiguration) -> Dict[str, str]:
        """Create brand guidelines for the franchise."""
        guidelines = {
            "franchise_name": config.franchise_name,
            "primary_genre": base_series.series_type.value,
            "brand_tone": "Consistent with founding series",
            "target_audience": "Aligned with franchise themes",
            "expansion_strategy": config.expansion_strategy
        }
        
        # Add theme-based guidelines
        for theme in config.franchise_themes:
            guidelines[f"theme_{theme}"] = f"All series should incorporate {theme} elements"
        
        return guidelines
    
    def _calculate_series_compatibility(self, franchise: FranchiseBlueprint, 
                                      new_series: SeriesBlueprint) -> float:
        """Calculate how compatible a series is with the franchise."""
        compatibility_scores = []
        
        # Check shared elements compatibility
        for element_name, shared_element in franchise.shared_elements.items():
            # Find matching elements in new series
            matching_elements = [e for e in new_series.consistent_elements 
                               if e.element_name == element_name or e.element_type == shared_element["type"]]
            
            if matching_elements:
                # Calculate similarity
                element_compatibility = min(1.0, len(matching_elements) * 0.5)
                compatibility_scores.append(element_compatibility)
            else:
                compatibility_scores.append(0.0)
        
        # Overall compatibility
        if compatibility_scores:
            return sum(compatibility_scores) / len(compatibility_scores)
        else:
            return 0.5  # Neutral compatibility if no shared elements
    
    def get_franchise_metrics(self, franchise_uuid: str) -> FranchiseMetrics:
        """Get performance metrics for a franchise."""
        try:
            if franchise_uuid not in self.franchise_metrics:
                return FranchiseMetrics()
            
            metrics = self.franchise_metrics[franchise_uuid]
            franchise = self.franchises.get(franchise_uuid)
            
            if franchise:
                # Update calculated metrics
                if franchise.series_blueprints:
                    consistency_scores = []
                    for series in franchise.series_blueprints:
                        # Calculate average consistency for each series
                        if series.consistent_elements:
                            avg_consistency = sum(e.consistency_level for e in series.consistent_elements) / len(series.consistent_elements)
                            consistency_scores.append(avg_consistency)
                    
                    if consistency_scores:
                        metrics.average_series_consistency = sum(consistency_scores) / len(consistency_scores)
                
                # Calculate expansion potential based on series count vs target
                if franchise.configuration.target_series_count > 0:
                    current_ratio = len(franchise.series_blueprints) / franchise.configuration.target_series_count
                    metrics.expansion_potential = max(0.0, 1.0 - current_ratio)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting franchise metrics: {e}")
            return FranchiseMetrics()
    
    def plan_franchise_expansion(self, franchise_uuid: str) -> Dict[str, Any]:
        """Plan expansion strategy for a franchise."""
        try:
            if franchise_uuid not in self.franchises:
                return {"error": "Franchise not found"}
            
            franchise = self.franchises[franchise_uuid]
            metrics = self.get_franchise_metrics(franchise_uuid)
            
            expansion_plan = {
                "franchise_uuid": franchise_uuid,
                "current_status": franchise.status.value,
                "current_series_count": len(franchise.series_blueprints),
                "target_series_count": franchise.configuration.target_series_count,
                "expansion_recommendations": [],
                "timeline_estimate": "6-12 months per series",
                "risk_assessment": "medium"
            }
            
            # Generate recommendations based on current state
            if len(franchise.series_blueprints) < franchise.configuration.target_series_count:
                remaining = franchise.configuration.target_series_count - len(franchise.series_blueprints)
                expansion_plan["expansion_recommendations"].append(
                    f"Develop {remaining} additional series to reach target"
                )
            
            if metrics.average_series_consistency < 0.7:
                expansion_plan["expansion_recommendations"].append(
                    "Improve consistency across existing series before expansion"
                )
                expansion_plan["risk_assessment"] = "high"
            
            # Strategy-specific recommendations
            if franchise.configuration.expansion_strategy == "aggressive":
                expansion_plan["timeline_estimate"] = "3-6 months per series"
                expansion_plan["expansion_recommendations"].append(
                    "Consider parallel development of multiple series"
                )
            elif franchise.configuration.expansion_strategy == "conservative":
                expansion_plan["timeline_estimate"] = "12-18 months per series"
                expansion_plan["expansion_recommendations"].append(
                    "Focus on quality and consistency over speed"
                )
            
            return expansion_plan
            
        except Exception as e:
            logger.error(f"Error planning franchise expansion: {e}")
            return {"error": str(e)}
    
    def get_franchise_summary(self, franchise_uuid: str) -> Dict[str, Any]:
        """Get comprehensive summary of a franchise."""
        try:
            if franchise_uuid not in self.franchises:
                return {"error": "Franchise not found"}
            
            franchise = self.franchises[franchise_uuid]
            metrics = self.get_franchise_metrics(franchise_uuid)
            
            return {
                "franchise_info": {
                    "uuid": franchise_uuid,
                    "name": franchise.franchise_name,
                    "status": franchise.status.value,
                    "total_books": metrics.total_books,
                    "total_series": metrics.total_series,
                    "created": franchise.created_timestamp
                },
                "performance_metrics": metrics.to_dict(),
                "expansion_analysis": self.plan_franchise_expansion(franchise_uuid),
                "recent_activity": [s.series_name for s in franchise.series_blueprints[-3:]]
            }
            
        except Exception as e:
            logger.error(f"Error getting franchise summary: {e}")
            return {"error": str(e)}
    
    def export_franchise_data(self, franchise_uuid: str) -> Dict[str, Any]:
        """Export franchise data for storage or sharing."""
        try:
            if franchise_uuid not in self.franchises:
                return {"error": "Franchise not found"}
            
            franchise = self.franchises[franchise_uuid]
            
            return {
                "export_timestamp": datetime.now().isoformat(),
                "franchise": franchise.to_dict(),
                "metrics": self.get_franchise_metrics(franchise_uuid).to_dict(),
                "summary": self.get_franchise_summary(franchise_uuid)
            }
            
        except Exception as e:
            logger.error(f"Error exporting franchise data: {e}")
            return {"error": str(e)}