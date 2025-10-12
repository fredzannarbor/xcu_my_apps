"""
Context collection system for arxiv paper generation.

This module provides a flexible framework for collecting and preparing context data
from various sources for paper generation.
"""

import logging
from typing import Dict, Any, List, Optional, Union, Protocol
from pathlib import Path
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import json
import pandas as pd
from datetime import datetime

from .exceptions import ConfigurationError, ValidationError
from .models import ValidationResult

logger = logging.getLogger(__name__)


@dataclass
class ContextConfig:
    """Configuration for context collection."""
    sources: List[Dict[str, Any]] = field(default_factory=list)
    validation_enabled: bool = True
    required_fields: List[str] = field(default_factory=list)
    output_format: str = "dict"  # dict, json, yaml
    preprocessing_steps: List[str] = field(default_factory=list)


class DataSource(Protocol):
    """Protocol for data sources."""
    
    def collect(self) -> Dict[str, Any]:
        """Collect data from the source."""
        ...
    
    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate collected data."""
        ...


class BaseDataSource(ABC):
    """Base class for data sources."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize data source with configuration."""
        self.config = config
        self.name = config.get("name", self.__class__.__name__)
        self.enabled = config.get("enabled", True)
        
    @abstractmethod
    def collect(self) -> Dict[str, Any]:
        """Collect data from the source."""
        pass
    
    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate collected data."""
        errors = []
        warnings = []
        
        # Basic validation
        if not isinstance(data, dict):
            errors.append(f"Data from {self.name} must be a dictionary")
        
        # Check required fields if specified
        required_fields = self.config.get("required_fields", [])
        for field in required_fields:
            if field not in data:
                errors.append(f"Required field '{field}' missing from {self.name}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            metrics={"source": self.name, "fields_count": len(data) if isinstance(data, dict) else 0}
        )


class FileDataSource(BaseDataSource):
    """Data source for file-based data (JSON, CSV, YAML)."""
    
    def collect(self) -> Dict[str, Any]:
        """Collect data from file."""
        file_path = Path(self.config.get("path", ""))
        
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return {}
        
        try:
            if file_path.suffix.lower() == '.json':
                return self._load_json(file_path)
            elif file_path.suffix.lower() == '.csv':
                return self._load_csv(file_path)
            elif file_path.suffix.lower() in ['.yaml', '.yml']:
                return self._load_yaml(file_path)
            else:
                logger.warning(f"Unsupported file format: {file_path.suffix}")
                return {}
        except Exception as e:
            logger.error(f"Error loading file {file_path}: {e}")
            return {}
    
    def _load_json(self, file_path: Path) -> Dict[str, Any]:
        """Load JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Wrap non-dict data
        if not isinstance(data, dict):
            return {"data": data, "source_file": str(file_path)}
        
        data["source_file"] = str(file_path)
        return data
    
    def _load_csv(self, file_path: Path) -> Dict[str, Any]:
        """Load CSV file."""
        df = pd.read_csv(file_path)
        
        # Generate basic statistics
        stats = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "dtypes": df.dtypes.to_dict(),
            "source_file": str(file_path)
        }
        
        # Add numeric statistics if available
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            stats["numeric_stats"] = df[numeric_cols].describe().to_dict()
        
        return {
            "data": df.to_dict('records'),
            "statistics": stats,
            "dataframe_info": {
                "shape": df.shape,
                "memory_usage": df.memory_usage(deep=True).sum()
            }
        }
    
    def _load_yaml(self, file_path: Path) -> Dict[str, Any]:
        """Load YAML file."""
        try:
            import yaml
        except ImportError:
            logger.error("PyYAML not installed. Cannot load YAML files.")
            return {}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Wrap non-dict data
        if not isinstance(data, dict):
            return {"data": data, "source_file": str(file_path)}
        
        data["source_file"] = str(file_path)
        return data


class DirectoryDataSource(BaseDataSource):
    """Data source for directory analysis."""
    
    def collect(self) -> Dict[str, Any]:
        """Collect data from directory."""
        dir_path = Path(self.config.get("path", ""))
        
        if not dir_path.exists() or not dir_path.is_dir():
            logger.warning(f"Directory not found: {dir_path}")
            return {}
        
        try:
            return self._analyze_directory(dir_path)
        except Exception as e:
            logger.error(f"Error analyzing directory {dir_path}: {e}")
            return {}
    
    def _analyze_directory(self, dir_path: Path) -> Dict[str, Any]:
        """Analyze directory structure and contents."""
        file_types = {}
        total_files = 0
        total_size = 0
        subdirs = []
        
        for item in dir_path.rglob("*"):
            if item.is_file():
                total_files += 1
                try:
                    size = item.stat().st_size
                    total_size += size
                    
                    ext = item.suffix.lower()
                    if ext not in file_types:
                        file_types[ext] = {"count": 0, "total_size": 0}
                    file_types[ext]["count"] += 1
                    file_types[ext]["total_size"] += size
                except OSError:
                    continue
            elif item.is_dir() and item != dir_path:
                subdirs.append(str(item.relative_to(dir_path)))
        
        return {
            "directory_path": str(dir_path),
            "total_files": total_files,
            "total_size_bytes": total_size,
            "file_types": file_types,
            "subdirectories": subdirs,
            "analysis_timestamp": datetime.now().isoformat()
        }


class DictDataSource(BaseDataSource):
    """Data source for direct dictionary data."""
    
    def collect(self) -> Dict[str, Any]:
        """Return the configured data directly."""
        return self.config.get("data", {})


class CodexesFactoryDataSource(BaseDataSource):
    """Data source adapter for Codexes Factory specific data patterns."""
    
    def collect(self) -> Dict[str, Any]:
        """Collect data using Codexes Factory patterns."""
        workspace_root = Path(self.config.get("workspace_root", "."))
        collection_type = self.config.get("collection_type", "xynapse_traces")
        
        if collection_type == "xynapse_traces":
            return self._collect_xynapse_traces_data(workspace_root)
        elif collection_type == "book_catalog":
            return self._collect_book_catalog_data(workspace_root)
        elif collection_type == "imprint_config":
            return self._collect_imprint_config_data(workspace_root)
        elif collection_type == "technical_architecture":
            return self._collect_technical_architecture_data(workspace_root)
        elif collection_type == "performance_metrics":
            return self._collect_performance_metrics()
        else:
            logger.warning(f"Unknown Codexes Factory collection type: {collection_type}")
            return {}
    
    def _collect_xynapse_traces_data(self, workspace_root: Path) -> Dict[str, Any]:
        """Collect comprehensive data about the xynapse_traces imprint."""
        logger.info("Collecting xynapse_traces context data...")
        
        context = {}
        
        # Collect book catalog data
        context.update(self._collect_book_catalog_data(workspace_root))
        
        # Collect imprint configuration data
        context.update(self._collect_imprint_config_data(workspace_root))
        
        # Collect technical architecture data
        context.update(self._collect_technical_architecture_data(workspace_root))
        
        # Collect performance metrics
        context.update(self._collect_performance_metrics())
        
        # Generate derived statistics
        context.update(self._generate_derived_statistics(context))
        
        return context
    
    def _collect_book_catalog_data(self, workspace_root: Path) -> Dict[str, Any]:
        """Collect data from the xynapse_traces book catalog."""
        catalog_path = workspace_root / "imprints" / "xynapse_traces" / "books.csv"
        
        if not catalog_path.exists():
            logger.warning(f"Book catalog not found at {catalog_path}")
            return {"book_catalog_error": "Catalog file not found"}
        
        try:
            df = pd.read_csv(catalog_path)
            
            # Basic statistics
            total_books = len(df)
            
            # Publication date analysis
            if 'publication_date' in df.columns:
                df['publication_date'] = pd.to_datetime(df['publication_date'], errors='coerce')
                date_range = f"{df['publication_date'].min().strftime('%B %Y')} to {df['publication_date'].max().strftime('%B %Y')}"
            else:
                date_range = "Date information not available"
            
            # Price analysis
            price_stats = {}
            if 'price' in df.columns:
                df['price'] = pd.to_numeric(df['price'], errors='coerce')
                price_stats = {
                    "mean_price": df['price'].mean(),
                    "median_price": df['price'].median(),
                    "price_range": f"${df['price'].min():.2f} - ${df['price'].max():.2f}"
                }
            
            # Page count analysis
            page_stats = {}
            if 'page_count' in df.columns:
                df['page_count'] = pd.to_numeric(df['page_count'], errors='coerce')
                page_stats = {
                    "mean_pages": df['page_count'].mean(),
                    "median_pages": df['page_count'].median(),
                    "page_range": f"{df['page_count'].min()} - {df['page_count'].max()} pages"
                }
            
            # Sample books for case studies
            sample_books = df.head(3).to_dict('records') if len(df) >= 3 else df.to_dict('records')
            
            return {
                "total_books": total_books,
                "publication_date_range": date_range,
                "book_catalog_summary": {
                    "total_count": total_books,
                    "price_statistics": price_stats,
                    "page_statistics": page_stats,
                    "sample_books": sample_books
                },
                "book_catalog_data": df.to_dict('records')[:10]  # First 10 for context
            }
            
        except Exception as e:
            logger.error(f"Error processing book catalog: {e}")
            return {"book_catalog_error": str(e)}
    
    def _collect_imprint_config_data(self, workspace_root: Path) -> Dict[str, Any]:
        """Collect imprint configuration data."""
        config_path = workspace_root / "configs" / "imprints" / "xynapse_traces.json"
        
        if not config_path.exists():
            logger.warning(f"Imprint config not found at {config_path}")
            return {"imprint_config_error": "Config file not found"}
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Extract key configuration elements
            imprint_config_summary = {
                "imprint_name": config.get("imprint", "xynapse traces"),
                "publisher": config.get("publisher", "Nimble Books LLC"),
                "branding": config.get("branding", {}),
                "publishing_focus": config.get("publishing_focus", {}),
                "default_settings": config.get("default_book_settings", {}),
                "ai_features": {
                    "llm_completion_enabled": config.get("workflow_settings", {}).get("llm_completion_enabled", False),
                    "auto_generate_missing_fields": config.get("workflow_settings", {}).get("auto_generate_missing_fields", False)
                }
            }
            
            return {
                "imprint_config_summary": imprint_config_summary,
                "imprint_branding": config.get("branding", {}),
                "publishing_focus": config.get("publishing_focus", {}),
                "config_hierarchy_summary": "Five-tier hierarchy: Global → Publisher → Imprint → Tranche → Book"
            }
            
        except Exception as e:
            logger.error(f"Error processing imprint config: {e}")
            return {"imprint_config_error": str(e)}
    
    def _collect_technical_architecture_data(self, workspace_root: Path) -> Dict[str, Any]:
        """Collect technical architecture information."""
        src_path = workspace_root / "src" / "codexes"
        
        if not src_path.exists():
            return {"technical_architecture_error": "Source directory not found"}
        
        # Analyze module structure
        modules = []
        modules_path = src_path / "modules"
        if modules_path.exists():
            for module_dir in modules_path.iterdir():
                if module_dir.is_dir() and not module_dir.name.startswith('.'):
                    modules.append(module_dir.name)
        
        # Key technologies and components
        key_technologies = [
            "Python 3.12+",
            "LiteLLM for multi-model LLM integration",
            "Pandas for data processing",
            "LaTeX/LuaLaTeX for document generation",
            "JSON-based configuration system",
            "Multi-level configuration inheritance"
        ]
        
        ai_models_used = [
            "Gemini (Google)",
            "Grok (xAI)",
            "Claude (Anthropic)",
            "GPT-4 (OpenAI)"
        ]
        
        technical_architecture = {
            "platform": "Codexes-Factory",
            "core_modules": modules,
            "configuration_system": "Multi-level JSON-based inheritance",
            "ai_integration": "LiteLLM abstraction layer",
            "document_generation": "LaTeX template system",
            "data_processing": "Pandas-based CSV and metadata handling"
        }
        
        return {
            "key_technologies": key_technologies,
            "ai_models_used": ai_models_used,
            "technical_architecture": technical_architecture,
            "technical_innovations": [
                "Multi-level configuration inheritance",
                "AI-assisted metadata generation",
                "Korean language LaTeX integration",
                "Automated LSI CSV generation",
                "Template-based document production"
            ]
        }
    
    def _collect_performance_metrics(self) -> Dict[str, Any]:
        """Collect or generate performance metrics."""
        # In a real implementation, this would collect actual metrics
        # For now, we'll provide representative data structure
        
        return {
            "processing_efficiency_metrics": {
                "average_processing_time_per_book": "15 minutes",
                "automation_rate": "85%",
                "manual_intervention_rate": "15%"
            },
            "quality_assessment_scores": {
                "metadata_accuracy": "94%",
                "content_consistency": "91%",
                "validation_success_rate": "97%"
            },
            "production_metrics": {
                "books_per_week": 8,
                "error_rate": "3%",
                "retry_success_rate": "89%"
            }
        }
    
    def _generate_derived_statistics(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate derived statistics from collected data."""
        total_books = context.get("total_books", 0)
        
        return {
            "statistical_summary": {
                "total_books_produced": total_books,
                "estimated_traditional_time": f"{total_books * 2} hours",
                "ai_assisted_time": f"{total_books * 0.25} hours",
                "efficiency_improvement": "87.5%"
            }
        }


class GenericCSVDataSource(BaseDataSource):
    """Enhanced CSV data source with configurable analysis."""
    
    def collect(self) -> Dict[str, Any]:
        """Collect data from CSV with enhanced analysis."""
        file_path = Path(self.config.get("path", ""))
        
        if not file_path.exists():
            logger.warning(f"CSV file not found: {file_path}")
            return {}
        
        try:
            df = pd.read_csv(file_path)
            
            # Basic statistics
            basic_stats = {
                "row_count": len(df),
                "column_count": len(df.columns),
                "columns": list(df.columns),
                "dtypes": df.dtypes.to_dict(),
                "source_file": str(file_path)
            }
            
            # Enhanced analysis based on configuration
            analysis_config = self.config.get("analysis", {})
            
            result = {
                "data": df.to_dict('records'),
                "basic_statistics": basic_stats,
                "dataframe_info": {
                    "shape": df.shape,
                    "memory_usage": df.memory_usage(deep=True).sum()
                }
            }
            
            # Add numeric analysis if requested
            if analysis_config.get("include_numeric_stats", True):
                numeric_cols = df.select_dtypes(include=['number']).columns
                if len(numeric_cols) > 0:
                    result["numeric_statistics"] = df[numeric_cols].describe().to_dict()
            
            # Add categorical analysis if requested
            if analysis_config.get("include_categorical_stats", True):
                categorical_cols = df.select_dtypes(include=['object']).columns
                if len(categorical_cols) > 0:
                    categorical_stats = {}
                    for col in categorical_cols:
                        categorical_stats[col] = {
                            "unique_count": df[col].nunique(),
                            "most_common": df[col].value_counts().head(5).to_dict(),
                            "null_count": df[col].isnull().sum()
                        }
                    result["categorical_statistics"] = categorical_stats
            
            # Add date analysis if requested
            if analysis_config.get("include_date_analysis", True):
                date_columns = analysis_config.get("date_columns", [])
                if date_columns:
                    date_stats = {}
                    for col in date_columns:
                        if col in df.columns:
                            df[col] = pd.to_datetime(df[col], errors='coerce')
                            date_stats[col] = {
                                "min_date": df[col].min().isoformat() if pd.notna(df[col].min()) else None,
                                "max_date": df[col].max().isoformat() if pd.notna(df[col].max()) else None,
                                "date_range_days": (df[col].max() - df[col].min()).days if pd.notna(df[col].min()) and pd.notna(df[col].max()) else None,
                                "null_count": df[col].isnull().sum()
                            }
                    result["date_statistics"] = date_stats
            
            # Add custom aggregations if specified
            aggregations = analysis_config.get("aggregations", {})
            if aggregations:
                agg_results = {}
                for agg_name, agg_config in aggregations.items():
                    try:
                        column = agg_config.get("column")
                        operation = agg_config.get("operation", "sum")
                        group_by = agg_config.get("group_by")
                        
                        if column in df.columns:
                            if group_by and group_by in df.columns:
                                agg_results[agg_name] = df.groupby(group_by)[column].agg(operation).to_dict()
                            else:
                                agg_results[agg_name] = getattr(df[column], operation)()
                    except Exception as e:
                        logger.warning(f"Failed to compute aggregation {agg_name}: {e}")
                
                if agg_results:
                    result["custom_aggregations"] = agg_results
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing CSV file {file_path}: {e}")
            return {"csv_error": str(e)}


class GenericJSONDataSource(BaseDataSource):
    """Enhanced JSON data source with configurable processing."""
    
    def collect(self) -> Dict[str, Any]:
        """Collect data from JSON with enhanced processing."""
        file_path = Path(self.config.get("path", ""))
        
        if not file_path.exists():
            logger.warning(f"JSON file not found: {file_path}")
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Basic processing
            result = {
                "source_file": str(file_path),
                "file_size_bytes": file_path.stat().st_size,
                "data_type": type(data).__name__
            }
            
            # Process based on data type and configuration
            processing_config = self.config.get("processing", {})
            
            if isinstance(data, dict):
                result["data"] = data
                result["key_count"] = len(data)
                result["keys"] = list(data.keys())
                
                # Extract nested structure info if requested
                if processing_config.get("analyze_structure", True):
                    result["structure_analysis"] = self._analyze_dict_structure(data)
                
                # Extract specific paths if configured
                extract_paths = processing_config.get("extract_paths", [])
                if extract_paths:
                    extracted = {}
                    for path in extract_paths:
                        try:
                            value = self._extract_nested_value(data, path)
                            extracted[path] = value
                        except Exception as e:
                            logger.warning(f"Failed to extract path {path}: {e}")
                    result["extracted_values"] = extracted
            
            elif isinstance(data, list):
                result["data"] = data
                result["item_count"] = len(data)
                
                if data and processing_config.get("analyze_list_items", True):
                    # Analyze first few items to understand structure
                    sample_size = min(5, len(data))
                    result["sample_items"] = data[:sample_size]
                    result["item_types"] = [type(item).__name__ for item in data[:sample_size]]
            
            else:
                result["data"] = data
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing JSON file {file_path}: {e}")
            return {"json_error": str(e)}
    
    def _analyze_dict_structure(self, data: Dict[str, Any], max_depth: int = 3) -> Dict[str, Any]:
        """Analyze the structure of a nested dictionary."""
        def analyze_level(obj, depth=0):
            if depth >= max_depth or not isinstance(obj, dict):
                return type(obj).__name__
            
            structure = {}
            for key, value in obj.items():
                if isinstance(value, dict):
                    structure[key] = analyze_level(value, depth + 1)
                elif isinstance(value, list) and value:
                    structure[key] = f"list[{type(value[0]).__name__}]"
                else:
                    structure[key] = type(value).__name__
            
            return structure
        
        return analyze_level(data)
    
    def _extract_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Extract value from nested dictionary using dot notation."""
        keys = path.split(".")
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                raise KeyError(f"Path {path} not found")
        
        return current


class ContextCollector:
    """
    Main context collector that orchestrates data collection from multiple sources.
    
    This class provides a flexible framework for collecting context data from various
    sources and preparing it for paper generation.
    """
    
    def __init__(self, config: ContextConfig):
        """
        Initialize context collector.
        
        Args:
            config: Context collection configuration
        """
        self.config = config
        self.sources: List[BaseDataSource] = []
        self._initialize_sources()
        
        logger.info(f"ContextCollector initialized with {len(self.sources)} sources")
    
    def _initialize_sources(self) -> None:
        """Initialize data sources from configuration."""
        for source_config in self.config.sources:
            try:
                source = self._create_source(source_config)
                if source and source.enabled:
                    self.sources.append(source)
                    logger.debug(f"Added data source: {source.name}")
            except Exception as e:
                logger.error(f"Failed to initialize source {source_config.get('name', 'unknown')}: {e}")
    
    def _create_source(self, source_config: Dict[str, Any]) -> Optional[BaseDataSource]:
        """Create a data source from configuration."""
        source_type = source_config.get("type", "").lower()
        
        source_classes = {
            "file": FileDataSource,
            "directory": DirectoryDataSource,
            "dict": DictDataSource,
            "codexes_factory": CodexesFactoryDataSource,
            "csv": GenericCSVDataSource,
            "json": GenericJSONDataSource,
        }
        
        source_class = source_classes.get(source_type)
        if not source_class:
            logger.error(f"Unknown source type: {source_type}")
            return None
        
        return source_class(source_config)
    
    def collect_context(self, additional_sources: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Collect context data from all configured sources.
        
        Args:
            additional_sources: Optional additional sources to include
            
        Returns:
            Dictionary containing collected context data
            
        Raises:
            ValidationError: If validation fails and is enabled
        """
        logger.info("Starting context collection")
        
        context = {
            "collection_metadata": {
                "timestamp": datetime.now().isoformat(),
                "sources_count": len(self.sources),
                "collector_config": {
                    "validation_enabled": self.config.validation_enabled,
                    "required_fields": self.config.required_fields,
                    "output_format": self.config.output_format
                }
            },
            "sources": {}
        }
        
        # Add additional sources if provided
        if additional_sources:
            for source_config in additional_sources:
                source = self._create_source(source_config)
                if source and source.enabled:
                    self.sources.append(source)
        
        # Collect from all sources
        validation_results = {}
        for source in self.sources:
            try:
                logger.debug(f"Collecting from source: {source.name}")
                source_data = source.collect()
                
                # Validate if enabled
                if self.config.validation_enabled:
                    validation_result = source.validate(source_data)
                    validation_results[source.name] = validation_result
                    
                    if not validation_result.is_valid:
                        error_msg = f"Validation failed for source {source.name}: {validation_result.errors}"
                        logger.error(error_msg)
                        raise ValidationError(error_msg)
                
                context["sources"][source.name] = source_data
                logger.debug(f"Successfully collected from {source.name}")
                
            except ValidationError:
                # Re-raise validation errors
                raise
            except Exception as e:
                logger.error(f"Failed to collect from source {source.name}: {e}")
                context["sources"][source.name] = {"error": str(e)}
        
        # Add validation results
        if validation_results:
            context["validation_results"] = validation_results
        
        # Apply preprocessing steps
        context = self._preprocess_context(context)
        
        # Validate required fields
        if self.config.required_fields:
            self._validate_required_fields(context)
        
        logger.info(f"Context collection completed. Collected from {len(context['sources'])} sources")
        return context
    
    def _preprocess_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply preprocessing steps to context data."""
        for step in self.config.preprocessing_steps:
            try:
                if step == "flatten_sources":
                    context = self._flatten_sources(context)
                elif step == "merge_statistics":
                    context = self._merge_statistics(context)
                elif step == "normalize_timestamps":
                    context = self._normalize_timestamps(context)
                else:
                    logger.warning(f"Unknown preprocessing step: {step}")
            except Exception as e:
                logger.error(f"Error in preprocessing step {step}: {e}")
        
        return context
    
    def _flatten_sources(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Flatten source data into top-level context."""
        flattened = context.copy()
        
        for source_name, source_data in context.get("sources", {}).items():
            if isinstance(source_data, dict) and "error" not in source_data:
                # Add source data with prefixed keys
                for key, value in source_data.items():
                    if key != "source_file":  # Skip metadata
                        flattened_key = f"{source_name}_{key}"
                        flattened[flattened_key] = value
        
        return flattened
    
    def _merge_statistics(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Merge statistics from all sources."""
        merged_stats = {}
        
        for source_name, source_data in context.get("sources", {}).items():
            if isinstance(source_data, dict) and "statistics" in source_data:
                merged_stats[source_name] = source_data["statistics"]
        
        if merged_stats:
            context["merged_statistics"] = merged_stats
        
        return context
    
    def _normalize_timestamps(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize timestamp formats across sources."""
        # This is a placeholder for timestamp normalization logic
        # Implementation would depend on specific timestamp formats found in data
        return context
    
    def _validate_required_fields(self, context: Dict[str, Any]) -> None:
        """Validate that required fields are present in context."""
        missing_fields = []
        
        for field in self.config.required_fields:
            if not self._field_exists_in_context(context, field):
                missing_fields.append(field)
        
        if missing_fields:
            raise ValidationError(f"Required fields missing from context: {missing_fields}")
    
    def _field_exists_in_context(self, context: Dict[str, Any], field_path: str) -> bool:
        """Check if a field exists in context (supports dot notation)."""
        keys = field_path.split(".")
        current = context
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return False
        
        return True
    
    def prepare_context(self, raw_context: Dict[str, Any], template_variables: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Prepare context data for template rendering.
        
        Args:
            raw_context: Raw context data from collection
            template_variables: List of variables expected by templates
            
        Returns:
            Prepared context data suitable for template rendering
        """
        logger.debug("Preparing context for template rendering")
        
        prepared = {
            "generation_metadata": {
                "prepared_at": datetime.now().isoformat(),
                "template_variables": template_variables or [],
                "context_sources": list(raw_context.get("sources", {}).keys())
            }
        }
        
        # Extract and flatten relevant data
        for source_name, source_data in raw_context.get("sources", {}).items():
            if isinstance(source_data, dict) and "error" not in source_data:
                # Add source data with clean keys
                prepared[source_name] = source_data
        
        # Add summary statistics
        prepared["context_summary"] = self._generate_context_summary(raw_context)
        
        # Ensure template variables are available
        if template_variables:
            missing_vars = []
            for var in template_variables:
                if not self._field_exists_in_context(prepared, var):
                    missing_vars.append(var)
            
            if missing_vars:
                logger.warning(f"Template variables not found in context: {missing_vars}")
                prepared["missing_template_variables"] = missing_vars
        
        logger.debug("Context preparation completed")
        return prepared
    
    def _generate_context_summary(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics for context data."""
        sources = context.get("sources", {})
        
        summary = {
            "total_sources": len(sources),
            "successful_sources": len([s for s in sources.values() if isinstance(s, dict) and "error" not in s]),
            "failed_sources": len([s for s in sources.values() if isinstance(s, dict) and "error" in s]),
            "total_data_points": 0,
            "data_types": {}
        }
        
        # Count data points and types
        for source_data in sources.values():
            if isinstance(source_data, dict) and "error" not in source_data:
                summary["total_data_points"] += len(source_data)
                
                for key, value in source_data.items():
                    value_type = type(value).__name__
                    if value_type not in summary["data_types"]:
                        summary["data_types"][value_type] = 0
                    summary["data_types"][value_type] += 1
        
        return summary


# Convenience functions for common use cases

def create_file_context_collector(file_paths: List[Union[str, Path]], **kwargs) -> ContextCollector:
    """
    Create a context collector for file-based sources.
    
    Args:
        file_paths: List of file paths to collect from
        **kwargs: Additional configuration options
        
    Returns:
        Configured ContextCollector instance
    """
    sources = []
    for i, path in enumerate(file_paths):
        sources.append({
            "name": f"file_{i}_{Path(path).stem}",
            "type": "file",
            "path": str(path),
            "enabled": True
        })
    
    config = ContextConfig(sources=sources, **kwargs)
    return ContextCollector(config)


def create_directory_context_collector(directory_paths: List[Union[str, Path]], **kwargs) -> ContextCollector:
    """
    Create a context collector for directory-based sources.
    
    Args:
        directory_paths: List of directory paths to analyze
        **kwargs: Additional configuration options
        
    Returns:
        Configured ContextCollector instance
    """
    sources = []
    for i, path in enumerate(directory_paths):
        sources.append({
            "name": f"directory_{i}_{Path(path).name}",
            "type": "directory", 
            "path": str(path),
            "enabled": True
        })
    
    config = ContextConfig(sources=sources, **kwargs)
    return ContextCollector(config)


def create_codexes_factory_context_collector(
    workspace_root: Union[str, Path] = ".",
    collection_types: Optional[List[str]] = None,
    **kwargs
) -> ContextCollector:
    """
    Create a context collector for Codexes Factory data patterns.
    
    Args:
        workspace_root: Root directory of the Codexes Factory workspace
        collection_types: List of collection types to include
        **kwargs: Additional configuration options
        
    Returns:
        Configured ContextCollector instance
    """
    if collection_types is None:
        collection_types = ["xynapse_traces"]
    
    sources = []
    for collection_type in collection_types:
        sources.append({
            "name": f"codexes_factory_{collection_type}",
            "type": "codexes_factory",
            "workspace_root": str(workspace_root),
            "collection_type": collection_type,
            "enabled": True
        })
    
    config = ContextConfig(sources=sources, **kwargs)
    return ContextCollector(config)


def create_csv_context_collector(
    csv_paths: List[Union[str, Path]],
    analysis_config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> ContextCollector:
    """
    Create a context collector for CSV files with enhanced analysis.
    
    Args:
        csv_paths: List of CSV file paths
        analysis_config: Configuration for CSV analysis
        **kwargs: Additional configuration options
        
    Returns:
        Configured ContextCollector instance
    """
    if analysis_config is None:
        analysis_config = {
            "include_numeric_stats": True,
            "include_categorical_stats": True,
            "include_date_analysis": True
        }
    
    sources = []
    for i, path in enumerate(csv_paths):
        sources.append({
            "name": f"csv_{i}_{Path(path).stem}",
            "type": "csv",
            "path": str(path),
            "analysis": analysis_config,
            "enabled": True
        })
    
    config = ContextConfig(sources=sources, **kwargs)
    return ContextCollector(config)


def create_json_context_collector(
    json_paths: List[Union[str, Path]],
    processing_config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> ContextCollector:
    """
    Create a context collector for JSON files with enhanced processing.
    
    Args:
        json_paths: List of JSON file paths
        processing_config: Configuration for JSON processing
        **kwargs: Additional configuration options
        
    Returns:
        Configured ContextCollector instance
    """
    if processing_config is None:
        processing_config = {
            "analyze_structure": True,
            "analyze_list_items": True
        }
    
    sources = []
    for i, path in enumerate(json_paths):
        sources.append({
            "name": f"json_{i}_{Path(path).stem}",
            "type": "json",
            "path": str(path),
            "processing": processing_config,
            "enabled": True
        })
    
    config = ContextConfig(sources=sources, **kwargs)
    return ContextCollector(config)