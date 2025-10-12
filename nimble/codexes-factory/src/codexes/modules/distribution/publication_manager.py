"""
Publication Manager - Handles book publication status and asset packaging
"""

import json
import logging
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
import pandas as pd
import re

logger = logging.getLogger(__name__)


class PublicationManager:
    """Manages publication status and asset packaging for published books"""
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.publication_db_path = self.base_dir / "data" / "publication_status.json"
        self.published_books_dir = self.base_dir / "data" / "published_books"
        self.logger = logging.getLogger(__name__)
        
        # Ensure directories exist
        self.publication_db_path.parent.mkdir(parents=True, exist_ok=True)
        self.published_books_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing publication status
        self.publication_status = self._load_publication_status()
    
    def _load_publication_status(self) -> Dict:
        """Load publication status database"""
        if self.publication_db_path.exists():
            try:
                with open(self.publication_db_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        return {
            "last_updated": datetime.now().isoformat(),
            "books": {},
            "statistics": {
                "total_published": 0,
                "by_imprint": {},
                "by_channel": {"LSI": 0, "KDP": 0, "storefront": 0}
            }
        }
    
    def _save_publication_status(self):
        """Save publication status database"""
        self.publication_status["last_updated"] = datetime.now().isoformat()
        
        with open(self.publication_db_path, 'w') as f:
            json.dump(self.publication_status, f, indent=2)
    
    def mark_book_published(self, isbn: str, title: str, imprint: str, 
                           distribution_channels: List[str]) -> bool:
        """
        Mark a book as published with specified distribution channels
        
        Args:
            isbn: Book ISBN
            title: Book title
            imprint: Publishing imprint
            distribution_channels: List of channels (LSI, KDP, storefront)
            
        Returns:
            True if successfully marked as published
        """
        try:
            book_key = isbn
            
            publication_record = {
                "isbn": isbn,
                "title": title,
                "imprint": imprint,
                "distribution_channels": distribution_channels,
                "publication_date": datetime.now().isoformat(),
                "status": "published",
                "assets_packaged": False,
                "package_path": None
            }
            
            self.publication_status["books"][book_key] = publication_record
            
            # Update statistics
            self.publication_status["statistics"]["total_published"] = len(
                [b for b in self.publication_status["books"].values() if b["status"] == "published"]
            )
            
            # Update imprint statistics
            if imprint not in self.publication_status["statistics"]["by_imprint"]:
                self.publication_status["statistics"]["by_imprint"][imprint] = 0
            self.publication_status["statistics"]["by_imprint"][imprint] += 1
            
            # Update channel statistics
            for channel in distribution_channels:
                if channel in self.publication_status["statistics"]["by_channel"]:
                    self.publication_status["statistics"]["by_channel"][channel] += 1
            
            self._save_publication_status()
            self.logger.info(f"✅ Marked book as published: {title} (ISBN: {isbn})")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error marking book as published: {e}")
            return False
    
    def get_published_books(self, imprint: Optional[str] = None) -> List[Dict]:
        """Get list of published books, optionally filtered by imprint"""
        published_books = [
            book for book in self.publication_status["books"].values()
            if book["status"] == "published"
        ]
        
        if imprint:
            published_books = [book for book in published_books if book["imprint"] == imprint]
        
        return published_books
    
    def package_published_book_assets(self, isbn: str) -> Optional[Path]:
        """
        Package all assets for a published book into a zip file
        
        Args:
            isbn: Book ISBN
            
        Returns:
            Path to created zip file or None if failed
        """
        try:
            # Get book record
            if isbn not in self.publication_status["books"]:
                self.logger.error(f"Book with ISBN {isbn} not found in publication database")
                return None
            
            book_record = self.publication_status["books"][isbn]
            title = book_record["title"]
            imprint = book_record["imprint"]
            
            # Create safe filename
            safe_title = re.sub(r'[^\w\s-]', '', title).replace(' ', '_')[:10]
            zip_filename = f"{isbn}_{safe_title}.zip"
            zip_path = self.published_books_dir / zip_filename
            
            self.logger.info(f"Packaging assets for: {title} (ISBN: {isbn})")
            
            # Collect all possible asset paths
            asset_paths = self._collect_book_assets(isbn, title, imprint)
            
            # Create zip file
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                assets_found = 0
                
                for asset_type, asset_path in asset_paths.items():
                    if asset_path and Path(asset_path).exists():
                        # Add to zip with organized structure
                        zip_internal_path = f"{asset_type}/{Path(asset_path).name}"
                        zip_file.write(asset_path, zip_internal_path)
                        assets_found += 1
                        self.logger.debug(f"Added {asset_type}: {asset_path}")
                    else:
                        self.logger.warning(f"Asset not found - {asset_type}: {asset_path}")
                
                # Add metadata file
                metadata = {
                    "isbn": isbn,
                    "title": title,
                    "imprint": imprint,
                    "package_created": datetime.now().isoformat(),
                    "assets_included": assets_found,
                    "distribution_channels": book_record["distribution_channels"],
                    "asset_inventory": {k: str(v) if v else "NOT FOUND" for k, v in asset_paths.items()}
                }
                
                zip_file.writestr("package_metadata.json", json.dumps(metadata, indent=2))
            
            # Update publication record
            book_record["assets_packaged"] = True
            book_record["package_path"] = str(zip_path)
            book_record["package_created"] = datetime.now().isoformat()
            book_record["assets_found"] = assets_found
            
            self._save_publication_status()
            
            self.logger.info(f"✅ Created asset package: {zip_path} ({assets_found} assets)")
            return zip_path
            
        except Exception as e:
            self.logger.error(f"Error packaging assets for ISBN {isbn}: {e}")
            return None
    
    def _collect_book_assets(self, isbn: str, title: str, imprint: str) -> Dict[str, Optional[str]]:
        """Collect all possible asset paths for a book"""
        
        # Create safe filename variants
        safe_title = re.sub(r'[^\w\s-]', '', title).replace(' ', '_')
        safe_title_spaces = title.replace(':', '').replace('?', '')
        
        # Common path patterns
        build_dir = f"output/{imprint}_build"
        
        asset_paths = {
            # Core processing files
            "final_json": self._find_file_variant([
                f"{build_dir}/processed_json/{safe_title}.json",
                f"output/{imprint}/{safe_title}.json",
                f"output/{safe_title}.json"
            ]),
            
            "response_json": self._find_file_variant([
                f"{build_dir}/responses/{safe_title}_response.json",
                f"output/responses/{safe_title}_response.json"
            ]),
            
            # PDFs
            "interior_pdf": self._find_file_variant([
                f"{build_dir}/interiors/{safe_title}_interior.pdf",
                f"{build_dir}/interiors/{isbn}_{safe_title}_interior.pdf",
                f"output/{imprint}/interiors/{safe_title}.pdf"
            ]),
            
            "cover_pdf": self._find_file_variant([
                f"{build_dir}/covers/{safe_title}_cover.pdf",
                f"{build_dir}/covers/{safe_title}_cover_spread.pdf",
                f"{build_dir}/covers/{isbn}_{safe_title}_cover.pdf"
            ]),
            
            # Cover images
            "front_cover_image": self._find_file_variant([
                f"{build_dir}/covers/{safe_title}_front_cover.png",
                f"{build_dir}/covers/{isbn}_{safe_title}_front_cover.png",
                f"output/{imprint}/covers/{safe_title}_front.png"
            ]),
            
            "back_cover_image": self._find_file_variant([
                f"{build_dir}/covers/{safe_title}_back_cover.png",
                f"{build_dir}/covers/{isbn}_{safe_title}_back_cover.png"
            ]),
            
            # Distribution files
            "lsi_csv": self._find_file_variant([
                f"ftp2lsi/csv/{imprint}_tranche1_processed.csv",
                f"data/lsi_exports/{isbn}_{safe_title}.csv",
                f"data/lsi/{imprint}_latest.csv"
            ]),
            
            "storefront_csv": self._find_file_variant([
                f"data/catalogs/{imprint}_latest.csv",
                f"imprints/{imprint}/books.csv",
                f"data/books.csv"
            ]),
            
            # Marketing materials
            "substack_post": self._find_file_variant([
                f"marketing/{imprint}/substack_posts/{safe_title.lower()}.html",
                f"marketing/xynapse_traces/substack_posts/{safe_title.lower()}.html"
            ]),
            
            # Templates and configs
            "latex_template": self._find_file_variant([
                f"imprints/{imprint}/template.tex",
                f"templates/{imprint}_template.tex"
            ]),
            
            "cover_template": self._find_file_variant([
                f"imprints/{imprint}/cover_template.tex",
                f"templates/{imprint}_cover_template.tex"
            ]),
            
            "prompts_config": self._find_file_variant([
                f"imprints/{imprint}/prompts.json"
            ])
        }
        
        return asset_paths
    
    def _find_file_variant(self, possible_paths: List[str]) -> Optional[str]:
        """Find the first existing file from a list of possible paths"""
        for path_str in possible_paths:
            path = self.base_dir / path_str
            if path.exists():
                return str(path)
        return None
    
    def package_all_published_books(self, imprint: Optional[str] = None) -> List[Path]:
        """Package assets for all published books"""
        published_books = self.get_published_books(imprint)
        packaged_files = []
        
        self.logger.info(f"Packaging assets for {len(published_books)} published books")
        
        for book in published_books:
            if not book.get("assets_packaged", False):
                package_path = self.package_published_book_assets(book["isbn"])
                if package_path:
                    packaged_files.append(package_path)
        
        return packaged_files
    
    def get_publication_statistics(self) -> Dict:
        """Get publication statistics"""
        return self.publication_status.get("statistics", {})
    
    def mark_book_unpublished(self, isbn: str) -> bool:
        """Mark a book as unpublished (remove from published list)"""
        try:
            if isbn in self.publication_status["books"]:
                book_record = self.publication_status["books"][isbn]
                
                # Update statistics
                imprint = book_record.get("imprint", "unknown")
                channels = book_record.get("distribution_channels", [])
                
                # Decrease counters
                if imprint in self.publication_status["statistics"]["by_imprint"]:
                    self.publication_status["statistics"]["by_imprint"][imprint] -= 1
                
                for channel in channels:
                    if channel in self.publication_status["statistics"]["by_channel"]:
                        self.publication_status["statistics"]["by_channel"][channel] -= 1
                
                # Remove the book record
                del self.publication_status["books"][isbn]
                
                # Update total
                self.publication_status["statistics"]["total_published"] = len(
                    [b for b in self.publication_status["books"].values() if b["status"] == "published"]
                )
                
                self._save_publication_status()
                self.logger.info(f"Marked book as unpublished: {isbn}")
                return True
            else:
                self.logger.warning(f"Book not found in publication database: {isbn}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error marking book as unpublished: {e}")
            return False
    
    def is_book_published(self, isbn: str) -> bool:
        """Check if a book is marked as published"""
        return (isbn in self.publication_status["books"] and 
                self.publication_status["books"][isbn]["status"] == "published")
    
    def get_book_package_path(self, isbn: str) -> Optional[Path]:
        """Get the asset package path for a published book"""
        if isbn in self.publication_status["books"]:
            package_path = self.publication_status["books"][isbn].get("package_path")
            if package_path and Path(package_path).exists():
                return Path(package_path)
        return None
    
    def cleanup_unpublished_packages(self) -> int:
        """Remove asset packages for books that are no longer marked as published"""
        removed_count = 0
        
        # Get all published ISBNs
        published_isbns = set(
            isbn for isbn, book in self.publication_status["books"].items()
            if book["status"] == "published"
        )
        
        # Check all zip files in published books directory
        for zip_file in self.published_books_dir.glob("*.zip"):
            # Extract ISBN from filename (format: ISBN_safetitle.zip)
            filename_parts = zip_file.stem.split('_', 1)
            if len(filename_parts) >= 1:
                file_isbn = filename_parts[0]
                
                if file_isbn not in published_isbns:
                    try:
                        zip_file.unlink()
                        removed_count += 1
                        self.logger.info(f"Removed orphaned package: {zip_file.name}")
                    except Exception as e:
                        self.logger.error(f"Error removing package {zip_file.name}: {e}")
        
        return removed_count
    
    def validate_book_assets(self, isbn: str) -> Dict[str, any]:
        """Validate that all expected assets exist for a book"""
        if isbn not in self.publication_status["books"]:
            return {"valid": False, "error": "Book not found in publication database"}
        
        book_record = self.publication_status["books"][isbn]
        title = book_record["title"]
        imprint = book_record["imprint"]
        
        # Collect asset paths
        asset_paths = self._collect_book_assets(isbn, title, imprint)
        
        # Check which assets exist
        found_assets = {}
        missing_assets = {}
        
        for asset_type, asset_path in asset_paths.items():
            if asset_path and Path(asset_path).exists():
                found_assets[asset_type] = asset_path
            else:
                missing_assets[asset_type] = asset_path or "Path not determined"
        
        return {
            "valid": len(missing_assets) == 0,
            "isbn": isbn,
            "title": title,
            "imprint": imprint,
            "total_assets": len(asset_paths),
            "found_assets": found_assets,
            "missing_assets": missing_assets,
            "assets_packaged": book_record.get("assets_packaged", False),
            "package_path": book_record.get("package_path")
        }


class PublicationCLI:
    """CLI interface for publication management"""
    
    def __init__(self, publication_manager: PublicationManager):
        self.manager = publication_manager
        self.logger = logging.getLogger(__name__)
    
    def mark_published_from_catalog(self, catalog_path: str, isbn_list: List[str], 
                                   distribution_channels: List[str]) -> Dict[str, bool]:
        """Mark multiple books as published from catalog data"""
        try:
            # Load catalog
            df = pd.read_csv(catalog_path)
            
            results = {}
            
            for isbn in isbn_list:
                # Find book in catalog
                book_rows = df[df['isbn13'].astype(str) == str(isbn)]
                
                if len(book_rows) == 0:
                    self.logger.error(f"Book with ISBN {isbn} not found in catalog")
                    results[isbn] = False
                    continue
                
                book_row = book_rows.iloc[0]
                title = book_row['title']
                imprint = book_row['imprint']
                
                # Mark as published
                success = self.manager.mark_book_published(
                    isbn=str(isbn),
                    title=title,
                    imprint=imprint,
                    distribution_channels=distribution_channels
                )
                
                results[isbn] = success
                
                if success:
                    self.logger.info(f"✅ Marked as published: {title}")
                else:
                    self.logger.error(f"❌ Failed to mark as published: {title}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error marking books from catalog: {e}")
            return {isbn: False for isbn in isbn_list}
    
    def package_books_batch(self, isbn_list: List[str]) -> List[Path]:
        """Package assets for multiple books"""
        packaged_files = []
        
        for isbn in isbn_list:
            if self.manager.is_book_published(isbn):
                package_path = self.manager.package_published_book_assets(isbn)
                if package_path:
                    packaged_files.append(package_path)
                    print(f"✅ Packaged: {package_path.name}")
                else:
                    print(f"❌ Failed to package ISBN: {isbn}")
            else:
                print(f"⚠️  Book not marked as published: {isbn}")
        
        return packaged_files


def main():
    """CLI interface for publication management"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage book publication status and assets")
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Mark published command
    publish_parser = subparsers.add_parser('mark-published', help='Mark books as published')
    publish_parser.add_argument('--catalog', required=True, help='Path to catalog CSV file')
    publish_parser.add_argument('--isbn', nargs='+', required=True, help='ISBN(s) to mark as published')
    publish_parser.add_argument('--channels', nargs='+', choices=['LSI', 'KDP', 'storefront'], 
                               required=True, help='Distribution channels')
    
    # Package assets command
    package_parser = subparsers.add_parser('package', help='Package book assets')
    package_parser.add_argument('--isbn', nargs='+', required=True, help='ISBN(s) to package')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show publication status')
    status_parser.add_argument('--imprint', help='Filter by imprint')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List published books')
    list_parser.add_argument('--imprint', help='Filter by imprint')
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Initialize manager
    manager = PublicationManager()
    cli = PublicationCLI(manager)
    
    if args.command == 'mark-published':
        results = cli.mark_published_from_catalog(args.catalog, args.isbn, args.channels)
        success_count = sum(1 for success in results.values() if success)
        print(f"✅ Successfully marked {success_count}/{len(args.isbn)} books as published")
        
    elif args.command == 'package':
        packaged_files = cli.package_books_batch(args.isbn)
        print(f"✅ Packaged {len(packaged_files)} books")
        
    elif args.command == 'status':
        stats = manager.get_publication_statistics()
        print(f"📊 Publication Statistics:")
        print(f"  Total Published: {stats.get('total_published', 0)}")
        print(f"  By Channel: {stats.get('by_channel', {})}")
        print(f"  By Imprint: {stats.get('by_imprint', {})}")
        
    elif args.command == 'list':
        published_books = manager.get_published_books(args.imprint)
        print(f"📚 Published Books ({len(published_books)}):")
        for book in published_books:
            channels = ', '.join(book['distribution_channels'])
            packaged = "📦" if book.get('assets_packaged') else "📋"
            print(f"  {packaged} {book['title']} (ISBN: {book['isbn']}) - {channels}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()