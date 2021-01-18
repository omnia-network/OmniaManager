# Omnia Manager

(this repo is the new version of [omnia-product-demo](https://github.com/omnia-network/omnia-product-demo))

Omnia Manager is the main part of Omnia Network. It's the server that relies between devices that want to connect to Omnia and get all data they need to work properly, and the servers owned by Omnia that handle the syncronization between them.

## Table of content
[ToC]

## Getting started
You can get started by cloning directly this repo or downloading our docker image.

### Cloning repo

#### Step 1

Clone our repo and move inside it:
```
git clone https://github.com/omnia-network/OmniaManager.git
cd OmniaManager
```

#### Step 2: Install requirements

Create a Python 3 virtual environment and install requirements:
```
python install -r requirements.txt
```
**Linux:** You must install truetype fonts and to use Arial:
```
sudo apt-get install ttf-mscorefonts-installer
sudo fc-cache
fc-match Arial
```

#### Step 3: Run

Run Omnia Manager server with this command:
```
python server.py
```
Server is now up and can accept devices.

### Docker image
Not implemented yet.

---

## Documentation

Will be added to the wiki.
