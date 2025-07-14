import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timezone
from fpdf import FPDF
import tempfile
import os

st.set_page_config(page_title="GitHub Portfolio Analyzer", layout="wide")

def fetch_github_data(username):
    url = f"https://api.github.com/users/{username}/repos"
    response = requests.get(url)
    if response.status_code != 200:
        st.error("Error fetching data. Check the username or API rate limit.")
        return []
    return response.json()

def extract_repo_data(repos):
    data = []
    for repo in repos:
        last_updated = pd.to_datetime(repo["updated_at"])
        is_stale = (datetime.now(timezone.utc) - last_updated).days > 365
        data.append({
            "Name": repo["name"],
            "Stars": repo["stargazers_count"],
            "Forks": repo["forks_count"],
            "Language": repo["language"],
            "Created At": repo["created_at"],
            "Last Updated": repo["updated_at"],
            "Has License": bool(repo["license"]),
            "Is Archived": repo["archived"],
            "Is Stale": is_stale
        })
    return pd.DataFrame(data)

def plot_growth_timeline(df):
    df["Created At"] = pd.to_datetime(df["Created At"])
    yearly = df["Created At"].dt.year.value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(yearly.index.astype(str), yearly.values, color='mediumseagreen')
    ax.set_title("Repository Growth Timeline")
    ax.set_xlabel("Year")
    ax.set_ylabel("Repositories Created")
    return fig

def create_pdf_summary(username, df, total_stars, top_lang):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"GitHub Summary Report for {username}", ln=True, align='C')

    pdf.ln(10)
    pdf.set_font("Arial", size=11)
    pdf.cell(200, 10, txt=f"Total Repositories: {len(df)}", ln=True)
    pdf.cell(200, 10, txt=f"Total Stars: {total_stars}", ln=True)
    pdf.cell(200, 10, txt=f"Top Language: {top_lang}", ln=True)

    pdf.ln(10)
    pdf.cell(200, 10, txt="Top Repositories:", ln=True)
    for i, row in df.sort_values(by="Stars", ascending=False).head(5).iterrows():
        # Replace the emoji with plain text
        pdf.cell(200, 10, txt=f"- {row['Name']} | Stars: {row['Stars']} | {row['Language']}", ln=True)

    tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp_pdf.name)
    return tmp_pdf.name

def main():
    st.title("🧠 GitHub Portfolio Analyzer")
    username = st.text_input("Enter your GitHub username:")

    if username:
        repos = fetch_github_data(username)
        if repos:
            df = extract_repo_data(repos)

            total_stars = df["Stars"].sum()
            top_lang = df["Language"].mode()[0] if not df["Language"].isnull().all() else "N/A"

            col1, col2, col3 = st.columns(3)
            col1.metric("Total Repositories", len(df))
            col2.metric("Total Stars ⭐", total_stars)
            col3.metric("Top Language", top_lang)

            st.subheader("📈 Repository Growth Over Time")
            st.pyplot(plot_growth_timeline(df))

            st.subheader("🩺 Project Health Check")
            health_cols = ["Name", "Stars", "Forks", "Language", "Has License", "Is Archived", "Is Stale"]
            st.dataframe(df[health_cols].sort_values(by="Stars", ascending=False), use_container_width=True)

            st.subheader("📥 Download Your Analysis")
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv, "github_repo_data.csv", "text/csv")

            pdf_path = create_pdf_summary(username, df, total_stars, top_lang)
            with open(pdf_path, "rb") as f:
                st.download_button("Download PDF Summary", f, file_name="github_summary.pdf", mime="application/pdf")

            st.subheader("💡 Summary Insight")
            if total_stars > 50 and not df["Is Stale"].all():
                st.success("Your GitHub is active and star-worthy! Great job maintaining your repositories.")
            else:
                st.info("Consider refreshing older projects and adding good READMEs or licenses to enhance your profile.")

if __name__ == "__main__":
    main()
