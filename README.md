# ONGC Industrial Data Analytics Dashboard

A complete Flask + HTML/CSS/JavaScript dashboard built from the supplied ONGC analytics dataset.

## Features
- KPI dashboard
- Region and year filters
- Oil and gas production charts
- Revenue vs operational cost
- Regional performance
- Operations/downtime analytics
- Safety analytics
- Data explorer
- Linear Regression revenue prediction
- Model metrics: R², MAE and RMSE

## Project structure
```text
ONGC_Industrial_Analytics_Dashboard/
│
├── app.py
├── requirements.txt
├── ONGC_Data_Analytics_Dataset_410_Rows.csv
├── templates/
│   └── index.html
└── static/
```

## Run in VS Code (Windows)

### 1. Open the folder
Open `ONGC_Industrial_Analytics_Dashboard` in VS Code.

### 2. Create a virtual environment
Open VS Code Terminal:
```powershell
python -m venv venv
```

### 3. Activate it
PowerShell:
```powershell
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt terminal:
```cmd
venv\Scripts\activate
```

### 4. Install packages
```powershell
pip install -r requirements.txt
```

### 5. Start the dashboard
```powershell
python app.py
```

You should see Flask running on:
`http://127.0.0.1:5000`

### 6. Open the dashboard
Open Chrome/Edge and visit:
```text
http://127.0.0.1:5000
```

## Important
Keep the CSV file in the same folder as `app.py`.

The dashboard follows the data-cleaning/modeling approach in the supplied notebook:
- missing Oil_Production_MMT values are filled with the mean
- duplicate rows are removed
- Month and Region are one-hot encoded
- Linear Regression predicts Revenue_Crore
- train/test split uses test_size=0.2 and random_state=42

The dashboard is an internship/academic analytics prototype, not an official ONGC operational system.
