
import json
from pathlib import Path
from datetime import datetime, timezone

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, jsonify
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from config import Config
from database.db import db

from database.models import (
    Student,
    QuizResult,
    Concept,
    Question,
    Attempt,
    LearnerMastery,
    Misconception,
    RevisionSchedule,
    DiagnosticResult
)


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


def load_json_file(filename):
    file_path = DATA_DIR / filename

    with file_path.open("r", encoding="utf-8") as file:
        return json.load(file)


# ==================================================
# CONCEPT SYNCHRONIZATION
# ==================================================

def sync_diagnostic_concepts():
    physics_data = load_json_file("physics_concepts.json")

    concept_map = {}

    for item in physics_data["concepts"]:
        concept = Concept.query.filter_by(
            name=item["title"],
            subject=physics_data.get("subject", "Physics"),
            chapter=physics_data.get("chapter", "Electricity")
        ).first()

        if not concept:
            concept = Concept(
                name=item["title"],
                description=item.get("description", ""),
                subject=physics_data.get("subject", "Physics"),
                chapter=physics_data.get("chapter", "Electricity"),
                difficulty=item.get("difficulty", "beginner").lower()
            )

            db.session.add(concept)
            db.session.flush()

        concept_map[item["id"]] = concept.id

    db.session.commit()

    return concept_map


# ==================================================
# STAGE 15 - QUESTION BANK SYNCHRONIZATION
# ==================================================

def sync_question_bank():
    question_data = load_json_file("question_bank.json")

    concept_map = sync_diagnostic_concepts()

    try:
        questions = question_data["questions"]

        for item in questions:
            question_id = int(item["id"])

            options = item["options"]
            correct_answer = item["correct_answer"]

            if len(options) != 4:
                raise ValueError(
                    f"Question {question_id} must have four options."
                )

            if correct_answer not in options:
                raise ValueError(
                    f"Invalid correct answer for question {question_id}."
                )

            concept_id = concept_map.get(item["concept_id"])

            if not concept_id:
                raise ValueError(
                    f"Concept not found for question {question_id}."
                )

            correct_letter = "ABCD"[options.index(correct_answer)]

            question_values = {
                "concept_id": concept_id,
                "question_text": item["question"],
                "option_a": options[0],
                "option_b": options[1],
                "option_c": options[2],
                "option_d": options[3],
                "correct_answer": correct_letter,
                "explanation": item.get("explanation", ""),
                "difficulty": item.get("difficulty", "Easy").lower()
            }

            database_question = db.session.get(
                Question,
                question_id
            )

            if database_question:
                for field, value in question_values.items():
                    setattr(database_question, field, value)

            else:
                database_question = Question(
                    id=question_id,
                    **question_values
                )

                db.session.add(database_question)

        db.session.commit()

        return len(questions)

    except Exception:
        db.session.rollback()
        raise


# ==================================================
# APPLICATION FACTORY
# ==================================================

def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    db.init_app(app)

    # ---------------- HOME ----------------

    @app.route("/")
    def home():
        if session.get("student_id"):
            return redirect(url_for("dashboard"))

        return redirect(url_for("login"))

    # ---------------- REGISTRATION ----------------

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")

            if not name or not email or not password:
                flash("Please fill in all fields.", "error")
                return redirect(url_for("register"))

            if len(password) < 8:
                flash(
                    "Password must contain at least 8 characters.",
                    "error"
                )
                return redirect(url_for("register"))

            existing_student = Student.query.filter_by(
                email=email
            ).first()

            if existing_student:
                flash("This email is already registered.", "error")
                return redirect(url_for("register"))

            student = Student(
                name=name,
                email=email,
                password_hash=generate_password_hash(password),
                role="student"
            )

            try:
                db.session.add(student)
                db.session.commit()

                flash(
                    "Registration successful! Please log in.",
                    "success"
                )

                return redirect(url_for("login"))

            except Exception:
                db.session.rollback()
                app.logger.exception("Registration failed.")

                flash(
                    "Registration could not be completed.",
                    "error"
                )

                return redirect(url_for("register"))

        return render_template("register.html")

    # ---------------- LOGIN ----------------

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form.get(
                "email", ""
            ).strip().lower()

            password = request.form.get("password", "")

            student = Student.query.filter_by(
                email=email
            ).first()

            if student and check_password_hash(
                student.password_hash, password
            ):
                session.clear()

                session["student_id"] = student.id
                session["student_name"] = student.name
                session["role"] = student.role

                return redirect(url_for("dashboard"))

            flash("Invalid email or password.", "error")

        return render_template("login.html")

    # ---------------- DASHBOARD ----------------

    @app.route("/dashboard")
    def dashboard():
        student_id = session.get("student_id")

        if not student_id:
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))

        student = db.session.get(Student, student_id)

        if not student:
            session.clear()
            return redirect(url_for("login"))

        return render_template(
            "dashboard.html",
            student=student
        )

    # ==================================================
    # STAGE 11 - MY MASTERY
    # ==================================================

    @app.route("/mastery")
    def my_mastery():
        student_id = session.get("student_id")

        if not student_id:
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))

        student = db.session.get(Student, student_id)

        if not student:
            session.clear()
            return redirect(url_for("login"))

        mastery_records = LearnerMastery.query.filter_by(
            student_id=student_id
        ).all()

        mastery_items = []

        for record in mastery_records:
            concept = (
                db.session.get(Concept, record.concept_id)
                if record.concept_id else None
            )

            score = max(
                0,
                min(100, float(record.mastery_score or 0))
            )

            mastery_items.append({
                "concept_name": (
                    concept.name if concept else "Unknown Concept"
                ),
                "score": round(score, 1),
                "level": record.mastery_level or "needs_attention"
            })

        overall_mastery = 0

        if mastery_items:
            overall_mastery = round(
                sum(item["score"] for item in mastery_items)
                / len(mastery_items)
            )

        mastered_count = sum(
            1 for item in mastery_items if item["score"] >= 80
        )

        improving_count = sum(
            1 for item in mastery_items
            if 50 <= item["score"] < 80
        )

        needs_attention_count = sum(
            1 for item in mastery_items if item["score"] < 50
        )

        quiz_results = QuizResult.query.filter_by(
            student_id=student_id
        ).order_by(
            QuizResult.completed_at.desc()
        ).limit(10).all()

        misconceptions = Misconception.query.filter_by(
            student_id=student_id,
            resolved=False
        ).all()

        revision_tasks = RevisionSchedule.query.filter_by(
            student_id=student_id,
            completed=False
        ).order_by(
            RevisionSchedule.revision_date.asc()
        ).all()

        average_quiz_score = 0

        if quiz_results:
            average_quiz_score = round(
                sum(result.percentage for result in quiz_results)
                / len(quiz_results),
                1
            )

        return render_template(
            "mastery.html",
            student=student,
            mastery_items=mastery_items,
            overall_mastery=overall_mastery,
            mastered_count=mastered_count,
            improving_count=improving_count,
            needs_attention_count=needs_attention_count,
            quiz_results=quiz_results,
            average_quiz_score=average_quiz_score,
            misconceptions=misconceptions,
            revision_tasks=revision_tasks
        )

    # ==================================================
    # STAGE 12 - REVISION SCHEDULE
    # ==================================================

    @app.route("/revision")
    def revision_schedule():
        student_id = session.get("student_id")

        if not student_id:
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))

        student = db.session.get(Student, student_id)

        if not student:
            session.clear()
            return redirect(url_for("login"))

        try:
            physics_data = load_json_file("physics_concepts.json")

            for item in physics_data["concepts"]:
                concept = Concept.query.filter_by(
                    name=item["title"],
                    subject=physics_data.get("subject", "Physics"),
                    chapter=physics_data.get("chapter", "Electricity")
                ).first()

                if not concept:
                    concept = Concept(
                        name=item["title"],
                        description=item.get("description", ""),
                        subject=physics_data.get("subject", "Physics"),
                        chapter=physics_data.get("chapter", "Electricity"),
                        difficulty=item.get(
                            "difficulty", "beginner"
                        ).lower()
                    )

                    db.session.add(concept)

            db.session.commit()

        except Exception:
            db.session.rollback()

            app.logger.exception(
                "Physics concept synchronization failed."
            )

            flash("Could not load Physics concepts.", "error")

            return redirect(url_for("dashboard"))

        concepts = Concept.query.filter_by(
            subject="Physics"
        ).order_by(Concept.id.asc()).all()

        pending_tasks = RevisionSchedule.query.filter_by(
            student_id=student_id,
            completed=False
        ).order_by(
            RevisionSchedule.revision_date.asc()
        ).all()

        completed_tasks = RevisionSchedule.query.filter_by(
            student_id=student_id,
            completed=True
        ).order_by(
            RevisionSchedule.revision_date.desc()
        ).all()

        return render_template(
            "revision.html",
            student=student,
            concepts=concepts,
            pending_tasks=pending_tasks,
            completed_tasks=completed_tasks
        )

    # ---------------- ADD REVISION TASK ----------------

    @app.route("/revision/add", methods=["POST"])
    def add_revision():
        student_id = session.get("student_id")

        if not student_id:
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))

        concept_id = request.form.get("concept_id", type=int)

        revision_date_text = request.form.get(
            "revision_date", ""
        ).strip()

        concept = (
            db.session.get(Concept, concept_id)
            if concept_id else None
        )

        if not concept or concept.subject != "Physics":
            flash(
                "Please select a valid Physics concept.",
                "error"
            )

            return redirect(url_for("revision_schedule"))

        try:
            revision_date = datetime.strptime(
                revision_date_text, "%Y-%m-%d"
            ).replace(tzinfo=timezone.utc)

            today = datetime.now(timezone.utc).date()

            if revision_date.date() < today:
                flash(
                    "Please select today or a future date.",
                    "error"
                )

                return redirect(url_for("revision_schedule"))

            revision_task = RevisionSchedule(
                student_id=student_id,
                concept_id=concept.id,
                revision_date=revision_date,
                completed=False
            )

            db.session.add(revision_task)
            db.session.commit()

            flash(
                "Revision task added successfully!",
                "success"
            )

        except ValueError:
            flash(
                "Please select a valid revision date.",
                "error"
            )

        except Exception:
            db.session.rollback()

            app.logger.exception("Failed to add revision task.")

            flash("Could not add revision task.", "error")

        return redirect(url_for("revision_schedule"))

    # ---------------- COMPLETE REVISION TASK ----------------

    @app.route("/revision/complete/<int:task_id>", methods=["POST"])
    def complete_revision(task_id):
        student_id = session.get("student_id")

        if not student_id:
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))

        task = RevisionSchedule.query.filter_by(
            id=task_id,
            student_id=student_id
        ).first()

        if not task:
            flash("Revision task not found.", "error")
            return redirect(url_for("revision_schedule"))

        task.completed = True

        try:
            db.session.commit()

            flash("Revision completed successfully!", "success")

        except Exception:
            db.session.rollback()

            app.logger.exception(
                "Failed to complete revision task."
            )

            flash("Could not update revision task.", "error")

        return redirect(url_for("revision_schedule"))

    # ---------------- LOGOUT ----------------

    @app.route("/logout")
    def logout():
        session.clear()

        flash("You have logged out successfully.", "success")

        return redirect(url_for("login"))

    # ==================================================
    # STAGE 9 - PHYSICS CONCEPT LIBRARY
    # ==================================================

    @app.route("/physics")
    def physics_library():
        if not session.get("student_id"):
            flash("Please log in to access Physics.", "error")
            return redirect(url_for("login"))

        try:
            physics_data = load_json_file("physics_concepts.json")

            return render_template(
                "concept_library.html",
                physics=physics_data,
                student_name=session.get("student_name")
            )

        except (FileNotFoundError, json.JSONDecodeError):
            return "Physics concept data could not be loaded.", 500

    # ---------------- INDIVIDUAL CONCEPT ----------------

    @app.route("/physics/concept/<int:concept_id>")
    def physics_concept(concept_id):
        if not session.get("student_id"):
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))

        try:
            physics_data = load_json_file("physics_concepts.json")

            concept = next(
                (
                    item for item in physics_data["concepts"]
                    if item["id"] == concept_id
                ),
                None
            )

            if concept is None:
                return "Concept not found.", 404

            return render_template(
                "concept_detail.html",
                concept=concept,
                physics=physics_data
            )

        except (FileNotFoundError, json.JSONDecodeError):
            return "Physics concept data could not be loaded.", 500

    # ==================================================
    # STAGE 9 - QUESTION BANK
    # ==================================================

    @app.route("/physics/questions")
    def physics_questions():
        if not session.get("student_id"):
            flash("Please log in to access questions.", "error")
            return redirect(url_for("login"))

        try:
            question_data = load_json_file("question_bank.json")

            return render_template(
                "question_bank.html",
                question_data=question_data
            )

        except (FileNotFoundError, json.JSONDecodeError):
            return "Question bank data could not be loaded.", 500

    # ==================================================
    # STAGE 13 - DIAGNOSTIC TEST
    # ==================================================

    @app.route("/diagnostic")
    def diagnostic_test():
        student_id = session.get("student_id")

        if not student_id:
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))

        student = db.session.get(Student, student_id)

        if not student:
            session.clear()
            return redirect(url_for("login"))

        try:
            question_data = load_json_file("question_bank.json")

            questions = []

            for question in question_data["questions"]:
                questions.append({
                    "id": question["id"],
                    "concept_id": question["concept_id"],
                    "question": question["question"],
                    "options": question["options"],
                    "difficulty": question.get("difficulty", "Easy")
                })

            if not questions:
                return "No diagnostic questions are available.", 404

            return render_template(
                "diagnostic.html",
                student=student,
                questions=questions
            )

        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            app.logger.exception(
                "Could not load diagnostic questions."
            )

            return "Diagnostic questions could not be loaded.", 500

    # ---------------- DIAGNOSTIC SUBMISSION API ----------------

    @app.route("/api/diagnostic/submit", methods=["POST"])
    def submit_diagnostic():
        student_id = session.get("student_id")

        if not student_id:
            return jsonify({
                "status": "error",
                "message": "Authentication required."
            }), 401

        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({
                "status": "error",
                "message": "Invalid JSON data."
            }), 400

        submitted_answers = data.get("answers")

        if not isinstance(submitted_answers, list) or not submitted_answers:
            return jsonify({
                "status": "error",
                "message": "No diagnostic answers were submitted."
            }), 400

        try:
            question_data = load_json_file("question_bank.json")
            physics_data = load_json_file("physics_concepts.json")

            question_bank = {
                question["id"]: question
                for question in question_data["questions"]
            }

            concept_names = {
                item["id"]: item["title"]
                for item in physics_data["concepts"]
            }

            concept_map = sync_diagnostic_concepts()

            seen_question_ids = set()
            concept_results = {}
            wrong_answers_by_concept = {}

            score = 0
            total_questions = 0

            # PROCESS STUDENT ANSWERS

            for answer in submitted_answers:

                if not isinstance(answer, dict):
                    return jsonify({
                        "status": "error",
                        "message": "Invalid answer format."
                    }), 400

                try:
                    question_id = int(answer.get("question_id"))

                except (TypeError, ValueError):
                    return jsonify({
                        "status": "error",
                        "message": "Invalid question ID."
                    }), 400

                if question_id in seen_question_ids:
                    return jsonify({
                        "status": "error",
                        "message": "Duplicate question answers are not allowed."
                    }), 400

                seen_question_ids.add(question_id)

                question = question_bank.get(question_id)

                if not question:
                    return jsonify({
                        "status": "error",
                        "message": "Unknown question submitted."
                    }), 400

                selected_answer = answer.get("selected_answer")

                if selected_answer not in question.get("options", []):
                    return jsonify({
                        "status": "error",
                        "message": "Invalid answer option."
                    }), 400

                json_concept_id = question["concept_id"]

                database_concept_id = concept_map.get(
                    json_concept_id
                )

                if not database_concept_id:
                    return jsonify({
                        "status": "error",
                        "message": "Question concept could not be found."
                    }), 400

                is_correct = (
                    selected_answer == question["correct_answer"]
                )

                total_questions += 1

                if is_correct:
                    score += 1

                if database_concept_id not in concept_results:
                    concept_results[database_concept_id] = {
                        "concept_id": database_concept_id,
                        "concept_name": concept_names.get(
                            json_concept_id,
                            "Unknown Concept"
                        ),
                        "correct": 0,
                        "total": 0
                    }

                concept_results[database_concept_id]["total"] += 1

                if is_correct:
                    concept_results[database_concept_id]["correct"] += 1

                # STAGE 14 - DETECT POTENTIAL MISCONCEPTIONS

                if not is_correct:

                    if database_concept_id not in wrong_answers_by_concept:
                        wrong_answers_by_concept[database_concept_id] = []

                    wrong_answers_by_concept[database_concept_id].append({
                        "question": question["question"],
                        "selected_answer": selected_answer,
                        "correct_answer": question["correct_answer"],
                        "explanation": question.get(
                            "explanation",
                            "Review this concept and its correct answer."
                        )
                    })

            if total_questions == 0:
                return jsonify({
                    "status": "error",
                    "message": "No valid answers were submitted."
                }), 400

            percentage = round(
                (score / total_questions) * 100, 2
            )

            # SAVE DIAGNOSTIC RESULT

            diagnostic_result = DiagnosticResult(
                student_id=student_id,
                score=score,
                total_questions=total_questions,
                percentage=percentage
            )

            db.session.add(diagnostic_result)

            # UPDATE LEARNER MASTERY

            concept_summary = []

            for concept_id, result in concept_results.items():

                concept_percentage = round(
                    (
                        result["correct"] / result["total"]
                    ) * 100,
                    2
                )

                if concept_percentage >= 80:
                    mastery_level = "strong"

                elif concept_percentage >= 50:
                    mastery_level = "developing"

                else:
                    mastery_level = "needs_attention"

                mastery = LearnerMastery.query.filter_by(
                    student_id=student_id,
                    concept_id=concept_id
                ).first()

                if not mastery:
                    mastery = LearnerMastery(
                        student_id=student_id,
                        concept_id=concept_id
                    )

                    db.session.add(mastery)

                mastery.mastery_score = concept_percentage
                mastery.mastery_level = mastery_level
                mastery.updated_at = datetime.now(timezone.utc)

                concept_summary.append({
                    "concept_name": result["concept_name"],
                    "correct": result["correct"],
                    "total": result["total"],
                    "percentage": concept_percentage,
                    "level": mastery_level
                })

            # STAGE 14 - SAVE MISCONCEPTION RECORDS

            for concept_id, wrong_answers in wrong_answers_by_concept.items():

                misconception_details = [
                    "Potential learning difficulty detected during diagnostic assessment."
                ]

                for item in wrong_answers:

                    misconception_details.append(
                        f"""
Question: {item['question']}
Student's Answer: {item['selected_answer']}
Correct Answer: {item['correct_answer']}
Explanation: {item['explanation']}
"""
                    )

                description = "\n".join(misconception_details)

                existing_misconception = Misconception.query.filter_by(
                    student_id=student_id,
                    concept_id=concept_id,
                    resolved=False
                ).first()

                if existing_misconception:

                    existing_misconception.description = description

                    existing_misconception.detected_at = datetime.now(
                        timezone.utc
                    )

                else:

                    new_misconception = Misconception(
                        student_id=student_id,
                        concept_id=concept_id,
                        description=description,
                        resolved=False
                    )

                    db.session.add(new_misconception)

            # SAVE ALL DATABASE CHANGES

            db.session.commit()

            if percentage >= 80:
                performance = "Excellent"

            elif percentage >= 50:
                performance = "Good"

            else:
                performance = "Needs Improvement"

            return jsonify({
                "status": "success",
                "message": "Diagnostic completed successfully.",
                "result": {
                    "diagnostic_id": diagnostic_result.id,
                    "score": score,
                    "total_questions": total_questions,
                    "percentage": percentage,
                    "performance": performance,
                    "concepts": concept_summary,
                    "misconceptions_detected": len(
                        wrong_answers_by_concept
                    )
                }
            }), 201

        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            db.session.rollback()

            app.logger.exception("Diagnostic data error.")

            return jsonify({
                "status": "error",
                "message": "Diagnostic data could not be processed."
            }), 500

        except Exception:
            db.session.rollback()

            app.logger.exception("Diagnostic submission failed.")

            return jsonify({
                "status": "error",
                "message": "Could not save diagnostic results."
            }), 500

    # ==================================================
    # STAGE 9 - PHYSICS APIs
    # ==================================================

    @app.route("/api/physics/concepts")
    def api_physics_concepts():
        if not session.get("student_id"):
            return jsonify({
                "status": "error",
                "message": "Authentication required."
            }), 401

        try:
            physics_data = load_json_file("physics_concepts.json")

            return jsonify({
                "status": "success",
                "total_concepts": len(physics_data["concepts"]),
                "data": physics_data
            })

        except (FileNotFoundError, json.JSONDecodeError):
            return jsonify({
                "status": "error",
                "message": "Physics data is unavailable."
            }), 500

    # ---------------- SINGLE CONCEPT API ----------------

    @app.route("/api/physics/concept/<int:concept_id>")
    def api_physics_concept(concept_id):
        if not session.get("student_id"):
            return jsonify({
                "status": "error",
                "message": "Authentication required."
            }), 401

        try:
            physics_data = load_json_file("physics_concepts.json")

            concept = next(
                (
                    item for item in physics_data["concepts"]
                    if item["id"] == concept_id
                ),
                None
            )

            if concept is None:
                return jsonify({
                    "status": "error",
                    "message": "Concept not found."
                }), 404

            return jsonify({
                "status": "success",
                "data": concept
            })

        except (FileNotFoundError, json.JSONDecodeError):
            return jsonify({
                "status": "error",
                "message": "Physics data is unavailable."
            }), 500

    # ---------------- QUESTIONS API ----------------

    @app.route("/api/physics/questions")
    def api_physics_questions():
        if not session.get("student_id"):
            return jsonify({
                "status": "error",
                "message": "Authentication required."
            }), 401

        try:
            question_data = load_json_file("question_bank.json")

            questions = question_data["questions"]

            concept_id = request.args.get("concept_id")
            difficulty = request.args.get("difficulty")

            if concept_id:
                try:
                    concept_id = int(concept_id)

                except ValueError:
                    return jsonify({
                        "status": "error",
                        "message": "concept_id must be a number."
                    }), 400

                questions = [
                    question for question in questions
                    if question["concept_id"] == concept_id
                ]

            if difficulty:
                questions = [
                    question for question in questions
                    if question["difficulty"].lower()
                    == difficulty.lower()
                ]

            return jsonify({
                "status": "success",
                "total_questions": len(questions),
                "data": questions
            })

        except (FileNotFoundError, json.JSONDecodeError):
            return jsonify({
                "status": "error",
                "message": "Question bank data is unavailable."
            }), 500

    # ==================================================
    # STAGE 15 - PRACTICE QUIZ AND INDIVIDUAL ATTEMPTS
    # ==================================================

    @app.route("/api/quiz/submit", methods=["POST"])
    def submit_quiz_result():
        student_id = session.get("student_id")

        if not student_id:
            return jsonify({
                "status": "error",
                "message": "Authentication required."
            }), 401

        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({
                "status": "error",
                "message": "Invalid JSON data."
            }), 400

        answers = data.get("answers")

        if not isinstance(answers, list) or not answers:
            return jsonify({
                "status": "error",
                "message": "Quiz answers are required."
            }), 400

        if len(answers) > 100:
            return jsonify({
                "status": "error",
                "message": "Too many quiz answers."
            }), 400

        try:
            processed_answers = []
            seen_question_ids = set()

            for answer in answers:

                if not isinstance(answer, dict):
                    raise ValueError("Invalid answer format.")

                try:
                    question_id = int(answer.get("question_id"))
                except (TypeError, ValueError):
                    raise ValueError("Invalid question ID.")

                selected_answer = str(
                    answer.get("selected_answer", "")
                ).upper()

                if selected_answer not in ["A", "B", "C", "D"]:
                    raise ValueError("Invalid selected answer.")

                if question_id in seen_question_ids:
                    raise ValueError("Duplicate question submitted.")

                seen_question_ids.add(question_id)

                question = db.session.get(
                    Question,
                    question_id
                )

                if not question:
                    raise ValueError(
                        f"Question {question_id} could not be found."
                    )

                is_correct = (
                    selected_answer == question.correct_answer
                )

                processed_answers.append({
                    "question_id": question_id,
                    "selected_answer": selected_answer,
                    "is_correct": is_correct
                })

            total_questions = len(processed_answers)

            score = sum(
                1 for answer in processed_answers
                if answer["is_correct"]
            )

            percentage = round(
                (score / total_questions) * 100,
                2
            )

            if percentage >= 80:
                performance = "Excellent"

            elif percentage >= 50:
                performance = "Good"

            else:
                performance = "Needs Improvement"

            # SAVE INDIVIDUAL ATTEMPTS

            for answer in processed_answers:

                attempt = Attempt(
                    student_id=student_id,
                    question_id=answer["question_id"],
                    selected_answer=answer["selected_answer"],
                    is_correct=answer["is_correct"]
                )

                db.session.add(attempt)

            # SAVE OVERALL QUIZ RESULT

            result = QuizResult(
                student_id=student_id,
                score=score,
                total_questions=total_questions,
                percentage=percentage,
                performance=performance
            )

            db.session.add(result)

            # COMMIT ALL CHANGES TOGETHER

            db.session.commit()

            return jsonify({
                "status": "success",
                "message": "Quiz result and individual attempts saved successfully.",
                "result": {
                    "id": result.id,
                    "score": score,
                    "total_questions": total_questions,
                    "percentage": percentage,
                    "performance": performance
                },
                "attempts_saved": len(processed_answers)
            }), 201

        except ValueError as error:
            db.session.rollback()

            return jsonify({
                "status": "error",
                "message": str(error)
            }), 400

        except Exception:
            db.session.rollback()

            app.logger.exception(
                "Quiz result and attempts could not be saved."
            )

            return jsonify({
                "status": "error",
                "message": "Could not save quiz result."
            }), 500

    # ---------------- HEALTH CHECK ----------------

    @app.route("/api/health")
    def health():
        return jsonify({
            "status": "success",
            "application": "LearnPilot AI"
        })

    # ---------------- DATABASE CHECK ----------------

    @app.route("/api/database-check")
    def database_check():
        try:
            with db.engine.connect() as connection:
                connection.exec_driver_sql("SELECT 1")

            return jsonify({
                "status": "success",
                "database": "connected",
                "tables": list(db.metadata.tables.keys())
            })

        except Exception:
            app.logger.exception("Database check failed.")

            return jsonify({
                "status": "error",
                "message": "Database connection failed."
            }), 500

    # ---------------- DATABASE INITIALIZATION ----------------

    with app.app_context():
        db.create_all()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
