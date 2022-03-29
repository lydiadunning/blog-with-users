#from functools import wraps

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
# ckeditor = CKEditor(app)
# Bootstrap(app)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


##CONFIGURE TABLES

# class B(db.Model):
#     __tablename__ = "b"
#     id = db.Column(db.Integer, primary_key=True)
#     b = db.Column(db.String(250), nullable=False)
#     a_id = db.Column(db.Integer, db.ForeignKey('a.id'))
#     a = relationship("A", back_populates="b")
#
#
# class A(db.Model):
#     __tablename__ = "a"
#     id = db.Column(db.Integer, primary_key=True)
#     a = db.Column(db.String(250))
#     b = relationship("B", back_populates="a")

class Parent(db.Model):
    __tablename__ = 'parent'
    id = db.Column(db.Integer, primary_key=True)
    children = relationship("Child", back_populates="parent")

class Child(db.Model):
    __tablename__ = 'child'
    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('parent.id'))
    parent = relationship("Parent", back_populates="children")

db.create_all()

first_parent = Parent()
db.session.add(first_parent)
first_child = Child(parent=first_parent)
second_child = Child(parent=first_parent)
third_child = Child(parent=first_parent)
db.session.add(first_child)
db.session.add(second_child)
db.session.add(third_child)
db.session.commit()

print(first_child.id)



# def create_a(a_value):
#     new_a = A(a=a_value)
#     db.session.add(new_a)
#     db.session.commit()
#
# def create_b(b_value, a):
#     new_b = B(b=b_value, a_id=a.id)
#     db.session.add(new_b)
#     db.session.commit()
#
# first_a = create_a("10")
# first_b = create_b("first_b", first_a)
# second_a = create_a("5")
# second_b = create_b("second_b", second_a)
# third_a = create_a("1")
# third_b = create_b("third_b", third_a)






if __name__ == "__main__":
    # app.run(host='0.0.0.0', port=5000)
    app.run(debug=True)
