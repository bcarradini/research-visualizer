# research-visualizer
Visualize research topics across [Scopus subject area classifications](https://service.elsevier.com/app/answers/detail/a_id/14882/supporthub/scopus/~/what-are-the-most-frequent-subject-area-categories-and-classifications-used-in/).

## Dependencies
- You have a GitHub account a
- PostgreSQL 12, or compatible
- Python 3.10
- pip3
- TODO: npm, v-network-graph

## Installation
These installation instructions were written for macOS but should be roughly applicable on other Unix-based operating systems.

### Install Dependencies

**Install or Update [Homebrew](https://brew.sh/)**
(_Install_)
ref: https://mac.install.guide/homebrew/3.html
```sh
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Add Homebrew to your PATH in ~/.zprofile
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```
_(Update)_
```sh
$ brew update
```
**Use Homebrew to install dependencies**
Install Python 3.10, PostgreSQL 12, and other dependencies
```sh
# Install dependencies
$ brew install python@3.10 postgresql@12 redis openssl pipenv gh
$ brew services start postgresql@12
$ brew services start redis

# Add Postgresql 12 to your PATH in ~/.zshrc
echo 'export PATH="/opt/homebrew/opt/postgresql@12/bin:$PATH"' >> ~/.zshrc

# Apply edited ~/.zshrc directives without having to restart your terminal
source ~/.zshrc
```
_Note_: `gh` is the GitHub CLI, which you may or may not already have installed. If you're already set up to interact with github.com from your command line, great! If not, use `gh auth login` and follow the prompts to login in to your GitHub account so that you can clone the source code repository.

**Clone Repository**
Navigate to the directory on your local machine where you want to house the source code repository. Clone the source code repository into this location using `git clone`. See the above **Note** if you're having trouble authenticating with GitHub.
```
git clone https://github.com/bcarradini/research-visualizer.git
```

**Create PSQL Database**
Run PSQL command to create a local database.
```
$ createdb resviz
```

**Create Python Virtual Environment**
Navigate to the root of the local repository and create Python virtual environment.
```
# Install pipenv
pip3 install pipenv

# Create Python 3 virtual environment
pipenv --python 3.10

# Activate virtual environment
pipenv shell

# From within the activated virtual environment, install dependencies
pipenv install
```






## **Setup**

### **Get Scopus API Key and Insttoken**
- TODO

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
$ brew services start redis
$ gunicorn project.wsgi -b localhost:5001 --reload
```
IMPORTANT: The Scopus API key must be set up to allow requests from localhost:5000
