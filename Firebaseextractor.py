import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# Web Server Dummy Port Bind
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Running Safely!")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

# Background Thread me Web Server Start Karein
threading.Thread(target=run_web_server, daemon=True).start()

# Aapka Normal/Safe Code Yahan Aayega
print("Main Script Started Safely...")import requests
import re
import urllib.parse
import time
import base64
import os
import tempfile
import zipfile

# ═══════════════════════════════════════════════════════════════
# TELEGRAM BOT CONFIGURATION
# ═══════════════════════════════════════════════════════════════
TG_TOKEN = "8640283878:AAEGSBnhIbwmh5ImyWNOQ4RDM6-MxGCrfc8"
BOT_USERNAME = "ecfirebasebot"
TG_GATEWAY = f"https://api.telegram.org/bot{TG_TOKEN}"

def send_message(chat_id, text):
    try:
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        requests.post(f"{TG_GATEWAY}/sendMessage", json=payload, timeout=8)
    except Exception:
        pass

def extract_urls_from_binary(data_bytes: bytes) -> set:
    found = set()
    strings = re.findall(b'[\x20-\x7E]{4,}', data_bytes)
    for s in strings:
        try:
            text = s.decode('utf-8', errors='ignore')
            matches = re.findall(r'https?://[a-zA-Z0-9_.-]+(?:firebaseio\.com|firebasedatabase\.app)', text)
            for m in matches:
                if "your-project" not in m:
                    found.add(m)
            domains = re.findall(r'[a-zA-Z0-9_-]+-default-rtdb\.[a-z0-9.-]+', text)
            for d in domains:
                if not d.startswith("http"):
                    d = "https://" + d
                if "your-project" not in d:
                    found.add(d)
        except:
            pass
    return found

def extract_firebase_from_apk(file_path: str) -> str:
    found_databases = set()
    try:
        with zipfile.ZipFile(file_path, 'r') as apk_zip:
            for filename in apk_zip.namelist():
                try:
                    file_data = apk_zip.read(filename)
                    found_databases.update(extract_urls_from_binary(file_data))
                except:
                    pass
        
        if found_databases:
            result_text = f"📦 <b>Deep APK Scan Successful!</b>\n\n<b>Found Firebase Databases ({len(found_databases)}):</b>\n"
            for idx, db_url in enumerate(found_databases, 1):
                result_text += f"\n{idx}. <code>{db_url}</code>"
            return result_text
        else:
            return "⚠️ <b>Deep Scan Result:</b> No Firebase database URL could be resolved from this APK."
    except Exception as e:
            return f"❌ <b>Error processing APK:</b> <code>{str(e)}</code>"

def extract_firebase_from_url(target_url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 14; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
    }
    try:
        if not target_url.startswith("http"):
            target_url = "https://" + target_url
            
        found_databases = set()
        
        parsed_url = urllib.parse.urlparse(target_url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        for key, values in query_params.items():
            for val in values:
                try:
                    padding = '=' * (-len(val) % 4)
                    dec = base64.b64decode(val + padding).decode('utf-8', errors='ignore')
                    found_databases.update(extract_urls_from_binary(dec.encode()))
                except:
                    pass
                found_databases.update(extract_urls_from_binary(val.encode()))

        response = requests.get(target_url, headers=headers, timeout=15, allow_redirects=True)
        found_databases.update(extract_urls_from_binary(response.content))
        
        js_files = re.findall(r'src=["\']([^"\']+\.js[^"\']*)["\']', response.text)
        for js in js_files:
            if not js.startswith("http"):
                parsed_base = urllib.parse.urlparse(target_url)
                js_url = f"{parsed_base.scheme}://{parsed_base.netloc}" + (js if js.startswith('/') else '/' + js)
            else:
                js_url = js
            try:
                js_resp = requests.get(js_url, headers=headers, timeout=10)
                found_databases.update(extract_urls_from_binary(js_resp.content))
            except:
                pass
                
        if found_databases:
            result_text = f"🔍 <b>Panel Scanned Successfully!</b>\n🌐 Target: <code>{target_url}</code>\n\n<b>Found Databases ({len(found_databases)}):</b>\n"
            for idx, db_url in enumerate(found_databases, 1):
                result_text += f"\n{idx}. <code>{db_url}</code>"
            return result_text
        else:
            return f"⚠️ <b>Scan Result:</b> No Firebase database URL found for <code>{target_url}</code>"
    except Exception as err:
        return f"❌ <b>Error:</b> <code>{str(err)}</code>"

def download_telegram_file(file_id: str) -> str:
    try:
        res = requests.get(f"{TG_GATEWAY}/getFile", params={"file_id": file_id}, timeout=10)
        file_path_info = res.json().get("result", {}).get("file_path")
        if not file_path_info:
            return None
        download_url = f"https://api.telegram.org/file/bot{TG_TOKEN}/{file_path_info}"
        file_resp = requests.get(download_url, timeout=40)
        temp_apk = os.path.join(tempfile.gettempdir(), "target_app.apk")
        with open(temp_apk, "wb") as f:
            f.write(file_resp.content)
        return temp_apk
    except:
        return None

def run_bot_polling():
    print(f"[*] Bot @{BOT_USERNAME} is running...")
    
    offset = 0
    while True:
        try:
            resp = requests.get(f"{TG_GATEWAY}/getUpdates", params={"offset": offset, "timeout": 30}, timeout=35)
            if resp.status_code == 200:
                data = resp.json()
                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    if "message" in update:
                        msg = update["message"]
                        chat_id = msg["chat"]["id"]
                        
                        if "document" in msg or "audio" in msg:
                            doc = msg.get("document") or msg.get("audio")
                            file_name = doc.get("file_name", "")
                            if file_name.endswith(".apk") or doc.get("mime_type") == "application/vnd.android.package-archive":
                                send_message(chat_id, "⚙️ <b>Scanning APK...</b> Please wait.")
                                local_apk = download_telegram_file(doc["file_id"])
                                if local_apk:
                                    scan_res = extract_firebase_from_apk(local_apk)
                                    send_message(chat_id, scan_res)
                                    try: os.remove(local_apk)
                                    except: pass
                                else:
                                    send_message(chat_id, "❌ Failed to download APK.")
                            else:
                                send_message(chat_id, "⚠️ Please send a valid <b>.apk</b> file.")
                        elif "text" in msg:
                            txt = msg["text"].strip()
                            if txt.startswith("/start"):
                                send_message(chat_id, f"👋 <b>Welcome to @{BOT_USERNAME}!</b>\n\nSend any web link or <b>.apk file</b> to extract Firebase Realtime Database URLs.")
                            else:
                                send_message(chat_id, "⏳ Scanning target data...")
                                res_text = extract_firebase_from_url(txt)
                                send_message(chat_id, res_text)
        except Exception as e:
            print(f"[!] Polling error: {e}")
            time.sleep(3)

if __name__ == "__main__":
    run_bot_polling()
