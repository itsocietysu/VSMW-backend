#!/usr/bin/env bash

#python3.6 ./server.py --profile $PROFILE
uwsgi --http :2000 --wsgi-file ./server_prod.py --callable wsgi_app 
#>output.log 2>error.log
