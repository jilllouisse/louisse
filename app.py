from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import os

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

    def find_matching_crops(self, ph: float, soil_type: str, moisture: str, crop_type: str = '') -> List[Dict[str, Any]]:
        """Find crops matching the given criteria."""
        matching_crops = []
        logger.info(f"Searching for crops with pH: {ph}, soil: {soil_type}, moisture: {moisture}, type: {crop_type}")
        
        for crop in self.crops:
            # Convert all strings to lowercase for case-insensitive comparison
            crop_soil = crop['soil_type'].lower()
            crop_moisture = crop['moisture_level'].lower()
            crop_type_lower = crop.get('crop_type', '').lower()
            input_soil = soil_type.lower()
            input_moisture = moisture.lower()
            input_crop_type = crop_type.lower() if crop_type else ''
            
            # Check pH range
            ph_match = crop['pH_min'] <= ph <= crop['pH_max']
            
            # Check soil type (more flexible matching)
            soil_match = (crop_soil == input_soil or 
                         (crop_soil == 'loamy' and input_soil in ['sandy', 'clay']) or
                         (input_soil == 'loamy' and crop_soil in ['sandy', 'clay']))
            
            # Check moisture level (more flexible matching)
            moisture_match = (crop_moisture == input_moisture or
                            (crop_moisture == 'medium' and input_moisture in ['high', 'low']) or
                            (input_moisture == 'medium' and crop_moisture in ['high', 'low']))
            
            # Check crop type if specified
            type_match = not input_crop_type or crop_type_lower == input_crop_type
            
            if ph_match and soil_match and moisture_match and type_match:
                # Calculate harvest date
                harvest_date = datetime.today() + timedelta(days=crop['duration_days'])
                crop['harvest_date'] = harvest_date.strftime('%B %d, %Y')
                
                # Add detailed information
                crop['description'] = self._get_crop_description(crop)
                crop['benefits'] = self._get_crop_benefits(crop)
                crop['growing_tips'] = self._get_growing_tips(crop)
                
                matching_crops.append(crop)
                logger.info(f"Found matching crop: {crop['crop']}")
        
        logger.info(f"Total matching crops found: {len(matching_crops)}")
        return matching_crops

    def _get_crop_description(self, crop: Dict[str, Any]) -> str:
        """Generate a detailed description for the crop."""
        crop_type = crop.get('crop_type', 'general')
        duration = crop['duration_days']
        yield_info = crop.get('yield_per_hectare', 'N/A')
        planting_season = crop.get('planting_season', ['Year-round'])
        
        descriptions = {
            'fruit': f"A tropical fruit crop that takes {duration} days to mature. Best planted during {', '.join(planting_season)}. Expected yield: {yield_info}. This crop is well-suited for the Philippine climate and can provide long-term benefits.",
            'vegetable': f"A vegetable crop with a growing period of {duration} days. Ideal planting season: {', '.join(planting_season)}. Expected yield: {yield_info}. Perfect for home gardens and commercial farming.",
            'root': f"A root crop that matures in {duration} days. Best planted during {', '.join(planting_season)}. Expected yield: {yield_info}. Excellent for improving soil structure and food security.",
            'leafy': f"A leafy vegetable that can be harvested in {duration} days. Planting season: {', '.join(planting_season)}. Expected yield: {yield_info}. Great for continuous harvesting and high nutritional value.",
            'grain': f"A grain crop with a growing period of {duration} days. Planting season: {', '.join(planting_season)}. Expected yield: {yield_info}. Essential for food security and traditional farming.",
            'industrial': f"An industrial crop that takes {duration} days to mature. Planting season: {', '.join(planting_season)}. Expected yield: {yield_info}. Good for commercial farming and export.",
            'legume': f"A legume crop that matures in {duration} days. Planting season: {', '.join(planting_season)}. Expected yield: {yield_info}. Excellent for soil improvement and protein production."
        }
        
        return descriptions.get(crop_type, f"A crop that takes {duration} days to mature. Planting season: {', '.join(planting_season)}. Expected yield: {yield_info}.")

    def _get_crop_benefits(self, crop: Dict[str, Any]) -> List[str]:
        """Generate benefits for the crop."""
        benefits = []
        
        # Add benefits based on crop type
        crop_type = crop.get('crop_type', '')
        if crop_type == 'fruit':
            benefits.extend([
                'High market value and export potential',
                'Good for home gardens and commercial farming',
                'Multiple harvests possible',
                'Provides shade and wind protection',
                'Long-term investment with good returns'
            ])
        elif crop_type == 'vegetable':
            benefits.extend([
                'Quick growing and early harvest',
                'High nutritional value',
                'Good for intercropping',
                'Multiple harvests possible',
                'Adaptable to various growing conditions'
            ])
        elif crop_type == 'root':
            benefits.extend([
                'Improves soil structure and aeration',
                'Drought resistant and hardy',
                'Good for food security',
                'Long storage life',
                'High yield potential'
            ])
        elif crop_type == 'leafy':
            benefits.extend([
                'Quick growing and early harvest',
                'High nutritional value',
                'Multiple harvests possible',
                'Good for continuous production',
                'Adaptable to various growing conditions'
            ])
        elif crop_type == 'grain':
            benefits.extend([
                'Essential for food security',
                'Good income generation',
                'Cultural and traditional importance',
                'Multiple uses (food, feed, industry)',
                'High yield potential'
            ])
        elif crop_type == 'industrial':
            benefits.extend([
                'High market value',
                'Long shelf life',
                'Good for export',
                'Industrial applications',
                'Stable market demand'
            ])
        elif crop_type == 'legume':
            benefits.extend([
                'Improves soil fertility naturally',
                'High protein content',
                'Good for crop rotation',
                'Reduces need for chemical fertilizers',
                'Multiple uses (food, feed, green manure)'
            ])
            
        # Add benefits based on pest resistance
        pest_resistance = crop.get('pest_resistance', '')
        if pest_resistance == 'high':
            benefits.append('High pest resistance - reduces need for pesticides')
        elif pest_resistance == 'moderate':
            benefits.append('Moderate pest resistance - requires basic pest management')
            
        # Add benefits based on climate zone
        climate_zone = crop.get('climate_zone', '')
        if climate_zone == 'tropical':
            benefits.append('Well-adapted to Philippine climate')
            
        return benefits

    def _get_growing_tips(self, crop: Dict[str, Any]) -> List[str]:
        """Generate growing tips for the crop."""
        tips = []
        
        # Add spacing tips
        spacing = crop.get('spacing', {})
        if spacing:
            plant_spacing = spacing.get('between_plants', '')
            row_spacing = spacing.get('between_rows', '')
            if plant_spacing and row_spacing:
                tips.append(f"Plant spacing: {plant_spacing} between plants, {row_spacing} between rows")
        
        # Add fertilizer tips
        fertilizer = crop.get('fertilizer_needs', {})
        if fertilizer:
            n_level = fertilizer.get('nitrogen', '')
            p_level = fertilizer.get('phosphorus', '')
            k_level = fertilizer.get('potassium', '')
            if n_level and p_level and k_level:
                tips.append(f"Fertilizer needs: N-{n_level}, P-{p_level}, K-{k_level}")
                if n_level == 'high':
                    tips.append("Apply nitrogen-rich fertilizer during vegetative growth")
                if p_level == 'high':
                    tips.append("Ensure good phosphorus levels for root development")
                if k_level == 'high':
                    tips.append("Maintain potassium levels for fruit/vegetable quality")
        
        # Add sunlight tips
        sunlight = crop.get('sunlight', '')
        if sunlight:
            tips.append(f"Sunlight requirement: {sunlight}")
            if sunlight == 'full':
                tips.append("Plant in open areas with maximum sunlight exposure")
            elif sunlight == 'partial':
                tips.append("Provide some shade during hottest part of the day")
            
        # Add water requirement tips
        water = crop.get('water_requirement', '')
        if water:
            tips.append(f"Water requirement: {water}")
            if 'mm/season' in water:
                tips.append("Ensure consistent moisture throughout growing season")
            elif 'mm/year' in water:
                tips.append("Maintain regular watering schedule throughout the year")
                
        # Add planting season tips
        planting_season = crop.get('planting_season', [])
        if planting_season and planting_season[0] != 'Year-round':
            tips.append(f"Best planting season: {', '.join(planting_season)}")
            
        # Add yield information
        yield_info = crop.get('yield_per_hectare', '')
        if yield_info:
            tips.append(f"Expected yield: {yield_info}")
            
        return tips

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
    app.config['SECRET_KEY'] = 'your-secret-key-here'
    
    # Initialize crop manager
    crop_manager = CropManager('negros_crops.json')

    @app.route('/', methods=['GET', 'POST'])
    def index():
        if request.method == 'POST':
            try:
                ph = float(request.form.get('ph', 0))
                soil_type = request.form.get('soil_type', '')
                moisture = request.form.get('moisture', '')
                crop_type = request.form.get('crop_type', '')
                
                # Validate inputs
                if not (6.0 <= ph <= 7.5):
                    return jsonify({'error': 'Invalid pH value. Please enter a value between 6.0 and 7.5.'})
                if not soil_type:
                    return jsonify({'error': 'Please select a soil type.'})
                if not moisture:
                    return jsonify({'error': 'Please select a moisture level.'})
                
                # Find matching crops
                matching_crops = crop_manager.find_matching_crops(ph, soil_type, moisture, crop_type)
                
                # Return JSON response for AJAX requests
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'crops': matching_crops})
                
                return render_template('index.html', 
                                    crops=matching_crops,
                                    min_ph=crop_manager.min_ph,
                                    max_ph=crop_manager.max_ph,
                                    crop_types=crop_manager.crop_types,
                                    climate_zones=crop_manager.climate_zones)
                
            except ValueError as e:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'error': str(e)})
                flash(str(e), 'error')
                return redirect(url_for('index'))
        
        return render_template('index.html',
                            min_ph=crop_manager.min_ph,
                            max_ph=crop_manager.max_ph,
                            crop_types=crop_manager.crop_types,
                            climate_zones=crop_manager.climate_zones)
    
    return app

app = create_app()

# Get environment variables with defaults
PORT = int(os.environ.get('PORT', 5000))
DEBUG = os.environ.get('FLASK_ENV') == 'development'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=DEBUG)

