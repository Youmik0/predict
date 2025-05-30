from flask import Flask, render_template_string
import pandas as pd
from sqlalchemy import create_engine
import urllib
import os

app = Flask(__name__)

server = 'predictionsv.database.windows.net'
database = 'PredictionDatabase'
username = 'sqladmin'
password = 'Adfxytdryxdt@szer21324'

port = int(os.environ.get("PORT", 8000))

params = urllib.parse.quote_plus(
    f"Driver={{ODBC Driver 17 for SQL Server}};"
    f"Server=tcp:{server},1433;"
    f"Database={database};"
    f"Uid={username};"
    f"Pwd={password};"
    f"Encrypt=yes;"
    f"TrustServerCertificate=no;"
    f"Connection Timeout=30;"
)

engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

@app.route('/')
def index():
    df_data = pd.read_sql("SELECT * FROM PredictionData", engine)
    df_preds = pd.read_sql("SELECT * FROM PredictionResults", engine)

    html_output = ""

    for session_id in df_data['session_id'].unique():
        df_orig = df_data[df_data['session_id'] == session_id]
        df_pred = df_preds[df_preds['session_id'] == session_id].sort_values(by='id').tail(3)  # zakładam że 'id' rośnie z czasem

        orig_table = df_orig.to_html(index=False)
        pred_table = df_pred.to_html(index=False)

        html_output += f"""
            <div style="margin-bottom: 40px; padding: 10px; border: 1px solid #ccc; border-radius: 10px;">
                <h2>Session ID: {session_id}</h2>
                <h3>Dane oryginalne</h3>
                {orig_table}
                <h3 style="color: green;">Predykcje (3 ostatnie)</h3>
                {pred_table}
            </div>
        """

    return render_template_string("""
        <html>
            <head>
                <title>Predykcje</title>
                <style>
                    body { font-family: Arial, sans-serif; padding: 20px; }
                    table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    th { background-color: #f2f2f2; }
                </style>
            </head>
            <body>
                <h1>Predykcje według sesji</h1>
                {{ content|safe }}
            </body>
        </html>
    """, content=html_output)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=port)
