# piscreen

Python application to display images in a RaspberyPi connected to a 3,5" touch display.
The display has a resolution of 480x320

# Description

The application consists in two processes
1. piscreen
  Configures and loads the images in the display. It is started when the user pi logs in, as configured in /home/pi/.bashrc.
  The raspberry is configured to log in automatically with pi user.
2. piscreen.mailparser.service
  A service checking periodically in an imap email address. The messages are parsed, attachments are saved as images for the piscreen process, and text messages are drawn in images for the piscreen process 

## Process: piscreen
Screen is divided in left/center/right areas, which can be clicked
* Left/Right -> navigation previous/next image
* Center -> Menu (to be implemented)

## Process: mailparser
Connects to an imap server (gmail), and fetches all messages in INBOX.
If message is from an authorized sender, it is processed. Attachments will be saved, and text within the body will be used to create an image. 
All messages will be deleted after being processed, or if sent by an unauthorized sender.

## Configuration
The configuration file piscreen/piscreen/piscreen.cfg is common for both processes

# Installation
## Pre-requisites

**LCD**
```/home/pi/LCD_show_v6_1_3/LCD_35v```

**Clone repo**
```
cd
git clone -b develop https://github.com/jordivea/piscreen
```

**Install python libraries**
```
pip3 install -r requirements.txt
```

**Autlogin**

Using raspi-config, configure raspberry to auto login in console mode.
Additionally set hostname to piscreen.

## Configuration file

```
cd /home/pi/piscreen/piscreen
cp piscreen.cfg.orig piscreen.cfg
```

Edit *piscreen.cfg* with the correct values
 
## Logging

Add daily crontab task to rotate logs.

```cp piscreen.log piscreen.log.$(date +%Y%m%d); cat /dev/null > piscreen.log; bzip2 piscreen.log.$(date +%Y%m%d)```

## Auto run

### piscreen

The process must be started when the raspberry pi is booted. As the pi user will be logged automatically, add the script call in the user's .bashrc file

```vim /home/pi/.bashrc```

```
#Run piscreen script
python3 /home/pi/piscreen/piscreen/piscreen.py &>/dev/null'
```

### piscreen.mailparser.service

Run as a service.
```
sudo cp /home/pi/piscreen/piscreen/piscreen.mailparser.service /lib/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable piscreen.mailparser.service
sudo systemctl start piscreen.mailparser.service
```

# Next versions
* Dynamically change font size in order to use as much display as possible
* Parse mail messages for text message properties (background and font color), scheduled display, expiration
* Add receipes functionality. Menu can alternate between images and receipes. Receipes are to be sent via email, using markdown notation.

