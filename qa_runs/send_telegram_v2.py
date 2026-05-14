#!/usr/bin/env python3
"""Send Telegram notification for QA run results"""
import json, os, sys, urllib.request, urllib.parse, urllib.error
from pathlib import Path

QA_RUNS_DIR = Path("/opt/hermes_shared_memory/projects/Knowledge_Factory/qa_runs")

# Get telegram config
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "1303674220")

# Also try from HERMES_SESSION_KEY
if not CHAT_ID:
    sk = os.environ.get("HERMES_SESSION_KEY", "")
    if ":" in sk:
        parts = sk.split(":")
        CHAT_ID = parts[-1]

if not BOT_TOKEN:
    print("ERROR: No TELEGRAM_BOT_TOKEN available")
    sys.exit(1)

# Load latest run data
telegram_files = sorted(QA_RUNS_DIR.glob("*_telegram_data.json"))
if not telegram_files:
    print("ERROR: No telegram data files found")
    sys.exit(1)

with open(telegram_files[-1]) as f:
    data = json.load(f)

run_id = data["run_id"]
total_passed = data["total_passed"]
total_failed = data["total_failed"]
total_tests = data["total_tests"]
api_passed = data["api_passed"]
api_total = data["api_total"]
fe_passed = data["fe_passed"]
fe_total = data["fe_total"]
severity = data["severity"]
issues = data.get("issues", {})
systems = data.get("systems", {})
pipeline = data.get("pipeline", "")
browser_logins = data.get("browser_logins", {})
fixed_issues = data.get("fixed_issues", [])
new_issues = data.get("new_issues", [])

# Build status emoji
status_emoji = "🟢" if total_failed == 0 else "🟡" if severity.get("critical", 0) == 0 else "🔴"

# Format message
msg = f"""{status_emoji} *Knowledge Factory QA Report*
📅 `{data.get('timestamp', '?')[:19]}`
🆔 `{run_id}`

📊 *Summary:* {total_passed}/{total_tests} passed
├─ API: {api_passed}/{api_total} ✅
├─ Browser: {fe_passed}/{fe_total} {'✅' if fe_passed == fe_total else '⚠️'}
└─ Critical: {severity.get('critical', 0)} | High: {severity.get('high', 0)} | Medium: {severity.get('medium', 0)} | Low: {severity.get('low', 0)}

📈 *Pipeline Status:*
`{pipeline[:200] if pipeline else 'N/A'}`

👤 *Role Logins (API):*
"""

# Role coverage
role_emojis = {r: "✅" if data.get("roles", {}).get(r) else "❌" for r in ["superadmin", "admin", "hr", "interviewer", "candidate"]}
for r, e in role_emojis.items():
    msg += f"  {e} {r.title()}\n"

msg += f"\n🌐 *Browser Logins:*\n"
for r, ok in browser_logins.items():
    emoji = "✅" if ok else "❌"
    msg += f"  {emoji} {r.title()}\n"

msg += f"\n⚙️ *Systems:*\n"
for sys_name, status in systems.items():
    status_icon = status.split(" ")[0] if status else "❓"
    msg += f"  {status_icon} {sys_name}\n"

# Issues
all_issues = issues.get("critical", []) + issues.get("high", []) + issues.get("medium", []) + issues.get("low", [])
if all_issues:
    msg += f"\n❌ *Issues ({len(all_issues)}):*\n"
    for iss in issues.get("critical", []):
        msg += f"  🔴 {iss}\n"
    for iss in issues.get("high", []):
        msg += f"  🟠 {iss}\n"
    for iss in issues.get("medium", []):
        msg += f"  🟡 {iss}\n"
    for iss in issues.get("low", []):
        msg += f"  🟢 {iss}\n"

if fixed_issues:
    msg += f"\n✅ *Fixed This Run:*\n"
    for fi in fixed_issues:
        msg += f"  ✅ {fi}\n"

if new_issues:
    msg += f"\n🆕 *New Issues:*\n"
    for ni in new_issues:
        msg += f"  🆕 {ni}\n"

msg += f"\n🔗 *Backend:* `http://localhost:8000`"
msg += f"\n🔗 *Swagger:* `http://localhost:8000/docs`"

# Send to Telegram
def send_tg_msg(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return json.loads(resp.read())
    except Exception as e:
        print(f"Telegram send error: {e}")
        return None

result = send_tg_msg(msg)
if result and result.get("ok"):
    print(f"✅ Telegram sent successfully (msg_id: {result['result']['message_id']})")
else:
    print(f"⚠️ Telegram send result: {result}")

# Also try sending as a file if message is too long
if len(msg) > 4000:
    print(f"Message too long ({len(msg)} chars), truncating...")
    msg_short = msg[:3500] + f"\n\n... (truncated, see QA dashboard for full report)"
    result2 = send_tg_msg(msg_short)
    print(f"   Truncated message sent: {result2}")
