import flask
from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import sqlite3
from datetime import datetime
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData

app = Flask(__name__)
app.secret_key = 'f42a73054b1749f8f58848be5e6502c'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/ma_base_de_donnees.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
metadata = MetaData()
login_manager = LoginManager(app)
login_manager.login_view = 'index'

login_manager = LoginManager(app)
login_manager.login_view = 'index'

class RendezVous(db.Model):
    __tablename__ = 'rendez_vous'
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, nullable=False)
    nom_patient = db.Column(db.String(50))

class User(UserMixin):
    def __init__(self, user_id, username, password):
        self.id = user_id
        self.username = username
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    user_info = get_user_info(user_id)
    if user_info:
        user = User(user_info['id'], user_info['username'], user_info['password'])
        return user
    else:
        return None

def get_user_info(user_id):
    conn = sqlite3.connect('ma_base_de_donnees.db')
    cursor = conn.cursor()

    cursor.execute('SELECT id, username, password_hash FROM utilisateurs WHERE id = ?', (user_id,))
    user_info = cursor.fetchone()

    conn.close()

    if user_info:
        return {'id': user_info[0], 'username': user_info[1], 'password': user_info[2]}
    else:
        return None

@app.route('/')
def index():
    return render_template('index.html')

bcrypt = Bcrypt(app)

def password_est_valide(username, password):
    # Connexion à la base de données
    conn = sqlite3.connect('ma_base_de_donnees.db')
    cursor = conn.cursor()

    # Exécutez une requête pour obtenir le mot de passe haché associé à l'utilisateur
    cursor.execute('SELECT * FROM utilisateurs WHERE username = ?', (username,))
    utilisateur = cursor.fetchone()

    if utilisateur and bcrypt.check_password_hash(utilisateur[2], password):
        # Le mot de passe correspond, l'utilisateur est authentifié
        return True
    else:
        # Le mot de passe ne correspond pas, l'utilisateur n'est pas authentifié
        return False

    # Fermeture de la connexion
    conn.close()

def create_database():
    try:
        with sqlite3.connect('instance/ma_base_de_donnees.db') as conn:
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS utilisateurs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rendez_vous (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    datetime DATETIME NOT NULL,
                    nom_patient TEXT
                )
            ''')

            conn.commit()

    except Exception as e:
        print(f"Erreur lors de la création de la base de données : {e}")

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if password_est_valide(username, password):
            user_info = get_user_info(get_user_id(username))
            user = User(user_info['id'], user_info['username'], user_info['password'])
            login_user(user)
            return redirect(url_for('compte'))
        else:
            return render_template('index.html', error="Nom d'utilisateur ou mot de passe incorrect.")

    return render_template('index.html')

@app.route('/compte')
@login_required
def compte():
    # Utilisez current_user.id pour récupérer l'user_id de l'utilisateur actuellement connecté
    username = current_user.username  # Utilisez current_user.username pour récupérer le nom d'utilisateur
    return render_template('compte.html', username=username)

@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        new_username = request.form['new_username']
        new_password = request.form['new_password']

        # Connexion à la base de données
        conn = sqlite3.connect('ma_base_de_donnees.db')
        cursor = conn.cursor()

        # Vérifiez si le nom d'utilisateur est déjà pris
        cursor.execute('SELECT * FROM utilisateurs WHERE username = ?', (new_username,))
        existing_user = cursor.fetchone()

        if existing_user:
            # Nom d'utilisateur déjà pris, transmettez un message à la page HTML
            return render_template('index.html', error="Le nom d'utilisateur est déjà pris.")

        # Hachez le mot de passe avant de l'insérer dans la base de données
        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')

        # Insérez le nouvel utilisateur dans la base de données
        cursor.execute('INSERT INTO utilisateurs (username, password_hash) VALUES (?, ?)', (new_username, hashed_password))

        # Commit pour sauvegarder les modifications
        conn.commit()

        # Fermeture de la connexion
        conn.close()

        # Redirigez l'utilisateur vers la page de connexion après la création du compte
        return redirect(url_for('index'))

    return render_template('index.html')  # Si la méthode n'est pas 'POST', afficher la page de connexion

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/prendre-rdv')
def prendre_rdv():
    return render_template('prendre-rdv.html')

@app.route('/confirmer-rdv', methods=['POST'])
def confirmer_rdv():
    user_id = current_user.id
    heure = request.form['heure']
    date = request.form['date']

    # Combinez la date et l'heure pour créer un objet datetime
    datetime_str = f"{date} {heure}"
    rendez_vous_datetime = datetime.strptime(datetime_str, "%d-%m-%Y %H:%M")

    conn = sqlite3.connect('ma_base_de_donnees.db')
    cursor = conn.cursor()

    # Insérez le rendez-vous dans la table
    cursor.execute('INSERT INTO rendez_vous (user_id, datetime) VALUES (?, ?)', (user_id, rendez_vous_datetime))

    # Commit pour sauvegarder les modifications
    conn.commit()

    # Fermeture de la connexion
    conn.close()

    # Générer l'URL de la page de compte
    compte_url = url_for('compte')

    # Renvoyer la réponse avec un lien de retour
    return f"Rendez-vous confirmé pour le {date} à {heure}. <br><a href='{compte_url}'>Retour au compte</a>"

def get_user_id(username):
    conn = sqlite3.connect('ma_base_de_donnees.db')
    cursor = conn.cursor()

    cursor.execute('SELECT id FROM utilisateurs WHERE username = ?', (username,))
    user_id = cursor.fetchone()

    conn.close()

    if user_id:
        return user_id[0]  # Retourne l'ID de l'utilisateur
    else:
        return None  # Retourne None si l'utilisateur n'est pas trouvé

if __name__ == '__main__':
    create_database()
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=8080)