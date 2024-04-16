import os

os.system('rm db.sqlite3')
os.system('rm -rf pourover/__pycache__')
os.system('rm -rf pourover/migrations/__pycache__')
os.system('rm -rf webapps/__pycache__')
os.system('python3 manage.py makemigrations')
os.system('python3 manage.py migrate')
os.system('python3 manage.py migrate --run-syncdb')
os.system(f'python3 manage.py loaddata pourover/fixtures/default_profiles.json')
