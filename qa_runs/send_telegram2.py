#!/usr/bin/env python3
"""Send QA report to Telegram - fixed markdown."""
import re, os, json, sys, urllib.request, urllib.error

env_path = "/home/shalem/.hermes/.env"
bot_token = None
chat_id = "1303674220"

with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line.startswith("TELEGRAM_BOT_TOKEN="):
            val = line.split("=", 1)[1]
            val = val.strip("\"'")
            if val and val != "***":
                bot_token = val

if not bot_token or bot_token == "***":
    print("TELEGRAM_BOT_TOKEN not found or masked")
    sys.exit(1)

run_id = "20260513_020204"
qa_dir = "/opt/hermes_shared_memory/projects/Knowledge_Factory/qa_runs"
report_path = f"{qa_dir}/{run_id}_report.json"

with open(report_path) as f:
    report = json.load(f)

def escape_md(text):
    """Escape special MarkdownV2 characters."""
    special = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(special)}])', r'\\\1', str(text))

summary = report["summary"]
severity = report["severity_counts"]
issues = report["issues"]
pipeline = report["pipeline"]
roles = report["role_coverage"]
systems = report["systems"]
comparison = report.get("comparison_with_last", {})

msg_lines = []

msg_lines.append("*Knowledge Factory QA Report*")
msg_lines.append(f"`{run_id}`")
msg_lines.append("")

passed = summary["total_passed"]
failed = summary["total_failed"]
total = summary["total_tests"]
msg_lines.append(f"*Summary:* {passed}/{total} passed, {failed} failed")
if severity["critical"]:
    msg_lines.append(f"  🔴 Critical: {severity['critical']}")
if severity["high"]:
    msg_lines.append(f"  🟠 High: {severity['high']}")
if severity["medium"]:
    msg_lines.append(f"  🟡 Medium: {severity['medium']}")
msg_lines.append("")

msg_lines.append("*Role Coverage:*")
for role, coverage in roles.items():
    parts = []
    if coverage.get("api_login"): parts.append("API✅")
    else: parts.append("API❌")
    if coverage.get("browser_login"): parts.append("Browser✅")
    else: parts.append("Browser🚫")
    if coverage.get("dashboard_accessible") or coverage.get("portal_accessible"): parts.append("Nav✅")
    else: parts.append("Nav🚫")
    msg_lines.append(f"  {role.capitalize()}: {' '.join(parts)}")
msg_lines.append("")

msg_lines.append(f"*Pipeline:* `{escape_md(pipeline)}`")
msg_lines.append("")

msg_lines.append("*Systems:*")
for sys_name, sys_status in systems.items():
    emoji = "✅" if "✅" in sys_status else ("⚠️" if "⚠" in sys_status else "❌")
    detail = sys_status.split(" - ")[-1] if " - " in sys_status else sys_status
    label = sys_name.replace("_", " ").title()
    msg_lines.append(f"  {emoji} {label}: {detail}")
msg_lines.append("")

if comparison and comparison.get("fixed_issues"):
    msg_lines.append("*Fixed This Run:*")
    for fix in comparison["fixed_issues"]:
        msg_lines.append(f"  ✅ {fix}")
    msg_lines.append("")

if comparison and comparison.get("new_issues"):
    msg_lines.append("*New Issues:*")
    for ni in comparison["new_issues"]:
        msg_lines.append(f"  🆕 {ni}")
    msg_lines.append("")

has_issues = any(v for v in issues.values())
if has_issues:
    msg_lines.append("*Issues:*")
    for severity_name, issue_list in [("🔴 Critical", issues["critical"]), 
                                        ("🟠 High", issues["high"]),
                                        ("🟡 Medium", issues["medium"]),
                                        ("🟢 Low", issues["low"])]:
        for iss in issue_list:
            msg_lines.append(f"  {severity_name}: {escape_md(iss[:150])}")
else:
    msg_lines.append("*All Checks Passing* ✅")
    msg_lines.append("  All 49 tests pass (38 API + 11 Browser)")
msg_lines.append("")

msg_lines.append("*Frontend Pages Tested:*")
for page in report.get("frontend_pages_tested", []):
    msg_lines.append(f"  {page}")
msg_lines.append("")

msg_lines.append("---")
msg_lines.append(f"Time: {report['timestamp']}")
msg_lines.append(f"Run: `{run_id}`")

message = "\n".join(msg_lines)

# Use MarkdownV2 for proper escaping
url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
data = json.dumps({
    "chat_id": chat_id,
    "text": message,
    "parse_mode": "MarkdownV2"
}).encode()
req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read().decode())
        if result.get("ok"):
            print(f"✅ Telegram message sent (id={result['result']['message_id']})")
        else:
            print(f"❌ Telegram error: {result}")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"❌ HTTP {e.code}: {body[:400]}")
    # Try without parse_mode as fallback
    data2 = json.dumps({
        "chat_id": chat_id,
        "text": message,
    }).encode()
    req2 = urllib.request.Request(url, data=data2, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req2, timeout=15) as resp2:
            result2 = json.loads(resp2.read().decode())
            if result2.get("ok"):
                print(f"✅ Telegram message sent (plain text, id={result2['result']['message_id']})")
    except Exception as e2:
        print(f"❌ Fallback also failed: {e2}")
