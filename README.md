# S3 Browser


S3 Browser is a simple and lightweight Python Flask based, web application that browse your AWS S3 *without* creating IAM users in you AWS Console.  
You just have to create an `AWS ACCESS KEY` with an `AWS SECRET KEY` that have S3 Access **ONLY** in your AWS Account.  
This project can be used in case of shared storage or file sharing.  
It has user frindly interface with administrator back office.  

## How it works ?
- First, users must ask for access to the Web application, so they must register by clicking on **Register** button.  
They enter their informations and after that, an email notification is sent to the administrator asking for validation.  
When the administrator confirms an user registration request, the user receive an email notification with his *ACCESS CODE*.  
- The administrator can login at */admin/login* and list all users or delete them. Only, an administrator is allowed to create and delete Bucket.  
He can see all actions made on the storage, who deleted a file, who where uploading a file, who delete a file, ...  

## Install & run it
1. Clone this repo with:
	 ```
	 git clone https://github.com/dijey099/s3-browser.git
	 ```

2. Enter into the directory
	 ```
	 cd s3-browser
	 ```

3. Set your environment
	 - Edit .env
	 ```
	 cp .env.example .env
	 nano .env
	 ```
	 - Set these fields correctly:
	 `ENVIRONMENT` : this set log level to DEBUG when set to *dev* and INFO when set to *prod*  
	 `SERVER_IP` : listen adress for the server. Set it to `0.0.0.0` to listen on all adress.  
	 `SERVER_PORT` : listen port for the server.  
	 `ADMIN_USERNAME` : admin username used for Back Office access.  
	 `ADMIN_PASSWORD` : admin password used for Back Office access.  
	 `ADMIN_MAIL` : admin mail address where to send notification about new user access request.  
	 `BASE_URL` : url used to access the Web Application. (It's recommended to use the server IP address or an URL that points to the server)  
	 `MAIL_USER` : sender mail address. Use Gmail mail address if possible.  
	 `MAIL_PASSWORD` : sender mail passowrd. You should create an *Application Password* in Gmail account settings, instead of using your Gmail password.  
	 `AWS_DEFAULT_REGION` : your AWS region.  
	 `AWS_ACCESS_KEY_ID` : your AWS ACCESS KEY  
	 `AWS_SECRET_ACCESS_KEY` : your AWS SECRET KEY  

	 - Save it:
	 Hit `Ctrl` + `X` , then `Y` and finally `Enter`

4. Update Groups permissions
   This file defines who has access to a bucket.
   ```
   nano group_permissions.json
   ```
   Then save it.

5. And then choose one of the following options:

### Using docker (most recommanded)
> [!NOTE]
> Make sure you have Docker engine installed on your OS
> If you wish to install Docker on Linux, copy and run `curl -sSL https://get.docker.io | sh`  
> If you are facing an issue (like in Kali Linux) refer [here](https://docs.docker.com/engine/install/)

- Build your image
	```
	docker build -t s3-browser .
	```

- Run your container
	```
	docker run -d --restart unless-stopped -p 4444:4444/tcp -v /full/path/to/project/data:/s3-browser/data --name s3-browser s3-browser
	```

- Check it
	```
	docker ps
	```

### Using simple Python
> [!NOTE]
> Make sure you have Python 3 installed.  
> If you want to use project level Python environment, install **Python venv** with `pip3 install virtualenv`
> and create a new environment using `python3 -m venv .venv` and activate the new created environment with `source .venv/bin/activate`

- Install depandencies
	```
	pip3 install -r requirements.txt
	```

- Run it
	Using Python binary
	```
	python3 s3b.py
	```

	Using Gunicorn binary
	```
	gunicorn --access-logfile /path/log//requests.log --log-file /path/log/app.log -b 0.0.0.0:4444 s3b:app
	```

### Using systemd daemon
> [!NOTE]
> Make sure you have Python 3 installed.

> [!WARNING]
> You must use system wide python environment

- Install depandencies
  ```
  pip3 install -r requirements.txt
  ```

- Create systemd file
  Open new file
  ```
  nano /etc/systemd/system/s3b.service
  ```

  Paste the following text into the file
  ```
  [Unit]
  Description = S3 - Browser
  Documentation = https://github.com/dijey099/s3-browser
  After = network.target

  [Service]
  Type = simple
  LimitCORE=infinity
  WorkingDirectory = /path/to/s3b
  ExecStart = /usr/local/bin/gunicorn \
                  --workers 2 \
                  --threads 5 \
                  --access-logfile /path/log//requests.log \
                  --log-file /path/log/app.log \
                  --timeout 780 \
                  -b 0.0.0.0:4444 \
                  s3b:app
  User = root
  SyslogIdentifier = s3-browser

  [Install]
  WantedBy = multi-user.target
  ```

- Reload systemd daemon
  ```
  sudo systemctl daemon-reload
  ```

- Start the service
  ```
  sudo systemctl enable --now sb3
  ```