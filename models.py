from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy as sa

db = SQLAlchemy()

class User(UserMixin, db.Model):
	__tablename__ = "users"

	id = sa.Column(sa.Integer, primary_key=True)
	username = sa.Column(sa.String(100), nullable=False, unique=True)
	password = sa.Column(sa.String(100), nullable=False)
	role_id = sa.Column(sa.Integer, sa.ForeignKey("user_roles.id"), nullable=False)
	team_id = sa.Column(sa.Integer, sa.ForeignKey("teams.id"), nullable=True)
	school_id = sa.Column(sa.Integer, sa.ForeignKey("schools.id"), nullable=True)
	email = sa.Column(sa.String(100), nullable=True, default="")
	submissions = db.relationship("Submission", backref="user", lazy=True)
	completed_onboarding = sa.Column(sa.Boolean, default=False)
	first = sa.Column(sa.String(100), default="")
	last = sa.Column(sa.String(100), default="")
	profile = db.relationship("StudentProfile", uselist=False, backref="user")
	
	def __repr__(self):
		return f"<User {self.username}>"
	

class StudentProfile(db.Model):
	__tablename__ = "student_profiles"

	id = sa.Column(sa.Integer, primary_key=True)
	user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"))
	github_url = sa.Column(sa.String(100))
	resume_filename = sa.Column(sa.String(100))
	linkedin_url = sa.Column(sa.String(100))
	tshirt_size = sa.Column(sa.String(5))

	def __repr__(self):
		return f"<StudentProfile {self.id}>"
	

class UserRole(db.Model):
	__tablename__ = "user_roles"

	id = sa.Column(sa.Integer, primary_key=True)
	name = sa.Column(sa.String(100), nullable=False)
	users = db.relationship("User", backref="role", lazy=True)
	
	def __repr__(self):
		return f"<UserRole {self.name}>"
	

class Competition(db.Model):
	__tablename__ = "competitions"

	id = sa.Column(sa.Integer, primary_key=True)
	name = sa.Column(sa.String(100), nullable=False)
	short_name = sa.Column(sa.String(20), nullable=False)
	contests = db.relationship("Contest", backref="competition", lazy=True)
	schools = db.relationship("School", backref="competition", lazy=True)
	school_codes = db.relationship("SchoolCode", backref="competition", lazy=True)
	full_profile_cutoff = sa.Column(sa.Integer)
	registration_cutoff = sa.Column(sa.Integer)
	async_start = sa.Column(sa.Integer)
	async_end = sa.Column(sa.Integer)
	
	def __repr__(self):
		return f"<Competition {self.name}>"


class School(db.Model):
	__tablename__ = "schools"

	id = sa.Column(sa.Integer, primary_key=True)
	name = sa.Column(sa.String(100), nullable=False)
	school_board_id = sa.Column(sa.Integer, sa.ForeignKey("school_boards.id"), nullable=False)
	teams = db.relationship("Team", backref="school", lazy=True)
	members = db.relationship("User", backref="school", lazy=True)
	async_start_times = db.relationship("AsyncStartTime", backref="school", lazy=True)
	competition_id = sa.Column(sa.Integer, sa.ForeignKey("competitions.id"), nullable=True)
	consider_in_person = sa.Column(sa.Boolean, default=False)
	synchronous = sa.Column(sa.Boolean, default=False)
	in_person_spots = sa.Column(sa.Integer, default=0)
	
	def __repr__(self):
		return f"<School {self.name}>"
	

class AsyncStartTime(db.Model):
	__tablename__ = "async_start_times"

	id = sa.Column(sa.Integer, primary_key=True)
	school_id = sa.Column(sa.Integer, sa.ForeignKey("schools.id"), nullable=False)
	contest_id = sa.Column(sa.Integer, sa.ForeignKey("contests.id"), nullable=False)
	start_time = sa.Column(sa.Integer, nullable=False)
	end_time = sa.Column(sa.Integer, nullable=False)

	def __repr__(self):
		return f"<AsyncStartTime {self.id}>"
	

class SchoolCode(db.Model):
	__tablename__ = "school_codes"

	id = sa.Column(sa.Integer, primary_key=True)
	school_name = sa.Column(sa.String(100), nullable=False)
	school_board_id = sa.Column(sa.Integer, sa.ForeignKey("school_boards.id"), nullable=False)
	competition_id = sa.Column(sa.Integer, sa.ForeignKey("competitions.id"), nullable=False)
	code = sa.Column(sa.String(100), nullable=False)
	used = sa.Column(sa.Boolean, default=False)

	def __repr__(self):
		return f"<SchoolCode {self.code}>"
	

class SchoolBoard(db.Model):
	__tablename__ = "school_boards"

	id = sa.Column(sa.Integer, primary_key=True)
	name = sa.Column(sa.String(100), nullable=False)
	schools = db.relationship("School", backref="school_board", lazy=True)
	school_codes = db.relationship("SchoolCode", backref="school_board", lazy=True)

	def __init__(self, name):
		self.name = name
	
	def __repr__(self):
		return f"<SchoolBoard {self.name}>"
	

class Team(db.Model):
	__tablename__ = "teams"

	id = sa.Column(sa.Integer, primary_key=True)
	name = sa.Column(sa.String(100), nullable=False)
	school_id = sa.Column(sa.Integer, sa.ForeignKey("schools.id"), nullable=True)
	members = db.relationship("User", backref="team", lazy=True)
	in_person = sa.Column(sa.Boolean, default=False)
	team_code = sa.Column(sa.String(100), nullable=True)
	individual = sa.Column(sa.Boolean, default=False)

	def __init__(self, name, school_id):
		self.name = name
		self.school_id = school_id
	
	def __repr__(self):
		return f"<Team {self.name}>"
	

class ContestType(db.Model):
	__tablename__ = "contest_types"

	id = sa.Column(sa.Integer, primary_key=True)
	name = sa.Column(sa.String(100), nullable=False)
	contests = db.relationship("Contest", backref="contest_type", lazy=True)
	
	def __repr__(self):
		return f"<ContestType {self.name}>"
	

class Contest(db.Model):
	__tablename__ = "contests"

	id = sa.Column(sa.Integer, primary_key=True)
	name = sa.Column(sa.String(100), nullable=False)
	contest_type_id = sa.Column(sa.Integer, sa.ForeignKey("contest_types.id"), nullable=False)
	problems = db.relationship("Problem", backref="contest", lazy=True)
	start_date = sa.Column(sa.Integer, nullable=False)
	end_date = sa.Column(sa.Integer, nullable=False)
	competition_id = sa.Column(sa.Integer, sa.ForeignKey("competitions.id"), nullable=True)
	point_multiplier = sa.Column(sa.Numeric, default=1)
	hide_until_start = sa.Column(sa.Boolean, default=False)
	async_start_times = db.relationship("AsyncStartTime", backref="contest", lazy=True)
	
	def __repr__(self):
		return f"<Contest {self.name}>"
	

class Problem(db.Model):
	__tablename__ = "problems"

	id = sa.Column(sa.Integer, primary_key=True)
	name = sa.Column(sa.String(100), nullable=False)
	contest_id = sa.Column(sa.Integer, sa.ForeignKey("contests.id"), nullable=False)
	test_case_groups = db.relationship("AbstractTestCaseGroup", backref="problem", lazy=True)
	description = sa.Column(sa.Text)
	show_test_cases = sa.Column(sa.Boolean, default=False)
	point_value = sa.Column(sa.Integer, default=0)
	submissions = db.relationship("Submission", backref="problem", lazy=True)
	topics = db.relationship("ProblemTopic", backref="problem", lazy=True)
	
	def __repr__(self):
		return f"<Problem {self.name}>"
	

class Submission(db.Model):
	__tablename__ = "submissions"

	id = sa.Column(sa.Integer, primary_key=True)
	user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"), nullable=False)
	problem_id = sa.Column(sa.Integer, sa.ForeignKey("problems.id"), nullable=False)
	language_id = sa.Column(sa.Integer, sa.ForeignKey("language_types.id"), nullable=False)
	code = sa.Column(sa.Text, nullable=False)
	test_case_groups = db.relationship("TestCaseGroup", backref="submission", lazy=True)
	timestamp = sa.Column(sa.Integer, nullable=False)
	status_id = sa.Column(sa.Integer, sa.ForeignKey("submission_statuses.id"), nullable=False)
	points_earned = sa.Column(sa.Integer, default=0)
	is_practice = sa.Column(sa.Boolean, default=False)
	
	def __repr__(self):
		return f"<Submission {self.id}>"
	

class TestCase(db.Model):
	__tablename__ = "test_cases"

	id = sa.Column(sa.Integer, primary_key=True)
	output = sa.Column(sa.String(200), default="")
	abstract_test_case_id = sa.Column(sa.Integer, sa.ForeignKey("abstract_test_cases.id"), nullable=True)
	status_id = sa.Column(sa.Integer, sa.ForeignKey("test_case_statuses.id"), nullable=False)
	group_id = sa.Column(sa.Integer, sa.ForeignKey("test_case_groups.id"), nullable=False)
	
	def __repr__(self):
		return f"<TestCase {self.id}>"
	

class AbstractTestCaseGroup(db.Model):
	__tablename__ = "abstract_test_case_groups"

	id = sa.Column(sa.Integer, primary_key=True)
	problem_id = sa.Column(sa.Integer, sa.ForeignKey("problems.id"), nullable=False)
	test_cases = db.relationship("AbstractTestCase", backref="group", lazy=True)
	groups = db.relationship("TestCaseGroup", backref="abstract_group", lazy=True)
	point_value = sa.Column(sa.Integer, default=0)
	is_sample = sa.Column(sa.Boolean, default=False)
	
	def __repr__(self):
		return f"<AbstractTestCaseGroup {self.id}>"
	

class TestCaseGroup(db.Model):
	__tablename__ = "test_case_groups"

	id = sa.Column(sa.Integer, primary_key=True)
	abstract_group_id = sa.Column(sa.Integer, sa.ForeignKey("abstract_test_case_groups.id"), nullable=True)
	test_cases = db.relationship("TestCase", backref="group", lazy=True)
	points_earned = sa.Column(sa.Integer, default=0)
	submission_id = sa.Column(sa.Integer, sa.ForeignKey("submissions.id"), nullable=False)
	
	def __repr__(self):
		return f"<TestCaseGroup {self.id}>"
	

class AbstractTestCase(db.Model):
	__tablename__ = "abstract_test_cases"

	id = sa.Column(sa.Integer, primary_key=True)
	input = sa.Column(sa.Text, nullable=True)
	expected_output = sa.Column(sa.Text, nullable=True)
	explanation = sa.Column(sa.Text, nullable=True)
	test_cases = db.relationship("TestCase", backref="abstract_test_case", lazy=True)
	group_id = sa.Column(sa.Integer, sa.ForeignKey("abstract_test_case_groups.id"), nullable=True)

	def __repr__(self):
		return f"<AbstractTestCase {self.id}>"
	

class TestCaseStatus(db.Model):
	__tablename__ = "test_case_statuses"

	id = sa.Column(sa.Integer, primary_key=True)
	name = sa.Column(sa.String(100), nullable=False)
	test_cases = db.relationship("TestCase", backref="status", lazy=True)
	
	def __repr__(self):
		return f"<TestCaseStatus {self.name}>"
	

class SubmissionStatus(db.Model):
	__tablename__ = "submission_statuses"

	id = sa.Column(sa.Integer, primary_key=True)
	name = sa.Column(sa.String(100), nullable=False)
	submissions = db.relationship("Submission", backref="status", lazy=True)
	
	def __repr__(self):
		return f"<SubmissionStatus {self.name}>"
	

class LanguageType(db.Model):
	__tablename__ = "language_types"

	id = sa.Column(sa.Integer, primary_key=True)
	name = sa.Column(sa.String(100), nullable=False)
	short_name = sa.Column(sa.String(10), nullable=False)
	grader_id = sa.Column(sa.Integer, nullable=False)
	submissions = db.relationship("Submission", backref="language", lazy=True)
	
	def __repr__(self):
		return f"<LanguageType {self.name}>"
	

class Topic(db.Model):
	__tablename__ = "topics"

	id = sa.Column(sa.Integer, primary_key=True)
	name = sa.Column(sa.String(100), nullable=False)
	bg_color = sa.Column(sa.String(50), nullable=False)
	text_color = sa.Column(sa.String(50), nullable=False)
	problem_topics = db.relationship("ProblemTopic", backref="topic", lazy=True)

	def __repr__(self):
		return f"<Topic {self.name}>"
	

class ProblemTopic(db.Model):
	__tablename__ = "problem_topics"

	id = sa.Column(sa.Integer, primary_key=True)
	topic_id = sa.Column(sa.Integer, sa.ForeignKey("topics.id"), nullable=False)
	problem_id = sa.Column(sa.Integer, sa.ForeignKey("problems.id"), nullable=False)

	def __repr__(self):
		return f"<ProblemTopic {self.id}>"
	
class BotSubmission(db.Model):
	__tablename__ = "bot_submissions"

	id = sa.Column(sa.Integer, primary_key=True)
	user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"), nullable=True)
	user = db.relationship("User", backref="bot_submissions")

	name = sa.Column(sa.String(120), nullable=False)
	code = sa.Column(sa.Text, nullable=False)

	tournament_id = sa.Column(sa.Integer, sa.ForeignKey("tournaments.id"))
	tournament = db.relationship("Tournament", backref="bot_submissions")


class SampleBot(db.Model):
	__tablename__ = "sample_bots"

	id = sa.Column(sa.Integer, primary_key=True)
	user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"), nullable=True)
	user = db.relationship("User", backref="sample_bots")
	
	name = sa.Column(sa.String(120), nullable=False)
	code = sa.Column(sa.Text, nullable=False)

	tournament_id = sa.Column(sa.Integer, sa.ForeignKey("tournaments.id"))
	tournament = db.relationship("Tournament", backref="sample_bots")


class Game(db.Model):
	__tablename__ = "games"

	id = sa.Column(sa.Integer, primary_key=True)
	name = sa.Column(sa.Text, nullable=False)
	formatter_code = sa.Column(sa.Text, nullable=False)
	gameplay_code = sa.Column(sa.Text, nullable=False)
	termination_code = sa.Column(sa.Text, nullable=False)
	utils_code = sa.Column(sa.Text, nullable=False)

	description = sa.Column(sa.Text)
	examples = db.relationship("GameExample", backref="games", lazy=True)

class GameExample(db.Model):
	__tablename__ = "game_examples"

	id = sa.Column(sa.Integer, primary_key=True)
	game_id = sa.Column(sa.Integer, sa.ForeignKey("games.id"), nullable=False)
	example_text = sa.Column(sa.Text, nullable=True)

class Tournament(db.Model):

	__tablename__ = "tournaments"

	id = sa.Column(sa.Integer, primary_key=True)
	name = sa.Column(sa.String(100), nullable=False, unique=True)

	game_id = sa.Column(sa.Integer, sa.ForeignKey("games.id"), nullable=False)
	game = db.relationship("Game", backref="tournaments")

	start_date = sa.Column(sa.Integer, nullable=False)
	end_date = sa.Column(sa.Integer, nullable=False)

	def __repr__(self):
		return f"<Tournament {self.name}>"

