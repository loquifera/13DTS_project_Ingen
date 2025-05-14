from flask import Flask, render_template, request, redirect, session
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt

DATABASE = 'Ingen_db'

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "project_dominus"


def is_logged_in():
    """
    This function simply tests to see if the user is logged in
    :return: It will return true or false based on if the user is logged in or not
    """
    if session.get("user_id") is None:
        return False
    else:
        return True


def clearance():
    """
    Similarly to the logged in function this will test to see the users clearance level which is used to give them access to various sections of the website
    :return: If they aren't logged in it will return -1 which means they have no clearance and can barely use the website but othewise will return an integer of the users clearance.
    """
    if session.get("clearance_level") is None:
        return -1
    else:
        return session.get("clearance_level")


def connect_database(db_file):
    """
    This function starts a connection to my database
    :param db_file: This is the database file the function will try to connect to.
    :return: Returns the connection top the database so that it can be used.
    """
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)
        print(f'An error occurred when connecting to the database')
    return


@app.route('/')
def render_home():  # put application's code here
    """
    :return:Renders the home page with the users access level and if they are logged in or not
    """
    return render_template('home.html', logged_in=is_logged_in(), access_level=clearance())


@app.route('/signup', methods=['POST', 'GET'])
def render_signup():  # put application's code here
    """

    :return:
    """
    if request.method == 'POST':
        fname = request.form.get('user_fname').title().strip()
        lname = request.form.get('user_lname').title().strip()
        email = request.form.get('user_email').lower().strip()
        password = request.form.get('user_password')
        password2 = request.form.get('user_password2')
        access = request.form.get('clearance_level')

        if access is None:
            access = 0

        if password != password2:
            return redirect('/signup?error=passwords+do+not+match', logged_in=is_logged_in())

        if len(password) < 8:
            return redirect('/signup?error=password+must+be+over+eight+characters', logged_in=is_logged_in())

        hashed_password = bcrypt.generate_password_hash(password)  # This line uses the Bcrypt 

        con = connect_database(DATABASE)
        query_insert = "INSERT INTO user (first_name, surname, email, password, clearance_level) VALUES (?, ?, ?, ?, ?)"
        cur = con.cursor()
        cur.execute(query_insert, (fname, lname, email, hashed_password, access))
        con.commit()
        con.close()
        return redirect('/login')
    return render_template('signup.html', logged_in=is_logged_in(), access_level=clearance())


@app.route('/login', methods=['POST', 'GET'])
def render_login():  # put application's code here
    """
    If the user is already logged in they will be redirected to the home page, if not then it will render the
    login page, after entering their information it will run the POST section of code.
    :return: When the POST code is run, if any information is wrong it will redirect them to re-enter their information
    if the entered password and email are correct then it will update the session to hold the information of the user.
    """
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
        except:
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
    """
    Logs out the user.
    :return: Sends the user back to the home page.
    """
    session.clear()
    return redirect("/?message = see+you+next+time")


@app.route('/dinos')
def render_dinos():  # put application's code here
    """
    This route gets the data for all dinosaurs that the user has clearance to view then renders the dino page.
    :return:Returns the information to render the dinosaurs page, list of dinosaurs hold the information from the
    dinosaurs database and the list of users in a similar fashion.
    """
    con = connect_database(DATABASE)
    query = "SELECT * FROM dinosaurs WHERE clearance_required <= ?"
    query_user = "SELECT * FROM user"
    cur = con.cursor()
    cur.execute(query, (clearance(), ))
    dino_list = cur.fetchall()
    cur.execute(query_user)
    user_list = cur.fetchall()
    con.close()
    return render_template('dinosaurs.html', list_of_dinosaurs=dino_list, list_of_users=user_list, logged_in=is_logged_in(), access_level=clearance())


@app.route('/transport', methods=['POST', 'GET'])
def render_transport():  # put application's code here
    if not is_logged_in():
        return redirect("/")
    if not clearance() >= 3:
        return redirect("/")
    con = connect_database(DATABASE)
    query_transport = "SELECT * FROM transport_log INNER JOIN dinosaurs ON transport_log.fk_dino_id = dinosaurs.dino_id;"
    cur = con.cursor()
    cur.execute(query_transport)
    transport_list = cur.fetchall()
    query_dinos = "SELECT * FROM dinosaurs WHERE clearance_required <= ?"
    cur.execute(query_dinos, (clearance(),))
    dino_list = cur.fetchall()
    if request.method == 'POST':
        con = connect_database(DATABASE)
        fk_dino_id = request.form.get('select_dinosaur').strip("()")
        fk_dino_id = fk_dino_id.split()
        new_location = request.form.get('place').strip()
        time = request.form.get('time')
        date = request.form.get('date')

        query_transport_insert = "INSERT INTO transport_log (fk_dino_id, date, time, new_location) VALUES (?, ?, ?, ?)"
        cur = con.cursor()
        cur.execute(query_transport_insert, (fk_dino_id[0].strip(","), date, time, new_location))
        query_dino_insert = "UPDATE dinosaurs SET location = ? WHERE dino_id = ?;"
        cur.execute(query_dino_insert, (new_location, fk_dino_id[0].strip(",")))
        con.commit()
        con.close()
        return redirect('/transport')
    return render_template('transport.html', logged_in=is_logged_in(), access_level=clearance(), list_of_transports=transport_list, list_of_dinosaurs=dino_list)


@app.route('/delete_transport', methods=['POST', 'GET'])
def delete_transport():
    if not is_logged_in():
        return redirect("/")
    if not clearance() >= 3:
        return redirect("/")

    if request.method == 'POST':
        chosen_transport = request.form.get('select_transport')
        chosen_transport = chosen_transport.strip("(")
        chosen_transport = chosen_transport.strip(")")
        chosen_transport = chosen_transport.split(", ")

    return render_template('delete_confirm.html', table_id=chosen_transport[0], name=str("Relocated " + chosen_transport[4].strip("'") + " to the " + chosen_transport[3].strip("'") + " at " + chosen_transport[2].strip("'") + " on the " + chosen_transport[1].strip("'")), type="log")


@app.route('/delete_log_confirm/<table_id>')
def delete_transport_confirm(table_id):
    if not is_logged_in():
        return redirect("/")
    if not clearance() >= 3:
        return redirect("/")
    con = connect_database(DATABASE)
    query = "DELETE FROM transport_log WHERE relocation_id=?"
    cur = con.cursor()
    cur.execute(query,(table_id, ))
    con.commit()
    con.close()
    return redirect('/transport')

@app.route('/dino_control', methods=['POST', 'GET'])
def render_dino_control():  # put application's code here
    if not is_logged_in():
        return redirect("/")
    if not clearance() >= 3:
        return redirect("/")
    con = connect_database(DATABASE)
    query_dinos = "SELECT * FROM dinosaurs WHERE clearance_required <= ?"
    cur = con.cursor()
    cur.execute(query_dinos, (clearance(),))
    dino_list = cur.fetchall()
    if request.method == 'POST':
        con = connect_database(DATABASE)
        species = request.form.get('species').strip()
        diet = request.form.get('select_diet').strip("()")
        location = request.form.get('place').strip()
        info = request.form.get('info')
        specimen = request.form.get('specimens').strip()
        image = request.form.get('image')
        chosen_clearance = request.form.get('select_clearance').strip("()")

        query_insert = "INSERT INTO dinosaurs (species, diet, location, information, living_specimens, image, clearance_required) VALUES (?, ?, ?, ?, ?, ?, ?)"
        cur = con.cursor()
        cur.execute(query_insert, (species, diet, location, info, specimen, image, chosen_clearance))
        con.commit()
        con.close()
        return redirect('/dino_control')
    return render_template('dino_control.html', logged_in=is_logged_in(), access_level=clearance(), list_of_dinosaurs=dino_list)


@app.route('/delete_dino', methods=['POST', 'GET'])
def delete_dino():
    if not is_logged_in():
        return redirect("/")
    if not clearance() >= 3:
        return redirect("/")

    if request.method == 'POST':
        chosen_dino = request.form.get('select_dino')
        chosen_dino = chosen_dino.strip("(")
        chosen_dino = chosen_dino.strip(")")
        chosen_dino = chosen_dino.split(", ")

    return render_template('delete_confirm.html', table_id=chosen_dino[0], name=chosen_dino[1].strip("'"), type="dinosaur")


@app.route('/delete_dinosaur_confirm/<table_id>')
def delete_dino_confirm(table_id):
    if not is_logged_in():
        return redirect("/")
    if not clearance() >= 3:
        return redirect("/")
    con = connect_database(DATABASE)
    query = "DELETE FROM dinosaurs WHERE dino_id=?"
    cur = con.cursor()
    cur.execute(query,(table_id, ))
    con.commit()
    con.close()
    return redirect('/dino_control')
