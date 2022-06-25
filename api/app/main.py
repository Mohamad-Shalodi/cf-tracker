import argparse
import requests
import time
import asyncio
import mysql.connector
import json
import jwt
import random
from typing import Optional, List
from datetime import datetime, date, timedelta
from fastapi import FastAPI, Header, Depends, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

class CreateUserRequest(BaseModel):
    handle: str
    display_name: str
    id_discord_user: str

class SyncUserRequest(BaseModel):
    handle: str

class GetScoreRequest(BaseModel):
    handle: str
    from_date: datetime
    to_date: datetime
    id_discord_user: Optional[str]

class getRanksRequest(BaseModel):
    year: int
    month: int
    id_discord_user: Optional[str]

class getTierRequest(BaseModel):
    handle: str
    from_date: datetime
    to_date: datetime

class getTierRank(BaseModel):
    year: int
    
class PublishHtmlContentRequest(BaseModel):
    html: str



def get_db_connection():
    return mysql.connector.connect(
        host="cf_tracker_db",
        user="root",
        password="root",
        database="cf_tracker"
    )

app = FastAPI()
app.add_middleware(
     CORSMiddleware,
     allow_origins=["*"],
     allow_credentials=True,
     allow_methods=["*"],
     allow_headers=["*"],
)

@app.get("/users")
async def get_users():
    db = get_db_connection()
    db_cursor = db.cursor()
    db_cursor.execute(f'''
        SELECT handle, display_name, image
        FROM user
    ''')
    rows = db_cursor.fetchall()

    users = []
    for row in rows:
        users.append({
            'handle': row[0],
            'display_name': row[1],
            'image': row[2]
        })
    return {
        'users': users
    }

@app.post("/user")
async def create_user(msg: CreateUserRequest):
    response = requests.get(f"https://codeforces.com/api/user.info?handles={msg.handle}")
    if response.status_code != 200:
        return {
            'status': 'failed',
            'message': 'cf api error'
        }

    image = response.json()['result'][0]['titlePhoto']
    db = get_db_connection()
    db_cursor = db.cursor()
    db_cursor.execute('''
        INSERT INTO user
        (handle, display_name, image, id_discord_user)
        VALUES(%s, %s, %s, %s)
    ''', [msg.handle, msg.display_name, image, msg.id_discord_user])
    db.commit()
    
    return {
        'status': 'success'
    }

    # ALTER TABLE user ADD COLUMN image VARCHAR(256) DEFAULT 'https://userpic.codeforces.org/no-title.jpg';

@app.delete("/user/{handle}")
async def delete_user(handle: str):
    db = get_db_connection()
    db_cursor = db.cursor()
    db_cursor.execute('''
        DELETE FROM user
        WHERE handle = %s
    ''', [handle])
    db.commit()
    
    return {
        'status': 'success'
    }

@app.post("/user/sync")
async def sync_user(msg: SyncUserRequest, force: bool = False):
    db = get_db_connection()
    db_cursor = db.cursor()
    db_cursor.execute(f'''
        SELECT id_user, last_synced_at
        FROM user
        WHERE handle = '{msg.handle}'
    ''')
    rows = db_cursor.fetchall()
    if len(rows) == 0:
        return {
            'status': 'failed',
            'message': 'user not found'
        }
    
    id_user = rows[0][0]
    now_date = datetime.now()
    last_synced_date = rows[0][1]

    # sync allowed every 1 hour only
    if not force and (now_date - last_synced_date).total_seconds() < 60 * 60:
        return {
            'status': 'failed',
            'message': 'recently synced'
        }

    response = requests.get(f"https://codeforces.com/api/user.status?handle={msg.handle}&from=1&count=999999999")
    if response.status_code != 200:
        return {
            'status': 'failed',
            'message': 'cf api error'
        }

    submissions = response.json().get('result', [])
    submissions = list(reversed(submissions))
    for submission in submissions:
        problem_key = f"{submission['problem']['contestId']}{submission['problem']['index']}"
        creation_time = datetime.fromtimestamp(submission['creationTimeSeconds'])
        problem_rate = int(submission.get('problem', {}).get('rating', 0))
        verdict = submission.get('verdict', 'WRONG_ANSWER')
        if verdict != "OK":
            continue

        try:
            db_cursor = db.cursor()
            db_cursor.execute('''
                INSERT INTO submission
                (id_user, problem_key, problem_rate, creation_time)
                VALUES(%s, %s, %s, %s)
            ''', [id_user, problem_key, problem_rate, creation_time])
            db.commit()
        except Exception as e:
            if (now_date - creation_time).total_seconds() >= 60 * 60 * 24 * 7:
                db_cursor = db.cursor()
                db_cursor.execute('''
                    UPDATE submission
                    SET problem_rate = %s
                    WHERE problem_key = %s
                ''', [problem_rate, problem_key])
                db.commit()

    db_cursor = db.cursor()
    db_cursor.execute('''
        UPDATE user
        SET last_synced_at = NOW()
        WHERE id_user = %s
    ''', [id_user])
    db.commit()

    return {
        'status': 'success',
        'message': 'complete sync'
    }

async def get_allowed_requests(user_handle):
    position = 1000000
    current_date = datetime.now()
    year = current_date.year
    month = current_date.month 
    request_body = GetRanksRequest(id_discord_user = None, year = year, month = month)
    ranks = await get_ranks(request_body)
    for rank in ranks:
        if rank['handle'] == user_handle:
            position = rank['rank']
            break
    if position <= 3:
        return 5
    elif position <= 10:
        return 3
    else:
        return 1                

def get_time_needed_formatted(seconds_needed_for_next_request):
    if seconds_needed_for_next_request >= 60 * 60 * 24:
        return f"{seconds_needed_for_next_request // 60 // 60 // 24} days ;("
    if seconds_needed_for_next_request >= 60 * 60:
        return f"{seconds_needed_for_next_request // 60 // 60 } hours :)"
    return f"{seconds_needed_for_next_request // 60} minutes :D"

@app.post("/get-score")
async def get_score(msg: GetScoreRequest):
    db = get_db_connection()
    db_cursor = db.cursor()
    db_cursor.execute(f'''
        SELECT id_user, display_name, id_discord_user, handle
        FROM user
        WHERE handle = '{msg.handle}'
    ''')
    rows = db_cursor.fetchall()
    if len(rows) == 0:
        return {
            'status': 'failed',
            'message': 'user not found'
        }

    id_user = rows[0][0]
    display_name = rows[0][1]
    id_discord_user = rows[0][2]
    user_handle = rows[0][3]

    if msg.id_discord_user is not None and msg.id_discord_user != id_discord_user:
        return {
            'status': 'failed',
            'message': 'user not found'
        }

    if msg.id_discord_user is not None:
        db_cursor = db.cursor()
        db_cursor.execute(f'''
            SELECT created_at 
            FROM user_call
            WHERE id_user = '{id_user}' AND TIMESTAMPDIFF(SECOND, NOW(),  created_at) <= 7 * 60 * 60 * 24
            ORDER BY created_at
        ''')
        rows = db_cursor.fetchall()

        number_of_allowed_requests = await get_allowed_requests(user_handle = user_handle)
        if len(rows) >= number_of_allowed_requests:
            seconds_needed_for_next_request = int((rows[0][0] + timedelta(days = 7) - datetime.now()).total_seconds())
            return{
                'status' :'failed',
                'message' : f'current limit exceeded, you will be able to request again after {get_time_needed_formatted(seconds_needed_for_next_request)}'
            }
    db_cursor = db.cursor()
    db_cursor.execute(f'''
        SELECT problem_rate
        FROM submission
        WHERE
            id_user = '{id_user}' AND
            creation_time >= '{msg.from_date}' AND
            creation_time <= '{msg.to_date}'
    ''')
    rows = db_cursor.fetchall()

    scores = {
        0: 0,
        800: 10, 900: 10, 1000: 10,
        1100: 25, 1200: 25, 1300: 25,
        1400: 50, 1500: 50,
        1600: 75, 1700: 75, 1800: 75,
        1900: 100, 2000: 100, 2100: 100, 2200: 100,
        2300: 100, 2400: 100, 2500: 100, 2600: 100,
        2700: 100, 2800: 100, 2900: 100, 3000: 100,
        3100: 100, 3200: 100, 3300: 100, 3400: 100
    }

    score = 0
    solved = 0
    problems = {}
    for row in rows:
        problem_rate = row[0]
        solved += 1
        score += scores[problem_rate]
        if problem_rate in problems:
            problems[problem_rate] += 1
        else:
            problems[problem_rate] = 1

    if msg.id_discord_user is not None: 
        db_cursor = db.cursor()
        db_cursor.execute('''
            INSERT INTO user_call
            (id_user)
            VALUES(%s)
        ''', [id_user])
        db.commit()

    return {
        'score': score,
        'solved': solved,
        'problems': problems
    }

@app.post("/get-ranks")
async def get_ranks(msg: GetRanksRequest):
    if msg.id_discord_user is not None:
        db = get_db_connection()
        db_cursor = db.cursor()
        db_cursor.execute(f'''
            SELECT handle, id_user
            FROM user
            WHERE id_discord_user = '{msg.id_discord_user}'
        ''')
    rows = db_cursor.fetchall()
    if len(rows) == 0:
        return {
            'status': 'failed',
            'message': 'user not found'
        }

    user_handle = rows[0][0]
    id_user = rows[0][1]

    db_cursor = db.cursor()
    db_cursor.execute(f'''
        SELECT created_at 
        FROM user_call
        WHERE id_user = '{id_user}' AND TIMESTAMPDIFF(SECOND, NOW(),  created_at) <= 7 * 60 * 60 * 24
        ORDER BY created_at
    ''')
    rows = db_cursor.fetchall()
    
    number_of_allowed_requests = await get_allowed_requests(user_handle = user_handle)
    if len(rows) >= number_of_allowed_requests:
        seconds_needed_for_next_request = int((rows[0][0] + timedelta(days = 7) - datetime.now()).total_seconds())
        return{
            'status' :'failed',
            'message' : f'current limit exceeded, you will be able to request again after {get_time_needed_formatted(seconds_needed_for_next_request)}'
        }

    users = await get_users()
    from_date = datetime(msg.year, msg.month, 1, 0, 0, 0)
    to_date = datetime(msg.year, msg.month + 1, 1, 0, 0, 0) + timedelta(seconds = -1)

    result = []
    
    for user in users['users']:
        request_body = GetScoreRequest(handle=user['handle'], id_discord_user=None, from_date=from_date, to_date=to_date)
        score = await get_score(request_body)
        result.append({
            'handle': user['handle'],
            'display_name': user['display_name'],
            'image': user['image'],
            'solved': score['solved'],
            'score': score['score']
        })
    
    sorted_result = sorted(result, key=lambda d: d['score'], reverse=True) 
    rank = 1
    for item in sorted_result:
        item['rank'] = rank
        rank += 1

    if msg.id_discord_user is not None:
        db_cursor = db.cursor()
        db_cursor.execute('''
            INSERT INTO user_call
            (id_user)
            VALUES(%s)
        ''', [id_user])
        db.commit()

    return sorted_result

@app.post("/get-tier")
async def get_tier(msg:getTierRequest):
    db = get_db_connection()
    db_cursor = db.cursor()
    db_cursor.execute(f'''
        SELECT display_name, handle, image
        FROM user
        WHERE handle = '{msg.handle}'
    ''')
    rows = db_cursor.fetchall()
    if len(rows) == 0:
        return {
            'status': 'failed',
            'message': 'user not found'
        }

    user_name = rows[0][0]
    handle = rows[0][1]
    user_image = rows[0][2]

    #will figure from_date later and change it
    from_date = datetime.now()
    to_date = datetime.now()
    request_body = GetScoreRequest(handle=user['handle'], id_discord_user=None, from_date=from_date, to_date=to_date)
    score = await get_score(request_body)
    #the scoring below is teporary at the moment
    tiers = {
        0: "Iron",
        350: "Bronze",
        1250: "Silver",
        4000: "Gold",
        10000: "Platinum",
        17500: "Diamond",
        25000: "Master",
        30000: "Grand Master",
        40000: "Legendary"
    }
    tier =""
    temp = tiers.keys
    for t in temp:
        if(score >= t):
            tier = tiers[t]
    return{
        'tier': tier,
        'total score': score,
        'name': user_name,
        'handle': handle,
        'image': user_image
    }
    
    

@app.post("/TierRank")
async def tier_rank(msg: getTierRank):
    db = get_db_connection()
    db_cursor = db.cursor()
    db_cursor.execute(f'''
        SELECT handle, id_user
        FROM user
    ''')
    useres =  db_cursor.fetchall()
    if(len(users) == 0):
        return{
            'status': 'failed',
            'message': 'no users in the database'
        }
    result = []
    for user in users:
            #must edit on from_date here also
            request_body = getTierRequest(handle = user[0][0],from_date = datetime.now(), to_date= datetime.now())
            result.append(get_tier(request_body))
    sorted_result = sorted(result, key=lambda d:d['score'],reverse = true)
    rank = 1
    for item in sorted_result:
        item['rank'] = rank
        rank += 1
    return sorted_result
    
@app.post("/publish-html-content")
async def publish_html_content(msg: PublishHtmlContentRequest):
    code = f'P{str(random.randint(100000000, 999999999))}'
    db = get_db_connection()
    db_cursor = db.cursor()
    db_cursor.execute('''
        INSERT INTO html_content
        (code, html)
        VALUES(%s, %s)
    ''', [code, msg.html])
    db.commit()
    
    return {
        'status': 'success',
        'code': code
    }

@app.get("/p/{code}")
async def get_html_content(code: str):
    db = get_db_connection()
    db_cursor = db.cursor()
    db_cursor.execute(f'''
        SELECT html
        FROM html_content
        WHERE code = '{code}'
    ''')
    rows = db_cursor.fetchall()
    if len(rows) == 0:
        return HTMLResponse(content='404! page not found', status_code=200)
    return HTMLResponse(content=rows[0][0], status_code=200)

