# BBN (Bot-Be-Named)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

- [BBN (Bot-Be-Named)](#bbn-bot-be-named)
  - [What is Bot-Be-Named](#what-is-bot-be-named)
  - [How to install](#how-to-install)
  - [Current Modules](#current-modules)
  - [Acknowledgements](#acknowledgements)
  - [Contributing/Issues](#contributingissues)

## What is Bot-Be-Named

A Discord bot that interoperates with Google Sheets to smoothen solving puzzle hunts. 

If you would like to add our instance of Bot-Be-Named to your server, please see below.

Bot-Be-Named is currently set up with our own configurations and environment variables, so might have assumptions that don't work for you. Please contact us if you need **a Bot invite link**, or to set up your own fork/instance of the bot.

## Inviting the Bot to your server

- Join the bot's discord server at `discord (dot) gg / x8f2ywHUky`

- There is an instance of the bot currently on that server, named `~Bot Be Named`. Click on that name - Add App - Add it to your discord server.  Note that you need "Manage Server" permission to do that.

- Use `~about` to get a quick guide to the bot, and `~startup` for all the commands that will come in very handy for you.

- In case of any problems, message us on discord or [open a new issue on Github](https://github.com/PuzzleTechHub/bot-be-named/issues/new)

## How to install your own instance

### Prerequisites - 

- [python3.12](https://realpython.com/installing-python/)

- [Git](https://github.com/git-guides/install-git)

- [Postgresql for storing data](https://www.postgresql.org/download/)

- [Pip package installer for Python](https://phoenixnap.com/kb/install-pip-windows)

Note that you may use another Python installer (instead of Pip), Host (instead of Google Cloud) or Database (instead of Supabase) but that will require you figuring out the required setup and configuation changes yourself.

### Installation

We recommend using [virtual environments](https://docs.python.org/3/tutorial/venv.html) to manage python packages for our repo. To clone the repo and install dependencies, run the following on the Command Line

```bash
#Clone the bot locally
git clone https://github.com/PuzzleTechHub/bot-be-named.git
cd bot-be-named
#Technically optional, but using virtualenv is usually a good idea
virtualenv venv -p=3.12
source venv/bin/activate
#This installs all the python dependancies the bot needs
pip install -r requirements.txt && pre-commit install

#If pre-commit is not installed, you may need to add that as well
#python -m pip install pre-commit
```

The bot uses [Supabase](https://supabase.com/) for storing data.

To run the bot locally, you will need a `.env` file which is used by [python-dotenv](https://github.com/theskumar/python-dotenv) to load `ENV` variables. Copy `.env.template` into `.env` with  

```bash
cp .env.template .env
```

and fill in the blanks in order to get the bot running. You also need to set up the Postgresql database for the bot. If you're using Supabase, follow [any regular guide](https://docs.stacksync.cloud/guides/two-way-sync-salesforce-and-postgres/create-a-postgres-database-with-supabase-free-forever) for it then copy the full URI.

Once you do all that, run

```bash
#Run this line if you haven't already
source venv/bin/activate
python bot.py
```

and the bot will run on the supplied discord token's account.

### Full GCloud instructions

To install BBN on GCloud, the full instructions is as follows.

#### Python

First, make sure you have the correct version of python. If not, install it.
```bash
# Example instructions for GCloud / Debian systems - How to install Python 3.12.3
# Following instructions on https://cloudcone.com/docs/article/how-to-install-python-3-10-on-debian-11/
sudo apt update
sudo apt install build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev libsqlite3-dev wget libbz2-dev
wget https://www.python.org/ftp/python/3.12.3/Python-3.12.3.tgz
tar -xvf Python-3.12.3.tgz
cd Python-3.12.3
sudo apt install pkg-config libgdbm-dev liblzma-dev tk-dev uuid-dev
sudo ./configure --enable-optimizations --prefix=/opt/python3.12
# or sudo ./configure --enable-optimizations --prefix=/opt/python3.12
# not sure what prefix does here
sudo make -j$(nproc)
sudo make altinstall

#Confirm if python is installed / what version it is
python3.12 --version
```

#### Aliasing
Depending on the system, you may want to also [alias](https://stackoverflow.com/questions/35435517/creating-an-alias-for-python3 for that) for simplicity, for example to point `python` to `python3.12`

If so, replace `python3.12 bot.py` in the BBN instructions to `python bot.py` or similar.

#### Other installations

```bash
#Now that you have python, install pip and git if you don't have them already
#Most systems do have both, but not GCloud
sudo apt-get update
sudo apt install -y pip git
# Now we install postgres, pre-commit, and virtualenv (Assuming you use it)
sudo apt install -y postgresql-client-common postgresql-client virtualenv pre-commit
```

#### First time installations

Everything else we have can now be handled by pip.

```bash
#Clone the bot locally
git clone https://github.com/PuzzleTechHub/bot-be-named.git
cd bot-be-named
#Technically optional, but using virtualenv is usually a good idea
virtualenv venv -p=3.12 
source venv/bin/activate
#This installs all the python dependancies the bot needs
pip install -r requirements.txt && pre-commit install

#Now Do .env stuff here. See above instructions for what to do
cp .env.template .env
nano .env
#Here - edit your .env file

#Test that your bot successfully runs!
python3.12 bot.py
```

#### Every other run on GCloud

Now that the bot is setup and successfully runs, you can keep it running from GCloud Console with something simple, like
```bash
cd bot-be-named
source venv/bin/activate
# nohup allows the bot to run while you close the SSH window, and also pastes log in a convenient spot. 
# You can use soemthing simpler than nohup if you like!
nohup python3.12 bot.py "This is BBN running" &
#That message is not necessary, I just like to include one when running
deactivate
```

If necessary, kill the previous instance of the bot running, with something like
```bash
#Search for process id of the bot
#Find the respective line that's giving you the actual run of the bot right now. The first number is your pid
ps aux | grep "python"
#Now kill the process using the pid
kill 000000000000000
#Now you can start a new instance of the bot
```

### Hosting

Once you have the bot running and basic commands (like `~help`) run properly, you can host it externally. Our instance of the bot is [hosted on Google Cloud Console](https://console.cloud.google.com/welcome).

### Other useful things

While only the above are necessary to run the code when deployed, some OSes might require additional installations to also run locally. 

For example, on Ubuntu, you also need - 
```bash
sudo apt-get install postgresql-client-common postgresql-client
```

### Using Fly.io for hosting

You can also use [Fly.io](https://dev.to/denvercoder1/hosting-a-python-discord-bot-for-free-with-flyio-3k19) for the bot hosting. Fly.io used to have a [free tier](https://fly.io/docs/about/pricing/#legacy-hobby-plan) as long as your monthly cost was below 5 USD.

You can set up automatic Continuous Deployment (CD) on Fly.io. [Follow the instructions here](https://dev.to/denvercoder1/hosting-a-python-discord-bot-for-free-with-flyio-3k19) 

### Using Heroku and Heroku Postgres for hosting.
The instructions for [hosting on Heroku](https://medium.com/@linda0511ny/create-host-a-discord-bot-with-heroku-in-5-min-5cb0830d0ff2) are linked. You may need the [heroku CLI client for hosting](https://medium.com/analytics-vidhya/how-to-install-heroku-cli-in-windows-pc-e3cf9750b4ae).

If you're using Heroku's PostgresSQL add-on instead, first [install the add-on](https://elements.heroku.com/addons/heroku-postgresql) then [set it up](https://devcenter.heroku.com/articles/heroku-postgresql) to attach your app to the Postgres. Now you can look at `Heroku - Dashboard - Resources - Add Ons` to look at the app on Heroku, and copy the URI given from Postgres add-on to the respective line in the `.env file`

If you have github + heroku, using Heroku's [Github integration](https://devcenter.heroku.com/articles/github-integration) allows you to automatically push Github pushes to also deploy on Heroku. (Using `git push` to push to both Github and Heroku)

When deploying on heroku, any variables stored in .env locally cannot be pushed to any public repos. It's advisable to use [Heroku Config Vars](https://devcenter.heroku.com/articles/config-vars) to store them.

## Current Modules

- [Admin](./modules/admin) for administrator commands
- [Archive](./modules/archive) for downloading channel/category/server contents into a Zip file
- [Custom Command](./modules/custom_command) for making custom commands in different servers
- [Discord](modules/discord) for discord utility commands (e.g. roles, stats)
- [Discord Channel Management](./modules/discord_channel_management) for cloning, creating, and moving channels 
- [Discord Role Management](./modules/discord_role_management) for managing roles and similar
- [Error Logging](./modules/error_logging) for printing error logs
- [Help](./modules/help) is an updated help command which automatically pulls docstrings for `~help`
- [Hydra](./modules/hydra) is the **NEW AND IMPROVED** "Google Sheets-Discord" commands. Currently Work in progress. 
- [Lion](./modules/lion) is the "Google Sheets-Discord" commands currently used in every Puzzle Hunt. 
- [Lookup](./modules/lookup) for Searching the internet via google and wikipedia
- [Misc](./modules/misc) for misc. random (fun) commands
- [Sheets](./modules/sheets) for working with Google Sheets during puzzlehunts
- [Time](./modules/time) for finding the time anywhere in the world

## Acknowledgements

The majority of this bot was written by [TheOriginalSoni](https://github.com/TheOriginalSoni) and [Kevslinger](https://github.com/kevslinger), with significant contributions from [Pete Cao](https://github.com/petecao) for the Lion module.

There are multiple repositories and code that BBN borrowed code from, most notably [Jonah Lawrence](https://github.com/DenverCoder1) and his [Professor Vector](https://github.com/DenverCoder1/professor-vector-discord-bot). Further info is included in respective modules.

## Contributing/Issues

If you find any issues, bugs, or improvements, please feel free to open an issue and/or pull request! Thank you!

Feel free to join our discord at `discord (dot) gg / x8f2ywHUky` with any questions you may have! If you are unable to join the discord, contact [TheOriginalSoni](https://github.com/TheOriginalSoni) (`@talesfromtim` on discord). 