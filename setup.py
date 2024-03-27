import os

os.system('rm db.sqlite3')
os.system('rm -rf pourover/__pycache__')
os.system('rm -rf pourover/migrations')
os.system('rm -rf webapps/__pycache__')
os.system('python3 manage.py makemigrations')
os.system('python3 manage.py migrate')
os.system('python3 manage.py migrate --run-syncdb')