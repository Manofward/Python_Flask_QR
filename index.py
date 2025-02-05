from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
import qrcode
import qrcode.image.svg
import pyotp
import duckdb

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management

class Connection:
    @staticmethod
    def Open_Connection():
        return duckdb.connect("Accounts.db")

    @staticmethod
    def CreateTable():
        con = Connection.Open_Connection()
        con.sql("CREATE TABLE IF NOT EXISTS user (ID INT , Username VARCHAR, Password VARCHAR, TwoFactor BOOL, Secret VARCHAR);")
        con.sql("INSERT INTO user VALUES (1, 'testuser', 'password123', false, NULL);")
        con.close()

    @staticmethod
    def GetSecret(username):
        con = Connection.Open_Connection()
        result = con.sql(f"SELECT Secret FROM user WHERE Username = '{username}';").fetchall()
        
        if result and result[0][0]:  # Check if a secret exists
            secret = result[0][0]
        else:
            secret = None
        
        con.close()
        return secret

    @staticmethod
    def CreateSecret(username):
        con = Connection.Open_Connection()

        secret = pyotp.random_base32()
        con.sql(f"UPDATE user SET Secret = '{secret}' WHERE Username = '{username}';")
        
        con.close()
        return secret


class Website:
    @staticmethod
    def create_svg_qr_code(data):
        """Generate an SVG QR code from the given data."""
        img = qrcode.make(data, image_factory=qrcode.image.svg.SvgPathImage)
        return img.to_string(encoding='unicode')

    @app.route('/')
    def homepage():
        Connection.CreateTable()
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            
            # Simple authentication check (replace with your own logic)
            if username == 'testuser' and password == 'password123':
                session['username'] = username  # Store username in session

                secret = Connection.GetSecret(username) 
                if secret is None:
                    return redirect(url_for('generate_qr_code'))  # Redirect to check TOTP
                else:
                    return redirect(url_for('check_totp'))
            else:
                flash('Invalid credentials. Please try again.')
        
        return render_template('login.html')  # Render login page

    @app.route('/check_totp')
    def check_totp():
        username = session.get('username')
        if not username:
            return redirect(url_for('login'))  # Redirect to login if not authenticated
        
        secret = Connection.GetSecret(username)  # Get or create the secret
        if secret:
            return redirect(url_for('verify_totp_page'))  # Redirect to TOTP verification page
        else:
            return redirect(url_for('generate_qr_code'))  # Redirect to QR code generation page

    @app.route('/generate_qr_code')
    def generate_qr_code():
        username = session.get('username')
        if not username:
            return redirect(url_for('login'))  # Redirect to login if not authenticated
        
        secret = Connection.CreateSecret(username)  # Get or create the secret
        my_name = "MyApp"  # You can customize this as needed
        otpauth_url = f"otpauth://totp/{my_name}?secret={secret}&issuer={my_name}"
        qr_code_svg = Website.create_svg_qr_code(otpauth_url)  # Generate QR code
        
        return render_template('qr_code.html', qr_code=qr_code_svg)  # Render QR code page

    @app.route('/verify_totp_page', methods=['GET', 'POST'])
    def verify_totp_page():
        if request.method == 'POST':
            username = session.get('username')
            current_totp = request.form.get('current_totp')
            secret = Connection.GetSecret(username)  # Get the secret
            
            totp = pyotp.TOTP(secret)
            is_valid = totp.verify(current_totp)
            if is_valid:
                return "TOTP is valid!", 200
            else:
                return "TOTP is invalid!", 401
        
        return render_template('verify_totp.html')  # Render TOTP verification page

    @app.route('/logout')
    def logout():
        session.pop('username', None)  # Clear the session
        return redirect(url_for('login'))  # Redirect to login page

if __name__ == "__main__":
    Connection.CreateTable()  # Ensure the table is created on startup
    app.run(debug=True)