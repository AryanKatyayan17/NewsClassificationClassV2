import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

load_dotenv()
key=os.getenv('w')

CITY='Newcastle-upon-Tyne'
FILE='weather.csv'

def fetch_data():
    url = f'http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={key}'
    response=requests.get(url)
    data=response.json

    if response.status_code != 200:
        print(f"Error fetching data: {data.get('message', 'Unknown error')}")
        return

    weather_info = {
        'timestamp': pd.Timestamp.now(),
        'city': data['name'],
        'temperature': data['main']['temp'],
        'weather': data['weather'][0]['description'],
        'humidity': data['main']['humidity'],
        'wind_speed': data['wind']['speed']
    }

    df=pd.DataFrame[(weather_info)]
    df.to_csv(FILE, mode='a', header=not pd.read_csv(FILE).empty)
    print("Weather data saved to CSV.")

fetch_data()

scheduler = BackgroundScheduler()
scheduler.add_job(fetch_data, 'interval', minutes=30)
scheduler.start()

try:
    while True:
        time.sleep(1)
except (KeyboardInterrupt, SystemExit):
    scheduler.shutdown()