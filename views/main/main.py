from flask import Blueprint, render_template, redirect, request
from flask_login import login_required, current_user, login_user
from time import time
import requests, markdown, re

from models import AbstractTestCaseGroup, AsyncStartTime, Competition, Contest, ContestType, \
	LanguageType, Problem, SchoolCode, Submission, SubmissionStatus, Team, TestCase, \
	TestCaseGroup, TestCaseStatus, User, db
from util import check_object_exists, logout_required
import handle_objects

main = Blueprint("main", __name__, template_folder="templates")


def can_access_contest(contest, submit=False):
	if current_user.role.name in ["admin", "tester"]:
		return True

	if contest.point_multiplier == 0 and time() > contest.start_date \
		and (not submit or time() < contest.end_date):
		return True

	if (current_user.school.synchronous or (current_user.team and current_user.team.in_person)) \
		and time() > contest.start_date and (not submit or time() < contest.end_date):
		return True
	
	if contest.competition.async_end is not None and time() > contest.competition.async_end \
		and not submit:
		return True
	
	async_start_time = AsyncStartTime.query \
		.filter_by(school=current_user.school, contest=contest) \
		.first()

	if async_start_time is None:
		return False
	
	if time() > async_start_time.start_time and (not submit or time() < async_start_time.end_time):
		return True
	
	return False


@main.route("/team")
@login_required
def team_view():
	if not current_user.role.name == "student":
		return redirect("/")
	
	return render_template("contest/team.html", team=current_user.team)


@main.route("/competitions")
@login_required
def competitions_view():
	if current_user.role.name == "student" and not current_user.completed_onboarding:
		return redirect("/student-onboarding")

	competitions = Competition.query.all()
	return render_template(
		"contest/competitions.html",
		competitions=competitions,
		current_time=time()
	)


@main.route("/competitions/<competition_id>")
@login_required
@check_object_exists(Competition, "/competitions", key_name="short_name")
def contests_view(competition):
	if current_user.role.name == "student" and not current_user.completed_onboarding:
		return redirect("/student-onboarding")

	contest_data = []

	for contest in competition.contests:
		async_start_time = AsyncStartTime.query \
			.filter_by(school=current_user.school, contest=contest) \
			.first()
		
		contest_data.append({
			"contest": contest
		})

		if (current_user.team is None or not current_user.team.in_person) \
			and (current_user.school is not None and not current_user.school.synchronous) \
			and (not current_user.role.name == "admin") and contest.point_multiplier > 0:
			contest_data[-1]["async_start_time"] = async_start_time

	return render_template(
		"contest/contests.html",
		contests=contest_data,
		current_time=time(),
		competition=competition
	)


def get_user_contest_data(contest):
	if contest.contest_type_id == ContestType.query.filter_by(name="individual").first().id \
		or not current_user.team:
		user_submissions = Submission.query \
			.join(Problem, Submission.problem_id == Problem.id) \
			.filter(Problem.contest_id == contest.id) \
			.filter(Submission.user_id == current_user.id) \
			.filter(Submission.is_practice == False)
	else:
		user_submissions = Submission.query \
			.join(Problem, Submission.problem_id == Problem.id) \
			.filter(Problem.contest_id == contest.id) \
			.join(User, Submission.user_id == User.id) \
			.join(Team, User.team_id == Team.id) \
			.filter(Team.id == current_user.team_id) \
			.filter(Submission.is_practice == False)
	
	ordered_submissions = user_submissions.order_by(Submission.points_earned.desc()).all()
	problem_dict = {
		problem.id: {
			"points_earned": 0,
			"point_value": problem.point_value,
			"has_submission": False,
			"title": problem.name,
			"id": problem.id
		} for problem in contest.problems
	}

	for sub in ordered_submissions:
		if not sub.problem.contest == contest:
			continue

		if problem_dict[sub.problem.id]["has_submission"]:
			continue

		problem_dict[sub.problem.id]["has_submission"] = True
		problem_dict[sub.problem.id]["points_earned"] = sub.points_earned

	return problem_dict, user_submissions


@main.route("/contest/<int:contest_id>")
@login_required
@check_object_exists(Contest, "/competitions")
def contest_view(contest):
	if not can_access_contest(contest):
		return redirect("/competitions")

	problem_dict, user_submissions = get_user_contest_data(contest)

	return render_template(
		"contest/contest.html",
		contest=contest,
		current_time=time(),
		user_submissions=user_submissions.order_by(Submission.timestamp.desc()).all(),
		problem_dict=problem_dict,
		show_topics=contest.point_multiplier == 0 or not can_access_contest(contest, submit=True) \
			or current_user.role.name in ["admin", "tester"]
	)


@main.route("/problem/<int:problem_id>")
@login_required
@check_object_exists(Problem, "/competitions")
def problem_view(problem):
	if not can_access_contest(problem.contest):
		return redirect("/competitions")
	
	sample_groups = AbstractTestCaseGroup.query \
		.filter_by(problem_id=problem.id, is_sample=True).all()
	languages = LanguageType.query.all()

	html_content = markdown.markdown(problem.description)

	return render_template(
		"contest/problem.html",
		problem=problem,
		problem_html=html_content,
		sample_groups=sample_groups,
		languages=languages,
		can_submit=can_access_contest(problem.contest, submit=True)
	)


@main.route("/submit/<int:problem_id>", methods=["POST"])
@login_required
@check_object_exists(Problem, "/competitions")
def submit(problem):
	if not can_access_contest(problem.contest, submit=True):
		return {
			"error": "Contest is over"
		}
	
	last_user_submission = Submission.query \
		.filter_by(user_id=current_user.id) \
		.filter_by(is_practice=False) \
		.order_by(Submission.timestamp.desc()) \
		.first()
	
	if last_user_submission and time() - last_user_submission.timestamp < 60 \
		and not current_user.role.name == "admin":
		return {
			"error": "You can only submit once per minute"
		}
	
	language_id = request.form["language"]
	code = request.form["code"]

	if len(code) == 0:
		return {
			"error": "You cannot submit a blank file"
		}

	language = LanguageType.query.filter_by(short_name=language_id).first()

	if not language:
		return redirect(f"/problem/{problem.id}")

	submission = Submission(
		user_id=current_user.id,
		problem_id=problem.id,
		language_id=language.id,
		code=code,
		timestamp=int(time()),
		status_id=SubmissionStatus.query.filter_by(name="Pending").first().id,
		is_practice=False
	)
	
	db.session.add(submission)
	db.session.commit()

	all_groups = []

	for tcg in problem.test_case_groups:
		test_case_group = TestCaseGroup(
			abstract_group_id=tcg.id,
			submission_id=submission.id
		)

		db.session.add(test_case_group)
		db.session.commit()

		all_groups.append([])

		for tc in tcg.test_cases:
			test_case = TestCase(
				abstract_test_case_id=tc.id,
				group_id=test_case_group.id,
				status_id=TestCaseStatus.query.filter_by(name="Pending").first().id
			)

			db.session.add(test_case)
			db.session.commit()

			all_groups[-1].append({
				"input": test_case.abstract_test_case.input,
				"expected_output": test_case.abstract_test_case.expected_output,
				"id": test_case.id
			})

	json_to_grader = {
		"code": submission.code,
		"testcases": all_groups,
		"language": language.grader_id,
		"submission_id": submission.id,
		"run_all": False
	}

	requests.post("http://127.0.0.1:8000/create-submission", json=json_to_grader)

	return { "id": submission.id }


@main.route("/submit-practice/<int:problem_id>", methods=["POST"])
@login_required
@check_object_exists(Problem, "/competitions")
def submit_practice(problem):
	if not can_access_contest(problem.contest, submit=True):
		return { "error": "Contest is over" }
	
	recent_practice_submissions = Submission.query \
		.filter(Submission.user_id == current_user.id) \
		.filter(Submission.timestamp > time() - 600, Submission.is_practice == True) \
		.all()
	
	if len(recent_practice_submissions) >= 15:
		return { "error": "Too many practice submissions", "ratelimit": "" }
	
	data = request.get_json()
	try:
		language = LanguageType.query.filter_by(short_name=data["language"]).first()
		code = data["code"]

		if len(code) == 0:
			return { "error": "You cannot submit a blank file" }
		
		test_cases = data["test_cases"]

		if not type(test_cases) == list or len(test_cases) > 10:
			raise Exception()
		
		send_to_grader = []

		for tc in test_cases:
			if not "expected_output" in tc or not "input" in tc \
				or len(tc["expected_output"]) > 2000 or len(tc["input"]) > 2000:
				raise Exception()
			
			send_to_grader.append({
				"input": tc["input"],
				"expected_output": tc["expected_output"]
			})

		submission = Submission(
			user_id=current_user.id,
			problem_id=problem.id,
			language_id=language.id,
			code=code,
			timestamp=int(time()),
			status_id=SubmissionStatus.query.filter_by(name="Pending").first().id,
			is_practice=True
		)

		db.session.add(submission)
		db.session.commit()

		test_case_group = TestCaseGroup(
			submission_id=submission.id,
			abstract_group_id=None
		)

		db.session.add(test_case_group)
		db.session.commit()

		for tc in send_to_grader:
			tc_obj = TestCase(
				abstract_test_case_id=None,
				group_id=test_case_group.id,
				status_id=TestCaseStatus.query.filter_by(name="Pending").first().id
			)
			db.session.add(tc_obj)
			db.session.commit()
			tc["id"] = tc_obj.id

		json_to_grader = {
			"code": code,
			"testcases": [send_to_grader],
			"language": language.grader_id,
			"submission_id": submission.id,
			"run_all": True
		}

		requests.post("http://127.0.0.1:8000/create-submission", json=json_to_grader)
	except Exception as e:
		print(e)
		return { "error": "An error occurred when submitting" }

	return { "id": submission.id }


@main.route("/practice-submission-status/<int:submission_id>")
@login_required
@check_object_exists(Submission, "/")
def practice_submission_status(submission):
	if not submission.user == current_user:
		return redirect("/")
	
	test_case_data = []

	for tcg in submission.test_case_groups:
		for tc in tcg.test_cases:
			test_case_data.append({
				"output": tc.output,
				"status": tc.status.name,
				"time": submission.timestamp
			})

	return test_case_data


@main.route("/last-practice-submission/<int:problem_id>")
@login_required
@check_object_exists(Problem, "/competitions")
def last_practice_submission(problem):
	if not can_access_contest(problem.contest):
		return []
	
	all_submissions = Submission.query \
		.filter(Submission.user_id == current_user.id) \
		.filter(Submission.problem_id == problem.id) \

	last_practice_submission = all_submissions \
		.filter(Submission.is_practice == True) \
		.order_by(Submission.timestamp.desc()) \
		.first()
	
	last_submission = all_submissions \
		.order_by(Submission.timestamp.desc()) \
		.first()
	
	test_case_data = []
	
	if last_practice_submission:
		for tcg in last_practice_submission.test_case_groups:
			for tc in tcg.test_cases:
				test_case_data.append({
					"output": tc.output,
					"status": tc.status.name,
					"time": last_practice_submission.timestamp
				})

	if last_submission:
		return {
			"test_cases": test_case_data,
			"code": last_submission.code,
			"language": last_submission.language.short_name,
			"timestamp": last_submission.timestamp
		}
	else:
		return {
			"test_cases": [],
			"code": "",
			"language": ""
		}


@main.route("/submission/<int:submission_id>")
@login_required
@check_object_exists(Submission, "/competitions")
def submission_view(submission):
	if not submission.user == current_user and not current_user.role.name == "admin" and not \
		(submission.problem.contest.contest_type.name == "team" and \
   		current_user.team and submission.user.team_id == current_user.team.id):
		return redirect("/")

	return render_template("contest/submission.html", submission=submission, current_time=time())


@main.route("/competitions/<competition_id>/register")
@check_object_exists(Competition, "/competitions", key_name="short_name")
def register(competition):
	return render_template("register.html", competition=competition)


@main.route("/competitions/<competition_id>/register/student", methods=["GET", "POST"])
@check_object_exists(Competition, "/competitions", key_name="short_name")
@logout_required
def register_as_student(competition):
	if request.method == "GET":
		return redirect("/")
		# return render_template("register-as-student.html", competition=competition)
	
	password = request.form.get("password")
	email = request.form.get("email")

	register_teacher_or_student(
		"", "", password, email,
		competition, "individual-student", "register-as-student.html"
	)
	return redirect(f"/competitions/{competition.short_name}")


@main.route("/competitions/<competition_id>/register/teacher", methods=["GET", "POST"])
@check_object_exists(Competition, "/competitions", key_name="short_name")
@logout_required
def register_as_teacher(competition):
	if request.method == "GET":
		return render_template("register-as-teacher.html", competition=competition)

	first = request.form.get("first")
	last = request.form.get("last")
	password = request.form.get("password")
	email = request.form.get("email")
	rawcode = request.form.get("schoolcode")
	code = ""
	for c in rawcode:
		if c.isalpha():
			code += c

	code_obj = SchoolCode.query.filter_by(code=code).first()

	if code_obj is None:
		return render_template(
			"register-as-teacher.html",
			competition=competition,
			error="School code is not valid"
		)
	
	if code_obj.used:
		return render_template(
			"register-as-teacher.html",
			competition=competition,
			error="School code has already been used"
		)
	
	school = handle_objects.add_school(
		code_obj.school_name,
		code_obj.school_board.id,
		code_obj.competition.id
	)

	user = register_teacher_or_student(
		first, last, password, email, competition, "teacher", "register-as-teacher.html"
	)
	if type(user) == str:
		return user

	user.school_id = school.id
	code_obj.used = True
	db.session.commit()

	return redirect("/teacher")


def register_teacher_or_student(first, last, password, email, competition, role, template):
	if not first or not last:
		return render_template(template, competition=competition, error="Invalid name")

	if not email or not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email):
		return render_template(template, competition=competition, error="Invalid email")

	if User.query.filter_by(email=email.lower()).first() is not None:
		return render_template(template, competition=competition, error="Email is already in use")
	
	if not password or not len(password) >= 8:
		return render_template(
			template,
			competition=competition,
			error="Password must be at least 8 characters"
		)

	first_clean, last_clean = "", ""
	for c in first.lower():
		if c in "abcdefghijklmnopqrstuvwxyz":
			first_clean += c

	for c in last.lower():
		if c in "abcdefghijklmnopqrstuvwxyz":
			last_clean += c

	if not first_clean and not last_clean:
		last_clean = "user"

	username_start = f"{first_clean[:3]}{last_clean[:5]}".lower()
	try:
		user, _ = handle_objects.add_student(username_start, password=password, role=role)
		user.email = email.lower()
		user.first = first
		user.last = last
	except Exception:
		return render_template(
			template,
			competition=competition,
			error="An error occurred when registering"
		)
	
	login_user(user)
	return user


@main.route("/editor/<int:problem_id>")
@login_required
@check_object_exists(Problem, "/competitions")
def editor(problem):
	if not can_access_contest(problem.contest):
		return redirect("/competitions")

	return render_template(
		"editor.html",
		problem=problem,
		languages=LanguageType.query.all(),
		can_submit=can_access_contest(problem.contest, submit=True)
	)


@main.route("/student-onboarding", methods=["GET", "POST"])
@login_required
def student_onboarding():
	if not current_user.role.name == "student":
		return redirect("/")
	
	full_profile_cutoff = current_user.school.competition.full_profile_cutoff
	full = True

	if full_profile_cutoff is not None and time() > full_profile_cutoff:
		full = False
	
	if request.method == "GET":
		return render_template("student-onboard.html", full=full)

	first = request.form.get("first")
	last = request.form.get("last")
	email = request.form.get("email")
	linkedin = request.form.get("linkedin")
	github = request.form.get("github")
	resume_file = request.files.get("resume")
	tshirt_size = request.form.get("tshirt")

	if not email or ((user := User.query.filter_by(email=email.lower()).first()) is not None \
		and not user.username == current_user.username):
		return render_template("student-onboard.html", full=full, error="Email is already in use")

	if not first or not last:
		return render_template(
			"student-onboard.html",
			full=full,
			error="Must include first and last name"
		)

	handle_objects.create_student_profile(
		current_user, first, last, email, github, linkedin, resume_file, tshirt_size
	)

	return redirect("/competitions/2025")