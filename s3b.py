import os
import json
import time
import boto3
import random
import string
import logging
import secrets
import smtplib
import sqlite3
from threading import Thread
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, make_response, session, render_template, redirect, url_for


# Init env file
load_dotenv(dotenv_path=".env")

# Running environment
ENVIRONMENT = os.getenv('ENVIRONMENT', "prod")

# S3 Browser server info
SRV_IP = os.getenv('SERVER_IP', "localhost")
SRV_PORT = os.getenv('SERVER_PORT', 4444)

# S3 Browser Base URL
BASE_URL = os.getenv('BASE_URL', "http://localhost:4444")

# Admin email address where to send new user access request
ADMIN_MAIL = os.getenv('ADMIN_MAIL', 'admin@gmail.com')

# Admin credentials
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'p4ssw0rD')

# AWS credentials to connect to S3 
AWS_REGION = os.getenv('AWS_DEFAULT_REGION', 'eu-west-3')
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID', 'YOUR_AWS_AK')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', 'YOUR_AWS_SK')

# Mail user and password that S3 Browser should use to send notification
MAIL_USER = os.getenv('MAIL_USER', 'system@gmail.com')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', 'password_key')

log_level = logging.INFO
app_debug = False
if ENVIRONMENT == "dev":
    log_level = logging.DEBUG
    app_debug = True
elif ENVIRONMENT == "prod":
    log_level = logging.INFO
    app_debug = False

# Init Logging
logging.basicConfig(
    # filename='s3-browser.log',
    level=log_level,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Init Database
conn = sqlite3.connect('data/s3_browser.db', check_same_thread=False)
cursor = conn.cursor()

# Flask app instance
app = Flask(__name__, template_folder='web', static_folder='static')
app.debug = app_debug
app.secret_key = secrets.token_hex(16)

# Init group permission
with open("group_permission.json", "r") as perm_file:
    PERMISSION = json.load(perm_file)

# S3 Client instance
s3 = boto3.client(
    's3',
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
)


def convert_bytes(size_in_bytes):
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_in_bytes)
    unit_index = 0
    
    while size >= 1024 and unit_index < len(units) - 1:
        next_size = size / 1024
        if next_size < 1.0:
            break
        size = next_size
        unit_index += 1
    
    return f"{size:.2f} {units[unit_index]}"


def new_bucket(bucket):
    try:
        location = {'LocationConstraint': AWS_REGION}
        s3.create_bucket(
            Bucket=bucket,
            CreateBucketConfiguration=location
        )
    except Exception as e:
        logging.error(f"CREATE_BUCKET: {e}")
        return False
    return True


def remove_bucket(bucket):
    try:
        s3_client = boto3.resource("s3")
        b = s3_client.Bucket(bucket)
        b.object_versions.delete()
        b.delete()
    except Exception as e:
        logging.error(f"DELETE_BUCKET: '{bucket}' - {e}")
        return False
    return True


def get_all_buckets():
    response = s3.list_buckets()
    return [bucket['Name'] for bucket in response['Buckets']]


def get_authorized_bucket(user_role):
    buckets = PERMISSION[user_role]
    if buckets == ["*"]:
        buckets = get_all_buckets()
    return buckets


def put_bucket_cors(bucket):
    try:
        response = s3.get_bucket_cors(
            Bucket=bucket
        )
        if not response.get('CORSRules'):
            raise Exception

    except:
        s3.put_bucket_cors(
            Bucket=bucket,
            CORSConfiguration={
                'CORSRules': [
                    {
                        'ID': str(time.time()),
                        'AllowedHeaders': [
                            '*'
                        ],
                        'AllowedMethods': [
                            'PUT'
                        ],
                        'AllowedOrigins': [
                            BASE_URL
                        ],
                        'MaxAgeSeconds': 3600
                    },
                ]
            },
            ChecksumAlgorithm='CRC32'
        )


def delete_bucket_cors(bucket):
    s3.delete_bucket_cors(
        Bucket=bucket
    )


def get_bucket_contents(bucket, path=""):
    response = s3.list_objects(
        Bucket=bucket,
        Prefix=path,
        Delimiter="/"
    )
    contents = []
    folders = []
    if response.get("Contents"):
        contents = [(str(content['Key']).split('/')[-1], convert_bytes(content['Size'])) for content in response["Contents"]]
    if response.get("CommonPrefixes"):
        folders = [str(folder['Prefix']).split('/')[-2] for folder in response["CommonPrefixes"]]
    return contents, folders


def generate_presigned_url(bucket, file_key, action):
    try:
        return s3.generate_presigned_url(
            ClientMethod=action,
            Params={
                'Bucket': bucket,
                'Key': file_key
            },
            ExpiresIn=3600
        )
    except Exception as e:
        logging.error(f"PRESIGNED_URL: {e}")
        return None


def send_mail(recipient_mail, new_mail):
    session = smtplib.SMTP('smtp.gmail.com', 587)
    session.starttls()
    session.login(MAIL_USER, MAIL_PASSWORD)
    session.sendmail(MAIL_USER, recipient_mail, new_mail.as_string())
    session.quit()


def send_access_request(name, role, mail, phone, access_code):
    new_mail = MIMEMultipart("alternative")
    new_mail["Subject"] = f"[S3 Browser] Access Request for {mail}"
    new_mail["From"] = f"S3 Browser <{MAIL_USER}>"
    new_mail["To"] = f"S3 Browser Admin <{ADMIN_MAIL}>"
    with open("mail_admin.html", 'r') as body:
        mail_body = body.read()
        mail_body = mail_body.format(
            name=name,
            role=role,
            mail=mail,
            phone=phone,
            access_code=access_code,
            url=BASE_URL
        )
        mail_body = MIMEText(mail_body, "html")
    new_mail.attach(mail_body)
    send_mail(ADMIN_MAIL, new_mail)


def send_access_code(name, mail, access_code):
    new_mail = MIMEMultipart("alternative")
    new_mail["Subject"] = "[S3 Browser] Access approved"
    new_mail["From"] = f"S3 Browser <{MAIL_USER}>"
    new_mail["To"] = "{} <{}>".format(name, mail)
    with open("mail_user.html", 'r') as body:
        mail_body = body.read()
        mail_body = mail_body.format(
            name=name,
            access_code=access_code
        )
        mail_body = MIMEText(mail_body, "html")
    new_mail.attach(mail_body)
    send_mail(mail, new_mail)


def authenticate(access_code):
    try:
        mail, approved = cursor.execute("SELECT MAIL, APPROVED FROM users WHERE ACCESS_CODE=?", (access_code,)).fetchone()
        if approved:
            logging.info(f"AUTHENTICATION: success => {mail} ({access_code})")
            return True
        else:
            return False

    except Exception as e:
        logging.error(f"AUTHENTICATION: failed => {access_code} - {e}")
        return False


def check_user(access_code):
    ok = cursor.execute("""
        SELECT NAME FROM users WHERE ACCESS_CODE=?
    """, (access_code,)).fetchone()
    if ok:
        return True
    else:
        return False


def generate_access_code(length=16):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))


def register_user(name, role, mail, phone):
    try:
        if role in PERMISSION:
            access_code = generate_access_code()

            cursor.execute("""
                INSERT INTO 
                users (ACCESS_CODE, NAME, ROLE, MAIL, PHONE, APPROVED) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, (access_code, name, role, mail, phone, False))
            conn.commit()
            logging.info(f"REGISTRATION: waiting => {mail} ({access_code})")

            return access_code, "Done"
        else:
            return None, "Undefined role"
    except Exception as e:
        logging.error(f"REGISTRATION: failed - {e}")
        return None, e


def remove_user(access_code):
    try:
        cursor.execute("DELETE FROM users WHERE ACCESS_CODE=?", (access_code,))
        conn.commit()
        return True, "Done"
    except Exception as e:
        return False, e


def get_user_info(access_code):
    return cursor.execute("""
        SELECT NAME, ROLE, MAIL, PHONE  FROM users WHERE ACCESS_CODE=?
    """, (access_code,)).fetchone()


def save_logs(user, action):
    _time = time.time()
    m_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(_time))
    cursor.execute("""
        INSERT INTO logs (DATE, USER, ACTION) VALUES (?, ?, ?)
    """, (m_time, user, action))
    conn.commit()


@app.route('/', methods=['GET'])
def root():
    if 'access_code' in session:
        return redirect(url_for("home"))

    return redirect(url_for("login"))


@app.route('/admin/', methods=['GET'])
@app.route('/admin', methods=['GET'])
def admin_root():
    if 'admin' in session:
        return redirect(url_for("admin_users"))

    return redirect(url_for("admin_login"))


@app.route('/login', methods=['GET'])
def login():
    if 'access_code' in session:
        return redirect(url_for("home"))

    return render_template('login.html')


@app.route('/admin/login', methods=['GET'])
def admin_login():
    if 'admin' in session:
        return redirect(url_for("admin_users"))

    return render_template('admin_login.html')


@app.route('/registration', methods=['GET'])
def registration():
    return render_template('registration.html', roles=list(PERMISSION.keys()))


@app.route('/home', methods=['GET'])
def home():
    if 'access_code' not in session:
        return redirect(url_for("login"))

    access_code = session['access_code']
    validUser = check_user(access_code)
    if not validUser:
        session.pop('access_code', None)
        return redirect(url_for("login"))

    name, role, mail, phone = get_user_info(access_code)
    authorized_buckets = get_authorized_bucket(role)

    return render_template(
        "home.html",
        name=name,
        role=role,
        mail=mail,
        phone=phone,
        buckets=authorized_buckets
    )


@app.route('/admin/users', methods=['GET'])
def admin_users():
    if 'admin' not in session:
        return redirect(url_for("admin_login"))

    users_data = cursor.execute("""
        SELECT ACCESS_CODE, NAME, role, MAIL, PHONE  FROM users
    """).fetchall()

    return render_template(
        "admin_users.html",
        name=ADMIN_USERNAME,
        mail=ADMIN_MAIL,
        users=users_data
    )


@app.route('/admin/permissions', methods=['GET'])
def admin_persmissions():
    if 'admin' not in session:
        return redirect(url_for("admin_login"))

    all_buckets = get_all_buckets()
    ab = " | ".join(all_buckets)
    ab += " |"

    return render_template(
        "admin_permissions.html",
        name=ADMIN_USERNAME,
        mail=ADMIN_MAIL,
        all_buckets=ab,
        permissions=PERMISSION
    )


@app.route('/admin/logs', methods=['GET'])
def admin_logs():
    if 'admin' not in session:
        return redirect(url_for("admin_login"))

    logs = cursor.execute("""
        SELECT *  FROM logs ORDER BY datetime(DATE) DESC
    """).fetchall()

    return render_template(
        "admin_logs.html",
        name=ADMIN_USERNAME,
        mail=ADMIN_MAIL,
        logs=logs
    )


@app.route('/admin/buckets', methods=['GET'])
def admin_buckets():
    if 'admin' not in session:
        return redirect(url_for("admin_login"))

    all_buckets = get_all_buckets()

    return render_template(
        "admin_buckets.html",
        name=ADMIN_USERNAME,
        mail=ADMIN_MAIL,
        buckets=all_buckets
    )


@app.route('/admin/bucket/<path:path>', methods=['GET'])
def admin_bucket(path):
    if 'admin' not in session:
        return redirect(url_for("admin_login"))

    rp = request.args

    paths = list(filter(None, path.split("/")))
    target_bucket = paths[0]

    if target_bucket in get_all_buckets():
        prefix = "/".join(paths[1:])
        if prefix:
            prefix += "/"

        if rp and rp.get("file"):
            download_url = generate_presigned_url(target_bucket, prefix + rp.get("file"), "get_object")
            Thread(target=save_logs, args=("admin", f"DOWNLOAD: {path}")).start()
            logging.info(f"DOWNLOAD: {path} => admin")
            return redirect(download_url)
        else:
            contents, folders = get_bucket_contents(target_bucket, prefix)
    else:
        return "<center><h1>404: Not found</h1><br></center>", 404

    current_path = ""
    list_paths = []
    for p in paths:
        current_path += f"{p}/"
        list_paths.append((p, f"{BASE_URL}/admin/bucket/{current_path}"))

    return render_template(
        "admin_bucket.html",
        name=ADMIN_USERNAME,
        mail=ADMIN_MAIL,
        paths=list_paths,
        path=path,
        contents=contents,
        folders=folders
    )


@app.route('/bucket/<path:path>', methods=['GET'])
def bucket(path):
    if 'access_code' not in session:
        return redirect(url_for("login"))

    rp = request.args
    access_code = session['access_code']
    validUser = check_user(access_code)
    if not validUser:
        session.pop('access_code', None)
        return redirect(url_for("login"))

    name, role, mail, phone = cursor.execute("""
        SELECT NAME, ROLE, MAIL, PHONE  FROM users WHERE ACCESS_CODE=?
    """, (access_code,)).fetchone()
    authorized_buckets = get_authorized_bucket(role)

    paths = list(filter(None, path.split("/")))
    target_bucket = paths[0]

    if target_bucket in authorized_buckets:
        prefix = "/".join(paths[1:])
        if prefix:
            prefix += "/"

        if rp and rp.get("file"):
            download_url = generate_presigned_url(target_bucket, prefix + rp.get("file"), "get_object")
            Thread(target=save_logs, args=(access_code, f"DOWNLOAD: {path}")).start()
            logging.info(f"DOWNLOAD: {path} => {mail}")
            return redirect(download_url)
        else:
            contents, folders = get_bucket_contents(target_bucket, prefix)
    else:
        return "<center><h1>404: Not found</h1><br></center>", 404

    current_path = ""
    list_paths = []
    for p in paths:
        current_path += f"{p}/"
        list_paths.append((p, f"{BASE_URL}/bucket/{current_path}"))

    return render_template(
        "bucket.html",
        name=name,
        role=role,
        mail=mail,
        phone=phone,
        paths=list_paths,
        path=path,
        contents=contents,
        folders=folders
    )


@app.route('/accept', methods=['GET'])
def confirm():
    rp = request.args
    if rp and rp.get('access_code'):
        access_code = rp.get('access_code')
        user_info = cursor.execute("SELECT NAME, MAIL, APPROVED FROM users WHERE ACCESS_CODE=?", (access_code,)).fetchone()

        if user_info:
            name, mail, approved = user_info
            if not approved:
                cursor.execute("UPDATE users SET APPROVED=? WHERE ACCESS_CODE=?", (True, access_code))
                conn.commit()
                Thread(target=save_logs, args=("admin", f"REGISTRATION: approved => {access_code}")).start()
                logging.info(f"REGISTRATION: approved => {mail} ({access_code})")
                Thread(
                    target=send_access_code,
                    args=(name, mail, access_code)
                ).start()
                return f"<h3>Access guaranted: {mail}</h3>", 200
            else:
                logging.error(f"REGISTRATION: already approved => {mail} ({access_code})")
                return f"<h3>User already approved: {mail}</h3>", 400
        else:
            logging.error(f"REGISTRATION: not found => {access_code}")
            return f"<h3>Access code not found</h3>", 404
    else:
        return "<h3>Bad request</h3>", 400


@app.route('/api/auth', methods=['POST'])
def auth():
    rdata = request.get_json()
    access_code = ""
    if rdata and rdata.get('access_code'):
        access_code = rdata.get('access_code')
    else:
        return make_response(
            {
                "code": 400,
                "message": "Bad request"
            },
            400
        )

    if authenticate(access_code):
        session['access_code'] = access_code
        Thread(target=save_logs, args=(access_code, "AUTHENTICATION: success")).start()
        logging.error(f"AUTHENTICATION: success => {access_code}")
        return make_response(
            {
                "code": 200,
                "message": "Logged in",
                "token": "lol"
            },
            200
        )
    else:
        Thread(target=save_logs, args=(access_code, "AUTHENTICATION: failed")).start()
        logging.error(f"AUTHENTICATION: failed => {access_code}")
        return make_response(
            {
                "code": 401,
                "message": "Invalid credentials"
            },
            401
        )


@app.route('/api/register', methods=['POST'])
def register():
    rdata = request.get_json()
    if (
        rdata and 
        rdata.get('name') and
        rdata.get('role') and 
        rdata.get('mail') and 
        rdata.get('phone')
    ):
        name = rdata.get('name')
        role = rdata.get('role')
        mail = rdata.get('mail')
        phone = rdata.get('phone')

        access_code, msg = register_user(name, role, mail, phone)
        if access_code:
            Thread(target=save_logs, args=(access_code, "REGISTRATION: waiting")).start()
            logging.error(f"REGISTRATION: waiting => {access_code}")
            Thread(
                target=send_access_request,
                args=(name, role, mail, phone, access_code)
            ).start()
            return make_response(
                {
                    "code": 200,
                    "message": "Waiting for approbation",
                    "access_code": None
                },
                200
            )
        else:
            return make_response(
                {
                    "code": 400,
                    "message": msg
                },
                400
            )

    else:
        return make_response(
            {
                "code": 400,
                "message": "Missing field"
            },
            400
        )


@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'admin' not in session and 'access_code' not in session:
        return make_response(
            {
                "code": 403,
                "message": "Forbidden"
            },
            403
        )

    try:
        if "path" not in request.args:
            return make_response(
                {
                    "code": 400,
                    "message": "Path is missing"
                },
                400
            )

        user = "admin"
        if "access_code" in session:
            user = session["access_code"]
            validUser = check_user(user)
            if not validUser:
                return make_response(
                    {
                        "code": 403,
                        "message": "Forbidden"
                    },
                    403
                )

        path = request.args.get("path")
        paths = list(filter(None, path.split("/")))
        target_bucket = paths[0]
        s3_key = '/'.join(paths[1:])
        
        put_bucket_cors(target_bucket)
        presignedURL = generate_presigned_url(target_bucket, s3_key, "put_object")
        Thread(target=save_logs, args=(user, f"UPLOAD: {path}")).start()
        logging.error(f"UPLOAD: {path} => {user}")

        return make_response(
            {
                "code": 200,
                "message": "OK",
                'url': presignedURL
            },
            200
        )
    except Exception as e:
        logging.error(f"DOWNLOAD: {e}")
        return make_response(
            {
                "code": 500,
                "message": "Internal server error"
            },
            500
        )


@app.route('/api/delete', methods=['POST'])
def delete_file():
    if 'access_code' not in session and 'admin' not in session:
        return make_response(
            {
                "code": 403,
                "message": "Forbidden"
            },
            403
        )

    try:
        if "path" not in request.form:
            return make_response(
                {
                    "code": 400,
                    "message": "Path is missing"
                },
                400
            )

        user = "admin"
        if "access_code" in session:
            user = session["access_code"]
            validUser = check_user(user)
            if not validUser:
                return make_response(
                    {
                        "code": 403,
                        "message": "Forbidden"
                    },
                    403
                )

        path = request.form.get("path")
        paths = list(filter(None, path.split("/")))
        target_bucket = paths[0]
        s3_key = '/'.join(paths[1:])
        
        s3.delete_object(
            Bucket=target_bucket,
            Key=s3_key
        )

        Thread(target=save_logs, args=(user, f"DELETE: {path}")).start()
        logging.error(f"UPLOAD: {path} => {user}")

        return make_response(
            {
                "code": 200,
                "message": "OK"
            },
            200
        )
    except Exception as e:
        logging.error(f"DELETE: {e}")
        return make_response(
            {
                "code": 500,
                "message": "Internal server error"
            },
            500
        )


@app.route('/api/bucket/create', methods=['POST'])
def create_bucket():
    if 'admin' not in session:
        return make_response(
            {
                "code": 403,
                "message": "Forbidden"
            },
            403
        )

    try:
        if "name" not in request.args:
            return make_response(
                {
                    "code": 400,
                    "message": "Bucket name is missing"
                },
                400
            )

        new_bucket_name = request.args.get("name")
        success = new_bucket(new_bucket_name)

        if success:
            Thread(target=save_logs, args=("admin", f"CREATE_BUCKET: {path}")).start()
            logging.error(f"CREATE_BUCKET: {path} => admin")

            return make_response(
                {
                    "code": 200,
                    "message": "OK"
                },
                200
            )
        else:
            return make_response(
                {
                    "code": 500,
                    "message": "Unable to create this bucket"
                },
                500
            )
    except Exception as e:
        logging.error(e)
        return make_response(
            {
                "code": 500,
                "message": "Internal server error"
            },
            500
        )


@app.route('/api/bucket/delete', methods=['POST'])
def delete_bucket():
    if 'admin' not in session:
        return make_response(
            {
                "code": 403,
                "message": "Forbidden"
            },
            403
        )

    try:
        if "name" not in request.args:
            return make_response(
                {
                    "code": 400,
                    "message": "Bucket name is missing"
                },
                400
            )

        bucket_name = request.args.get("name")
        success = remove_bucket(bucket_name)

        if success:
            Thread(target=save_logs, args=("admin", f"DELETE_BUCKET: {path}")).start()
            logging.error(f"DELETE_BUCKET: {path} => admin")

            return make_response(
                {
                    "code": 200,
                    "message": "OK"
                },
                200
            )
        else:
            return make_response(
                {
                    "code": 500,
                    "message": "Unable to delete this bucket"
                },
                500
            )
    except Exception as e:
        logging.error(e)
        return make_response(
            {
                "code": 500,
                "message": "Internal server error"
            },
            500
        )


@app.route('/api/user/delete', methods=['POST'])
def delete_user():
    if 'admin' not in session:
        return make_response(
            {
                "code": 403,
                "message": "Forbidden"
            },
            403
        )

    try:
        if "access_code" not in request.args:
            return make_response(
                {
                    "code": 400,
                    "message": "User access code is missing"
                },
                400
            )

        access_code = request.args.get("access_code")
        success, msg = remove_user(access_code)

        if success:
            Thread(target=save_logs, args=("admin", f"DELETE_USER: success => {access_code}")).start()
            logging.info(f"DELETE_USER: success => {access_code}")

            return make_response(
                {
                    "code": 200,
                    "message": "Done"
                },
                200
            )
        else:
            logging.error(f"DELETE_USER: failed => {access_code} - {e}")
            return make_response(
                {
                    "code": 500,
                    "message": "Unable to delete this user"
                },
                500
            )
    except Exception as e:
        logging.error(f"DELETE_USER: failed => {access_code} - {e}")
        return make_response(
            {
                "code": 500,
                "message": "Internal server error"
            },
            500
        )


@app.route('/api/user/info', methods=['GET'])
def user_info():
    if 'admin' not in session:
        return make_response(
            {
                "code": 403,
                "message": "Forbidden"
            },
            403
        )

    try:
        if "access_code" not in request.args:
            return make_response(
                {
                    "code": 400,
                    "message": "User access code is missing"
                },
                400
            )

        access_code = request.args.get("access_code")
        if access_code == ADMIN_USERNAME:
            return make_response(
                {
                    "code": 200,
                    "message": {
                        "name": ADMIN_USERNAME,
                        "role": "admin/validator",
                        "mail": ADMIN_MAIL,
                        "phone": "none"
                    }
                },
                200
            )

        name, role, mail, phone = get_user_info(access_code)

        if name and role and mail and phone:
            return make_response(
                {
                    "code": 200,
                    "message": {
                        "name": name,
                        "role": role,
                        "mail": mail,
                        "phone": phone
                    }
                },
                200
            )
        else:
            return make_response(
                {
                    "code": 500,
                    "message": "Error from server"
                },
                500
            )

    except Exception as e:
        return make_response(
            {
                "code": 500,
                "message": "Internal server error"
            },
            500
        )


@app.route('/api/folder/create', methods=['POST'])
def create_folder():
    if 'access_code' not in session and 'admin' not in session:
        return make_response(
            {
                "code": 403,
                "message": "Forbidden"
            },
            403
        )

    try:
        user = "admin"
        if "access_code" in session:
            user = session["access_code"]
            validUser = check_user(user)
            if not validUser:
                return make_response(
                    {
                        "code": 403,
                        "message": "Forbidden"
                    },
                    403
                )

        rdata = request.get_json()
        if "folder" not in rdata or "path" not in rdata:
            return make_response(
                {
                    "code": 400,
                    "message": "Some parameters are missing"
                },
                400
            )

        folder_name = rdata["folder"]
        path = rdata["path"]
        paths = list(filter(None, path.split("/")))
        target_bucket = paths[0]

        prefix = ""
        if len(paths) > 1:
            prefix = "/".join(paths[1:])
            if prefix:
                prefix += "/" + folder_name + "/"
        else:
            prefix = folder_name + "/"

        s3.put_object(Bucket=target_bucket, Key=prefix)
        Thread(target=save_logs, args=(user, f"CREATE_FOLDER: success => {path}/{folder_name}")).start()
        logging.info(f"CREATE_FOLDER: success => {user} : {path}/{folder_name}")

        return make_response(
            {
                "code": 200,
                "message": "Done"
            },
            200
        )

    except Exception as e:
        print(e)
        return make_response(
            {
                "code": 500,
                "message": "Internal server error"
            },
            500
        )


@app.route('/api/admin/auth', methods=['POST'])
def admin_auth():
    rdata = request.get_json()
    username = ""
    password = ""
    if rdata and rdata.get('username') and rdata.get('password'):
        username = rdata.get('username')
        password = rdata.get('password')
    else:
        return make_response(
            {
                "code": 400,
                "message": "Bad request"
            },
            400
        )

    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session['admin'] = f"{username}:{password}"
        Thread(target=save_logs, args=("admin", "AUTHENTICATION: success")).start()
        logging.error("AUTHENTICATION: success => admin")

        return make_response(
            {
                "code": 200,
                "message": "Logged in",
                "token": "lol"
            },
            200
        )
    else:
        return make_response(
            {
                "code": 401,
                "message": "Invalid credentials"
            },
            401
        )


@app.route('/logout', methods=['GET'])
def logout():
    session.pop('access_code', None)
    return redirect(url_for("login"))


@app.route('/admin/logout', methods=['GET'])
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for("admin_login"))


if __name__ == '__main__':
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users(
                ID integer primary key autoincrement,
                ACCESS_CODE text,
                NAME text,
                ROLE text,
                MAIL text,
                PHONE text,
                APPROVED bool
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs(
                DATE text,
                USER text,
                ACTION text
            )
        """)

        app.run(debug=True, host='0.0.0.0', port=SRV_PORT)

    except KeyboardInterrupt:
        logging.warning("Keyboard interruption !")

    except Exception as e:
        logging.error(e)

    finally:
        logging.warning("Exiting...")
        conn.close()