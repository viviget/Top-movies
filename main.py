from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
Bootstrap5(app)
headers = {
            "accept": "application/json",
            "Authorization": os.environ.get('AUTHOR_KEY')
        }

db = SQLAlchemy()
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('SQL_URL')
db.init_app(app)


class Movies(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=True)
    year = db.Column(db.Integer)
    description = db.Column(db.String)
    rating = db.Column(db.Float)
    ranking = db.Column(db.Integer)
    review = db.Column(db.String)
    img_url = db.Column(db.String)


with app.app_context():
    db.create_all()


class RateMovieForm(FlaskForm):
    rating = StringField('Your Rating Out of 10 e.g. 7.5', validators=[DataRequired()])
    review = StringField('Your Review', validators=[DataRequired()])
    submit = SubmitField('Update')


class AddMovieForm(FlaskForm):
    movie_title = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField('Add Movie')


@app.route("/")
def home():
    #order_by
    result = db.session.execute(db.select(Movies).order_by(Movies.rating)).scalars()
    # convert ScalarResult to Python List
    all_movies = result.all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies)-i
    return render_template("index.html", movies=all_movies)


@app.route("/add", methods=['POST', 'GET'])
def add():
    form = AddMovieForm()
    if form.validate_on_submit():
        search_movie = form.movie_title.data
        movie_url = f"https://api.themoviedb.org/3/search/movie?query={search_movie}&include_adult=false&language=en-US&page=1"
        response = requests.get(movie_url, headers=headers)
        data = response.json()['results']
        return render_template('select.html', movies = data)
    return render_template('add.html', form=form)

@app.route("/find")
def find():
    add_movie_id = request.args.get('id_chosen')
    movie_detail_url = f'https://api.themoviedb.org/3/movie/{add_movie_id}?language=en-US'
    response2 = requests.get(movie_detail_url, headers=headers)
    detail_data = response2.json()
    new_movie = Movies(
        title=detail_data['original_title'],
        year=detail_data['release_date'].split('-')[0],
        description=detail_data['overview'],
        img_url=f"https://image.tmdb.org/t/p/w500{detail_data['poster_path']}"
    )
    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for('edit', id=new_movie.id))


@app.route("/edit", methods=['POST', 'GET'])
def edit():
    form = RateMovieForm()
    # POST用form；GETh和POST用args
    movie_id = request.args.get('id')
    movie_to_edit = db.get_or_404(Movies, movie_id)
    if form.validate_on_submit():
        movie_to_edit.rating = float(form.rating.data)
        movie_to_edit.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", form=form, movie=movie_to_edit)


@app.route("/delete")
def delete():
    movie_id = request.args.get('id')
    movie_to_delete = db.get_or_404(Movies, movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
