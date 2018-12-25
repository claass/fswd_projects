# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import urllib
import webapp2
import jinja2
import hmac
import random
import re
import hashlib
from string import letters
from google.appengine.ext import ndb

# Initializing Jinja

template_dir = os.path.join(os.path.dirname(__file__), 'templates')

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(template_dir),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

# Initializing database model


class BlogEntry(ndb.Model):
    date = ndb.DateTimeProperty(auto_now_add=True)
    last_modified = ndb.DateTimeProperty(auto_now=True)
    subject = ndb.StringProperty(required=True)
    content = ndb.TextProperty(required=True)
    author = ndb.StringProperty(required=True)

    def render(self):
        self._render_text = self.content.replace('\n', '<br>')
        return self._render_text


class Comment(ndb.Model):
    date = ndb.DateTimeProperty(auto_now_add=True)
    author = ndb.StringProperty(required=True)
    content = ndb.TextProperty(required=True)
    last_modified = ndb.DateTimeProperty(auto_now=True)

    @classmethod
    def query_entry_comments(cls, entry_key):
        return cls.query(ancestor=entry_key).order(cls.date).fetch()


class Like(ndb.Model):
    username = ndb.StringProperty(required=True)
    last_modified = ndb.DateTimeProperty(auto_now=True)


class User(ndb.Model):
    create_time = ndb.DateTimeProperty(auto_now_add=True)
    username = ndb.StringProperty(required=True)
    email = ndb.StringProperty(required=False)
    hashed_pw = ndb.StringProperty(required=True)

    @classmethod
    def get_by_name(cls, username):
        users_matching = User.query(User.username == username)
        for user in users_matching:
            return user

    @classmethod
    def get_by_user_id(cls, user_id):
        user = ndb.Key('User', int(user_id)).get()
        return user

    @classmethod
    def login_retrieve_user(csl, username, password):
        user = User.get_by_name(username)
        if user and valid_pw(username, password, user.hashed_pw):
            return user


# class Comment(ndb.Model):


# Supporting functions
# Hashing functions

SECRET = 'm2H215W1Ptq8w7fNJ1PkY16ef48cU93Q'


def make_secure_val(val):
    return '%s|%s' % (val, hmac.new(SECRET, val).hexdigest())


def chec_secure_val(secure_val):
    val = secure_val.split('|')[0]
    if secure_val == make_secure_val(val):
        return val


def make_salt(length=5):
    return ''.join(random.choice(letters) for x in xrange(length))


def make_pw_hash(username, pw, salt=None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(username+pw+salt).hexdigest()
    return '%s,%s' % (salt, h)


def valid_pw(username, pw, hashed_pw):
    salt = hashed_pw.split(',')[0]
    return hashed_pw == make_pw_hash(username, pw, salt)


# Signup functions (referenced from course material)
USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")


def valid_username(username):
    return username and USER_RE.match(username)

PASS_RE = re.compile(r"^.{3,20}$")


def valid_password(password):
    return password and PASS_RE.match(password)

EMAIL_RE = re.compile(r'^[\S]+@[\S]+\.[\S]+$')


def valid_email(email):
    return not email or EMAIL_RE.match(email)

# Main Handler class


class Handler(webapp2.RequestHandler):
    # Render helper functions for jinja
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = JINJA_ENVIRONMENT.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        user = self.user
        self.write(self.render_str(template, user=user, **kw))

    # Set an read cookie functions
    def set_secure_cookie(self, name, val):
        cookie_val = make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; Path=/' % (name, cookie_val))

    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        if cookie_val and chec_secure_val(cookie_val):
            return cookie_val.split('|')[0]

    # Login/Logout fucntions
    def login_set_cookie(self, user):
        self.set_secure_cookie('user_id', str(user.key.id()))

    def logout(self, user):
        self.response.headers.add_header(
            'Set-Cookie',
            'user_id= ;Path=/')

    # Define initialize function to check for login status at any point
    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        user_id = self.read_secure_cookie('user_id')
        self.user = user_id and User.get_by_user_id(user_id)


# Frontpage handler


class FrontPage(Handler):
    def get(self):
        entries = ndb.gql('SELECT * FROM BlogEntry ORDER BY date DESC')
        # entries = BlogEntry.query()
        self.render("frontpage.html", entries=entries)


# NewPost handler


class NewEntry(Handler):
    def get(self):
        if self.user:
            self.render('newpost.html')
        else:
            self.render('error.html', error='Please login to write a new entry')

    def post(self, **kw):
        if self.user:
            subject = self.request.get("subject")
            content = self.request.get("content")

            if self.request.get("button") == "Submit":

                if subject and content:
                    post = BlogEntry(
                        author=self.user.username,
                        subject=subject,
                        content=content)
                    post.put()
                    self.redirect('/post/%s' % str(post.key.id()))

                else:
                    error = 'Please enter title and content before submitting.'
                    self.render(
                        "newpost.html",
                        error=error,
                        content=content,
                        subject=subject)
            else:
                self.redirect('/')
        else:
            self.render('error.html', error='Please login to write a new entry')


# Permalink handler


class PermaLink(Handler):
    #TODO split comment and like handlers similar to edit/delete handlers
    #TODO Add custom 404 page
    
    def get(self, entry_id, comment_error=''):
        entry = ndb.Key('BlogEntry', int(entry_id)).get()
        if entry:
            try:
                comments = Comment.query(ancestor=entry.key).fetch()
            except:
                comments = []
            total_likes = str(len(Like.query(ancestor=entry.key).fetch()))
            user_like = None
            if self.user:
                user_like = Like.query(
                    Like.username == self.user.username,
                    ancestor=entry.key).get()

            self.render(
                "permalink.html",
                entry=entry,
                comments=comments,
                user_like=user_like,
                total_likes=total_likes,
                comment_error=comment_error)
        else:
            self.error(404)

    def post(self, entry_id):
        entry = ndb.Key('BlogEntry', int(entry_id)).get()
        like = Like.query(
                    Like.username == self.user.username,
                    ancestor=entry.key).get()

        if self.user and entry:
            #Comment actions by any user
            if self.request.get('comment_post') == 'Submit':
                print "going down comment path"
                content = self.request.get('content')
                if content:
                    author = self.user.username
                    new_comment = Comment(
                        content=content,
                        author=author,
                        parent=entry.key)
                    new_comment.put()
                    self.get(entry_id) 
                else:
                    self.get(entry_id, comment_error='Please enter a comment.')

            #Unlike action by any user
            if self.request.get('like') and like:
                print "going down unlike path"
                like.key.delete()
                self.get(entry_id)

            #Like action by any user
            if self.request.get('like') and not like:
                print "going down like path"
                like = Like(username=self.user.username, parent=entry.key)
                like.put()
                self.get(entry_id)

            # Actions by entry author
            if self.request.get('entry'):
                self.redirect('/post/%s/edit' % entry_id)

        else:
            self.render('error.html', error='Please login to contribute.')


# Edit handler for entries


class EditEntry(Handler):
    def get(self, entry_id):
        item = ndb.Key('BlogEntry', int(entry_id)).get()

        if self.user and item:
            if self.user.username == item.author:
                self.render("edit.html", item=item)
            else:
                error = 'Authentication Error: Only the author can edit posts.'
                self.render(
                    "error.html",
                    error=error)
        else:
            self.render('error.html', error='Please login to edit.')

    def post(self, entry_id):
        #TODO: Split edit & delete into seperate handlers
        item = ndb.Key('BlogEntry', int(entry_id)).get()

        if self.user and item:
            if self.user.username == item.author:
                if self.request.get('edit') == 'Submit':
                    item.subject = self.request.get('subject')
                    item.content = self.request.get('content')
                    item.put()
                    self.redirect('/post/%s' % str(entry_id))

                if self.request.get('delete') == 'Delete':
                    item.key.delete()
                    self.redirect('/')

                if self.request.get('edit') == 'Cancel':
                    self.redirect('/post/%s' % str(entry_id))
            else:
                error = 'Authentication Error: Only the author can edit posts.'
                self.render(
                    "error.html",
                    error=error)
        else:
            self.render('error.html', error='Please login to edit.')


# Edit handler for comments


class EditComment(Handler):
    def get(self, entry_id, comment_id):
        parent_key = ndb.Key('BlogEntry', int(entry_id))
        item = Comment.get_by_id(int(comment_id), parent=parent_key)

        if self.user and item:
            if self.user.username == item.author:
                self.render("edit.html", item=item)
            else:
                error = 'Authentication Error: Only author can edit comments.'
                self.render(
                    "error.html",
                    error=error)
        else:
            self.render('error.html', error='Please login to edit.')

    def post(self, entry_id, comment_id):
        parent_key = ndb.Key('BlogEntry', int(entry_id))
        item = Comment.get_by_id(int(comment_id), parent=parent_key)

        if self.user and item:
            if self.user.username == item.author:
                if self.request.get('edit') == 'Submit':
                    item.content = self.request.get('content')
                    item.put()
                    self.redirect('/post/%s' % str(entry_id))

                if self.request.get('delete') == 'Delete':
                    item.key.delete()
                    self.redirect('/post/%s' % str(entry_id))

                if self.request.get('edit') == 'Cancel':
                    self.redirect('/post/%s' % str(entry_id))
            else:
                error = 'Authentication Error: Only author can edit comments.'
                self.render(
                    "error.html",
                    error=error)

        else:
            self.render('error.html', error='Please login to edit')


# Signup Handler


class Signup(Handler):
    def get(self):
        if self.user:
            self.redirect('/')
        else:
            self.render("signup.html")

    def post(self):
        if not self.user:
            if self.request.get('button') == "Cancel":
                self.redirect('/')

            else:
                have_error = False
                username = self.request.get("username")
                password = self.request.get("password")
                password_resub = self.request.get("password_resub")
                email = self.request.get("email")

                params = dict(username=username, email=email)

                if not valid_username(username):
                    have_error = True
                    params['error_name'] = "This is not a valid username"

                if not valid_password(password):
                    have_error = True
                    params['error_pw'] = "This is not a valid password"

                if password != password_resub:
                    have_error = True
                    params['error_pwc'] = "Password does not match"

                if not valid_email(email):
                    have_error = True
                    params['error_email'] = "This is not a valid email"

                if User.get_by_name(username):
                    have_error = True
                    params['error_name'] = "This username is already taken"

                if have_error is True:
                    self.render('signup.html', **params)

                else:
                    new_user = User(
                        username=username,
                        email=email,
                        hashed_pw=make_pw_hash(username, password))
                    new_user.put()
                    self.login_set_cookie(new_user)
                    self.redirect('/')
        else:
            self.redirect('/')


# Login handler

class Login(Handler):
    def get(self):
        if not self.user:
            self.render("login.html")
        else:
            self.render("error.html", error="Please log out before logging in.")

    def post(self):
        if not self.user:
            if self.request.get("button") == "Cancel":
                self.redirect('/')

            else:
                username = self.request.get('username')
                password = self.request.get('password')
                user = User.login_retrieve_user(username, password)

                if user:
                    self.login_set_cookie(user)
                    self.render("welcome.html", username=username)

                else:
                    login_error = "Invalid login credentials"
                    self.render('/login.html', login_error=login_error)
        else:
            self.render("error.html", error="Please log out before logging in.")

# Logout handler


class Logout(Handler):
    def get(self):
        self.logout(user=self.user)
        self.render("goodbye.html")


# Initializing app


app = webapp2.WSGIApplication([
    ('/', FrontPage),
    ('/newpost', NewEntry),
    ('/post/([0-9]+)', PermaLink),
    ('/post/([0-9]+)/edit', EditEntry),
    ('/post/([0-9]+)/([0-9]+)/edit', EditComment),
    ('/signup', Signup),
    ('/login', Login),
    ('/logout', Logout),
], debug=True)
