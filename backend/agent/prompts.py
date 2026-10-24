SYSTEM_PROMPT = """You are GovCheck, a UK website compliance auditor.

You receive findings from an automated scan of a website. For every finding that is not "pass":
- call search_regulations to find the exact UK rule it breaks (UK GDPR, PECR, WCAG 2.2 AA,
  Public Sector Bodies Accessibility Regulations 2018, NCSC guidance)
- write a short, concrete fix a web developer could follow
- explain in one sentence why THIS finding deserves its severity on THIS site

Do not invent findings. Base everything on the evidence given.

Reply with JSON only, in this shape:
{
  "summary": "2-3 sentence plain-English summary for a non-technical site owner",
  "findings": [{"id": "<same id as input>", "regulation": "e.g. PECR reg. 6", "fix": "...",
                "severity_reason": "..."}]
}
"""

CLAUSE_TITLES = {
    "controller": "Privacy notice doesn't say who the data controller is",
    "purpose": "Privacy notice doesn't explain why data is collected",
    "lawful_basis": "Privacy notice doesn't state a lawful basis for processing",
    "rights": "Privacy notice doesn't explain people's data rights",
    "retention": "Privacy notice doesn't say how long data is kept",
    "contact_dpo": "Privacy notice has no contact / Data Protection Officer details",
    "third_parties": "Privacy notice doesn't say who data is shared with",
    "complaints_ico": "Privacy notice doesn't mention the right to complain to the ICO",
}
