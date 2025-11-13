# Copilot Instructions for Argus eINK Project

## Project Overview
Argus is a **Raspberry Pi 5**-based e-ink display driver project for Waveshare 2.13" e-paper modules. The codebase provides abstraction layers for hardware communication (GPIO, SPI) and image rendering for both black and red/yellow (RY) color e-ink displays.

## Architecture

### Directory Structure
- **`lib/waveshare_epd/`**: Core driver library
  - `epd2in13b_V4.py`: Main EPD controller (122×250 resolution)
  - `epdconfig.py`: Hardware abstraction layer for Raspberry Pi (GPIO, SPI)
  - `epd2in13_V4.py`: Alternative display variant
  
- **`demo/`**: Example usage and test scripts
  - `epd_2in13b_V4_test.py`: Comprehensive demo with various drawing operations
  
- **`eink-writer.py`**: Production script for Team 8736 "The Mechanisms" display

### Data Flow
1. **Image Creation**: PIL `Image` objects (mode '1' for 1-bit monochrome)
2. **Drawing Layer**: `ImageDraw` for text/shapes on black and red/yellow layers separately
3. **Buffer Conversion**: `EPD.getbuffer()` converts PIL images to bytearrays
4. **Hardware Display**: `EPD.display()` sends buffers via SPI to hardware

### Hardware Communication (Raspberry Pi 5)
- **SPI Protocol**: 4MHz, mode 0, via `spidev` library on SPI0
- **GPIO Control**: Uses `/dev/gpiochip4` (Pi 5's GPIO controller)
  - RST_PIN: GPIO27, DC_PIN: GPIO22, BUSY_PIN: GPIO23, PWR_PIN: GPIO4, CS_PIN: GPIO12
- **Hardware Flow**: Commands→Data via `send_command()` and `send_data()` methods
- **Status Polling**: `busy()` waits for hardware ready state (essential before operations)

## Key Conventions & Patterns

### EPD Display Pattern
```python
# Standard workflow for rendering
epd = epd2in13b_V4.EPD()
epd.init()
epd.clear()

# Create separate images for black and red/yellow
HBlackimage = Image.new('1', (epd.height, epd.width), 255)
HRYimage = Image.new('1', (epd.height, epd.width), 255)

drawblack = ImageDraw.Draw(HBlackimage)
drawry = ImageDraw.Draw(HRYimage)

# Note: Dimensions are (height, width) = (250, 122) for 2.13" V4
# Drawing uses (x, y) coordinates; fill=0 = black, outline=0 = black
drawblack.text((10, 0), 'hello world', font=font20, fill=0)
drawry.rectangle((80, 50, 130, 100), fill=0)

epd.display(epd.getbuffer(HBlackimage), epd.getbuffer(HRYimage))
```

### Image Dimension Handling
- Hardware resolution: 122×250 (width×height)
- Images can be created as `(height, width)` or `(width, height)` tuples
- `getbuffer()` auto-rotates if dimensions swapped: `image.rotate(90, expand=True)`
- Always validate with logging if dimensions don't match

### GPIO & Power Management
```python
# Hardware initialization via epdconfig
epdconfig.module_init()  # Powers on, initializes SPI
epdconfig.module_exit(cleanup=True)  # Powers down, closes GPIO
```
- Power control is critical—leave PWR_PIN enabled during operation
- Always wrap display ops in try-except with `KeyboardInterrupt` cleanup

### Font Management
- Fonts loaded from `pic/Font.ttc` using `ImageFont.truetype()`
- Sizes (18, 20, 24px) commonly used; choose based on text length
- Font path resolution: `os.path.join(picdir, 'Font.ttc')`

## Critical Workflows

### Running Display Scripts
- **Development**: `python eink-writer.py` or demo scripts
- **Hardware Prerequisites**: Script must run on Raspberry Pi 5 with:
  - `/dev/gpiochip4` available (Pi 5's GPIO controller)
  - `spidev` and `periphery` packages installed
  - e-ink module connected to Pi 5 GPIO and SPI0 pins (RST, DC, BUSY, PWR, CS)

### Debugging
- Enable logging: `logging.basicConfig(level=logging.DEBUG)`
- Monitor `epdconfig` logs for GPIO/SPI initialization failures
- Check `busy()` blocking indicates hardware communication issues

### Display Refresh Delays
- Always use `time.sleep()` after operations:
  - `time.sleep(1)` after `clear()`
  - `time.sleep(2)` after `display()`
- E-ink updates are slow (~2s); delays prevent command queue issues

## Project-Specific Patterns

### Method Name Variants
- `clear()` vs `Clear()`: Both supported (latter for backward compatibility)
- Always prefer lowercase `clear()` in new code

### Color Layer Separation
- **Black layer** (`HBlackimage`): Text, outlines, shapes with fill=0
- **Red/Yellow layer** (`HRYimage`): Colored elements (appears as red on hardware)
- Both layers required for `display()` call (send empty buffer if not using RY)

### Image Mode
- Always use mode '1' (1-bit monochrome): `Image.new('1', ...)`
- Background color 255 (white); draw with fill=0 (black)
- `getbuffer()` handles conversion internally

## Error Handling
- Wrap all EPD operations in try-except catching `IOError` (SPI failures)
- Catch `KeyboardInterrupt` to ensure `epdconfig.module_exit(cleanup=True)` executes
- Log all failures with descriptive context (see demo for pattern)
