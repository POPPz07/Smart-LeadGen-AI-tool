import streamlit as st
import pandas as pd
from googlesearch import search
from concurrent.futures import ThreadPoolExecutor, as_completed
from scraper import scrape_domain
from ai_utils import generate_summary, generate_cold_email, start_company_chat, get_company_tags

st.set_page_config(page_title="Smart LeadGen AI", layout="centered")

# -------------------------------
# 🌍 Introduction Section
# -------------------------------
st.title("🚀 Smart LeadGen AI Tool")
st.markdown("""
Welcome to the **AI-Powered Lead Generation Assistant**.

This tool helps you:
- 🕵️ Scrape company websites to extract leads (emails, phones, LinkedIn)
- 🧠 Summarize company background using AI
- ✉️ Generate outreach emails for cold contacts
- 📤 Export leads as CSV for sales workflows

### 📌 Steps to Use:
1. Provide company input using **one of the 3 options** below.
2. Let the app **scrape** homepage, about, and contact pages.
3. Review and export the structured leads.
4. Optionally generate **AI summary and email message**.

---
""")

# -------------------------------
# 🔍 Input Mode Selection
# -------------------------------
st.subheader("🔽 Choose Input Method")

input_mode = st.radio("Select how you want to provide company input:", ["Enter a domain", "Upload CSV", "Search by company name"])

domains = st.session_state.get("domains_to_scrape", [])

# -------------------------------
# 🧾 Mode 1: Manual Domain
# -------------------------------
if input_mode == "Enter a domain":
    domain_input = st.text_input("Enter one or more domains (comma-separated)")
    if domain_input:
        domains = [d.strip() for d in domain_input.split(",") if d.strip()]
        st.session_state["domains_to_scrape"] = domains

# -------------------------------
# 📤 Mode 2: CSV Upload
# -------------------------------

elif input_mode == "Upload CSV":
    uploaded_file = st.file_uploader("Upload CSV or XLSX with column 'domain'", type=["csv", "xlsx"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        if "domain" in df.columns:
            domains = df["domain"].dropna().tolist()
            st.success(f"✅ {len(domains)} domains loaded.")
            st.session_state["domains_to_scrape"] = domains
        else:
            st.warning("⚠️ File must contain a column named 'domain'.")



# -------------------------------
# 🌐 Mode 3: Search by Company Name
# -------------------------------
elif input_mode == "Search by company name":
    company_input = st.text_input("Enter one or more company names (comma-separated)")
    if company_input:
        company_names = [c.strip() for c in company_input.split(",") if c.strip()]
        found = []
        with st.spinner("🔍 Searching websites..."):
            for name in company_names:
                try:
                    result = next(search(name + " official site", num_results=1))
                    st.success(f"✅ {name}: {result}")
                    found.append(result)
                except Exception as e:
                    st.warning(f"❌ {name}: {e}")
        if found:
            domains = found
            st.session_state["domains_to_scrape"] = domains

# -----------------------------------------
# 🔁 Step 2: Scrape Data and Show Results
# -----------------------------------------
def safe_scrape(domain):
    try:
        result = scrape_domain(domain)
        score = 0
        if result['emails']: score += 40
        if result['phones']: score += 20
        if result['social_links']: score += 20
        if result.get('revenue'): score += 10
        if result.get('founders'): score += 10
        result['lead_score'] = score
        result['tags'] = get_company_tags(result)
        return result
    except Exception as e:
        return {"domain": domain, "error": str(e)}

if domains and "scraped_results" not in st.session_state:
    st.markdown("---")
    st.write("✅ Domains ready for scraping:")
    st.write(domains)

    if st.button("🚀 Start Scraping"):
        with st.spinner("Scraping in parallel..."):
            results = []
            with ThreadPoolExecutor(max_workers=10) as executor:
                future_to_domain = {executor.submit(safe_scrape, d): d for d in domains}
                for future in as_completed(future_to_domain):
                    results.append(future.result())

        st.success("✅ Scraping complete!")
        flat_data = []
        for item in results:
            flat_data.append({
                "Domain": item.get('domain', ''),
                "Emails": ", ".join(item.get('emails', [])),
                "Phones": ", ".join(item.get('phones', [])),
                "Social": ", ".join(item.get('social_links', [])),
                "Title": item.get('title', ''),
                "Meta Description": item.get('description', ''),
                "Revenue": item.get('revenue', 'N/A'),
                "Founder/CEO": item.get('founders', 'N/A'),
                "Tags": ", ".join(item.get('tags', [])),
                "Lead Score": item.get('lead_score', 0)
            })

        df = pd.DataFrame(flat_data)
        st.subheader("📊 Scraped Lead Data")
        st.dataframe(df)
        st.download_button("📥 Download CSV", data=df.to_csv(index=False).encode("utf-8"), file_name="scraped_leads.csv")

        st.session_state["scraped_results"] = results

# -----------------------------------------
# 🤖 AI Summary & Outreach Generator
# -----------------------------------------
if "scraped_results" in st.session_state:
    st.markdown("---")
    st.subheader("🤖 AI Summary & Outreach Generator")

    for idx, company in enumerate(st.session_state["scraped_results"]):
        with st.expander(f"📦 {company['domain']}"):
            if st.button(f"🧠 Generate AI Summary", key=f"summary_btn_{idx}"):
                summary = generate_summary(company)
                st.session_state[f"summary_{idx}"] = summary
                st.success("✅ Summary generated!")

            if f"summary_{idx}" in st.session_state:
                st.markdown("**🔍 Company Summary:**")
                st.info(st.session_state[f"summary_{idx}"])

                if st.button(f"✉️ Generate Cold Outreach Email", key=f"email_btn_{idx}"):
                    email = generate_cold_email(st.session_state[f"summary_{idx}"], company['domain'])
                    st.session_state[f"email_{idx}"] = email
                    st.success("✅ Cold email generated!")

            if f"email_{idx}" in st.session_state:
                st.markdown("**✉️ Cold Outreach Email:**")
                st.code(st.session_state[f"email_{idx}"], language="markdown")

            with st.expander("💬 Ask More About This Company"):
                if f"chat_{idx}" not in st.session_state:
                    st.session_state[f"chat_{idx}"] = start_company_chat(company)

                user_question = st.text_input("Ask a follow-up question:", key=f"q_{idx}")
                if st.button("🔎 Get Answer", key=f"get_answer_{idx}"):
                    chat = st.session_state[f"chat_{idx}"]
                    response = chat.send_message(user_question)
                    st.session_state[f"chat_response_{idx}"] = response.text.strip()

                if f"chat_response_{idx}" in st.session_state:
                    st.markdown("**🤖 Response:**")
                    st.info(st.session_state[f"chat_response_{idx}"])
