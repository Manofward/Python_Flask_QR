from flask import Flask, request, jsonify
import qrcode
import qrcode.image.svg
import pyotp

app = Flask(__name__)

def create_svg_qr_code(data):
    """Generate an SVG QR code from the given data."""
    img = qrcode.make(data, image_factory=qrcode.image.svg.SvgPathImage)
    return img.to_string(encoding='unicode')

@app.route("/api/v1/totp/generate", methods=['POST'])
def generate_totp():
    """Generate a TOTP based on the provided secret."""
    secret = request.form.get('secret')
    if not secret:
        return jsonify({"error": "Secret is required"}), 400
    
    totp = pyotp.TOTP(secret)
    return jsonify({"totp": totp.now()})

@app.route("/api/v1/totp/verify", methods=['POST'])
def verify_totp():
    """Verify the provided TOTP against the secret."""
    secret = request.form.get('secret')
    current_totp = request.form.get('current_totp')
    
    if not secret or not current_totp:
        return jsonify({"error": "Secret and current_totp are required"}), 400
    
    totp = pyotp.TOTP(secret)
    is_valid = totp.verify(current_totp)
    return jsonify({"success": is_valid}), 200 if is_valid else 401

@app.route("/api/v1/totp/generateQrCode", methods=['POST'])
def generate_totp_qr_code():
    """Generate a QR code for TOTP using the provided secret and application name."""
    my_secret = request.form.get('my_secret')
    my_name = request.form.get('my_name')
    
    if not my_secret or not my_name:
        return jsonify({"error": "my_secret and my_name are required"}), 400
    
    otpauth_url = f"otpauth://totp/{my_name}?secret={my_secret}&issuer={my_name}"
    return create_svg_qr_code(otpauth_url)

@app.route("/generate_qr_page/<string:text>")
def generate_qr_page(text):
    """Generate a TOTP and display the QR code on a webpage."""
    my_secret = text
    my_name = "MyApp"  # You can customize this as needed

    # Generate the otpauth URL for the QR code
    otpauth_url = f"otpauth://totp/{my_name}?secret={my_secret}&issuer={my_name}"
    
    # Generate the QR code
    qr_code_svg = create_svg_qr_code(otpauth_url)

    # Create a simple HTML page to display the QR code
    html = f"""
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
        <title>QR Code</title>
      </head>
      <body>
        <h1>Your QR Code</h1>
        <div>{qr_code_svg}</div>  <!-- Display the QR code -->
      </body>
    </html>
    """
    return html  # Return the HTML page directly

if __name__ == "__main__":
    app.run(debug=True)