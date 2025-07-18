# Corporate Translator

We’ve all experienced it (actually I haven’t), but when you apply and enter a corporate job, you always listen (and even use yourself) absurd corporate jargon terms. That’s why I designed this Slack Bot that translates back and forth whatever the heck your boss is telling you!

Look imagine your boss says this: *“We must initiate a paradigm shift, leveraging our core competencies to procure stakeholder engagement through a value-added, synergistic ideation process. This will require a strategic recalibration of our input protocols to maximize actionable insights and ensure optimal bandwidth utilization across all functional verticals.”*

Now, you might be asking what the hell does that even mean? Well they are saying: *“We need to change things and make more money. Figure it out, and work harder. Don't bother us with problems; just make it happen.”* - Yeah, it looks like this boss isn’t too happy about their circumstances!

So, how did I understand it? Well I used **Corporate Translator** Slack Bot, in particular, the `/befr` command which cuts right through your boss’ bull 💩 and into their villainous minds of greed. Well guess what, you have this bot by your side like Google Translate so you don’t have to deal with all of his formalities. And on top of that you have `/tellboss` command which converts your casual, slang language into a corporate to make your boss’ life harder! You can also simply use `/tldr` which translates your boss' messages into plain text, but it does not identify what they are implying behind his fancy words! 

If you want to immediately test the Slack Bot, join this [Slack Server](https://join.slack.com/t/seriousbusinessstuff/shared_invite/zt-39n69tneo-AEt7r4xs_g6i56BaLwXXYg) which has all the features out of the box! And to check if the bot is up [visit this site](https://corporate-translator-ooco.onrender.com/)!

Also, the bot is being hosted on a [Flask web app] (https://corporate-translator-ooco.onrender.com/)

---

### Hosting the Bot
1. git clone https://github.com/ryan-mai/corporate-translator.git
2. a) Locally Host (On your computer) b) Deploy the Bot (Does not require your computer to be on 24/7)
3. Install all dependencies from requirements.txt - `pip install -r requirements.txt` into your virtual environment (`python -m venv venv`)
4. To create your Slack bot, visit the [official site](https://api.slack.com/apps)
5. After creating the bot go to OAuth & Permissions > Bot Token Scopes > `channels:history`, `chat:write`, `commands`, `groups:history`, `groups:read`, `im:history`, `npim:history`, `user:read`
6. a) Go to Socket Mode > Enable Socket Mode - b) Skip this step
7. Go to Slash Commands > `/tldr`, `/befr`, `/clear`, `/tellboss`
7. Generate your API key by visiting [Google Cloud](https://console.cloud.google.com/) - Optionally, choose your perferred AI service (this will require you to change the variable name in the next step)
7. Create an environment variable (`.env`) containing `GEMINI_API_KEY`, `SLACK_BOT_TOKEN`, and `SLACK_SIGNING_SECRET` (Req 2b.) or `BOT_SOCKET_TOKEN` (Req 2a.)
8. a) Run `python slack_local_bot.py` and tada! - b) Decide on where you will host the site (Choose [Render](https://render.com/) if you are new)

---
#### IGNORE STEPS BELOW IF YOU HOST LOCALLY/VIA SOCKET
These **ONLY** apply if you are **deploying** the bot
1. Set the run command to `python slack_bot.py`
2. Add the environment variable in your hosting service
3. Go to Event Subscriptions > Request URL > `https://<sitename>.onrender.com/slack/events`
4. Go to Slash Commands > For each command add the request url > `https://<sitename>.onrender.com/slack/events`
5. Tada! Celebrate your deployment by expressing your spite or joy at your current job with `/tellboss <message>`

---

#### Commands
1. `/tldr` - Transforms complex corporate jargon into plain English
2. `/befr` - Identifies what your boss' is actually expressing/sarcasm
3. `/clear` - Clears channel for professionalism 😉
4. `/tellboss` - Chat like you would to your friend and the bot elevates it into corporate jargon

---

#### Features
1. `Use This` - Reformats the generate response into a more clear message
2. `Regenerate` - Creates a new response while still following the original prompt
3. `Email` - Only for `/tellboss` which reformats the response into an email template to save your time

---

#### Additional Notes
1. Ensure after making changes to your Slack bot's configuration go to OAuth & Permission > `Reinstall <Bot Name>`
2. In Step 7. `SLACK_SIGNING SECRET` (2b.) can be found in Basic Information > Signing Secret & `BOT_SOCKET_TOKEN`(2a.) can be found in Socket Mode
