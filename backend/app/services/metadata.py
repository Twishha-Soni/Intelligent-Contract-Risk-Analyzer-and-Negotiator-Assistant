CLAUSE_CATEGORIES: dict[str, list[str]] = {
    "indemnification": ["indemnify", "indemnification", "hold harmless"],
    "limitation_of_liability": ["limitation of liability", "liability shall not exceed", "consequential damages"],
    "auto_renewal_termination": ["auto-renew", "automatic renewal", "termination", "terminate this agreement"],
    "ip_assignment": ["intellectual property", "assignment of inventions", "work product", "ip assignment"],
    "non_compete_non_solicit": ["non-compete", "non-solicitation", "restrictive covenant"],
    "governing_law_jurisdiction": ["governing law", "jurisdiction", "venue", "choice of law"],
    "data_protection": ["data protection", "personal data", "gdpr", "confidential information"],
    "payment_terms": ["payment terms", "invoice", "net 30", "late fee", "fees due"],
}

def classify_category(section_title: str, chunk_text: str) -> str:
    combined = f'{section_title} {chunk_text}'.lower()
    best_category, best_score = 'uncategorized', 0
    for category, terms in CLAUSE_CATEGORIES.items():
        score = sum(1 for term in terms if term in combined)
        if score > best_score:
            best_category, best_score = category, score
    return best_category