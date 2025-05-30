from flask import Flask, render_template_string, request
import pandas as pd
import plotly.graph_objs as go
import plotly.io as pio
from sqlalchemy import create_engine
import urllib
import statsmodels.api as sm

app = Flask(__name__)

# Dane logowania do bazy SQL
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
    # Pobranie danych z bazy
    df_data = pd.read_sql("SELECT * FROM PredictionData", engine)
    df_preds = pd.read_sql("SELECT * FROM PredictionResults", engine)

    df_data['date'] = pd.to_datetime(df_data['date'])
    df_preds['predicted_date'] = pd.to_datetime(df_preds['predicted_date'])

    session_ids = df_data['session_id'].unique().tolist()
    selected_session = request.args.get('session_id', session_ids[0] if session_ids else None)

    # Filtrowanie po session_id
    df_data_filtered = df_data[df_data['session_id'] == selected_session]
    df_preds_filtered = df_preds[df_preds['session_id'] == selected_session]

    # Sortowanie
    df_data_sorted = df_data_filtered.sort_values('date')
    df_preds_sorted = df_preds_filtered.sort_values('predicted_date')

    # Linia oryginalna
    trace_original = go.Scatter(
        x=df_data_sorted['date'], y=df_data_sorted['value'],
        mode='lines+markers', name='Oryginalne dane', line=dict(color='blue')
    )

    # Predykcje
    trace_predicted = go.Scatter(
        x=df_preds_sorted['predicted_date'], y=df_preds_sorted['predicted_value'],
        mode='lines+markers', name='Predykcje', line=dict(color='red')
    )

    # Linia regresji
    df_data_sorted['timestamp'] = (df_data_sorted['date'] - df_data_sorted['date'].min()).dt.total_seconds()
    X = sm.add_constant(df_data_sorted['timestamp'])
    model = sm.OLS(df_data_sorted['value'], X).fit()

    # Zakres od początku danych do końca predykcji
    full_range = pd.date_range(
        start=df_data_sorted['date'].min(),
        end=df_preds_sorted['predicted_date'].max()
    )
    full_timestamp = (full_range - df_data_sorted['date'].min()).total_seconds()
    X_full = sm.add_constant(full_timestamp)
    y_reg_line = model.predict(X_full)

    trace_regression = go.Scatter(
        x=full_range, y=y_reg_line,
        mode='lines', name='Linia regresji',
        line=dict(dash='dash', color='gray')
    )

    fig = go.Figure(data=[trace_original, trace_predicted, trace_regression])
    fig.update_layout(title=f'Dane i Predykcja: {selected_session}', xaxis_title='Data', yaxis_title='Wartość')
    chart_html = pio.to_html(fig, full_html=False)

    # Tabela z danymi + predykcjami (na końcu)
    df_preds_filtered = df_preds_filtered.rename(columns={
        'predicted_date': 'date',
        'predicted_value': 'value'
    })[['date', 'value']]

    df_all = pd.concat([df_data_sorted[['date', 'value']], df_preds_filtered], ignore_index=True)
    df_all = df_all.sort_values('date')

    table_html = df_all.to_html(index=False)

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Predykcje</title>
        <style>
            body { font-family: Arial; padding: 20px; }
            select { font-size: 16px; padding: 4px; margin-bottom: 20px; }
            table { border-collapse: collapse; width: 100%; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
        </style>
    </head>
    <body>
        <h1>Predykcja OLS - Sesja</h1>
        <form method="get">
            <label for="session_id">Wybierz session_id:</label>
            <select name="session_id" onchange="this.form.submit()">
                {% for sid in session_ids %}
                    <option value="{{ sid }}" {% if sid == selected_session %}selected{% endif %}>{{ sid }}</option>
                {% endfor %}
            </select>
        </form>

        {{ chart_html|safe }}

        <h2>Dane</h2>
        {{ table_html|safe }}
    </body>
    </html>
    """, session_ids=session_ids, selected_session=selected_session, chart_html=chart_html, table_html=table_html)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
