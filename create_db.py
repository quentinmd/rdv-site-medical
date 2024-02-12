import sqlite3
from flask import Flask
from flask_bcrypt import Bcrypt

app = Flask(__name__)
bcrypt = Bcrypt(app)

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

# Appel de la fonction pour créer la base de données
create_database()
