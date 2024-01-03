from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

'''
Red underlines? Install the required packages first: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from requirements.txt for this project.
'''
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

# CREATE DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
db = SQLAlchemy()
db.init_app(app)

# CREATE TABLE
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)

# Create table schema in the database. 
# Requires application context.
with app.app_context():
    db.create_all()

class RateMovieForm(FlaskForm):
    rating = StringField("Your Rating Out of 10 e.g. 7.5")
    review = StringField("Your Review")
    submit = SubmitField("Done")

# New Find Movie Form
class FindMovieForm(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")

# 建立movie 实例对象
# new_movie = Movie(
#      title="Phone Booth",
#      year=2002,
#      description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#      rating=7.3,
#      ranking=10,
#      review="My favourite character was the caller.",
#      img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
# )

# second_movie = Movie(
#      title="Avatar The Way of Water",
#      year=2022,
#      description="Set more than a decade after the events of the first film, learn the story of the Sully family (Jake, Neytiri, and their kids), the trouble that follows them, the lengths they go to keep each other safe, the battles they fight to stay alive, and the tragedies they endure.",
#      rating=7.3,
#      ranking=9,
#      review="I liked the water.",
#      img_url="https://image.tmdb.org/t/p/w500/t6HIqrRAclMCA60NsSmeqe9RmNV.jpg"
# )

# with app.app_context():
#     # 将 new movie 加入 Movie 表 中
#     db.session.add(new_movie)
#     # 将 second movie 加入 Movie 表 中
#     db.session.add(second_movie)
#     # 提交即保存到数据库:
#     db.session.commit()
    
MOVIE_DB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_DB_INFO_URL = "https://api.themoviedb.org/3/movie"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"
MOVIE_DB_API_KEY = "4a868962497b10fbc9522ad8d74774fd"

@app.route("/")
def home():
    query = db.select(Movie).order_by(Movie.rating)
    result = db.session.execute(query)
    # 将 Scalar 的结果 转换 成 Python List
    # 返还一个保存所有movie实例对象的数组
    all_movies = result.scalars().all()

    '''
    此时 电影 按照 rating 从 小到大 排列

    假如有三部电影，评分为9.3, 9.7, 9.9

    第一部电影，ranking 是 3 - 0 = 3
    第一部电影，ranking 是 3 - 1 = 2
    第一部电影，ranking 是 3 - 2 = 1
    
    '''
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i

    # 将 all_movies 对象 用于 渲染 index.html
    # 将 index.html 页面 发送回客户端
    return render_template("index.html", movies = all_movies)

'''
1. 用户首次访问 /add 时，会执行 return render_template("add.html", form = form)。
    这时，服务器将 add.html 页面和一个新的空白 form 对象发送给客户端浏览器。
    用户在浏览器中看到的是一个空白的表单，用于输入数据。

2. 当用户填写表单并点击提交按钮时，浏览器会将表单数据以 POST 请求的方式发送回服务器。

3. 服务器接收到 POST 请求后，if form.validate_on_submit() 会检查表单数据是否符合要求。
    如果数据验证通过（例如，所有必填字段都已正确填写），则执行 if 块内的代码。

4. 在这个例子中，如果验证通过，服务器会处理电影标题的搜索，然后将搜索结果返回到 select.html 页面。
    如果数据验证未通过（比如某些字段没填或格式不正确），或者这是用户第一次访问（GET 请求），
    则再次执行 return render_template("add.html", form = form)。
    这时，服务器会再次将 add.html 和包含了用户之前输入数据及错误信息的 form 对象发送回客户端。

因此，return render_template("add.html", form = form) 这行代码可能执行于两种情况：
用户第一次访问该路由时，或者用户提交的表单数据未通过验证需要重新填写时。
在这两种情况下，服务器都会将 form 对象（可能包含错误信息）和 add.html 页面发送回客户端。

'''
@app.route("/add", methods=["GET", "POST"])
def add_movie():
    form = FindMovieForm()

    '''
    tell our form to validate the user's entry when they hit submit. 
    so we have to edit our route and make sure it is able to respond to POST requests and then to validate_on_submit()
    '''

    # POST 请求
    if form.validate_on_submit():
        # 从 add.html 表单 发给 客户端 的 数据 中 获取 movie的 title 信息
        movie_title = form.title.data
        response = requests.get(MOVIE_DB_SEARCH_URL, params={"api_key": MOVIE_DB_API_KEY, "query": movie_title})
        data = response.json()["results"]

 
        # 将 data 对象 用于 渲染 select.html
        # 将 select.html 页面 发送回客户端
        return render_template("select.html", options = data)
    
    # GET 请求，第一次访问该 /add URL
    # 将 form 对象 用于 渲染 add.html
    # 将 add.html 页面发送回客户端
    return render_template("add.html", form = form)

'''
    这个函数首先创建一个 RateMovieForm 表单实例，然后从客户端请求的 URL 中获取电影的 ID。
    使用这个 ID，它从数据库中检索出相应的电影实例。

    接下来，函数检查是否收到了一个 POST 请求，并且表单数据是否有效。如果是这样：

    - 表单数据被用来更新数据库中该电影实例的 rating 和 review 字段。
    - 然后提交这些更改到数据库。
    - 最后，用户被重定向到 home 视图函数定义的 URL。

    如果不是 POST 请求或者表单数据无效（比如用户第一次访问这个页面，或者表单验证失败），
    那么 return render_template("edit.html", movie = movie, form = form) 这行代码将执行。
    这意味着 edit.html 模板和当前的表单数据（包括任何错误信息）以及电影信息将被发送回客户端以供用户查看和编辑。

    总结一下，这段代码的主要功能是：

    1. 从数据库获取特定电影的详细信息。
    2. 允许用户通过表单提交对该电影的评分和评论。
    3. 验证用户提交的表单数据。
    4. 如果表单数据有效，更新数据库中的电影信息并重定向到主页。
    5. 如果表单数据无效或者是 GET 请求，向用户显示带有当前数据和错误信息（如果有的话）的表单。
'''
@app.route("/edit", methods = ["GET", "POST"])
def rate_movie():

    form = RateMovieForm()
    # 从客户端 传给 服务器 的 request url中获取 movie 的 id
    movie_id = request.args.get("id")
    # 从数据库 Movie 表 中 获取 对应 该 movie id的 movie 实例对象
    movie = db.get_or_404(Movie, movie_id)

    '''
    tell our form to validate the user's entry when they hit submit. 
    so we have to edit our route and make sure it is able to respond to POST requests and then to validate_on_submit()
    '''

    # POST请求
    if form.validate_on_submit():
        # 从 edit.html 表单 发给 服务器 的 数据 中 更新movie里面的rating
        movie.rating = float(form.rating.data)
        # 从 edit.html 表单 发给 服务器 的 数据 中 更新movie里面的review
        movie.review = form.review.data
        db.session.commit()

        # 查找名为 rate_movie 的视图函数，并使用该函数定义的路由规则来生成 URL
        # redirect 该 URL
        return redirect(url_for('home'))
    
    # GET请求， 第一次访问 /edit URL
    # 将 form 对象, movie 对象 用于 渲染 edit.html 
    # 将 edit.html 页面发送回客户端
    return render_template("edit.html", movie = movie, form = form)

@app.route("/find")
def find_movie():
    movie_api_id = request.args.get("id")

    if movie_api_id:
        movie_api_url = f"{MOVIE_DB_INFO_URL}/{movie_api_id}"
        #The language parameter is optional, if you were making the website for a different audience 
        #e.g. Hindi speakers then you might choose "hi-IN"
        response = requests.get(movie_api_url, params={"api_key": MOVIE_DB_API_KEY, "language": "en-US"})
        data = response.json()

        new_movie = Movie(
            title=data["title"],
            year=data["release_date"].split("-")[0],
            img_url=f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}",
            description=data["overview"]
        )

        db.session.add(new_movie)
        db.session.commit()
        
        return redirect(url_for("rate_movie", id = new_movie.id))

@app.route("/delete")
def delete_movie():
    # 从客户端 传给 服务器 的 request url中获取 movie 的 id
    movie_id = request.args.get("id")
    # 从数据库 Moviek表 中 获取 对应 该 movie id的 movie 实例对象
    movie = db.get_or_404(Movie, movie_id)
    db.session.delete(movie)
    db.session.commit()

    '''
    查找名为 rate_movie 的视图函数，并使用该函数定义的路由规则来生成 URL

    id = movie.id 是一个关键字参数，它将被添加到生成的 URL 中。
    在这个例子中，movie.id 的值将作为 id 参数附加到 URL 上
    '''
    return redirect(url_for("home"))

if __name__ == '__main__':
    app.run(debug=True)
