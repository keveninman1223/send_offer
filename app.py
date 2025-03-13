from flask import Flask, render_template, request
import pdfkit
import smtplib
from email.message import EmailMessage
import os

app = Flask(__name__)

# Ensure "offers" folder exists
os.makedirs("offers", exist_ok=True)

# Email Configuration (Use your credentials)
EMAIL_SENDER = "keven@capitalreigroup.com"
EMAIL_PASSWORD = "dafu xfrq stlv lnab"  # Paste your generated App Password here
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# PDFKit Configuration (Ensure correct wkhtmltopdf path)
config = pdfkit.configuration(wkhtmltopdf="/usr/local/bin/wkhtmltopdf")


def generate_offer_pdf(
    seller_name, property_address, offer_amount, seller_email, terms
):
    """Generate a well-formatted PDF with proper spacing and emoji fixes."""

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
        <p class="offer-details"><strong>Inspection Period:</strong> 7 days</p>
        <p class="offer-details"><strong>Financing:</strong> Cash or Hard Money</p>
        <p class="offer-details"><strong>Close of Escrow:</strong> 30 days</p>

        <p class="cta"><i>If you are interested, please let us know by clicking the <strong>"Accept Offer"</strong> button in the email. Please note that clicking this button does not obligate you in any way, it simply lets our team know you are interested in proceeding with a formal offer letter.</i></p>
        
        <p class="cta"><i>Please also click the <strong>"Counter This Offer"</strong> button if you have different terms that you would accept! Our team will review and respond in a timely manner.</i></p>

        <p class="spacing">For any further questions, please feel free to reply to the email, and a member of our team will reach out to you shortly. Thank you!</p>

        <p><strong>Best Regards,</strong><br>
        Capital House Buyers</p>

        <p class="spacing">Find out what others have to say about us!<br>
        <a href="https://www.cashforhousesca.com/reviews/" style="font-weight: bold;">Check our reviews here</a></p>
    </body>
    </html>
    """

    pdf_path = f"offers/{seller_email}_offer.pdf"
    pdfkit.from_string(html, pdf_path, configuration=config)
    return pdf_path


def send_email(seller_email, pdf_path, property_address, offer_amount):
    """Send an email with the offer PDF attached."""
    subject = f"Offer for Your Property at {property_address}"
    body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ddd; }}
            h2 {{ color: #000; }}
            .offer-details {{ font-size: 16px; }}
            .action-links {{ margin-top: 20px; }}
            .button {{ display: inline-block; padding: 10px 15px; margin: 5px 0; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; }}
            .accept {{ background-color: #28a745; }}
            .counter {{ background-color: #007bff; }}
            .disclaimer {{ font-size: 14px; color: #555; margin-top: 5px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Offer for Your Property at {property_address}</h2>
            <p>Hello,</p>
            <p>Congratulations! You have received a preliminary offer for your property at <strong>{property_address}</strong>.</p>

            <p class="offer-details">💰 <strong>Offer Amount:</strong> ${int(offer_amount):,}</p>
            <p>Please review the attached offer letter for details.</p>

            <div class="action-links">
                <p>👉 <a href="http://127.0.0.1:5000/accept?email={seller_email}&address={property_address}" class="button accept">Accept Offer</a></p>
                <p class="disclaimer">📄 Clicking "Accept" does not obligate the owner to anything. It simply informs our team that you would like to move forward with a formal offer. Someone from our team will follow up with the next steps.</p>

                <p>👉 <a href="http://127.0.0.1:5000/counter?email={seller_email}&address={property_address}" class="button counter">Counter This Offer</a></p>
                <p class="disclaimer">💬 Have different terms in mind? Let us know by submitting a counteroffer!</p>
            </div>

            <p>Best,<br>Your Home Buying Team</p>
        </div>
    </body>
    </html>
    """

    msg = EmailMessage()
    msg.set_content(body, subtype="html")
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = seller_email

    # Attach the PDF
    with open(pdf_path, "rb") as pdf_file:
        msg.add_attachment(
            pdf_file.read(),
            maintype="application",
            subtype="pdf",
            filename="Preliminary_Offer.pdf",
        )

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"✅ Email sent successfully to {seller_email}")
    except Exception as e:
        print(f"❌ Email sending failed: {e}")


@app.route("/")
def home():
    return render_template("send_offer.html")


@app.route("/send_offer", methods=["POST"])
def send_offer():
    seller_name = request.form.get("seller_name", "").strip()
    seller_email = request.form["email"]
    property_address = request.form["address"]
    offer_amount = request.form["offer"]
    terms = request.form["terms"]

    # If seller_name is empty, default to "Homeowner"
    if not seller_name:
        seller_name = "Homeowner"

    print("Generating PDF with the following details:")
    print(f"Seller Name: {seller_name}")
    print(f"Email: {seller_email}")
    print(f"Property: {property_address}")
    print(f"Offer: {offer_amount}")
    print(f"Terms: {terms}")

    try:
        pdf_path = generate_offer_pdf(
            seller_name, property_address, offer_amount, seller_email, terms
        )
        print(f"✅ PDF generated successfully at: {pdf_path}")

        # Send the email with the PDF attached
        send_email(seller_email, pdf_path, property_address, offer_amount)
    except Exception as e:
        print(f"❌ Error: {e}")

    return f"""
    Offer sent to: {seller_email} <br>
    Seller Name: {seller_name} <br>
    Property Address: {property_address} <br>
    Offer Amount: ${offer_amount} <br>
    Terms: {terms} <br>
    <br><strong>Check your email for the offer!</strong>
    """


@app.route("/accept")
def accept_offer():
    seller_email = request.args.get("email")
    property_address = request.args.get("address")

    return f"""
    <h2>Thank You!</h2>
    <p>Your offer for {property_address} has been accepted.</p>
    <p>Our team will reach out to you shortly to finalize the details.</p>
    """


@app.route("/counter", methods=["GET", "POST"])
def counter_offer():
    if request.method == "POST":
        seller_email = request.form["email"]
        property_address = request.form["address"]
        counter_amount = request.form["counter_offer"]
        notes = request.form["notes"]

        # Send counteroffer email
        subject = f"Counter Offer Received for {property_address}"
        body = f"""
        A counteroffer has been submitted for {property_address}.
        
        Seller Email: {seller_email}
        Counter Offer Amount: ${counter_amount}
        Additional Notes: {notes}
        """

        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_SENDER  # Send to your email

        try:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
            return "<h2>Thank you! Your counteroffer has been submitted.</h2>"
        except Exception as e:
            return f"<h2>Error sending counteroffer: {e}</h2>"

    # If it's a GET request, show the form
    seller_email = request.args.get("email")
    property_address = request.args.get("address")

    return f"""
    <h2>Submit a Counter Offer</h2>
    <form method="post">
        <input type="hidden" name="email" value="{seller_email}">
        <input type="hidden" name="address" value="{property_address}">
        
        <label for="counter_offer">Your Counter Offer:</label>
        <input type="number" name="counter_offer" required><br><br>

        <label for="notes">Additional Notes:</label>
        <textarea name="notes"></textarea><br><br>

        <button type="submit">Submit Counter Offer</button>
    </form>
    """


if __name__ == "__main__":
    app.run(debug=True)
