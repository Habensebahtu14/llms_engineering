import os
import json
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from scraper import fetch_website_links, fetch_website_contents

load_dotenv(override=True)
MODEL = "gpt-4o-mini"

link_system_prompt = """
Je krijgt een lijst van links gevonden op een webpagina.
Jouw taak is te bepalen welke links het meest relevant zijn voor een brochure over het bedrijf,
zoals links naar een 'Over ons'-pagina, bedrijfspagina of vacaturepagina.
Reageer in JSON zoals in dit voorbeeld:

{
    "links": [
        {"type": "over ons pagina", "url": "https://volledig.url/over-ons"},
        {"type": "vacatures pagina", "url": "https://volledig.url/vacatures"}
    ]
}
"""

brochure_system_prompt = """
Je bent een assistent die de inhoud van meerdere relevante pagina's van een bedrijfswebsite analyseert
en een beknopte brochure opstelt over het bedrijf, gericht op potentiële klanten, investeerders en kandidaten.
Reageer in Markdown zonder codeblokken.
Schrijf altijd in professioneel Nederlands.
Neem indien beschikbaar details op over bedrijfscultuur, klanten en vacatures.
"""

def get_links_user_prompt(url):
    links = fetch_website_links(url)
    return f"""
Hier is de lijst van links op de website {url}.
Bepaal welke links relevant zijn voor een bedrijfsbrochure en geef de volledige https-URL terug in JSON-formaat.
Sluit links naar Algemene Voorwaarden, Privacy en e-mailadressen uit.

Links (sommige kunnen relatieve links zijn):

""" + "\n".join(links)

def select_relevant_links(url, client):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": link_system_prompt},
            {"role": "user", "content": get_links_user_prompt(url)}
        ],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

def fetch_page_and_all_relevant_links(url, client):
    contents = fetch_website_contents(url)
    relevant_links = select_relevant_links(url, client)
    result = f"## Landingspagina:\n\n{contents}\n## Relevante Links:\n"
    for link in relevant_links["links"]:
        result += f"\n\n### Link: {link['type']}\n"
        result += fetch_website_contents(link["url"])
    return result

def get_brochure_user_prompt(company_name, url, client):
    user_prompt = f"""
Je analyseert een bedrijf genaamd: {company_name}
Hieronder vind je de inhoud van de landingspagina en andere relevante pagina's.
Gebruik deze informatie om een beknopte brochure te maken in Markdown, zonder codeblokken.\n\n
"""
    user_prompt += fetch_page_and_all_relevant_links(url, client)
    return user_prompt[:5_000]

# --- Streamlit UI ---
st.set_page_config(page_title="Bedrijfsbrochure Generator", page_icon="📄")
st.title("📄 Bedrijfsbrochure Generator")
st.markdown("Voer een bedrijfsnaam en website-URL in om automatisch een professionele brochure te genereren.")

company_name = st.text_input("Bedrijfsnaam", placeholder="bijv. Mijn Portfolio")
url = st.text_input("Website URL", placeholder="bijv. https://habensebhatu.nl")

if st.button("Genereer brochure"):
    if not company_name or not url:
        st.warning("Vul zowel een bedrijfsnaam als een URL in.")
    else:
        api_key = st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            st.error("OPENAI_API_KEY is niet ingesteld. Voeg deze toe via Streamlit secrets.")
            st.stop()
        openai = OpenAI(api_key=api_key)
        with st.spinner("Website wordt geanalyseerd en brochure wordt gegenereerd..."):
            stream = openai.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": brochure_system_prompt},
                    {"role": "user", "content": get_brochure_user_prompt(company_name, url, openai)}
                ],
                stream=True
            )
            result_placeholder = st.empty()
            response = ""
            for chunk in stream:
                response += chunk.choices[0].delta.content or ""
                result_placeholder.markdown(response)
