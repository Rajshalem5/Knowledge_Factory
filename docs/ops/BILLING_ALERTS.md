# Billing Alerts Setup

Set budget alerts on all cloud services to prevent surprise charges.

## Supabase
1. Dashboard > Project Settings > Billing
2. Set "Budget Alert" → notify at 80% of planned spend
3. Set "Usage Alert" → warn when approaching row limits
4. Email alerts to shalem@knowledge-factory.com

## OpenAI (AI Question Generation)
1. https://platform.openai.com/account/usage
2. Set spend cap: $10/month for dev, $50/month for prod
3. Enable email alerts for 50%, 80%, 100% usage

## SendGrid (Email)
1. https://app.sendgrid.com/settings/billing
2. Set monthly budget alerts

## AWS (if using S3/storage)
1. AWS Console > Billing > Budgets
2. Create budget: Actual spend, alert at $5, $10, $20
3. Alert to: shalem@knowledge-factory.com

## Quick Check Command
```bash
# Check current month spend
curl -s "https://api.openai.com/dashboard/billing/usage" \
  -H "Authorization: Bearer $OPENAI_API_KEY" | jq '.total_usage'
```

## Cost Optimization Tips
- Use SQLite for dev to avoid Supabase compute costs
- Set AI_MODEL=qwen3-coder-30b (cheaper than GPT-4)
- Enable caching: Redis for sessions, CDN for static assets
- Use rate limits to prevent runaway AI costs