from flask import render_template, flash, redirect, session, url_for, request, g
from flask_login import login_user, logout_user, current_user, login_required, fresh_login_required
from app import app, db, lm, es
from app.forms import LoginForm, EditForm, PostForm, SearchForm
from app.models import User, Post
from datetime import datetime
from flask import Blueprint
from config import POSTS_PER_PAGE

bp = Blueprint('microblog', __name__)

@bp.route('/givemeurl')
def givemeurl():
    return "The URL for this page is {}".format(url_for('.givemeurl'))

@bp.route('/', methods=['GET'])
@bp.route('/index', methods=['GET'])
@bp.route('/index/<int:page>', methods=['GET'])
@login_required
def index(page=1):
    '''###############################
    Index page
    ##################################
    '''
    #posts = g.user.followed_posts().all()
    posts = g.user.followed_posts().paginate(page, POSTS_PER_PAGE, False)

    return render_template('index.html',
                           title='Home',
                           form=PostForm(),
                           posts=posts)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    '''###############################
    Log to the system
    ##################################
    '''
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
@bp.route('/user/<nickname>/<int:page>')
@login_required
def user(nickname, page=1):
    '''###############################
    Get user information
    ##################################
    '''
    user = User.query.filter_by(nickname=nickname).first()
    if user == None:
        flash('User %s not found.' % nickname)
        return redirect(url_for('.index'))
    # posts = [
    #     {'author': user, 'body': 'Test post #1'},
    #     {'author': user, 'body': 'Test post #2'}
    # ]
    posts = user.posts.paginate(page, POSTS_PER_PAGE, False)
    return render_template('user.html',
                           user=user,
                           posts=posts)

@bp.route('/edit', methods=['GET', 'POST'])
@fresh_login_required
def edit():
    '''###############################
    Edit user information
    ##################################
    '''
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

@bp.route("/post", methods=["POST"])
@login_required
def post():
    '''###############################
    Submit a new post
    ##################################
    '''
    form = PostForm()
    if form.validate_on_submit():
        #save the post
        post = Post(body=form.post.data, timestamp=datetime.utcnow(), author=g.user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is live!')

        res = es.index(index="microblog", doc_type='post', 
            body=dict(id=post.id, body=post.body, 
            user_id=post.user_id, timestamp=post.timestamp))
        app.logger.debug(res['created'])

    return redirect(url_for('.index'))

@bp.route("/logout")
@login_required
def logout():
    '''###############################
    Logout from the system
    ##################################
    '''
    logout_user()
    return redirect(url_for('.login'))

@bp.route("/follow/<nickname>")
@login_required
def follow(nickname):
    '''###############################
    Follow user route
    ##################################
    '''
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
    '''###############################
    Unfollow user route
    ##################################
    '''
    flash('Operation not implemented')
    return redirect(url_for('.index'))

@bp.route("/search", methods=["POST"])
@login_required
def search():
    '''###############################
    Search through posts
    ##################################
    '''
    if not g.search_form.validate_on_submit():
        return redirect(url_for('index'))
    return redirect(url_for('.search_results', query=g.search_form.search.data))

@bp.route("/search_results/<query>")
@login_required
def search_results(query):
    res = es.search(index="microblog", doc_type="post", body={"query": {"match": { "body": query }}})

    post_ids = []
    for hit in res['hits']['hits']:
        app.logger.debug(hit)
        post_ids.append(hit['_source']['id'])
    app.logger.debug(post_ids)
    posts = g.user.followed_posts().filter(Post.id.in_(post_ids))
    return render_template('search_results.html', 
                           query=query,
                           results=posts)

@app.before_request
def before_request():
    g.user = current_user
    if g.user.is_authenticated:
        g.user.last_seen = datetime.utcnow()
        db.session.add(g.user)
        db.session.commit()
        g.search_form = SearchForm()
    
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