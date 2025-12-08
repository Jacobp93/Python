import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import streamlit.components.v1 as components

# ---------------------------------------------------
# STREAMLIT PAGE SETUP
# ---------------------------------------------------

st.set_page_config(page_title="Red Flag Email Generator", layout="wide")

st.markdown("<h1 style='color:#052839;'>📧 Red Flag Email Generator (.eml)</h1>", unsafe_allow_html=True)
st.write("Upload the spreadsheet → preview the formatted email → download as a .eml file ready for Outlook.")

uploaded_file = st.file_uploader("Upload Red Flag Spreadsheet", type=["xlsx", "xls", "csv"])

html_email = None  # will populate

# ---------------------------------------------------
# PROCESS FILE
# ---------------------------------------------------

if uploaded_file:

    # Load file
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    df = df.replace("(No value)", None)

    # Parse dates
    date_cols = ["Date Created - Daily", "Date Closed - Daily", "Last Update Date - Daily"]
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)

    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    # Days Open
    df["Days Open"] = df["Date Created - Daily"].apply(
        lambda d: (today - d.date()).days if pd.notnull(d) else 0
    )

    # ---------------------------------------------------
    # SUMMARY NUMBERS
    # ---------------------------------------------------

    total_open = df[df["Status"].str.contains("New", na=False)].shape[0]
    new_since_yesterday = df[
        (df["Status"].str.contains("New", na=False)) &
        (df["Date Created - Daily"].dt.date == yesterday)
    ].shape[0]
    closed_since_yesterday = df[df["Date Closed - Daily"].dt.date == yesterday].shape[0]
    critical_items = df[df["Status"].str.contains("Red Flag", na=False)].shape[0]

    # ---------------------------------------------------
    # BUILD HTML EMAIL
    # ---------------------------------------------------

    html_email = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8" />
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap" rel="stylesheet" />

    <style>
    body {{
      margin:0; padding:0;
      background:#f4f4f4;
      font-family:'DM Sans',Arial,sans-serif;
      color:#052839;
    }}
    table {{ border-collapse:collapse; }}
    .container {{ max-width:600px; margin:0 auto; background:#fff; }}
    .primary-bg {{ background:#2E52FE; }}
    .metric-card {{ background:#fff; border:1px solid #e0e0e0; border-radius:6px; }}
    </style>

    </head>

    <body>
    <table width="100%">
      <tr><td align="center">
      <table class="container">

        <!-- Header -->
        <tr>
          <td class="primary-bg" align="center" style="padding:20px;">
            <img src="https://www.buildconcierge.com/api/media/file/build-concierge-white.svg" width="200" />
          </td>
        </tr>

        <!-- Title -->
        <tr>
          <td align="center" style="padding:20px;">
            <h1>Today's Red Flag Report</h1>
            <p style="color:#6D6D6D;">{today.strftime('%d %b %Y')}</p>
          </td>
        </tr>

        <!-- Summary Metrics -->
        <tr>
          <td style="padding:20px;">
            <h2>Summary Metrics</h2>

            <table width="100%" class="metric-card" cellpadding="10">
              <tr>
                <td align="center"><span style="font-size:28px;color:#d9534f;">{total_open}</span><br><small>Total Open</small></td>
                <td align="center"><span style="font-size:28px;color:#2E52FE;">{new_since_yesterday}</span><br><small>New Since Yesterday</small></td>
                <td align="center"><span style="font-size:28px;color:#5cb85c;">{closed_since_yesterday}</span><br><small>Closed Yesterday</small></td>
                <td align="center"><span style="font-size:28px;color:#d9534f;">{critical_items}</span><br><small>Critical</small></td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Open Red Flags -->
        <tr>
          <td style="padding:0 20px;">
            <h2>Open Red Flags – {total_open}</h2>
    """

    # ---------------------------------------------------
    # ATTACH INDIVIDUAL RED FLAG CARDS
    # ---------------------------------------------------

    open_items = df[df["Status"].str.contains("New", na=False)]

    for _, row in open_items.iterrows():

        summary = row["Issue description"] or "No summary provided."
        last_update = row["Last Update"] or "No recent update."
        last_update_date = (
            row["Last Update Date - Daily"].date().strftime("%d %b %Y")
            if pd.notnull(row["Last Update Date - Daily"])
            else "—"
        )
        date_logged = (
            row["Date Created - Daily"].date().strftime("%d %b %Y")
            if pd.notnull(row["Date Created - Daily"])
            else "—"
        )

        html_email += f"""
            <table width="100%" style="border:1px solid #d9534f;border-radius:6px;margin-bottom:20px;">
              <tr>
                <td style="background:#d9534f;color:#fff;padding:10px;">
                  <strong>{row["Ticket name"]}</strong>
                </td>
              </tr>

              <tr>
                <td style="padding:15px;background:#ffffff;">

                  <p><strong>Status:</strong> {row["Status"]}</p>
                  <p><strong>Date Logged:</strong> {date_logged}</p>
                  <p><strong>Days Open:</strong> {row["Days Open"]}</p>

                  <p><strong>Summary:</strong><br>{summary}</p>

                  <p><strong>Last Update:</strong><br>{last_update}</p>
                  <p style="font-size:12px;color:#6D6D6D;">Last updated on: {last_update_date}</p>

                </td>
              </tr>
            </table>
        """

    # ---------------------------------------------------
    # CLOSED ITEMS
    # ---------------------------------------------------

    closed_items = df[df["Date Closed - Daily"].notnull()]

    html_email += """
          </td>
        </tr>

        <tr>
          <td style="padding:20px;">
            <h3>Excluded Items</h3>
    """

    if closed_items.empty:
        html_email += "<p>No recently closed items.</p>"
    else:
        for _, row in closed_items.iterrows():
            closed_date = row["Date Closed - Daily"].date().strftime("%d %b %Y")
            html_email += f"<p>• {row['Ticket name']} (Closed {closed_date})</p>"

    html_email += """
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td class="primary-bg" align="center" style="padding:15px;">
            <p style="color:#fff;font-size:12px;">Internal daily report</p>
          </td>
        </tr>

      </table>
      </td></tr>
    </table>
    </body>
    </html>
    """

    # ---------------------------------------------------
    # PREVIEW THE EMAIL
    # ---------------------------------------------------

    st.markdown("### 📧 Preview Email")
    components.html(html_email, height=1500, scrolling=True)

    # ---------------------------------------------------
    # DOWNLOAD HTML
    # ---------------------------------------------------

    st.download_button(
        label="📥 Download HTML Email",
        data=html_email,
        file_name="red_flag_report.html",
        mime="text/html"
    )

    # ---------------------------------------------------
    # DOWNLOAD .EML (SAFE FOR OUTLOOK)
    # ---------------------------------------------------

    # EML FORMAT: requires headers + HTML body
    eml_content = f"""Subject: Today's Red Flag Report
MIME-Version: 1.0
Content-Type: text/html; charset=UTF-8

{html_email}
"""

    st.download_button(
        label="📥 Download Outlook Email (.eml)",
        data=eml_content.encode("utf-8"),
        file_name="red_flag_report.eml",
        mime="message/rfc822"
    )
