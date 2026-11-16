import os, hmac, hashlib, time, json
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, make_response
import psycopg
from psycopg.rows import dict_row

BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__)
SECRET = os.getenv('SECRET_KEY', '')
USERNAME = os.getenv('PORTAL_USERNAME', '')
PASSWORD = os.getenv('PORTAL_PASSWORD', '')
DATABASE_URL = os.getenv('DATABASE_URL', '')
COOKIE_NAME = 'portal_auth'
COOKIE_MAX_AGE = 60 * 60 * 24 * 14


def db():
    if not DATABASE_URL:
        raise RuntimeError('DATABASE_URL belum diatur. Hubungkan database PostgreSQL (Neon) di Vercel.')
    conn = psycopg.connect(DATABASE_URL, row_factory=dict_row, connect_timeout=10)
    with conn.cursor() as cur:
        cur.execute('''CREATE TABLE IF NOT EXISTS portal_data (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            data JSONB NOT NULL DEFAULT '{"items":[]}'::jsonb,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )''')
        cur.execute("INSERT INTO portal_data (id, data) VALUES (1, '{\"items\":[]}') ON CONFLICT (id) DO NOTHING")
    conn.commit()
    return conn


def make_auth_token():
    expiry = str(int(time.time()) + COOKIE_MAX_AGE)
    payload = 'bunga:' + expiry
    signature = hmac.new(SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return payload + ':' + signature


def is_authenticated():
    if not SECRET:
        return False
    token = request.cookies.get(COOKIE_NAME, '')
    try:
        user, expiry, signature = token.split(':', 2)
        payload = user + ':' + expiry
        expected = hmac.new(SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
        return user == 'bunga' and int(expiry) > int(time.time()) and hmac.compare_digest(signature, expected)
    except Exception:
        return False


def require_auth():
    if not is_authenticated():
        return jsonify({'error': 'Sesi login berakhir. Silakan masuk kembali.'}), 401
    return None


@app.get('/')
def home():
    return send_from_directory(BASE_DIR, 'index.html')


@app.get('/health')
def health():
    return jsonify({'ok': True, 'service': 'Portal Tugas'})


@app.post('/api/login')
def login():
    if not USERNAME or not PASSWORD or not SECRET:
        return jsonify({'error': 'Atur PORTAL_USERNAME, PORTAL_PASSWORD, dan SECRET_KEY di Environment Variables Vercel.'}), 500
    body = request.get_json(silent=True) or {}
    if hmac.compare_digest(str(body.get('username', '')), USERNAME) and hmac.compare_digest(str(body.get('password', '')), PASSWORD):
        response = make_response(jsonify({'ok': True}))
        response.set_cookie(COOKIE_NAME, make_auth_token(), max_age=COOKIE_MAX_AGE, httponly=True, secure=True, samesite='Lax', path='/')
        return response
    return jsonify({'error': 'Username atau password tidak sesuai.'}), 401


@app.post('/api/logout')
def logout():
    response = make_response(jsonify({'ok': True}))
    response.delete_cookie(COOKIE_NAME, path='/')
    return response


@app.get('/api/session')
def session_status():
    return jsonify({'authenticated': is_authenticated()})


@app.get('/api/data')
def get_data():
    denied = require_auth()
    if denied: return denied
    try:
        with db() as conn:
            row = conn.execute('SELECT data FROM portal_data WHERE id=1').fetchone()
        return jsonify({'data': row['data'] if row else {'items': []}, 'empty': not bool((row or {}).get('data', {}).get('items'))})
    except Exception as exc:
        app.logger.exception('Gagal membaca database')
        return jsonify({'error': 'Database belum siap atau DATABASE_URL salah: ' + str(exc)}), 500


@app.put('/api/data')
def put_data():
    denied = require_auth()
    if denied: return denied
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or not isinstance(payload.get('items', []), list):
        return jsonify({'error': 'Format data tidak valid.'}), 400
    # Identitas di server dikunci; data tugas disimpan sebagai JSONB.
    payload.update({'universitas': 'Universitas Muhammadiyah Cirebon', 'nim': '240511170', 'nama': 'Bunga Indah Lestari', 'kelas': 'TI24D'})
    try:
        with db() as conn:
            conn.execute('''INSERT INTO portal_data (id, data, updated_at) VALUES (1, %s::jsonb, NOW())
                ON CONFLICT (id) DO UPDATE SET data=EXCLUDED.data, updated_at=NOW()''', (json.dumps(payload, ensure_ascii=False),))
        return jsonify({'ok': True})
    except Exception as exc:
        app.logger.exception('Gagal menyimpan database')
        return jsonify({'error': 'Data gagal disimpan: ' + str(exc)}), 500

@app.post('/api/blob-upload')
def blob_upload():
    denied = require_auth()
    if denied:
        return denied
    try:
        body = request.get_json(silent=True) or {}
        json_response = handle_upload(
            body=body,
            request=request,
            on_before_generate_token=lambda pathname, client_payload, multipart: {
                'maximum_size_in_bytes': 1024 * 1024 * 1024,
                'add_random_suffix': True,
            },
            on_upload_completed=lambda blob, token_payload: None,
        )
        return jsonify(json_response)
    except Exception as exc:
        return jsonify({'error': str(exc)}), 400


# Vercel menggunakan objek WSGI `app` ini.

# Vercel menggunakan objek WSGI `app` ini.
