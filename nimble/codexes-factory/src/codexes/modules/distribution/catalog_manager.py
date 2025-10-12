"""
Catalog Manager for versioned storefront catalogs
Handles creation, versioning, and management of storefront catalog files
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
import pandas as pd

logger = logging.getLogger(__name__)


class CatalogManager:
    """Manages versioned storefront catalog files"""
    
    def __init__(self, catalog_dir: str = "data/catalogs"):
        self.catalog_dir = Path(catalog_dir)
        self.catalog_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def save_catalog_version(self, catalog_df: pd.DataFrame, imprint: str, 
                           version: Optional[str] = None) -> Path:
        """
        Save a catalog with version control
        
        Args:
            catalog_df: DataFrame containing catalog data
            imprint: Imprint name (e.g., 'xynapse_traces')
            version: Optional version string (defaults to timestamp)
            
        Returns:
            Path to the saved catalog file
        """
        if version is None:
            version = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create versioned filename
        versioned_filename = f"{imprint}_v{version}.csv"
        versioned_path = self.catalog_dir / versioned_filename
        
        # Save versioned catalog
        catalog_df.to_csv(versioned_path, index=False)
        self.logger.info(f"Saved versioned catalog: {versioned_path}")
        
        # Update 'latest' link
        latest_path = self.catalog_dir / f"{imprint}_latest.csv"
        if latest_path.exists():
            latest_path.unlink()
        shutil.copy2(versioned_path, latest_path)
        self.logger.info(f"Updated latest catalog: {latest_path}")
        
        # Update combined catalog if it exists
        self._update_combined_catalog(catalog_df, imprint)
        
        return versioned_path
    
    def save_catalog_from_file(self, source_path: str, imprint: str, 
                              version: Optional[str] = None) -> Path:
        """
        Save a catalog from an existing file with version control
        
        Args:
            source_path: Path to source catalog CSV
            imprint: Imprint name
            version: Optional version string
            
        Returns:
            Path to the saved catalog file
        """
        catalog_df = pd.read_csv(source_path)
        return self.save_catalog_version(catalog_df, imprint, version)
    
    def get_catalog_versions(self, imprint: str) -> List[Dict[str, str]]:
        """
        Get all versions of catalogs for an imprint
        
        Args:
            imprint: Imprint name
            
        Returns:
            List of version info dictionaries
        """
        pattern = f"{imprint}_v*.csv"
        version_files = list(self.catalog_dir.glob(pattern))
        
        versions = []
        for file_path in sorted(version_files):
            # Extract version from filename
            filename = file_path.stem
            version_part = filename.split('_v')[1]
            
            # Get file stats
            stat = file_path.stat()
            modified_time = datetime.fromtimestamp(stat.st_mtime)
            
            versions.append({
                'version': version_part,
                'filename': file_path.name,
                'path': str(file_path),
                'modified': modified_time.strftime('%Y-%m-%d %H:%M:%S'),
                'size_bytes': stat.st_size
            })
        
        return versions
    
    def get_latest_catalog(self, imprint: str) -> Optional[Path]:
        """
        Get path to the latest catalog for an imprint
        
        Args:
            imprint: Imprint name
            
        Returns:
            Path to latest catalog or None if not found
        """
        latest_path = self.catalog_dir / f"{imprint}_latest.csv"
        return latest_path if latest_path.exists() else None
    
    def _update_combined_catalog(self, new_catalog_df: pd.DataFrame, imprint: str):
        """Update the combined catalog with books from this imprint"""
        combined_path = self.catalog_dir / "combined_catalog.csv"
        
        if combined_path.exists():
            # Load existing combined catalog
            combined_df = pd.read_csv(combined_path)
            
            # Remove existing books from this imprint
            combined_df = combined_df[combined_df['imprint'] != imprint]
            
            # Add new books from this imprint
            combined_df = pd.concat([combined_df, new_catalog_df], ignore_index=True)
        else:
            # Create new combined catalog
            combined_df = new_catalog_df.copy()
        
        # Sort by publication date and imprint
        combined_df = combined_df.sort_values(['publication_date', 'imprint', 'title'])
        
        # Save combined catalog
        combined_df.to_csv(combined_path, index=False)
        self.logger.info(f"Updated combined catalog with {len(new_catalog_df)} books from {imprint}")
    
    def create_backup(self, catalog_path: str, backup_dir: str = "data/backups") -> Path:
        """
        Create a backup of a catalog file
        
        Args:
            catalog_path: Path to catalog to backup
            backup_dir: Directory to store backups
            
        Returns:
            Path to backup file
        """
        backup_path = Path(backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)
        
        source_path = Path(catalog_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{source_path.stem}_backup_{timestamp}.csv"
        backup_file = backup_path / backup_filename
        
        shutil.copy2(source_path, backup_file)
        self.logger.info(f"Created backup: {backup_file}")
        
        return backup_file
    
    def merge_catalogs(self, catalog_paths: List[str], output_path: str) -> bool:
        """
        Merge multiple catalog files into one
        
        Args:
            catalog_paths: List of catalog file paths to merge
            output_path: Path for merged catalog
            
        Returns:
            True if successful, False otherwise
        """
        try:
            merged_df = pd.DataFrame()
            
            for catalog_path in catalog_paths:
                df = pd.read_csv(catalog_path)
                merged_df = pd.concat([merged_df, df], ignore_index=True)
                self.logger.info(f"Added {len(df)} books from {catalog_path}")
            
            # Remove duplicates based on ISBN
            merged_df = merged_df.drop_duplicates(subset=['isbn13'], keep='last')
            
            # Sort by imprint and title
            merged_df = merged_df.sort_values(['imprint', 'title'])
            
            # Save merged catalog
            merged_df.to_csv(output_path, index=False)
            self.logger.info(f"Saved merged catalog with {len(merged_df)} unique books to {output_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error merging catalogs: {e}")
            return False
    
    def validate_catalog(self, catalog_path: str) -> Dict[str, any]:
        """
        Validate a catalog file and return validation results
        
        Args:
            catalog_path: Path to catalog to validate
            
        Returns:
            Dictionary with validation results
        """
        try:
            df = pd.read_csv(catalog_path)
            
            required_columns = [
                'id', 'title', 'subtitle', 'author', 'isbn13', 'series_name',
                'series_number', 'page_count', 'publication_date', 'imprint',
                'back_cover_text', 'storefront_publishers_note_en',
                'front_cover_image_path', 'full_spread_pdf_path', 'interior_pdf_path'
            ]
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            duplicate_isbns = df[df.duplicated(subset=['isbn13'], keep=False)]
            empty_titles = df[df['title'].isna() | (df['title'] == '')]
            empty_isbns = df[df['isbn13'].isna() | (df['isbn13'] == '')]
            
            return {
                'valid': len(missing_columns) == 0 and len(duplicate_isbns) == 0 and len(empty_titles) == 0,
                'total_books': len(df),
                'missing_columns': missing_columns,
                'duplicate_isbns': len(duplicate_isbns),
                'empty_titles': len(empty_titles),
                'empty_isbns': len(empty_isbns),
                'imprints': df['imprint'].unique().tolist(),
                'series': df['series_name'].unique().tolist()
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }


def main():
    """CLI interface for catalog management"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage versioned storefront catalogs")
    parser.add_argument("action", choices=["save", "versions", "validate", "merge"], 
                       help="Action to perform")
    parser.add_argument("--catalog", required=True, help="Path to catalog file")
    parser.add_argument("--imprint", help="Imprint name (for save action)")
    parser.add_argument("--version", help="Version string (optional)")
    parser.add_argument("--output", help="Output path (for merge action)")
    parser.add_argument("--catalogs", nargs="+", help="Multiple catalog paths (for merge action)")
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    manager = CatalogManager()
    
    if args.action == "save":
        if not args.imprint:
            print("Error: --imprint required for save action")
            exit(1)
        path = manager.save_catalog_from_file(args.catalog, args.imprint, args.version)
        print(f"✅ Saved catalog: {path}")
        
    elif args.action == "versions":
        if not args.imprint:
            print("Error: --imprint required for versions action")
            exit(1)
        versions = manager.get_catalog_versions(args.imprint)
        print(f"Versions for {args.imprint}:")
        for v in versions:
            print(f"  {v['version']} - {v['modified']} ({v['size_bytes']} bytes)")
            
    elif args.action == "validate":
        result = manager.validate_catalog(args.catalog)
        if result['valid']:
            print(f"✅ Catalog is valid ({result['total_books']} books)")
        else:
            print(f"❌ Catalog has issues:")
            if 'error' in result:
                print(f"  Error: {result['error']}")
            else:
                for issue in ['missing_columns', 'duplicate_isbns', 'empty_titles', 'empty_isbns']:
                    if result.get(issue):
                        print(f"  {issue}: {result[issue]}")
                        
    elif args.action == "merge":
        if not args.catalogs or not args.output:
            print("Error: --catalogs and --output required for merge action")
            exit(1)
        success = manager.merge_catalogs(args.catalogs, args.output)
        if success:
            print(f"✅ Merged catalogs to {args.output}")
        else:
            print("❌ Failed to merge catalogs")


if __name__ == "__main__":
    main()