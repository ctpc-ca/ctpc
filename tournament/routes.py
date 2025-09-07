import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from util import admin_required
import time

from models import BotSubmission, SampleBot, Tournament, Game, db
from tournament.core.loader import load_bots
from tournament.core.results import round_robin
# from tournament.core.results import sandbox_results
from tournament.bot_runner.swiss import run_swiss_tournament

from tournament.loader import load_game_modules

tournament_bp = Blueprint("tournament", __name__, template_folder="../templates/tournament")

@tournament_bp.route("/tournaments")
@login_required
def view_tournaments():
    tournaments = Tournament.query.all()
    return render_template("tournament/tournaments.html", tournaments=tournaments, current_time=time.time())

@tournament_bp.route("/tournaments/<int:tournament_id>", methods=["GET", "POST"])
@login_required
def view_tournament(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    sample_bots = SampleBot.query.filter_by(tournament_id=tournament.id).all()

    sandbox_result = None
    state_histories = None
    move_histories = None
    match_results = None
    formatted_history = None
    user_stats = None
    success_message = None

    if request.method == "POST":
        action = request.form.get("action")
        bot_file = request.files.get("bot_file")
        bot_name = request.form.get("bot_name")

        if not bot_file or not bot_file.filename.endswith(".py"):
            return "Only .py files are allowed.", 400

        bot_code = bot_file.read().decode("utf-8")

        # if action == "sandbox":
        #     game_module = load_game_modules(tournament.game)
        #     utils = game_module["utils_code"]
        #     gameplay = game_module["gameplay_code"]
        #     termination = game_module["termination_code"]

        #     initial = utils.initial
        #     scoring = utils.scoring
        #     is_terminal = termination.is_terminal
        #     fetch_result = termination.fetch_result
        #     is_legal_move = gameplay.is_legal_move
        #     make_move = gameplay.make_move
        #     move_types = utils.move_types

        #     sandbox_result, state_histories, move_histories, match_results = sandbox_results(
        #         bot_code,
        #         sample_bots,
        #         initial=initial,
        #         scoring=scoring,
        #         is_terminal=is_terminal,
        #         fetch_result=fetch_result,
        #         is_legal_move=is_legal_move,
        #         make_move=make_move,
        #         move_types=move_types,
        #     )

        #     user_stats = {
        #         "wins": sum(bot["wins"] for bot in sandbox_result.values()),
        #         "draws": sum(bot["draws"] for bot in sandbox_result.values()),
        #         "losses": sum(bot["losses"] for bot in sandbox_result.values()),
        #         "score": sum(bot["score"] for bot in sandbox_result.values()),
        #     }

        #     format_state = None
        #     if state_histories:
        #         formatter = game_module["formatter_code"]
        #         format_state = formatter.format

        #         formatted_history = {
        #             bot1: {
        #                 bot2: [format_state(state) if format_state else state for state in history]
        #                 for bot2, history in opponents.items()
        #             }
        #             for bot1, opponents in state_histories.items()
        #         }

        #     return render_template("tournament/user_dashboard.html",
        #         tournament=tournament,
        #         sample_bots=sample_bots,
        #         results=sandbox_result,
        #         state_histories=formatted_history,
        #         move_histories=move_histories,
        #         success=success_message,
        #         user_stats=user_stats,
        #         match_results=match_results)

        if action == "submit":
            if current_user.role.name != "admin":
                BotSubmission.query.filter_by(user_id=current_user.id).delete()
                db.session.commit()

            new_bot = BotSubmission(
                name=bot_name,
                code=bot_code,
                user_id=current_user.id,
                tournament_id=tournament_id
            )
            db.session.add(new_bot)
            db.session.commit()
            success_message = "Bot submitted successfully!"

            # Now just render a fresh view with the message
            return render_template("tournament/user_dashboard.html",
                tournament=tournament,
                sample_bots=sample_bots,
                results=None,
                state_histories=None,
                move_histories=None,
                success=success_message,
                user_stats=None,
                match_results=None)

    # GET request: just render the dashboard
    return render_template("tournament/user_dashboard.html",
        tournament=tournament,
        sample_bots=sample_bots,
        results=None,
        state_histories=None,
        move_histories=None,
        success=None,
        user_stats=None,
        match_results=None)


@tournament_bp.route("/games/<int:game_id>")
@login_required
def view_game(game_id):
    game = Game.query.get_or_404(game_id)

    return render_template("tournament/game_info.html", game=game)

@tournament_bp.route("/tournament/<int:tournament_id>/admin", methods=["GET", "POST"])
@admin_required
def tournament_admin_dashboard(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)

    bots = BotSubmission.query.filter_by(tournament_id=tournament.id).all()
    sample_bots = SampleBot.query.filter_by(tournament_id=tournament.id).all()

    return render_template("tournament/admin_dashboard.html",
                           tournament=tournament,
                           bots=bots,
                           sample_bots=sample_bots)

@tournament_bp.route("/tournaments/<int:tournament_id>/submit", methods=["POST"])
@admin_required
def submit_bot(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    bot_name = request.form.get("bot_name")
    bot_file = request.files.get("bot_file")

    if not bot_file or not bot_file.filename.endswith(".py"):
        flash("Only .py files are allowed", "danger")
        return redirect(url_for("tournament.tournament_admin_dashboard", tournament_id=tournament_id))

    code = bot_file.read().decode("utf-8")
    bot = BotSubmission(user_id=current_user.id,
                        name=bot_name,
                        code=code,
                        tournament_id=tournament.id)
    db.session.add(bot)
    db.session.commit()
    flash("Bot submitted successfully!", "success")
    return redirect(url_for("tournament.tournament_admin_dashboard", tournament_id=tournament_id))

@tournament_bp.route("/tournaments/<int:tournament_id>/delete_bot", methods=["POST"])
@admin_required
def delete_bot(tournament_id):
    bot_id = request.form.get("bot_id")

    bot = BotSubmission.query.filter_by(id=bot_id, tournament_id=tournament_id).first()
    if bot:
        db.session.delete(bot)
        db.session.commit()

    return redirect(url_for('tournament.tournament_admin_dashboard', tournament_id=tournament_id))

@tournament_bp.route("/tournaments/<int:tournament_id>/run_round_robin", methods=["POST"])
@admin_required
def run_round_robin(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    bots = BotSubmission.query.filter_by(tournament_id=tournament.id).all()

    game_module = load_game_modules(tournament.game)
    utils = game_module["utils_code"]
    gameplay = game_module["gameplay_code"]
    termination = game_module["termination_code"]

    initial = utils.initial
    scoring = utils.scoring
    is_terminal = termination.is_terminal
    fetch_result = termination.fetch_result
    is_legal_move = gameplay.is_legal_move
    make_move = gameplay.make_move
    move_types = utils.move_types

    results, state_histories, move_histories, match_results = round_robin(
        bots=bots,
        verbose=False,
        initial=initial,
        scoring=scoring,
        is_terminal=is_terminal,
        fetch_result=fetch_result,
        is_legal_move=is_legal_move,
        make_move=make_move,
        move_types=move_types
    )

    return render_template("tournament/leaderboard.html",
                           results=results,
                           state_histories=state_histories,
                           move_histories=move_histories,
                           match_results=match_results,
                           scores=None,
                           swiss_log=None)

@tournament_bp.route("/tournaments/<int:tournament_id>/run_swiss", methods=["POST"])
@admin_required
def run_swiss(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    bots = BotSubmission.query.filter_by(tournament_id=tournament.id).all()
    bot_dict = {bot.name: bot for bot in bots}

    game_module = load_game_modules(tournament.game)
    utils = game_module["utils_code"]
    gameplay = game_module["gameplay_code"]
    termination = game_module["termination_code"]

    if not bots:
        return "No bots available.", 400

    num_rounds = int(request.form.get("num_rounds", 5))
    top_k = int(request.form.get("top_k", 4))

    initial = utils.initial
    scoring = utils.scoring
    is_terminal = termination.is_terminal
    fetch_result = termination.fetch_result
    is_legal_move = gameplay.is_legal_move
    make_move = gameplay.make_move
    move_types = utils.move_types

    # Swiss now returns PGNs instead of state/move histories
    top_bots, swiss_scores, pairings_log, pgn_swiss = run_swiss_tournament(
        bots=bots,
        num_rounds=num_rounds,
        top_k=top_k,
        verbose=False,
        initial=initial,
        scoring=scoring,
        is_terminal=is_terminal,
        fetch_result=fetch_result,
        is_legal_move=is_legal_move,
        make_move=make_move,
        move_types=move_types,
    )

    # Run RR on the top_k bots
    top_subset = [bot_dict[name] for name in top_bots]
    # Round-robin now returns PGNs as well
    final_results, pgn_round_robin, match_results = round_robin(
        bots=top_subset,
        verbose=False,
        initial=initial,
        scoring=scoring,
        is_terminal=is_terminal,
        fetch_result=fetch_result,
        is_legal_move=is_legal_move,
        make_move=make_move,
        move_types=move_types,
    )

    sorted_scores = sorted(
        swiss_scores.items(),  # list of (bot, {score, sb, win/draw/loss})
        key=lambda item: (-item[1]["score"], -item[1]["sb"])
    )

    return render_template(
        "tournament/leaderboard.html",
        results=final_results,
        match_results=match_results,
        swiss_log=pairings_log,
        scores=sorted_scores,
        qualified=top_k,
        pgn_swiss=pgn_swiss,               # defaultdict(str->defaultdict(list[str]))
        pgn_round_robin=pgn_round_robin,   # defaultdict(str->defaultdict(str))
    )

@tournament_bp.route("/tournaments/<int:tournament_id>/submit_sample_bot", methods=["POST"])
@admin_required
def submit_sample_bot(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    bot_name = request.form.get("bot_name")
    bot_file = request.files.get("bot_file")

    if not bot_file or not bot_file.filename.endswith(".py"):
        flash("Only .py files are allowed", "danger")
        return redirect(url_for("tournament.tournament_admin_dashboard", tournament_id=tournament_id))

    code = bot_file.read().decode("utf-8")

    bot = SampleBot(
        user_id=current_user.id,
        name=bot_name,
        code=code,
        tournament_id=tournament.id
    )

    db.session.add(bot)
    db.session.commit()
    flash("Sample bot uploaded successfully!", "success")
    return redirect(url_for("tournament.tournament_admin_dashboard", tournament_id=tournament_id))

@tournament_bp.route("/tournaments/<int:tournament_id>/delete_sample_bot", methods=["POST"])
@admin_required
def delete_sample_bot(tournament_id):
    bot_id = request.form.get("bot_id")

    bot = SampleBot.query.filter_by(id=bot_id, tournament_id=tournament_id).first()
    if bot:
        db.session.delete(bot)
        db.session.commit()

    return redirect(url_for('tournament.tournament_admin_dashboard', tournament_id=tournament_id))
