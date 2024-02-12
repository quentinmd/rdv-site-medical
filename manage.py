from flask import Flask
from flask_migrate import Migrate
from serveur_3 import app, db  # Import your Flask app and SQLAlchemy db instance

migrate = Migrate(app, db)

if __name__ == '__main__':
    app.run()