# /src/codexes/modules/covers/treepoem_barcode_generator.py
# version 1.0.0
import logging
import tempfile
import argparse
from pathlib import Path
from typing import Optional

import treepoem
from PIL import Image, ImageDraw, ImageFont

# Configure a logger for standalone use
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BooklandBarcodeGenerator:
    """
    Generates a Bookland EAN (EAN-13 + 5-digit supplemental) barcode image.
    This version uses the `treepoem` library, which wraps the robust BW-IPP backend.

    This class encapsulates the logic for creating a composite barcode image
    from an ISBN-13 and an optional 5-digit price code, which is standard
    for books sold at retail.
    """

    def __init__(self, output_dir: Path):
        """
        Initializes the generator.

        Args:
            output_dir: The directory where barcode images will be saved.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _clean_isbn(self, isbn_str: str) -> Optional[str]:
        """Cleans and validates a 13-digit ISBN string."""
        if not isinstance(isbn_str, str):
            logger.error(f"Invalid ISBN type: {type(isbn_str)}. Must be a string.")
            return None

        # Handle common invalid values
        if isbn_str.lower() in ['nan', 'none', '', 'null']:
            logger.error(f"Invalid ISBN value: '{isbn_str}'. Cannot be empty or null.")
            return None

        cleaned_isbn = isbn_str.replace('.0', '').replace('-', '').strip()
        if len(cleaned_isbn) == 13 and cleaned_isbn.isdigit():
            return cleaned_isbn

        logger.error(f"Invalid ISBN format: '{isbn_str}'. Expected a 13-digit number.")
        return None

    def _format_isbn_with_hyphens(self, isbn_str: str) -> str:
        """
        Formats an ISBN-13 with standard hyphenation pattern.
        Basic formatting - for more sophisticated hyphenation, use ISBNFormatter.
        """
        # Basic ISBN-13 hyphenation: 978-X-XXXXXX-XX-X
        if len(isbn_str) == 13 and isbn_str.startswith(('978', '979')):
            return f"{isbn_str[:3]}-{isbn_str[3]}-{isbn_str[4:10]}-{isbn_str[10:12]}-{isbn_str[12]}"
        return isbn_str

    def generate(self, isbn: str, price_code: str = "90000") -> Optional[Path]:
        """
        Generates and saves a composite Bookland EAN barcode image with ISBN text.

        The generated image includes both the EAN-13 barcode from the ISBN
        and the 5-digit supplemental price code, with the formatted ISBN text
        displayed above the barcode with 0.25" white margins on all sides.

        Args:
            isbn: The 13-digit ISBN for the book.
            price_code: The 5-digit supplemental price code. Defaults to "90000",
                        which indicates no suggested retail price in the US.

        Returns:
            The Path to the generated PNG image file, or None if generation failed.
        """
        cleaned_isbn = self._clean_isbn(isbn)
        if not cleaned_isbn:
            return None

        if not (isinstance(price_code, str) and len(price_code) == 5 and price_code.isdigit()):
            logger.error(f"Invalid price code: '{price_code}'. Must be a 5-digit string.")
            return None

        # A Bookland EAN barcode is an EAN-13 with a 5-digit supplemental.
        # The `treepoem` library takes this in the format "EAN13 SUPPLEMENTAL".
        code_with_supplemental = f"{cleaned_isbn} {price_code}"

        # The filename for the output image.
        barcode_filename = f"barcode_{cleaned_isbn}_{price_code}.png"
        barcode_path = self.output_dir / barcode_filename

        try:
            # Generate the barcode image using treepoem. It returns a Pillow image object.
            # The 'ean13' type supports a supplemental code when separated by a space.
            barcode_image = treepoem.generate_barcode(
                barcode_type='ean13',
                data=code_with_supplemental,
                options={'includetext': True}  # Ensure human-readable text is included
            )

            # Convert to black and white for crisp contrast
            barcode_image = barcode_image.convert('1')

            # Format the ISBN with hyphens for display
            formatted_isbn = self._format_isbn_with_hyphens(cleaned_isbn)
            isbn_text = f"ISBN {formatted_isbn}"

            # Create a new image with white margins and ISBN text
            # Add 0.25" (18 points at 72 DPI) margins on all sides
            # Add space for ISBN text at the top
            margin = 18  # 0.25" at 72 DPI
            text_height = 20  # Space for ISBN text

            new_width = barcode_image.width + (2 * margin)
            new_height = barcode_image.height + (2 * margin) + text_height

            # Create new white image
            final_image = Image.new('RGB', (new_width, new_height), 'white')

            # Paste barcode centered with margins
            barcode_x = margin
            barcode_y = margin + text_height
            final_image.paste(barcode_image, (barcode_x, barcode_y))

            # Add ISBN text at the top
            draw = ImageDraw.Draw(final_image)

            # Try to use a system font, fall back to default if not available
            try:
                # Match font size to be closer to the barcode's own text
                font = ImageFont.truetype("Arial.ttf", 20)
            except (IOError, OSError):
                try:
                    font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 20)
                except (IOError, OSError):
                    font = ImageFont.load_default()

            # Position text flush left69
            text_x = margin
            text_y = margin // 2

            # Draw the ISBN text in black
            draw.text((text_x, text_y), isbn_text, fill='black', font=font)

            # Convert final image to 1-bit for crisp black and white output
            final_image = final_image.convert('1')

            # Save the final composite image
            final_image.save(barcode_path)

            if barcode_path.exists() and barcode_path.stat().st_size > 0:
                logger.info(f"✅ Successfully generated Bookland EAN barcode with ISBN text: {barcode_path}")
                return barcode_path
            else:
                logger.error("Barcode file was not created or is empty, despite no exception.")
                return None

        except Exception as e:
            logger.error(f"Failed to generate barcode for code '{code_with_supplemental}': {e}", exc_info=True)
            return None


def main():
    """A command-line interface for testing the BooklandBarcodeGenerator."""
    parser = argparse.ArgumentParser(
        description="Generate a Bookland EAN (ISBN-13 + 5) barcode image.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("isbn", type=str, help="The 13-digit ISBN (hyphens are optional).")
    parser.add_argument("--price", type=str, default="90000",
                        help="The 5-digit supplemental price code (e.g., 51999 for $19.99). Default: 90000.")
    parser.add_argument("--output-dir", type=str,
                        help="Directory to save the barcode image. Defaults to a temporary directory.")

    args = parser.parse_args()

    output_path = Path(args.output_dir) if args.output_dir else Path(tempfile.mkdtemp(prefix="barcodes_"))
    if not args.output_dir:
        print(f"No output directory specified. Using temporary directory: {output_path}")

    generator = BooklandBarcodeGenerator(output_dir=output_path)
    image_path = generator.generate(isbn=args.isbn, price_code=args.price)

    if image_path:
        print(f"\n--- Success! ---\nBarcode image created at: {image_path.resolve()}")
    else:
        print("\n--- Failure ---\nBarcode generation failed. Check log messages for details.")


if __name__ == "__main__":
    main()