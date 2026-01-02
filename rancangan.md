# IoT Larva Detection System – Backend & Device Flow Specification

## 1. Tujuan Sistem

Membangun backend berbasis FastAPI yang:

- menerima gambar dari ESP32-CAM
- melakukan inference menggunakan Roboflow
- mem-parsing hasil deteksi jentik
- menentukan status (AMAN / BAHAYA)
- mengirim status & perintah ke Blynk
- mengembalikan action ke ESP32 (ACTIVATE / SLEEP)
- menyimpan seluruh riwayat ke database

Sistem ini **device-centric**, tanpa akun user personal.
Login dilakukan **per device** menggunakan password device.

---

## 2. Komponen Sistem

### 2.1 Hardware

- ESP32-CAM
- Kamera
- Servo / Pompa Abate

### 2.2 Backend

- FastAPI
- mySql Database
- Local filesystem storage (Railway)
- Roboflow Inference API
- Blynk Cloud API

### 2.3 Client

- ESP32 firmware
- Blynk Dashboard (monitoring & manual override)

---

## 3. Database Contract (Single Source of Truth)

### 3.1 Device Authentication Model

- Device = akun
- Username = device_code
- Password = device password (hashed)
- Tidak ada akun user personal

---

### 3.2 Database Schema

```dbml
Table devices {
  id uuid [pk]
  device_code varchar [unique, not null]
  location varchar
  description text
  is_active boolean
  created_at timestamp
}

Table device_auth {
  id uuid [pk]
  device_id uuid [not null, ref: > devices.id]
  device_code varchar [unique, not null]
  password_hash varchar [not null]
}

Table images {
  id uuid [pk]
  device_id uuid [not null, ref: > devices.id]
  device_code varchar [not null]
  image_type varchar // original | preprocessed
  image_path varchar
  width int
  height int
  checksum varchar
  captured_at timestamp
  uploaded_at timestamp
}

Table inference_results {
  id uuid [pk]
  image_id uuid [not null, ref: > images.id]
  device_id uuid [not null, ref: > devices.id]
  device_code varchar [not null]
  inference_at timestamp
  raw_prediction json
  total_objects int
  total_jentik int
  total_non_jentik int
  avg_confidence float
  parsing_version varchar
}

Table alerts {
  id uuid [pk]
  device_id uuid [not null, ref: > devices.id]
  device_code varchar [not null]
  alert_type varchar
  alert_message text
  alert_level varchar // info | warning | critical
  created_at timestamp
  resolved_at timestamp
}
```

---

## 4. Flow Sistem

```markdown
ESP32 / Simulator
   ↓
Backend (FastAPI)
   ↓
Image Storage (Local FS)
   ↓
Preprocessing image
   ↓
Inference (Roboflow)
   ↓
Decision Engine
   ↓
Database
   ↓
Blynk Dashboard
   ↓
Action kembali ke ESP32
```

B. Flow Detail Berdasarkan Kondisi Nyata Anda

1. Flow Registrasi & Provisioning Device (Sekali Saja)

Flow ini tidak dilakukan ESP32, tapi oleh admin / developer

Admin
 ├─ Generate device_code (misal: ESP32_TOREN_01)
 ├─ Generate device_password
 ├─ Insert ke:
 │   - devices
 │   - device_auth (password di-hash)
 └─ Device siap digunakan

ESP32 hanya menyimpan:

- device_code
- device_password / API key

1. Flow Login Device (Implicit, Tanpa Session)

Karena ESP32 tidak pakai session, maka:

SETIAP REQUEST:
ESP32 → Authorization Header (API Key / Basic Auth)
Backend → Validate → lanjut / reject

Tidak ada:

- JWT user
- refresh token
- session table

1. Flow Pengiriman Gambar (Normal Case)

ESP32
 ├─ Capture image
 ├─ POST /upload
 │   ├─ device_code
 │   ├─ captured_at
 │   └─ image file
 ↓
Backend
 ├─ Auth device
 ├─ Save image ke filesystem
 ├─ Insert images (original)
 ├─ Preprocess image
 ├─ Insert images (preprocessed)
 ├─ Kirim ke Roboflow
 ├─ Parse hasil
 ├─ Insert inference_results
 ├─ Decision logic
 ├─ Insert alert (jika perlu)
 ├─ Update Blynk
 └─ Response ke ESP32

1. Flow Interval & Concurrency (Sesuai Kekhawatiran Anda)

Karena:

- device tidak kirim gambar terus-menerus
- interval ± 6 jam
- bisa ada 10 device kirim hampir bersamaan

Maka flow backend HARUS non-blocking:

Upload Endpoint
 ├─ Save image cepat
 ├─ Response diterima
 └─ Inference dijalankan async / background

Rekomendasi:

- FastAPI BackgroundTasks
- atau Celery ringan
- atau asyncio task

ESP32 tidak perlu menunggu inference selesai lama

1. Flow Fallback Jika Inference Error

Jika Roboflow error:
 ├─ Simpan image tetap
 ├─ inference_results status = failed
 ├─ Jangan trigger alert
 ├─ Kirim status ke Blynk = "INFERENCE ERROR"
 └─ ESP32 default ke SLEEP

Ini penting agar:

- sistem tetap stabil
- tidak false-positive

1. Flow Alert (Sesuai Penjelasan Anda)

Alert tidak realtime spam, tapi berbasis kondisi:

IF total_jentik > 0
AND alert sebelumnya belum resolved
THEN
 └─ Jangan buat alert baru

Alert hanya dibuat:

- pertama kali kondisi bahaya muncul
- resolved ketika kondisi aman kembali

1. Flow Blynk (Monitoring, Bukan Source of Truth)

Blynk:

- hanya display
- hanya override manual (opsional)

Backend = source of truth
Blynk = dashboard + remote control

Jika Blynk kirim override:

- backend validasi
- backend kirim command ke ESP32

1. Flow ESP32 (Final & Deterministik)

BOOT
 ├─ Capture image
 ├─ Upload
 ├─ Tunggu response
 ├─ Parse action
 │   ├─ ACTIVATE → Servo ON
 │   └─ SLEEP → Deep Sleep
 └─ Timer wakeup

ESP32 tidak menyimpan histori
ESP32 tidak menyimpan image

1. Flow Simulasi (Tanpa Device – Sesuai Tujuan Anda Sekarang)

A. Testing Awal

- Gunakan Postman
- Upload image manual

Pastikan:

- image tersimpan
- inference jalan
- response benar

B. Load / Stress Test

- Python client

Simulasikan:

- 10–50 device
- random interval
- random image

ESP32 tidak dibutuhkan sama sekali untuk tahap ini.

C. Tambahan Minor di Database (Opsional tapi Disarankan)

Tambahkan ke inference_results:

- status varchar // success | failed
- error_message text

Agar error inference bisa dilacak.
