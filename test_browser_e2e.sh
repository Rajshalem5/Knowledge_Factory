#!/bin/bash
# Run Knowledge Factory browser E2E tests using ab CLI
BASE_URL="https://ila-sturdiest-oversentimentally.ngrok-free.dev"
AB="/opt/hermes_shared_memory/bin/ab"
FAILURES_DIR="/opt/hermes_shared_memory/projects/Knowledge_Factory/failures"
RUN_ID=$(date +%Y%m%d_%H%M%S)
mkdir -p "$FAILURES_DIR/$RUN_ID"

echo "================================================================="
echo "  KF E2E Browser Tests - Run $RUN_ID"
echo "================================================================="

# Clean start
$AB close --all 2>/dev/null

# ----------------------------------------
# Test 1: Login as Super Admin
# ----------------------------------------
echo ""
echo "[TEST] Super Admin Login"
echo "----------------------------------------"

# Navigate to app
$AB open "$BASE_URL" 2>&1 | tail -3

# Wait for page to load
sleep 2

# Take initial screenshot
$AB screenshot "$FAILURES_DIR/$RUN_ID/01_superadmin_home.png" 2>&1 | tail -2

# Get page snapshot to find login elements
SNAPSHOT=$($AB snapshot -i -c 2>&1)
echo "Page elements:"
echo "$SNAPSHOT" | head -20

# Try to log in via JavaScript (more reliable than clicking)
echo ""
echo "Attempting login via JS..."
$AB eval "
document.querySelector('input[type=\"email\"]')?.value 
  ? 'Email field found' 
  : 'No email field - checking login link'
" 2>&1

# Check if we're on a login page or need to navigate
$AB eval "document.title" 2>&1
$AB eval "window.location.href" 2>&1

# Check console
$AB console 2>&1 | head -5

echo ""
echo "[DONE] Super Admin test"
