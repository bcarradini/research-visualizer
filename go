[[ -z $VIRTUAL_ENV ]] && printf "\n*** run within pipenv shell\n" && exit 1

printf "\n\n\nrunning\n"
echo "    gunicorn project.wsgi -b localhost:5000 --reload"
echo
gunicorn project.wsgi -b localhost:5001 --reload
