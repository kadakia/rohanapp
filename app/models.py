from flask import current_app
from app import db, login
from app.search import add_to_index, remove_from_index, query_index
from datetime import datetime
from time import time
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5
import jwt
import json


class SearchableMixin(object):
    @classmethod # as opposed to instance method
    def search(cls, expression, page, per_page): # cls.search, not self.search
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total == 0:
            return cls.query.filter_by(id=0), 0
        when = [] # this list must be called "when"
        for i in range(len(ids)):
            when.append((ids[i], i))
        return cls.query.filter(cls.id.in_(ids)).order_by(
            db.case(when, value=cls.id)), total

    @classmethod
    def before_commit(cls, session):
        session._changes = {
            'add': [obj for obj in session.new if isinstance(obj, cls)],
            'update': [obj for obj in session.dirty if isinstance(obj, cls)], # there is no db.session.update()
            'delete': [obj for obj in session.deleted if isinstance(obj, cls)]
        }

    @classmethod
    def after_commit(cls, session):
        for obj in session._changes['add']:
            add_to_index(cls.__tablename__, obj)
        for obj in session._changes['update']: # modified post overwrites original post in Elasticsearch db
            add_to_index(cls.__tablename__, obj)
        for obj in session._changes['delete']:
            remove_from_index(cls.__tablename__, obj)
        session._changes = None # resets the dictionary - which survived the commit - to None
        # functionality for editing, deleting posts doesn't yet exist

    @classmethod
    def reindex(cls):
        for obj in cls.query: # to index posts ALREADY in the SQLAlchemy db
            add_to_index(cls.__tablename__, obj)

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
    messages_sent = db.relationship('Message', foreign_keys='Message.sender_id', # need to specify which foreign key
                                    backref='author', lazy='dynamic') # what else could lazy= be?
    messages_received = db.relationship('Message', foreign_keys='Message.recipient_id',
                                        backref='recipient', lazy='dynamic')
    last_message_read_time = db.Column(db.DateTime)
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')

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

    def new_messages(self):
        # last_read_time = self.last_message_read_time or datetime(1900, 1, 1) # latter iff former is empty
        # return Message.query.filter_by(recipient=self).filter(
        #    Message.timestamp > last_read_time).count()
        new_messages = 0
        for user in User.query.all():
            new_messages += self.new_messages_from_other(user)
        return new_messages

    def new_messages_from_other(self, other):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1) # latter iff former is empty
        return Message.query.filter_by(recipient=self).filter_by(author=other).filter(
            Message.timestamp > last_read_time).count()

    # def last_read_time_other(self, other):

    def all_messages_with_other(self, other):
        received = Message.query.filter_by(author=other).filter_by(recipient=self)
        sent = Message.query.filter_by(author=self).filter_by(recipient=other)
        return received.union(sent).order_by(Message.timestamp.desc())

    def messages_from_other(self, other):
        return Message.query.filter_by(author=other).filter_by(recipient=self).count()

    def add_notification(self, name, data):
        self.notifications.filter_by(name=name).delete() # not db.session.delete
        n = Notification(name=name, payload_json=json.dumps(data), user=self)
        db.session.add(n)
        return n # why both add n and return n ?

class Post(SearchableMixin, db.Model):
    __searchable__ = ['body']
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow) # datetime.utcnow, NOT datetime.utcnow()
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    language = db.Column(db.String(5))

    def __repr__(self):
        return '<Post {}>'.format(self.body)

db.event.listen(db.session, 'before_commit', Post.before_commit) # purpose of middle component ?
db.event.listen(db.session, 'after_commit', Post.after_commit)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return '<Message {}>'.format(self.body)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True) # name == 'unread_message_count'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.Float, index=True, default=time) # time() is a float, not a datetime object!
    payload_json = db.Column(db.Text)

    def get_data(self):
        return json.loads(str(self.payload_json)) # since json.dumps returns a string, why is str() necessary?

    # def __repr__(self):
    #    return '<Notification {}>'.format(self.id)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))
# UserMixin includes get_id(), which generates unique identifier (as string) for a given user