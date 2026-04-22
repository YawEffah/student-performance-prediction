import pandas as pd
import numpy as np

def analyze_risk_factors():
    print("--- Analyzing Final_Dataset.csv ---")
    try:
        df = pd.read_csv("Final_Dataset.csv")
        # Ensure 'result' is numeric
        df['result'] = pd.to_numeric(df['result'], errors='coerce')
        df = df.dropna(subset=['result'])
        
        # Split into High Risk (0) and Low Risk (1)
        high_risk = df[df['result'] == 0]
        low_risk = df[df['result'] == 1]
        
        print(f"Total students: {len(df)}")
        print(f"High Risk students: {len(high_risk)}")
        print(f"Low Risk students: {len(low_risk)}")
        
        # Calculate means for comparison
        features = ['age', 'studytime', 'failures', 'absences', 'G3']
        stats = pd.DataFrame({
            'Feature': features,
            'High Risk Mean': [high_risk[f].mean() for f in features],
            'Low Risk Mean': [low_risk[f].mean() for f in features]
        })
        print("\nSummary Statistics:")
        print(stats)
        
        # Check G3 threshold
        print(f"\nMax G3 for High Risk: {high_risk['G3'].max()}")
        print(f"Min G3 for Low Risk: {low_risk['G3'].min()}")

    except Exception as e:
        print(f"Error analyzing Final_Dataset.csv: {e}")

    print("\n--- Analyzing Student_Performance.csv ---")
    try:
        df_sp = pd.read_csv("Student_Performance.csv")
        # Check final_grade vs overall_score
        grade_stats = df_sp.groupby('final_grade')['overall_score'].agg(['mean', 'min', 'max', 'count'])
        print("\nGrade Statistics (Student_Performance.csv):")
        print(grade_stats)
        
    except Exception as e:
        print(f"Error analyzing Student_Performance.csv: {e}")

if __name__ == "__main__":
    analyze_risk_factors()
