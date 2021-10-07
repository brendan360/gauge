# gauge


sudo apt-get update

sudo apt-get -y upgrade

sudo apt-get -y install git python3 python3-pip wiringpi python-pil python-numpy RPi.GPIO python3-numpy libopenjp2-7-dev vim




cd ~

wget http://www.airspayce.com/mikem/bcm2835/bcm2835-1.68.tar.gz

tar zxvf bcm2835-1.68.tar.gz 

cd bcm2835-1.68/

sudo ./configure

sudo make

sudo make check

sudo make install

sudo pip3 install adafruit-circuitpython-seesaw Adafruit-Blinka adafruit-circuitpython-htu31d pillow

cd ~

git clone https://github.com/brendan360/gauge.git
