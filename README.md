# Apollo MCP - B2B Prospecting & Enrichment

Single API key setup (no OAuth) for Apollo.io. Provides company/people search and lead enrichment.

## Features

- ✅ **Free Tier Company Search** - Up to 50 organizations with people profiles
- ✅ **Free Tier People Search** - Search by title, company, country
- ✅ **Paid Email Enrichment** - 1 credit per verified work email
- ✅ **ICP Scoring Rubric** - Score leads 0-10 on fit for Twynity

## Toolset

| Tool | Cost | Description |
|------|------|-----------|
| `apollo_search_organizations` | Free | Search EU companies (50-500 employees, top industries) |
| `apollo_search_people` | Free | Search people by title/company/country |
| `apollo_enrich_person` | 1 credit | Get verified work email for a person |
| `apollo_score_lead` | Free | Score lead 0-10 on ICP fit |

## Setup

### 1. Get Apollo API Key

1. Go to [https://www.apollo.io/](https://www.apollo.io/)
2. Sign up for free
3. Get API key from [https://www.apollo.io/api/](https://www.apollo.io/api/)

### 2. Configure Environment

```bash
# Copy .env.example to .env
cp .env.example .env

# Edit .env with your API key
echo "APOLLO_API_KEY=your_key_here" > .env
```

### 3. Run Server

```bash
# Using Docker (recommended)
docker build -t apollo-mcp .
docker run -p 8000:8000 -v $(pwd):/app --env-file .env apollo-mcp

# Or with Python
pip install -r requirements.txt
python -m app.main
```

### 4. Deploy to Render

1. Push to GitHub
2. Connect Render → New Web Service
3. Select GitHub repo
4. Set env var: `APOLLO_API_KEY`
5. Deploy!

## Usage Examples

### Search EU Tech Companies

```python
# Maya's workflow:
# 1. Search 50 EU companies (50-500 employees, SaaS/Logistics)
apollo_search_organizations(
    limit=50,
    countries="DE,FR,IT,ES,NL,BE,AT,SE,NO,DK,UK",
    employee_count_ranges="50-500,501-2000",
    industries="SaaS,B2B_SaaS,Logistics",
    job_titles="CTO,Head_of_AI,VP_of_Engineering",
)

# 2. Score each lead 0-10 on ICP fit
apollo_score_lead(person={
    "country": "DE",
    "company_size": "50-500",
    "industry": "SaaS",
    "title": "CTO",
})

# 3. Enrich only top 5 leads (8+ score) with verified email
apollo_enrich_person(person_id="123456")
```

### Smart Credit Saving

```python
# Free tier: 50 orgs × 30 people = 1500 people search
# Only enrich 5 top leads: 5 credits/month

# That's $0 for 1500 leads/month! 🎉
```

## ICP Scoring Rubric

Scores 0-10 on:

- **Region** (2 pts max): EU countries only
- **Company Size** (3 pts max): 50-500 = 3 pts
- **Industry** (3 pts max): SaaS/B2B_SaaS = 3 pts
- **Job Title** (3 pts max): CTO/Head of AI = 5 pts

## Deployment

### Render (Free Tier)

```bash
# Deploy to Render
git init
git add .
git commit -m "Initial Apollo MCP commit"
git remote add origin https://github.com/YOUR_USERNAME/apollo-mcp.git
git push -u origin master

# Then connect via Render dashboard
```

## License

MIT
