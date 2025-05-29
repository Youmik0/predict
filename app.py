from flask import Flask, render_template_string
import pandas as pd
from sqlalchemy import create_engine
import urllib

app = Flask(__name__)

server = 'predictionsv.database.windows.net'
database = 'PredictionDatabase'
username = 'sqladmin'
password = 'Adfxytdryxdt@szer21324'

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

    df = pd.merge(df_data, df_preds, on='session_id', how='outer', suffixes=('_original', '_predicted'))
    
    html = df.to_html(index=False)
    return render_template_string("""
        <html>
            <head><title>Predictions</title></head>
            <body>
                <h1>Dane i Predykcje</h1>
                {{table|safe}}
            </body>
        </html>
    """, table=html)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
