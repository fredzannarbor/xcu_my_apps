# generate_dot_grid.py

import argparse
import logging
from PIL import Image, ImageDraw
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_dot_grid_image(
        output_path: Path,
        page_width_in: float,
        page_height_in: float,
        margin_in: float,
        dpi: int,
        spacing_mm: float,
        opacity: float,
        dot_diameter_px: int,
):
    """
    Generates a PNG image of a dot grid that fits within a specified text block.

    Args:
        output_path (Path): The path to save the output PNG file.
        page_width_in (float): The total width of the paper in inches.
        page_height_in (float): The total height of the paper in inches.
        margin_in (float): The margin size in inches on all sides.
        dpi (int): The resolution of the image in dots per inch.
        spacing_mm (float): The distance between dots in millimeters.
        opacity (float): The opacity of the dots (0.0 to 1.0).
        dot_diameter_px (int): The diameter of each dot in pixels.
    """
    try:
        # --- 1. Calculate Dimensions in Pixels ---
        text_area_width_in = page_width_in - (2 * margin_in)
        text_area_height_in = page_height_in - (2 * margin_in)

        img_width_px = int(text_area_width_in * dpi)
        img_height_px = int(text_area_height_in * dpi)

        # Convert dot spacing from mm to pixels
        spacing_in = spacing_mm / 25.4  # 1 inch = 25.4 mm
        spacing_px = int(spacing_in * dpi)

        logger.info(f"Image dimensions: {img_width_px}px x {img_height_px}px at {dpi} DPI")
        logger.info(f"Dot spacing: {spacing_mm}mm -> {spacing_px}px")

        # --- 2. Setup Image and Drawing Context ---
        # Create a transparent RGBA image
        image = Image.new("RGBA", (img_width_px, img_height_px), (255, 255, 255, 0))
        draw = ImageDraw.Draw(image)

        # --- 3. Configure Dot Appearance ---
        alpha = int(255 * opacity)
        dot_color = (0, 0, 0, alpha)  # Black with specified opacity
        dot_radius = dot_diameter_px / 2

        # --- 4. Draw the Grid ---
        logger.info("Drawing dot grid...")
        dot_count = 0
        for y in range(0, img_height_px, spacing_px):
            for x in range(0, img_width_px, spacing_px):
                # Define the bounding box for the ellipse
                left = x - dot_radius
                top = y - dot_radius
                right = x + dot_radius
                bottom = y + dot_radius
                draw.ellipse([left, top, right, bottom], fill=dot_color)
                dot_count += 1

        # --- 5. Save the Image ---
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # MODIFICATION: Explicitly set the DPI metadata in the PNG file.
        image.save(output_path, "PNG", dpi=(dpi, dpi))
        logger.info(f"✅ Successfully created dot grid with {dot_count} dots.")
        logger.info(f"   Saved to: {output_path}")

    except Exception as e:
        logger.critical(f"An unexpected error occurred: {e}", exc_info=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate a dot grid PNG image for use in LaTeX documents.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("templates/dotgrid.png"),
        help="Path for the output PNG file."
    )
    parser.add_argument("--page-width", type=float, default=6.0, help="Page width in inches.")
    parser.add_argument("--page-height", type=float, default=9.0, help="Page height in inches.")
    parser.add_argument("--margin", type=float, default=0.25, help="Margin size in inches.")
    parser.add_argument("--dpi", type=int, default=300, help="Resolution in dots per inch.")
    parser.add_argument("--spacing", type=float, default=5.0, help="Dot spacing in millimeters.")
    parser.add_argument("--opacity", type=float, default=1, help="Dot opacity (0.0 to 1.0).")
    parser.add_argument("--dot-diameter", type=int, default=2, help="Diameter of each dot in pixels.")

    args = parser.parse_args()

    create_dot_grid_image(
        output_path=args.output,
        page_width_in=args.page_width,
        page_height_in=args.page_height,
        margin_in=args.margin,
        dpi=args.dpi,
        spacing_mm=args.spacing,
        opacity=args.opacity,
        dot_diameter_px=args.dot_diameter,
    )
