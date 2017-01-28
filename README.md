This is a repository containing Washington State campaign finance data analysis and presentation, from KUOW.

## Starting webserver

0.  Create EC2 instance with Ubuntu server AMI and/or log in
1.  Make a directory to host the code: mkdir ~/code and cd into it
2.  Install git: sudo apt-get install git
3.  Create ~/.bash_profile and put the following inside:
  eval `ssh-agent -s`
  ssh-add ~/.ssh/id_rsa
4.  source ~/.bash_profile
5.  ssh-keygen
6.  scp key file into instance; example using fleet script:
  fleet webserver scpsend ~/kuow_keys.pem /home/ubuntu/kuow_keys.pem
7.  Add the keys to the keychain: ssh-add ~/kuow_keys.pem
8.  Attach machine-specific SSH key to IAM role; first, grab the key by copying output of: 
  cat ~/.ssh/id_rsa.pub
9.  Add copied contents of public key to relevant IAM user at https://console.aws.amazon.com/iam/home
10. Get the key ID from the above URL corresponding to the new key, and create a file at ~/.ssh/config with the following:
Host git-codecommit.*.amazonaws.com
  User <KEYID>
  IdentityFile ~/.ssh/id_rsa
11. Clone the repo
12. sudo apt-get update && sudo apt-get install python-pip
13. sudo pip install virtualenv && sudo pip install virtualenvwrapper
14. Append the following to ~/.bash_profile:
export WORKON_HOME=$HOME/.virtualenvs
source /usr/local/bin/virtualenvwrapper.sh
15. source ~/.bash_profile
16. mkvirtualenv campfin
17. sudo apt-get install libpq-dev python-dev
18. CD into campfin and run pip install -r requirements.txt
19. Append the following into ~/.bash_profile:
export AWS_SECRET_ACCESS_KEY=<ACCESS_KEY>
export AWS_ACCESS_KEY_ID=<KEY_ID>
export DJANGO_SETTINGS_MODULE=campfin.settings.staging
20. mkdir ~/logs
21. sudo mkdir /var/www
21. sudo mkdir /var/www/campfin_data
22. sudo chmod 777 /var/www/campfin_data
23. python manage.py collectstatic
24. Associate webserver instance with elastic IP (may require you to log out and back in)
25. sudo apt-get install nginx
26. sudo cp http/campfin /etc/nginx/sites-available/campfin
27. sudo ln -s /etc/nginx/sites-available/campfin /etc/nginx/sites-enabled/campfin
28. http/runserver.sh
29. sudo service nginx start

### Optional steps for workers

1. sudo apt-get install language-pack-en-base
2. sudo dpkg-reconfigure locales
3. sudo add-apt-repository ppa:ubuntugis/ubuntugis-unstable && sudo apt-get update
4. sudo apt-get install gdal-bin
