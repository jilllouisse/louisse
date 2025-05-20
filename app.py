from flask import Flask, render_template, request, redirect, url_for, flash
import json
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for flash messages

# Load crop data
with open('negros_crops.json') as f:
    crop_data = json.load(f)

# Get the valid pH range from the crop data
min_ph = min(crop['pH_min'] for crop in crop_data)
max_ph = max(crop['pH_max'] for crop in crop_data)

@app.route('/', methods=['GET', 'POST'])
def index():
    crops = []
    if request.method == 'POST' and 'exit' not in request.form:
        try:
            pH = float(request.form['ph'])
            if pH < min_ph or pH > max_ph:
                flash(f'Please enter a pH value between {min_ph} and {max_ph}', 'error')
                return render_template('index.html', crops=crops)
        except ValueError:
            flash('Please enter a valid pH value', 'error')
            return render_template('index.html', crops=crops)

        soil_type = request.form['soil_type'].lower()
        moisture = request.form['moisture'].lower()

        print(f"User input - pH: {pH}, Soil: {soil_type}, Moisture: {moisture}")

        for crop in crop_data:
            print(f"Checking crop: {crop['crop']}")
            if (crop['pH_min'] <= pH <= crop['pH_max'] and
                crop['soil_type'] == soil_type and
                crop['moisture_level'].lower() == moisture):
                print(f"Match found: {crop['crop']}")
                harvest_date = datetime.today() + timedelta(days=crop['duration_days'])
                crop['harvest_date'] = harvest_date.strftime('%B %d, %Y')
                crops.append(crop)

        if not crops:
            flash('No matching crops found for your input. Try adjusting your parameters.', 'info')

    elif request.method == 'POST' and 'exit' in request.form:
        return render_template('goodbye.html')

    return render_template('index.html', crops=crops, min_ph=min_ph, max_ph=max_ph)

if __name__ == '__main__':
    app.run(debug=True)

