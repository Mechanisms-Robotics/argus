import os
import logging
import sys
import time

logger = logging.getLogger(__name__)

class RaspberryPi:
    def __init__(self):
        import spidev
        from periphery import GPIO

        self.RST_PIN  = 17
        self.DC_PIN   = 25
        self.CS_PIN   = 8
        self.BUSY_PIN = 24
        self.PWR_PIN  = 18
        self.MOSI_PIN = 10
        self.SCLK_PIN = 11

        # # Pin definition for Pi 5
        # self.RST_PIN = 27   # GPIO27
        # self.DC_PIN = 22    # GPIO22
        # self.CS_PIN = 12    # GPIO12 (SPI0 CS0)
        # self.BUSY_PIN = 23  # GPIO23
        # self.PWR_PIN = 4    # GPIO4
        
        # Initialize GPIO using gpiochip4 (Pi 5's GPIO controller)
        try:
            self.rst = GPIO("/dev/gpiochip4", self.RST_PIN, "out")
            self.dc = GPIO("/dev/gpiochip4", self.DC_PIN, "out")
            self.pwr = GPIO("/dev/gpiochip4", self.PWR_PIN, "out")
            self.busy = GPIO("/dev/gpiochip4", self.BUSY_PIN, "in")
            logger.debug("GPIO initialized successfully")
        except Exception as e:
            logger.error(f"GPIO initialization failed: {str(e)}")
            raise
            
        self.SPI = spidev.SpiDev()

    def digital_write(self, pin, value):
        try:
            if pin == self.RST_PIN:
                self.rst.write(bool(value))
            elif pin == self.DC_PIN:
                self.dc.write(bool(value))
            elif pin == self.PWR_PIN:
                self.pwr.write(bool(value))
        except Exception as e:
            logger.error(f"digital_write failed on pin {pin}: {str(e)}")
            raise

    def digital_read(self, pin):
        try:
            if pin == self.BUSY_PIN:
                return self.busy.read()
            return False
        except Exception as e:
            logger.error(f"digital_read failed on pin {pin}: {str(e)}")
            raise

    def delay_ms(self, delaytime):
        time.sleep(delaytime / 1000.0)

    def spi_writebyte(self, data):
        self.SPI.writebytes(data)

    def spi_writebyte2(self, data):
        self.SPI.writebytes2(data)

    def module_init(self):
        try:
            # Power on the module
            self.pwr.write(True)
            
            # Initialize SPI
            self.SPI.open(0, 0)  # Use SPI0
            self.SPI.max_speed_hz = 4000000
            self.SPI.mode = 0b00
            
            return 0
            
        except Exception as e:
            logger.error(f"module_init failed: {str(e)}")
            return -1

    def module_exit(self, cleanup=False):
        logger.debug("Closing SPI and powering down module...")
        try:
            self.SPI.close()
            
            self.rst.write(False)
            self.dc.write(False)
            self.pwr.write(False)
            
            if cleanup:
                self.rst.close()
                self.dc.close()
                self.pwr.close()
                self.busy.close()
        except Exception as e:
            logger.error(f"module_exit failed: {str(e)}")

# Create a global instance of the RaspberryPi class
implementation = RaspberryPi()

# Make all the functions available at the module level
for func in [x for x in dir(implementation) if not x.startswith('_')]:
    setattr(sys.modules[__name__], func, getattr(implementation, func))