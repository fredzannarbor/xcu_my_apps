import numpy as np
import rasterio
from datetime import datetime
import pandas as pd
from typing import List, Dict, Tuple
import cv2
import nltk
from nltk.tokenize import sent_tokenize
import torch
import torch.nn.functional as F
from huggingface_hub import hf_hub_download
from transformers import AutoImageProcessor, AutoModelForSemanticSegmentation
import ee
import requests
import io
import logging
import argparse
import os
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('global_human_activity.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

nltk.download('punkt', quiet=True)


class ActivityAnalyzer:
    """
    A class to handle the initialization and inference of the segmentation model
    using the Hugging Face transformers library.
    """

    def __init__(self):
        logger.info("Initializing new segmentation model (transformers-based)...")
        try:
            model_name = "nielsr/segformer-b0-finetuned-landcover"
            self.processor = AutoImageProcessor.from_pretrained(model_name)
            self.model = AutoModelForSemanticSegmentation.from_pretrained(model_name)

            self.device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
            self.model.to(self.device)
            logger.info(f"Using device: {self.device}")
            logger.info("Segmentation model initialized successfully.")

            # Define the mapping from the new model's labels to our target categories
            model_labels = self.model.config.id2label
            label_map = {
                'agriculture': ['AnnualCrop', 'Pasture', 'PermanentCrop'],
                'natural': ['Forest', 'HerbaceousVegetation'],
                'urban': ['Highway', 'Industrial', 'Residential'],
                'other': ['River', 'SeaLake']
            }
            # Create a reverse map from the model's label ID to our category name
            self.id_to_category = {}
            for category, labels in label_map.items():
                for label in labels:
                    for id_val, name in model_labels.items():
                        if name == label:
                            self.id_to_category[id_val] = category
                            break
        except Exception as e:
            logger.error(f"Failed to initialize transformers model: {e}")
            self.model = None
            self.processor = None

    def classify_human_activity(self, image: np.ndarray) -> Dict[str, float]:
        """Analyzes an image patch using a transformers-based segmentation model."""
        if self.model is None:
            logger.error("Model is not initialized, cannot perform classification.")
            return self._default_probs()

        logger.info("Classifying human activity with new model")
        try:
            if image.shape[-1] != 3:
                raise ValueError('Input image must have 3 bands (RGB) for this model.')

            inputs = self.processor(images=image, return_tensors="pt").to(self.device)

            with torch.no_grad():
                outputs = self.model(**inputs)

            logits = outputs.logits
            # Upsample logits to the original image size for pixel-wise classification
            upsampled_logits = F.interpolate(
                logits, size=image.shape[:-1], mode="bilinear", align_corners=False
            )
            pred_seg = upsampled_logits.argmax(dim=1)[0]

            # Calculate probabilities for our target categories
            category_counts = {cat: 0 for cat in self.id_to_category.values()}
            total_pixels = pred_seg.nelement()

            # Efficiently count pixels for each category
            for pixel_id, category in self.id_to_category.items():
                count = (pred_seg == pixel_id).sum().item()
                category_counts[category] += count

            output_probs = {cat: count / total_pixels for cat, count in category_counts.items()}

            # Add the 'deforestation' key to maintain data structure, though it's no longer detected
            output_probs['deforestation'] = 0.0

            logger.info(f"Classification complete: {output_probs}")
            return output_probs
        except Exception as e:
            logger.error(f"Error in classify_human_activity: {e}")
            return self._default_probs()

    @staticmethod
    def _default_probs() -> Dict[str, float]:
        """Returns a default, uniform probability distribution for the target categories."""
        return {'urban': 0.25, 'agriculture': 0.25, 'natural': 0.25, 'other': 0.25, 'deforestation': 0.0}


def fetch_hls_data(aoi: ee.Geometry, start_date: str, end_date: str) -> np.ndarray:
    """Fetch HLS data from GEE, selecting only RGB bands for the new model."""
    logger.info(f"Fetching HLS data for {start_date} to {end_date}")
    try:
        collection = (ee.ImageCollection('LANDSAT/HLSL30')
                      .filterBounds(aoi)
                      .filterDate(start_date, end_date)
                      .filter(ee.Filter.lt('CLOUD_COVERAGE', 20))
                      .median()
                      .select(['B4', 'B3', 'B2']))  # Red, Green, Blue for RGB

        image = collection.clip(aoi)
        region = aoi.bounds().getInfo()['coordinates']
        url = image.getDownloadURL({
            'scale': 30,
            'region': region,
            'format': 'NPY'
        })
        response = requests.get(url)
        response.raise_for_status()
        data = np.load(io.BytesIO(response.content))

        # Stack the bands into an RGB image
        bands = [data[band_name] for band_name in ['B4', 'B3', 'B2']]
        img = np.stack(bands, axis=-1)
        logger.info(f"Successfully fetched HLS data: shape {img.shape}")
        return img
    except Exception as e:
        logger.error(f"Error fetching HLS data: {e}")
        return np.zeros((224, 224, 3))


def generate_narrative(activity_history: List[Dict]) -> str:
    """Generates a textual narrative from a time-series of activity data."""
    logger.info("Generating narrative")
    narrative = 'This area shows a history of human activity: '
    for entry in activity_history:
        date = entry['date'].strftime('%Y-%m')
        activities = entry['activities']
        dominant = max(activities, key=activities.get)
        narrative += f'In {date}, the dominant activity was {dominant} ({activities[dominant]:.2%}). '
    return narrative


def process_grid_cell(analyzer: ActivityAnalyzer, images: List[Tuple[datetime, np.ndarray]], cell_id: str) -> Dict:
    """Analyzes time-series imagery for a grid cell and returns its activity history."""
    logger.info(f"Processing grid cell: {cell_id}")
    history = []
    for timestamp, image in images:
        activities = analyzer.classify_human_activity(image)
        history.append({'date': timestamp, 'activities': activities, 'cell_id': cell_id})
    narrative = generate_narrative(history)
    return {'cell_id': cell_id, 'history': history, 'narrative': narrative}


def aggregate_to_global(cell_histories: List[Dict]) -> str:
    """Aggregates individual cell histories into a global narrative."""
    logger.info("Aggregating global narrative")
    global_narrative = 'Global Human Activity History:\n\n'
    activity_trends = {}
    for cell in cell_histories:
        for entry in cell['history']:
            date = entry['date'].strftime('%Y')
            for activity, prob in entry['activities'].items():
                if activity not in activity_trends:
                    activity_trends[activity] = {}
                if date not in activity_trends[activity]:
                    activity_trends[activity][date] = []
                activity_trends[activity][date].append(prob)

    for activity in sorted(activity_trends.keys()):
        if activity == 'deforestation': continue  # Don't report on the zero-value class
        global_narrative += f'{activity.capitalize()} Trends:\n'
        for date in sorted(activity_trends[activity].keys()):
            avg_prob = np.mean(activity_trends[activity][date])
            global_narrative += f'  In {date}, {activity} activity averaged {avg_prob:.2%} across observed regions.\n'
    return global_narrative


def main(args):
    """Main function to process HLS data and generate narratives."""
    logger.info("Starting main execution")

    # Initialize GEE, prompting for authentication if needed.
    try:
        ee.Initialize()
        logger.info("Google Earth Engine initialized.")
    except ee.EEException:
        logger.warning("GEE not initialized. Attempting authentication.")
        ee.Authenticate()
        ee.Initialize()
        logger.info("Google Earth Engine initialized after authentication.")
    except Exception as e:
        logger.error(f"Failed to initialize GEE: {e}")
        return

    # Initialize the model analyzer once
    analyzer = ActivityAnalyzer()
    if not analyzer.model:
        logger.error("Exiting due to model initialization failure.")
        return

    # Define AOI from CLI arguments
    aoi = ee.Geometry.Rectangle([args.min_lon, args.min_lat, args.max_lon, args.max_lat])
    logger.info(f"AOI defined: {aoi.getInfo()['coordinates']}")

    # Parse years and create date ranges
    years = [int(y) for y in args.years.split(',')]
    dates = [(f'{y}-01-01', f'{y}-12-31') for y in years]

    # Fetch HLS data for each time period for the single AOI
    logger.info("Fetching time-series data for the AOI...")
    time_series_images = [(datetime.strptime(start, '%Y-%m-%d'), fetch_hls_data(aoi, start, end)) for start, end in
                          dates]

    # Process the single AOI as one "cell"
    cell_history = process_grid_cell(analyzer, time_series_images, cell_id="AOI_1")
    cell_histories = [cell_history]

    global_narrative = aggregate_to_global(cell_histories)

    # Save results to output file
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        for cell in cell_histories:
            f.write(f'Cell {cell["cell_id"]} Narrative:\n{cell["narrative"]}\n\n')
        f.write(global_narrative)
    logger.info(f"Results saved to {args.output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze human activity from HLS data")
    parser.add_argument('--min-lon', type=float, required=True, help='Minimum longitude of AOI')
    parser.add_argument('--min-lat', type=float, required=True, help='Minimum latitude of AOI')
    parser.add_argument('--max-lon', type=float, required=True, help='Maximum longitude of AOI')
    parser.add_argument('--max-lat', type=float, required=True, help='Maximum latitude of AOI')
    parser.add_argument('--years', type=str, required=True, help='Comma-separated list of years (e.g., 2013,2015,2025)')
    parser.add_argument('--output', type=str, default='output/narrative.txt', help='Output file for narratives')

    args = parser.parse_args()
    main(args)
