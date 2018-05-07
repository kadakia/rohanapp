from flask import render_template, flash, redirect, url_for, request, g, jsonify, current_app
from flask_login import current_user, login_required
from flask_babel import _, get_locale
from app import db
from app.main.forms import EditProfileForm, PostForm, SearchForm, MessageForm
from app.models import User, Post, Message, Notification
from app.translate import translate
from datetime import datetime
from guess_language import guess_language
from app.main import bp
from sqlalchemy import func, and_

# VIEW functions

@bp.route('/', methods = ['GET', 'POST'])
@bp.route('/index', methods = ['GET', 'POST'])
@login_required # built-in flash message: "Please log in to access this page."
def index():
    form = PostForm()
    if form.validate_on_submit():
        language = guess_language(form.post.data)
        if language == 'UNKNOWN' or len(language) > 5:
            language = ''
        post = Post(body=form.post.data, author=current_user, language=language)
        db.session.add(post)
        db.session.commit()
        flash(_('Your post is now live!'))
        return redirect(url_for('main.index'))
    # user = {'username': 'Rohan'}
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.index', page=posts.next_num) if posts.has_next else None
    # even though page isn't referenced in the URL directly, unlike <username>
    prev_url = url_for('main.index', page=posts.prev_num) if posts.has_prev else None
    if posts.total % current_app.config['POSTS_PER_PAGE'] == 0:
        last_page = posts.total // current_app.config['POSTS_PER_PAGE']
    else:
        last_page = posts.total // current_app.config['POSTS_PER_PAGE'] + 1
    last_url = url_for('main.index', page=last_page)
    return render_template('index.html', title = 'RohanApp - Home', posts = posts.items, form = form,
                            next_url = next_url, prev_url = prev_url, last_url = last_url)
    # no subdirectory for "main" templates

@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.user', username=user.username, page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.user', username=user.username, page=posts.prev_num) if posts.has_prev else None
    if posts.total % current_app.config['POSTS_PER_PAGE'] == 0:
        last_page = posts.total // current_app.config['POSTS_PER_PAGE']
    else:
        last_page = posts.total // current_app.config['POSTS_PER_PAGE'] + 1
    last_url = url_for('main.user', username=user.username, page=last_page)
    return render_template('user.html', title = user.username, user = user, posts = posts.items,
                            next_url = next_url, prev_url = prev_url, last_url = last_url)

@bp.before_app_request # executed just before any view function
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow() # .strftime('%m/%d/%Y %I:%M:%S %p')
        # db.session.add()
        db.session.commit()
        g.search_form = SearchForm()
        # under .is_authenticated, so search form appears iff logged in
        # need this form object to persist until it can be rendered at the end of the request
        # don't need to include 'form = g.search_form' in all render_template calls
    g.locale = str(get_locale())

@bp.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('main.explore')) # shouldn't empty search just do nothing ?
    # never: if g.search_form.validate():
    page = request.args.get('page', 1, type=int)
    posts, total = Post.search(g.search_form.q.data, page, current_app.config['POSTS_PER_PAGE'])
    next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1) \
        if total > page * current_app.config['POSTS_PER_PAGE'] else None # does order of q= and page= matter?
    prev_url = url_for('main.search', q=g.search_form.q.data, page=page - 1) \
        if page > 1 else None # can't use .next_num, .has_next, .prev_num, .has_prev !
    return render_template('search.html', title='Search', total=total, posts=posts, # why not posts.items ?!
                           next_url=next_url, prev_url=prev_url)

# how to enable searching for exact phrases

@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.edit_profile')) # Shouldn't we redirect to the user's updated profile?
    elif request.method == 'GET':
        form.username.data = current_user.username # fields pre-populated with current data
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title = 'Edit Profile', form = form)

@bp.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username)) # or 'User {} not found.' %s username
        return redirect(url_for('main.index'))
    if user == current_user:
        flash('You cannot follow yourself!')
        return redirect(url_for('main.user', username=username))
    if current_user.is_following(user):
        flash('You are already following {}.'.format(username))
        return redirect(url_for('main.user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('You are now following {}!'.format(username))
    return redirect(url_for('main.user', username=username))

@bp.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('main.index'))
    if user == current_user:
        flash('You cannot unfollow yourself!')
        return redirect(url_for('main.user', username=username))
    if not current_user.is_following(user):
        flash('You are not following {}.'.format(username))
        return redirect(url_for('main.user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('You are no longer following {}.'.format(username))
    return redirect(url_for('main.user', username=username))

@bp.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int) # "page" as opposed to "next" in URL
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False) # False means return empty if out of range, not 404
    next_url = url_for('main.explore', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.explore', page=posts.prev_num) if posts.has_prev else None
    if posts.total % current_app.config['POSTS_PER_PAGE'] == 0:
        last_page = posts.total // current_app.config['POSTS_PER_PAGE']
    else:
        last_page = posts.total // current_app.config['POSTS_PER_PAGE'] + 1
    last_url = url_for('main.explore', page=last_page)
    return render_template('explore.html', title='Explore', posts=posts.items, next_url=next_url, prev_url=prev_url, last_url=last_url)

@bp.route('/translate', methods=['POST']) # no form to GET
@login_required
def translate_text():
    return jsonify({'text': translate(request.form['text'], request.form['source_language'], request.form['dest_language'])}) # not request.args.form

@bp.route('/user/<username>/popup')
@login_required
def user_popup(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user_popup.html', user=user)

@bp.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    user = User.query.filter_by(username=recipient).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        language = guess_language(form.message.data)
        if language == 'UNKNOWN' or len(language) > 5:
            language = ''
        msg = Message(author=current_user, recipient=user, body=form.message.data, language=language)
        db.session.add(msg)
        user.add_notification('unread_message_count', user.new_messages())
        db.session.commit()
        flash('Your message has been sent.')
        return redirect(url_for('main.user', username=recipient)) # redirect (when and) only when form is successfully submitted
    return render_template('send_message.html', title='Send Message',
                           form=form, user=user)

@bp.route('/messages')
@login_required
def messages():
    current_user.last_message_read_time = datetime.utcnow()
    current_user.add_notification('unread_message_count', current_user.new_messages())
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    sub = db.session.query(func.max(Message.timestamp).label("max_stamp")).filter(
        Message.recipient == current_user).group_by(Message.sender_id).subquery()
    messages = current_user.messages_received.join(sub, and_(Message.timestamp == sub.c.max_stamp)).order_by(
        Message.timestamp.desc()).paginate(
            page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.messages', page=messages.next_num) if messages.has_next else None
    prev_url = url_for('main.messages', page=messages.prev_num) if messages.has_prev else None
    if messages.total % current_app.config['POSTS_PER_PAGE'] == 0:
        last_page = messages.total // current_app.config['POSTS_PER_PAGE']
    else:
        last_page = messages.total // current_app.config['POSTS_PER_PAGE'] + 1
    last_url = url_for('main.messages', page=last_page)
    return render_template('messages.html', messages=messages.items,
                           next_url=next_url, prev_url=prev_url, title='Messages', last_url=last_url)

@bp.route('/messages/sent')
@login_required
def sent_messages():
    page = request.args.get('page', 1, type=int)
    sub = db.session.query(func.max(Message.timestamp).label("max_stamp")).filter(
        Message.author == current_user).group_by(Message.recipient_id).subquery()
    sent_messages = current_user.messages_sent.join(sub, and_(Message.timestamp == sub.c.max_stamp)).order_by(
        Message.timestamp.desc()).paginate(
            page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.sent_messages', page=sent_messages.next_num) if sent_messages.has_next else None
    prev_url = url_for('main.sent_messages', page=sent_messages.prev_num) if sent_messages.has_prev else None
    if sent_messages.total % current_app.config['POSTS_PER_PAGE'] == 0:
        last_page = sent_messages.total // current_app.config['POSTS_PER_PAGE']
    else:
        last_page = sent_messages.total // current_app.config['POSTS_PER_PAGE'] + 1
    last_url = url_for('main.sent_messages', page=last_page)
    return render_template('messages_sent.html', sent_messages=sent_messages.items,
                           next_url=next_url, prev_url=prev_url, title='Messages Sent', last_url=last_url)

@bp.route('/messages/<other>', methods=['GET', 'POST'])
@login_required
def conversation(other):
    user = User.query.filter_by(username=other).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        language = guess_language(form.message.data)
        if language == 'UNKNOWN' or len(language) > 5:
            language = ''
        msg = Message(author=current_user, recipient=user, body=form.message.data, language=language)
        db.session.add(msg)
        user.add_notification('unread_message_count', user.new_messages())
        db.session.commit()
        flash('Your message has been sent.')
        return redirect(url_for('main.conversation', other=other))
    page = request.args.get('page', 1, type=int)
    conversation = current_user.all_messages_with_other(user).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.conversation', page=conversation.next_num, other=other) if conversation.has_next else None
    prev_url = url_for('main.conversation', page=conversation.prev_num, other=other) if conversation.has_prev else None
    if conversation.total % current_app.config['POSTS_PER_PAGE'] == 0:
        last_page = conversation.total // current_app.config['POSTS_PER_PAGE']
    else:
        last_page = conversation.total // current_app.config['POSTS_PER_PAGE'] + 1
    last_url = url_for('main.conversation', page=last_page, other=other)
    return render_template('messages_with_other.html', conversation=conversation.items,
                           next_url=next_url, prev_url=prev_url, user=user,
                           title=user.username + ' - Conversation', form=form, last_url=last_url)

@bp.route('/notifications')
@login_required
def notifications():
    since = request.args.get('since', 0.0, type=float)
    notifications = current_user.notifications.filter(
        Notification.timestamp > since).order_by(Notification.timestamp.asc()) # isn't .asc() the default ?
    return jsonify([{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications])

@bp.route('/export_posts')
@login_required
def export_posts():
    if current_user.get_task_in_progress('export_posts'):
        flash('An export task is currently in progress')
    else:
        current_user.launch_task('export_posts', 'Exporting posts...')
        db.session.commit() # after having already added task to session
    return redirect(url_for('main.user', username=current_user.username))

# set password criteria via validators
# functionality for deleting posts