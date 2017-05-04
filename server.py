"""Movie Ratings."""

from jinja2 import StrictUndefined

from flask import (Flask, render_template, redirect, request, flash,
                  session, jsonify)
from flask_debugtoolbar import DebugToolbarExtension

from model import User, Rating, Movie, connect_to_db, db


app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

# Normally, if you use an undefined variable in Jinja2, it fails
# silently. This is horrible. Fix this so that, instead, it raises an
# error.
app.jinja_env.undefined = StrictUndefined


@app.route('/')
def index():
    """Homepage."""

    return render_template("homepage.html")


@app.route("/users")
def user_list():
    """Show list of users; returns list of user objects."""

    users = User.query.all()
    return render_template("user_list.html", users=users)


@app.route("/movies")
def movie_list():
    """Show list of movies; returns list of movie titles."""

    movies = Movie.query.order_by(Movie.title).all()
    return render_template("movie_list.html", movies=movies)


@app.route("/register")
def register_form():
    """Renders register template form."""

    return render_template("register_form.html")


@app.route("/register", methods=["POST"])
def register_process():
    """Takes information from register form and checks if a user with the
       email address exists, and if not, creates a new user in the database."""

    email = request.form.get("email")
    pwd = request.form.get("pwd")

    if db.session.query(User).filter(User.email == email).first() is None:
        new_user = User(email=email, password=pwd)
        db.session.add(new_user)
        db.session.commit()

    return redirect("/login-page")


@app.route("/login")  # This is a get request.
def login_page():

    return render_template("login.html")


@app.route("/login", methods=["POST"])  # Post request; can have same route name.
def login_process():
    """Takes information from register form and checks if a user with the
       email address/pwd matches, and if so, logs them in."""

    email = request.form.get("email")
    pwd = request.form.get("pwd")

    if db.session.query(User).filter(User.email == email, User.password == pwd
                                     ).first() is None:
        flash("Email/password combination do not match.")
        return redirect("/login-page")
    else:
        flash("Logged in! as %s" % email)
        user_id = db.session.query(User.user_id).filter(User.email == email).one()
        print user_id[0]
        session['user_id'] = user_id[0]
        return redirect("/users/%s" % (user_id[0]))


@app.route("/logout")
def logout_process():
    """Logs out current user."""

    del session['user_id']
    flash("You are now logged out. Goodbye!")

    return redirect("/")


@app.route("/users/<user_id>")
def show_user_details(user_id):
    """Shows user details: age, zipcode, list of movies they rated and score."""

    user = db.session.query(User).get(user_id)

    return render_template("user_info.html", user=user)


@app.route("/movies/<movie_id>")
def show_movie_details(movie_id):
    """Shows movie details: title, release date, IMDB url, and list of ratings."""

    movie = Movie.query.get(movie_id)

    user_id = session.get('user_id')

    if user_id:
        user_rating = Rating.query.filter_by(
            movie_id=movie_id, user_id=user_id).first()
    else:
        user_rating = None

    # Get average rating of movie

    prediction = None

    rating_scores = [r.score for r in movie.ratings]
    avg_rating = float(sum(rating_scores)) / len(rating_scores)

     # Prediction: only predict if the user hasn't rated it.

    if (user_rating is None) and user_id:
        user = User.query.get(user_id)
        if user:
            prediction = user.predict_rating(movie)

    return render_template(
        "movie_info.html",
        movie=movie,
        user_rating=user_rating,
        average=avg_rating,
        prediction=prediction
        )


@app.route("/rate_movie", methods=["POST"])
def rate_movie():
    """Rates movie from the movie_info page if user is logged in."""

    if 'user_id' in session:
        movie_id = request.form.get("movie_id")
        user_id = session['user_id']
        score = request.form.get("new_rating")

        if db.session.query(Rating).filter(Rating.movie_id == movie_id,
                                           Rating.user_id == user_id).count() == 0:
            new_rating = Rating(movie_id=movie_id,
                                user_id=user_id,
                                score=score)
            db.session.add(new_rating)
        else:
            update = db.session.query(Rating).filter(Rating.movie_id == movie_id,
                                                     Rating.user_id == user_id).first()
            update.score = score

        db.session.commit()
        flash("Success! Your rating has been added!")
        return redirect("/")
    else:
        flash("Please log in!")
        return redirect("/login")
        # Auto redirects to a GET page, can't redirect to a POST page.


if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True
    app.jinja_env.auto_reload = app.debug  # make sure templates, etc. are not cached in debug mode

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run(port=5000, host='0.0.0.0')
