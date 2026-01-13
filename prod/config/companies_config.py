# -*- coding: utf-8 -*-
"""
Configuration: Liste des compagnies AI a analyser
Inclut ticker, nom complet, et mots-cles pour Google News
"""

AI_COMPANIES = [
    # --- PORTFOLIO THÉMATIQUE (Piliers d'Investissement) ---
    
    # Pilier 1: Cerveau (IA & Logiciel) - 25%
    {
        "ticker": "NVDA",
        "name": "NVIDIA Corporation",
        "search_terms": ["NVIDIA", "NVDA stock", "Jensen Huang", "AI chips"],
        "sector": "AI Hardware",
        "pillar": "Cerveau"
    },
    {
        "ticker": "PLTR",
        "name": "Palantir Technologies",
        "search_terms": ["Palantir AI", "Palantir AIP", "Palantir stock"],
        "sector": "AI Analytics",
        "pillar": "Cerveau"
    },
    {
        "ticker": "VOO",
        "name": "Vanguard S&P 500 ETF",
        "search_terms": ["VOO", "Vanguard S&P 500", "VOO ETF"],
        "sector": "ETF",
        "pillar": "Cerveau"
    },
    {
        "ticker": "GOOGL",
        "name": "Alphabet Inc",
        "search_terms": ["Google AI", "Gemini AI", "DeepMind", "Alphabet stock"],
        "sector": "AI Software",
        "pillar": "Cerveau"
    },
    {
        "ticker": "AMZN",
        "name": "Amazon.com Inc",
        "search_terms": ["Amazon AI", "AWS Bedrock", "Amazon stock"],
        "sector": "AI Software",
        "pillar": "Cerveau"
    },
    {
        "ticker": "CRWD",
        "name": "CrowdStrike Holdings",
        "search_terms": ["CrowdStrike", "CRWD stock", "cybersecurity AI"],
        "sector": "Cybersecurity",
        "pillar": "Cerveau"
    },
    {
        "ticker": "MU",
        "name": "Micron Technology",
        "search_terms": ["Micron", "MU stock", "HBM memory", "AI memory"],
        "sector": "Semiconductors",
        "pillar": "Cerveau"
    },
    {
        "ticker": "AIA",
        "name": "iShares Asia 50 ETF",
        "search_terms": ["AIA ETF", "Asian tech stocks", "TSMC Samsung"],
        "sector": "ETF",
        "pillar": "Cerveau"
    },

    # Pilier 2: Carburant (Uranium & Cuivre) - 20%
    {
        "ticker": "CCO.TO",
        "name": "Cameco Corporation",
        "search_terms": ["Cameco", "uranium", "CCO.TO", "nuclear energy"],
        "sector": "Energy",
        "pillar": "Carburant"
    },
    {
        "ticker": "FCX",
        "name": "Freeport-McMoRan",
        "search_terms": ["Freeport", "FCX stock", "copper mining", "Freeport copper"],
        "sector": "Basic Materials",
        "pillar": "Carburant"
    },
    {
        "ticker": "URA",
        "name": "Global X Uranium ETF",
        "search_terms": ["URA ETF", "uranium stocks", "nuclear energy"],
        "sector": "ETF",
        "pillar": "Carburant"
    },
    {
        "ticker": "BLDP.TO",
        "name": "Ballard Power Systems",
        "search_terms": ["Ballard Power", "BLDP.TO", "fuel cells", "hydrogen"],
        "sector": "Energy",
        "pillar": "Carburant"
    },

    # Pilier 3: Thermostat (Refroidissement) - 15%
    {
        "ticker": "VRT",
        "name": "Vertiv Holdings",
        "search_terms": ["Vertiv", "VRT stock", "data center cooling", "Vertiv infrastructure"],
        "sector": "Technology",
        "pillar": "Thermostat"
    },
    {
        "ticker": "MOD",
        "name": "Modine Manufacturing",
        "search_terms": ["Modine", "MOD stock", "thermal management", "Modine cooling"],
        "sector": "Industrials",
        "pillar": "Thermostat"
    },
    {
        "ticker": "HPS-A.TO",
        "name": "Hammond Power Solutions",
        "search_terms": ["Hammond Power", "HPS.A", "transformers", "power solutions"],
        "sector": "Industrials",
        "pillar": "Thermostat"
    },

    # Pilier 4: Corps (Robots) - 10%
    {
        "ticker": "RBOT.TO",
        "name": "Horizons Robotics & Automation ETF",
        "search_terms": ["RBOT", "robotics ETF", "automation ETF"],
        "sector": "ETF",
        "pillar": "Corps"
    },
    {
        "ticker": "WSP.TO",
        "name": "WSP Global",
        "search_terms": ["WSP Global", "WSP engineering", "WSP.TO", "infrastructure"],
        "sector": "Industrials",
        "pillar": "Corps"
    },

    # Pilier 5: Espace (Défense/Satellites) - 10%
    {
        "ticker": "RKLB",
        "name": "Rocket Lab USA",
        "search_terms": ["Rocket Lab", "RKLB stock", "space launch", "satellites"],
        "sector": "Aerospace",
        "pillar": "Espace"
    },
    {
        "ticker": "MDA.TO",
        "name": "MDA Space",
        "search_terms": ["MDA Space", "MDA.TO", "Canadarm", "satellite systems"],
        "sector": "Aerospace",
        "pillar": "Espace"
    },

    # Pilier 6: Rente (Cash Flow) - 15%
    {
        "ticker": "VDY.TO",
        "name": "Vanguard FTSE Canadian High Dividend Yield",
        "search_terms": ["VDY", "Vanguard dividend", "VDY.TO"],
        "sector": "ETF",
        "pillar": "Rente"
    },
    {
        "ticker": "JEPI",
        "name": "JPMorgan Equity Premium Income ETF",
        "search_terms": ["JEPI", "JPMorgan income", "JEPI ETF"],
        "sector": "ETF",
        "pillar": "Rente"
    },
    {
        "ticker": "JEPQ",
        "name": "JPMorgan Nasdaq Equity Premium",
        "search_terms": ["JEPQ", "JEPQ ETF", "Nasdaq income"],
        "sector": "ETF",
        "pillar": "Rente"
    },
    {
        "ticker": "DGS.TO",
        "name": "Dividend Growth Split Corp",
        "search_terms": ["DGS.TO", "Dividend Growth Split", "Brompton Funds"],
        "sector": "ETF",
        "pillar": "Rente"
    },

    # Pilier 7: Joker (Crypto) - 5%
    {
        "ticker": "FBTC.TO",
        "name": "Fidelity Advantage Bitcoin ETF",
        "search_terms": ["FBTC", "Fidelity Bitcoin", "Bitcoin ETF Canada"],
        "sector": "Crypto",
        "pillar": "Joker"
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
    },
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
