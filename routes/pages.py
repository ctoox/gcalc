from flask import Blueprint, render_template

pages_bp = Blueprint("pages", __name__)

@pages_bp.route("/")
def home():
    return render_template("home.html")

@pages_bp.route("/decision")
def decision():
    return render_template("decision.html")

@pages_bp.route("/persons")
def persons():
    return render_template("persons.html")

@pages_bp.route("/discover")
def discover():
    return render_template("discover_v6_cosmic.html")

@pages_bp.route("/relationship")
def relationship():
    return render_template("relationship.html")
