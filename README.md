<div>


[![Licence](https://img.shields.io/badge/licence-MIT-blue.svg)](/LICENSE)
[![Discord](https://discord.com/api/guilds/849341001167273996/widget.png?style=shield)](https://discord.gg/E7bnXS2hpn)

</div>

## 🏁 Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Discord application
Create a new Discord application [here](https://discord.com/developers/applications) by clicking the `New application` button and name it whatever you want.

![New application](https://cdn.discordapp.com/attachments/721750194797936823/794646477505822730/unknown.png)

Go to the Bot section on the right-hand side and click on Add Bot.

![Add Bot](https://cdn.discordapp.com/attachments/852867509765799956/853984486970359838/unknown.png)

Get the bot token

![Token](https://cdn.discordapp.com/attachments/852867509765799956/853985222127124500/unknown.png)


To Invite the bot to your server go to Oauth2 select bot then select administrator and go to the link
![Invite Bot](https://cdn.discordapp.com/attachments/852867509765799956/853985694183850004/unknown.png)


### Prerequisites

Install Pipenv:

```sh
pip install pipenv
```

Install the required packages and the packages for development with Pipenv:

```sh
pipenv install --dev
```

### Environment variables

Set the environment variables. Start by writing this in a file named `local.env`:

```dotenv
TOKEN=your_bot_token
DB_URI=postgresql://user:password@db:5432/bonafide
rapid-api-key=rapi_api_key_for_fun_commands
google-api-key=google_api_key_for_youtube/google_etc.
```

```

### Running

Run the main.py file to get the bot running.
To enable music commands in bot run java -jar Lavalink.jar in terminal.
