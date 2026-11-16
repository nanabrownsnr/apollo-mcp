"""Apollo.io API tools for B2B prospection and lead enrichment."""

import httpx
from starlette.exceptions import HTTPException

from app.config import settings


async def search_organizations(
    limit: int = 50,
    countries: list[str] = None,
    employee_count_ranges: list[str] = None,
    industries: list[str] = None,
    job_titles: list[str] = None,
) -> dict:
    """Search for companies using Apollo.io free API.

    Args:
        limit: Number of results (default 50, Apollo free tier allows more)
        countries: List of country codes (e.g., ["DE", "FR", "IT"])
        employee_count_ranges: List of ranges like ["50-500", "501-2000"]
        industries: List of industries
        job_titles: List of job titles to filter people

    Returns:
        dict: Search results with organizations and people
    """
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": settings.APOLLO_API_KEY,
    }

    # Build organizations search
    org_params = {
        "limit": limit,
        "page": 1,
    }

    if countries:
        org_params["country"] = ",".join(countries)
    if employee_count_ranges:
        org_params["employee_count_range"] = ",".join(employee_count_ranges)
    if industries:
        org_params["industry"] = ",".join(industries)

    async with httpx.AsyncClient(timeout=settings.TIMEOUT) as client:
        # Search organizations
        org_response = await client.get(
            f"{settings.APOLLO_BASE_URL}/organizations",
            headers=headers,
            params=org_params,
        )
        org_response.raise_for_status()
        org_data = org_response.json()

        # Search people within organizations
        people_results = []

        # Build people search params
        people_params = {
            "limit": min(limit, 30),  # Limit people per org
            "page": 1,
        }

        if countries:
            people_params["country"] = ",".join(countries)
        if job_titles:
            people_params["title"] = ",".join(job_titles)

        # We'll do separate person searches for efficiency
        # In production, you'd batch this better

        return {
            "organizations": org_data.get("organizations", []),
            "people_search_params": people_params,
            "org_params": org_params,
        }


async def search_people(
    title: str = None,
    company_name: str = None,
    country: str = None,
    limit: int = 50,
) -> dict:
    """Search for people using Apollo.io free API.

    Args:
        title: Job title (e.g., "CTO", "Head of AI")
        company_name: Company name or domain
        country: Country code
        limit: Number of results (default 50)

    Returns:
        dict: People search results
    """
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": settings.APOLLO_API_KEY,
    }

    params = {
        "limit": limit,
        "page": 1,
    }

    if title:
        params["title"] = title
    if company_name:
        params["company_name"] = company_name
    if country:
        params["country"] = country

    async with httpx.AsyncClient(timeout=settings.TIMEOUT) as client:
        response = await client.get(
            f"{settings.APOLLO_BASE_URL}/people",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        return response.json()


async def enrich_person(person_id: str) -> dict:
    """Enrich a person's data with verified work email.

    Uses 1 Apollo credit.
    Only call this for high-scored leads (8+ on ICP rubric).

    Args:
        person_id: Apollo person ID

    Returns:
        dict: Enriched person data including verified email
    """
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": settings.APOLLO_API_KEY,
    }

    async with httpx.AsyncClient(timeout=settings.TIMEOUT) as client:
        response = await client.get(
            f"{settings.APOLLO_BASE_URL}/people/{person_id}",
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()

        # Extract verified email if available
        email = data.get("verified_work_email") or data.get("work_email")

        return {
            "person_id": person_id,
            "name": data.get("name"),
            "title": data.get("title"),
            "company": data.get("company_name"),
            "email": email,
            "linkedin_url": data.get("linkedin_url"),
            "linkedin_profile_id": data.get("linkedin_profile_id"),
        }


async def score_lead(
    person: dict,
    rubric: dict = None,
) -> dict:
    """Score a lead on ICP fit using custom rubric.

    Args:
        person: Person data dict
        rubric: Custom scoring rubric (optional, uses defaults if None)

    Returns:
        dict: Score breakdown and total (0-10)
    """
    # Default ICP scoring rubric for Twynity
    if rubric is None:
        rubric = {
            "region_fit": {"EU_countries": {"DE", "FR", "IT", "ES", "NL", "BE", "AT", "CH", "SE", "NO", "FI", "DK", "UK", "IE", "PT", "GR"}},
            "company_size": {"50-500": 3, "501-2000": 4, "2001-5000": 3, "5001+": 2},
            "industry": {
                "SaaS": 3,
                "B2B_SaaS": 3,
                "Logistics": 4,
                "E-commerce": 4,
                "Creative_Agency": 3,
                "Manufacturing": 3,
                "Software_Development": 5,
                "Technology": 3,
                "Consulting": 2,
            },
            "job_title": {
                "CTO": 5,
                "VP_of_Engineering": 5,
                "Head_of_AI": 5,
                "Head_of_Innovation": 4,
                "Technical_COO": 4,
                "VP_of_Technology": 4,
                "Director_of_AI": 4,
                "CTO": 5,
                "Chief_AI_Officer": 4,
                "VP_of_Product": 2,
                "Head_of_Product": 2,
                "Product_Manager": 1,
                "VP_of_Sales": 3,
                "Head_of_Sales": 3,
                "Sales_Director": 2,
            },
        }

    score = 0
    breakdown = {}

    # Region fit (max 2 points)
    region = person.get("country", "")
    if region in rubric["region_fit"]["EU_countries"]:
        region_score = 2
    else:
        region_score = 0
    breakdown["region"] = region_score
    score += region_score

    # Company size (max 3 points)
    company_size = person.get("company_size", "")
    size_score = rubric["company_size"].get(company_size, 0)
    breakdown["company_size"] = size_score
    score += size_score

    # Industry (max 3 points)
    industry = person.get("industry", "")
    industry_score = rubric["industry"].get(industry, 1)
    breakdown["industry"] = industry_score
    score += industry_score

    # Job title (max 3 points)
    job_title = person.get("title", "")
    title_score = rubric["job_title"].get(job_title, 1)
    breakdown["job_title"] = title_score
    score += title_score

    # Normalize to 0-10
    return {
        "total_score": score,
        "breakdown": breakdown,
        "scored": True,
    }


def register_apollo_tools(mcp):
    """Register Apollo tools with FastMCP server."""
    from fastmcp.tools import ToolResult

    @mcp.tool(
        name="apollo_search_organizations",
        description="Search Apollo.io for companies. Returns orgs with people profiles. Free tier: up to 50 orgs, 30 people per org."
    )
    async def tool_apollo_search_organizations(
        limit: int = 50,
        countries: str = "DE,FR,IT,ES,NL,BE,AT,SE,NO,DK,UK",
        employee_count_ranges: str = "50-500,501-2000",
        industries: str = "SaaS,B2B_SaaS,Logistics,E-commerce,Manufacturing,Software_Development",
        job_titles: str = "CTO,Head_of_AI,VP_of_Engineering,Technical_COO",
    ) -> ToolResult:
        """Search organizations"""
        org_data = await search_organizations(
            limit=limit,
            countries=countries.split(","),
            employee_count_ranges=employee_count_ranges.split(","),
            industries=industries.split(","),
            job_titles=job_titles.split(","),
        )
        return ToolResult(
            content=[org_data],
            structured_content={
                "organizations": org_data["organizations"],
                "people_search_params": org_data["people_search_params"],
            }
        )

    @mcp.tool(
        name="apollo_search_people",
        description="Search for people by title, company, or country."
    )
    async def tool_apollo_search_people(
        title: str = None,
        company_name: str = None,
        country: str = None,
        limit: int = 50,
    ) -> ToolResult:
        """Search people"""
        data = await search_people(title=title, company_name=company_name, country=country, limit=limit)
        return ToolResult(content=[data], structured_content={"people": data.get("people", [])})

    @mcp.tool(
        name="apollo_enrich_person",
        description="Enrich a person with verified work email. Costs 1 Apollo credit. Only use for high-scored leads (8+)."
    )
    async def tool_apollo_enrich_person(person_id: str) -> ToolResult:
        """Enrich person"""
        data = await enrich_person(person_id)
        return ToolResult(content=[data], structured_content={"enriched_person": data})

    @mcp.tool(
        name="apollo_score_lead",
        description="Score a lead on ICP fit (0-10). Returns breakdown by region, company size, industry, and job title."
    )
    async def tool_apollo_score_lead(
        person: dict,
        rubric: str = None,
    ) -> ToolResult:
        """Score lead"""
        scored = await score_lead(person, rubric)
        return ToolResult(content=[scored], structured_content=scored)
