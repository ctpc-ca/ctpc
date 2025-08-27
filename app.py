import os

from flask import Flask
from flask_migrate import Migrate
from flask_session import Session

from models import User, db
from setup import bcrypt, login_manager
from views.admin.admin import admin
from views.api import api
from views.views import views

from tournament.routes import tournament_bp

def setup_app():
	app = Flask(__name__)
	app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
	app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
	app.config["MAX_CONTENT_LENGTH"] = 100 * 1024**2
	app.secret_key = os.environ["SECRET_KEY"]

	app.jinja_env.auto_reload = True
	app.config["TEMPLATES_AUTO_RELOAD"] = True

	app.config["SESSION_TYPE"] = "filesystem"
	app.config["SESSION_PERMANENT"] = False

	session_dir = os.path.join(os.getcwd(), ".flask_session")
	if not os.path.exists(session_dir):
		os.makedirs(session_dir)
	
	app.config["SESSION_FILE_DIR"] = session_dir

	Session(app)

	migrate = Migrate()

	db.init_app(app)
	migrate.init_app(app, db)
	bcrypt.init_app(app)
	login_manager.init_app(app)

	return app

app = setup_app()
app.register_blueprint(views)
app.register_blueprint(api)
app.register_blueprint(admin)
app.register_blueprint(tournament_bp)

@login_manager.user_loader
def load_user(user_id):
	return User.query.get(user_id)

if __name__ == "__main__":
	app.run(host="0.0.0.0", port=5000, debug=True)