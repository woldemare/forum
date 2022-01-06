from flask import Flask, render_template, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


app = Flask(__name__)
app.config['SECRET_KEY'] = 'afee8c5f1b942ef5df1e8e68846e00ec6e233e42b1cecbe236f26581cf8b6765'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    intro = db.Column(db.String(300), nullable=False)
    text = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime)
    creator = db.Column(db.String(100), default=None)

    def __repr__(self):
        return '<Article %r>' % self.id


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(200))
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<User %r>' % self.id


@app.route('/')
@app.route('/home')
def index():
    return render_template("index.html")


@app.route('/item')
def items():
    articles = Article.query.order_by(Article.date.desc()).all()
    return render_template("item.html", articles=articles)


@app.route('/item/<int:id>')
def item_detail(id):
    article = Article.query.get(id)
    if current_user.is_authenticated is True:
        set = True if article.creator == current_user.name else False
    else:
        set = False
    return render_template("item_detail.html", article=article, set=set)


@app.route('/item/<int:id>/delete')
def item_delete(id):
    article = Article.query.get_or_404(id)
    if current_user.is_authenticated:
        if article.creator == current_user.name:
            try:
                db.session.delete(article)
                db.session.commit()
                return redirect('/item')
            except:
                return "При удалении статьи произошла ошибка"
        else:
            return "Удалять чужие статьи нехорошо"
    else:
        return "Зарегистрируйтесь"


@app.route('/item/<int:id>/update', methods=['POST', 'GET'])
def item_update(id):
    article = Article.query.get(id)
    if current_user.is_authenticated:
        set = True if article.creator == current_user.name else False
    else:
        set = False
    if request.method == "POST":
        article.title = request.form['title']
        article.intro = request.form['intro']
        article.text = request.form['text']
        try:
            db.session.commit()
            return redirect('/item')
        except:
            return "При изменении статьи произошла ошибка"
    else:
        return render_template("item_update.html", article=article, set=set)


@app.route('/create-article', methods=['POST', 'GET'])
def create_article():
    if request.method == "POST":
        title = request.form['title']
        intro = request.form['intro']
        text = request.form['text']
        date = datetime.utcnow()
        if current_user.is_authenticated is False:
            article = Article(title=title, intro=intro, text=text, date=date)
        else:
            article = Article(title=title, intro=intro, text=text, date=date, creator=current_user.name)
        try:
            db.session.add(article)
            db.session.commit()
            return redirect('/')
        except:
            return "При добавлении статьи в базу данных произошла ошибка"
    else:
        return render_template("create_article.html")


@app.route('/profile')
@login_required
def profile():
    articles = Article.query.filter_by(creator=current_user.name).all()
    return render_template("profile.html", articles=articles, name=current_user.name)


@app.route('/login')
def login():
    return render_template("login.html")


@app.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password, password):
        flash('Please check your login details and try again')
        return render_template("login.html")
    login_user(user, remember=remember)
    return redirect(url_for('profile'))


@app.route('/signup')
def signup():
    return render_template("signup.html")


@app.route('/signup', methods=['POST'])
def signup_post():
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')
    user = User.query.filter_by(email=email).first()
    if user:
        flash('Этот email уже зарегистрирован')
        return redirect(url_for('signup'))
    new_user = User(email=email, name=name, password=generate_password_hash(password, method='sha256'))
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('login'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)