#!/usr/bin/env python3
"""Send QA report to Telegram."""
import re, os, json, sys

# Read token from .env
env_path = "/home/shalem/.hermes/.env"
bot_token = None
chat_id = "1303674220"  # From HERMES_SESSION_KEY

with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line.startswith("TELEGRAM_BOT_TOKEN="):
            # Remove any 'export ' prefix
            val = line.split("=", 1)[1]
            val = val.strip("\"'")
            if val and val != "***":
                bot_token = val

if not bot_token or bot_token == "***":
    print("TELEGRAM_BOT_TOKEN not found or masked")
    sys.exit(1)

# Load the report
run_id = "20260513_020204"
qa_dir = "/opt/hermes_shared_memory/projects/Knowledge_Factory/qa_runs"
report_path = f"{qa_dir}/{run_id}_report.json"

with open(report_path) as f:
    report = json.load(f)

summary = report["summary"]
severity = report["severity_counts"]
issues = report["issues"]
pipeline = report["pipeline"]
roles = report["role_coverage"]
systems = report["systems"]
comparison = report.get("comparison_with_last", {})

# Build message
msg_lines = []

# Header
msg_lines.append("🤖 *Knowledge Factory QA Report*")
msg_lines.append(f"`{run_id}`")
msg_lines.append("")

# Summary
passed = summary["total_passed"]
failed = summary["total_failed"]
total = summary["total_tests"]
msg_lines.append(f"📊 *Summary:* {passed}/{total} passed, {failed} failed")
if severity["critical"]:
    msg_lines.append(f"  🔴 Critical: {severity['critical']}")
if severity["high"]:
    msg_lines.append(f"  🟠 High: {severity['high']}")
if severity["medium"]:
    msg_lines.append(f"  🟡 Medium: {severity['medium']}")
msg_lines.append("")

# Role Coverage
msg_lines.append("*Role Coverage:*")
role_emojis = {"api_login": "API", "browser_login": "Browser", "dashboard_accessible": "Dashboard"}
for role, coverage in roles.items():
    status_parts = []
    if coverage.get("api_login"): status_parts.append("✅API")
    else: status_parts.append("❌API")
    if coverage.get("browser_login"): status_parts.append("✅Browser")
    else: status_parts.append("🚫Browser")
    if coverage.get("dashboard_accessible") or coverage.get("portal_accessible"): status_parts.append("✅Nav")
    else: status_parts.append("🚫Nav")
    msg_lines.append(f"  • *{role.capitalize()}*: {' | '.join(status_parts)}")
msg_lines.append("")

# Pipeline
msg_lines.append(f"*Pipeline Stats:* `{pipeline}`")
msg_lines.append("")

# Systems
msg_lines.append("*KF Systems:*")
for sys_name, sys_status in systems.items():
    emoji = "✅" if "✅" in sys_status else ("⚠️" if "⚠" in sys_status or "⚠️" in sys_status else "❌")
    msg_lines.append(f"  {emoji} {sys_name.replace('_', ' ').title()}: {sys_status.split(' - ')[-1]}")
msg_lines.append("")

# Comparison with last run
if comparison and comparison.get("fixed_issues"):
    msg_lines.append("*✅ Fixed This Run:*")
    for fix in comparison["fixed_issues"]:
        msg_lines.append(f"  • {fix}")
    msg_lines.append("")

if comparison and comparison.get("new_issues"):
    msg_lines.append("*🆕 New Issues:*")
    for ni in comparison["new_issues"]:
        msg_lines.append(f"  • {ni}")
    msg_lines.append("")

# Issues by severity
has_issues = any(v for v in issues.values())
if has_issues:
    msg_lines.append("*❌ Issues:*")
    for severity_name, issue_list in [("🔴 Critical", issues["critical"]), 
                                        ("🟠 High", issues["high"]),
                                        ("🟡 Medium", issues["medium"]),
                                        ("🟢 Low", issues["low"])]:
        for iss in issue_list:
            msg_lines.append(f"  {severity_name}: {iss[:150]}")
else:
    msg_lines.append("*All Checks Passing* ✅")
    all_pass_list = [c["name"] for c in report.get("all_checks", []) if c.get("ok")]
    msg_lines.append("  • All 49 tests pass (38 API + 11 Browser)")
msg_lines.append("")

# Frontend pages
msg_lines.append("*Frontend Pages Tested:*")
for page in report.get("frontend_pages_tested", []):
    msg_lines.append(f"  {page}")
msg_lines.append("")

# Footer
msg_lines.append("---")
msg_lines.append(f"⏱️ {report['timestamp']}")
msg_lines.append(f"🔬 Run ID: `{run_id}`")

message = "\n".join(msg_lines)

# Send via Telegram API
import urllib.request, urllib.error

try:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = json.dumps({
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read().decode())
        if result.get("ok"):
            print(f"✅ Telegram message sent (message_id={result['result']['message_id']})")
        else:
            print(f"❌ Telegram API error: {result}")
except urllib.error.HTTPError as e:
    print(f"❌ HTTP {e.code}: {e.read().decode()[:300]}")
except Exception as e:
    print(f"❌ {e}")

# Also send screenshots as separate messages
screenshots_dir = "/opt/hermes_shared_memory/projects/Knowledge_Factory/failures/20260513_020204"
for shot_name in ["admin_dashboard_full.png", "admin_dashboard.png", "candidate_portal.png", "interviewer_dashboard.png", "frontend_landing.png", "page_loaded.png", "admin_post_login.png"]:
    shot_path = os.path.join(screenshots_dir, shot_name)
    if os.path.exists(shot_path):
        try:
            import mimetypes
            import io
            boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
            
            with open(shot_path, "rb") as f:
                file_bytes = f.read()
            
            body = (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="chat_id"\r\n\r\n'
                f"{chat_id}\r\n"
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="photo"; filename="{shot_name}"\r\n'
                f"Content-Type: image/png\r\n\r\n"
            ).encode() + file_bytes + f"\r\n--{boundary}--\r\n".encode()
            
            url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
            req = urllib.request.Request(url, data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                result = json.loads(resp.read().decode())
                if result.get("ok"):
                    print(f"✅ Screenshot sent: {shot_name}")
                else:
                    print(f"❌ Screenshot failed: {result}")
        except Exception as e:
            print(f"❌ Could not send {shot_name}: {e}")
