import flask
from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import sqlite3
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__, static_folder='assets')
app.config['SECRET_KEY'] = 'f42a73054b1749f8f58848be5e6502c'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ma_base_de_donnees.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'index'

class User(UserMixin):
    def __init__(self, user_id, username=None, password=None):
        self.id = user_id
        self.username = username
        self.password = password

    @staticmethod
    def load_user(user_id):
        user_info = get_user_info(user_id)
        if user_info:
            user = User(user_info['id'])
            user.load_info(user_info['username'], user_info['password'])
            return user
        else:
            return None

    def load_info(self, username, password):
        self.username = username
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    user_info = get_user_info(user_id)
    if user_info:
        user = User(user_info['id'])
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
    
class RendezVous(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, nullable=False)
    nom_patient = db.Column(db.String(50))


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
    user_id = current_user.id

    conn = sqlite3.connect('ma_base_de_donnees.db')
    cursor = conn.cursor()

    # Sélectionnez les rendez-vous pour l'utilisateur actuel
    cursor.execute('SELECT date, heure, id FROM rendez_vous WHERE user_id = ?', (user_id,))
    rendez_vous = cursor.fetchall()

    # Fermeture de la connexion
    conn.close()

    print("Rendez-vous récupérés:", rendez_vous)  # Ajoutez cette ligne pour déboguer

    rendez_vous_format = []

    for rdv in rendez_vous:
        date_obj = rdv[0]  # Si date est déjà un objet datetime, laissez-le tel quel
        heure_obj = rdv[1]  # Si heure est déjà un objet datetime, laissez-le tel quel

        rendez_vous_format.append((date_obj, heure_obj, rdv[2]))

    print("Rendez-vous formatés:", rendez_vous_format)  # Ajoutez cette ligne pour déboguer

    return render_template('compte.html', username=current_user.username, rendez_vous=rendez_vous_format)


# Modification et la suppression
@app.route('/modifier-rdv/<int:rdv_id>', methods=['GET', 'POST'])
@login_required
def modifier_rdv(rdv_id):
    if request.method == 'POST':
        # Récupérer la nouvelle date et heure depuis le formulaire
        nouvelle_date = request.form['nouvelle_date']
        nouvelle_heure = request.form['nouvelle_heure']

        # Mettre à jour le rendez-vous dans la base de données
        conn = sqlite3.connect('ma_base_de_donnees.db')
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


@app.route('/supprimer-rdv/<int:rdv_id>', methods=['POST'])
@login_required
def supprimer_rdv(rdv_id):
    # Supprimer le rendez-vous de la base de données
    conn = sqlite3.connect('ma_base_de_donnees.db')
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


@app.route('/mes-rdv')
@login_required
def mes_rdv():
    user_id = current_user.id

    conn = sqlite3.connect('ma_base_de_donnees.db')
    cursor = conn.cursor()

    # Récupérez les rendez-vous de l'utilisateur
    cursor.execute('SELECT date, heure FROM rendez_vous WHERE user_id = ?', (user_id,))
    rdvs = cursor.fetchall()

    # Fermeture de la connexion
    conn.close()

    return render_template('compte.html', rdvs=rdvs)


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
    
def supprimer_rdv_passes():
    now = datetime.now()
    conn = sqlite3.connect('ma_base_de_donnees.db')
    cursor = conn.cursor()

    # Sélectionnez les rendez-vous passés
    cursor.execute('SELECT id FROM rendez_vous WHERE datetime < ?', (now,))
    rdvs_passes = cursor.fetchall()

    # Supprimez les rendez-vous passés de la base de données
    for rdv_id in rdvs_passes:
        cursor.execute('DELETE FROM rendez_vous WHERE id = ?', (rdv_id,))

    # Commit pour sauvegarder les modifications
    conn.commit()

    # Fermeture de la connexion
    conn.close()

# Planifiez la tâche de suppression des rendez-vous passés toutes les heures
scheduler = BackgroundScheduler()
scheduler.add_job(supprimer_rdv_passes, 'interval', hours=1)
scheduler.start()


# Configuration de Flask-Admin
admin = Admin(app, name='Admin', template_mode='bootstrap3')
admin.add_view(ModelView(RendezVous, db.session))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Créez les tables dans la base de données si elles n'existent pas encore
    app.run(debug=True, port=8080)
