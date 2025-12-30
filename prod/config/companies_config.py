# -*- coding: utf-8 -*-
"""
Configuration: Liste des compagnies AI a analyser
Inclut ticker, nom complet, et mots-cles pour Google News
"""

AI_COMPANIES = [
    {
        "ticker": "NVDA",
        "name": "NVIDIA Corporation",
        "search_terms": ["NVIDIA", "NVDA stock", "Jensen Huang"],
        "sector": "AI Hardware"
    },
    {
        "ticker": "MSFT",
        "name": "Microsoft Corporation",
        "search_terms": ["Microsoft AI", "Azure AI", "Copilot", "OpenAI Microsoft"],
        "sector": "AI Software"
    },
    {
        "ticker": "GOOGL",
        "name": "Alphabet Inc",
        "search_terms": ["Google AI", "Gemini AI", "DeepMind", "Alphabet stock"],
        "sector": "AI Software"
    },
    {
        "ticker": "META",
        "name": "Meta Platforms",
        "search_terms": ["Meta AI", "LLaMA", "Facebook AI", "Mark Zuckerberg AI"],
        "sector": "AI Software"
    },
    {
        "ticker": "AMZN",
        "name": "Amazon.com Inc",
        "search_terms": ["Amazon AI", "AWS AI", "Amazon Bedrock", "Alexa AI"],
        "sector": "AI Cloud"
    },
    {
        "ticker": "AMD",
        "name": "Advanced Micro Devices",
        "search_terms": ["AMD AI", "AMD chips", "Lisa Su", "AMD data center"],
        "sector": "AI Hardware"
    },
    {
        "ticker": "TSLA",
        "name": "Tesla Inc",
        "search_terms": ["Tesla AI", "Tesla FSD", "Tesla Optimus", "Tesla autonomous"],
        "sector": "AI Automotive"
    },
    {
        "ticker": "ORCL",
        "name": "Oracle Corporation",
        "search_terms": ["Oracle AI", "Oracle Cloud", "Oracle database AI"],
        "sector": "AI Cloud"
    },
    {
        "ticker": "CRM",
        "name": "Salesforce Inc",
        "search_terms": ["Salesforce AI", "Einstein AI", "Salesforce Agentforce"],
        "sector": "AI Software"
    },
    {
        "ticker": "PLTR",
        "name": "Palantir Technologies",
        "search_terms": ["Palantir AI", "Palantir AIP", "Palantir stock"],
        "sector": "AI Analytics"
    },
    {
        "ticker": "SNOW",
        "name": "Snowflake Inc",
        "search_terms": ["Snowflake AI", "Snowflake data cloud", "Snowflake ML"],
        "sector": "AI Data"
    },
    {
        "ticker": "AVGO",
        "name": "Broadcom Inc",
        "search_terms": ["Broadcom AI", "Broadcom chips", "Broadcom semiconductor"],
        "sector": "AI Hardware"
    },
    {
        "ticker": "ADBE",
        "name": "Adobe Inc",
        "search_terms": ["Adobe AI", "Adobe Firefly", "Adobe Sensei"],
        "sector": "AI Creative"
    },
    {
        "ticker": "NOW",
        "name": "ServiceNow Inc",
        "search_terms": ["ServiceNow AI", "ServiceNow Now Assist"],
        "sector": "AI Software"
    },
    {
        "ticker": "INTC",
        "name": "Intel Corporation",
        "search_terms": ["Intel AI", "Intel chips", "Intel Gaudi", "Intel Xeon"],
        "sector": "AI Hardware"
    }
]

# Compagnies privees (pas de ticker boursier mais importantes)
PRIVATE_AI_COMPANIES = [
    {
        "ticker": "OPENAI",
        "name": "OpenAI",
        "search_terms": ["OpenAI", "ChatGPT", "GPT-4", "Sam Altman"],
        "sector": "AI Research"
    },
    {
        "ticker": "ANTHROPIC",
        "name": "Anthropic",
        "search_terms": ["Anthropic", "Claude AI", "Dario Amodei"],
        "sector": "AI Research"
    },
    {
        "ticker": "COHERE",
        "name": "Cohere",
        "search_terms": ["Cohere AI", "Cohere LLM"],
        "sector": "AI Research"
    },
    {
        "ticker": "MISTRAL",
        "name": "Mistral AI",
        "search_terms": ["Mistral AI", "Mistral LLM"],
        "sector": "AI Research"
    }
]

def get_all_companies():
    """Retourne toutes les compagnies (publiques + privees)"""
    return AI_COMPANIES + PRIVATE_AI_COMPANIES

def get_public_companies():
    """Retourne seulement les compagnies cotees en bourse"""
    return AI_COMPANIES

def get_company_by_ticker(ticker):
    """Trouve une compagnie par son ticker"""
    all_companies = get_all_companies()
    for company in all_companies:
        if company['ticker'] == ticker:
            return company
    return None

def get_search_query(company):
    """Genere la requete Google News pour une compagnie"""
    # Combine nom + termes de recherche
    terms = [company['name']] + company['search_terms']
    return " OR ".join(f'"{term}"' for term in terms)

if __name__ == "__main__":
    print("=== Compagnies AI Configurees ===\n")
    
    print("PUBLIQUES (cotees en bourse):")
    for company in AI_COMPANIES:
        print(f"  {company['ticker']:6} - {company['name']:30} ({company['sector']})")
    
    print(f"\nTotal publiques: {len(AI_COMPANIES)}")
    
    print("\n\nPRIVEES:")
    for company in PRIVATE_AI_COMPANIES:
        print(f"  {company['ticker']:10} - {company['name']:30} ({company['sector']})")
    
    print(f"\nTotal privees: {len(PRIVATE_AI_COMPANIES)}")
    print(f"\nGRAND TOTAL: {len(get_all_companies())} compagnies")
    
    # Test requete
    print("\n\n=== Exemple de requete Google News ===")
    nvda = get_company_by_ticker("NVDA")
    print(f"\nCompagnie: {nvda['name']}")
    print(f"Requete: {get_search_query(nvda)}")
