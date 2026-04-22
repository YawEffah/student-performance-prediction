import os
import django
import json
import pickle
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from myapp.models import Student
from django.conf import settings
from django.utils import timezone

def load_model_and_meta():
    model_path = os.path.join(settings.BASE_DIR, 'random_forest_model.pkl')
    meta_path = os.path.join(settings.BASE_DIR, 'model_metadata.json')
    
    with open(model_path, 'rb') as file:
        model = pickle.load(file)
    with open(meta_path, 'r') as file:
        meta = json.load(file)
    return model, meta

def run_all_predictions():
    print("Loading model...")
    try:
        model, meta = load_model_and_meta()
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    students = Student.objects.all()
    total = students.count()
    print(f"Starting predictions for {total} students...")
    
    high_risk_count = 0
    low_risk_count = 0
    
    for i, student in enumerate(students):
        try:
            features = student.get_ml_features(meta)
            prediction = model.predict([features])
            prediction_value = int(prediction[0])
            
            student.result = prediction_value
            student.risk_level = 'High' if prediction_value == 0 else 'Low'
            student.last_prediction_date = timezone.now()
            student.save()
            
            if prediction_value == 0:
                high_risk_count += 1
            else:
                low_risk_count += 1
                
            if (i + 1) % 10 == 0 or (i + 1) == total:
                print(f"Processed {i + 1}/{total} students...")
        
        except Exception as e:
            print(f"Error predicting for student {student.student_id}: {e}")

    print("\n--- Prediction Summary ---")
    print(f"Total Processed: {total}")
    print(f"High Risk Identified: {high_risk_count}")
    print(f"Low Risk Identified: {low_risk_count}")
    print("--------------------------")

if __name__ == "__main__":
    run_all_predictions()
