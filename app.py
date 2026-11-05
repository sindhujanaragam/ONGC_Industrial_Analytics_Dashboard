from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "ONGC_Data_Analytics_Dataset_410_Rows.csv"

app = Flask(__name__)

# -----------------------------
# Load and prepare dataset
# -----------------------------
df_raw = pd.read_csv(CSV_PATH)
df = df_raw.copy()

# Same cleaning approach as the uploaded notebook:
# fill missing oil production with its mean, then remove duplicates.
df["Oil_Production_MMT"] = df["Oil_Production_MMT"].fillna(
    df["Oil_Production_MMT"].mean()
)
df = df.drop_duplicates().reset_index(drop=True)

# Model: predict Revenue_Crore from all other variables.
model_df = pd.get_dummies(
    df,
    columns=["Month", "Region"],
    drop_first=True
)

X = model_df.drop("Revenue_Crore", axis=1)
y = model_df["Revenue_Crore"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = LinearRegression()
model.fit(X_train, y_train)

pred = model.predict(X_test)
mae = mean_absolute_error(y_test, pred)
rmse = np.sqrt(mean_squared_error(y_test, pred))
r2 = r2_score(y_test, pred)

# -----------------------------
# Helpers
# -----------------------------
MONTH_ORDER = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4,
    "May": 5, "Jun": 6, "Jul": 7, "Aug": 8,
    "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
}

def filtered_data(region="All", year="All"):
    d = df.copy()
    if region and region != "All":
        d = d[d["Region"] == region]
    if year and str(year) != "All":
        d = d[d["Year"] == int(year)]
    return d

def safe_float(x):
    return round(float(x), 2)

# -----------------------------
# Pages
# -----------------------------
@app.route("/")
def dashboard():
    return render_template(
        "index.html",
        regions=sorted(df["Region"].dropna().unique().tolist()),
        years=sorted(df["Year"].dropna().unique().tolist()),
        model_r2=safe_float(r2),
        model_mae=safe_float(mae),
        model_rmse=safe_float(rmse),
        records=len(df)
    )

# -----------------------------
# API: dashboard data
# -----------------------------
@app.get("/api/dashboard")
def dashboard_api():
    region = request.args.get("region", "All")
    year = request.args.get("year", "All")
    d = filtered_data(region, year)

    if len(d) == 0:
        return jsonify({"error": "No records match the selected filters."}), 400

    # Monthly production
    monthly = (
        d.assign(MonthNum=d["Month"].map(MONTH_ORDER))
         .groupby(["Year", "MonthNum", "Month"], as_index=False)
         .agg(
             oil=("Oil_Production_MMT", "sum"),
             gas=("Gas_Production_BCM", "sum"),
             revenue=("Revenue_Crore", "sum"),
             cost=("Operational_Cost_Crore", "sum"),
             downtime=("Equipment_Downtime_Hours", "sum")
         )
         .sort_values(["Year", "MonthNum"])
    )

    # Region summary
    region_summary = (
        d.groupby("Region", as_index=False)
         .agg(
             oil=("Oil_Production_MMT", "mean"),
             gas=("Gas_Production_BCM", "mean"),
             wells=("Wells_Drilled", "sum"),
             revenue=("Revenue_Crore", "mean"),
             cost=("Operational_Cost_Crore", "mean"),
             downtime=("Equipment_Downtime_Hours", "mean"),
             safety=("Safety_Incidents", "sum")
         )
         .sort_values("revenue", ascending=False)
    )

    # KPIs use sums for production/financial/operations and averages for
    # point-in-time indicators.
    kpis = {
        "oil": safe_float(d["Oil_Production_MMT"].sum()),
        "gas": safe_float(d["Gas_Production_BCM"].sum()),
        "revenue": safe_float(d["Revenue_Crore"].sum()),
        "cost": safe_float(d["Operational_Cost_Crore"].sum()),
        "wells": int(d["Wells_Drilled"].sum()),
        "downtime": safe_float(d["Equipment_Downtime_Hours"].sum()),
        "safety": int(d["Safety_Incidents"].sum()),
        "crude": safe_float(d["Crude_Oil_Price_USD"].mean()),
        "records": int(len(d))
    }

    # Safety
    safety_by_region = (
        d.groupby("Region", as_index=False)["Safety_Incidents"]
         .sum()
         .sort_values("Safety_Incidents", ascending=False)
    )

    # Downtime
    downtime_by_region = (
        d.groupby("Region", as_index=False)["Equipment_Downtime_Hours"]
         .mean()
         .sort_values("Equipment_Downtime_Hours", ascending=False)
    )

    # Correlation with Revenue for numeric columns
    corr_cols = [
        "Oil_Production_MMT", "Gas_Production_BCM", "Wells_Drilled",
        "Employees", "Operational_Cost_Crore", "Crude_Oil_Price_USD",
        "Equipment_Downtime_Hours", "Safety_Incidents"
    ]
    corr = []
    for c in corr_cols:
        value = d[c].corr(d["Revenue_Crore"])
        if pd.notna(value):
            corr.append({"feature": c, "value": safe_float(value)})
    corr = sorted(corr, key=lambda x: abs(x["value"]), reverse=True)

    # Table rows
    table = d.sort_values(["Year", "Month"]).copy()
    table_rows = []
    for _, row in table.head(100).iterrows():
        table_rows.append({
            "month": row["Month"],
            "year": int(row["Year"]),
            "region": row["Region"],
            "oil": safe_float(row["Oil_Production_MMT"]),
            "gas": safe_float(row["Gas_Production_BCM"]),
            "wells": int(row["Wells_Drilled"]),
            "revenue": safe_float(row["Revenue_Crore"]),
            "cost": safe_float(row["Operational_Cost_Crore"]),
            "downtime": safe_float(row["Equipment_Downtime_Hours"]),
            "safety": int(row["Safety_Incidents"])
        })

    return jsonify({
        "kpis": kpis,
        "monthly": monthly.to_dict(orient="records"),
        "region_summary": region_summary.to_dict(orient="records"),
        "safety_by_region": safety_by_region.to_dict(orient="records"),
        "downtime_by_region": downtime_by_region.to_dict(orient="records"),
        "correlation": corr,
        "table": table_rows
    })

# -----------------------------
# API: Revenue prediction
# -----------------------------
@app.post("/api/predict")
def predict():
    data = request.get_json(force=True)

    required = [
        "Month", "Year", "Region", "Oil_Production_MMT",
        "Gas_Production_BCM", "Wells_Drilled", "Employees",
        "Operational_Cost_Crore", "Crude_Oil_Price_USD",
        "Equipment_Downtime_Hours", "Safety_Incidents"
    ]

    missing = [k for k in required if k not in data or data[k] in ("", None)]
    if missing:
        return jsonify({"error": "Missing fields: " + ", ".join(missing)}), 400

    try:
        row = {
            "Month": str(data["Month"]),
            "Year": int(data["Year"]),
            "Region": str(data["Region"]),
            "Oil_Production_MMT": float(data["Oil_Production_MMT"]),
            "Gas_Production_BCM": float(data["Gas_Production_BCM"]),
            "Wells_Drilled": int(data["Wells_Drilled"]),
            "Employees": int(data["Employees"]),
            "Operational_Cost_Crore": float(data["Operational_Cost_Crore"]),
            "Crude_Oil_Price_USD": float(data["Crude_Oil_Price_USD"]),
            "Equipment_Downtime_Hours": float(data["Equipment_Downtime_Hours"]),
            "Safety_Incidents": int(data["Safety_Incidents"])
        }

        one = pd.DataFrame([row])
        one = pd.get_dummies(one, columns=["Month", "Region"], drop_first=True)
        one = one.reindex(columns=X.columns, fill_value=0)

        prediction = float(model.predict(one)[0])

        return jsonify({
            "prediction": round(prediction, 2),
            "model": "Linear Regression",
            "r2": round(float(r2), 4),
            "mae": round(float(mae), 2),
            "rmse": round(float(rmse), 2)
        })
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
