from flask import Flask, request, jsonify, render_template
from flask_mail import Mail, Message
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from dotenv import load_dotenv
import os
import logging

load_dotenv()  # Load environment variables from a .env file

app = Flask(__name__)
CORS(app)  # Enable CORS

app.secret_key = os.getenv('SECRET_KEY')  # Needed for flash messages

# Configure Flask-Mail
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = (
    os.getenv('MAIL_DEFAULT_SENDER_NAME'), os.getenv('MAIL_DEFAULT_SENDER_EMAIL'))

mail = Mail(app)

# Configure Flask-Limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["5 per hour"]
)
limiter.init_app(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route('/api/contact', methods=['POST'])
@limiter.limit("2 per minute")  # Limit to 2 requests per minute per IP
def send_email():
    try:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        subject = data.get('subject')
        message = data.get('message')

        if not name or not email or not subject or not message:
            return jsonify({"error": "All fields are required!"}), 400

        email_body = render_template(
            'email_template.html', name=name, email=email, subject=subject, message=message)
        recipient = os.getenv('MAIL_RECIPIENT')
        msg = Message(subject, recipients=[recipient], html=email_body)
        mail.send(msg)

        return jsonify({"message": "Message sent successfully!"}), 200
    except Exception as e:
        logger.error('Failed to send email: %s', e)
        return jsonify({"error": "Failed to send message. Please try again later."}), 500


if __name__ == '__main__':
    app.run(debug=True)
