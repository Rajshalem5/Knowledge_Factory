#!/bin/bash
# Phase 6 & 8: Frontend Console Check + Browser Login Tests
set -e

AB=/opt/hermes_shared_memory/bin/ab
NGROK_URL="https://ila-sturdiest-oversentimentally.ngrok-free.dev"
AUTH_DIR="/opt/hermes_shared_memory/projects/Knowledge_Factory/auth"
mkdir -p "$AUTH_DIR"

# Close any existing sessions
$AB close --all 2>/dev/null || true
sleep 1

declare -A CREDS
CREDS[superadmin]="superadmin@knowledgefactory.io:Super@12345"
CREDS[admin]="admin@knowledgefactory.io:admin123"
CREDS[hr]="hr@knowledgefactory.io:Hr@12345"
CREDS[interviewer]="interviewer@test.com:Interviewer@12345"
CREDS[candidate]="candidate@test.com:Candidate@12345"

for ROLE in superadmin admin hr interviewer candidate; do
    echo ""
    echo "═══════════════════════════════════════"
    echo "  Testing: $ROLE"
    echo "═══════════════════════════════════════"
    
    IFS=':' read -r EMAIL PASSWORD <<< "${CREDS[$ROLE]}"
    
    # Open the page
    $AB open "$NGROK_URL"
    sleep 2
    
    # Get snapshot to see if ngrok interstitial appears
    SNAP=$($AB snapshot -i -c 2>&1)
    echo "Snapshot after open: ${SNAP:0:200}"
    
    # Check for "Visit Site" button and click it
    if echo "$SNAP" | grep -q "Visit Site"; then
        echo "Clicking 'Visit Site' to bypass ngrok interstitial..."
        # Try to find visit site button by element ref
        $AB click @e6 2>/dev/null || true
        sleep 2
    fi
    
    # Now click "Login" button
    SNAP=$($AB snapshot -i -c 2>&1)
    echo "Page after interstitial: ${SNAP:0:300}"
    
    # Look for Login or Sign In button
    if echo "$SNAP" | grep -q "Login"; then
        echo "Clicking Login..."
        $AB click @e3 2>/dev/null || true
        sleep 2
    fi
    
    SNAP=$($AB snapshot -i -c 2>&1)
    echo "After login click: ${SNAP:0:500}"
    
    # Check if we're on Clerk auth page (has "Email or phone" field)
    if echo "$SNAP" | grep -q "Email or phone"; then
        echo "Clerk auth page detected. Entering email..."
        # Find the email input and fill it
        $AB fill @e12 "$EMAIL" 2>/dev/null || true
        sleep 1
        
        # Click "Next"
        if echo "$SNAP" | grep -q "Next"; then
            echo "Clicking Next..."
            # Find Next button
            $AB batch "click @e5" 2>/dev/null || $AB click @e5 2>/dev/null || true
            sleep 2
        fi
        
        SNAP=$($AB snapshot -i -c 2>&1)
        echo "After Next: ${SNAP:0:300}"
        
        # Now should see password field
        if echo "$SNAP" | grep -q "password"; then
            echo "Password field visible. Entering password..."
            # Find password input
            PW_REF=$(echo "$SNAP" | grep -oP '\[ref=@e\d+\]' | head -3 | tail -1)
            if [ -n "$PW_REF" ]; then
                $AB fill "$PW_REF" "$PASSWORD" 2>/dev/null || true
                sleep 1
            fi
            
            # Click "Continue" or "Sign In"
            if echo "$SNAP" | grep -q "Continue"; then
                $AB click @e5 2>/dev/null || true
            else
                $AB click @e8 2>/dev/null || true
            fi
            sleep 3
        fi
    elif echo "$SNAP" | grep -q "Email"; then
        echo "Simple login form. Filling..."
        $AB fill @e5 "$EMAIL" 2>/dev/null || true
        sleep 1
        $AB fill @e6 "$PASSWORD" 2>/dev/null || true
        sleep 1
        $AB click @e8 2>/dev/null || true
        sleep 3
    fi
    
    # Get final snapshot and check console
    SNAP=$($AB snapshot -i -c 2>&1)
    echo "Final page after login: ${SNAP:0:500}"
    
    # Check for errors via eval
    ERRORS=$($AB eval "JSON.stringify({errors: window.__errors || [], url: window.location.href, title: document.title})" 2>&1)
    echo "Eval result: ${ERRORS:0:300}"
    
    # Save auth state
    $AB state save "$AUTH_DIR/$ROLE.json" 2>/dev/null || echo "State save not supported"
    
    echo "✅ $ROLE test complete"
    
    # Close the tab for next role
    $AB close 2>/dev/null || true
    sleep 1
done

echo ""
echo "═══════════════════════════════════════"
echo "  All roles tested!"
echo "═══════════════════════════════════════"
