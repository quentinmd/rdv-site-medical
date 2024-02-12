import sqlite3
from flask_bcrypt import Bcrypt

# Connexion à la base de données
conn = sqlite3.connect('ma_base_de_donnees.db')
cursor = conn.cursor()

# Exemple d'ajout d'utilisateurs à la table
utilisateurs = [
    ('quentin', 'motdepasse1'),
    ('yacine', 'motdepasse2'),
    # Ajoutez autant d'utilisateurs que nécessaire
]

bcrypt = Bcrypt()

# Utilisation d'une boucle pour insérer les utilisateurs dans la table
for utilisateur in utilisateurs:
    username, password = utilisateur
    # Hachez le mot de passe avant de l'insérer dans la base de données
    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    cursor.execute('INSERT INTO utilisateurs (username, password_hash) VALUES (?, ?)', (username, password_hash))

# Commit pour sauvegarder les modifications
conn.commit()

# Fermeture de la connexion
conn.close()
