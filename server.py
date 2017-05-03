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


@app.route("/login-page")
def login_page():

    return render_template("login.html")


@app.route("/login")
def login_process():
    """Takes information from register form and checks if a user with the
       email address/pwd matches, and if so, logs them in."""

    email = request.args.get("email")
    pwd = request.args.get("pwd")

    if db.session.query(User).filter(User.email == email, User.password == pwd
                                     ).first() is None:
        flash("Email/password combination do not match.")
        return redirect("/login-page")
    else:
        flash("Logged in! as %s" % email)
        user_id = db.session.query(User.user_id).filter(User.email == email).one()
        print user_id[0]
        session['user_id'] = user_id[0]
        return redirect("/")


if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True
    app.jinja_env.auto_reload = app.debug  # make sure templates, etc. are not cached in debug mode

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run(port=5000, host='0.0.0.0')
