#! /bin/bash

python pip install -r requirements/local.txt
echo '##### Checking for new changes #####'
python manage.py makemigrations
echo '##### Migrating changes #####'
python manage.py migrate
echo ''
echo '##### Starting server, double crtl+c to stop #####'
echo ''
python manage.py runserver
