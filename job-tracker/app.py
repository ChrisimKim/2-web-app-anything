#!/usr/bin/env python3
import os
from datetime import datetime, timedelta
import certifi
from flask import Flask, render_template, request, redirect, url_for, flash
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

    # ObjectId of current logged in user. Will have to fetch this with pymongo commands later
    loggedUser = ObjectId('67bd0feb736f2e7829d2dbe9')

    #Login stuff
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
            return User(user_id = user["_id"], username = user["username"], is_active=True)
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
            user_data = users_collection.find_one({"username":username})
            if user_data:
                #check database for password
                if check_password_hash(user_data["password"],password):
                    #Create User instance (flask-login)
                    user = User(user_id = user_data["_id"],
                                username = user_data["username"],
                                is_active = True)
                    
                    login_user(user)
                    flash("Logged in successfully!", "success")
                    return redirect("/home")
                else:
                    flash("Invalid email or password.", "danger")
            else:
                flash("Invalid email or password.", "danger")

            # If login failed, re-render the login form
            return render_template("login.html")
        return render_template("login.html")
    

    # signup page
    @app.route('/signup', methods=['GET','POST'])
    def signup():
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
        
            # Check if the username already exists in the database.
            if users_collection.find_one({"username": username}):
                flash("Username already exists. Please choose another.", "danger")
                return render_template("signup.html")
            
            # hash password for security 
            hashed_password = generate_password_hash(password, method='sha256')

            #insert into database
            insert_result = users_collection.insert_one({"username": username,
                                         "password": hashed_password})
            user_id = insert_result.inserted_id

            #check that insert succesful 
            if user_id:
                flash("Account created successfully!", "success")
                return redirect("/login")
            else:
                flash("An error occurred during signup. Please try again.", "danger")
        return render_template("signup.html")

    # home page
    @app.route('/home')
    @login_required
    def home():
        # finding total apps of user
        total = db.Apps.count_documents({"user": loggedUser})

        # calculating dates
        today = datetime.now()

        week = today - timedelta(days=today.weekday())
        month = datetime(today.year, today.month, 1)

        iso_week = week.replace(hour=0, minute=0, second=0, microsecond=0)
        iso_month = month.replace(hour=0, minute=0, second=0, microsecond=0)

        # documents created this week and month
        docs_week_cursor = db.Apps.find({
            "date": {
                "$gte": iso_week
            },
            "user": loggedUser
        })
        docs_month_cursor = db.Apps.find({
            "date": {
                "$gte": iso_month
            },
            "user": loggedUser
        })

        # convert to lists
        docs_week = list(docs_week_cursor)
        docs_month = list(docs_month_cursor)

        # finding number of apps based on status
        accepted = db.Apps.count_documents({
            "status": "Accepted",
            "user": loggedUser
        })
        interviewing = db.Apps.count_documents({
            "status": "Interviewing",
            "user": loggedUser
        })
        rejected = db.Apps.count_documents({
            "status": "Rejected",
            "user": loggedUser
        })

        return render_template("home.html",
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

            if choice.lower() in 'applied interviewing rejected':
                applications = db.Apps.find({
                    "user": loggedUser,
                    "status": choice
                })
            elif choice.lower() == 'descending':
                applications = db.Apps.find({
                    "user": loggedUser
                }).sort("date", -1)
            elif choice.lower() == 'ascending':
                applications = db.Apps.find({
                    "user": loggedUser
                }).sort("date", 1)

            return render_template("track.html", applications=applications)

        # get request
        applications = db.Apps.find({"user": loggedUser})
        return render_template("track.html", applications=applications)

    # delete app
    @app.route('/delete', methods=['GET', 'POST'])
    @login_required
    def delete():
        # post request
        # if request.method == 'POST':
        db.Apps.delete_one({"_id": ObjectId('67bdf16a3028f7eee227824d')})

        applications = db.Apps.find({"user": loggedUser})
        return render_template("delete.html", applications=applications)

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
