FROM python:3.12.10-alpine

ADD . /s3-browser
WORKDIR /s3-browser

RUN pip install --no-cache-dir -r requirements.txt

CMD ["gunicorn", "--access-logfile", "/s3-browser/data/requests.log", "--log-file", "/s3-browser/data/app.log", "-b", "0.0.0.0:4444", "s3b:app"]