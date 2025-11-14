# Copilot Instructions for Argus eINK Project

## Project Overview
Argus is a **Raspberry Pi 5**-based e-ink display driver for Waveshare 2.13" e-paper modules (122×250 resolution). It provides abstraction layers for hardware communication (GPIO via `/dev/gpiochip4`, SPI via `spidev`) and image rendering for dual-layer displays (black + red/yellow).

## Architecture

### Directory Structure
- **`eink/`**: Core application
  - `epdconfig.py`: GPIO/SPI hardware abstraction layer (RaspberryPi class)
  - `epd2in13b_V4.py`: EPD controller with init, display, clear methods
  - `eink-writer.py`: Production script for Team 8736 "The Mechanisms" display
  - `pic/Font.ttc`: TrueType font for text rendering
  - `demo/epd_2in13b_V4_test.py`: Comprehensive test/demo examples
  
- **`scripts/check_env.py`**: Environment smoke-test (import checks, syntax validation)

### Data Flow
1. **PIL Image Creation**: `Image.new('1', (height, width), 255)` for 1-bit monochrome
2. **Drawing**: Use `ImageDraw` separately for black layer and red/yellow layer
3. **Buffer Encoding**: `EPD.getbuffer(image)` converts PIL to bytearray (auto-rotates if needed)
4. **Hardware Transmission**: `EPD.display(black_buffer, ry_buffer)` sends via SPI+GPIO
5. **Status Polling**: `EPD.busy()` waits for hardware ready (blocking loop checks BUSY_PIN)

### Hardware Communication Stack
- **GPIO Controller**: `/dev/gpiochip4` (Pi 5's GPIO controller via `periphery` library)
  - RST_PIN: GPIO17, DC_PIN: GPIO25, PWR_PIN: GPIO18, BUSY_PIN: GPIO24, CS_PIN: GPIO8
  - Pin names are defined in `epdconfig.RaspberryPi.__init__()` (commented alternatives exist for Pi 5)
- **SPI Protocol**: `spidev` on /dev/spidev0.0, 4MHz, mode 0
- **Data Commands**: `send_command()` + `send_data()` via GPIO control (DC, CS pins)

## Key Conventions & Patterns

### EPD Display Pattern (Standard Workflow)
```python
import epd2in13b_V4
from PIL import Image, ImageDraw, ImageFont
import time

epd = epd2in13b_V4.EPD()
epd.init()       # Powers on, initializes SPI, resets hardware
epd.clear()      # Clears display (all white)
time.sleep(1)

# Create black and red/yellow layers separately
HBlackimage = Image.new('1', (epd.height, epd.width), 255)  # 250×122
HRYimage = Image.new('1', (epd.height, epd.width), 255)

drawblack = ImageDraw.Draw(HBlackimage)
drawry = ImageDraw.Draw(HRYimage)

# Draw on layers: fill=0 (black), fill=255 (white/transparent)
drawblack.text((10, 0), 'Team 8736', font=font18, fill=0)
drawry.text((10, 20), 'The Mechanisms', font=font24, fill=0)
drawry.rectangle((80, 50, 130, 100), fill=0)

epd.display(epd.getbuffer(HBlackimage), epd.getbuffer(HRYimage))
time.sleep(2)

epd.sleep()  # Powers down module
```

### Image Dimension Handling (Critical)
- Hardware: 122×250 (width×height)
- Create images as `(height, width)` = `(250, 122)` for standard rendering
- OR `(width, height)` = `(122, 250)` for vertical orientation
- `getbuffer()` detects swapped dimensions and auto-rotates: `image.rotate(90, expand=True)`
- Logs warning if dimensions don't match—returns blank buffer to prevent crashes

### Module Lifecycle & Cleanup
```python
# Initialization: epdconfig.module_init() called inside epd.init()
# - Powers on PWR_PIN, opens SPI0, sets 4MHz speed

# Cleanup: epdconfig.module_exit(cleanup=True) via epd.sleep()
# - Closes SPI, powers down all GPIO pins
```
- Always pair `epd.init()` with `epd.sleep()` (or use try-finally)
- Power management is critical—leaving GPIO enabled drains battery

### Font Management & Image Paths
- Fonts: `ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), size)`
- Common sizes: 18px, 20px, 24px (choose based on text length vs. available space)
- `picdir` resolved dynamically: `os.path.join(os.path.dirname(__file__), 'pic')`

### Color Layer Separation (Key Design Pattern)
- **Black layer** (`HBlackimage`): Text, outlines, geometric shapes; draw with `fill=0`
- **Red/Yellow layer** (`HRYimage`): Colored elements (appears red on hardware); draw with `fill=0`
- Both layers required for `display()` call (can send all-white buffer if not using red/yellow)
- Use separate `ImageDraw` objects to avoid interference

### Image Creation & Drawing Rules
- Always mode `'1'` (1-bit monochrome): `Image.new('1', (height, width), 255)`
- Background: 255 (white); draw with: 0 (black), outline=0 (black border)
- Coordinates: PIL `(x, y)` standard; verify layout with print/logging
- `getbuffer()` handles PIL→bytearray conversion (internal processing)

## Critical Workflows

### Running Display Scripts
- **Development**: `python eink-writer.py` or demo scripts
- **Hardware Prerequisites**: Script must run on Raspberry Pi 5 with:
  - `/dev/gpiochip4` available (Pi 5's GPIO controller)
  - `spidev` and `periphery` packages installed
  - e-ink module connected to Pi 5 GPIO and SPI0 pins (RST, DC, BUSY, PWR, CS)

### Environment Validation
- Run `scripts/check_env.py` to validate setup (imports, syntax, device file)
- Supports CI mode via `CI=1 ./scripts/check_env.py` for syntax-only checks

### Display Refresh Delays
- Always use `time.sleep()` after operations:
  - `time.sleep(1)` after `clear()`
  - `time.sleep(2)` after `display()`
- E-ink updates are slow (~2s); delays prevent command queue issues

### Debugging & Logging
- Enable logging: `logging.basicConfig(level=logging.DEBUG)`
- Monitor `epdconfig` logs for GPIO/SPI initialization failures
- Check `busy()` blocking indicates hardware communication issues

## Error Handling Patterns
- Wrap all EPD operations in try-except catching `IOError` (SPI failures)
- Always catch `KeyboardInterrupt` to ensure cleanup via `epdconfig.module_exit(cleanup=True)`
- Example pattern (see `demo/epd_2in13b_V4_test.py`):
```python
try:
    epd = epd2in13b_V4.EPD()
    epd.init()
    # ... rendering code ...
except Exception as e:
    logging.error(f"Display error: {e}", exc_info=True)
finally:
    epd.sleep()
```

## Implementation Checklist
- [ ] Create images with correct dimensions: `(height, width)` = `(250, 122)`
- [ ] Use separate ImageDraw for black and red/yellow layers
- [ ] Always include `time.sleep()` after `clear()` and `display()`
- [ ] Wrap display ops in try-finally with cleanup
- [ ] Test on Raspberry Pi 5 with `/dev/gpiochip4` available
