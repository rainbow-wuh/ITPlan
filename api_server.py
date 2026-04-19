"""
WUH-IT-Plan — Flask REST API Server
รัน: python api_server.py
เข้าถึง: http://localhost:5001
"""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import psycopg2, json, os
from datetime import datetime
from functools import wraps

app = Flask(__name__, static_folder='public')
CORS(app)

# Supabase PostgreSQL Connection
DB_URL = os.environ.get('DATABASE_URL') or 'postgresql://postgres:YOUR-PASSWORD@db.ivesmxwavwodhmdbwfpx.supabase.co:5432/postgres'

def get_db():
    try:
        conn = psycopg2.connect(DB_URL)
        return conn
    except Exception as e:
        print(f"DB Connection Error: {e}")
        raise
    conn = psycopg2.connect(DB_URL)
    conn.row_factory = psycopg2.row_factory
    return conn

def rows_to_list(rows):
    return [dict(r) for r in rows]

def log_action(user, action, detail=''):
    conn = get_db()
    conn.execute("INSERT INTO logs (user,action,detail) VALUES (%s,%s,%s)",
                 (user, action, detail))
    conn.commit(); conn.close()

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    return response

@app.route('/api/health')
def health():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM projects")
        count = cur.fetchone()[0]
        conn.close()
        return jsonify({'status': 'ok', 'projects_count': count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ══════════════════════════════════════════════════
# PROJECTS
# ══════════════════════════════════════════════════════════
@app.route('/api/projects', methods=['GET'])
def get_projects():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id,section,name,full_name,it,po,dept,status,status_raw,size,manday,approved,hold,team,months,y2569,y2570,y2571,progress,budget,gstart,gend FROM projects ORDER BY id")
        rows = cur.fetchall()
        result = []
        for r in rows:
            p = {
                'id': r[0], 'section': r[1], 'name': r[2], 'full_name': r[3],
                'it': r[4], 'po': r[5], 'dept': r[6], 'status': r[7],
                'status_raw': r[8], 'size': r[9], 'manday': r[10],
                'approved': r[11], 'hold': r[12], 'team': json.loads(r[13] or '[]'),
                'months': json.loads(r[14] or '[]'), 'y2569': bool(r[15]),
                'y2570': bool(r[16]), 'y2571': bool(r[17]),
                'progress': r[18], 'budget': r[19], 'gstart': r[20], 'gend': r[21]
            }
            result.append(p)
        conn.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects', methods=['POST'])
def add_project():
    d = request.json
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''INSERT INTO projects
        (section,name,full_name,it,po,dept,status,status_raw,size,
         manday,approved,hold,team,months,y2569,y2570,y2571,
         progress,budget,gstart,gend)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING id''', (
        d.get('section',''), d.get('name',''), d.get('full_name',''),
        d.get('it',''), d.get('po',''), d.get('dept',''),
        d.get('status','todo'), d.get('status_raw',''),
        d.get('size',''), str(d.get('manday','')),
        d.get('approved',''), d.get('hold',''),
        json.dumps(d.get('team',[])),
        json.dumps(d.get('months',[])),
        1 if d.get('y2569') else 0,
        1 if d.get('y2570') else 0,
        1 if d.get('y2571') else 0,
        d.get('progress',''), str(d.get('budget','')),
        d.get('gstart',0), d.get('gend',0)
    ))
    new_id = cur.fetchone()[0]
    conn.commit()
    conn.close()
    log_action(d.get('_user','system'), 'ADD_PROJECT', d.get('name',''))
    return jsonify({'id': new_id, 'ok': True})

@app.route('/api/projects/<int:pid>', methods=['PUT'])
def update_project(pid):
    d = request.json
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''UPDATE projects SET
        section=%s, name=%s, full_name=%s, it=%s, po=%s, dept=%s,
        status=%s, status_raw=%s, size=%s, manday=%s, approved=%s, hold=%s,
        team=%s, months=%s, y2569=%s, y2570=%s, y2571=%s,
        progress=%s, budget=%s, gstart=%s, gend=%s,
        updated_at=NOW()
        WHERE id=%s''', (
        d.get('section',''), d.get('name',''), d.get('full_name',''),
        d.get('it',''), d.get('po',''), d.get('dept',''),
        d.get('status','todo'), d.get('status_raw',''),
        d.get('size',''), str(d.get('manday','')),
        d.get('approved',''), d.get('hold',''),
        json.dumps(d.get('team',[])),
        json.dumps(d.get('months',[])),
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
    cur = conn.cursor()
    cur.execute("DELETE FROM projects WHERE id=%s", (pid,))
    conn.commit(); conn.close()
    log_action('system', 'DELETE_PROJECT', str(pid))
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
    import os
    public_path = os.path.join(os.path.dirname(__file__), 'public', 'index.html')
    if os.path.exists(public_path):
        return send_from_directory('public', 'index.html')
    return f"public/index.html not found at {public_path}", 404

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('public', filename)

if __name__ == '__main__':
    print("=" * 50)
    print("  WUH-IT-Plan API Server")
    print("  http://localhost:5001")
    print("=" * 50)
    try:
        conn = get_db()
        conn.close()
        print("✅ Database connected!")
    except Exception as e:
        print(f"❌ Database error: {e}")
    app.run(host='0.0.0.0', port=5001, debug=True)
