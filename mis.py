from flask import Flask, render_template_string, request
import pandas as pd
from datetime import datetime

app = Flask(__name__)

UPLOAD_HTML = '''
<!doctype html>
<title>MIS Reconciliation Tool</title>
<h1>🦅M.I.S🦅</h1>
<h2>!!!MAKE RECONCILIATION GREAT AGAIN!!!</h2>
<h2>!!!!UPLOAD SAP AND WMS EXCEL FILES!!!!</h2>
<p>!!!!!YOU CAN DOWNLOAD SAMPLE EXCEL FILES FROM THE LINK BELOW!!!!!</p>
<form method=post enctype=multipart/form-data action="/reconcile">
  <label>SAP FILE!!</label><br><input type=file name=sap_file required><br><br>
  <label>WMS FILE!!</label><br><input type=file name=wms_file required><br><br>
  <input type=submit value="🔥🔥🔥!!!RECONCILE!!!RECONCILE!!!RECONCILE!!!🔥🔥🔥">
</form>
<p><a href="https://github.com/axolotzzz/HERLEN" target="_blank">View GitHub Repository</a></p>
'''

DASHBOARD_HTML = '''
<!doctype html>
<title>Reconciliation Dashboard</title>
<h2>Reconciliation Report</h2>
<style>
  .matched { background-color: #e0ffe0; }
  .mismatch { background-color: #ffe0e0; font-weight: bold; }
</style>
<label>Filter:</label>
<select id="statusFilter" onchange="filterTable()">
  <option value="">All</option>
  <option value="Matched">Matched</option>
  <option value="Mismatch">Mismatch</option>
</select>
<br><br>
<table border="1" cellpadding="5" id="reportTable">
  <thead>
    <tr>
      {% for col in columns %}<th>{{ col }}</th>{% endfor %}
    </tr>
  </thead>
  <tbody>
    {% for row in rows %}
    <tr class="{{ 'mismatch' if row[-1] == 'Mismatch' else 'matched' }}">
      {% for cell in row %}<td>{{ cell }}</td>{% endfor %}
    </tr>
    {% endfor %}
  </tbody>
</table>
<br><a href="/">Back to Upload</a>
<script>
function filterTable() {
  const filter = document.getElementById('statusFilter').value;
  const rows = document.querySelectorAll('#reportTable tbody tr');
  rows.forEach(row => {
    if (!filter || row.classList.contains(filter.toLowerCase())) {
      row.style.display = '';
    } else {
      row.style.display = 'none';
    }
  });
}
</script>
'''

@app.route('/')
def upload_form():
    return render_template_string(UPLOAD_HTML)

def reconcile_data(sap_df, wms_df):
    sap_df.rename(columns={'Quantity': 'Quantity_SAP', 'Last GRN Date': 'Last GRN Date_SAP'}, inplace=True)
    wms_df.rename(columns={'Quantity': 'Quantity_WMS', 'Last GRN Date': 'Last GRN Date_WMS'}, inplace=True)

    merged = pd.merge(sap_df, wms_df, on='Part No')
    merged['Last GRN Date_SAP'] = pd.to_datetime(merged['Last GRN Date_SAP'], dayfirst=True)
    merged['Last GRN Date_WMS'] = pd.to_datetime(merged['Last GRN Date_WMS'], dayfirst=True)
    merged['Qty Difference'] = merged['Quantity_SAP'] - merged['Quantity_WMS']
    merged['GRN Date Difference'] = merged['Last GRN Date_SAP'] - merged['Last GRN Date_WMS']
    merged['Status'] = merged.apply(
        lambda row: 'Mismatch' if row['Qty Difference'] != 0 or row['GRN Date Difference'].days != 0 else 'Matched', axis=1
    )

    return merged

@app.route('/reconcile', methods=['POST'])
def reconcile():
    sap_file = request.files['sap_file']
    wms_file = request.files['wms_file']
    sap_df = pd.read_excel(sap_file)
    wms_df = pd.read_excel(wms_file)
    report = reconcile_data(sap_df, wms_df)

    columns = report.columns.tolist()
    rows = report.astype(str).values.tolist()

    return render_template_string(DASHBOARD_HTML, columns=columns, rows=rows)

if __name__ == '__main__':
    app.run(debug=True)
