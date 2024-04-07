import os
import random
from flask import (Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/index")
def index():
    reviews = list(mongo.db.reviews.find())
    random.shuffle(reviews)
    selected_reviews = reviews[:3]
    return render_template("index.html", reviews=selected_reviews)

@app.route("/get_reviews")
def get_reviews():
    reviews = list(mongo.db.reviews.find())
    return render_template("reviews.html", reviews=reviews)


@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    reviews = list(mongo.db.reviews.find({"$text": {"$search": query}}))
    return render_template("reviews.html", reviews=reviews)


@app.route('/review_details/<string:review_id>')
def review_details(review_id):
    review = mongo.db.reviews.find_one({'_id': ObjectId(review_id)})
    return render_template('review_details.html', review=review)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))
        elif request.form.get("password") != request.form.get(
                "password_check"):
            flash("Oops! Passwords do not match.")
            return redirect(url_for("register"))
        else:
            register = {
                "username": request.form.get("username").lower(),
                "password": generate_password_hash(request.form.get("password"))
            }
            mongo.db.users.insert_one(register)

            session["user"] = request.form.get("username").lower()
            flash("You have successfully registered!")
            return redirect(url_for("profile", username=session["user"]))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            if check_password_hash(
                existing_user["password"], request.form.get("password")):
                    session["user"] = request.form.get("username").lower()
                    flash("Welcome, {}".format(
                        request.form.get("username")))
                    return redirect(url_for(
                        "profile", username=session["user"]))
            else:
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]
    

    if session["user"]:
        user_reviews = list(mongo.db.reviews.find({"review_by": session["user"]}))
        return render_template("profile.html", username=username, user_reviews=user_reviews)

    return redirect(url_for("login"))
    

@app.route("/logout")
def logout():
    flash("You are logged out. Bye for now!")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/new_review", methods=["GET", "POST"])
def new_review():
    if request.method == "POST":
        review = {
            "genre_name": request.form.get("genre_name"),
            "song_name": request.form.get("song_name"),
            "artist_name": request.form.get("artist_name"),
            "explicit_language": request.form.get("explicit_language"),
            "review_title": request.form.get("review_title"),
            "review_content": request.form.get("review_content"),
            "review_by": session["user"]
        }
        mongo.db.reviews.insert_one(review)
        flash("Rock on! Your review has been submitted.")
        return redirect(url_for("get_reviews"))

    genres = mongo.db.genres.find().sort("genre_name", 1)
    return render_template("new_review.html", genres=genres)


@app.route("/edit_review/<review_id>", methods=["GET", "POST"])
def edit_review(review_id):
    if request.method == "POST":
        submit = {
            "genre_name": request.form.get("genre_name"),
            "song_name": request.form.get("song_name"),
            "artist_name": request.form.get("artist_name"),
            "explicit_language": request.form.get("explicit_language"),
            "review_title": request.form.get("review_title"),
            "review_content": request.form.get("review_content"),
            "review_by": session["user"]
        }
        mongo.db.reviews.replace_one({"_id": ObjectId(review_id)}, submit)
        flash("Rock on! Your review has been updated.")

    review = mongo.db.reviews.find_one({"_id": ObjectId(review_id)})
    if review["review_by"] != session["user"]:
        flash("This is not your review.")
        return redirect(url_for("get_reviews"))
    genres = mongo.db.genres.find().sort("genre_name", 1)
    return render_template("edit_review.html", review=review, genres=genres)


@app.route("/delete_review/<review_id>")
def delete_review(review_id):
    review = mongo.db.reviews.find_one({"_id": ObjectId(review_id)})
    print(review["review_by"], session["user"])
    if review["review_by"] != session["user"]:
        flash("This is not your review.")
        return redirect(url_for("get_reviews"))
    mongo.db.reviews.delete_one({"_id": ObjectId(review_id)})
    flash("Your review has been deleted.")
    return redirect(url_for("get_reviews"))


@app.errorhandler(404)
def page_not_found(e):
    """
    With 404 error user is passed to a custom 404 page within the application
    """
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(err):
    """
    With 500 error user is passed to a custom 404 page within the application
    """
    return render_template('500.html'), 500

if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
    port=int(os.environ.get("PORT")),
    debug=True)
