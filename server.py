"""
server.py — Backend API สำหรับระบบแผนการพัฒนา IT WU-HIS
ใช้ Flask + SQLite  |  Port: 5001
รัน: python server.py
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

DB_FILE = "it_plan.db"

# ============================================================
# เริ่มต้น Database
# ============================================================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            section_name  TEXT,
            name          TEXT NOT NULL,
            full_name     TEXT,
            it_owner      TEXT,
            product_owner TEXT,
            department    TEXT,
            status        TEXT DEFAULT 'todo',
            status_raw    TEXT,
            size          TEXT,
            manday        TEXT,
            budget        TEXT,
            approved      TEXT,
            hold          TEXT,
            progress      TEXT,
            team          TEXT,
            y2569         INTEGER DEFAULT 0,
            y2570         INTEGER DEFAULT 0,
            y2571         INTEGER DEFAULT 0,
            gantt_start   INTEGER DEFAULT 0,
            gantt_end     INTEGER DEFAULT 0,
            created_at    TEXT DEFAULT (datetime('now','localtime')),
            updated_at    TEXT DEFAULT (datetime('now','localtime'))
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS subtasks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id  INTEGER NOT NULL,
            name        TEXT NOT NULL,
            detail      TEXT,
            it_owner    TEXT,
            status      TEXT DEFAULT 'todo',
            m_start     INTEGER DEFAULT 0,
            m_end       INTEGER DEFAULT 0,
            manday      INTEGER,
            priority    TEXT DEFAULT 'normal',
            note        TEXT,
            created_at  TEXT DEFAULT (datetime('now','localtime')),
            updated_at  TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()
    print(f"✅ Database พร้อม: {DB_FILE}")


def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def row_to_dict(row):
    d = dict(row)
    if d.get("team"):
        try:
            d["team"] = json.loads(d["team"])
        except Exception:
            d["team"] = []
    else:
        d["team"] = []
    return d


# ── Stats (ใช้ตรวจสอบว่า backend online) ──
@app.route("/api/stats")
def stats():
    conn = get_conn()
    total     = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
    done      = conn.execute("SELECT COUNT(*) FROM projects WHERE status='done'").fetchone()[0]
    inprog    = conn.execute("SELECT COUNT(*) FROM projects WHERE status='inprog'").fetchone()[0]
    todo      = conn.execute("SELECT COUNT(*) FROM projects WHERE status='todo'").fetchone()[0]
    hold      = conn.execute("SELECT COUNT(*) FROM projects WHERE hold != '' AND hold IS NOT NULL").fetchone()[0]
    sub_total = conn.execute("SELECT COUNT(*) FROM subtasks").fetchone()[0]
    conn.close()
    return jsonify({"total": total, "done": done, "inprog": inprog,
                    "todo": todo, "hold": hold, "subtasks": sub_total,
                    "db_file": DB_FILE,
                    "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M")})


# ── PROJECTS ──
@app.route("/api/projects", methods=["GET"])
def get_projects():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM projects ORDER BY id").fetchall()
    conn.close()
    return jsonify([row_to_dict(r) for r in rows])

@app.route("/api/projects/<int:pid>", methods=["GET"])
def get_project(pid):
    conn = get_conn()
    row = conn.execute("SELECT * FROM projects WHERE id=?", (pid,)).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "ไม่พบโครงการ"}), 404
    return jsonify(row_to_dict(row))

@app.route("/api/projects", methods=["POST"])
def add_project():
    data = request.get_json()
    team_json = json.dumps(data.get("team", []), ensure_ascii=False)
    conn = get_conn()
    cur = conn.execute("""
        INSERT INTO projects
          (section_name,name,full_name,it_owner,product_owner,department,
           status,status_raw,size,manday,budget,approved,hold,progress,
           team,y2569,y2570,y2571,gantt_start,gantt_end,updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now','localtime'))
    """, (data.get("section",""),data.get("name",""),data.get("full_name",""),
          data.get("it",""),data.get("po",""),data.get("dept",""),
          data.get("status","todo"),data.get("status_raw",""),
          data.get("size",""),data.get("manday",""),data.get("budget",""),
          data.get("approved",""),data.get("hold",""),data.get("progress",""),
          team_json,
          1 if data.get("y2569") else 0,
          1 if data.get("y2570") else 0,
          1 if data.get("y2571") else 0,
          data.get("gstart",0),data.get("gend",0)))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return jsonify({"id": new_id, "message": "เพิ่มโครงการสำเร็จ"}), 201

@app.route("/api/projects/<int:pid>", methods=["PUT"])
def update_project(pid):
    data = request.get_json()
    team_json = json.dumps(data.get("team", []), ensure_ascii=False)
    conn = get_conn()
    conn.execute("""
        UPDATE projects SET
          section_name=?,name=?,full_name=?,it_owner=?,product_owner=?,
          department=?,status=?,status_raw=?,size=?,manday=?,budget=?,
          approved=?,hold=?,progress=?,team=?,
          y2569=?,y2570=?,y2571=?,gantt_start=?,gantt_end=?,
          updated_at=datetime('now','localtime')
        WHERE id=?
    """, (data.get("section",""),data.get("name",""),data.get("full_name",""),
          data.get("it",""),data.get("po",""),data.get("dept",""),
          data.get("status","todo"),data.get("status_raw",""),
          data.get("size",""),data.get("manday",""),data.get("budget",""),
          data.get("approved",""),data.get("hold",""),data.get("progress",""),
          team_json,
          1 if data.get("y2569") else 0,
          1 if data.get("y2570") else 0,
          1 if data.get("y2571") else 0,
          data.get("gstart",0),data.get("gend",0),pid))
    conn.commit()
    conn.close()
    return jsonify({"message": "แก้ไขโครงการสำเร็จ"})

@app.route("/api/projects/<int:pid>", methods=["DELETE"])
def delete_project(pid):
    conn = get_conn()
    conn.execute("DELETE FROM subtasks WHERE project_id=?", (pid,))
    conn.execute("DELETE FROM projects WHERE id=?", (pid,))
    conn.commit()
    conn.close()
    return jsonify({"message": "ลบโครงการสำเร็จ"})


# ── SUBTASKS ──
@app.route("/api/subtasks", methods=["GET"])
def get_subtasks():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM subtasks ORDER BY project_id, id").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/subtasks/<int:sid>", methods=["GET"])
def get_subtask(sid):
    conn = get_conn()
    row = conn.execute("SELECT * FROM subtasks WHERE id=?", (sid,)).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "ไม่พบงานย่อย"}), 404
    return jsonify(dict(row))

@app.route("/api/subtasks", methods=["POST"])
def add_subtask():
    data = request.get_json()
    conn = get_conn()
    cur = conn.execute("""
        INSERT INTO subtasks
          (project_id,name,detail,it_owner,status,m_start,m_end,manday,priority,note,updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,datetime('now','localtime'))
    """, (data.get("parentId"),data.get("name",""),data.get("detail",""),
          data.get("it",""),data.get("status","todo"),
          data.get("mStart",0),data.get("mEnd",0),
          data.get("manday") or None,
          data.get("priority","normal"),data.get("note","")))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return jsonify({"id": new_id, "message": "เพิ่มงานย่อยสำเร็จ"}), 201

@app.route("/api/subtasks/<int:sid>", methods=["PUT"])
def update_subtask(sid):
    data = request.get_json()
    conn = get_conn()
    conn.execute("""
        UPDATE subtasks SET
          project_id=?,name=?,detail=?,it_owner=?,status=?,
          m_start=?,m_end=?,manday=?,priority=?,note=?,
          updated_at=datetime('now','localtime')
        WHERE id=?
    """, (data.get("parentId"),data.get("name",""),data.get("detail",""),
          data.get("it",""),data.get("status","todo"),
          data.get("mStart",0),data.get("mEnd",0),
          data.get("manday") or None,
          data.get("priority","normal"),data.get("note",""),sid))
    conn.commit()
    conn.close()
    return jsonify({"message": "แก้ไขงานย่อยสำเร็จ"})

@app.route("/api/subtasks/<int:sid>", methods=["DELETE"])
def delete_subtask(sid):
    conn = get_conn()
    conn.execute("DELETE FROM subtasks WHERE id=?", (sid,))
    conn.commit()
    conn.close()
    return jsonify({"message": "ลบงานย่อยสำเร็จ"})


# ── IMPORT (ทำครั้งแรกครั้งเดียว) ──
@app.route("/api/import", methods=["POST"])
def import_data():
    data = request.get_json()
    projects = data.get("projects", [])
    if not projects:
        return jsonify({"error": "ไม่มีข้อมูลส่งมา"}), 400
    conn = get_conn()
    count = 0
    for p in projects:
        if conn.execute("SELECT id FROM projects WHERE id=?", (p["id"],)).fetchone():
            continue
        team_json = json.dumps(p.get("team", []), ensure_ascii=False)
        conn.execute("""
            INSERT INTO projects
              (id,section_name,name,full_name,it_owner,product_owner,department,
               status,status_raw,size,manday,budget,approved,hold,progress,
               team,y2569,y2570,y2571,gantt_start,gantt_end)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (p["id"],p.get("section",""),p.get("name",""),p.get("full_name",""),
              p.get("it",""),p.get("po",""),p.get("dept",""),
              p.get("status","todo"),p.get("status_raw",""),
              p.get("size",""),str(p.get("manday","")),str(p.get("budget","")),
              p.get("approved",""),p.get("hold",""),p.get("progress",""),
              team_json,
              1 if p.get("y2569") else 0,
              1 if p.get("y2570") else 0,
              1 if p.get("y2571") else 0,
              p.get("gstart",0),p.get("gend",0)))
        count += 1
    conn.commit()
    conn.close()
    return jsonify({"message": f"นำเข้าข้อมูลสำเร็จ {count} รายการ", "imported": count})


# ── EXPORT ──
@app.route("/api/export", methods=["GET"])
def export_data():
    conn = get_conn()
    projects = [row_to_dict(r) for r in conn.execute("SELECT * FROM projects ORDER BY id").fetchall()]
    subtasks = [dict(r) for r in conn.execute("SELECT * FROM subtasks ORDER BY id").fetchall()]
    conn.close()
    return jsonify({"exported_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "projects": projects, "subtasks": subtasks})


# ============================================================
if __name__ == "__main__":
    init_db()
    print("🚀 เริ่มต้น Server ที่ http://localhost:5001")
    print("   กด Ctrl+C เพื่อหยุด Server")
    app.run(debug=True, host="0.0.0.0", port=5001)
