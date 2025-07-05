import os
from flask import Flask, request, render_template, redirect, url_for
from models import db, BotSubmission

from core.loader import load_bots
from core.results import return_results

app = Flask(__name__, instance_relative_config=True)

# Ensure the instance folder exists
try:
    os.makedirs(app.instance_path, exist_ok=True)
except OSError:
    pass

# Set up SQLite path and config
db_path = os.path.join(app.instance_path, "database.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Bind db to app
db.init_app(app)

# Create the DB and table schema
with app.app_context():
    db.create_all()
    print(f"[✓] DB should be at: {db_path}")

@app.route("/")
def index():
    bots = BotSubmission.query.all()
    return render_template("index.html", bots=bots)


@app.route("/submit", methods=["POST"])
def submit():
    try:
        bot_name = request.form["bot_name"]
        bot_file = request.files["bot_file"]

        if not bot_file.filename.endswith(".py"):
            return "Only .py files are allowed.", 400

        bot_code = bot_file.read().decode("utf-8")
        new_bot = BotSubmission(name=bot_name, code=bot_code)
        db.session.add(new_bot)
        db.session.commit()
        return f"Bot '{bot_name}' saved!"
    except Exception as e:
        db.session.rollback()
        return f"Error saving bot: {e}", 500

@app.route("/delete", methods=["POST"])
def delete_bot():
    bot_id = request.form.get("bot_id")
    bot = BotSubmission.query.get(bot_id)
    if bot:
        db.session.delete(bot)
        db.session.commit()
    return redirect(url_for("index"))
    
@app.route("/run", methods=["POST"])
def run_tournament():
    bots = load_bots()
    if not bots:
        return "No bots available.", 400
    results = return_results(bots)
    return render_template("leaderboard.html", results=results)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
