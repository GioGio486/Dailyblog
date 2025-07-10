from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash  # ✅ Add this
from ext import app, db, login
from models import User, Post, FriendRequest
from forms import RegisterForm, LoginForm, PostForm, EditPostForm


@login.user_loader
def load_user(user_id): return db.session.get(User, int(user_id))

@app.route('/')
def home():
    posts = Post.query.filter_by(visibility='public').order_by(Post.id.desc()).all()
    return render_template('home.html', posts=posts)

@app.route('/why')
def why(): return render_template('why.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated: return redirect(url_for('dashboard'))
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, password=generate_password_hash(form.password.data))
        db.session.add(user); db.session.commit()
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user); return redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user(); return redirect(url_for('home'))

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    form = PostForm()
    if form.validate_on_submit():
        db.session.add(Post(content=form.content.data, visibility=form.visibility.data, author=current_user))
        db.session.commit(); flash('Post created!')
        return redirect(url_for('dashboard'))
    posts = Post.query.filter_by(user_id=current_user.id).order_by(Post.id.desc()).all()
    return render_template('dashboard.html', form=form, posts=posts)

@app.route('/admin_posts')
@login_required
def admin_posts():
    if not current_user.is_admin(): return redirect(url_for('dashboard'))
    posts = Post.query.order_by(Post.id.desc()).all()
    return render_template('admin_posts.html', posts=posts)

@app.route('/admin/edit_post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    if not current_user.is_admin(): return redirect(url_for('dashboard'))
    post = Post.query.get_or_404(post_id)
    form = EditPostForm(obj=post)
    if form.validate_on_submit():
        post.content, post.visibility = form.content.data, form.visibility.data
        db.session.commit(); flash("Post updated.")
        return redirect(url_for('admin_posts'))
    return render_template('edit_post.html', form=form, post=post)

@app.route('/admin/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    if not current_user.is_admin(): return redirect(url_for('dashboard'))
    db.session.delete(Post.query.get_or_404(post_id)); db.session.commit()
    flash("Post deleted."); return redirect(url_for('admin_posts'))

@app.route('/friends')
@login_required
def friends():
    ids = [f.id for f in current_user.friends]
    posts = Post.query.filter(Post.user_id.in_(ids), Post.visibility == 'friends').order_by(Post.id.desc()).all()
    return render_template('friends.html', posts=posts)

@app.route('/users')
@login_required
def users():
    all_users = User.query.filter(User.id != current_user.id).all()
    sent = [r.to_id for r in FriendRequest.query.filter_by(from_id=current_user.id, status='pending')]
    received = [r.from_id for r in FriendRequest.query.filter_by(to_id=current_user.id, status='pending')]
    friends = [f.id for f in current_user.friends]
    return render_template('users.html', users=all_users, sent=sent, received=received, friends_ids=friends)

@app.route('/send_request/<int:user_id>')
@login_required
def send_request(user_id):
    if user_id == current_user.id or FriendRequest.query.filter_by(from_id=current_user.id, to_id=user_id).first():
        return redirect(url_for('users'))
    db.session.add(FriendRequest(from_id=current_user.id, to_id=user_id)); db.session.commit()
    return redirect(url_for('users'))

@app.route('/requests')
@login_required
def requests():
    reqs = FriendRequest.query.filter_by(to_id=current_user.id, status='pending').all()
    for r in reqs: r.from_user = User.query.get(r.from_id)
    return render_template('requests.html', requests=reqs)

@app.route('/accept/<int:req_id>')
@login_required
def accept(req_id):
    req = FriendRequest.query.get_or_404(req_id)
    if req.to_id != current_user.id: return redirect(url_for('requests'))
    req.status = 'accepted'
    u = User.query.get(req.from_id)
    if u not in current_user.friends:
        current_user.friends.append(u); u.friends.append(current_user)
    db.session.commit(); return redirect(url_for('requests'))

@app.route('/reject/<int:req_id>')
@login_required
def reject(req_id):
    req = FriendRequest.query.get_or_404(req_id)
    if req.to_id != current_user.id: return redirect(url_for('requests'))
    db.session.delete(req); db.session.commit()
    return redirect(url_for('requests'))
