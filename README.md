Flask Store
===
This is an online store built with Python and its web framework, Flask.

## Usage
To run this program is quite easy. First, do `pip install -r requirements.txt` to install all packages including Flask, 
werkzeug and others.

Then, create a new file called `.env`. It should have content like below:
```text
DATABASE_PASS=<your-mysql-database-password>
DATABASE_NAME=<your-mysql-database-name>
FLASK_DEBUG=<debug-or-not>
```

Then, create a new file called `sendgrid.txt` and should contain the content below:
```text
apikey
<your-sendgrid-apikey-here>
```

DO NOT MODIFY THE FIRST LINE. OTHERWISE IT WON'T WORK.

**Finally**, you can do `flask run` to run the website, or just run app.py in the root dictionary.