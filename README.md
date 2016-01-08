# thermal

##Summary 
This respository is for controlling a Raspberry Pi computer running the standard camera that comes with the Pi and a second thermal imaging camera
Images are taken with both cameras and combined via Imagemagick/PIL
It's run as a Flask application and all interaction is done with JSON and through RESTful APIs
CouchDB is the database
Interactions with the hardware are processed asynchronously by means of Celery.
RabbitMQ is used as the message brokering service for Celery.
There is also support for taking pictures by means of a button on the project box.

##Hardware Requirements
It has been developed with the following requirements:
- Raspberry Pi 2 B computer, 32GB SD card
- Raspian Jessie 11.21.2015 image is the os on the RPi
- Raspberry Pi standard camera
- FLIR Lepton camera with the Pure Engineering breakout board
- A project box with a momentary button

##Installation Instructions
The hostname for this Raspberry Pi will be strangefruit4.
I'll be installing software and running it as the default pi user.

- install the 11.21.15 version of Raspian Jessie (for RPi 2 B) on a 32GB micro SD card using Pi Filler on a Mac Mini.
- put the card in a Raspberry Pi 2 B, connect the RPi to power and ethernet.  
- ssh pi@raspberrypi
- sudo vi /etc/hostname     
  - set it to strangefruit4
- if you have a USB wifi dongle plugged in to the unit:
  - sudo vi /etc/wpa_supplicant/wpa_supplicant.conf , add this to the bottom:
    network={
    ssid="YOUR_WIFI_ACCESS_POINT_NAME"
    psk="YOUR_WIFI_PASSWORD"
    proto=RSN
    key_mgmt=WPA-PSK
    pairwise=TKIP
    auth_alg=OPEN
    }
- sudo apt-get install vim
- sudo vim /etc/apt/sources.list , uncomment the line at the bottom
- sudo raspi-config
  - Enable Camera
  - Advanced Options > SPI > Enable Spi Module, also enable the SPI kernel module to load by default
  -Internationalization Options > set up your locale and timezone
  -Change User Password
  -Expand Filesystem
  -Finish
  -reboot the machine
- ssh pi@strangefruit4
- sudo apt-get update
- sudo apt-get upgrade
- set up the authorized key for my main linux desktop on strangefruit4
- sudo easy_install virtualenv
- sudo apt-get install python-dev python-opencv
- sudo apt-get install couchdb rabbitmq-server
- sudo apt-get build-dep python-imaging
- sudo apt-get install libjpeg9-dev
- cd ~
- git clone https://github.com/dcaulton/thermal.git
- cd ~/thermal
- virtualenv venv
- source venv/bin/activate
- pip install numpy  *** I know, shouldn't be needed but it runs long with a lot of c compiles.  
- pip install -r requirements/common.txt
- git config --global user.email "dcaulton@gmail.com"; git config --global user.name "Dave Caulton"
- git config --global color.ui true
- touch ~/.vimrc; echo 'syntax on' > ~/.vimrc
- add this to ~/.bashrc:  export EDITOR=/usr/bin/vim
- ln -s /usr/lib/python2.7/dist-packages/cv2.arm-linux-gnueabihf.so ~/thermal/venv/lib/python2.7/site-packages/cv2.arm-linux-gnueabihf.so
###at this point the system should be able to service api calls and take pictures

- Enable the CouchDB management panel access from other computers on the local network:
  - sudo vim /etc/couchdb/default.ini , update bind_address to 0.0.0.0.
  - maybe a sudo service couchdb restart?
  - *Now you can access the couchdb web interface from other computers/browsers on the local network at http://strangefruit4:5984/_utils*
- Enable the RabbitMQ management panel access from other points on the local network:
  - sudo rabbitmq-plugins enable rabbitmq_management
  - sudo rabbitmqctl add_user dave dave
  - sudo rabbitmqctl set_user_tags dave administrator 
  - sudo reboot  
  - *Now you can get at the rabbitmq admin server at http://strangefruit4:15672/#/  with the dave/dave credentials*
