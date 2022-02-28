import json
import os
import re
import requests

from datetime import datetime, timedelta
from google.cloud import storage

graph_api_base = os.getenv('MICROSOFT_GRAPH_API_BASE_URL')
weather_api_base = os.getenv('WEATHER_API_BASE_URL')
weather_api_key = os.getenv('WEATHER_API_KEY')

storage_client = storage.Client(os.getenv('GCP_PROJECT'))
bucket = storage_client.get_bucket(os.getenv('GCP_BUCKET_NAME'))

# Pull access tokens from storage bucket
token_blob = bucket.blob('tokens.json')
previous_token_data = json.loads(token_blob.download_as_string().decode('utf-8'))

token_url = os.getenv('MICROSOFT_OAUTH_TOKEN_URL')
refresh_token_payload = {
  'grant_type': 'refresh_token',
  'client_id': os.getenv('MICROSOFT_OAUTH_CLIENT_ID'),
  'client_secret': os.getenv('MICROSOFT_OAUTH_CLIENT_SECRET'),
  'scope': previous_token_data['scope'],
  'refresh_token': previous_token_data['refresh_token'],
  'redirect_uri': previous_token_data['redirect_uri'],
}

token_response = requests.post(token_url, data=refresh_token_payload)
tokens = token_response.json()
tokens['redirect_uri'] = previous_token_data['redirect_uri']
access_token = tokens['access_token']

# Persist access tokens in bucket for next run
token_blob.upload_from_string(json.dumps(tokens))

today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
tomorrow = today + timedelta(days=1)

graph_request_headers = {
  'Authorization': f'Bearer {access_token}',
  'Accept': 'application/json',
  'Content-Type': 'application/json',
  'Prefer': 'outlook.timezone="America/New_York"',
}

calendar_response = requests.post(f'{graph_api_base}/me/calendar/getschedule', json={
  'Schedules': [ 'jawbenne@iu.edu' ],
  'StartTime': {
    'dateTime': today.isoformat(),
    'timeZone': 'America/New_York',
  },
  'EndTime': {
    'dateTime': tomorrow.isoformat(),
    'timeZone': 'America/New_York',
  },
}, headers=graph_request_headers)

full_schedule = calendar_response.json()['value'][0]['scheduleItems']
schedule = list(map(lambda item: { 'summary': item['subject'], 'startTime': datetime.fromisoformat(item['start']['dateTime'].replace('.0000000', '')).astimezone().isoformat(), 'endTime': datetime.fromisoformat(item['end']['dateTime'].replace('.0000000', '')).astimezone().isoformat() }, filter(lambda item: item['status'] == 'busy' and item['isMeeting'], full_schedule)))

task_list_resposne = requests.get(f'{graph_api_base}/me/todo/lists', headers=graph_request_headers)
task_list_ids = list(map(lambda task_list: task_list['id'], task_list_resposne.json()['value']))

todays_tasks = []
for task_list_id in task_list_ids:
    tasks_response = requests.get(f'{graph_api_base}/me/todo/lists/{task_list_id}/tasks?$filter=dueDateTime/dateTime ge \'{today.isoformat()}\' and dueDateTime/dateTime lt \'{tomorrow.isoformat()}\'', headers=graph_request_headers)
    todays_tasks.extend(tasks_response.json()['value'])
tasks = list(map(lambda task: { 'summary': task['title'], 'complete': task['status'] == 'completed' }, todays_tasks))

weather_response = requests.get(f'{weather_api_base}/v1/forecast.json?key={weather_api_key}&q=47404&days=1&aqi=no&alerts=no')
hourly_forecast = weather_response.json()['forecast']['forecastday'][0]['hour']
hour_pattern = re.compile('.*(07:00|12:00|17:00)$')
weather_forecast = list(map(lambda forecast: { 'time': datetime.fromisoformat(forecast['time']).astimezone().isoformat(), 'condition': forecast['condition']['code'], 'temperature': int(forecast['feelslike_f']), 'precipitation': forecast['chance_of_rain'] }, filter(lambda forecast: hour_pattern.match(forecast['time']), hourly_forecast)))

output = {
  'schedule': schedule,
  'tasks': tasks,
  'weather': weather_forecast,
}

output_blob = bucket.blob('current.json')
output_blob.upload_from_string(json.dumps(output))
