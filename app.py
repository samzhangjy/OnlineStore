# Main file for Shirts4Mike

import os
import ssl
import uuid
from datetime import date
from functools import wraps
from urllib.parse import urljoin, urlparse

import sendgrid
# Import statement
from flask import Flask, render_template, Markup, url_for, flash, redirect, request, session

from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user

# Setting ssl due to it has some errors with SendGrid
ssl._create_default_https_context = ssl._create_unverified_context

# App setup
app = Flask(__name__)
app.config.update(  # App config
    SECRET_KEY=str(uuid.uuid4()),
    # Change this to True if you want it to be debugged by default
    DEBUG=os.environ.get('FLASK_DEBUG') or False,
    # Database
    SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URI') or 'mysql+pymysql://root:%s@localhost:3306/%s' \
                                                                  '?charset' \
                                                                  '=utf8mb4' % (os.environ.get('DATABASE_PASS'),
                                                                                os.environ.get('DATABASE_NAME')),
    SQLALCHEMY_TRACK_MODIFICATIONS=False
)

# App extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Set the login view


# User loader for flask-login
@login_manager.user_loader
def load_user(id):
    return User.query.get(id)


# Get details for sendgrid details
sendgrid_file = "sendgrid.txt"
sendgrid_details = []

with open(sendgrid_file) as f:
    sendgrid_details = f.readlines()
    sendgrid_details = [x.strip("\n") for x in sendgrid_details]


# Database models

class Product(db.Model):
    """
    Model for every product. See `AddSize` to connect it with the sizes.
    :param id: the id for this product
    :param name: the name for the product, which needs to be a string under 64 letters
    :param price: the price for the product, an integer
    :param paypal: the PayPal-code for the product for payment, a string under 128 letters
    :param description: the description for the product, and unlimited length
    :param cover_image: the image cover for the product, with a string under 64 letters, which will stored in ./static
    :param textual: the textual of the product, a string under 64 letters
    """
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    price = db.Column(db.Integer)
    paypal = db.Column(db.String(128))
    description = db.Column(db.Text)
    cover_image = db.Column(db.String(64))
    textual = db.Column(db.String(64))

    def __repr__(self):
        return '<Product %s>' % self.name


class User(db.Model, UserMixin):
    """
    The user model.
    :param id: the id of this user, an integer
    :param username: the username of this user, which is a string under 64 letters, and have to be unique. Otherwise,
    an error will be raised
    :param password_hash: the password hash of the user, uses when checking passwords
    :param password: not stored in the database, but uses it to generate password_hash, an unreadable attribute. If you
    type in user.password, an AttributeError will be raised

    To create a new user is quite easy:
    >>> user = User(username='Test User', password='123')
    >>> db.session.add(user)
    >>> db.session.commit()

    """
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    password_hash = db.Column(db.String(256))

    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)


# Global Variables
products_info = [
    {
        "id": "101",
        "name": "Logo Shirt, Red",
        "img": "shirt-101.jpg",
        "price": 18,
        "paypal": "LNRBY7XSXS5PA",
        "sizes": ["Small", "Medium", "Large"],
        "textual": "cotton"
    },

    {
        "id": "102",
        "name": "Mike the Frog Shirt, Black",
        "img": "shirt-102.jpg",
        "price": 20,
        "paypal": "XP8KRXHEXMQ4J",
        "sizes": ["Small", "Medium", "Large"]
    },

    {
        "id": "103",
        "name": "Mike the Frog Shirt, Blue",
        "img": "shirt-103.jpg",
        "price": 20,
        "paypal": "95C659J3VZGNJ",
        "sizes": ["Small", "Medium", "Large"]
    },

    {
        "id": "104",
        "name": "Logo Shirt, Green",
        "img": "shirt-104.jpg",
        "price": 18,
        "paypal": "Z5EY4SJN64SLU",
        "sizes": ["Small", "Medium", "Large"]
    },

    {
        "id": "105",
        "name": "Mike the Frog Shirt, Yellow",
        "img": "shirt-105.jpg",
        "price": 25,
        "paypal": "RYAGP5EWG4V4G",
        "sizes": ["Small", "Medium", "Large"]
    },

    {
        "id": "106",
        "name": "Logo Shirt, Gray",
        "img": "shirt-106.jpg",
        "price": 20,
        "paypal": "QYHDD4N4SMUKN",
        "sizes": ["Small", "Medium", "Large"]
    },

    {
        "id": "107",
        "name": "Logo Shirt, Teal",
        "img": "shirt-107.jpg",
        "price": 20,
        "paypal": "RSDD7RPZFPQTQ",
        "sizes": ["Small", "Medium", "Large"]
    },

    {
        "id": "108",
        "name": "Mike the Frog Shirt, Orange",
        "img": "shirt-108.jpg",
        "price": 25,
        "paypal": "LFRHBPYZKHV4Y",
        "sizes": ["Small", "Medium", "Large"]
    }
]


# Functions


def get_list_view_html(product):
    """Function to return html for given shirt

    The product argument should be a dictionary in this structure:
    {
        "id": "shirt_id",
        "name": "name_of_shirt",
        "img": "image_name.jpg",
        "price": price_of_shirt_as_int_or_flat,
        "paypal": "paypal_id"
        "sizes": ["array_of_sizes"]
    }

    The html is returned in this structure:
    <li>
      <a href="shirt/shirt_id">
        <img src="/static/shirt_img" alt="shirt_name">
        <p>View Details</p>
      </a>
    </li>
    """
    output = ""
    image_url = url_for("static", filename=product["img"])
    shirt_url = url_for("shirt", product_id=product["id"])
    output = output + "<li>"
    output = output + '<a href="' + shirt_url + '">'
    output = (
            output + '<img src="' + image_url +
            '" alt="' + product["name"] + '">')
    output = output + "<p>View Details</p>"
    output = output + "</a>"
    output = output + "</li>"

    return output


# Routes
# All functions should have a page_title variables if they render templates

@app.route("/")
def index():
    """Function for Shirts4Mike Homepage"""
    context = {"page_title": "Shirts 4 Mike", "current_year": date.today().year}
    counter = 0
    product_data = []
    for product in products_info:
        counter += 1
        if counter < 5:  # Get first 4 shirts
            product_data.append(
                Markup(get_list_view_html(product))
            )
    context["product_data"] = Markup("".join(product_data))
    return render_template("index.html", **context)


@app.route("/shirts")
def shirts():
    """Function for the Shirts Listing Page"""
    context = {"page_title": "Shirts 4 Mike", "current_year": date.today().year}
    product_data = []
    for product in products_info:
        product_data.append(Markup(get_list_view_html(product)))
    context["product_data"] = Markup("".join(product_data))
    return render_template("shirts.html", **context)


@app.route("/shirt/<product_id>")
def shirt(product_id):
    """Function for Individual Shirt Page"""
    context = {"page_title": "Shirts 4 Mike", "current_year": date.today().year}
    my_product = ""
    for product in products_info:
        if product["id"] == product_id:
            my_product = product
    context["product"] = my_product
    return render_template("shirt.html", **context)


@app.route("/receipt")
def receipt():
    """Function to display receipt after purchase"""
    context = {"page_title": "Shirts 4 Mike", "current_year": date.today().year}
    return render_template("receipt.html", **context)


@app.route("/contact")
def contact():
    """Function for contact page"""
    context = {"page_title": "Shirts 4 Mike", "current_year": date.today().year}
    return render_template("contact.html", **context)


# Route to send email
@app.route("/send", methods=['POST'])
def send():
    """Function to send email using sendgrid API"""
    sendgrid_object = sendgrid.SendGridClient(
        sendgrid_details[0], sendgrid_details[1])
    message = sendgrid.Mail()
    sender = request.form["email"]
    subject = request.form["name"]
    body = request.form["message"]
    message.add_to(sender)
    message.set_from("noreply@tomthefrog.com")
    message.set_subject(subject)
    message.set_html(body)
    sendgrid_object.send(message)
    flash("Email sent.")
    return redirect(url_for("contact"))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Route for login"""
    if request.method == 'POST':
        # Get user information
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember')
        # Get user
        user = User.query.filter_by(username=username).first()
        # If the user is valid and the password is correct, login user
        if user is not None and user.verify_password(password):
            login_user(user, remember)
            flash('Login success!')
            next = request.args.get('next')  # Get the next arg from the url, can be generated from flask-login
            if next and is_safe_url(next):  # If the `next` is valid and it's safe, return back to it
                return redirect(next)
            return redirect(url_for('index'))  # Else, go back to the home page
        # Otherwise, the user either not here or the password is incorrect
        flash('Incorrect username or password. Please try again.')
        return redirect(url_for('login'))  # Go back to login view
    return render_template('login.html')


@app.route('/logout')
@login_required  # Login required because you can't logout before you are logged in!
def logout():
    """Logout function for the users"""
    logout_user()  # Logout the current user using logout_user() - simple!
    flash('You have now logged out.')
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register an user account"""
    if request.method == 'POST':
        # Get form data
        username = request.form.get('username')
        password = request.form.get('password')
        # If the user with the same username already exists, tell the user
        if User.query.filter_by(username=username).first() is not None:
            flash('Username already exists. Please choose another one.')
            return redirect(url_for('register'))
        # Create user
        user = User(username=username, password=password)
        db.session.add(user)  # Add user to the current session
        db.session.commit()  # Commit it to the whole database
        flash('Account registered! You can login now.')
        return redirect(url_for('login'))  # Return to the login view to let the user login
    return render_template('register.html')


def admin_required(func):
    """Function to tell if the current user is logged in as an admin or not"""
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if session.get('ADMIN') is None or not session.get('ADMIN') or session.get('ADMIN_LOGGED_OUT'):
            return redirect(url_for('index'))
        return func(*args, **kwargs)
    return decorated_view


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == os.environ.get('ADMIN_USERNAME') and password == os.environ.get('ADMIN_PASSWORD'):
            session['ADMIN'] = True
            flash('You have now logged in as admin.')
            return redirect(url_for('admin'))
        flash('Invalid username or password. Please try again.')
        return redirect(url_for('admin_login'))
    return render_template('admin/login.html')


@app.route('/admin/logout')
@admin_required
def admin_logout():
    session['ADMIN'] = False
    return redirect(url_for('index'))


@app.route('/admin')
@admin_required
def admin():
    products = Product.query.all()
    return render_template('admin/index.html', products=products)


@app.route('/admin/delete/<int:id>')
@admin_required
def admin_delete(id):
    product = Product.query.get_or_404(id)
    db.session.commit()
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully.')
    return redirect(url_for('admin'))


@app.route('/admin/new', methods=['GET', 'POST'])
@admin_required
def admin_new():
    if request.method == 'POST':
        name = request.form.get('name')
        price = int(request.form.get('price'))
        paypal = request.form.get('paypal')
        description = request.form.get('description')
        textual = request.form.get('textual')
        image = request.form.get('image')
        if Product.query.filter_by(name=name).first() is not None:
            flash('Product with the same name already exists. Please choose another one.')
            return redirect(url_for('admin_new'))
        product = Product(name=name, price=price, paypal=paypal, description=description, textual=textual, cover_image=image)
        db.session.add(product)
        db.session.commit()
        flash('New product added successfully!')
        return redirect(url_for('admin'))
    return render_template('admin/new.html')


def is_safe_url(target):
    ref_url = urlparse(request.host_url)  # Get the current base url
    test_url = urlparse(urljoin(request.host_url, target))  # Turn the target url to the absolute url
    # Validate if it is the url inside our website and it's a real url with prefix of http or https
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


# Run application
if __name__ == "__main__":
    app.run(debug=bool(app.config['DEBUG']))  # With debug. If you are running in production, set it to False
