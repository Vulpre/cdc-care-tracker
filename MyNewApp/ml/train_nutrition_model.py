"""
Child Nutritional Status Prediction Model Training Script
Based on WHO Child Growth Standards (Ages 0 - 72 months / 0 - 6 years)
For CDC Care Tracker (Child Development Center) - BSIT IT3A

Target Classes:
  - Normal
  - Underweight
  - Severely Underweight
  - Overweight
"""

import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
import joblib

np.random.seed(42)

def generate_who_growth_dataset(n_samples=6000):
    """
    Generates realistic child growth data modeled after WHO Child Growth Standards:
    - Age: 6 to 72 months (preschool/daycare range)
    - Gender: 0 = Male, 1 = Female
    - Height (cm): based on age growth curve + noise
    - Weight (kg): based on height/age + variation to represent nutritional categories
    """
    ages = np.random.randint(6, 73, size=n_samples)
    genders = np.random.randint(0, 2, size=n_samples) # 0: Male, 1: Female

    records = []

    for age, gender in zip(ages, genders):
        # WHO approximate median height in cm: ~50cm at birth, ~75cm at 1yr (12m), ~87cm at 2yr (24m), ~96cm at 3yr, ~103cm at 4yr, ~110cm at 5yr, ~116cm at 6yr
        expected_height = 50.0 + 6.2 * (age ** 0.55) - (0.8 if gender == 1 else 0.0)
        height = float(np.random.normal(expected_height, 3.5))
        height = max(55.0, min(135.0, height))

        # Expected normal BMI for preschool is roughly 15.0 - 16.5
        # We simulate 4 groups:
        # ~65% Normal, ~18% Underweight, ~7% Severely Underweight, ~10% Overweight
        category_roll = np.random.random()

        if category_roll < 0.65:
            # Normal
            bmi = np.random.normal(15.8, 0.9)
            weight = bmi * ((height / 100.0) ** 2)
            label = 'Normal'
        elif category_roll < 0.83:
            # Underweight (BMI roughly 13.0 - 14.5)
            bmi = np.random.uniform(13.0, 14.4)
            weight = bmi * ((height / 100.0) ** 2)
            label = 'Underweight'
        elif category_roll < 0.90:
            # Severely Underweight (BMI < 13.0)
            bmi = np.random.uniform(10.5, 12.9)
            weight = bmi * ((height / 100.0) ** 2)
            label = 'Severely Underweight'
        else:
            # Overweight (BMI > 17.5)
            bmi = np.random.uniform(17.5, 22.0)
            weight = bmi * ((height / 100.0) ** 2)
            label = 'Overweight'

        weight = round(max(3.0, min(40.0, weight)), 2)
        height = round(height, 2)
        bmi = round(weight / ((height / 100.0) ** 2), 2)

        records.append({
            'age_months': int(age),
            'gender': int(gender),
            'height_cm': height,
            'weight_kg': weight,
            'bmi': bmi,
            'nutritional_status': label
        })

    return pd.DataFrame(records)

def train_and_save():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, 'who_child_growth_dataset.csv')
    model_path = os.path.join(base_dir, 'nutrition_model.pkl')

    print("[1/4] Generating WHO-standard child nutritional dataset...")
    df = generate_who_growth_dataset(n_samples=8000)
    df.to_csv(csv_path, index=False)
    print(f"      Saved dataset ({len(df)} rows) to: {csv_path}")

    print("\n[2/4] Preparing features and target...")
    features = ['age_months', 'gender', 'height_cm', 'weight_kg', 'bmi']
    X = df[features]
    y = df['nutritional_status']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("[3/4] Training Random Forest Classifier...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=12,
        random_state=42,
        class_weight='balanced'
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"      Model Accuracy on Test Set: {acc * 100:.2f}%\n")
    print("Classification Report:")
    print(classification_report(y_test, y_pred))

    print("[4/4] Saving trained model...")
    joblib.dump(model, model_path)
    print(f"      Model saved successfully to: {model_path}")

if __name__ == '__main__':
    train_and_save()
