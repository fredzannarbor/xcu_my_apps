import numpy as np
import rasterio
from datetime import datetime
import pandas as pd
from typing import List, Dict, Tuple
import cv2
import nltk
from nltk.tokenize import sent_tokenize
import torch
from huggingface_hub import hf_hub_download
from mmseg.apis import init_segmentor, inference_segmentor
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

# Define a direct mapping from the model's output index to the desired final label
MODEL_OUTPUT_TO_LABEL = {
    0: 'urban',
    1: 'agriculture',
    2: 'natural',  # Original Prithvi label was 'forest'
    3: 'other',  # Original Prithvi label was 'water'
    4: 'deforestation'  # Original Prithvi label was 'barren'
}


class ActivityAnalyzer:
    """
    A class to handle the initialization and inference of the segmentation model.
    This ensures the model is loaded from Hugging Face Hub only once.
    """

    def __init__(self):
        logger.info("Initializing segmentation model...")
        try:
            config_file = hf_hub_download(
                repo_id='ibm-nasa-geospatial/Prithvi-100M-multi-temporal-crop-classification',
                filename='config.py'
            )
            checkpoint_file = hf_hub_download(
                repo_id='ibm-nasa-geospatial/Prithvi-100M',
                filename='checkpoint.pth'
            )

            self.device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
            logger.info(f"Using device: {self.device}")
            self.model = init_segmentor(config_file, checkpoint_file, device=self.device)
            logger.info("Segmentation model initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize model: {e}")
            self.model = None

    def classify_human_activity(self, image: np.ndarray) -> Dict[str, float]:
        """Analyzes an image patch using the pre-initialized NASA HLS Geospatial Foundation Model."""
        if self.model is None:
            logger.error("Model is not initialized, cannot perform classification.")
            return self._default_probs()

        logger.info("Classifying human activity")
        try:
            if image.shape[-1] != 6:
                raise ValueError('Input image must have 6 bands (B2, B3, B4, B5, B6, B7)')

            image = cv2.resize(image, (224, 224), interpolation=cv2.INTER_LINEAR)
            image = image / 10000.0
            image_tensor = np.transpose(image, (2, 0, 1))
            image_tensor = np.expand_dims(image_tensor, axis=0)
            image_tensor = np.expand_dims(image_tensor, axis=2)
            image_tensor = torch.from_numpy(image_tensor).float().to(self.device)

            result = inference_segmentor(self.model, image_tensor)
            pred = result[0]
            class_counts = np.bincount(pred.flatten(), minlength=len(MODEL_OUTPUT_TO_LABEL))
            total_pixels = pred.size
            class_probs = class_counts / total_pixels

            # Build the output dictionary programmatically for clarity and robustness.
            output_probs = {
                label: class_probs[index] for index, label in MODEL_OUTPUT_TO_LABEL.items()
            }

            total = sum(output_probs.values())
            if total > 0:
                output_probs = {k: v / total for k, v in output_probs.items()}
            else:
                output_probs = self._default_probs()

            logger.info(f"Classification complete: {output_probs}")
            return output_probs
        except Exception as e:
            logger.error(f"Error in classify_human_activity: {e}")
            return self._default_probs()

    @staticmethod
    def _default_probs() -> Dict[str, float]:
        """Returns a default, uniform probability distribution."""
        return {label: 1.0 / len(MODEL_OUTPUT_TO_LABEL) for label in MODEL_OUTPUT_TO_LABEL.values()}


def fetch_hls_data(aoi: ee.Geometry, start_date: str, end_date: str) -> np.ndarray:
    """Fetch HLS data from GEE for the given AOI and time period."""
    logger.info(f"Fetching HLS data for {start_date} to {end_date}")
    try:
        collection = (ee.ImageCollection('LANDSAT/HLSL30')
                      .filterBounds(aoi)
                      .filterDate(start_date, end_date)
                      .filter(ee.Filter.lt('CLOUD_COVERAGE', 20))
                      .median()
                      .select(['B2', 'B3', 'B4', 'B5', 'B6', 'B7']))  # Blue, Green, Red, NIR, SWIR1, SWIR2

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

        bands = [data[f'B{i}'] for i in [2, 3, 4, 5, 6, 7]]
        img = np.stack(bands, axis=-1)
        logger.info(f"Successfully fetched HLS data: shape {img.shape}")
        return img
    except Exception as e:
        logger.error(f"Error fetching HLS data: {e}")
        return np.zeros((224, 224, 6))


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
        global_narrative += f'{activity.capitalize()} Trends:\n'
        for date in sorted(activity_trends[activity].keys()):
            avg_prob = np.mean(activity_trends[activity][date])
            global_narrative += f'  In {date}, {activity} activity averaged {avg_prob:.2%} across observed regions.\n'
    return global_narrative


def main(args):
    """Main function to process HLS data and generate narratives."""
    logger.info("Starting main execution")

    # Initialize GEE
    try:
        # ee.Authenticate() # Uncomment if you need to authenticate
        ee.Initialize()
        logger.info("Google Earth Engine initialized")
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
