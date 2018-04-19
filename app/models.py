from flask import current_app
from app import db, login
from datetime import datetime
from time import time
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5
import jwt

followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)
# followers is a so-called association table
# this means that each row in the table accounts for one follower - followed relationship
# if user1 is a follower of user2, then user2 is being followed by user1
# and there is a single row in the followers table to document this

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic') # u.posts, p.author(s)
    about_me = db.Column(db.String(140))
    # last_seen = db.Column(db.String(60)) # default=datetime.utcnow
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    followed = db.relationship('User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id), # LEFT # why isn't it just followers.follower_id ?
        secondaryjoin=(followers.c.followed_id == id), # RIGHT
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest() # .encode('utf-8') converts email string to bytes
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user) # built-in list functionality

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user) # built-in list functionality

    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0 # filter ==, filter_by =

    def followed_posts(self):
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
                followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id = self.id) # it's not filter(Post.user_id == self.id)
        return followed.union(own).order_by(Post.timestamp.desc())
    # this is a right merge, since the query result only contains posts whose author is being followed by at least one user
    # if the author is followed by multiple users, each of the author's posts is returned multiple times

    def get_reset_password_token(self, expires_in=600): # expires_in units are seconds
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8') # since jwt.encode returns a bytes expression

    @staticmethod # probably since this doesn't reference self
    def verify_reset_password_token(token):
        try: # there is no conditional, ALWAYS try this
            id = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
            # invertible, unlike password hash
            # can multiple algorithms be used together?
        except: # if validation fails
            return # return None
        return User.query.get(id)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow) # datetime.utcnow, NOT datetime.utcnow()
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    language = db.Column(db.String(5))

    def __repr__(self):
        return '<Post {}>'.format(self.body)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))
# UserMixin includes get_id(), which generates unique identifier (as string) for a given user