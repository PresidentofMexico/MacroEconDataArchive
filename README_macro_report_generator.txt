Macro Economic Report Generator (Template)

Files included:
- generate_macro_report.py: Python script to generate a chart-driven PDF from public time series.
- macro_chart_spec.json: Example chart specification (edit/extend to match your 100+ page report).

Quick start (run locally with internet access):
1) Install dependencies:
   pip install pandas pandas_datareader matplotlib reportlab

2) Generate a PDF:
   python generate_macro_report.py --spec macro_chart_spec.json --out Macro_Economic_Data_Archive.pdf

3) Extend:
   - Add additional entries under "charts" in macro_chart_spec.json.
   - For each chart, specify:
       - series: list of FRED IDs + labels
       - transform: level | yoy | qoq_saar
       - frequency: daily | weekly | monthly | quarterly
       - units: label for y-axis

Notes:
- The attached sample PDF included in the recreated report is used as a layout/style reference.
- For some sector charts, you may need additional public sources beyond FRED (EIA, BTS, Census, etc.).
