from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class BotSubmission(db.Model):
    __tablename__ = "bot_submission"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    code = db.Column(db.Text, nullable=False)
