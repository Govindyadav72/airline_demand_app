# --- Requirements ---
# Flask (for web app), requests (for API calls), pandas (data processing), plotly (for visualization)

from flask import Flask, render_template, request
import requests
import pandas as pd
import plotly.express as px
import io

app = Flask(__name__)

# --- Sample Public API (Aviationstack, or use placeholder data for mockup) ---
API_KEY = "0829db4a5c642b35f3cd3b33dc607209"  # Replace with your aviationstack or aviationdata API key
API_URL = "http://api.aviationstack.com/v1/flights"

# --- Helper to fetch airline data ---
def fetch_airline_data():
    params = {
        'access_key': API_KEY,
        'limit': 100
    }
    response = requests.get(API_URL, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# --- Process data to extract trends ---
def process_data(raw_data, departure_filter=None, arrival_filter=None):
    if not raw_data or 'data' not in raw_data:
        return pd.DataFrame(), pd.DataFrame()

    flights = raw_data['data']
    df = pd.json_normalize(flights)

    df['departure_time'] = pd.to_datetime(df['departure.scheduled'])
    df['route'] = df['departure.iata'] + " → " + df['arrival.iata']

    # Apply filters
    if departure_filter:
        df = df[df['departure.iata'].str.upper() == departure_filter.upper()]
    if arrival_filter:
        df = df[df['arrival.iata'].str.upper() == arrival_filter.upper()]

    if df.empty:
        return pd.DataFrame(columns=['Route', 'Count']), pd.DataFrame(columns=['Hour', 'Flights'])

    # Top routes
    top_routes = df['route'].value_counts().head(10).reset_index()
    top_routes.columns = ['Route', 'Count']

    # Hourly demand
    df['hour'] = df['departure_time'].dt.hour
    hourly_demand = df['hour'].value_counts().sort_index().reset_index()
    hourly_demand.columns = ['Hour', 'Flights']

    return top_routes, hourly_demand


# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    departure_filter = request.form.get('departure')
    arrival_filter = request.form.get('arrival')

    raw_data = fetch_airline_data()
    top_routes, hourly_demand = process_data(raw_data, departure_filter, arrival_filter)

    fig1 = px.bar(top_routes, x='Route', y='Count', title='Top 10 Popular Routes')
    fig2 = px.line(hourly_demand, x='Hour', y='Flights', title='Hourly Demand Trend')

    graph1 = fig1.to_html(full_html=False)
    graph2 = fig2.to_html(full_html=False)

    return render_template('result.html', graph1=graph1, graph2=graph2)

# --- Run app ---
if __name__ == '__main__':
    app.run(debug=True)
