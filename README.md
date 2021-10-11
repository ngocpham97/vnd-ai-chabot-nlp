# Notes on Rasa `2.x / 1.x`

1. The `main` branch of this repo is compatible with Rasa Open Source **version 2.x**
2. The bot for **Rasa 1.x** can be found in the [rasa-1 branch].



# VND Credit Bot

This is an example chatbot demonstrating how to build AI assistants for financial services and banking. This starter pack can be used as a base for your own development or as a reference guide for implementing common banking-industry features with Rasa. It includes pre-built intents, actions, and stories for handling conversation flows like checking spending history and transferring money to another account.

## Install dependencies

Run:
```bash
pip install -r requirements.txt
```

To install development dependencies:

```bash
pip install -r requirements-dev.txt
pre-commit install
python -m spacy download en_core_web_md en
python -m spacy link en_core_web_md en
```

> With pre-commit installed, the `black` and `doctoc` hooks will run on every `git commit`.
> If any changes are made by the hooks, you will need to re-add changed files and re-commit your changes.

## Run the bot

Use `rasa train` to train a model.

Then, to run, first set up your action server in one terminal window, listening on port 5056:
```bash
rasa run actions --port 5056
```

Note that port 5056 is used for the action server, to avoid a conflict when you also run the helpdesk bot as described below in the `handoff` section.

In another window, run the duckling server (for entity extraction):

```bash
docker run -p 8000:8000 rasa/duckling
```

Then to talk to the bot, run:
```
rasa shell --debug
```

Note that `--debug` mode will produce a lot of output meant to help you understand how the bot is working
under the hood. To simply talk to the bot, you can remove this flag.


You can also try out your bot locally using Rasa X by running
```
rasa x
```

Refer to our guided workflow in the [Wiki page](https://github.com/RasaHQ/financial-demo/wiki/Using-Rasa-X-with-the-Financial-Demo) for how to get started with Rasa X in local mode.


## Overview of the files

`data/nlu/nlu.yml` - contains NLU training data

`data/nlu/rules.yml` - contains rules training data

`data/stories/stories*.yml` - contains stories training data

`actions.py` - contains custom action/api code

`domain.yml` - the domain file, including bot response templates

`config.yml` - training configurations for the NLU pipeline and policy ensemble

`tests/` - end-to-end tests