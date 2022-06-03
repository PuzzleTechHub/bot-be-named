# Hogwarts Ghost Bot

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Hogwarts Ghost Bot is a bot for allowing users to create confessional channels in the Hogwarts Ghost Discord server.

This bot is a fork of [bot-be-named](https://github.com/kevslinger/bot-be-named) to make use of its archiving features.

## How to install your own instance

### Prerequisites

- [python3.8 or newer](https://realpython.com/installing-python/)

- [Git](https://github.com/git-guides/install-git)

- [Postgresql for storing data](https://www.postgresql.org/download/)

- [Heroku CLI client for hosting](https://medium.com/analytics-vidhya/how-to-install-heroku-cli-in-windows-pc-e3cf9750b4ae)

- [Pip package installer for Python](https://phoenixnap.com/kb/install-pip-windows)

Note that you may use another Python installer (instead of Pip), Host (instead of Heroku) or Database (instead of Postgresql) but that will require you figuring out the required setup and configuation changes yourself.

### Installation

We recommend using [virtual environments](https://docs.python.org/3/tutorial/venv.html) to manage python packages for our repo. To clone the repo and install dependencies, run the following on the Command Line

```bash
#Clone the bot locally
git clone https://github.com/DenverCoderOne/hogwarts-ghosts.git
cd hogwarts-ghosts
virtualenv .venv
# Activate the virtual environment
source .venv/bin/activate # Linux
source .venv\Scripts\activate # Windows
#This installs all the python dependancies the bot needs
pip install -r requirements.txt && pre-commit install
```

The bot uses [Heroku Postgres](https://www.heroku.com/postgres) for storing data.

To run the bot locally, you will need a `.env` file which is used by [python-dotenv](https://github.com/theskumar/python-dotenv) to load `ENV` variables. Copy `.env.template` into `.env` with  

```bash
cp .env.template .env
```

and fill in the blanks in order to get the bot running. You also need to set up the Postgresql database for the bot using Heroku's PostgresSQL add-on (To be finished). First [install the add-on](https://elements.heroku.com/addons/heroku-postgresql) then [set it up](https://devcenter.heroku.com/articles/heroku-postgresql) to attach your app to the Postgres. Now you can look at `Heroku - Dashboard - Resources - Add Ons` to look at the app on Heroku, and copy the URI given from Postgres add-on to the respective line in the `.env file`

Once you do all that, run


```bash
source venv/bin/activate
python bot.py
```

and the bot will run on the supplied discord token's account.

### Hosting

Once you have the bot running and basic commands (like `~help`) run properly, you can host it externally. Our instance of the bot is [hosted on Heroku](https://medium.com/@linda0511ny/create-host-a-discord-bot-with-heroku-in-5-min-5cb0830d0ff2)


### Other useful things

If you have github + heroku, using Heroku's [Github integration](https://devcenter.heroku.com/articles/github-integration) allows you to automatically push Github pushes to also deploy on Heroku. (Using `git push` to push to both Github and Heroku)

When deploying on heroku, any variables stored in .env locally cannot be pushed to any public repos. It's advisable to use [Heroku Config Vars](https://devcenter.heroku.com/articles/config-vars) to store them.

## Current Modules

- [Admin](./modules/admin) for administrator commands
- [Archive](./modules/archive) for downloading channel/category/server contents into a Zip file
- [Channel Management](./modules/channel_management) for cloning, creating, and moving channels - [Cipher Race](modules/cipher_race) Race against the clock decoding ciphers!
- [Confessional Request](./modules/confessional_request) for allowing users to create temporary channels in a category
- [Custom Command](./modules/custom_command) for making custom commands in different servers
- [Discord](modules/discord) for discord utility commands (e.g. roles, stats)
- [Error Logging](./modules/error_logging) for printing error logs
- [Help](./modules/help) is an updated help command which automatically pulls docstrings for `~help`
- [Lookup](./modules/lookup) for Searching the internet via google and wikipedia
- [Misc](./modules/misc) for misc. random (fun) commands
- [Music Race](./modules/music_race/) Help! Our tunes have been sawed apart and put back incorrectly!
- [Perfect Pitch](./modules/perfect_pitch) Become a composer and write tunes in mp4
- [Role Management](./modules/role_management) for managing roles and similar
- [Solved](./modules/solved) for marking Discord Channels as solved, backsolved, solvedish etc.

Note: the main purpose of this bot is for Confessional Requests and Archiving.

The other features have not been tested in this bot and may not work as expected.
