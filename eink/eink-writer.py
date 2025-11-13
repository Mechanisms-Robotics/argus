#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
picdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'pic')
libdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

import logging
import epd2in13b_V4
import time
from PIL import Image,ImageDraw,ImageFont
import traceback

logging.basicConfig(level=logging.DEBUG)

epd = epd2in13b_V4.EPD()
logging.info("init and Clear")
epd.init()
epd.clear()
time.sleep(5)

# Drawing on the image
logging.info("Drawing")    
font24 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 24)
font18 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 18)

HBlackimage = Image.new('1', (epd.height, epd.width), 255) 
HRYimage = Image.new('1', (epd.height, epd.width), 255)  # 250*122

drawblack = ImageDraw.Draw(HBlackimage)
drawry = ImageDraw.Draw(HRYimage)

drawblack.text((10, 0), 'Team 8736', font = font18, fill = 0)
drawry.text((10, 20), 'The Mechanisms', font = font24, fill = 0)
drawblack.text((10, 50), 'A really long logline.', font = font18, fill = 0)

epd.display(epd.getbuffer(HBlackimage), epd.getbuffer(HRYimage))
