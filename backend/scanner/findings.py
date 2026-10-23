"""Every check builds its findings with finding() so they all have the same shape
(see docs/scan_result.schema.json)."""


def finding(id, category, severity, title, evidence="", page="", regulation="", fix=""):
    return {
        "id": id,
        "category": category,      # accessibility | cookies | privacy | security
        "severity": severity,      # critical | high | medium | low | pass
        "title": title,
        "evidence": evidence,      # exactly what we saw: cookie names, header values, counts
        "page": page,
        "regulation": regulation,  # the agent fills this in if left empty
        "fix": fix,                # the agent fills this in if left empty
    }
