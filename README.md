# 🎓 EduPredict: Student Performance Prediction System

![EduPredict Banner](banner.png)

## 🌟 Overview
**EduPredict** is a sophisticated web-based platform designed to proactively identify and support at-risk students using Machine Learning. By analyzing academic history, behavioral patterns, and socio-economic factors, the system provides educators with actionable insights to improve student success rates.

Built with **Django** and powered by a **Random Forest** classification model, EduPredict bridges the gap between data science and educational administration.

---

## ✨ Key Features

### 👨‍💼 For Administrators
- **Institution-Wide Analytics**: Monitor performance trends across all departments.
- **Staff Management**: Manage HOD and Admin accounts with a unified secure system.
- **Departmental Control**: Create and organize departments to mirror the institution's structure.
- **Global Reports**: Generate comprehensive PDF summaries of institutional performance.

### 🏫 For Heads of Department (HODs)
- **Departmental Dashboard**: Real-time visualization of student performance within their department.
- **Predictive Analytics**: Run individual or bulk predictions to identify at-risk students.
- **Intervention Tracking**: Record and monitor support actions (e.g., extra classes, counseling).
- **Automated Alerts**: Receive and send automated email notifications for critical risk levels.
- **Bulk Enrollment**: Upload student data via CSV or Excel for rapid system population.

### 📊 Machine Learning Core
- **Random Forest Model**: High-accuracy classification based on multiple features.
- **Feature Engineering**: Incorporates study hours, attendance, parental education, and socio-economic indicators.
- **Real-time Prediction**: Immediate feedback upon student enrollment or data update.
- **Automated Risk Labeling**: Categorizes students into Low, Medium, and High-risk tiers.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.12+, Django 5.x
- **Frontend**: HTML5, Vanilla CSS3, JavaScript (Chart.js for visualizations)
- **Machine Learning**: Scikit-Learn (Random Forest), Pandas, NumPy
- **Reporting**: xhtml2pdf, Matplotlib (for PDF charts), QR Code Generation
- **Database**: SQLite (Default) / PostgreSQL compatible
- **Notifications**: Django Email Backend

---

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/Student_performance_ML_Project.git
cd Student_performance_ML_Project
```

### 2. Create a Virtual Environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install django pandas numpy scikit-learn matplotlib xhtml2pdf qrcode pillow python-decouple python-dotenv openpyxl
```

### 4. Environment Configuration
Create a `.env` file in the root directory and configure your email settings:
```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### 5. Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser
```bash
python manage.py createsuperuser
```

### 7. Run the Application
```bash
python manage.py run server
```
Access the dashboard at `http://127.0.0.1:8000`.

---

## 📁 Project Structure

```text
├── myproject/              # Django project configuration
├── myapp/                  # Core application logic
│   ├── models.py           # Database schema (User, Student, Intervention)
│   ├── views.py            # Business logic and ML integration
│   ├── templates/          # HTML templates for dashboards and reports
│   └── utils.py            # Email and reporting utilities
├── random_forest_model.pkl # Trained ML model
├── model_metadata.json     # Encoders and metadata for the model
├── All_Models_comparison.py # ML experimentation script
├── Final_Dataset.csv       # Training data
└── manage.py               # Django management script
```

---

## 📈 ML Methodology
The prediction engine utilizes a **Random Forest Classifier** trained on the `Student_Performance.csv` dataset. The model evaluates 10+ features including:
- **Academic**: Attendance %, Overall Scores, Study Method.
- **Socio-Economic**: Parental Education, Internet Access, Travel Time.
- **Behavioral**: Study Hours, Extra-curricular activities.

The model achieves high precision in identifying students likely to fail, enabling timely interventions.

---

## 📜 License
Distributed under the MIT License. See `LICENSE` for more information.

---
*Developed with ❤️ for Academic Excellence.*
