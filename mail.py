import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(user_email, topic, chat_link, chart_link):
    # Email Configuration
    sender_email = "psypherions@gmail.com"
    sender_password = "secd ddjm mzbn vtuj"  # Use an App Password if using Gmail for enhanced security.
    smtp_server = "smtp.gmail.com"           # Change SMTP server for other providers (e.g., Yahoo, Outlook)
    smtp_port = 587                          # For TLS

    # Email Content
    subject = f"Links for {topic.capitalize()} Discussion"
    body = f"""
    Hi,

    Here are the links you requested for the topic **{topic.capitalize()}**:

    - Chat Link: {chat_link}
    - Chart Link: {chart_link}

    Please click on the links to proceed.

    Best regards,  
    Preptify Team ✨
    """

    # Create MIME email message
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = user_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        # Connect to SMTP server and send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Enable TLS encryption
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, user_email, message.as_string())
        server.quit()
        print(f"Email sent successfully to {user_email}")
    except Exception as e:
        print(f"Error sending email: {e}")

    return True


if __name__ == "__main__":
    user_email = "williamskyle562@gmail.com"
    topic = 'input("Enter the topic: ")'
    chat_link = 'input("Enter the chat link: ")'
    chart_link = 'input("Enter the chart link: ")'
    send_email(user_email, topic, chat_link, chart_link)