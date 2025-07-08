# ai_utils.py

import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Get the API key from environment
api_key = os.getenv("GEMINI_API_KEY")

# ✅ VERY IMPORTANT: This configures the Gemini SDK to use the key. Can adjust the gemini version according to api being used.
genai.configure(api_key=api_key)

# Now you can create the model
model = genai.GenerativeModel('gemini-2.0-flash')

def generate_summary(company_data):
    prompt = f"""
You are an AI assistant helping with lead generation.

Here is information about a company:
Title: {company_data.get('title')}
Meta Description: {company_data.get('description')}
Revenue: {company_data.get('revenue')}
Founder/CEO: {company_data.get('founders')}
Scraped Website Text: {company_data.get('scraped_text')[:1500]}
There can also be random words scraped in place of name that make no sense. For example "Founder", "ceo", etc. if any fields contains just random info try to answer by yourself.
Based on this, write a concise summary (~5 lines) covering:
- What the company does
- Which domain or sector it's in
- Who its customers likely are
- How big it is (if revenue or other hints present)
- Any unique traits
"""

    response = model.generate_content(prompt)
    return response.text.strip()

def generate_cold_email(summary_text, company_name):
    prompt = f"""
Write a personalized cold outreach email to {company_name}.

Start with a light, respectful tone. Reference their business (based on summary below), and offer an AI-based tool that helps improve operations, save time, or grow leads. End with a CTA to schedule a chat.

Company Summary:
{summary_text}
"""

    response = model.generate_content(prompt)
    return response.text.strip()

def start_company_chat(company_data):
    prompt = f"""
    You are a B2B lead intelligence assistant.

    Your ONLY goal is to answer questions about the following company using ONLY the information provided.

    ---
    Company domain: {company_data.get('domain')}
    Title: {company_data.get('title')}
    Meta Description: {company_data.get('description')}
    Revenue: {company_data.get('revenue')}
    Founder/CEO: {company_data.get('founders')}
    Scraped Website Text: {company_data.get('scraped_text')[:2000]}
    ---

    ⚠️ STRICT RULES:
    1. If the user asks anything not related to this company, politely respond: 
       "I'm here to help you understand this company only. Please ask something related to it."
    2. Do not guess or fabricate details. If unsure, respond with:
       "That information isn’t available from the data I have."
    3. Always keep responses factual and concise, as this is for lead generation purposes.
    4. If information is insufficient or unclear, try to search and find the info by yourself. If not found then say "Some details were unavailable, but here's what I can infer..."

    Respond in a professional tone suitable for B2B sales research.
    """

    chat = model.start_chat(history=[])
    chat.send_message(prompt)
    return chat

def get_company_tags(company):
    """
    Uses an LLM to extract relevant industry/sector tags from the scraped content of a company.
    Args:
        company (dict): Contains scraped fields like title, description, about text, etc.
    Returns:
        list[str]: A list of 2–5 relevant industry tags.
    """

    # Combine textual inputs for context
    context = f"""
Company Title: {company.get('title', '')}
Description: {company.get('description', '')}
About Text: {company.get('about', '')}
"""

    prompt = f"""
Based on the following company information, return a comma-separated list of 2 to 5 industry or sector tags that describe what the company does.
Be specific and avoid generic terms like 'company' or 'business'.

Example tags: SaaS, FinTech, HealthTech, CRM, AI, Cybersecurity, Logistics, HRTech, Ecommerce
⚠️ Note: Some fields may be empty or unclear. In that case, infer based on what is available. Do not output "unknown" or "generic company". Be precise but concise. 
Company Info:
{context}

Tags:
"""

    try:
        response = genai.GenerativeModel("gemini-2.0-flash").generate_content(prompt)
        tags_text = response.text.strip()
        # Clean and return as a list
        return [tag.strip() for tag in tags_text.split(",") if tag.strip()]
    except Exception as e:
        print(f"[ERROR] Tag generation failed: {e}")
        return ["N/A"]
