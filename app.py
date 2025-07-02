from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
import os

from models import db, User, Calculation  # Import db, User, and Calculation from models

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pricensy.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

bcrypt = Bcrypt(app)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        currency = request.form['currency']
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already exists.', 'danger')
            return render_template('register.html')
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password_hash=hashed_password, preferred_currency=currency)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter((User.username == username) | (User.email == username)).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        product_name = request.form['product_name']
        cost_price = float(request.form['cost_price'])
        selling_price = float(request.form['selling_price'])
        currency = request.form['currency']
        profit = max(0, selling_price - cost_price)
        loss = max(0, cost_price - selling_price)
        calc = Calculation(
            product_name=product_name,
            cost_price=cost_price,
            selling_price=selling_price,
            profit=profit,
            loss=loss,
            currency=currency,
            user_id=current_user.id
        )
        db.session.add(calc)
        db.session.commit()
        flash('Calculation saved!', 'success')
    calculations = Calculation.query.filter_by(user_id=current_user.id).order_by(Calculation.timestamp.desc()).all()
    return render_template('dashboard.html', calculations=calculations)

@app.route('/report')
@login_required
def report():
    calculations = Calculation.query.filter_by(user_id=current_user.id).order_by(Calculation.timestamp.desc()).all()
    total_profit = sum(c.profit for c in calculations)
    total_loss = sum(c.loss for c in calculations)
    return render_template('report.html', calculations=calculations, total_profit=total_profit, total_loss=total_loss)

# Blueprints or routes will be added here

if __name__ == '__main__':
    app.run(debug=True) 