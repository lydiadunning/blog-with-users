from functools import wraps

from flask import Flask, render_template, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
from flask_gravatar import Gravatar
import dotenv
import os

dotenv.load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("secret_key")
ckeditor = CKEditor(app)
Bootstrap(app)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL",  "sqlite:///blog.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


##CONFIGURE TABLES

class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    blog_posts = relationship("BlogPost", back_populates="author")
    comments = relationship("BlogComment", back_populates="author")

# class Parent(db.Model):
#     __tablename__ = 'parent'
#     id = db.Column(db.Integer, primary_key=True)
#     children = relationship("Child", back_populates="parent")
#
# class Child(db.Model):
#     __tablename__ = 'child'
#     id = db.Column(db.Integer, primary_key=True)
#     parent_id = db.Column(db.Integer, db.ForeignKey('parent.id'))
#     parent = relationship("Parent", back_populates="children")

class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    author = relationship("User", back_populates="blog_posts")
    comments = relationship("BlogComment", back_populates="blog_post")

class BlogComment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.String(250), nullable=False)
    blog_post_id = db.Column(db.Integer, db.ForeignKey('blog_posts.id'))
    blog_post = relationship("BlogPost", back_populates="comments")
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    author = relationship("User", back_populates="comments")


db.create_all()

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


def admin_only(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if current_user.is_authenticated:
            if current_user.id == 1:
                return function(*args, **kwargs)
            else:
                return abort(403)
        else:
            return abort(403)
    wrapper.__name__ = function.__name__
    return wrapper


#CREATE GRAVATARS
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)


@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts, current_user=current_user)


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if not User.query.filter_by(email=form.email.data).first():
            salty_password_hash = generate_password_hash(form.password.data,
                                                         method='pbkdf2:sha256',
                                                         salt_length=8)
            new_user = User(
                name=form.name.data,
                email=form.email.data,
                password=salty_password_hash
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for("get_all_posts"))
        else:
            flash("That email already has an account.")
            return redirect(url_for("login"))
    return render_template("register.html", form=form, current_user=current_user)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user_email = form.email.data
        user = User.query.filter_by(email=user_email).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('get_all_posts'))
            else:
                flash("That password is not correct")
                return redirect(url_for("login"))
        else:
            flash("There is no user with that email address.")
            return redirect(url_for("login"))
    return render_template("login.html", form=form, current_user=current_user)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    requested_post = BlogPost.query.get(post_id)
    form = CommentForm()
    if form.validate_on_submit():
        if current_user.is_authenticated:
            new_comment = BlogComment(
                comment=form.comment.data,
                author=current_user,
                blog_post=requested_post
            )
            db.session.add(new_comment)
            db.session.commit()
        else:
            return redirect(url_for("login"))
    return render_template("post.html", post=requested_post, current_user=current_user, form=form, gravatar=gravatar)


@app.route("/about")
def about():
    return render_template("about.html", current_user=current_user)


@app.route("/contact")
def contact():
    return render_template("contact.html", current_user=current_user)


@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y"),
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form, current_user=current_user)


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = current_user
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form, current_user=current_user)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
    #app.run(debug=True)
