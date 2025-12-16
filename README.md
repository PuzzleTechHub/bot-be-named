# BBN (Bot-Be-Named)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

- [BBN (Bot-Be-Named)](#bbn-bot-be-named)
  - [What is Bot-Be-Named](#what-is-bot-be-named)
  - [How to install](#how-to-install)
  - [Current Modules](#current-modules)
  - [Acknowledgements](#acknowledgements)
  - [Contributing/Issues](#contributingissues)

### What is Bot-Be-Named?

Bot Be Named (BBN) is a powerful Discord bot designed to make puzzle tracking and server management easier — especially during puzzle hunts like Puzzle Boat!

Key features:
- Automatically creates threads, Google Sheet tabs, and entries for new puzzles with one command (~threadlion "Puzzle Name")
- Marks puzzles as solved
- Integrates deeply with Google Sheets for real-time tracking
- Includes many helpful modules:
  • Admin — administrator commands
  • Archive — download channel contents as ZIP
  • Sheets — advanced puzzle sheet management
  • Lion — improved Google Sheets-Discord integration
  • Hydra — the newest puzzle-solving tools
  • And more (full list below!)

Perfect for puzzle teams who want less manual work and more solving time ♡

Ready to add BBN to your server? See "Inviting the Bot to your server" below.


### Inviting the Bot to your server

Want to add Bot-Be-Named to your Discord server? It's easy! ♡

1. Join the bot's support server:  
   https://discord.gg/x8f2ywHUky

2. In that server, you'll find an instance named **~Bot Be Named**.  
   Click its name → **Add App** → **Add to your server**.  
   (Note: You'll need "Manage Server" permission on your own server.)

3. Once added, use `~about` for a quick guide to the bot, and `~startup` for all available commands.

Having trouble? Message us on the support server or  [open a new issue on Github](https://github.com/PuzzleTechHub/bot-be-named/issues/new) — we're happy to help!

## How to install your own instance

Want to run Bot-Be-Named on your own server or computer? It's totally doable — even if you're new to this! ♡

We'll use a **virtual environment** (highly recommended) to keep everything neat.

### Prerequisites - 

- [python3.12](https://realpython.com/installing-python/) (or newer)

- [Git](https://github.com/git-guides/install-git)

- [Postgresql for storing data](https://www.postgresql.org/download/) or [Supabase for easier cloud option](https://supabase.com/)

- [Pip package installer for Python](https://phoenixnap.com/kb/install-pip-windows)

**Note**: You can use alternatives (different host, database, etc.), but you'll need to adjust the setup yourself.

#### Installation steps

```bash
1. **Clone the repository**  
   Open your terminal/command line and run:
git clone https://github.com/PuzzleTechHub/bot-be-named
cd bot-be-named

2. **(Recommended) Create a virtual environment**
virtualenv venv -p3.12
source venv/bin/activate   # On Windows: venv\Scripts\activate

3. **Install dependencies**
pip install -r requirements.txt

4. **(If needed) Install pre-commit hooks**
python -m pip install pre-commit
pre-commit install

5. **Set up your environment file**  
Copy the template and fill in your secrets:
cp .env.template .env
nano .env   # or use any text editor
Add your Discord token, Google Sheets credentials, database URL, etc.

6. **Run the bot**
python bot.py
```

The bot will start using the Discord token you provided.

#### Using Supabase (easier database option)
If you're using Supabase instead of local PostgreSQL, just follow any standard Supabase setup guide and put the connection URL in your `.env` file.

#### Questions?
Feel free to ask in our Discord support server or [open a new issue on Github](https://github.com/PuzzleTechHub/bot-be-named/issues/new) — we're happy to help!

### Running on Google Cloud (Advanced)

Want to host Bot-Be-Named on Google Cloud for 24/7 uptime? This is for experienced users — it requires a Google Cloud account and some setup.

The full instructions are a work in progress, but here's the basic flow:

```bash
1. Set up a Google Cloud project and enable billing.
2. Use Google Cloud Console or gcloud CLI to deploy.
3. Follow standard Python app deployment guides for Cloud Run or App Engine.
4. Configure your `.env` file with Supabase/PostgreSQL details and Discord token.
5. Deploy with continuous integration if desired.
```

For detailed steps, check official Google Cloud docs or ask in our Discord support server!

**Beginners**: We recommend starting with local installation or Fly.io/Heroku (see below) — they're much easier ♡

#### Python

First, make sure you have the correct version of python. If not, install it.
```bash
First, make sure you have the correct version of Python installed (3.12 or newer).

If not, download it from https://www.python.org/downloads/

**Quick check**: Open terminal/command prompt and run:
python3.12 --version
(or `python --version` on Windows)

No complicated sudo commands needed for most users — just install from the official site!

Once Python is ready, continue with the "Installation" steps above.
```

#### Aliasing (Optional — for convenience)
On some systems, you might need to type `python3.12` instead of just `python`.  
To make it simpler, you can create an "alias" — a shortcut so `python` points to Python 3.12.

```bash
#### On Linux/Mac:
Add this line to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.):
alias python=python3.12

Then restart your terminal or run `source ~/.bashrc`.
```
```bash
#### On Windows:
You can use the Python Launcher (usually installed automatically) — just type `py -3.12` instead of `python3.12`.

For a permanent alias on Windows, see this guide:  
https://stackoverflow.com/questions/3543517/creating-an-alias-for-python3-for-that

After setting an alias, you can replace `python3.12` with `python` in all the bot commands (like `python bot.py`).
```

Not sure if you need this? Try running `python --version` first — if it shows 3.12, you're good to go without aliasing! ♡

#### Other installations

```bash
#### Other packages you might need
Most systems already have these, but if you get errors, install them:
sudo apt-get update
sudo apt install -y pip git

For PostgreSQL (if not using Supabase):
sudo apt install -y postgresql-
(Replace with your system's package manager if not on Ubuntu/Debian.)
```

#### First time installations

Everything else is handled by pip — no extra steps needed for most users!

```bash
After cloning and installing requirements:
1. Copy the environment template:
cp .env.template .env

2. Edit `.env` with your secrets (Discord token, database URL, etc.):
nano .env   # or use any text editor

3. Test the bot:
python3.12 bot.py
```

If you see errors about missing packages, just install them with pip.

Having trouble? Join our Discord support server or [open a new issue on Github](https://github.com/PuzzleTechHub/bot-be-named/issues/new) — we're happy to help!

### Running the bot continuously on Google Cloud (Advanced)

Once the bot is set up and running locally, you can deploy it to Google Cloud for 24/7 uptime.

This is for experienced users — it requires a Google Cloud account with billing enabled.

```bash
Basic steps:
1. Set up a Google Cloud project.
2. Use Cloud Run, App Engine, or Compute Engine to deploy.
3. Configure your `.env` file on the server.
4. Follow official Google Cloud guides for Python apps.
```

Our instance is hosted on Google Cloud Console, but we recommend easier alternatives below for beginners ♡

### Hosting options (Easier alternatives)

Want to keep the bot running without your computer always on? Here are friendlier options:

- **Fly.io** — great for small bots.  
  Follow their guide here: [Fly.io](https://dev.to/denvercoder1/hosting-a-python-discord-bot-for-free-with-flyio-3k19) for the bot hosting. Fly.io used to have a [free tier](https://fly.io/docs/about/pricing/#legacy-hobby-plan) as long as your monthly cost was below 5 USD.

- **Heroku** — Simple deployment with free dynos (sleeps when inactive).  
 Heroku is a great option for easy deployment with a free tier.
Full step-by-step instructions are here: [hosting on Heroku](https://medium.com/@linda0511ny/create-host-a-discord-bot-with-heroku-in-5-min-5cb0830d0ff2) are linked. You may need the [heroku CLI client for hosting](https://medium.com/analytics-vidhya/how-to-install-heroku-cli-in-windows-pc-e3cf9750b4ae).

If you're using Heroku's PostgresSQL add-on instead, first [install the add-on](https://elements.heroku.com/addons/heroku-postgresql) then [set it up](https://devcenter.heroku.com/articles/heroku-postgresql) to attach your app to the Postgres. Now you can look at `Heroku - Dashboard - Resources - Add Ons` to look at the app on Heroku, and copy the URI given from Postgres add-on to the respective line in the `.env file`

If you have github + heroku, using Heroku's [Github integration](https://devcenter.heroku.com/articles/github-integration) allows you to automatically push Github pushes to also deploy on Heroku. (Using `git push` to push to both Github and Heroku)

When deploying on heroku, any variables stored in .env locally cannot be pushed to any public repos. It's advisable to use [Heroku Config Vars](https://devcenter.heroku.com/articles/config-vars) to store them.

- **Render**, **Railway**, or **Vercel** — Other free/cheap platforms with easy Python support.

For beginners: Start with local running or the hosted instance. Cloud hosting is powerful but more complex!

Questions? Join our Discord support server — we're happy to help you choose the best option ♡

### Other useful things

While the steps above are enough to run the bot locally or on cloud platforms, some operating systems might need extra packages.

For example, on Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt install postgresql   # if using local PostgreSQL
```
Check your system's package manager for equivalents.

For hosting alternatives (Fly.io, Heroku, Render, Railway, etc.), see the "Hosting options" section above ♡

Questions? Join our Discord support server or open an issue — we're happy to help!

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
