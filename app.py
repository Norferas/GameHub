from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import os, uuid

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "instance", "gamehub.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "static", "uploads")
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024

db = SQLAlchemy(app)

ALLOWED_IMAGES = {"png", "jpg", "jpeg", "gif", "webp"}
ALLOWED_VIDEOS = {"mp4", "webm", "mov"}

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    bio = db.Column(db.Text, default="")
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    cover = db.Column(db.String(500), default="")
    description = db.Column(db.Text, default="")
    developer = db.Column(db.String(150), default="")
    release_year = db.Column(db.Integer)

class UserGame(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey("game.id"), nullable=False)
    status = db.Column(db.String(30), default="playing")
    user = db.relationship("User", backref="library")
    game = db.relationship("Game", backref="players")
    __table_args__ = (db.UniqueConstraint("user_id", "game_id", name="unique_user_game"),)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey("game.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    user = db.relationship("User", backref="reviews")
    game = db.relationship("Game", backref="reviews")

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    media_path = db.Column(db.String(500), nullable=False)
    media_type = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    user = db.relationship("User", backref="posts")

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    user = db.relationship("User")
    post = db.relationship("Post", backref=db.backref("comments", cascade="all, delete-orphan"))

class SiteSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(80), unique=True, nullable=False)
    value = db.Column(db.Text, default="")

def current_user():
    uid = session.get("user_id")
    return db.session.get(User, uid) if uid else None

@app.context_processor
def inject_globals():
    settings = {s.key: s.value for s in SiteSetting.query.all()}
    return {"current_user": current_user(),
            "site_name": settings.get("site_name", "GameHub"),
            "site_description": settings.get("site_description", "")}

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user():
            flash("Faça login para continuar.", "warning")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user or not user.is_admin:
            abort(403)
        return fn(*args, **kwargs)
    return wrapper

def save_upload(file):
    if not file or not file.filename:
        return None, None
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_IMAGES | ALLOWED_VIDEOS:
        return None, None
    filename = f"{uuid.uuid4().hex}.{ext}"
    file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
    kind = "image" if ext in ALLOWED_IMAGES else "video"
    return f"uploads/{filename}", kind

@app.route("/")
def home():
    posts = Post.query.order_by(Post.created_at.desc()).limit(50).all()
    games = Game.query.order_by(Game.title).all()
    return render_template("home.html", posts=posts, games=games)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        if len(password) < 6:
            flash("A senha precisa ter pelo menos 6 caracteres.", "danger")
            return redirect(url_for("register"))
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("Usuário ou e-mail já cadastrado.", "danger")
            return redirect(url_for("register"))
        user = User(username=username, email=email, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        flash("Conta criada. Agora faça login.", "success")
        return redirect(url_for("login"))
    return render_template("auth.html", mode="register")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form["email"].strip().lower()).first()
        if user and check_password_hash(user.password_hash, request.form["password"]):
            session["user_id"] = user.id
            return redirect(url_for("home"))
        flash("E-mail ou senha inválidos.", "danger")
    return render_template("auth.html", mode="login")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/profile/<username>")
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    reviews = Review.query.filter_by(user_id=user.id).order_by(Review.created_at.desc()).all()
    return render_template("profile.html", user=user, reviews=reviews)

@app.route("/game/<int:game_id>", methods=["GET", "POST"])
def game(game_id):
    game = Game.query.get_or_404(game_id)
    user = current_user()
    if request.method == "POST":
        if not user:
            return redirect(url_for("login"))
        rating = int(request.form["rating"])
        rating = max(1, min(10, rating))
        review = Review.query.filter_by(user_id=user.id, game_id=game.id).first()
        if not review:
            review = Review(user_id=user.id, game_id=game.id)
            db.session.add(review)
        review.rating = rating
        review.comment = request.form.get("comment", "").strip()
        if not UserGame.query.filter_by(user_id=user.id, game_id=game.id).first():
            db.session.add(UserGame(user_id=user.id, game_id=game.id))
        db.session.commit()
        flash("Avaliação salva.", "success")
        return redirect(url_for("game", game_id=game.id))
    reviews = Review.query.filter_by(game_id=game.id).order_by(Review.created_at.desc()).all()
    avg = round(sum(r.rating for r in reviews) / len(reviews), 1) if reviews else None
    return render_template("game.html", game=game, reviews=reviews, average=avg)

@app.route("/library/add/<int:game_id>", methods=["POST"])
@login_required
def add_library(game_id):
    if not Game.query.get(game_id):
        abort(404)
    status = request.form.get("status", "playing")
    item = UserGame.query.filter_by(user_id=current_user().id, game_id=game_id).first()
    if not item:
        db.session.add(UserGame(user_id=current_user().id, game_id=game_id, status=status))
    else:
        item.status = status
    db.session.commit()
    return redirect(request.referrer or url_for("home"))

@app.route("/post/create", methods=["POST"])
@login_required
def create_post():
    path, kind = save_upload(request.files.get("media"))
    if not path:
        flash("Envie uma imagem ou vídeo válido.", "danger")
        return redirect(url_for("home"))
    post = Post(user_id=current_user().id, media_path=path, media_type=kind,
                description=request.form.get("description", "").strip())
    db.session.add(post)
    db.session.commit()
    return redirect(url_for("home"))

@app.route("/post/<int:post_id>/comment", methods=["POST"])
@login_required
def comment_post(post_id):
    if not Post.query.get(post_id):
        abort(404)
    text = request.form.get("text", "").strip()
    if text:
        db.session.add(Comment(post_id=post_id, user_id=current_user().id, text=text))
        db.session.commit()
    return redirect(url_for("home"))

@app.route("/admin")
@admin_required
def admin():
    settings = {s.key: s.value for s in SiteSetting.query.all()}
    return render_template("admin.html", users=User.query.count(), games=Game.query.count(),
                           posts=Post.query.count(), settings=settings)

@app.route("/admin/settings", methods=["POST"])
@admin_required
def admin_settings():
    for key in ["site_name", "site_description", "accent_color"]:
        value = request.form.get(key, "").strip()
        setting = SiteSetting.query.filter_by(key=key).first()
        if not setting:
            setting = SiteSetting(key=key)
            db.session.add(setting)
        setting.value = value
    db.session.commit()
    flash("Configurações atualizadas.", "success")
    return redirect(url_for("admin"))

@app.route("/admin/game/create", methods=["POST"])
@admin_required
def admin_game_create():
    game = Game(
        title=request.form["title"].strip(),
        cover=request.form.get("cover", "").strip(),
        developer=request.form.get("developer", "").strip(),
        description=request.form.get("description", "").strip(),
        release_year=int(request.form["release_year"]) if request.form.get("release_year") else None
    )
    db.session.add(game)
    db.session.commit()
    return redirect(url_for("admin"))

@app.cli.command("init")
def init_db():
    db.create_all()
    if not SiteSetting.query.filter_by(key="site_name").first():
        db.session.add(SiteSetting(key="site_name", value="GameHub"))
        db.session.add(SiteSetting(key="site_description", value="Sua biblioteca social de jogos."))
        db.session.add(SiteSetting(key="accent_color", value="#7c5cff"))
    if not User.query.filter_by(email="admin@gamehub.local").first():
        admin = User(username="admin", email="admin@gamehub.local",
                     password_hash=generate_password_hash("admin123"), is_admin=True)
        db.session.add(admin)
    db.session.commit()
    print("Banco inicializado. Admin: admin@gamehub.local / admin123")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
