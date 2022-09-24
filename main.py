from flask import Flask,render_template,request,session,redirect
from flask_sqlalchemy import SQLAlchemy 
from werkzeug.utils import secure_filename
from flask_mail import Mail
import json
from datetime import datetime
import os
import math

with open("config.json","r") as c:
    params = json.load(c)["params"]

local_server = True

app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = params['upload_location']

#  FOR MAIL 
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD = params['gmail-pass'],
    )

mail = Mail(app)

if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']
db = SQLAlchemy(app)


class Contacts(db.Model):
    ''' sno,name,phno,email,msg,date '''
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    phno = db.Column(db.String(12), nullable=False)
    email = db.Column(db.String(20),nullable=False)
    message = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)

class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(20), nullable = False)
    tagline = db.Column(db.String(20), nullable = False)
    slug = db.Column(db.String(20), nullable = False)
    content = db.Column(db.String(20), nullable = False)
    imgfile = db.Column(db.String(12), nullable = True)
    date = db.Column(db.String(20), nullable = True)


@app.route("/")  
def home():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['no_of_posts']))
    page = request.args.get('page')
    if (not str(page).isnumeric()): 
        page = 1
    page = int(page)
    posts = posts[(page-1)*int(params['no_of_posts']) : (page-1)*int(params['no_of_posts']) + int(params['no_of_posts'])]
    if page == 1:
        prev = "#"
        next = "/?page=" + str(page+1)
    elif page == last:
        prev = "/?page=" + str(page-1)
        next = "#"
    else:
        prev = "/?page=" + str(page-1)
        next = "/?page=" + str(page+1)
    return render_template("1index 2.html",params = params,posts = posts,prev = prev,next = next)


@app.route('/login', methods = ['GET','POST'])
def log():
    if ('user' in session and session['user'] == params['admin_user']):
        posts = Posts.query.all()
        return render_template('1dashboard.html',params = params,posts= posts)

    if request.method == 'POST':
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if (username == params['admin_user'] and userpass == params['admin_pass']):
            session['user'] = username
            posts = Posts.query.all()
            return render_template('1dashboard.html',params = params,post = posts)
    return render_template('1log.html',params = params)


@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/')


@app.route('/exit')
def exe():
    return redirect("/")


@app.route('/delete/<string:sno>',methods = ['GET','POST'])
def delete(sno):
    if('user' in session and session['user'] == params['admin_user']):
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/login')


@app.route("/edit/<string:sno>",methods =['GET','POST'] )
def edit_post(sno):
    if ('user' in session and session['user'] == params['admin_user']): 
        if request.method == 'POST':
            title = request.form.get('title')
            subheading = request.form.get("tline")
            slug = request.form.get('slug')
            content = request.form.get('content')
            imagefile = request.form.get('image')
            date = datetime.now()
            if sno == '0':
                post = Posts(title = title,tagline = subheading, slug = slug, content = content, imgfile = imagefile, date = date)
                db.session.add(post)
                try :
                    db.session.commit()
                except:
                    db.session.rollback()
            else:
                post = Posts.query.filter_by(sno = sno).first()
                post.title = title
                post.tagline = subheading
                post.slug = slug
                post.content = content
                post.imgfile = imagefile
                post.date = date
                try :
                    db.session.commit()
                except:
                    db.session.rollback()
                return redirect("/login")
        post = Posts.query.filter_by(sno = sno).first()
        return render_template("1edit.html",params = params, post = post,sno = sno)


@app.route("/uploader",methods = ['GET','POST'])
def upload():
    if('user' in session and session['user'] == params['admin_user'] ):
        if (request.method == "POST"):
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename))) 
            return "uploaded successefully"


@app.route("/about")
def about():
    return render_template("1about.html",params = params)


@app.route("/post/<string:post_slug>",methods = ['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug = post_slug).first()
    return render_template("1post.html",params = params, post = post)


@app.route("/contact", methods = ['GET' , 'POST'])
def contact(): 
    if (request.method == 'POST'):
        ''' add entry to data base'''
        name = request.form.get('name')
        email = request.form.get('email')
        phone_no = request.form.get('phno')
        msg = request.form.get('msg')
        entry = Contacts(name = name,phno = phone_no,email = email,message = msg,date = datetime.now())
        db.session.add(entry)
        db.session.commit()
        # MAIL NOTIFICAIONS 
        # mail.send_message("New message from blog",
        #                     sender = 'email',
        #                     recipients = [params['gmail-user']],
        #                     body = msg +"\n"+ phone_no
        #                     )
        
    return render_template("1contact.html",params = params)

if __name__ == "__main__":
    app.run(debug=True)


