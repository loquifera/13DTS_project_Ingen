from flask import Flask, render_template, request, redirect, session
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt

DATABASE = 'Ingen_db'

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "project_dominus"


def is_logged_in():
    if session.get("user_id") is None:
        print("Not logged in")
        return False
    else:
        print("logged in")
        return True


def clearance():
    if session.get("clearance_level") is None:
        return -1
    else:
        return session.get("clearance_level")


def connect_database(db_file):
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)
        print(f'An error occurred when connecting to the database')
    return


@app.route('/')
def render_home():  # put application's code here
    return render_template('home.html', logged_in=is_logged_in(), access_level=clearance())


@app.route('/signup', methods=['POST', 'GET'])
def render_signup():  # put application's code here
    if request.method == 'POST':
        fname = request.form.get('user_fname').title().strip()
        lname = request.form.get('user_lname').title().strip()
        email = request.form.get('user_email').lower().strip()
        password = request.form.get('user_password')
        password2 = request.form.get('user_password2')
        access = request.form.get('clearance_level')

        if access == None:
            access = 0

        if password != password2:
            return redirect('/signup?error=passwords+do+not+match', logged_in=is_logged_in())

        if len(password) < 8:
            return redirect('/signup?error=password+must+be+over+eight+characters', logged_in=is_logged_in())

        hashed_password = bcrypt.generate_password_hash(password)

        con = connect_database(DATABASE)
        query_insert = "INSERT INTO user (first_name, surname, email, password, clearance_level) VALUES (?, ?, ?, ?, ?)"
        cur = con.cursor()
        cur.execute(query_insert, (fname, lname, email, hashed_password, access))
        con.commit()
        con.close()
        return redirect('/')
    return render_template('signup.html', logged_in=is_logged_in(), access_level=clearance())


@app.route('/login', methods=['POST', 'GET'])
def render_login():  # put application's code here
    if is_logged_in():
        return redirect("/")
    if request.method == 'POST':
        email = request.form.get('user_email').strip().lower()
        password = request.form.get('user_password')

        query = "SELECT user_id, first_name, password, clearance_level FROM user WHERE email = ?"
        con = connect_database(DATABASE)
        cur = con.cursor()
        cur.execute(query, (email,))
        user_info = cur.fetchone()
        cur.close()

        try:
            user_id = user_info[0]
            first_name = user_info[1]
            user_password = user_info[2]
            clearance_level = user_info[3]
        except IndexError:
            return redirect('/login?error=email+or+password+incorrect')
        if not bcrypt.check_password_hash(user_password, password):
            return redirect('/login?error=email+or+password+incorrect')

        session['email'] = email
        session['user_id'] = user_id
        session['first_name'] = first_name
        session['clearance_level'] = clearance_level

        return redirect("/")
    return render_template('login.html', logged_in=is_logged_in(), access_level=clearance())


@app.route('/logout')
def logout():  # put application's code here
    session.clear()
    return redirect("/?message = see+you+next+time")


@app.route('/dinos')
def render_dinos():  # put application's code here
    con = connect_database(DATABASE)
    query = "SELECT * FROM dinosaurs WHERE clearance_required <= ?"
    query_user = "SELECT * FROM user"
    cur = con.cursor()
    cur.execute(query, (clearance(), ))
    dino_list = cur.fetchall()
    cur.execute(query_user)
    user_list = cur.fetchall()
    con.close()
    return render_template('dinosaurs.html', list_of_dinosaurs=dino_list, list_of_users=user_list, logged_in=is_logged_in(), access=clearance())


