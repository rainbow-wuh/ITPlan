"""
WUH-IT-Plan — SQLite Database Initializer
สร้าง database และ tables ทั้งหมด
"""
import sqlite3, json, re, os, sys
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'wuh_it_plan.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn

def create_tables():
    conn = get_db()
    c = conn.cursor()

    # ── projects ──
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
        budget      TEXT    DEFAULT '',
        gstart      INTEGER DEFAULT 0,
        gend        INTEGER DEFAULT 0,
        created_at  TEXT    DEFAULT (datetime('now','localtime')),
        updated_at  TEXT    DEFAULT (datetime('now','localtime'))
    )''')

    # ── master_it (บุคลากร IT) ──
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

    # ── master_section (หมวดงาน) ──
    c.execute('''CREATE TABLE IF NOT EXISTS master_section (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT    UNIQUE NOT NULL,
        note        TEXT    DEFAULT '',
        sort_order  INTEGER DEFAULT 0
    )''')

    # ── master_po (Product Owner) ──
    c.execute('''CREATE TABLE IF NOT EXISTS master_po (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT    UNIQUE NOT NULL,
        dept        TEXT    DEFAULT '',
        contact     TEXT    DEFAULT ''
    )''')

    # ── master_dept (หน่วยงาน) ──
    c.execute('''CREATE TABLE IF NOT EXISTS master_dept (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT    UNIQUE NOT NULL,
        group_name  TEXT    DEFAULT '',
        note        TEXT    DEFAULT '',
        sort_order  INTEGER DEFAULT 0
    )''')

    # ── master_size (ขนาดงาน) ──
    c.execute('''CREATE TABLE IF NOT EXISTS master_size (
        key         TEXT    PRIMARY KEY,
        label       TEXT    DEFAULT '',
        bg          TEXT    DEFAULT '#e0f2fe',
        color       TEXT    DEFAULT '#0369a1',
        manday      INTEGER DEFAULT 0,
        note        TEXT    DEFAULT '',
        sort_order  INTEGER DEFAULT 0
    )''')

    # ── fiscal_years (ปีงบประมาณ) ──
    c.execute('''CREATE TABLE IF NOT EXISTS fiscal_years (
        key         TEXT    PRIMARY KEY,
        label       TEXT    NOT NULL,
        sort_order  INTEGER DEFAULT 0
    )''')

    # ── it_groups (ลำดับกลุ่ม IT) ──
    c.execute('''CREATE TABLE IF NOT EXISTS it_groups (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT    UNIQUE NOT NULL,
        sort_order  INTEGER DEFAULT 0
    )''')

    # ── performance (บันทึกความสำเร็จรายเดือน) ──
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

    # ── users (ผู้ใช้งาน) ──
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        username    TEXT    UNIQUE NOT NULL,
        password    TEXT    NOT NULL,
        name        TEXT    DEFAULT '',
        role        TEXT    DEFAULT 'viewer',
        note        TEXT    DEFAULT '',
        created_at  TEXT    DEFAULT (datetime('now','localtime'))
    )''')

    # ── subtasks (แผนงานย่อย) ──
    c.execute('''CREATE TABLE IF NOT EXISTS subtasks (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id  INTEGER REFERENCES projects(id) ON DELETE CASCADE,
        name        TEXT    NOT NULL,
        status      TEXT    DEFAULT 'todo',
        assignee    TEXT    DEFAULT '',
        due_date    TEXT    DEFAULT '',
        note        TEXT    DEFAULT ''
    )''')

    # ── logs ──
    c.execute('''CREATE TABLE IF NOT EXISTS logs (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user        TEXT    DEFAULT '',
        action      TEXT    NOT NULL,
        detail      TEXT    DEFAULT '',
        created_at  TEXT    DEFAULT (datetime('now','localtime'))
    )''')

    conn.commit()
    print("✅ สร้าง tables สำเร็จ")
    conn.close()

def migrate_from_html(html_path):
    """ดึงข้อมูลจาก HTML แล้ว insert เข้า database"""
    if not os.path.exists(html_path):
        print(f"⚠️  ไม่พบ {html_path}")
        return

    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    conn = get_db()
    c = conn.cursor()

    # ── projects ──
    m = re.search(r'let DB = (\[.*?\]);', html, re.DOTALL)
    if m:
        projects = json.loads(m.group(1))
        for p in projects:
            c.execute('''INSERT OR REPLACE INTO projects
                (id,section,name,full_name,it,po,dept,status,status_raw,
                 size,manday,approved,hold,team,months,
                 y2569,y2570,y2571,progress,budget,gstart,gend)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (
                p['id'], p.get('section',''), p.get('name',''),
                p.get('full_name',''), p.get('it',''), p.get('po',''),
                p.get('dept',''), p.get('status','todo'), p.get('status_raw',''),
                p.get('size',''), str(p.get('manday','')),
                p.get('approved',''), p.get('hold',''),
                json.dumps(p.get('team',[]), ensure_ascii=False),
                json.dumps(p.get('months',[]), ensure_ascii=False),
                1 if p.get('y2569') else 0,
                1 if p.get('y2570') else 0,
                1 if p.get('y2571') else 0,
                p.get('progress',''), str(p.get('budget','')),
                p.get('gstart',0), p.get('gend',0)
            ))
        print(f"✅ Import projects: {len(projects)} รายการ")

    # ── master_size defaults ──
    default_sizes = [
        ('XL','XL (6-12 เดือน)','#fff0e6','#c2410c',300,'',0),
        ('M','M (3-6 เดือน)','#fef3c7','#b45309',180,'',1),
        ('S','S (1-3 เดือน)','#dcfce7','#15803d',90,'',2),
        ('XS','XS (<1 เดือน)','#f3f4f6','#6b7280',30,'',3),
        ('XXS','XXS (<1 สัปดาห์)','#f3f4f6','#6b7280',5,'',4),
        ('Bug','Bug Fix','#fce7f3','#be185d',0,'',5),
    ]
    for s in default_sizes:
        c.execute('INSERT OR IGNORE INTO master_size VALUES (?,?,?,?,?,?,?)', s)
    print(f"✅ Import master_size: {len(default_sizes)} รายการ")

    # ── fiscal_years defaults ──
    fiscal = [('y2569','2569',0),('y2570','2570',1),('y2571','2571',2)]
    for f in fiscal:
        c.execute('INSERT OR IGNORE INTO fiscal_years VALUES (?,?,?)', f)
    print(f"✅ Import fiscal_years: {len(fiscal)} รายการ")

    conn.commit()
    conn.close()
    print(f"\n🎉 Migration สำเร็จ → {DB_PATH}")

if __name__ == '__main__':
    print("=== WUH-IT-Plan Database Setup ===\n")
    create_tables()
    html_file = sys.argv[1] if len(sys.argv)>1 else 'WUH-IT-Plan.html'
    migrate_from_html(html_file)

    # แสดง summary
    conn = get_db()
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    print("\n📊 Tables ที่สร้าง:")
    for t in tables:
        cnt = conn.execute(f"SELECT COUNT(*) FROM {t['name']}").fetchone()[0]
        print(f"   {t['name']:20s} {cnt} rows")
    conn.close()
