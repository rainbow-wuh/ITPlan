# WUH-IT-Plan — Database Setup Guide

## ไฟล์ทั้งหมด
| ไฟล์ | หน้าที่ |
|---|---|
| `wuh_it_plan.db` | SQLite database หลัก |
| `init_db.py` | สร้าง tables + import data จาก HTML |
| `api_server.py` | Flask REST API server |
| `migrate_localstorage.py` | ย้ายข้อมูลจาก Browser localStorage → DB |

---

## วิธีใช้งาน

### ขั้นตอนที่ 1 — สร้าง Database (ครั้งแรก)
```bash
pip install flask flask-cors
python init_db.py WUH-IT-Plan.html
```

### ขั้นตอนที่ 2 — ย้ายข้อมูลจาก Browser (ถ้ามีข้อมูลใน localStorage แล้ว)
```bash
python migrate_localstorage.py
# → จะแสดง script ให้รันใน Browser Console
# → บันทึกไฟล์ JSON ที่ได้
python migrate_localstorage.py wuh_localstorage.json
```

### ขั้นตอนที่ 3 — รัน API Server
```bash
python api_server.py
# เปิด http://localhost:5001
```

---

## API Endpoints
| Method | Path | คำอธิบาย |
|---|---|---|
| GET | `/api/projects` | ดึงโครงการทั้งหมด |
| POST | `/api/projects` | เพิ่มโครงการ |
| PUT | `/api/projects/{id}` | แก้ไขโครงการ |
| DELETE | `/api/projects/{id}` | ลบโครงการ |
| GET | `/api/master/it` | บุคลากร IT |
| POST | `/api/master/it` | บันทึกบุคลากร IT |
| GET | `/api/master/dept` | หน่วยงาน |
| GET | `/api/master/size` | ขนาดงาน |
| GET | `/api/performance/{pid}/{year}` | ความสำเร็จรายเดือน |
| POST | `/api/performance/{pid}/{year}` | บันทึกความสำเร็จ |
| GET | `/api/users` | ผู้ใช้งาน |
| GET | `/api/fiscal` | ปีงบประมาณ |
| GET | `/api/logs` | log ระบบ |
| GET | `/api/health` | ตรวจสถานะ server |

---

## Database Schema
```
projects        — โครงการ IT (70+ รายการ)
master_it       — บุคลากร IT
master_section  — หมวดงาน
master_po       — Product Owner
master_dept     — หน่วยงาน
master_size     — ขนาดงาน
fiscal_years    — ปีงบประมาณ
it_groups       — ลำดับกลุ่ม IT
performance     — ความสำเร็จรายเดือน
users           — ผู้ใช้งาน
subtasks        — แผนงานย่อย
logs            — Log ระบบ
```

## ดู Database ด้วย GUI
ดาวน์โหลด **DB Browser for SQLite** (ฟรี)
→ https://sqlitebrowser.org
