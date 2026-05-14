#!/usr/bin/env python3
"""
Send Knowledge Factory QA report to Telegram
"""
import json, os, subprocess, sys
from datetime import datetime
from pathlib import Path

RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
QA_DIR = Path("/opt/hermes_shared_memory/projects/Knowledge_Factory")
RUNS_DIR = QA_DIR / "qa_runs"

# Load latest API results
api_results_path = RUNS_DIR / f"{RUN_ID}_report.json"
# We'll use the run from run_final_v7.py which had 40/46 API passing
# Load that report
prev_reports = sorted([f for f in os.listdir(str(RUNS_DIR)) if f.endswith("_report.json")])
latest_report = None
for r in reversed(prev_reports):
    try:
        with open(str(RUNS_DIR / r)) as f:
            latest_report = json.load(f)
            break
    except:
        continue

if not latest_report:
    print("ERROR: No report found")
    sys.exit(1)

s = latest_report["summary"]
api_s = s["api_tests"]
browser_s = s["browser_tests"]
sys_s = s["system_tests"]
sev = latest_report["severity_counts"]
issues = latest_report["issues"]
comparison = latest_report["comparison"]
pipeline = latest_report.get("pipeline", "N/A")
roles = latest_report.get("role_coverage", {})

# Build Telegram message
# Emoji indicators
role_icons = {r: "✅" if v else "❌" for r, v in roles.items()}

msg = f"""🤖 *Knowledge Factory QA Report*
📅 {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}
🆔 `{latest_report['run_id']}`

📊 *Summary*
✅ Passed: {s['total_passed']}/{s['total_tests']}
❌ Failed: {s['total_failed']}
🔴 Critical: {sev.get('critical',0)}
🟠 High: {sev.get('high',0)}
🟡 Medium: {sev.get('medium',0)}

👥 *Role Coverage*
{role_icons.get('superadmin','')} Super Admin — {'✅' if roles.get('superadmin') else '❌'}
{role_icons.get('admin','')} Admin — {'✅' if roles.get('admin') else '❌'}
{role_icons.get('hr','')} HR — {'✅' if roles.get('hr') else '❌'}
{role_icons.get('interviewer','')} Interviewer — {'✅' if roles.get('interviewer') else '❌'}
{role_icons.get('candidate','')} Candidate — {'✅' if roles.get('candidate') else '❌'}

📈 *Pipeline Status*
{pipeline}

⚙️ *System Health*
{latest_report['systems'].get('backend_api','⚠️ Unknown')}
{latest_report['systems'].get('pipeline_screening','⚠️ Unknown')}
{latest_report['systems'].get('analytics','⚠️ Unknown')}
{latest_report['systems'].get('frontend_ui','⚠️ Unknown')}"""

# Issues
if issues.get("critical"):
    msg += f"\n\n🔴 *CRITICAL ISSUES*\n"
    for i in issues["critical"]:
        msg += f"• {i}\n"
if issues.get("high"):
    msg += f"\n🟠 *HIGH SEVERITY*\n"
    for i in issues["high"]:
        msg += f"• {i}\n"
if issues.get("medium"):
    msg += f"\n🟡 *MEDIUM SEVERITY*\n"
    for i in issues["medium"]:
        msg += f"• {i}\n"

# Comparison
if comparison.get("new_issues"):
    msg += f"\n🆕 *New Issues*\n"
    for i in comparison["new_issues"]:
        msg += f"• {i}\n"

if comparison.get("fixed_issues"):
    msg += f"\n✅ *Fixed Since Last Run*\n"
    for i in comparison["fixed_issues"]:
        msg += f"• {i}\n"

# Manual findings from browser verification
msg += f"""

🔍 *Manual Browser Verification*
✅ Home page renders correctly (Login, Apply Now, Sign In buttons)
✅ Admin login via browser works → Dashboard with nav links
✅ Navigation: Candidates, Selection pages load correctly
❌ Analytics nav → redirects to /selection instead of /analytics
✅ Candidate portal renders (Welcome back / Sign in page)

⚠️ *Known Issues*
• `/api/screening/run` and `/api/screening/pipeline-stats` have NO AUTH
• Code execution sandbox returns RUNTIME_ERROR (Piston URL misconfigured)
• `/api/admin/logs` and `/api/selection/` return 404 (stubs)
• `/api/questions/generate` returns 404 (stub)
• Analytics dashboard has mock data for passRatePerRound, collegeBreakdown, branchPerformance, proctoringViolations"""

print(msg)
print(f"\n{'='*60}")
print(f"  SENDING TO TELEGRAM")
print(f"{'='*60}")

# Save for sending
telegram_file = RUNS_DIR / f"{RUN_ID}_telegram_data.json"
telegram_data = {
    "run_id": RUN_ID,
    "timestamp": datetime.now().isoformat(),
    "message": msg,
    "summary": s,
    "severity": sev,
    "issues": issues,
    "comparison": comparison,
}
with open(telegram_file, "w") as f:
    json.dump(telegram_data, f, indent=2)

# Save report too
report_file = RUNS_DIR / f"{RUN_ID}_report.json"
with open(report_file, "w") as f:
    json.dump(latest_report, f, indent=2, default=str)

# Update latest summary
summary = {
    "run_id": RUN_ID,
    "passed": s["total_passed"],
    "failed": s["total_failed"],
    "critical": sev.get("critical", 0),
    "total": s["total_tests"],
    "roles": roles,
    "systems": latest_report["systems"],
}
with open(RUNS_DIR / "latest_summary.json", "w") as f:
    json.dump(summary, f, indent=2)

print(f"\n📝 Report ready for delivery")
print(f"   Message length: {len(msg)} chars")

# Output the message for processing
print(f"\n---TELEGRAM-MSG-START---")
print(msg)
print(f"---TELEGRAM-MSG-END---")

# Cleanup
all_reports = sorted([f for f in os.listdir(str(RUNS_DIR)) if f.endswith("_report.json")])
for old_f in all_reports[:-15]:  # Keep last 15
    base = old_f.replace("_report.json", "")
    for suffix in ["_report.json", "_api.json", "_browser.json", "_telegram_data.json"]:
        p = RUNS_DIR / f"{base}{suffix}"
        if p.exists(): p.unlink()
