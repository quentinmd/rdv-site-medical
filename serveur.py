import flask
from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import sqlite3
from flask_bcrypt import Bcrypt
from datetime import datetime

app = Flask(__name__, static_folder='assets')
app.secret_key = 'f42a73054b1749f8f58848be5e6502c'
login_manager = LoginManager(app)
login_manager.login_view = 'index'


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

def get_rendez_vous(user_id):
    conn = sqlite3.connect('instance/ma_base_de_donnees.db')
    cursor = conn.cursor()

    cursor.execute('SELECT datetime FROM rendez_vous WHERE user_id = ?', (user_id,))
    rendez_vous = cursor.fetchall()

    conn.close()

    return rendez_vous

def get_user_info(user_id):
    conn = sqlite3.connect('instance/ma_base_de_donnees.db')
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
    conn = sqlite3.connect('instance/ma_base_de_donnees.db')
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
            user_info = get_user_info(get_user_id(username))
            user = User(user_info['id'], user_info['username'], user_info['password'])

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
    # Récupérer les rendez-vous de la base de données pour l'utilisateur actuellement connecté
    rendez_vous = get_rendez_vous(current_user.id)
    
    # Passer les rendez-vous à la fonction render_template
    return render_template('compte.html', username=current_user.username, rendez_vous=rendez_vous)

# Modification et la suppression
@app.route('/modifier_rdv/<int:rdv_id>', methods=['GET', 'POST'])
@login_required
def modifier_rdv(rdv_id):
    if request.method == 'POST':
        # Récupérer la nouvelle date et heure depuis le formulaire
        nouvelle_date = request.form['nouvelle_date']
        nouvelle_heure = request.form['nouvelle_heure']

        # Mettre à jour le rendez-vous dans la base de données
        conn = sqlite3.connect('instance/ma_base_de_donnees.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE rendez_vous SET date=?, heure=? WHERE id=? AND user_id=?', (nouvelle_date, nouvelle_heure, rdv_id, current_user.id))
        conn.commit()
        conn.close()

        # Rediriger vers la page de compte après la modification
        return redirect(url_for('compte'))

    # Récupérer les détails du rendez-vous pour l'affichage dans le formulaire de modification
    conn = sqlite3.connect('ma_base_de_donnees.db')
    cursor = conn.cursor()
    cursor.execute('SELECT date, heure FROM rendez_vous WHERE id=? AND user_id=?', (rdv_id, current_user.id))
    rdv_details = cursor.fetchone()
    conn.close()

    return render_template('modifier_rdv.html', rdv_id=rdv_id, rdv_details=rdv_details)


@app.route('/supprimer_rdv/<int:rdv_id>', methods=['POST'])
@login_required
def supprimer_rdv(rdv_id):
    # Supprimer le rendez-vous de la base de données
    conn = sqlite3.connect('instance/ma_base_de_donnees.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM rendez_vous WHERE id=? AND user_id=?', (rdv_id, current_user.id))
    conn.commit()
    conn.close()

    # Rediriger vers la page de compte après la suppression
    return redirect(url_for('compte'))


@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        new_username = request.form['new_username']
        new_password = request.form['new_password']

        # Vérifier si le nom d'utilisateur existe déjà dans la base de données
        if username_exists(new_username):
            return render_template('index.html', error="Ce nom d'utilisateur est déjà utilisé. Veuillez choisir un autre.")

        # Hachez le mot de passe avant de l'insérer dans la base de données
        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')

        # Insérez le nouvel utilisateur dans la base de données
        with sqlite3.connect('instance/ma_base_de_donnees.db') as conn:
            cursor = conn.cursor()

            cursor.execute('INSERT INTO utilisateurs (username, password_hash) VALUES (?, ?)',
                           (new_username, hashed_password))
            conn.commit()

        # Redirigez l'utilisateur vers la page de connexion après la création du compte
        return redirect(url_for('index'))

    return render_template('index.html')  # Si la méthode n'est pas 'POST', afficher la page de connexion

def username_exists(username):
    conn = sqlite3.connect('instance/ma_base_de_donnees.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM utilisateurs WHERE username = ?', (username,))
    existing_user = cursor.fetchone()

    conn.close()

    return existing_user is not None


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/confirmer-rdv', methods=['POST'])
def confirmer_rdv():
    user_id = current_user.id
    heure = request.form['heure']
    date = request.form['date']

    # Combinez la date et l'heure pour créer un objet datetime
    datetime_str = f"{date} {heure}"
    rendez_vous_datetime = datetime.strptime(datetime_str, "%d-%m-%Y %H:%M")

    conn = sqlite3.connect('instance/ma_base_de_donnees.db')
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


@app.route('/prendre-rdv', methods=['GET', 'POST'])
@login_required
def prendre_rdv():
    if request.method == 'POST':
        # Récupérer les données du formulaire de rendez-vous
        date = request.form['date']
        heure = request.form['heure']
        # Ajouter le code pour enregistrer le rendez-vous dans la base de données
        return redirect(url_for('compte'))
    return render_template('prendre-rdv.html')


def get_user_id(username):
    conn = sqlite3.connect('instance/ma_base_de_donnees.db')
    cursor = conn.cursor()

    cursor.execute('SELECT id FROM utilisateurs WHERE username = ?', (username,))
    user_id = cursor.fetchone()

    conn.close()

    if user_id:
        return user_id[0]  # Retourne l'ID de l'utilisateur
    else:
        return None  # Retourne None si l'utilisateur n'est pas trouvé


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8080)
