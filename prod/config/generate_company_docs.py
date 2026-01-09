import sys
import os
import json
import requests

# Add parent dir to path to import companies_config
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
import companies_config

def generate_description(company):
    prompt = f"Donne une description très courte (1 phrase, max 15 mots) en français de la compagnie '{company['name']}' ({company['ticker']}) et son lien avec l'IA ou son activité principale."
    try:
        resp = requests.post('http://localhost:11434/api/generate', json={
            "model": "llama3.1:8b",
            "prompt": prompt,
            "stream": False
        })
        # Clean up response (remove quotes, newlines)
        text = resp.json()['response'].strip().replace('"', '').replace('\n', ' ')
        return text
    except:
        return f"Compagnie du secteur {company['sector']}."

def main():
    print("🚀 Démarrage de la génération de documentation...")
    all_companies = companies_config.get_all_companies()
    
    # Group by Sector
    by_sector = {}
    for c in all_companies:
        s = c['sector']
        if s not in by_sector: by_sector[s] = []
        by_sector[s].append(c)
        
    # Generate MD content
    md_content = "# 🏢 Univers des Compagnies Analysées\n\n"
    md_content += f"**Total:** {len(all_companies)} compagnies suivies.\n\n"
    
    print(f"📝 Génération des descriptions pour {len(all_companies)} compagnies...")
    
    # Process and add descriptions
    for sector, companies in by_sector.items():
        md_content += f"## 🔹 {sector}\n\n"
        for c in companies:
            print(f"  - {c['ticker']}...", end='', flush=True)
            desc = generate_description(c)
            # Add to company dict for backup
            c['description'] = desc 
            print(f" OK")
            
            md_content += f"### {c['name']} ({c['ticker']})\n"
            md_content += f"{desc}\n\n"
            
    with open(os.path.join(current_dir, 'analyzed_companies.md'), 'w', encoding='utf-8') as f:
        f.write(md_content)
    print(f"\n✅ Markdown généré: {os.path.join(current_dir, 'analyzed_companies.md')}")
        
    # Generate Backup Py content
    py_content = "# -*- coding: utf-8 -*-\n"
    py_content += '"""\nBACKUP Configuration des compagnies (Généré automatiquement)\nInclut descriptions générées par IA\n"""\n\n'
    py_content += "AI_COMPANIES = [\n"
    
    def format_company(c):
        res = "    {\n"
        res += f'        "ticker": "{c["ticker"]}",\n'
        res += f'        "name": "{c["name"]}",\n'
        res += f'        "search_terms": {json.dumps(c["search_terms"])},\n'
        res += f'        "sector": "{c["sector"]}",\n'
        res += f'        "description": "{c.get("description", "")}"\n'
        res += "    },\n"
        return res

    public_comps = [c for c in all_companies if c in companies_config.AI_COMPANIES]
    private_comps = [c for c in all_companies if c in companies_config.PRIVATE_AI_COMPANIES]

    for c in public_comps:
        py_content += format_company(c)
    py_content += "]\n\n"
    
    py_content += "PRIVATE_AI_COMPANIES = [\n"
    for c in private_comps:
        py_content += format_company(c)
    py_content += "]\n"
    
    py_content += """
def get_all_companies():
    \"\"\"Retourne toutes les compagnies (publiques + privees)\"\"\"
    return AI_COMPANIES + PRIVATE_AI_COMPANIES

def get_public_companies():
    \"\"\"Retourne seulement les compagnies cotees en bourse\"\"\"
    return AI_COMPANIES

def get_company_by_ticker(ticker):
    \"\"\"Trouve une compagnie par son ticker\"\"\"
    all_companies = get_all_companies()
    for company in all_companies:
        if company['ticker'] == ticker:
            return company
    return None

def get_search_query(company):
    \"\"\"Genere la requete Google News pour une compagnie\"\"\"
    terms = [company['name']] + company['search_terms']
    return " OR ".join(f'"{term}"' for term in terms)
"""
    
    with open(os.path.join(current_dir, 'companies_config_backup.py'), 'w', encoding='utf-8') as f:
        f.write(py_content)
    print(f"✅ Backup Python généré: {os.path.join(current_dir, 'companies_config_backup.py')}")

if __name__ == "__main__":
    main()
