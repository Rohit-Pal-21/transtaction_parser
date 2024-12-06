# XML TRANSACTION TO .XLSX COVERTER


## PreRequisites
"""
Make sure that the python and curl is installed in your system

copy the repository from https://github.com/Rohit-Pal-21/transtaction_parser.git

"""

## SETUP
"""
cd into the project directory

make a veritual environment by python3 -m virtualenv  ./venv

activate the virtual environment by using source ./venv/bin/activate in linux or Mac 
for windows use ./venv/Scripts/activate


then 

pip install -r requirements.txt

python manage.py makemigrations
pyhton manage.py migrate

python manage.py runserver

"""

## Testing 
"""
curl --location 'http://127.0.0.1:8000/api/convert/' --header 'Content-Type: multipart/form-data' --form 'file=@"/FILEPATH/Input.xml"' --output Result.xlsx


befor hitting the curl REPLACE the FILEPATH with actual file path

"""