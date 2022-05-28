import time
import requests
import json

def sync_user(handle: str):
    print(f'syncing user with handle {handle}')
    response = requests.post(f"http://cf_tracker_app:80/user/sync", data = json.dumps({'handle': handle}))
    result = response.json()
    if result['status'] == 'success':
        print(f'successfully synced with {result["message"]} mode')


def sync_users():
    response = requests.get(f"http://cf_tracker_app:80/users")
    users = response.json()['users']
    for user in users:
        sync_user(handle=user['handle'])


while True:
    try:
        sync_users()
    except Exception as e:
        print(e)

    time.sleep(60 * 5)
