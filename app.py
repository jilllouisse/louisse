from flask import Flask, render_template, request, redirect, url_for, flash
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class CropData:
    """Data class to represent crop information."""
    crop: str
    pH_min: float
    pH_max: float
    soil_type: str
    moisture_level: str
    duration_days: int
    harvest_date: Optional[str] = None
    crop_type: Optional[str] = None
    climate_zone: Optional[str] = None

class CropManager:
    """Manages crop data and operations."""
    def __init__(self, data_file: str):
        self.data_file = data_file
        self.crops: List[Dict[str, Any]] = self._load_crop_data()
        self.min_ph = min(crop['pH_min'] for crop in self.crops)
        self.max_ph = max(crop['pH_max'] for crop in self.crops)
        self.crop_types = self._get_unique_crop_types()
        self.climate_zones = self._get_unique_climate_zones()

    def _load_crop_data(self) -> List[Dict[str, Any]]:
        """Load crop data from JSON file."""
        try:
            with open(self.data_file) as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Crop data file {self.data_file} not found")
            return []
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in {self.data_file}")
            return []

    def _get_unique_crop_types(self) -> List[str]:
        """Get unique crop types from the data."""
        return sorted(list(set(crop.get('crop_type', '') for crop in self.crops if crop.get('crop_type'))))

    def _get_unique_climate_zones(self) -> List[str]:
        """Get unique climate zones from the data."""
        return sorted(list(set(crop.get('climate_zone', '') for crop in self.crops if crop.get('climate_zone'))))

    def find_matching_crops(self, ph: float, soil_type: str, moisture: str) -> List[Dict[str, Any]]:
        """Find crops matching the given criteria."""
        matching_crops = []
        for crop in self.crops:
            if (crop['pH_min'] <= ph <= crop['pH_max'] and
                crop['soil_type'].lower() == soil_type.lower() and
                crop['moisture_level'].lower() == moisture.lower()):
                harvest_date = datetime.today() + timedelta(days=crop['duration_days'])
                crop['harvest_date'] = harvest_date.strftime('%B %d, %Y')
                matching_crops.append(crop)
        return matching_crops

    def get_crop_rotation_schedule(self, selected_crops: List[str], duration_months: int = 12) -> List[Dict[str, Any]]:
        """Generate a crop rotation schedule for the selected crops."""
        schedule = []
        current_date = datetime.today()
        end_date = current_date + timedelta(days=30 * duration_months)
        
        while current_date < end_date:
            for crop_name in selected_crops:
                crop = next((c for c in self.crops if c['crop'] == crop_name), None)
                if crop:
                    planting_date = current_date
                    harvest_date = planting_date + timedelta(days=crop['duration_days'])
                    
                    if harvest_date > end_date:
                        break
                        
                    schedule.append({
                        'crop': crop['crop'],
                        'planting_date': planting_date.strftime('%B %d, %Y'),
                        'harvest_date': harvest_date.strftime('%B %d, %Y'),
                        'duration_days': crop['duration_days'],
                        'soil_type': crop['soil_type'],
                        'moisture_level': crop['moisture_level']
                    })
                    
                    current_date = harvest_date + timedelta(days=7)  # 7-day gap between crops
                    
        return schedule

def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.secret_key = 'your-secret-key-here'  # TODO: Move to environment variable
    
    # Initialize crop manager
    crop_manager = CropManager('negros_crops.json')

    @app.route('/', methods=['GET', 'POST'])
    def index():
        """Handle the main page requests."""
        crops = []
        rotation_schedule = []
        
        if request.method == 'POST':
            if 'exit' in request.form:
                return render_template('goodbye.html')

            try:
                ph = float(request.form['ph'])
                if ph < crop_manager.min_ph or ph > crop_manager.max_ph:
                    flash(f'Please enter a pH value between {crop_manager.min_ph} and {crop_manager.max_ph}', 'error')
                    return render_template('index.html', 
                                         crops=crops,
                                         rotation_schedule=rotation_schedule,
                                         min_ph=crop_manager.min_ph,
                                         max_ph=crop_manager.max_ph,
                                         crop_types=crop_manager.crop_types,
                                         climate_zones=crop_manager.climate_zones)
            except ValueError:
                flash('Please enter a valid pH value', 'error')
                return render_template('index.html',
                                     crops=crops,
                                     rotation_schedule=rotation_schedule,
                                     min_ph=crop_manager.min_ph,
                                     max_ph=crop_manager.max_ph,
                                     crop_types=crop_manager.crop_types,
                                     climate_zones=crop_manager.climate_zones)

            soil_type = request.form['soil_type']
            moisture = request.form['moisture']

            logger.info(f"User input - pH: {ph}, Soil: {soil_type}, Moisture: {moisture}")
            
            crops = crop_manager.find_matching_crops(ph, soil_type, moisture)
            
            if not crops:
                flash('No matching crops found for your input. Try adjusting your parameters.', 'info')
            else:
                # Generate rotation schedule for the first 3 matching crops
                selected_crops = [crop['crop'] for crop in crops[:3]]
                rotation_schedule = crop_manager.get_crop_rotation_schedule(selected_crops)

        return render_template('index.html',
                             crops=crops,
                             rotation_schedule=rotation_schedule,
                             min_ph=crop_manager.min_ph,
                             max_ph=crop_manager.max_ph,
                             crop_types=crop_manager.crop_types,
                             climate_zones=crop_manager.climate_zones)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)

