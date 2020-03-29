# Main file for Shirts4Mike

import os
import ssl
import uuid
from datetime import date

import sendgrid
# Import statement
from flask import Flask, render_template, Markup, url_for, flash, redirect, request

from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

ssl._create_default_https_context = ssl._create_unverified_context  # Setting ssl due to it has some errors with sendgrid

# App setup
app = Flask(__name__)
app.config.update(  # App config
    SECRET_KEY=uuid.uuid4(),
    DEBUG=os.environ.get('FLASK_DEBUG') or False,
    # Database
    SQLALCHEMY_DATABASE_URI=os.environ.get('DEV_DATABASE_URI') or 'mysql+pymysql://root:%s@localhost:3306/%s' \
                                                                  '?charset' \
                                                                  '=utf8mb4' % (os.environ.get('DEV_DATABASE_PASS'),
                                                                                os.environ.get('DEV_DATABASE_NAME')),
    SQLALCHEMY_TRACK_MODIFICATIONS=False
)

# App extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Get details for sendgrid details
sendgrid_file = "sendgrid.txt"
sendgrid_details = []

with open(sendgrid_file) as f:
    sendgrid_details = f.readlines()
    sendgrid_details = [x.strip("\n") for x in sendgrid_details]


# Database models
class AddSize(db.Model):
    """
    A connect model between Size and Product. Use this model to add a new size for a product.
    :param size_id: the id of the given size
    :param product_id: the id of the given product
    :param size: a foreignkey linked from model `Size`
    :param product: a foreignkey linked from model `Product`

    You must provide two params to use it - size and product. The other two can be filled automatically:

    >>> add_size = AddSize(size=size_small, product=test_product)
    >>> db.session.add(add_size)
    >>> db.session.commit()
    >>> size_small.products
    [<AddSize 2; 2>]
    >>> test_product.sizes
    [<AddSize 2; 2>]

    """
    __tablename__ = 'addsizes'
    size_id = db.Column(db.Integer, db.ForeignKey('sizes.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), primary_key=True)

    def __repr__(self):
        return '<AddSize %d; %d>' % (self.size_id, self.product_id)


class Size(db.Model):
    """
    The model for sizes. See `AddSize` to know how to connect it with `Product`.
    :param id: the id for this size, also the primary_key
    :param name: the name for this size, needs to be a string under 64 letters
    :param products: foreignkey. A relationship to model `AddSize`. You can also use this to check the products under
    this size.

    It's very simple to use it, you just need to provide param name:
    >>> size_small = Size(name='Small')
    >>> db.session.add(size_small)
    >>> db.session.commit()

    """
    __tablename__ = 'sizes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    products = db.relationship('AddSize', foreign_keys=[AddSize.size_id],
                               backref=db.backref('size', lazy='joined'))

    def __repr__(self):
        return '<Size %s>' % self.name


class Product(db.Model):
    """
    Model for every product. See `AddSize` to connect it with the sizes.
    :param id: the id for this product
    :param name: the name for the product, which needs to be a string under 64 letters
    :param price: the price for the product, an integer
    :param paypal: the PayPal-code for the product for payment, a string under 128 letters
    :param sizes: all available sizes for the product, also a foreignkey to connect with `AddSize`. Use it to checkout
    all sizes for it
    :param description: the description for the product, and unlimited length
    :param cover_image: the image cover for the product, with a string under 64 letters, which will stored in ./static
    :param textual: the textual of the product, a string under 64 letters
    """
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    price = db.Column(db.Integer)
    paypal = db.Column(db.String(128))
    sizes = db.relationship('AddSize', foreign_keys=[AddSize.product_id],
                            backref=db.backref('product', lazy='joined'))
    description = db.Column(db.Text)
    cover_image = db.Column(db.String(64))
    textual = db.Column(db.String(64))

    def __repr__(self):
        return '<Product %s>' % self.name


class User(db.Model):
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
        "sizes": ["Small", "Medium", "Large"]
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
            '" al  t="' + product["name"] + '">')
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
    flash("This site is a demo do not buy anything")
    return render_template("index.html", **context)


@app.route("/shirts")
def shirts():
    """Function for the Shirts Listing Page"""
    context = {"page_title": "Shirts 4 Mike", "current_year": date.today().year}
    product_data = []
    for product in products_info:
        product_data.append(Markup(get_list_view_html(product)))
    context["product_data"] = Markup("".join(product_data))
    flash("This site is a demo do not buy anything")
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
    flash("This site is a demo do not buy anything")
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
    message.add_to("samzhang951@outlook.com")
    message.set_from("noreply@tomthefrog.com")
    message.set_subject(subject)
    message.set_html(body)
    sendgrid_object.send(message)
    flash("Email sent.")
    return redirect(url_for("contact"))


# Run application
if __name__ == "__main__":
    app.run(debug=True)
