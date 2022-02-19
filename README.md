# joi-skill-photo

## Managing Skill Installations
All of these Mycroft kills Manager (mycroft-msm) commands are executed on the Raspberry Pi

### Install Skill
    cd ~/mycroft-core/bin
    ./mycroft-msm install https://github.com/TySeddon/joi-skill-photo.git

### Remove Skill    
    cd ~/mycroft-core/bin
    ./mycroft-msm remove joi-skill-photo

### Bash Script to automate updating of skills
In home director create file called update-skills.sh
    #!/bin/sh
    cd ~/mycroft-core/bin
    echo "----Updating joi-skill-utils----"
    pip install git+https://github.com/TySeddon/joi-skill-utils   
    echo "----Uninstalling joi-skill-photo----"
    ./mycroft-msm remove joi-skill-photo
    echo "----Installing joi-skill-photo----"
    ./mycroft-msm install https://github.com/TySeddon/joi-skill-photo.git

Make script executable and writeable
    sudo chmod a+xw update-skills.sh

## One-Time Raspberry Pi setup
    cd ~/mycroft-core        
    source venv-activate.sh  
    pip install git+https://github.com/TySeddon/joi-skill-utils    

    sudo nano client_secret.json
        get content for this file from https://console.developers.google.com/


## Mycroft Terminology

* **utterance** - An utterance is a phrase spoken by the User, after the User says the Wake Word. what's the weather like in Toronto? is an utterance.
* **dialog** - A dialog is a phrase that is spoken by Mycroft. Different Skills will have different dialogs, depending on what the Skill does. For example, in a weather Skill, a dialog might be the.maximum.temperature.is.dialog.
* **intent** - Mycroft matches utterances that a User speaks with a Skill by determining an intent from the utterance. For example, if a User speaks Hey Mycroft, what's the weather like in Toronto? then the intent will be identified as weather and matched with the Weather Skill. When you develop new Skills, you need to define new intents.

## Virtual Environment Setup

### Install Virtual Environment
    pip install virtualenv

### Creating 
    python -m venv venv

### Activate Virtual Environment
    .\venv\Scripts\activate

# Required Packages
    pip install msk
    pip install adapt-parser
    pip install git+https://github.com/TySeddon/joi-skill-utils

## Update requirements.txt
    pip freeze > requirements.txt

## Load Required Packages
Create your virtual environment, then load all the required dependencies with:
    pip install -r requirements.txt

## API Keys
1. Login to https://console.developers.google.com/
2. Click OAuth Consent Screen
    a. Choose External, Click Create
    b. App name = "Joi Photo Skill"
    b. User support email = <any email you want>
    c. Developer contact = <any email you want>
    d. Click "Save and Continue"
    e. No scopes at this time
    f. Click "Save and Continue"
    g. Add user email of test user
    h. Click "Save and Continue"
    i. Back to Dashboard
3. Click on Credentials
4. Click Create Credentials
5. Click OAuth client ID
6. Application type = Desktop App, Name = Joi
7. Click Create
    a. Dialog "OAuth client created" displays.  
    b. Click Download JSON
    b. Store contents of this file in "client_secrets.json" in this project.
8. From Dashboard, click "Enable APIs and Services"
9. Search for Photos Library API
10. Click Enable



# Content
https://www.gardendesign.com/flowers/easy.html
