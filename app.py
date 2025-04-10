from flask import Flask, render_template, request
import pdfkit
import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import json
from datetime import datetime
from google.auth.transport.requests import Request

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
    # ✅ Load token info directly from the file instead of env variable
    with open("token.json", "r") as f:
        token_info = json.load(f)
    creds = Credentials.from_authorized_user_info(token_info)

    # ✅ Auto-refresh if expired
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open("token.json", "w") as token_file:
            token_file.write(creds.to_json())

    service = build("gmail", "v1", credentials=creds)

    message = MIMEMultipart()
    message["to"] = seller_email
    message["from"] = "ccinvestre@gmail.com"
    message["subject"] = f"Offer for Your Property at {property_address}"

    html_content = f"""
    <html>
    <body>
        <p>We are pleased to present a preliminary offer for your property at <strong>{property_address}</strong> for <strong>${int(offer_amount):,}</strong>.</p>
        <p>Please see the attached offer letter for full details.</p>

        <p>If you'd like to <strong>accept this offer</strong>, simply reply to this email and let us know — we'll get started drafting the formal agreement.</p>
        <p>If you'd like to <strong>counter the offer</strong>, reply with your terms and we’ll review them immediately.</p>

        <p>We look forward to hearing from you!</p>
        <p>Best,<br>CC Invest Team</p>
    </body>
    </html>
    """

    message.attach(MIMEText(html_content, "html"))

    with open(pdf_path, "rb") as pdf:
        attachment = MIMEApplication(pdf.read(), _subtype="pdf")
        attachment.add_header(
            "Content-Disposition", "attachment", filename="Preliminary_Offer.pdf"
        )
        message.attach(attachment)

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    send = service.users().messages().send(userId="me", body={"raw": raw}).execute()
    print(f"✅ Email sent to {seller_email} (Message ID: {send['id']})")


def send_team_notification(subject, body):
    # ✅ Load token directly from file
    with open("token.json", "r") as f:
        token_info = json.load(f)
    creds = Credentials.from_authorized_user_info(token_info)

    # ✅ Auto-refresh if expired
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open("token.json", "w") as token_file:
            token_file.write(creds.to_json())

    service = build("gmail", "v1", credentials=creds)

    message = MIMEText(body)
    message["to"] = "offers@capitalreigroup.com"
    message["from"] = "ccinvestre@gmail.com"
    message["subject"] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": raw}).execute()


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

        send_email(
            seller_email, pdf_path, property_address, offer_amount, offer_sent_timestamp
        )
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
    <br><strong>Your offer has been sent!</strong>
    """


# @app.route("/accept")
# def accept_offer():
#    seller_email = request.args.get("email")
#    property_address = request.args.get("address")
#    offer_sent_timestamp = request.args.get("sent")
#    offer_amount = request.args.get("offer")

# Send notification to team
#    subject = f"🎉 Offer Accepted - {property_address}"
#    body = f"""
#    The seller has accepted the offer!

#    📍 Property: {property_address}
#    📧 Email: {seller_email}
#    💰 Accepted Offer: ${int(offer_amount):,}
#    📅 Offer Originally Sent: {offer_sent_timestamp}

#    Please follow up ASAP.
#    """
#    send_team_notification(subject, body)

#    return f"""
#    <h2>Thank You!</h2>
#    <p>Your offer for {property_address} has been accepted.</p>
#    <p>Our team will reach out to you shortly to finalize the details.</p>
#    """


# @app.route("/counter", methods=["GET", "POST"])
# def counter_offer():
#    if request.method == "POST":
#        seller_email = request.form["email"]
#        property_address = request.form["address"]
#        original_offer = request.form["offer"]
#        counter_amount = request.form["counter_offer"]
#        notes = request.form["notes"]
#        offer_sent_timestamp = request.args.get("sent")

#        subject = f"Counter Offer Received for {property_address}"
#        body = f"""
#        A counteroffer has been submitted for {property_address}.

#        📧 Seller Email: {seller_email}
#        📅 Offer Originally Sent: {offer_sent_timestamp}
#        💰 Original Offer: ${int(original_offer):,}
#        🔁 Counter Offer: ${int(counter_amount):,}
#        📝 Notes: {notes}
#        """

#        send_team_notification(subject, body)

#        return "<h2>Thank you! Your counteroffer has been submitted.</h2>"

#    seller_email = request.args.get("email")
#    property_address = request.args.get("address")
#    original_offer = request.args.get("offer")
#    offer_sent_timestamp = request.args.get("sent")

#    return f"""
#    <h2>Submit a Counter Offer</h2>
#    <form method="post">
#        <input type="hidden" name="email" value="{seller_email}">
#        <input type="hidden" name="address" value="{property_address}">
#        <input type="hidden" name="offer" value="{original_offer}">
#        <input type="hidden" name="sent" value="{offer_sent_timestamp}">


#        <label for="counter_offer">Your Counter Offer:</label>
#        <input type="number" name="counter_offer" required><br><br>

#        <label for="notes">Additional Notes:</label>
#        <textarea name="notes"></textarea><br><br>

#        <button type="submit">Submit Counter Offer</button>
#    </form>
#    """


if __name__ == "__main__":
    app.run(debug=True)
