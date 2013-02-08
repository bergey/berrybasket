Documentation for Raspberry Pi/MCP3008/Cosm datalogging project

# Install

1. Install [Adafruit Occidentalis](http://learn.adafruit.com/adafruit-raspberry-pi-educational-linux-distro) 0.2 on Raspberry Pi

2. Plug RasPi into router, log into router to find IP address, ssh into RasPi

3. Install python SPI library.  We learned to do this from [this blog post](http://jeremyblythe.blogspot.com/2012/09/raspberry-pi-hardware-spi-analog-inputs.html)

        git clone git://github.com/doceme/py-spidev
        cd py-spidev
        sudo python setup.py install

4. Download and install python packages for the Cosm API

        git clone git://github.com/petervizi/python-eeml

5. Download this script.

        git clone git://github.com/bergey/berrybasket.git

6. Sign up for Cosm account, create a new feed, fill out config file:

    Fill in the blanks in config.json

    - API_KEY

    - API_URL appears in the URL of the feed webpage.  It's the number in http://cosm.com/feeds/84597

# Hardware Setup

We're using the MCP3008 chip to convert analog measurements to digital.  The pins down one side of the chip are analog inputs; the other side connect to the computer.  The [aforementioned blog post](http://jeremyblythe.blogspot.com/2012/09/raspberry-pi-hardware-spi-analog-inputs.html) has good pictures of which pins go to which Raspberry Pi connections.  The [Pi T-Cobbler breakout board](http://adafruit.com/products/1105) from [Adafruit](http://adafruit.com/) is a great help in connecting the Raspberry Pi to a breadboard.  Adafruit also sells the [MCP3008](http://adafruit.com/products/856).

# TODO

- Allow measurement frequency to be specified in config file
- Specify channels to log in config file
- Add examples with specific sensors (thermistor, photoresistor)
