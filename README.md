# research-visualizer
Visualize research topics across [Scopus subject area classifications](https://service.elsevier.com/app/answers/detail/a_id/14882/supporthub/scopus/~/what-are-the-most-frequent-subject-area-categories-and-classifications-used-in/).

## **Dependencies**
- PostgreSQL 12.4, or compatible
- Python 3.7.10
- pip3
- heroku cli (optional)
- TODO: npm, v-network-graph

## **Setup**

### **Get Scopus API Key and Insttoken**
- TODO

### **Clone Repository**
Clone the repository onto your local machine
```
git clone https://github.com/bcarradini/research-visualizer.git
```

### **Create PSQL Database**
Run PSQL command to create a local database
```
$ createdb resviz
```

### **Create Virtual Environment**
Navigate to the root of the local repository and create Python virtual environment
```
# Update pipenv by pulling directly for its master branch, which includes important bugfixes
$ pip3 install git+https://github.com/pypa/pipenv.git@master
# Create Python 3 virtual environment
$ pipenv --three
# Activate virtual environment
$ pipenv shell
# Install dependencies
# pipenv install
```

## **Run**
To run locally:
```
gunicorn project.wsgi -b localhost:5000 --reload
```
IMPORTANT: The Scopus API key must be set up to allow requests from localhost:5000
