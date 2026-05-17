# Uptime Monitoring Setup

## Recommended: UptimeRobot (Free - 50 monitors)

1. Sign up at https://uptimerobot.com
2. Add a new monitor:
   - **Type**: HTTP(s)
   - **Friendly name**: Knowledge Factory API
   - **URL**: `https://your-domain.com/health`
   - **Monitoring interval**: 5 minutes
   - **Alert contacts**: Your email, Telegram bot

3. Add monitors for:
   - `GET /health` → should return `{"status":"ok"}`
   - `GET /api/auth/login` → smoke test for auth
   - `GET /api/hiring-cycles` → authenticated endpoint test (use API key header)

## Alternative: BetterStack (Free - 10 monitors)

1. Sign up at https://betterstack.com
2. Create an uptime check:
   - **URL**: `https://your-domain.com/health`
   - **Check interval**: 3 minutes
   - **Locations**: Choose 3 nearest to your users
3. Set up notifications to Telegram/Slack/Email

## Self-hosted: Cron-based health check

Add to crontab:
```bash
# Every 5 minutes, alert if /health fails
*/5 * * * * curl -sf https://your-domain.com/health || curl -X POST https://api.telegram.org/botYOUR_TOKEN/sendMessage -d "chat_id=YOUR_ID" -d "text=Knowledge Factory is DOWN!"
```

## Alerting Rules
- **Critical**: API down > 2 min → SMS + Telegram
- **Warning**: Response time > 3s → Email
- **Info**: Daily uptime report → Email