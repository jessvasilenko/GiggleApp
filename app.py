import requests
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from passlib.hash import sha256_crypt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///giggle.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists.')
            return redirect(url_for('register'))
        hashed_password = sha256_crypt.hash(password)
        new_user = User(email=email, username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and sha256_crypt.verify(password, user.password):
            login_user(user)
            return redirect(url_for('events'))
        else:
            flash('Invalid login credentials')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/events', methods=['GET', 'POST'])
@login_required
def events():
    if request.method == 'POST':
        # This block is executed when the form is submitted
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        # Here we make a POST request to the microservice
        try:
            response = requests.post('http://localhost:5001/get_location', json={'lat': latitude, 'lon': longitude})
            response.raise_for_status()  # Will raise an HTTPError if the HTTP request returned an unsuccessful status code
        except requests.exceptions.RequestException as e:
            # Handle any errors that occur during the request
            print(e)
            flash('Could not get location-based events.')
            return redirect(url_for('events'))

        # If the request was successful, we process the response
        events_data = response.json()
        return render_template('events.html', events=events_data)
    else:
        # This block is executed on GET request
        return render_template('events.html')

if __name__ == '__main__':
    app.run(debug=True)
