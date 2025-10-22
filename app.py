from flask import Flask, render_template, request
import pdfkit
import os
import requests
import json
from datetime import datetime

app = Flask(__name__)

# Ensure "offers" folder exists
os.makedirs("offers", exist_ok=True)

# PDFKit Configuration (Ensure correct wkhtmltopdf path)
config = pdfkit.configuration()


def generate_offer_pdf(
    seller_name,
    property_address,
    offer_amount,
    seller_email,
    terms,
    inspection_period,
    financing,
    close_of_escrow,
):
    if not terms.strip():
        terms = "Property to be sold in 'as-is' condition."

    html = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 40px;
                padding: 20px;
                line-height: 1.8;
            }}
            h2 {{
                font-size: 24px;
                font-weight: bold;
            }}
            h3 {{
                font-size: 20px;
                font-weight: bold;
            }}
            p {{
                font-size: 14px;
                line-height: 1.8;
                margin-bottom: 15px;
            }}
            .offer-details {{
                font-size: 16px;
                margin-top: 10px;
            }}
            .highlight {{
                font-weight: bold;
            }}
            .cta {{
                font-style: italic;
                margin-top: 20px;
            }}
            .spacing {{
                margin-top: 20px;
            }}
            .emoji {{
                width: 20px;
                vertical-align: middle;
            }}
        </style>
    </head>
    <body>
        <h2>Preliminary Offer Letter</h2>
        
        <p>Dear {seller_name if seller_name else "Homeowner"},</p>
        <p>We are pleased to present a preliminary offer for your property at:</p>
        <h3><img src="https://abs.twimg.com/emoji/v2/72x72/1f3e0.png" class="emoji"> <span class="highlight">{property_address}</span> <img src="https://abs.twimg.com/emoji/v2/72x72/1f3e0.png" class="emoji"></h3>

        <p class="offer-details"><strong>Offer Amount:</strong> ${int(offer_amount):,}</p>
        <p class="offer-details"><strong>Terms:</strong> {terms}</p>
        <p class="offer-details"><strong>Inspection Period:</strong> {inspection_period} days</p>
        <p class="offer-details"><strong>Financing:</strong> {financing}</p>
        <p class="offer-details"><strong>Close of Escrow:</strong> {close_of_escrow} days</p>

        <p class="cta"><i>If you are interested in this offer, simply reply to the email and let us know. We will then get started preparing the formal agreement.</i></p>
        <p class="cta"><i>If you would like to counter the offer, just reply with your terms and we will review them promptly.</i></p>


        <p class="spacing">For any questions, reply to the email and a team member will follow up shortly. Thank you!</p>
        <p><strong>Best Regards,</strong><br>CC Invest RE Team</p>
    </body>
    </html>
    """

    pdf_path = f"offers/{seller_email}_offer.pdf"
    pdfkit.from_string(html, pdf_path, configuration=config)
    return pdf_path


def send_email(
    seller_email, pdf_path, property_address, offer_amount, offer_sent_timestamp
):
    import resend

    # Set your Resend API key
    resend.api_key = os.environ.get("RESEND_API_KEY")

    # Read the PDF file
    with open(pdf_path, "rb") as pdf:
        pdf_content = pdf.read()

    html_content = f"""
<html>
<body>
    <p>We are pleased to present a preliminary offer for your property at <strong>{property_address}</strong> for <strong>${offer_amount}</strong>.</p>
    <p>Please see the attached offer letter for full details.</p>
    
    <p>If you'd like to <strong>accept this offer</strong>, simply reply to this email and let us know — we'll get started immediately!</p>
    <p>If you'd like to <strong>counter the offer</strong>, reply with your terms and we'll review them immediately.</p>
    
    <p>We look forward to hearing from you!</p>
    <p>Best,<br>CC Invest Team</p>
</body>
</html>
"""

    try:
        params = {
            "from": "CC Invest Team <offers@ccinvestre.com>",
            "to": [seller_email],
            "subject": f"Offer for Your Property at {property_address}",
            "html": html_content,
            "attachments": [
                {"filename": "Preliminary_Offer.pdf", "content": list(pdf_content)}
            ],
        }

        email = resend.Emails.send(params)
        print(f"✅ Email sent to {seller_email} (Message ID: {email['id']})")
        return True
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False


@app.route("/")
def home():
    return render_template("send_offer.html")


@app.route("/send_offer", methods=["POST"])
def send_offer():
    seller_name = request.form.get("seller_name", "").strip() or "Homeowner"
    seller_email = request.form["email"]
    property_address = request.form["address"]
    offer_amount = request.form["offer"]
    inspection_period = request.form.get("inspection_period", "7 days")
    financing = request.form.get("financing", "Cash or Hard Money")
    close_of_escrow = request.form.get("close_of_escrow", "30")
    terms = request.form["terms"]
    lead_id = request.form.get("lead_id", "")
    opportunity_id = request.form.get("opportunity_id", "")
    offer_sent_timestamp = datetime.now().strftime("%Y-%m-%d %I:%M %p")

    print("Generating PDF with the following details:")
    print(f"Seller Name: {seller_name}")
    print(f"Email: {seller_email}")
    print(f"Property: {property_address}")
    print(f"Offer: {offer_amount}")
    print(f"Inspection Period: {inspection_period} days")
    print(f"Financing: {financing}")
    print(f"Close of Escrow: {close_of_escrow} days")
    print(f"Terms: {terms}")

    try:
        pdf_path = generate_offer_pdf(
            seller_name,
            property_address,
            offer_amount,
            seller_email,
            terms,
            inspection_period,
            financing,
            close_of_escrow,
        )
        print(f"✅ PDF generated successfully at: {pdf_path}")

        email_sent = send_email(
            seller_email, pdf_path, property_address, offer_amount, offer_sent_timestamp
        )

        # Send webhook to Zapier to create Offer record in Salesforce
        if email_sent:
            webhook_url = "https://hooks.zapier.com/hooks/catch/6774691/urko8wo/"
            webhook_data = {
                "offer_amount": offer_amount,
                "property_address": property_address,
                "seller_email": seller_email,
                "lead_id": lead_id,
                "opportunity_id": opportunity_id,
            }

            try:
                requests.post(webhook_url, json=webhook_data)
                print("✅ Offer logged in Salesforce")
            except Exception as e:
                print(f"⚠️ Failed to log in Salesforce: {e}")

    except Exception as e:
        print(f"❌ Error: {e}")

    return f"""
    Offer sent to: {seller_email} <br>
    Seller Name: {seller_name} <br>
    Property Address: {property_address} <br>
    Offer Amount: ${offer_amount} <br>
    Inspection Period: {inspection_period} days <br>
    Financing: {financing} <br>
    Close of Escrow: {close_of_escrow} days <br>
    Terms: {terms} <br>
    <br><strong>Your offer has been sent and logged in Salesforce!</strong>
    """


if __name__ == "__main__":
    app.run(debug=True)
