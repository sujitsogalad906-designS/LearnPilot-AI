
from datetime import datetime, timezone
from database.db import db


def utc_now():
    return datetime.now(timezone.utc)


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="student", nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now)

    attempts = db.relationship(
        "Attempt",
        backref="student",
        lazy=True
    )

    mastery_records = db.relationship(
        "LearnerMastery",
        backref="student",
        lazy=True
    )

    quiz_results = db.relationship(
        "QuizResult",
        backref="student",
        lazy=True,
        cascade="all, delete-orphan"
    )


class Concept(db.Model):
    __tablename__ = "concepts"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    subject = db.Column(db.String(100), default="Physics")
    chapter = db.Column(db.String(150), default="Electricity")
    difficulty = db.Column(db.String(30), default="beginner")

    questions = db.relationship(
        "Question",
        backref="concept",
        lazy=True
    )


class Question(db.Model):
    __tablename__ = "questions"

    id = db.Column(db.Integer, primary_key=True)
    concept_id = db.Column(db.Integer, db.ForeignKey("concepts.id"))
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(300), nullable=False)
    option_b = db.Column(db.String(300), nullable=False)
    option_c = db.Column(db.String(300), nullable=False)
    option_d = db.Column(db.String(300), nullable=False)
    correct_answer = db.Column(db.String(1), nullable=False)
    explanation = db.Column(db.Text)
    difficulty = db.Column(db.String(30), default="beginner")


class Attempt(db.Model):
    __tablename__ = "attempts"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"))
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"))
    selected_answer = db.Column(db.String(1))
    is_correct = db.Column(db.Boolean, default=False)
    attempted_at = db.Column(db.DateTime(timezone=True), default=utc_now)


class LearnerMastery(db.Model):
    __tablename__ = "learner_mastery"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"))
    concept_id = db.Column(db.Integer, db.ForeignKey("concepts.id"))
    mastery_score = db.Column(db.Float, default=0.0)
    mastery_level = db.Column(db.String(30), default="needs_attention")
    updated_at = db.Column(db.DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        db.UniqueConstraint(
            "student_id",
            "concept_id",
            name="unique_student_concept_mastery"
        ),
    )


class Misconception(db.Model):
    __tablename__ = "misconceptions"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"))
    concept_id = db.Column(db.Integer, db.ForeignKey("concepts.id"))
    description = db.Column(db.Text, nullable=False)
    detected_at = db.Column(db.DateTime(timezone=True), default=utc_now)
    resolved = db.Column(db.Boolean, default=False)


class RevisionSchedule(db.Model):
    __tablename__ = "revision_schedule"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"))
    concept_id = db.Column(db.Integer, db.ForeignKey("concepts.id"))
    revision_date = db.Column(db.DateTime(timezone=True), nullable=False)
    completed = db.Column(db.Boolean, default=False)

    # Relationship to access the concept name
    concept = db.relationship(
        "Concept",
        backref="revision_schedules"
    )


class QuizResult(db.Model):
    __tablename__ = "quiz_results"

    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.id"),
        nullable=False
    )

    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    percentage = db.Column(db.Float, nullable=False)
    performance = db.Column(db.String(50), nullable=False)

    completed_at = db.Column(
        db.DateTime(timezone=True),
        default=utc_now
    )
class DiagnosticResult(db.Model):
    __tablename__ = "diagnostic_results"

    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.id"),
        nullable=False
    )

    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    percentage = db.Column(db.Float, nullable=False)

    completed_at = db.Column(
        db.DateTime(timezone=True),
        default=utc_now
    )