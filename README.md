# research-visualizer
Visualize research topics across [Scopus subject area classifications](https://service.elsevier.com/app/answers/detail/a_id/14882/supporthub/scopus/~/what-are-the-most-frequent-subject-area-categories-and-classifications-used-in/).

## Prerequisites
- You have a GitHub account a
- You have a Scopus API Key and Insttoken **TODO: write instructions**

## Installation
These installation instructions were written for macOS but should be roughly applicable on other Unix-based operating systems.

### Install or Update [Homebrew](https://brew.sh/)
**Install:**
ref: https://mac.install.guide/homebrew/3.html
```sh
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Add Homebrew to your PATH in ~/.zprofile
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```
**Update:**
```sh
$ brew update
```

### Install backend dependencies
Use Homebrew to install Python 3.10, PostgreSQL 12, and other backend dependencies:
```
# Install dependencies
$ brew install python@3.10 postgresql@12 gdal redis openssl pipenv gh
$ brew services start postgresql@12
$ brew services start redis

# Add Postgresql 12 to your PATH in ~/.zshrc
echo 'export PATH="/opt/homebrew/opt/postgresql@12/bin:$PATH"' >> ~/.zshrc

# Apply edited ~/.zshrc directives without having to restart your terminal
source ~/.zshrc
```
_Note_: `gh` is the GitHub CLI, which you may or may not already have installed. If you're already set up to interact with github.com from your command line, great! If not, use `gh auth login` and follow the prompts to login in to your GitHub account so that you can clone the source code repository.

### Install Node.js and npm
First, install nvm (node version manager):
```
# Install nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.1/install.sh | bash

# Set NVM_DIR variable
export NVM_DIR="$HOME/.nvm"

# Load nvm
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
```
Close your terminal session and open a new one, then use nvm to install node:
```
# Install node 12.7.0
nvm install node 12.7.0

# Add `nvm use` directive to ~/.zshrc
echo 'nvm use 12.7.0' >> ~/.zshrc

# Apply edited ~/.zshrc directives without having to restart your terminal
source ~/.zshrc
```

### Install frontend dependencies
Use npm to install frontend dependencies:
```
npm install
```

### Create PSQL Database
Run PSQL command to create a local database:
```
$ createdb resviz
```

### Clone Source Code Repository
Navigate to the directory on your local machine where you want to house the source code repository. Clone the source code repository into this location using `git clone`. See the above note about `gh` if you're having trouble authenticating with GitHub.
```
git clone https://github.com/bcarradini/research-visualizer.git
```

### Create Python Virtual Environment
Navigate to the root of the local source code repository and create Python virtual environment.
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
**Create Local Settings**
Navigate to the root of the local source code repository and create a file called `local_settings.py` inside of the `project` directory. This is a _secret file_ that will not be tracked by source code versioning. It is used to store secret keys and should look like this, where `YOUR_SCOPUS_API_KEY` and `YOUR_SCOPUS_INST_TOKEN` are placeholders:
```
import os

os.environ['SCOPUS_API_KEY'] = 'YOUR_SCOPUS_API_KEY'
os.environ['SCOPUS_INST_TOKEN'] = 'YOUR_SCOPUS_INST_TOKEN'
```
_Note_: Both the Scopus API Key and the Insttoken are expected to be 32-character hex strings (e.g. "0123456789ab4567cdef0123456789yz")

## **Run**
To run locally, you can use the shortcut, `./go`, which is a wrapper for:
```
$ gunicorn project.wsgi -b localhost:5001 --reload
```
