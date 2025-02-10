from flask import Flask, request, jsonify, session, render_template
import qrcode
import qrcode.image.svg
import pyotp
import duckdb
import bcrypt
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Erforderlich für die Sitzungsverwaltung

class Database:
    @staticmethod
    def open_connection():
        return duckdb.connect("Accounts.db")

    @staticmethod
    def create_table():
        con = Database.open_connection()
        con.sql("""
            CREATE TABLE IF NOT EXISTS user (
                Username VARCHAR UNIQUE NOT NULL,
                Password VARCHAR NOT NULL,
                TwoFactor BOOL NOT NULL DEFAULT false,
                Secret VARCHAR
            );
        """)
        con.close()

    @staticmethod
    def add_user(username, password):
        con = Database.open_connection()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        print(f"{hashed_password}")
        try:
            con.execute(f"INSERT INTO user (Username, Password) VALUES ('{username}', '{hashed_password}');")
        except Exception as e:
            print(f"Fehler Nutzer erstekkung {e}")
            raise Exception("Fehler beim Hinzufügen des Benutzers.") from e
        finally:
            con.close()

    @staticmethod
    def get_user(username):
        con = Database.open_connection()
        result = con.sql(f"SELECT * FROM user WHERE Username = '{username}';").fetchone()
        con.close()
        return result

    @staticmethod
    def update_two_factor(username, enabled):
        con = Database.open_connection()
        con.sql(f"UPDATE user SET TwoFactor = '{enabled}' WHERE Username = '{username}';")
        con.close()

    @staticmethod
    def set_secret(username, secret):
        con = Database.open_connection()
        con.sql(f"UPDATE user SET Secret = '{secret}' WHERE Username = '{username}';")
        con.close()

@app.before_request
def initialize():
    Database.create_table()

class User:
    @staticmethod
    def register():
        data = request.json
        username = data.get('username')
        password = data.get('password')

        # Validation
        if not username or not password:
            return jsonify({"error": "Benutzername und Passwort erforderlich."}), 400

        if len(password) < 10 or not re.search(r"[A-Z]", password) or not re.search(r"[a-z]", password) or not re.search(r"\d", password):
            return jsonify({"error": "Passwort muss mindestens 10 Zeichen lang sein und kleine und große Buchstaben sowie mindestens eine Zahl enthalten."}), 400

        try:
            Database.add_user(username, password)
        except Exception as e:
            return jsonify({"error": str(e)}), 400
        
        return jsonify({"message": "Benutzer erfolgreich registriert."}), 201

    @staticmethod
    def login():
        data = request.json
        username = data.get('username')
        password = data.get('password')

        user = Database.get_user(username)
        if user and bcrypt.checkpw(password.encode('utf-8'), user[1].encode('utf-8')):  # Passwort überprüfen
            session['username'] = username
            if user[2]:
                return jsonify({"message": "Erfolgreich eingeloggt, bitte gebe deinen TOTP code.", "requires_2FA": True}), 200

            return jsonify({"message": "Erfolgreich eingeloggt.", "requires_2FA": user[2]}), 200
        
        return jsonify({"error": "Ungültige Anmeldeinformationen."}), 401

    @staticmethod
    def enable_2FA():
        username = session.get('username')
        if not username:
            return jsonify({"error": "Benutzer nicht angemeldet."}), 401
        
        secret = pyotp.random_base32()
        Database.set_secret(username, secret)
        Database.update_two_factor(username, True)

        my_name = "MyApp"  # You can customize this as needed
        otpauth_url = f"otpauth://totp/{my_name}?secret={secret}&issuer={my_name}"
        img = qrcode.make(otpauth_url, image_factory=qrcode.image.svg.SvgPathImage)
        gen_qr_code = img.to_string(encoding='unicode')

        return jsonify({"message": "2FA erfolgreich aktiviert.", "qr_code": gen_qr_code}), 200

    @staticmethod
    def disable_2FA():
        username = session.get('username')
        if not username:
            return jsonify({"error": "Benutzer nicht angemeldet."}), 401

        Database.update_two_factor(username, False)
        Database.set_secret(username, None)
        
        return jsonify({"message": "2FA erfolgreich deaktiviert."}), 200

    @staticmethod
    def logout():
        session.pop('username', None)
        return jsonify({"message": "Erfolgreich ausgeloggt."}), 200

    @staticmethod
    def verify_totp():
        data = request.json
        username = session.get('username')
        if not username:
            return jsonify({"error": "Benutzer nicht angemeldet."}), 401

        user = Database.get_user(username)
        if user is None or user[3] is None:
            return jsonify({"error": "Keine 2FA-Informationen gefunden."}), 400
        totp = pyotp.TOTP(user[3])  # Geheimen aus der DB holen
        is_valid = totp.verify(data.get('totp'))

        if is_valid:
            return jsonify({"message": "TOTP ist gültig!"}), 200
        else:
            return jsonify({"error": "TOTP ist ungültig."}), 401

# API-Routen
@app.route('/api/v1/user/register', methods=['POST'])
def register():
    return User.register()

@app.route('/api/v1/user/login', methods=['POST'])
def login():
    return User.login()

@app.route('/api/v1/user/enable2FA', methods=['POST'])
def enable_2FA():
    return User.enable_2FA()

@app.route('/api/v1/user/disable2FA', methods=['POST'])
def disable_2FA():
    return User.disable_2FA()

@app.route('/api/v1/user/logout', methods=['POST'])
def logout():
    return User.logout()

@app.route('/api/v1/user/verify_totp', methods=['POST'])
def verify_totp():
    return User.verify_totp()

# HTML Seiten
@app.route('/dashboard')
def dashboard_page():
    return render_template('dashboard.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/verify_totp')
def verify_totp_page():
    return render_template('verify_totp.html')

if __name__ == "__main__":
    app.run(debug=True)