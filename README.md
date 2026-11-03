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

- Use `~about` to get a quick guide to the bot, and `~info` for all the commands that will come in very handy for you.

- In case of any problems, message us on discord or [open a new issue on Github](https://github.com/PuzzleTechHub/bot-be-named/issues/new)

## How to install your own instance

### Running your own Bot Be Named for contributing

Welcome! Once you've followed these instructions, you should be good to start contributing.

#### Before you start

| You need | Cost |
| --- | --- |
| [Python 3.12+](https://www.python.org/downloads/) and [Git](https://git-scm.com/downloads) | Free |
| A [Discord account](https://discord.com/register) and a [test server you own](https://support.discord.com/hc/en-us/articles/204849977-How-do-I-create-a-server) | Free |
| A personal [Google account](https://accounts.google.com/signup) | Free for this use |
| A [Postgres database](https://www.postgresql.org/download/) (see [step 4](#4-set-up-a-database)) (we use [Supabase](https://supabase.com/)) | Free tier |
| A [GeoNames account](https://www.geonames.org/login) (optional, only for some functions) | Free |

Be sure to not commit `.env` or `client_secret.json`. Both are already in `.gitignore`.

#### 1. Clone the repo and install requirements

Try not to clone the repo in a cloud storage directory.

```bash
git clone https://github.com/PuzzleTechHub/bot-be-named.git
cd bot-be-named

# Make a virtual environment with Python 3.12
python3.12 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

# Install pre-commit hooks, like ruff
pip install pre-commit
pre-commit install

cp .env.template .env           # Windows: copy .env.template .env
```

Debian and Ubuntu spit the venv/pip support into separate packages, so if creating the venv raises an `ensurepip` error, run `sudo apt install python3.12-venv` first.

You'll fill in `.env` in step 5.

#### 2. Create the Discord bot

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications), and make a **New Application**.
2. Open the **Bot** tab. Click **Reset Token**, copy the token and save it. You'll need it later. If you forget the token, reset and copy the new one.
3. On the same tab, under **Privileged Gateway Intents**, turn on **Server Members Intent** and **Message Content Intent**, then save.
4. Open the **Installation** tab. Make sure **Guild Install** is on, add the `bot` scope to the guild install, and give it **Administrator** for your private test server.
5. Open the install link, pick your test server and authorise it. Don't worry, the bot will appear offline, until Step 6.
6. In Discord (not the Developer Portal), turn on **Developer Mode** (User Settings -> Advanced), right-click your own name and **Copy User ID**. That's `BOT_OWNER_DISCORD_ID`.

#### 3. Create the Google service account

BBN edits its sheets through a service account: essentially its own email and credentials. Use a personal account while logged in to Google Cloud.

1. In the [Google Cloud console](https://console.cloud.google.com/), create a new project (e.g. `bbn-dev`) and make sure it's selected at the top.
2. Go to **APIs & Services -> Library** and enable both the **Google Sheets API** and the **Google Drive API**.
3. Go to **IAM & Admin -> Service Accounts -> Create service account**. You'll only need to give it a name.
4. Open the new account, go to the **Keys** tab, click **Add key -> Create new key -> JSON**. A file should download.
5. Rename it to `client_secret.json` and put it in the root of your `bot-be-named` folder, next to `bot.py`. 
6. Copy the `client_email` from that file (it ends in `iam.gserviceaccount.com`). Your tests sheet must give this email **Editor** permissions, the same way you'd share with a person, or you can set the sheet's general access to "Anyone with the link" as Editor.

#### 4. Set up a database

Pick one. The bot creates its tables on first start, so an empty database is all you need.

**Option A: Supabase** (recommended, what we use in prod)

1. Create a free project at [supabase.com](https://supabase.com/) and save the database password it asks for.
2. Click **Connect** at the top of the project, use "Direct Connection" if your network is configured with IPv6. Otherwise, use "Session Pooler".
3. Scroll down and copy the Connection String. When we paste it into `.env` in the next step, replace `[YOUR-PASSWORD]` with your actual project password. A `postgres://` prefix is fine.

**Option B: local Postgres with Docker** (works offline)

```bash
docker run --name bbn-db -e POSTGRES_PASSWORD=bbn -p 5432:5432 -d postgres:16
```

Then `DATABASE_URL = postgresql://postgres:bbn@localhost:5432/postgres`. Start it again later with `docker start bbn-db`.

#### 5. Fill in `.env`

Open the `.env` you copied in step 1.

| Line | Required? | What goes there |
| --- | --- | --- |
| `DISCORD_TOKEN` | Yes | The bot token from step 2. |
| `BOT_OWNER_DISCORD_ID` | Yes | Your Discord user ID from step 2. This is how the bot will check if you're the owner. |
| `DATABASE_URL` | Yes | The connection string from step 4. |
| `GEOPY_USERNAME` | No | Not required. A [GeoNames](https://www.geonames.org/login) username, with free web services enabled on its account page. Functions like `~time` won't work without this. |
| `WEBHOOK_URL` | No | Not required. A Discord webhook that gets a line for every command used. To add one: in your test server, **Edit Channel -> Integrations -> Webhooks -> New Webhook -> Copy Webhook URL**, and paste it here in quotes. Leave as `""` to skip; the console then prints "Webhook failed" after each command, which is harmless |
| `type` to `client_x509_cert_url` | No | Unneeded. `client_secret.json` from step 3 covers this. |

#### 6. Run it and test it

```bash
source venv/bin/activate        # Windows: venv\Scripts\activate
python bot.py
```

It's working when it prints `has connected to the following guild: <your server> ... with prefix ~` and the bot shows online. Stop it with Ctrl+C. Startup currently prints your full `DATABASE_URL`, password included, so don't paste your startup logs anywhere public.

#### Try this

**Try** `~help` and `~about` in your test server to see if the bot is awake.

**then, try these common commands**:

1. Ask in the BBN Discord for the puzzle sheet template, make your own copy, and share it with the service account.
2. Run `~addperm Solver @everyone`, so you can use the solver commands.
3. Create a category `Test Hunt`, an archive category `Test Hunt Archive`, and a channel `#test-bot-spam` inside `Test Hunt`.
4. In `#test-bot-spam`, run `~tetherhydra <your sheet link>`.
5. Run `~chanhydra "Test Puzzle" "https://example.com"`. You should get a new channel, a new tab and a new Overview row.
6. In the new channel, run `~solvedhydra "ANSWER"`, then `~mtahydra` to move it to the archive.

After completing this successfully, congratulations! You're now ready to contribute.

Feel free to ask anythingin the Discord. Try not to send any secrets, though.

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

The majority of this bot was written by [TheOriginalSoni](https://github.com/TheOriginalSoni).

Significant portions of the bot were written by [Kevslinger](https://github.com/kevslinger) (early modules), [Pete Cao](https://github.com/petecao) (Lion module) and [c12](https://github.com/aleaffallingintothedarkness-c12) (Hydra module).

There are multiple repositories and code that BBN borrowed code from. Further info is included in respective modules.

## Contributing/Issues

See [Contributing.MD](/.github/CONTRIBUTING.md) for the full contribution guidelines. No AI, be on discord, be a human. 

Join the discord for any issues, improvements or answers. **If you are unable to join the discord, contact [TheOriginalSoni](https://github.com/TheOriginalSoni) (`@talesfromtim` on discord).**
