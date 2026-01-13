# API Documentation - Mosquito Detection Backend

## Base URL

```
Production: https://mosquitobackend-production.up.railway.app
Local Development: http://localhost:8080
```

## Authentication

Semua endpoint (kecuali `/health`) menggunakan **HTTP Basic Authentication** dengan device credentials.

### Format Authentication

```
Authorization: Basic base64(device_code:password)
```

**Example:**

- Device Code: `test`
- Password: `123`
- Combined: `test:123`
- Base64: `dGVzdDoxMjM=`
- Header: `Authorization: Basic dGVzdDoxMjM=`

---

## Endpoints

### 1. Upload Image (ESP32 Endpoint)

**Endpoint:** `POST /api/upload`

**Description:** Upload gambar dari ESP32 untuk deteksi jentik nyamuk. Sistem akan:

1. Menyimpan gambar original
2. Preprocessing gambar
3. Response cepat ke ESP32 (action: ACTIVATE/SLEEP)
4. Inference di background dengan Roboflow
5. Update Blynk (jika configured)

**Authentication:** Required (HTTP Basic Auth)

**Request:**

- **Method:** POST (PENTING: Harus POST, bukan GET)
- **Content-Type:** multipart/form-data
- **Headers:**

  ```
  Authorization: Basic <base64_credentials>
  Content-Type: multipart/form-data; boundary=----WebKitFormBoundary...
  ```

- **Body (multipart/form-data):**

  ```
  image: file (binary, field name harus "image")
  captured_at: string (optional, ISO format datetime)
  ```

**Response Success (200):**

```json
{
  "success": true,
  "message": "Image uploaded successfully, processing in background",
  "action": "SLEEP",
  "status": "PROCESSING",
  "device_code": "test",
  "total_jentik": 0,
  "total_objects": 0
}
```

**Response Fields:**

- `success`: boolean - Status keberhasilan upload
- `message`: string - Informasi hasil upload
- `action`: "ACTIVATE" (ada jentik) | "SLEEP" (aman/processing)
- `status`: "PROCESSING" - Status inference (diproses di background)
- `device_code`: string - Kode device yang upload
- `total_jentik`: number - Jumlah jentik terdeteksi (0 saat upload, updated di background)
- `total_objects`: number - Total objek terdeteksi (0 saat upload, updated di background)

**Response Error (401 Unauthorized):**

```json
{
  "detail": "Invalid credentials"
}
```

**Response Error (405 Method Not Allowed):**

```json
{
  "detail": "Method Not Allowed"
}
```

**Penyebab Error 405:**

- Request menggunakan GET bukan POST
- HTTPClient melakukan redirect dan berubah menjadi GET
- URL tidak tepat atau ada trailing slash issue

**Solusi Error 405:**

- Pastikan menggunakan `http.POST()` di ESP32
- Disable follow redirects: `http.setFollowRedirects(HTTPC_DISABLE_FOLLOW_REDIRECTS);`
- Pastikan URL benar dan tidak ada redirect
- Check server logs untuk detail error

**Response Error (500 Internal Server Error):**

```json
{
  "detail": "Upload failed: <error_description>"
}
```

#### Contoh Penggunaan

**cURL:**

```bash
curl -X POST https://mosquitobackend-production.up.railway.app/api/upload \
  -u "test:123" \
  -F "image=@/path/to/image.jpg"
```

**Python:**

```python
import requests
from requests.auth import HTTPBasicAuth

url = "https://mosquitobackend-production.up.railway.app/api/upload"
auth = HTTPBasicAuth("test", "123")

with open("image.jpg", "rb") as f:
    files = {"image": f}
    response = requests.post(url, auth=auth, files=files)
    
print(response.json())
```

**ESP32 (Arduino) - CORRECT IMPLEMENTATION:**

```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <base64.h>

const char* serverURL = "https://mosquitobackend-production.up.railway.app/api/upload";
const char* deviceCode = "test";
const char* devicePassword = "123";

String encodeBasicAuth(String username, String password) {
  String credentials = username + ":" + password;
  return base64::encode(credentials);
}

void sendPhotoToServer(camera_fb_t * fb) {
  HTTPClient http;
  
  // PENTING: Disable redirects untuk menghindari GET
  http.setFollowRedirects(HTTPC_DISABLE_FOLLOW_REDIRECTS);
  
  http.begin(serverURL);
  http.setTimeout(15000);
  
  // Set Basic Auth header
  String authHeader = "Basic " + encodeBasicAuth(deviceCode, devicePassword);
  http.addHeader("Authorization", authHeader);
  
  // Set multipart form-data
  String boundary = "----WebKitFormBoundaryESP32CAM";
  http.addHeader("Content-Type", "multipart/form-data; boundary=" + boundary);
  
  // Build multipart body
  String bodyStart = "--" + boundary + "\r\n";
  bodyStart += "Content-Disposition: form-data; name=\"image\"; filename=\"esp32cam.jpg\"\r\n";
  bodyStart += "Content-Type: image/jpeg\r\n\r\n";
  
  String bodyEnd = "\r\n--" + boundary + "--\r\n";
  
  // Allocate payload
  uint32_t totalLen = bodyStart.length() + fb->len + bodyEnd.length();
  uint8_t *payload = (uint8_t *)malloc(totalLen);
  
  memcpy(payload, bodyStart.c_str(), bodyStart.length());
  memcpy(payload + bodyStart.length(), fb->buf, fb->len);
  memcpy(payload + bodyStart.length() + fb->len, bodyEnd.c_str(), bodyEnd.length());
  
  // Send POST request
  int httpResponseCode = http.POST(payload, totalLen);
  
  free(payload);
  
  if (httpResponseCode == 200) {
    String response = http.getString();
    Serial.println("Success: " + response);
  } else {
    Serial.printf("Error: HTTP %d\n", httpResponseCode);
  }
  
  http.end();
}
```

**Troubleshooting Upload Errors:**

| Error Code | Penyebab | Solusi |
|------------|----------|--------|
| 405 Method Not Allowed | Request menggunakan GET bukan POST | 1. Pastikan `http.POST()` dipanggil<br>2. Tambahkan `http.setFollowRedirects(HTTPC_DISABLE_FOLLOW_REDIRECTS);`<br>3. Verifikasi URL tidak redirect |
| 401 Unauthorized | Credentials salah | 1. Check device_code dan password<br>2. Verifikasi Base64 encoding benar<br>3. Pastikan device terdaftar di database |
| 500 Internal Server Error | Server error saat processing | 1. Check server logs<br>2. Verifikasi format multipart benar<br>3. Pastikan image file valid |
| -1 Connection Failed | Tidak bisa connect ke server | 1. Check WiFi connection<br>2. Verifikasi server URL benar<br>3. Check firewall/network |
| -11 Timeout | Request timeout | 1. Increase timeout value<br>2. Check network stability<br>3. Reduce image size jika perlu |

---
    int httpCode = http.POST(imageData, imageSize);
    
    if (httpCode > 0) {
        String response = http.getString();
        Serial.println(response);
        
        // Parse JSON dan ambil action
        // if (action == "ACTIVATE") { jalankan pompa }
        // else { sleep mode }
    }
    
    http.end();
}

```

---

### 2. Get Device Info

**Endpoint:** `GET /api/device/info`

**Description:** Mendapatkan informasi detail device yang sedang login

**Authentication:** Required (HTTP Basic Auth)

**Request:**

- **Method:** GET
- **Headers:**

  ```markdown
  Authorization: Basic <base64_credentials>
  ```

**Response Success (200):**

```json
{
  "id": "4ebc0405-7647-436a-a448-4ac8f0a462cb",
  "device_code": "ESP32_TEST_01",
  "location": "Kantor Depan",
  "description": "Testing device",
  "is_active": true,
  "created_at": "2026-01-01T15:30:00+07:00"
}
```

**Response Error (401):**

```json
{
  "detail": "Invalid credentials"
}
```

#### Contoh Penggunaan

**cURL:**

```bash
curl -X GET http://localhost:8080/api/device/info \
  -u "ESP32_TEST_01:password123"
```

**Python:**

```python
import requests
from requests.auth import HTTPBasicAuth

url = "http://localhost:8080/api/device/info"
auth = HTTPBasicAuth("ESP32_TEST_01", "password123")

response = requests.get(url, auth=auth)
print(response.json())
```

---

### 3. Health Check

**Endpoint:** `GET /api/health`

**Description:** Cek status server

**Authentication:** None

**Request:**

- **Method:** GET

**Response Success (200):**

```json
{
  "status": "healthy",
  "timestamp": "2026-01-02T12:00:00+07:00"
}
```

#### Contoh Penggunaan

**cURL:**

```bash
curl http://localhost:8080/api/health
```

**Python:**

```python
import requests

response = requests.get("http://localhost:8080/api/health")
print(response.json())
```

---

## Flow Diagram

```markdown
ESP32 Capture Image
    ↓
POST /api/upload (with auth)
    ↓
Backend: Save Original Image
    ↓
Backend: Preprocess Image
    ↓
Backend: Response cepat (ACTIVATE/SLEEP) ← ESP32 terima response
    ↓
[Background Process]
    ↓
Roboflow Workflow Inference
    ↓
Parse Predictions (count jentik)
    ↓
Decision Engine (AMAN/BAHAYA)
    ↓
Update Blynk Dashboard
    ↓
Create/Resolve Alerts in Database
```

---

## Database Schema

### Images Table

Menyimpan gambar original dan preprocessed

```sql
- id (UUID)
- device_id (UUID, FK)
- device_code (string)
- image_type (original | preprocessed)
- image_path (string)
- width, height (int)
- checksum (string)
- captured_at (datetime)
- uploaded_at (datetime)
```

### Inference Results Table

Menyimpan hasil inference dari Roboflow

```sql
- id (UUID)
- image_id (UUID, FK)
- device_id (UUID, FK)
- device_code (string)
- inference_at (datetime)
- raw_prediction (JSON) - Full response dari Roboflow
- total_objects (int)
- total_jentik (int)
- total_non_jentik (int)
- avg_confidence (float)
- parsing_version (string)
- status (success | failed)
- error_message (text)
```

### Alerts Table

Menyimpan alert status BAHAYA

```sql
- id (UUID)
- device_id (UUID, FK)
- device_code (string)
- alert_type (BAHAYA)
- alert_message (text)
- alert_level (info | warning | critical)
- created_at (datetime)
- resolved_at (datetime, nullable)
```

---

## Environment Variables

File `.env` configuration:

```env
# Database
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/mosquito_db

# Roboflow (Workflow Mode)
ROBOFLOW_API_KEY=your_api_key
ROBOFLOW_WORKSPACE=your_workspace
ROBOFLOW_WORKFLOW_ID=workflow_id

# Blynk (Optional)
BLYNK_AUTH_TOKEN=your_blynk_token
BLYNK_TEMPLATE_ID=your_template_id

# Timezone (WIB/UTC/etc)
TIMEZONE=Asia/Jakarta

# Security
SECRET_KEY=your_secret_key
```

---

## Error Codes & Troubleshooting

| Code | Description | Common Causes | Solutions |
|------|-------------|---------------|-----------|
| 200 | Success | - | Request processed successfully |
| 400 | Bad Request | Invalid parameters, missing required fields | Check request format and required fields |
| 401 | Unauthorized | Invalid credentials, wrong Basic Auth | Verify device_code:password and Base64 encoding |
| 405 | Method Not Allowed | Using GET instead of POST, redirect issues | 1. Use POST method<br>2. Disable redirects in HTTPClient<br>3. Verify URL is correct |
| 500 | Internal Server Error | Server processing error, invalid file format | Check server logs, verify image format is valid |

---

## Debugging ESP32 Upload Issues

### Checklist untuk Debug Error 405 (Method Not Allowed)

1. **Verify HTTP Method**

   ```cpp
   // BENAR ✓
   int httpResponseCode = http.POST(payload, totalLen);
   
   // SALAH ✗ 
   int httpResponseCode = http.GET();
   ```

2. **Disable HTTP Redirects**

   ```cpp
   // Tambahkan sebelum http.begin()
   http.setFollowRedirects(HTTPC_DISABLE_FOLLOW_REDIRECTS);
   ```

3. **Check URL Configuration**

   ```cpp
   // BENAR ✓
   const char* serverURL = "https://mosquitobackend-production.up.railway.app/api/upload";
   
   // SALAH ✗ (missing /api)
   const char* serverURL = "https://mosquitobackend-production.up.railway.app/upload";
   ```

4. **Verify Authentication Header**

   ```cpp
   // Generate Basic Auth
   String encodeBasicAuth(String username, String password) {
     String credentials = username + ":" + password;
     return base64::encode(credentials);
   }
   
   // Apply header
   String authHeader = "Basic " + encodeBasicAuth(deviceCode, devicePassword);
   http.addHeader("Authorization", authHeader);
   ```

5. **Check Multipart Form-Data Format**

   ```cpp
   // Field name HARUS "image"
   String bodyStart = "--" + boundary + "\r\n";
   bodyStart += "Content-Disposition: form-data; name=\"image\"; filename=\"esp32cam.jpg\"\r\n";
   bodyStart += "Content-Type: image/jpeg\r\n\r\n";
   ```

### Serial Monitor Debug Output

Expected output dari ESP32 yang benar:

```
====================
Taking a photo...
Photo captured successfully!
Image size: 45678 bytes
Payload size: 45890 bytes (Header: 152, Image: 45678, Footer: 60)
Sending POST request to server...
URL: https://mosquitobackend-production.up.railway.app/api/upload
Method: POST
Auth: Basic (device credentials)
✓ HTTP Response code: 200
Server Response:
{"success":true,"message":"Image uploaded successfully, processing in background","action":"SLEEP","status":"PROCESSING","device_code":"test","total_jentik":0,"total_objects":0}
--- Parsed Response ---
Status: PROCESSING
Action: SLEEP
Message: Image uploaded successfully, processing in background
✓ RELAY OFF - Safe, no larvae detected
====================
```

Error output jika ada masalah:

```
====================
Taking a photo...
Photo captured successfully!
Image size: 45678 bytes
Sending POST request to server...
✗ HTTP Response code: 405
✗ Method Not Allowed. Server might not accept POST at this endpoint.
Response: {"detail":"Method Not Allowed"}
====================
```

### Common ESP32 Issues & Solutions

| Issue | Symptoms | Solution |
|-------|----------|----------|
| GET instead of POST | HTTP 405 error | Verify using `http.POST()`, not `http.GET()` |
| Redirect changing method | HTTP 405 after 301/302 | Add `http.setFollowRedirects(HTTPC_DISABLE_FOLLOW_REDIRECTS);` |
| Authentication failure | HTTP 401 error | Check device credentials, verify Base64 encoding |
| Image too large | Timeout or memory error | Reduce JPEG quality or frame size in camera config |
| WiFi disconnection | Connection failed (-1) | Add WiFi reconnection logic in loop |
| SSL certificate issues | Connection failed on HTTPS | Use `http.setInsecure()` or install proper CA cert |

---

## Server Log Examples

### Successful Upload Log

```
=== Upload Request ===
Device: test
Image filename: esp32cam.jpg
Content-Type: image/jpeg
Captured at: None
=====================

✓ Image uploaded successfully from test
  Original: test_original_20260112_145230_abc123.jpg
  Preprocessed: test_preprocessed_20260112_145230_abc123.jpg
  Background inference queued
```

### Failed Upload Log (405 Error)

```
INFO:     100.64.0.3:43370 - "GET /api/upload HTTP/1.1" 405 Method Not Allowed
```

**Penyebab:** ESP32 mengirim GET request bukan POST, kemungkinan karena:

- HTTPClient mengikuti redirect dan method berubah ke GET
- Kesalahan implementasi di kode ESP32

**Solusi:**

1. Tambahkan `http.setFollowRedirects(HTTPC_DISABLE_FOLLOW_REDIRECTS);`
2. Verifikasi menggunakan `http.POST()` bukan `http.GET()`
3. Check URL tidak ada trailing slash atau redirect

---
| 404 | Not Found |
| 500 | Internal Server Error |

---

## Rate Limiting

Belum diimplementasi (untuk production sebaiknya tambahkan rate limiting)

---

## Testing & Verification

### Register Device Baru

```bash
python register_device.py
# Atau langsung via script:
python register_device.py test 123 "ESP32 Test Device" "Testing device"
```

### Test Upload via cURL

**Test Success (200):**

```bash
curl -X POST https://mosquitobackend-production.up.railway.app/api/upload \
  -u "test:123" \
  -F "image=@test_image.jpg" \
  -v
```

Expected response:

```json
{
  "success": true,
  "message": "Image uploaded successfully, processing in background",
  "action": "SLEEP",
  "status": "PROCESSING",
  "device_code": "test",
  "total_jentik": 0,
  "total_objects": 0
}
```

**Test Authentication Error (401):**

```bash
curl -X POST https://mosquitobackend-production.up.railway.app/api/upload \
  -u "wrong:credentials" \
  -F "image=@test_image.jpg"
```

Expected response:

```json
{
  "detail": "Invalid credentials"
}
```

### Test Upload via Python Script

```bash
python test_upload.py
```

### Test via Swagger UI

Buka browser:

- Production: `https://mosquitobackend-production.up.railway.app/docs`
- Local: `http://localhost:8080/docs`

### Test via Postman

1. Create new POST request
2. URL: `https://mosquitobackend-production.up.railway.app/api/upload`
3. Authorization → Type: Basic Auth
   - Username: `test`
   - Password: `123`
4. Body → form-data
   - Key: `image` (Type: File)
   - Value: Select image file
5. Send request

### Verify ESP32 Upload

1. Upload [sketch_apr8a.ino](sketch_apr8a.ino) ke ESP32-CAM
2. Update WiFi credentials di kode
3. Open Serial Monitor (115200 baud)
4. Check output untuk success message:

   ```
   ✓ HTTP Response code: 200
   ```

5. Verify relay control based on response
6. Check server logs untuk confirmation

**Expected Serial Output (Success):**

```
====================
Taking a photo...
Photo captured successfully!
Image size: 45678 bytes
Payload size: 45890 bytes
Sending POST request to server...
✓ HTTP Response code: 200
Server Response:
{"success":true,"message":"Image uploaded successfully, processing in background"...}
--- Parsed Response ---
Status: PROCESSING
Action: SLEEP
✓ RELAY OFF - Safe, no larvae detected
====================
```

---

## Production Deployment

### Railway/Heroku

1. Set environment variables di dashboard
2. Set `DATABASE_URL` ke MySQL production
3. Set `TIMEZONE` sesuai region
4. Deploy via Git push

### Docker

```bash
docker build -t mosquito-backend .
docker run -p 8080:8080 --env-file .env mosquito-backend
```

### Security Checklist

- ✅ HTTPS only in production
- ✅ Strong SECRET_KEY
- ✅ Database password yang kuat
- ✅ Rate limiting untuk production
- ✅ CORS configuration jika ada frontend
- ⚠️ Backup database regular

---

## Support & Contact

Untuk pertanyaan atau issue, silakan buka issue di repository atau contact developer.

---
