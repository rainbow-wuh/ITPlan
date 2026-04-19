"""
WUH-IT-Plan — LocalStorage → SQLite Migration Helper
วิธีใช้: เปิด Browser → F12 → Console → วาง script แล้วกด Enter
จะได้ JSON → บันทึกเป็นไฟล์ → รัน python migrate_localstorage.py <ไฟล์.json>
"""
BROWSER_SCRIPT = """
// รันใน Browser Console เพื่อ export localStorage ทั้งหมด
const data = {};
const keys = ['wu_master_it','wu_master_dept','wu_master_size',
               'wu_fiscal_years','wu_it_groups','wu_users'];
keys.forEach(k => {
    try { data[k] = JSON.parse(localStorage.getItem(k) || 'null'); } catch(e) {}
});
// หา perf_ keys
Object.keys(localStorage).filter(k=>k.startsWith('perf_')).forEach(k=>{
    try { data[k] = JSON.parse(localStorage.getItem(k)); } catch(e) {}
});
console.log(JSON.stringify(data, null, 2));
// หรือดาวน์โหลดอัตโนมัติ:
const blob = new Blob([JSON.stringify(data,null,2)], {type:'application/json'});
const a = document.createElement('a');
a.href = URL.createObjectURL(blob);
a.download = 'wuh_localstorage.json';
a.click();
"""

import sys, json, sqlite3, os

if len(sys.argv) < 2:
    print("=" * 55)
    print("วิธีใช้:")
    print("1. เปิด WUH-IT-Plan.html ใน Browser")
    print("2. กด F12 → Console")
    print("3. Copy script นี้แล้ว Paste ใน Console:")
    print("-" * 55)
    print(BROWSER_SCRIPT)
    print("-" * 55)
    print("4. บันทึกไฟล์ JSON ที่ได้")
    print("5. รัน: python migrate_localstorage.py wuh_localstorage.json")
    sys.exit(0)

json_file = sys.argv[1]
DB_PATH = os.path.join(os.path.dirname(__file__), 'wuh_it_plan.db')

with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# ── master_it ──
if data.get('wu_master_it'):
    c.execute("DELETE FROM master_it")
    for i, x in enumerate(data['wu_master_it']):
        c.execute('''INSERT INTO master_it
            (id,name,nickname,role,group_name,phone,email,desc,dept,sort_order)
            VALUES (?,?,?,?,?,?,?,?,?,?)''', (
            x.get('id',i+1), x.get('name',''), x.get('nickname',''),
            x.get('role',''), x.get('group',''), x.get('phone',''),
            x.get('email',''), x.get('desc',''), x.get('dept',''), i
        ))
    print(f"✅ master_it: {len(data['wu_master_it'])} รายการ")

# ── master_dept ──
if data.get('wu_master_dept'):
    c.execute("DELETE FROM master_dept")
    for i, x in enumerate(data['wu_master_dept']):
        c.execute("INSERT INTO master_dept (name,group_name,note,sort_order) VALUES (?,?,?,?)",
                  (x.get('name',''), x.get('group',''), x.get('note',''), i))
    print(f"✅ master_dept: {len(data['wu_master_dept'])} รายการ")

# ── master_size ──
if data.get('wu_master_size'):
    c.execute("DELETE FROM master_size")
    for i, x in enumerate(data['wu_master_size']):
        c.execute("INSERT OR REPLACE INTO master_size VALUES (?,?,?,?,?,?,?)",
                  (x['key'], x.get('label',''), x.get('bg',''), x.get('color',''),
                   x.get('manday',0), x.get('note',''), i))
    print(f"✅ master_size: {len(data['wu_master_size'])} รายการ")

# ── users ──
if data.get('wu_users'):
    c.execute("DELETE FROM users")
    for u in data['wu_users']:
        c.execute("INSERT INTO users (username,password,name,role,note) VALUES (?,?,?,?,?)",
                  (u['username'], u['password'], u.get('name',''), u.get('role','viewer'), u.get('note','')))
    print(f"✅ users: {len(data['wu_users'])} รายการ")

# ── it_groups ──
if data.get('wu_it_groups'):
    c.execute("DELETE FROM it_groups")
    for i, g in enumerate(data['wu_it_groups']):
        c.execute("INSERT INTO it_groups (name,sort_order) VALUES (?,?)", (g['name'], i))
    print(f"✅ it_groups: {len(data['wu_it_groups'])} รายการ")

# ── performance (perf_*) ──
perf_count = 0
for key, val in data.items():
    if key.startswith('perf_') and val:
        parts = key[5:].rsplit('_', 1)
        if len(parts) == 2:
            pid, year_key = parts
            months = val.get('months', {})
            c.execute('''INSERT OR REPLACE INTO performance
                (project_id,year_key,target,yearly,m1,m2,m3,m4,m5,m6,m7,m8,m9,m10,m11,m12)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (
                int(pid), year_key, val.get('target',0), val.get('yearly',0),
                months.get('m1',0), months.get('m2',0), months.get('m3',0),
                months.get('m4',0), months.get('m5',0), months.get('m6',0),
                months.get('m7',0), months.get('m8',0), months.get('m9',0),
                months.get('m10',0), months.get('m11',0), months.get('m12',0)
            ))
            perf_count += 1
if perf_count: print(f"✅ performance: {perf_count} รายการ")

conn.commit()
conn.close()
print(f"\n🎉 Migration สำเร็จ → {DB_PATH}")
