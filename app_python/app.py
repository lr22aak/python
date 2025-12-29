from flask import Flask, render_template, flash, session, redirect, url_for, logging, request
from data import Articles
# from flask_mysqldb import MySQl
from wtforms import Form, StringField,TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt 
from functools import wraps

import mysql.connector

#config mysql
mydbs = mysql.connector.connect(
    host="localhost", 
    user="root", 
    passwd="", 
    database="python" )

mydb = mydbs.cursor()

app = Flask(__name__)

Articles = Articles()

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/articles')
def articles():
    cur = mydbs.cursor()
    cur.execute("SELECT * FROM articles")
    
    articles = cur.fetchall()

    # print(articles)
    if cur.rowcount > 0 :
        return render_template('articles.html', articles = articles)
    else: 
        msg = 'No Articles Found'
        return render_template('articles.html', msg = msg)
    cur.close()

# single article
@app.route('/article/<string:id>')
def article(id):
    cur = mydbs.cursor()
    cur.execute("SELECT * FROM articles WHERE id= %s", [id])
    
    art = cur.fetchone()

    cur.close()
    return render_template('article.html', art = art )

# Register form class
class RegisterForm(Form):
    name = StringField('Name',[validators.length(min=5,max=50) ])
    username = StringField('Username',[validators.length(min=4,max=20)])
    email = StringField('Email', [validators.length(min=6, max=40)])
    password = PasswordField('Password',[
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Password didnot match')
    ])
    confirm = PasswordField('Confirm Password')

# user register
@app.route('/register', methods=['GET','POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = form.password.data
        # password = sha256_crypt.encrypt(str(form.password.data))

        mydb = mydbs.cursor()
        # create insert
        mydb.execute("INSERT INTO registers(name,username,email,password) VALUES(%s, %s, %s, %s)", (name, username, email, password))

        # commit to db
        mydbs.commit()

        flash('you are now registered and can login','success')

        # close connection
        mydb.close()
        
        # return render_template('register.html')
        return redirect(url_for('login'))
    return render_template('register.html', form = form)

# user login
@app.route('/login',methods=['GET',"POST"])
def login():
    if request.method == 'POST':
        # get details
        Username = request.form['username']
        password_user = request.form['password']
        
        cur = mydbs.cursor(buffered=True)
        print(Username)
        cur.execute("SELECT * FROM registers WHERE username = %s", [Username])

        if cur.rowcount > 0:
            # get stored hash
            data = cur.fetchone()
            password = data[4]
            
            #compare passwords
            if password_user == password:
                # passed
                session['logged_in'] = True
                session['username'] = Username

                flash('you are now logged in','success')
                return redirect(url_for('dashboard'))
            else: 
                error = 'Invalid login'
                return render_template('login.html', error=error)
            cur.close()
        else: 
            print(Username)
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

# check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else: 
            flash('Unauthrorised, please Login', 'danger')
            return redirect(url_for('login'))
    return wrap

# logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out','success')
    return redirect(url_for('login'))

# dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    cur = mydbs.cursor()
    cur.execute("SELECT * FROM articles")
    
    articles = cur.fetchall()

    if cur.rowcount > 0 :
        return render_template('dashboard.html', articles = articles)
    else: 
        msg = 'No Articles Found'
        return render_template('dashboard.html', msg = msg)
    cur.close()
    

# Article form class
class ArticleForm(Form):
    tittle = StringField('Tittle',[validators.length(min=5,max=200) ])
    body = TextAreaField('Body',[validators.length(min=30)])

# Add Article
@app.route('/add_article', methods=['GET','POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        tittle = form.tittle.data
        body = form.body.data
        # session['username'] = "kumar"
        #execute
        mydb = mydbs.cursor()

        mydb.execute("INSERT INTO articles(tittle, body, author) VALUES(%s, %s, %s)",(tittle,body,session['username']))

        #commit db
        mydbs.commit()

        #close
        mydb.close()

        flash('Article Created', 'success')

        return redirect(url_for('dashboard'))
    
    return render_template('add_article.html', form=form)

# edit Article
@app.route('/edit_article/<string:id>', methods=['GET','POST'])
@is_logged_in
def edit_article(id):
    cur = mydbs.cursor()
    #get article id
    cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()

    form = ArticleForm(request.form)

    # populate article from fields
    form.tittle.data = article[1]
    form.body.data = article[3]

    if request.method == 'POST' and form.validate():
        tittle = request.form['tittle']
        body = request.form['body']
        
        #execute
        mydb.execute("UPDATE articles SET tittle=%s, body=%s WHERE id=%s ",(tittle,body,id))

        #commit db
        mydbs.commit()

        #close
        mydb.close()

        flash('Article Upadted', 'success')

        return redirect(url_for('dashboard'))
    
    return render_template('edit_article.html', form=form)

# delet article
@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    cur = mydbs.cursor()
    #execute
    cur.execute("DELETE FROM articles WHERE id = %s", [id])
    #commit db
    mydbs.commit()

    #close
    cur.close()
    flash('Article Deleted', 'success')

    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True) 
