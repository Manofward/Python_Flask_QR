from flask import Flask, request, render_template_string
from markupsafe import escape
import qrcode
import qrcode.image.svg

class QrCode:
    def generate(text):
        img = qrcode.make(text, image_factory=qrcode.image.svg.SvgPathImage)
        return img.to_string(encoding='unicode')

app = Flask(__name__)

# Index
@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

# aufgabe 1
@app.route("/sum/<int:num1>/<int:num2>")
def sum(num1, num2):
    total = num1 + num2
    return f"The sum of {escape(num1)} and {escape(num2)} is {escape(total)}!"
# Aufgabe 2
@app.route("/api/v1/qr/generate/<string:text>")
def generateQrCode(text):
    img = QrCode.generate(text)
    return f"{img}"

# Aufgabe 3
@app.route("/generated")
def qrInput():
    return render_template_string('''
        <form action="/generated/qr" method="post">
            <input type="text" name="text" placeholder="Geben Sie Ihren Text ein" required>
            <input type="submit" value="QR-Code generieren">
        </form>
        {% if qr_code %}
            <h2>Ihr QR-Code:</h2>
            <div>{{ qr_code | safe }}</div>
        {% endif %}
    ''')

@app.route("/generated/qr", methods=["POST"])
def generated():
    text = request.form['text']
    qr_code = QrCode.generate(text)
    return render_template_string('''
        <form action="/generated/qr" method="post">
            <input type="text" name="text" placeholder="Geben Sie Ihren Text ein" required>
            <input type="submit" value="QR-Code generieren">
        </form>
        <h2>Ihr QR-Code:</h2>
        <div>{{ qr_code | safe }}</div>
    ''', qr_code=qr_code)