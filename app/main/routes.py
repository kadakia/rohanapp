from flask import render_template, flash, redirect, url_for, request, g, jsonify, current_app
from flask_login import current_user, login_required
from flask_babel import _, get_locale
from app import db
from app.main.forms import EditProfileForm, PostForm, SearchForm
from app.models import User, Post
from app.translate import translate
from datetime import datetime
from guess_language import guess_language
from app.main import bp

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
    # skip directly to first posts, last posts ?!
    return render_template('index.html', title = 'Home', posts = posts.items, form = form,
                            next_url = next_url, prev_url = prev_url)
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
    return render_template('user.html', title = user.username, user = user, posts = posts.items,
                            next_url = next_url, prev_url = prev_url)

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
    return render_template('explore.html', title='Explore', posts=posts.items, next_url=next_url, prev_url=prev_url)

@bp.route('/translate', methods=['POST']) # no form to GET
@login_required
def translate_text():
    return jsonify({'text': translate(request.form['text'], request.form['source_language'], request.form['dest_language'])}) # not request.args.form

# set password criteria via validators
# functionality for deleting posts