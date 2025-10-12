# /src/codexes/modules/distribution/bookland_barcode_generator.py
# version 2.3.0
import logging
import tempfile
import argparse
import subprocess
from pathlib import Path
from typing import Optional

import treepoem

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

        cleaned_isbn = isbn_str.replace('.0', '').replace('-', '').strip()
        if len(cleaned_isbn) == 13 and cleaned_isbn.isdigit():
            return cleaned_isbn

        logger.error(f"Invalid ISBN format: '{isbn_str}'. Expected a 13-digit number.")
        return None

    def generate(self, isbn: str, price_code: str = "90000") -> Optional[Path]:
        """
        Generates and saves a composite Bookland EAN barcode image.

        The generated image includes both the EAN-13 barcode from the ISBN
        and the 5-digit supplemental price code.

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
            # Get the barcode as vector PostScript data from treepoem.
            barcode_ps_data = treepoem.get_data(
                barcode_type='ean13',
                data=code_with_supplemental,
                options={'includetext': True}  # Ensure human-readable text is included
            )

            # Use Ghostscript to render the PostScript to a high-DPI PNG.
            # This is superior to upscaling a low-resolution raster image.
            target_dpi = 600

            # -sDEVICE=pnggray: Creates an 8-bit grayscale PNG (like 'L' mode).
            # -dTextAlphaBits=4, -dGraphicsAlphaBits=4: Enable anti-aliasing for smooth text/lines.
            # -r<dpi>: Set the output resolution.
            # -sOutputFile=<path>: The output file.
            # -: Read from stdin.
            gs_command = [
                "gs",
                "-sDEVICE=pnggray",
                "-dTextAlphaBits=4",
                "-dGraphicsAlphaBits=4",
                f"-r{target_dpi}",
                f"-sOutputFile={barcode_path}",
                "-"
            ]

            # Execute Ghostscript, piping the PostScript data to its stdin.
            process = subprocess.run(
                gs_command,
                input=barcode_ps_data,
                capture_output=True,
                check=False  # We check the return code manually.
            )

            if process.returncode != 0:
                logger.error(f"Ghostscript failed to render barcode. Return code: {process.returncode}")
                logger.error(f"Ghostscript stderr: {process.stderr.decode('utf-8', errors='ignore')}")
                return None

            if barcode_path.exists() and barcode_path.stat().st_size > 0:
                logger.info(f"✅ Successfully generated Bookland EAN barcode with treepoem/Ghostscript: {barcode_path}")
                return barcode_path
            else:
                logger.error("Barcode file was not created by Ghostscript, despite no exception.")
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