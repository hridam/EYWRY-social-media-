from ast import And
import pandas as pd
from sklearn.model_selection import train_test_split
import joblib
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from cmath import polar
import email
from lib2to3.pgen2.pgen import generate_grammar
from multiprocessing import connection
from telnetlib import LOGOUT
from flask import Flask, render_template, url_for, redirect, flash, request, session
import psycopg2 
import psycopg2.extras
import re
from werkzeug.security import generate_password_hash, check_password_hash
from textblob import TextBlob

data = pd.read_csv('google_play_store_apps_reviews_training.csv')

def preprocess_data(data):
    
    data = data.drop('package_name', axis=1)
    
    
    data['review'] = data['review'].str.strip().str.lower()
    return data
data = preprocess_data(data)

x = data['review']
y = data['polarity']
x, x_test, y, y_test = train_test_split(x, y, stratify=y, test_size=0.20, random_state=42)
# Vectorize text reviews to numbers
vec = CountVectorizer(stop_words='english')
x = vec.fit_transform(x).toarray()
x_test = vec.transform(x_test).toarray()

model = MultinomialNB()
model.fit(x, y)

print(model.score(x_test, y_test))


app = Flask(__name__)
app.secret_key = "hridam_dhimal"

DB_HOST = 'localhost'
DB_NAME = 'eywry'
DB_USER = 'postgres'
DB_PASS = '123456'

conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST) 
    

@app.route("/<password_rs>")
def index(password_rs):
    
    if 'loggedin' in session:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        s = "SELECT * FROM table_post ORDER BY id DESC"
        cur.execute(s)
        username = cur.fetchall()
        # User is loggedin show them the home page
        return render_template('index.html', email=session['email'], username=username, password_rs=password_rs)
    else:
        if 'id' in session:
            return redirect(url_for('index'))
        else :
    # User is not loggedin redirect to login page
            return redirect(url_for('login'))

@app.route('/add_record', methods=['POST', 'GET'])
def add_record():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'email' in request.form and 'password' in request.form :
        fullname = request.form['fullname']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        _hashed_password = generate_password_hash(password)


        #Check if account exists using MySQL
        cur.execute('SELECT * FROM user_info WHERE email = %s', (email,))
        account = cur.fetchone()
        print(account)
        # If account exists show error and validation checks
        if account:
            flash('Account already exists!')
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash('Invalid email address!')
        elif not re.match(r'[A-Za-z0-9]+', username):
            flash('Username must contain only characters and numbers!')
        elif not username or not password or not email:
            flash('Please fill out the form!')
        else:
            cur.execute("INSERT INTO user_info (full_name, user_name, email, password) VALUES(%s,%s,%s,%s)", (fullname, username, email, _hashed_password))
            conn.commit()
            flash('User Record is been recorded')
        return redirect(url_for('login'))


@app.route('/login_record', methods=['GET', 'POST'])
def login_record():
    cur=conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    if request.method == 'POST' and 'email' in request.form and 'password' in request.form :
        email = request.form['email']
        password = request.form['password']
        # print(password)

        cur.execute('SELECT * FROM user_info WHERE email = %s', (email,))
        account = cur.fetchone()

        if account:
            password_rs = account['password']
            # print(password_rs)

            if check_password_hash(password_rs, password):
                session['loggedin'] = True
                session['id'] = account['id']
                session['email'] = account['email']
                return redirect(url_for('index', password_rs=password_rs))
            else:
                if 'loggedin' in session:
                    return redirect(url_for("index", password_rs=password_rs))
        else:
            flash('Incorrect email/Password')

    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('email', None)
    return render_template('login.html')


@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('email', None)
   # Redirect to login page
   return redirect(url_for('login'))


@app.route('/post/<password_rs>', methods=['POST', 'GET'])
def post(password_rs):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if request.method == 'POST' and 'text' in request.form:
        text = request.form['text']
        ss = (model.predict(vec.transform([text])))
        if ss == [0]:
            print('no post')
        else:
            cur.execute(f"INSERT INTO table_post (post, password) VALUES(%s,%s)", (text, password_rs,))
            conn.commit()
            return redirect(url_for('index', password_rs = password_rs))
        return redirect(url_for('index', password_rs = password_rs))
        


@app.route('/your_post/<password_rs>')
def your_post(password_rs):
    if 'loggedin' in session:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        s = f"SELECT * FROM table_post where password = '{password_rs}'"
        cur.execute(s)
        username = cur.fetchall()
        # User is loggedin show them the home page
        return render_template('post.html', email=session['email'],username=username, password_rs=password_rs)

@app.route('/account/<password_rs>', methods = ['POST', 'GET'])
def account(password_rs):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # s = f"SELECT COUNT(post) FROM table_post WHERE password = '{password_rs}'" 
    cur.execute("SELECT COUNT(post) FROM table_post WHERE password = %s", (password_rs,))
    count = cur.fetchall()
    cur.execute("SELECT * FROM user_info WHERE password = %s", (password_rs,))
    datas = cur.fetchall()
    return render_template('account.html', count=count, datas=datas, password_rs=password_rs)
    

@app.route('/about/<password_rs>')
def about(password_rs):
    return render_template('about.html', password_rs=password_rs)


@app.route('/delete/<string:id>/<password_rs>', methods = ['POST', 'GET'])
def delete(id, password_rs):
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute('DELETE FROM table_post WHERE id= {0}'.format(id))
        conn.commit()
        flash('student removed Successfully')
        return redirect(url_for('your_post', password_rs = password_rs))

@app.route("/modal/<string:id>/<password_rs>", methods = ['POST', 'GET'])
def modal(id, password_rs):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute('SELECT * FROM table_post WHERE id= %s', (id,))
    data = cur.fetchall()
    print(data[0])
    return render_template("modal.html", id=id, password_rs=password_rs, post=data[0])


@app.route("/edit/<string:id>/<password_rs>", methods = ['POST', 'GET'])
def edit(id, password_rs):
    if request.method == 'POST':
        post = request.form['post']
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        sss = (model.predict(vec.transform([post])))
        if sss == [1]:
            cur.execute("UPDATE table_post SET post = %s WHERE id = %s", (post, id,)) 
            flash('post has been updated')
            conn.commit()
            print(post)
            return redirect(url_for('your_post', password_rs = password_rs))
        return redirect(url_for('your_post', password_rs = password_rs))
        
        

@app.route("/modal_username/<string:id>/<password_rs>", methods = ['POST', 'GET'])
def modal_username(id, password_rs):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute('SELECT * FROM user_info WHERE id= %s', (id,))
    data = cur.fetchall()
    print(data[0])
    return render_template("modal_username.html", id=id, password_rs=password_rs, user=data[0])


@app.route("/edit_username/<string:id>/<password_rs>", methods = ['POST', 'GET'])
def edit_username(id, password_rs):
    if request.method == 'POST':
        username = request.form['username']
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("UPDATE user_info SET user_name = %s WHERE id = %s", (username, id,)) 
        flash('post has been updated')
        conn.commit()
        print(username)
        return redirect(url_for('account', password_rs = password_rs))


@app.route("/modal_email/<string:id>/<password_rs>", methods = ['POST', 'GET'])
def modal_email(id, password_rs):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute('SELECT * FROM user_info WHERE id= %s', (id,))
    data = cur.fetchall()
    print(data[0])
    return render_template("modal_email.html", id=id, password_rs=password_rs, user=data[0])


@app.route("/edit_email/<string:id>/<password_rs>", methods = ['POST', 'GET'])
def edit_email(id, password_rs):
    if request.method == 'POST':
        email = request.form['email']
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("UPDATE user_info SET email = %s WHERE id = %s", (email, id,)) 
        flash('post has been updated')
        conn.commit()
        print(email)
        return redirect(url_for('account', password_rs = password_rs))

@app.route("/modal_password/<string:id>/<password_rs>", methods = ['POST', 'GET'])
def modal_password(id, password_rs):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute('SELECT * FROM user_info WHERE id= %s', (id,))
    data = cur.fetchall()
    print(data[0])
    return render_template("modal_password.html", id=id, password_rs=password_rs, user=data[0])


@app.route("/edit_password/<string:id>/<password_rs>", methods = ['POST', 'GET'])
def edit_password(id, password_rs):
    if request.method == 'POST' and 'oldpass' in request.form and 'newpass' in request.form and 'configpass' in request.form :
        old_password = request.form['oldpass']
        password = request.form['newpass']
        config_passqword = request.form['configpass']
        if password != config_passqword:
            flash("passowrd don't match")
            return redirect(url_for('account', password_rs = password_rs))
        password = generate_password_hash(password)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute('SELECT * FROM user_info WHERE id= %s', (id,))
        account = cur.fetchone()
        if account:
            passw = account['password']
            if check_password_hash(passw, old_password):
                cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                cur.execute("UPDATE user_info SET password = %s WHERE id = %s", (password, id,))
                flash('your password has been successfull updaetd')
            else:
                flash("old password didnt match")
                return redirect(url_for('account', password_rs = password_rs, passw=passw))
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("UPDATE table_post SET password= %s WHERE password = %s", (passw, password,))
            flash('updated')
            return redirect(url_for('logout'))


if __name__ == "__main__":
    app.run(debug=True)