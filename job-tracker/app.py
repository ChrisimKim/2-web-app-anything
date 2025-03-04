#!/usr/bin/env python3
import os
from datetime import datetime, timedelta
import certifi
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, current_user, login_required, logout_user
import pymongo
from bson.objectid import ObjectId
from dotenv import load_dotenv, dotenv_values
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()  # load environment variables from .env file


def create_app():
    app = Flask(__name__)
    secret_key = load_dotenv("SECRET_KEY")

    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

    config = dotenv_values()
    app.config.from_mapping(config)

    cxn = pymongo.MongoClient(os.getenv("MONGO_URI"),
                              tlsCAFile=certifi.where())
    db = cxn[os.getenv("MONGO_DBNAME")]

    try:
        cxn.admin.command("ping")
        print(" *", "Connected to MongoDB!")
    except Exception as e:
        print(" * MongoDB connection error:", e)

    #Login
    users_collection = db["Users"]
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    class User(UserMixin):

        def __init__(self, user_id, username, is_active=True):
            self.id = str(user_id)
            self.username = username
            self._is_active = is_active

        def is_active(self):
            return self._is_active

        def is_authenticated(self):
            return self.is_authenticated

        def get_id(self):
            return self.id

    @login_manager.user_loader
    def load_user(user_id):
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if user:
            return User(user_id=user["_id"],
                        username=user["username"],
                        is_active=True)
        else:
            return None

    # landing page
    @app.route('/')
    @login_required
    def landing():
        return render_template("landing.html")

    # login page
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")

            #check database for username
            user_data = users_collection.find_one({"username": username})
            if user_data:
                #check database for password
                if check_password_hash(user_data["password"], password):
                    #Create User instance (flask-login)
                    user = User(user_id=user_data["_id"],
                                username=user_data["username"],
                                is_active=True)

                    session["user_id"] = str(user_data["_id"])

                    login_user(user)
                    flash("Logged in successfully!", "success")
                    return redirect("/home")
                else:
                    flash("Invalid username or password.", "danger")
            else:
                flash("Invalid username or password.", "danger")

            # If login failed, re-render the login form
            return render_template("login.html")
        return render_template("login.html")

    # signup page
    @app.route('/signup', methods=['GET', 'POST'])
    def signup():
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")

            # Check if the username already exists in the database.
            if users_collection.find_one({"username": username}):
                flash("Username already exists. Please choose another.",
                      "danger")
                return render_template("signup.html")

            # hash password for security
            hashed_password = generate_password_hash(password, method='md5')

            #insert into database
            insert_result = users_collection.insert_one({
                "username":
                username,
                "password":
                hashed_password
            })
            user_id = insert_result.inserted_id

            #check that insert succesful
            if user_id:
                flash("Account created successfully!", "success")
                return redirect("/login")
            else:
                flash("An error occurred during signup. Please try again.",
                      "danger")
        return render_template("signup.html")

    @app.route('/addapplication', methods=['GET', 'POST'])
    @login_required
    def addapplication():
        if request.method == 'POST':
            company = request.form.get("company")
            role = request.form.get("role")
            category = request.form.get("category")
            location = request.form.get("location")
            flexibility = request.form.get("flexibility")
            status = request.form.get("status")
            date = request.form.get("date")
            link = request.form.get("applied-link")

            new_app = {
                "company": company,
                "role": role,
                "category": category,
                "location": location,
                "flexibility": flexibility,
                "status": status,
                "date": date,
                "link": link,
                "user": ObjectId(session.get("user_id"))
            }

            mongoid = db.Apps.insert_one(new_app)

            return redirect(url_for('addapplication'))

        current_date = datetime.now().strftime("%B %d, %Y")
        return render_template('addapplication.html',
                               current_date=current_date)

    @app.route('/addnew')
    @login_required
    def addnew():
        return render_template('addnew.html')

    # home dashboard page
    @app.route('/home')
    @login_required
    def home():
        # today's date
        today = datetime.now()

        # beginning of the week (Monday)
        week_start = today - timedelta(days=today.weekday())

        # beginning of the month
        month_start = datetime(today.year, today.month, 1)

        # adjusting time to midnight
        week_start = week_start.replace(hour=0,
                                        minute=0,
                                        second=0,
                                        microsecond=0)
        month_start = month_start.replace(hour=0,
                                          minute=0,
                                          second=0,
                                          microsecond=0)

        # getting user ID
        user_id = ObjectId(session.get("user_id"))

        # documents created this week
        docs_week_cursor = db.Apps.find({
            "$expr": {
                "$gte": [{
                    "$dateFromString": {
                        "dateString": "$date",
                        "format": "%m/%d/%Y"
                    }
                }, week_start]
            },
            "user": user_id
        })

        # documents created this month
        docs_month_cursor = db.Apps.find({
            "$expr": {
                "$gte": [{
                    "$dateFromString": {
                        "dateString": "$date",
                        "format": "%m/%d/%Y"
                    }
                }, month_start]
            },
            "user": user_id
        })

        # convert to lists
        docs_week = list(docs_week_cursor)
        docs_month = list(docs_month_cursor)

        # finding number of apps based on status
        accepted = db.Apps.count_documents({
            "status":
            "Offer Received",
            "user":
            ObjectId(session.get("user_id"))
        })
        interviewing = db.Apps.count_documents({
            "status":
            "Interview Scheduled",
            "user":
            ObjectId(session.get("user_id"))
        })
        rejected = db.Apps.count_documents({
            "status":
            "Rejected",
            "user":
            ObjectId(session.get("user_id"))
        })

        # finding total apps of user
        total = db.Apps.count_documents(
            {"user": ObjectId(session.get("user_id"))})

        # finding current logged user for name
        user = db.Users.find_one({"_id": ObjectId(session.get("user_id"))})

        return render_template("home.html",
                               user=user,
                               week=len(docs_week),
                               month=len(docs_month),
                               total=total,
                               accepted=accepted,
                               interviewing=interviewing,
                               rejected=rejected)

    # job tracking page
    @app.route('/track', methods=['GET', 'POST'])
    @login_required
    def track():
        # post request
        if request.method == 'POST':
            # get user input from search bar
            choice = request.form.get('status')

            if 'applied' in choice.lower() or 'interview' in choice.lower(
            ) or 'rejected' in choice.lower() or 'offer' in choice.lower():
                applications = db.Apps.find({
                    "user":
                    ObjectId(session.get("user_id")),
                    "status":
                    choice
                })
            elif choice.lower() == 'descending':
                applications = db.Apps.find({
                    "user":
                    ObjectId(session.get("user_id"))
                }).sort("date", 1)
            elif choice.lower() == 'ascending':
                applications = db.Apps.find({
                    "user":
                    ObjectId(session.get("user_id"))
                }).sort("date", -1)

            return render_template("track.html", applications=applications)

        # get request
        applications = db.Apps.find({
            "user": ObjectId(session.get("user_id"))
        }).sort("date", -1)
        return render_template("track.html", applications=applications)

    # edit app
    @app.route('/edit', methods=['POST'])
    @login_required
    def edit():
        app_id = request.form.get("app_id")
        company = request.form.get("company")
        role = request.form.get("role")
        category = request.form.get("category")
        location = request.form.get("location")
        flexibility = request.form.get("flexibility")
        status = request.form.get("status")
        date = request.form.get("date")
        link = request.form.get("applied-link")

        # update record
        updated = db.Apps.update_one({"_id": ObjectId(app_id)}, {
            "$set": {
                "company": company,
                "role": role,
                "category": category,
                "location": location,
                "flexibility": flexibility,
                "status": status,
                "date": date,
                "link": link
            }
        })

        return redirect(url_for('track'))

    # delete app
    @app.route('/delete', methods=['POST'])
    @login_required
    def delete():
        app_id = request.form.get("app_id")
        db.Apps.delete_one({"_id": ObjectId(app_id)})

        return redirect(url_for('track'))

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        session.pop('_flashes', None)
        session.pop("user_id", None)
        flash("You have been logged out.", "info")
        return redirect(url_for('login'))

    @app.errorhandler(Exception)
    def handle_error(e):
        """
        Output any errors - good for debugging.
        Args:
            e (Exception): The exception object.
        Returns:
            rendered template (str): The rendered HTML template.
        """
        return render_template("error.html", error=e)

    return app


app = create_app()

if __name__ == "__main__":
    FLASK_PORT = os.getenv("FLASK_PORT", "5000")
    FLASK_ENV = os.getenv("FLASK_ENV")
    print(f"FLASK_ENV: {FLASK_ENV}, FLASK_PORT: {FLASK_PORT}")

    app.run(port=FLASK_PORT)
