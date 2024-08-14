import os
from datetime import datetime

from flask import Flask, redirect, render_template, request, send_from_directory, url_for
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

# demo
from os import getenv
from mysql.connector import Error
from pymongo import MongoClient
import mysql.connector
import pika
import redis
import boto3
from botocore.client import Config
from sqlalchemy import text

app = Flask(__name__, static_folder='static')
csrf = CSRFProtect(app)

# WEBSITE_HOSTNAME exists only in production environment
if 'WEBSITE_HOSTNAME' not in os.environ:
    # local development, where we'll use environment variables
    print("Loading config.development and environment variables from .env file.")
    app.config.from_object('azureproject.development')
else:
    # production
    print("Loading config.production.")
    app.config.from_object('azureproject.production')

app.config.update(
    SQLALCHEMY_DATABASE_URI=app.config.get('DATABASE_URI'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)

# Initialize the database connection
db = SQLAlchemy(app)

# Enable Flask-Migrate commands "flask db init/migrate/upgrade" to work
migrate = Migrate(app, db)

# The import must be done after db initialization due to circular import issue
from models import Restaurant, Review

@app.route('/', methods=['GET'])
def index():
    print('Request for index page received')
    restaurants = Restaurant.query.all()
    return render_template('index.html', restaurants=restaurants)

@app.route('/<int:id>', methods=['GET'])
def details(id):
    restaurant = Restaurant.query.where(Restaurant.id == id).first()
    reviews = Review.query.where(Review.restaurant == id)
    return render_template('details.html', restaurant=restaurant, reviews=reviews)

@app.route('/create', methods=['GET'])
def create_restaurant():
    print('Request for add restaurant page received')
    return render_template('create_restaurant.html')

@app.route('/add', methods=['POST'])
@csrf.exempt
def add_restaurant():
    try:
        name = request.values.get('restaurant_name')
        street_address = request.values.get('street_address')
        description = request.values.get('description')
    except (KeyError):
        # Redisplay the question voting form.
        return render_template('add_restaurant.html', {
            'error_message': "You must include a restaurant name, address, and description",
        })
    else:
        restaurant = Restaurant()
        restaurant.name = name
        restaurant.street_address = street_address
        restaurant.description = description
        db.session.add(restaurant)
        db.session.commit()

        return redirect(url_for('details', id=restaurant.id))

@app.route('/review/<int:id>', methods=['POST'])
@csrf.exempt
def add_review(id):
    try:
        user_name = request.values.get('user_name')
        rating = request.values.get('rating')
        review_text = request.values.get('review_text')
    except (KeyError):
        #Redisplay the question voting form.
        return render_template('add_review.html', {
            'error_message': "Error adding review",
        })
    else:
        review = Review()
        review.restaurant = id
        review.review_date = datetime.now()
        review.user_name = user_name
        review.rating = int(rating)
        review.review_text = review_text
        db.session.add(review)
        db.session.commit()

    return redirect(url_for('details', id=id))

@app.context_processor
def utility_processor():
    def star_rating(id):
        reviews = Review.query.where(Review.restaurant == id)

        ratings = []
        review_count = 0
        for review in reviews:
            ratings += [review.rating]
            review_count += 1

        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        stars_percent = round((avg_rating / 5.0) * 100) if review_count > 0 else 0
        return {'avg_rating': avg_rating, 'review_count': review_count, 'stars_percent': stars_percent}

    return dict(star_rating=star_rating)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/ping')
def ping():
    # PG/Embedded DB
    try:
        db_conn_test = text("SELECT 1")
        db_status = db.session.execute(db_conn_test).fetchone()[0]
    except:
        db_status = 0

    # Redis
    try:
        redis_host = getenv("REDIS_HOSTNAME", "localhost")
        redis_pwd = getenv("REDIS_PASSWORD", "")
        redis_client = redis.Redis(host=redis_host, port=6379, db=0, password=redis_pwd)
        response = redis_client.ping()
        if response:
            redis_status = 1
        else:
            redis_status = 0
    except:
        redis_status = 0

    # mysql
    try:
        mysql_host = getenv("MYSQL_HOSTNAME", "localhost")
        mysql_username = getenv("MYSQL_USERNAME", "root")
        mysql_password = getenv("MYSQL_PASSWORD", "")
        mysql_port = getenv("MYSQL_PORT", "3306")
        mysql_connection = mysql.connector.connect(
            host=mysql_host,
            user=mysql_username,
            password=mysql_password,
            port=mysql_port
        )
        if mysql_connection.is_connected():
            mysql_status = 1
        else:
            mysql_status = 0
    except:
        mysql_status = 0

    # mongo
    try:
        mongo_uri = getenv("MONGODB_URL", "")
        mongo_client = MongoClient(mongo_uri)
        mongo_result = mongo_client.server_info()
        if mongo_result:
            mongo_status = 1
        else:
            mongo_status = 0
    except:
        mongo_status = 0

    # rabbitmq
    try:
        rabbit_host = getenv("RABBITMQ_HOSTNAME", "localhost")
        rabbit_username = getenv("RABBITMQ_USERNAME", "root")
        rabbit_password = getenv("RABBITMQ_PASSWORD", "")
        rabbit_port = getenv("RABBITMQ_PORT", "5672")
        rabbit_uri = "amqp://{0}:{1}@{2}:{3}/".format(rabbit_username, rabbit_password, rabbit_host, rabbit_port)
        rabbit_conn = pika.BlockingConnection(pika.URLParameters(rabbit_uri))
        channel = rabbit_conn.channel()
        rabbit_status = 1
    except:
        rabbit_status = 0

    try:
        minio_endpoint = getenv("AWS_ENDPOINT_URL_S3", "http://localhost")
        minio_access_key = getenv("AWS_ACCESS_KEY_ID", "")
        minio_secret_access_key = getenv("AWS_SECRET_ACCESS_KEY", "")
        minio_region = getenv("AWS_REGION", "us-east-1")
        minio_bucket_name = getenv("S3_BUCKET_NAME", "")
        s3 = boto3.resource('s3',
                            endpoint_url=minio_endpoint,
                            aws_access_key_id=minio_access_key,
                            aws_secret_access_key=minio_secret_access_key,
                            config=Config(signature_version='s3v4'),
                            region_name=minio_region)

        bucket = s3.Bucket(minio_bucket_name)

        for obj in bucket.objects.all():
            print(obj.key)

        minio_status = 1
    except:
        minio_status = 0

    json = [
        {'Resource': 'Postgres/Embedded DB', 'Status': db_status},
        {'Resource': 'Redis', 'Status': redis_status},
        {'Resource': 'Mysql', 'Status': mysql_status},
        {'Resource': 'Mongo', 'Status': mongo_status},
        {'Resource': 'RabbitMQ', 'Status': rabbit_status},
        {'Resource': 'MinIO', 'Status': minio_status}
    ]
    return json

if __name__ == '__main__':
    app.run()
