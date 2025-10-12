#!/usr/bin/env python3
"""
Font Manager - Downloads and manages Google Fonts for the Codexes Factory
"""

import os
import re
import requests
import zipfile
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging
import json
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)

class GoogleFontsManager:
    """Manages Google Fonts downloads and local storage"""

    def __init__(self, fonts_dir: str = "fonts"):
        """
        Initialize Google Fonts Manager

        Args:
            fonts_dir: Directory to store downloaded fonts
        """
        self.fonts_dir = Path(fonts_dir)
        self.fonts_dir.mkdir(exist_ok=True)

        # Google Fonts API endpoint
        self.api_key = os.getenv('GOOGLE_FONTS_API_KEY')
        self.api_url = "https://www.googleapis.com/webfonts/v1/webfonts"

        # Cache for font metadata
        self.fonts_cache = {}
        self.cache_file = self.fonts_dir / "fonts_cache.json"
        self._load_cache()

    def _load_cache(self):
        """Load fonts cache from file"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    self.fonts_cache = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load fonts cache: {e}")
                self.fonts_cache = {}

    def _save_cache(self):
        """Save fonts cache to file"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.fonts_cache, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save fonts cache: {e}")

    def search_google_fonts(self, font_name: str) -> Optional[Dict]:
        """
        Search for a font in Google Fonts

        Args:
            font_name: Name of the font to search for

        Returns:
            Font metadata if found, None otherwise
        """
        # Normalize font name for searching
        normalized_name = font_name.replace(" ", "+").lower()

        # Check cache first
        if normalized_name in self.fonts_cache:
            return self.fonts_cache[normalized_name]

        try:
            if self.api_key:
                # Use API if available
                params = {'key': self.api_key}
                response = requests.get(self.api_url, params=params, timeout=10)
                response.raise_for_status()

                fonts_data = response.json()
                for font in fonts_data.get('items', []):
                    if font['family'].lower().replace(" ", "+") == normalized_name:
                        self.fonts_cache[normalized_name] = font
                        self._save_cache()
                        return font
            else:
                # Fallback: construct likely Google Fonts URL
                logger.info(f"No Google Fonts API key, attempting direct download for {font_name}")
                constructed_font = {
                    'family': font_name,
                    'files': {
                        'regular': f"https://fonts.gstatic.com/s/{font_name.lower().replace(' ', '')}/v1/{font_name.lower().replace(' ', '')}-regular.ttf"
                    }
                }
                return constructed_font

        except requests.RequestException as e:
            logger.warning(f"Failed to search Google Fonts API: {e}")

        return None

    def download_google_font(self, font_name: str, variants: List[str] = None) -> bool:
        """
        Download a Google Font to local storage

        Args:
            font_name: Name of the font to download
            variants: List of font variants to download (e.g., ['regular', '700', 'italic'])

        Returns:
            True if download successful, False otherwise
        """
        if variants is None:
            variants = ['regular']

        # Create font directory
        font_dir = self.fonts_dir / font_name.replace(" ", "_")
        font_dir.mkdir(exist_ok=True)

        # Try to get font URLs through Google Fonts CSS API
        font_urls = self._get_font_urls_from_css(font_name, variants)

        if not font_urls:
            # Fallback: search for the font via API or construct URLs
            font_data = self.search_google_fonts(font_name)
            if font_data and 'files' in font_data:
                font_urls = {variant: url for variant, url in font_data['files'].items() if variant in variants}

        if not font_urls:
            logger.error(f"No font URLs found for '{font_name}'")
            return False

        # Download each variant
        success_count = 0
        for variant, font_url in font_urls.items():
            if variant in variants:
                success = self._download_font_file(font_url, font_dir, font_name, variant)
                if success:
                    success_count += 1

        if success_count > 0:
            logger.info(f"Successfully downloaded {success_count} variants of '{font_name}'")
            return True
        else:
            logger.error(f"Failed to download any variants of '{font_name}'")
            return False

    def _get_font_urls_from_css(self, font_name: str, variants: List[str]) -> Dict[str, str]:
        """
        Get font download URLs by parsing Google Fonts CSS

        Args:
            font_name: Name of the font
            variants: List of variants to get URLs for

        Returns:
            Dictionary mapping variants to download URLs
        """
        try:
            # Construct Google Fonts CSS URL
            family_param = font_name.replace(" ", "+")

            # Map variants to Google Fonts weight parameters
            variant_map = {
                'regular': '400',
                '700': '700',
                'italic': '400italic',
                '700italic': '700italic',
                'bold': '700',
                'light': '300',
                'thin': '100'
            }

            weights = []
            for variant in variants:
                if variant in variant_map:
                    weights.append(variant_map[variant])
                elif variant.isdigit():
                    weights.append(variant)

            if not weights:
                weights = ['400']  # Default to regular

            weight_param = ','.join(weights)
            css_url = f"https://fonts.googleapis.com/css?family={family_param}:{weight_param}"

            # Request the CSS
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(css_url, headers=headers, timeout=10)
            response.raise_for_status()

            # Parse CSS to extract font URLs
            font_urls = {}
            css_content = response.text

            # Look for @font-face rules and extract URLs
            import re

            # Parse CSS line by line to extract font info
            current_weight = None
            current_style = None
            current_url = None

            for line in css_content.split('\n'):
                line = line.strip()

                # Extract font-weight
                weight_match = re.search(r'font-weight:\s*(\d+);', line)
                if weight_match:
                    current_weight = weight_match.group(1)

                # Extract font-style
                style_match = re.search(r'font-style:\s*(\w+);', line)
                if style_match:
                    current_style = style_match.group(1)

                # Extract URL
                url_match = re.search(r'src:\s*url\(([^)]+)\)', line)
                if url_match:
                    current_url = url_match.group(1).strip('\'"')

                # When we have all three pieces, map to variant
                if current_weight and current_style and current_url:
                    # Map back to our variant names
                    if current_weight == '400' and current_style == 'normal':
                        variant = 'regular'
                    elif current_weight == '700' and current_style == 'normal':
                        variant = '700'
                    elif current_weight == '400' and current_style == 'italic':
                        variant = 'italic'
                    elif current_weight == '700' and current_style == 'italic':
                        variant = '700italic'
                    else:
                        variant = current_weight

                    if variant in variants:
                        font_urls[variant] = current_url

                    # Reset for next font-face rule
                    current_weight = None
                    current_style = None
                    current_url = None

            return font_urls

        except Exception as e:
            logger.warning(f"Failed to get font URLs from CSS: {e}")
            return {}

    def _download_font_file(self, url: str, font_dir: Path, font_name: str, variant: str) -> bool:
        """
        Download a single font file

        Args:
            url: URL of the font file
            font_dir: Directory to save the font
            font_name: Name of the font
            variant: Font variant (e.g., 'regular', '700')

        Returns:
            True if download successful, False otherwise
        """
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Determine file extension
            content_type = response.headers.get('content-type', '')
            if 'woff2' in content_type:
                ext = '.woff2'
            elif 'woff' in content_type:
                ext = '.woff'
            elif 'truetype' in content_type or 'ttf' in content_type:
                ext = '.ttf'
            elif 'opentype' in content_type or 'otf' in content_type:
                ext = '.otf'
            else:
                # Try to guess from URL
                if url.endswith('.woff2'):
                    ext = '.woff2'
                elif url.endswith('.woff'):
                    ext = '.woff'
                elif url.endswith('.ttf'):
                    ext = '.ttf'
                elif url.endswith('.otf'):
                    ext = '.otf'
                else:
                    ext = '.ttf'  # Default

            # Create filename
            safe_name = font_name.replace(" ", "_")
            filename = f"{safe_name}-{variant}{ext}"
            file_path = font_dir / filename

            # Save the font file
            with open(file_path, 'wb') as f:
                f.write(response.content)

            logger.info(f"Downloaded {font_name} {variant} to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to download font file from {url}: {e}")
            return False

    def get_local_fonts(self) -> List[str]:
        """
        Get list of locally downloaded fonts

        Returns:
            List of font names that are available locally
        """
        local_fonts = []

        if not self.fonts_dir.exists():
            return local_fonts

        for font_dir in self.fonts_dir.iterdir():
            if font_dir.is_dir() and font_dir.name != '__pycache__':
                # Check if directory contains font files
                font_files = list(font_dir.glob('*.ttf')) + list(font_dir.glob('*.otf')) + \
                           list(font_dir.glob('*.woff')) + list(font_dir.glob('*.woff2'))
                if font_files:
                    local_fonts.append(font_dir.name.replace("_", " "))

        return sorted(local_fonts)

    def is_font_available(self, font_name: str) -> bool:
        """
        Check if a font is available locally

        Args:
            font_name: Name of the font to check

        Returns:
            True if font is available locally, False otherwise
        """
        normalized_name = font_name.replace(" ", "_")
        font_dir = self.fonts_dir / normalized_name

        if not font_dir.exists():
            return False

        # Check for font files
        font_files = list(font_dir.glob('*.ttf')) + list(font_dir.glob('*.otf')) + \
                    list(font_dir.glob('*.woff')) + list(font_dir.glob('*.woff2'))

        return len(font_files) > 0

    def download_fonts_from_config(self, config: Dict) -> Dict[str, bool]:
        """
        Download fonts specified in an imprint configuration

        Args:
            config: Imprint configuration dictionary

        Returns:
            Dictionary mapping font names to download success status
        """
        results = {}
        fonts_to_download = set()

        # Extract fonts from configuration
        fonts_section = config.get('fonts', {})

        for font_type, font_spec in fonts_section.items():
            if isinstance(font_spec, dict):
                # New format with primary/fallback
                fallback_font = font_spec.get('fallback')
                fallback_source = font_spec.get('fallback_source', '').lower()

                if fallback_font and 'google' in fallback_source:
                    fonts_to_download.add(fallback_font)
            elif isinstance(font_spec, str):
                # Old format - assume it might be a Google Font
                fonts_to_download.add(font_spec)

        # Download each font
        for font_name in fonts_to_download:
            if not self.is_font_available(font_name):
                logger.info(f"Downloading Google Font: {font_name}")
                success = self.download_google_font(font_name, ['regular', '700', 'italic', '700italic'])
                results[font_name] = success
            else:
                logger.info(f"Font '{font_name}' already available locally")
                results[font_name] = True

        return results

def download_fonts_for_imprint(config_path: str) -> bool:
    """
    Utility function to download fonts for a specific imprint configuration

    Args:
        config_path: Path to the imprint configuration file

    Returns:
        True if all fonts downloaded successfully, False otherwise
    """
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)

        font_manager = GoogleFontsManager()
        results = font_manager.download_fonts_from_config(config)

        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)

        if total_count == 0:
            logger.info("No Google Fonts to download")
            return True
        elif success_count == total_count:
            logger.info(f"Successfully downloaded all {total_count} Google Fonts")
            return True
        else:
            logger.warning(f"Downloaded {success_count}/{total_count} Google Fonts")
            return False

    except Exception as e:
        logger.error(f"Failed to process imprint configuration: {e}")
        return False

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Google Fonts Manager")
    parser.add_argument("--download", help="Download a specific Google Font")
    parser.add_argument("--list", action="store_true", help="List locally available fonts")
    parser.add_argument("--config", help="Download fonts from imprint configuration")

    args = parser.parse_args()

    font_manager = GoogleFontsManager()

    if args.download:
        success = font_manager.download_google_font(args.download)
        print(f"Download {'successful' if success else 'failed'}")
    elif args.list:
        fonts = font_manager.get_local_fonts()
        print("Locally available fonts:")
        for font in fonts:
            print(f"  - {font}")
    elif args.config:
        success = download_fonts_for_imprint(args.config)
        print(f"Font download {'successful' if success else 'failed'}")
    else:
        parser.print_help()