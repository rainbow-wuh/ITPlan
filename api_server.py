"""
WUH-IT-Plan — Flask REST API Server
รัน: python api_server.py
เข้าถึง: http://localhost:5001
"""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3, json, os
from datetime import datetime
from functools import wraps

app = Flask(__name__)
CORS(app)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    return response

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'db_exists': os.path.exists(DB_PATH)})

DB_PATH = os.path.join(os.path.dirname(__file__), 'wuh_it_plan.db')
HTML_DIR = os.path.dirname(__file__)

def init_db():
    """สร้าง tables อัตโนมัติถ้ายังไม่มี"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS projects (
        id          INTEGER PRIMARY KEY,
        section     TEXT    DEFAULT '',
        name        TEXT    NOT NULL,
        full_name   TEXT    DEFAULT '',
        it          TEXT    DEFAULT '',
        po          TEXT    DEFAULT '',
        dept        TEXT    DEFAULT '',
        status      TEXT    DEFAULT 'todo',
        status_raw  TEXT    DEFAULT '',
        size        TEXT    DEFAULT '',
        manday      TEXT    DEFAULT '',
        approved    TEXT    DEFAULT '',
        hold        TEXT    DEFAULT '',
        team        TEXT    DEFAULT '[]',
        months      TEXT    DEFAULT '[]',
        y2569       INTEGER DEFAULT 0,
        y2570       INTEGER DEFAULT 0,
        y2571       INTEGER DEFAULT 0,
        progress    TEXT    DEFAULT '',
        budget     TEXT    DEFAULT '',
        gstart      INTEGER DEFAULT 0,
        gend        INTEGER DEFAULT 0,
        created_at  TEXT    DEFAULT (datetime('now','localtime')),
        updated_at  TEXT    DEFAULT (datetime('now','localtime'))
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS master_it (
        id          INTEGER PRIMARY KEY,
        name        TEXT    NOT NULL,
        nickname    TEXT    DEFAULT '',
        role        TEXT    DEFAULT '',
        group_name  TEXT    DEFAULT '',
        phone       TEXT    DEFAULT '',
        email       TEXT    DEFAULT '',
        desc        TEXT    DEFAULT '',
        dept        TEXT    DEFAULT '',
        sort_order  INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS master_section (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT    UNIQUE NOT NULL,
        note        TEXT    DEFAULT '',
        sort_order  INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS master_po (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT    UNIQUE NOT NULL,
        dept        TEXT    DEFAULT '',
        contact     TEXT    DEFAULT ''
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS master_dept (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT    UNIQUE NOT NULL,
        group_name  TEXT    DEFAULT '',
        note        TEXT    DEFAULT '',
        sort_order  INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS master_size (
        key         TEXT    PRIMARY KEY,
        label       TEXT    DEFAULT '',
        bg          TEXT    DEFAULT '#e0f2fe',
        color      TEXT    DEFAULT '#0369a1',
        manday      INTEGER DEFAULT 0,
        note        TEXT    DEFAULT '',
        sort_order  INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS fiscal_years (
        key         TEXT    PRIMARY KEY,
        label       TEXT    NOT NULL,
        sort_order  INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS it_groups (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT    UNIQUE NOT NULL,
        sort_order  INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS performance (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id  INTEGER REFERENCES projects(id) ON DELETE CASCADE,
        year_key    TEXT    NOT NULL,
        target      REAL    DEFAULT 0,
        yearly      REAL    DEFAULT 0,
        m1          REAL    DEFAULT 0,
        m2          REAL    DEFAULT 0,
        m3          REAL    DEFAULT 0,
        m4          REAL    DEFAULT 0,
        m5          REAL    DEFAULT 0,
        m6          REAL    DEFAULT 0,
        m7          REAL    DEFAULT 0,
        m8          REAL    DEFAULT 0,
        m9          REAL    DEFAULT 0,
        m10         REAL    DEFAULT 0,
        m11         REAL    DEFAULT 0,
        m12         REAL    DEFAULT 0,
        updated_at  TEXT    DEFAULT (datetime('now','localtime')),
        UNIQUE(project_id, year_key)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        username    TEXT    UNIQUE NOT NULL,
        password    TEXT    NOT NULL,
        name        TEXT    DEFAULT '',
        role        TEXT    DEFAULT 'viewer',
        note        TEXT    DEFAULT '',
        created_at  TEXT    DEFAULT (datetime('now','localtime'))
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS subtasks (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id  INTEGER REFERENCES projects(id) ON DELETE CASCADE,
        name        TEXT    NOT NULL,
        status      TEXT    DEFAULT 'todo',
        assignee    TEXT    DEFAULT '',
        due_date    TEXT    DEFAULT '',
        note        TEXT    DEFAULT ''
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS logs (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user        TEXT    DEFAULT '',
        action      TEXT    NOT NULL,
        detail      TEXT    DEFAULT '',
        created_at  TEXT    DEFAULT (datetime('now','localtime'))
    )''')
    conn.commit()
    conn.close()

if not os.path.exists(DB_PATH):
    init_db()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def rows_to_list(rows):
    return [dict(r) for r in rows]

def log_action(user, action, detail=''):
    conn = get_db()
    conn.execute("INSERT INTO logs (user,action,detail) VALUES (?,?,?)",
                 (user, action, detail))
    conn.commit(); conn.close()

# ══════════════════════════════════════════════════════════
# PROJECTS
# ══════════════════════════════════════════════════════════
@app.route('/api/projects', methods=['GET'])
def get_projects():
    try:
        conn = get_db()
        rows = conn.execute("SELECT * FROM projects ORDER BY id").fetchall()
        result = []
        for r in rows:
            p = dict(r)
            p['team']   = json.loads(p.get('team','[]') or '[]')
            p['months'] = json.loads(p.get('months','[]') or '[]')
            p['y2569']  = bool(p.get('y2569',0))
            p['y2570']  = bool(p.get('y2570',0))
            p['y2571']  = bool(p.get('y2571',0))
            result.append(p)
        conn.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects', methods=['POST'])
def add_project():
    d = request.json
    conn = get_db()
    cur = conn.execute('''INSERT INTO projects
        (section,name,full_name,it,po,dept,status,status_raw,size,
         manday,approved,hold,team,months,y2569,y2570,y2571,
         progress,budget,gstart,gend)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (
        d.get('section',''), d.get('name',''), d.get('full_name',''),
        d.get('it',''), d.get('po',''), d.get('dept',''),
        d.get('status','todo'), d.get('status_raw',''),
        d.get('size',''), str(d.get('manday','')),
        d.get('approved',''), d.get('hold',''),
        json.dumps(d.get('team',[]), ensure_ascii=False),
        json.dumps(d.get('months',[]), ensure_ascii=False),
        1 if d.get('y2569') else 0,
        1 if d.get('y2570') else 0,
        1 if d.get('y2571') else 0,
        d.get('progress',''), str(d.get('budget','')),
        d.get('gstart',0), d.get('gend',0)
    ))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    log_action(d.get('_user','system'), 'ADD_PROJECT', d.get('name',''))
    return jsonify({'id': new_id, 'ok': True})

@app.route('/api/projects/<int:pid>', methods=['PUT'])
def update_project(pid):
    d = request.json
    conn = get_db()
    conn.execute('''UPDATE projects SET
        section=?, name=?, full_name=?, it=?, po=?, dept=?,
        status=?, status_raw=?, size=?, manday=?, approved=?, hold=?,
        team=?, months=?, y2569=?, y2570=?, y2571=?,
        progress=?, budget=?, gstart=?, gend=?,
        updated_at=datetime('now','localtime')
        WHERE id=?''', (
        d.get('section',''), d.get('name',''), d.get('full_name',''),
        d.get('it',''), d.get('po',''), d.get('dept',''),
        d.get('status','todo'), d.get('status_raw',''),
        d.get('size',''), str(d.get('manday','')),
        d.get('approved',''), d.get('hold',''),
        json.dumps(d.get('team',[]), ensure_ascii=False),
        json.dumps(d.get('months',[]), ensure_ascii=False),
        1 if d.get('y2569') else 0,
        1 if d.get('y2570') else 0,
        1 if d.get('y2571') else 0,
        d.get('progress',''), str(d.get('budget','')),
        d.get('gstart',0), d.get('gend',0), pid
    ))
    conn.commit(); conn.close()
    log_action(d.get('_user','system'), 'UPDATE_PROJECT', str(pid))
    return jsonify({'ok': True})

@app.route('/api/projects/<int:pid>', methods=['DELETE'])
def delete_project(pid):
    conn = get_db()
    conn.execute("DELETE FROM projects WHERE id=?", (pid,))
    conn.commit(); conn.close()
    log_action('system', 'DELETE_PROJECT', str(pid))
    return jsonify({'ok': True})

# ══════════════════════════════════════════════════════════
# MASTER IT
# ══════════════════════════════════════════════════════════
@app.route('/api/master/it', methods=['GET'])
def get_master_it():
    conn = get_db()
    rows = conn.execute("SELECT * FROM master_it ORDER BY sort_order, id").fetchall()
    conn.close()
    return jsonify(rows_to_list(rows))

@app.route('/api/master/it', methods=['POST'])
def save_master_it():
    """รับ array ทั้งหมด แล้ว replace"""
    data = request.json
    conn = get_db()
    conn.execute("DELETE FROM master_it")
    for i, x in enumerate(data):
        conn.execute('''INSERT INTO master_it
            (id,name,nickname,role,group_name,phone,email,desc,dept,sort_order)
            VALUES (?,?,?,?,?,?,?,?,?,?)''', (
            x.get('id', i+1), x.get('name',''),
            x.get('nickname',''), x.get('role',''),
            x.get('group',''), x.get('phone',''),
            x.get('email',''), x.get('desc',''),
            x.get('dept',''), i
        ))
    conn.commit(); conn.close()
    return jsonify({'ok': True})

# ══════════════════════════════════════════════════════════
# MASTER DEPT
# ══════════════════════════════════════════════════════════
@app.route('/api/master/dept', methods=['GET'])
def get_master_dept():
    conn = get_db()
    rows = conn.execute("SELECT * FROM master_dept ORDER BY sort_order, name").fetchall()
    conn.close()
    return jsonify(rows_to_list(rows))

@app.route('/api/master/dept', methods=['POST'])
def save_master_dept():
    data = request.json
    conn = get_db()
    conn.execute("DELETE FROM master_dept")
    for i, x in enumerate(data):
        conn.execute("INSERT INTO master_dept (name,group_name,note,sort_order) VALUES (?,?,?,?)",
                     (x.get('name',''), x.get('group',''), x.get('note',''), i))
    conn.commit(); conn.close()
    return jsonify({'ok': True})

# ══════════════════════════════════════════════════════════
# MASTER SIZE
# ══════════════════════════════════════════════════════════
@app.route('/api/master/size', methods=['GET'])
def get_master_size():
    conn = get_db()
    rows = conn.execute("SELECT * FROM master_size ORDER BY sort_order").fetchall()
    conn.close()
    return jsonify(rows_to_list(rows))

@app.route('/api/master/size', methods=['POST'])
def save_master_size():
    data = request.json
    conn = get_db()
    conn.execute("DELETE FROM master_size")
    for i, x in enumerate(data):
        conn.execute("INSERT INTO master_size VALUES (?,?,?,?,?,?,?)",
                     (x['key'], x.get('label',''), x.get('bg','#e0f2fe'),
                      x.get('color','#0369a1'), x.get('manday',0), x.get('note',''), i))
    conn.commit(); conn.close()
    return jsonify({'ok': True})

# ══════════════════════════════════════════════════════════
# PERFORMANCE
# ══════════════════════════════════════════════════════════
@app.route('/api/performance/<int:pid>/<year_key>', methods=['GET'])
def get_performance(pid, year_key):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM performance WHERE project_id=? AND year_key=?", (pid, year_key)
    ).fetchone()
    conn.close()
    if not row: return jsonify({})
    d = dict(row)
    d['months'] = {f'm{i}': d.pop(f'm{i}', 0) for i in range(1,13)}
    return jsonify(d)

@app.route('/api/performance/<int:pid>/<year_key>', methods=['POST'])
def save_performance(pid, year_key):
    d = request.json
    months = d.get('months', {})
    conn = get_db()
    conn.execute('''INSERT INTO performance
        (project_id,year_key,target,yearly,m1,m2,m3,m4,m5,m6,m7,m8,m9,m10,m11,m12,updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now','localtime'))
        ON CONFLICT(project_id,year_key) DO UPDATE SET
        target=excluded.target, yearly=excluded.yearly,
        m1=excluded.m1, m2=excluded.m2, m3=excluded.m3, m4=excluded.m4,
        m5=excluded.m5, m6=excluded.m6, m7=excluded.m7, m8=excluded.m8,
        m9=excluded.m9, m10=excluded.m10, m11=excluded.m11, m12=excluded.m12,
        updated_at=excluded.updated_at''', (
        pid, year_key,
        d.get('target',0), d.get('yearly',0),
        months.get('m1',0), months.get('m2',0), months.get('m3',0),
        months.get('m4',0), months.get('m5',0), months.get('m6',0),
        months.get('m7',0), months.get('m8',0), months.get('m9',0),
        months.get('m10',0), months.get('m11',0), months.get('m12',0)
    ))
    conn.commit(); conn.close()
    return jsonify({'ok': True})

# ══════════════════════════════════════════════════════════
# USERS (Auth)
# ══════════════════════════════════════════════════════════
@app.route('/api/users', methods=['GET'])
def get_users():
    conn = get_db()
    rows = conn.execute("SELECT id,username,name,role,note FROM users").fetchall()
    conn.close()
    return jsonify(rows_to_list(rows))

@app.route('/api/users', methods=['POST'])
def save_users():
    data = request.json  # array of users
    conn = get_db()
    conn.execute("DELETE FROM users")
    for u in data:
        conn.execute("INSERT INTO users (username,password,name,role,note) VALUES (?,?,?,?,?)",
                     (u['username'], u['password'], u.get('name',''), u.get('role','viewer'), u.get('note','')))
    conn.commit(); conn.close()
    return jsonify({'ok': True})

# ══════════════════════════════════════════════════════════
# FISCAL YEARS
# ══════════════════════════════════════════════════════════
@app.route('/api/fiscal', methods=['GET'])
def get_fiscal():
    conn = get_db()
    rows = conn.execute("SELECT * FROM fiscal_years ORDER BY sort_order").fetchall()
    conn.close()
    return jsonify(rows_to_list(rows))

@app.route('/api/fiscal', methods=['POST'])
def save_fiscal():
    data = request.json
    conn = get_db()
    conn.execute("DELETE FROM fiscal_years")
    for i, f in enumerate(data):
        conn.execute("INSERT INTO fiscal_years VALUES (?,?,?)", (f['key'], f.get('label', f['key']), i))
    conn.commit(); conn.close()
    return jsonify({'ok': True})

# ══════════════════════════════════════════════════════════
# IT GROUPS
# ══════════════════════════════════════════════════════════
@app.route('/api/it-groups', methods=['GET'])
def get_it_groups():
    conn = get_db()
    rows = conn.execute("SELECT * FROM it_groups ORDER BY sort_order").fetchall()
    conn.close()
    return jsonify(rows_to_list(rows))

@app.route('/api/it-groups', methods=['POST'])
def save_it_groups():
    data = request.json
    conn = get_db()
    conn.execute("DELETE FROM it_groups")
    for i, g in enumerate(data):
        conn.execute("INSERT INTO it_groups (name,sort_order) VALUES (?,?)", (g['name'], i))
    conn.commit(); conn.close()
    return jsonify({'ok': True})

# ══════════════════════════════════════════════════════════
# LOGS
# ══════════════════════════════════════════════════════════
@app.route('/api/logs', methods=['GET'])
def get_logs():
    conn = get_db()
    rows = conn.execute("SELECT * FROM logs ORDER BY id DESC LIMIT 500").fetchall()
    conn.close()
    return jsonify(rows_to_list(rows))

# ══════════════════════════════════════════════════════════
# SERVE HTML
# ══════════════════════════════════════════════════════════
@app.route('/')
def serve_html():
    return send_from_directory(HTML_DIR, 'WUH-IT-Plan.html')

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'db': DB_PATH,
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})

if __name__ == '__main__':
    print("=" * 50)
    print("  WUH-IT-Plan API Server")
    print("  http://localhost:5001")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5001, debug=True)
