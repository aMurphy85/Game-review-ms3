import os
import datetime
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGODB_NAME"] = os.environ.get("MONGODB_NAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/home")
def home():
    return render_template("index.html")


@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    games = list(mongo.db.games.find({"$text": {"$search": query}}))
    return render_template("games.html", games=games)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username already exists in database
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get(
                "password"))
        }
        mongo.db.users.insert_one(register)

        # put user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful, Welcome To Game Review!")
        return redirect(url_for(
                    "get_games", username=session["user"]))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists in database
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # confirm hashed password matches user input
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("username").lower()
                flash("Welcome back, {}!".format(request.form.get("username")))
                return redirect(url_for(
                    "get_games", username=session["user"]))
            else:
                # invalid password match
                flash("Invalid Username and/or Password!")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Invalid Username and/or Password!")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    # remove user session cookies
    flash("Logged Out Successfully!")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/get_games")
def get_games():
    games = list(mongo.db.games.find())
    return render_template("games.html", games=games)


@app.route("/game/<game_id>", methods=["GET", "POST"])
def game(game_id):
    game = mongo.db.games.find_one({"_id": ObjectId(game_id)})
    reviews = mongo.db.reviews.find(
        {"game_reference": game['game_title']})
    return render_template("game_card.html", game=game, reviews=reviews)


@app.route("/add_review", methods=["GET", "POST"])
def add_review():
    if session.get("user"):
        if request.method == "POST":
            review = {
                "game_reference": request.form.get("game_title"),
                "user_review": request.form.get("user_review"),
                "star_rating": request.form.get("star_rating"),
                "date_created": datetime.datetime.utcnow().strftime(
                    '%B %d %Y'),
                "created_by": session["user"]
            }
            mongo.db.reviews.insert_one(review)
            flash("Review Successfully Added!")
            return redirect(url_for("get_games"))

        game = mongo.db.games.find().sort("game_title", 1)
        return render_template("game_card.html", game=game)
    flash("You Must Be Logged In To Add A Review!")
    return redirect(url_for("login"))


@app.route("/edit_review/<review_id>", methods=["GET", "POST"])
def edit_review(review_id):
    if session.get("user"):
        if request.method == "POST":
            username = mongo.db.users.find_one(
                {"username": session["user"]})
            review = mongo.db.reviews.find_one({"_id": ObjectId(review_id)})
            if (session["user"] == review["created_by"]):

                update = {
                    "game_reference": request.form.get("game_title"),
                    "user_review": request.form.get("user_review"),
                    "star_rating": request.form.get("star_rating"),
                    "date": request.form.get("date"),
                    "created_by": session["user"]
                }
                mongo.db.reviews.update({"_id": ObjectId(review_id)}, update)
                flash("Review Successfully Updated!")
                return redirect(url_for(
                    "get_games", usename=username, review=review))

        review = mongo.db.reviews.find_one({"_id": ObjectId(review_id)})
        game = mongo.db.games.find().sort("game_title", 1)
        return render_template("game_card.html", review=review, game=game)
    flash("You Must Be Logged In To Edit A Review!")
    return redirect(url_for("login"))


@app.route("/delete_review/<review_id>")
def delete_review(review_id):
    if session.get("user"):
        username = mongo.db.users.find_one(
            {"username": session["user"]})
        review = mongo.db.reviews.find_one({"_id": ObjectId(review_id)})
        if (session["user"] == review["created_by"]):
            mongo.db.reviews.remove({"_id": ObjectId(review_id)})
            flash("Review Successfully Deleted!")
            return redirect(url_for(
                "home", username=username, review=review))
    flash("You Must Be Logged In To Edit A Review!")
    return redirect(url_for("login"))


# error handler
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html")


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
