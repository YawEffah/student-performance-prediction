import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier
import pickle
import json

# Load dataset
df = pd.read_csv("Student_Performance.csv")

# Define Target: 1 for Pass (A, B, C), 0 for At Risk (D, E, F)
grade_map = {
    'a': 1, 'b': 1, 'c': 1,
    'd': 0, 'e': 0, 'f': 0
}
df['result'] = df['final_grade'].str.lower().map(grade_map)

# Features selection (excluding IDs and raw scores if we want a predictive system, 
# but usually scores are part of the academic profile)
categorical_cols = [
    'gender', 'school_type', 'parent_education', 
    'internet_access', 'travel_time', 'extra_activities', 'study_method'
]
numerical_cols = ['age', 'study_hours', 'attendance_percentage']

# Label Encoding for categoricals
label_encoders = {}
for col in categorical_cols:
    le = LabelEncoder()
    df[col] = le.fit_transform(df[col].astype(str))
    label_encoders[col] = list(le.classes_)

# Prepare X and y
X = df[categorical_cols + numerical_cols]
y = df['result']

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Scale numerical features
scaler = StandardScaler()
# Note: In a real production app, we'd scale X_train and save the scaler.
# For simplicity in this local refactor, we'll fit on the whole X if needed or just use RF which is scale-invariant.
# Let's keep it simple for now and use RF.

# Model
rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X_train, y_train)

# Accuracy check
print(f"Model Accuracy: {rf.score(X_test, y_test):.2f}")

# Save the trained model
with open("random_forest_model.pkl", "wb") as file:
    pickle.dump(rf, file)

# Save encoders mapping for the web app to use
with open("model_metadata.json", "w") as file:
    json.dump({
        "categorical_cols": categorical_cols,
        "numerical_cols": numerical_cols,
        "encoders": label_encoders
    }, file)

print("Model and metadata saved successfully.")
