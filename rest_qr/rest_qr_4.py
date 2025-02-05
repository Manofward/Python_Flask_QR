from flask import Flask, request, render_template_string
from markupsafe import escape
import qrcode
import qrcode.image.svg

app = Flask(__name__)

class QrCode:
    @app.route("/api/v1/qr/generate/<string:text>")
    def generate(text):
        img = qrcode.make(text, image_factory=qrcode.image.svg.SvgPathImage)
        return img.to_string(encoding='unicode')
 