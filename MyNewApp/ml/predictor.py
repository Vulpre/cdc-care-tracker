import os
from datetime import date
from django.utils import timezone
import joblib
import pandas as pd

MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(MODEL_DIR, 'nutrition_model.pkl')

_cached_model = None

def get_model():
    global _cached_model
    if _cached_model is None:
        if not os.path.exists(MODEL_PATH):
            # Train model if not present
            from MyNewApp.ml.train_nutrition_model import train_and_save
            train_and_save()
        _cached_model = joblib.load(MODEL_PATH)
    return _cached_model

def calculate_age_months(date_of_birth):
    today = timezone.localdate()
    months = (today.year - date_of_birth.year) * 12 + (today.month - date_of_birth.month)
    if today.day < date_of_birth.day:
        months -= 1
    return max(1, months)

def predict_nutritional_status(date_of_birth, gender_str, weight_kg, height_cm):
    """
    Predicts nutritional status using the trained Random Forest model.

    Returns:
        dict: {
            'status': 'Normal' | 'Underweight' | 'Severely Underweight' | 'Overweight',
            'bmi': float,
            'age_months': int,
            'is_at_risk': bool,
            'flag_type': str or None,
            'recommendation': str
        }
    """
    if not weight_kg or not height_cm or float(height_cm) <= 0:
        return {
            'status': 'Unassessed',
            'bmi': None,
            'age_months': calculate_age_months(date_of_birth) if date_of_birth else None,
            'is_at_risk': False,
            'flag_type': None,
            'recommendation': 'Weight and height required for assessment.'
        }

    weight = float(weight_kg)
    height = float(height_cm)
    height_m = height / 100.0
    bmi = round(weight / (height_m ** 2), 2)
    age_months = calculate_age_months(date_of_birth) if isinstance(date_of_birth, (date,)) else 36
    gender_num = 1 if str(gender_str).lower().startswith('f') else 0

    try:
        model = get_model()
        input_df = pd.DataFrame([{
            'age_months': age_months,
            'gender': gender_num,
            'height_cm': height,
            'weight_kg': weight,
            'bmi': bmi
        }])
        status = model.predict(input_df)[0]
    except Exception as e:
        # Fallback heuristic based on WHO standards
        if bmi < 13.0:
            status = 'Severely Underweight'
        elif bmi < 14.5:
            status = 'Underweight'
        elif bmi > 18.0:
            status = 'Overweight'
        else:
            status = 'Normal'

    # Determine risk & recommendation
    is_at_risk = status in ['Underweight', 'Severely Underweight', 'Overweight']
    flag_type = 'Underweight' if 'Underweight' in status else None

    if status == 'Severely Underweight':
        rec = "Urgent: Child requires immediate supplementary feeding, therapeutic care, and pediatric checkup."
    elif status == 'Underweight':
        rec = "Child is underweight. Recommended for CDC daily dietary supplementation and monthly monitoring."
    elif status == 'Overweight':
        rec = "Child is overweight. Advise parents on balanced meals and active physical play."
    else:
        rec = "Normal growth parameters. Continue healthy diet and regular development tracking."

    return {
        'status': status,
        'bmi': bmi,
        'age_months': age_months,
        'is_at_risk': is_at_risk,
        'flag_type': flag_type,
        'recommendation': rec
    }
