from flask import render_template, flash, redirect, session, url_for, request, g
from flask_login import login_user, logout_user, current_user, login_required, fresh_login_required
from app import app, db, lm
from app.forms import LoginForm, EditForm, PostForm
from app.models import User, Post
from datetime import datetime
from flask import Blueprint

bp = Blueprint('microblog', __name__)

@bp.route('/givemeurl')
def givemeurl():
    return "The URL for this page is {}".format(url_for('.givemeurl'))

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        #save the post
        post = Post(body=form.post.data, timestamp=datetime.utcnow(), author=g.user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is live!')
        return redirect(url_for('.index'))

    posts = g.user.followed_posts().all()

    return render_template('index.html',
                           title='Home',
                           form=form,
                           posts=posts)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if g.user is not None and g.user.is_authenticated:
        return redirect(url_for('.index'))
    form = LoginForm()
    if form.validate_on_submit():
        session['remember_me'] = form.remember_me.data

        user = User.query.filter_by(email=form.openid.data).first()
        if user is None:
            #flash('Invalid login. Please try again.')
            #return redirect(url_for('.login'))
            user = add_user(form.openid.data)
        
        remember_me = False
        if 'remember_me' in session:
            remember_me = session['remember_me']
            session.pop('remember_me', None)
        login_user(user, remember = remember_me)
        return redirect(request.args.get('next') or url_for('.index'))

    return render_template('login.html', 
                           title='Sign In',
                           form=form,
                           providers=app.config['OPENID_PROVIDERS'])

@bp.route('/user/<nickname>')
@login_required
def user(nickname):
    user = User.query.filter_by(nickname=nickname).first()
    if user == None:
        flash('User %s not found.' % nickname)
        return redirect(url_for('.index'))
    # posts = [
    #     {'author': user, 'body': 'Test post #1'},
    #     {'author': user, 'body': 'Test post #2'}
    # ]
    posts = user.posts
    return render_template('user.html',
                           user=user,
                           posts=posts)

@bp.route('/edit', methods=['GET', 'POST'])
@fresh_login_required
def edit():
    form = EditForm(g.user.nickname)
    if form.validate_on_submit():
        g.user.nickname = form.nickname.data
        g.user.about_me = form.about_me.data
        db.session.add(g.user)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('.user', nickname=g.user.nickname))
    else:
        form.nickname.data = g.user.nickname
        form.about_me.data = g.user.about_me
    return render_template('edit.html', form=form)

@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('.login'))

@bp.route("/follow/<nickname>")
@login_required
def follow(nickname):
    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        flash('User %s not found.' % nickname)
        return redirect(url_for('.index'))
    if user == g.user:
        flash('You can\'t follow yourself!')
        return redirect(url_for('.user', nickname=nickname))
    u = g.user.follow(user)
    if u is None:
        flash("Cannot follow " + nickname + ".")
        return redirect(url_for('.user', nickname=nickname))
    db.session.add(u)
    db.session.commit()
    flash('You are now following ' + nickname + '.')
    return redirect(url_for('.user', nickname=nickname))

@bp.route("/unfollow/<nickname>")
@login_required
def unfollow(nickname):
    pass

@app.before_request
def before_request():
    g.user = current_user
    if g.user.is_authenticated:
        g.user.last_seen = datetime.utcnow()
        db.session.add(g.user)
        db.session.commit()
    
@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

def add_user(email):
    nickname = email.split('@')[0]
    nickname = User.make_unique_nickname(nickname)
    user = User(nickname=nickname, email=email)
    db.session.add(user)
    db.session.commit()

    # make the user follow him/herself
    db.session.add(user.follow(user))
    db.session.commit()
    return user