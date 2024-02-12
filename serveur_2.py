import flask 
from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import sqlite3
from flask_bcrypt import Bcrypt

app = Flask(__name__, static_folder='assets')
app.secret_key = 'f42a73054b1749f8f58848be5e6502c'
login_manager = LoginManager(app)
login_manager.login_view = 'index'


class User(UserMixin):
    pass

@login_manager.user_loader
def load_user(user_id):
    user = User()
    user.id = user_id
    return user

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

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Appel de la fonction de vérification du mot de passe
        if password_est_valide(username, password):
            # Mot de passe valide, redirigez vers la page de compte

            # Créez une instance User pour le gestionnaire de connexion
            user = User()
            user.id = get_user_id(username)  # Assurez-vous d'avoir une fonction get_user_id
            
            # Connectez l'utilisateur
            login_user(user)

            return redirect(url_for('compte'))
        else:
            # Mot de passe invalide, transmettez un message à la page HTML
            return render_template('index.html', error="Nom d'utilisateur ou mot de passe incorrect.")

    return render_template('index.html')  # Si la méthode n'est pas 'POST', afficher la page de connexion

@app.route('/compte')
@login_required
def compte():
    # Utilisez current_user.id pour récupérer l'user_id de l'utilisateur actuellement connecté
    print(current_user.is_authenticated)
    return render_template('compte.html')


@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        new_username = request.form['new_username']
        new_password = request.form['new_password']

        # Connexion à la base de données
        conn = sqlite3.connect('ma_base_de_donnees.db')
        cursor = conn.cursor()

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
    app.run(debug=True, port=8080)