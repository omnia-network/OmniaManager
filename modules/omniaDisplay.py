from PIL                    import Image, ImageDraw, ImageFont, ImageOps
import io
import logging
import json
import time

### Omnia libraries ###
from core.omniaMessageTypes      import OmniaMessageTypes as OMT
### --- ###

class OmniaDisplay:
    """Utilities for displays. 
    Uses PIL library for image processing.
    You can draw on the display image using OmniaDisplay.image_draw, which is a PIL ImageDraw instance.
    FONT_ARIAL_11, FONT_ARIAL_30 are ImageFont.truetype objects already instanciated.
    """

    FONT_ARIAL_11 = ImageFont.truetype("fonts/Arial.ttf", 11)
    FONT_ARIAL_30 = ImageFont.truetype("fonts/Arial.ttf", 30)

    def __init__(self, omniaProtocol, dimensions, image_mode="RGBA"):
        """Initialization

        :param omniaProtocol: low-level OmniaProtocol
        :type omniaProtocol: OmniaProtocol instance
        :param dimensions: width, length of the display
        :type dimensions: tuple or list
        :param image_mode: image mode, please refer to pillow modes (https://pillow.readthedocs.io/en/stable/handbook/concepts.html#concept-modes), defaults to "RGBA"
        :type image_mode: str, optional
        """

        ### OmniaProtocol ###
        self.omniaProtocol = omniaProtocol
        ### --- ###

        ### Dimensions ###
        self.width = dimensions[0]
        self.height = dimensions[1]
        ### --- ###

        ### Display image ###
        self.image_mode = image_mode
        self.image = Image.new(self.image_mode, (self.width, self.height))

        self.image_draw = ImageDraw.Draw(self.image)    # ImageDraw object
        
        self.img_old = self.image     # temp variable to save the current image

        # Flags
        self.img_is_new = False     # True if there is a new image to display
        ### --- ###

        ### Log ###
        self.log = logging.getLogger(
            '[{}]: OmniaDisplay'.format(self.omniaProtocol.client_info["name"])
        )
        ### --- ###
    
    def setDimensions(self, dimensions):
        """Sets display dimensions. Creates new image with new dimensions.

        :param dimensions: width, length of the display
        :type dimensions: tuple or list
        """
        self.width = dimensions[0]
        self.height = dimensions[1]

        self.image = self.image.resize( (self.width, self.height) )

        self.img_is_new = True

        self.__updateImageDraw()
    
    def getDimensions(self):
        """Returns a tuple containing display dimensions

        :return: (width, height)
        :rtype: tuple
        """
        return self.width, self.height
    
    def setImage(self, image):
        """Sets display image, updates image_draw

        :param image: image, must be a PIL.Image instance
        :type image: PIL.Image
        """
        self.image = image
        self.__updateImageDraw()

        self.img_is_new = True
    
    def getImage(self, original=False):
        """Returns a copy of the display image. You can get the original image by setting the 'original' parameter to True.

        :param original: True if you want the original image object (be careful!), defaults to False
        :type original: bool, optional
        """

        if original:
            return self.image
        else:
            return self.image.copy()
    
    def resetImage(self):
        """Overwrite current image with a new one with the same dimensions, the same mode and filled in black. Updates image_draw
        """
        self.image = Image.new(self.image_mode, (self.width, self.height))
        self.__updateImageDraw()

        self.img_is_new = True
    
    def setImageMode(self, image_mode):
        """Convert current image to new image_mode

        :param image_mode: image mode, please refer to pillow modes (https://pillow.readthedocs.io/en/stable/handbook/concepts.html#concept-modes)
        :type image_mode: str
        """
        self.image_mode = image_mode

        self.image = self.image.convert(image_mode)
        self.__updateImageDraw()

        self.img_is_new = True
    
    def __updateImageDraw(self):
        """Updates ImageDraw object
        """
        self.image_draw = ImageDraw.Draw(self.image)

    async def sendDisplay(self, image_format='jpeg'):
        """Send image display, encoding it with format

        :param image_format: image format encoding, defaults to 'jpeg'. Refer to pillow image formats (https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html)
        :type image_format: str, optional
        """
        f = io.BytesIO()    # temp I/O file object
        self.image.save(f, image_format)
        buf = f.getbuffer() # buffer from I/O file object

        await self.omniaProtocol.send(buf, OMT.RGBA_IMAGE)

        del buf     # delete buffer, so that temp I/O file object can be closed
        f.close()   # close temp I/O file object
    
    async def startVideoStream(self):
        """Tells display to start a video stream
        """
        await self.omniaProtocol.send([ 1 ], OMT.START_STOP_VIDEO_STREAM)
    
    async def stopVideoStream(self):
        """Tells display to stop the video stream
        """
        await self.omniaProtocol.send([ 0 ], OMT.START_STOP_VIDEO_STREAM)

    async def sendVideoFrame(self, frame=None, image_format='jpeg'):
        """Send video frame to display, encoding it with format. If none frame is set, send 1-length buffer to display

        :param frame: image of type PIL.Image, defaults to None
        :type frame: PIL.Image, optional
        :param image_format: image format encoding, defaults to 'jpeg'. Refer to pillow image formats (https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html)
        :type image_format: str, optional
        """
        if frame:
            f = io.BytesIO()    # temp I/O file object
            frame.save(f, image_format) # save image with format encoding
            buf = f.getbuffer() # buffer from I/O file object

            await self.omniaProtocol.send(buf, OMT.VIDEO_FRAME)

            del buf     # delete buffer, so that temp I/O file object can be closed
            f.close()   # close temp I/O file object
        else:
            await self.omniaProtocol.send(b'0', OMT.VIDEO_FRAME)

# ---------------------------------------------------- #

class Omnia1BitDisplay(OmniaDisplay):
    """Utilities for SH1106 and SSD1306 displays. Extends OmniaDisplay
    """

    SH1106 = 0
    SSD1306 = 1

    def __init__(self, omniaProtocol, dimensions, configuration={}):
        """Initialization

        :param omniaProtocol: low-level OmniaProtocol
        :type omniaProtocol: OmniaProtocol instance
        :param dimensions: width, length of the display
        :type dimensions: tuple or list
        :param configuration: display configuration dictionary, defaults to {}
                              must have this structure:
                                {
                                    "contrast": <bool variable>,    # True if you want to invert default display colors
                                    "rotation": <bool variable>     # True if you want to rotate display 180 degrees
                                }
        :type configuration: dict, optional
        """
        super().__init__(omniaProtocol, dimensions, image_mode="L") # 8-bit pixels, black and white
        
        ### Display configuration ###
        self.configuration = configuration
        self.json_config_path = None
        ### --- ###

        ### Display info ###
        self.display_type = None
        ### --- ###

        ### Display wiring ###
        self.sda = None
        self.scl = None
        ### --- ###

        ### Log ###
        self.log = logging.getLogger(
            '[{}]: Omnia1BitDisplay'.format(self.omniaProtocol.client_info["name"])
        )
        ### --- ###
    
    def loadConfigFromJSON(self, json_config_path):
        """Loads the configuration from a JSON file

        :param json_config_path: path to JSON file containing the configuration,
                                 must have this structure:
                                    {
                                        "contrast": <bool variable>,    # True if you want to invert default display colors
                                        "rotation": <bool variable>     # True if you want to rotate display 180 degrees
                                    }
        :type json_config_path: str
        """

        self.json_config_path = json_config_path

        with open(self.json_config_path, "r") as j:
            self.configuration = json.load(j)

    def setConfiguration(self, configuration):
        """Sets the display configuration

        :param configuration: display configuration dictionary
                              must have this structure:
                                {
                                    "contrast": <bool variable>,    # True if you want to invert default display colors
                                    "rotation": <bool variable>     # True if you want to rotate display 180 degrees
                                }
        :type configuration: dict
        """
        self.configuration = configuration
    
    def setContrast(self, contrast, json_config_path=None):
        """Sets display contrast and saves configuration at json_config_path. If none is provided, uses the json_config_path attribute.

        :param contrast: True if you want to invert default display colors
        :type contrast: bool
        :param json_config_path: json file path where to save configuration, defaults to None
        :type json_config_path: str
        """
        self.img_is_new=True
        self.configuration["contrast"] = contrast

        if json_config_path:
            self.json_config_path = json_config_path

        self.__saveConfiguration()

    def setRotation(self, rotation, json_config_path=None):
        """Sets display rotation and saves configuration at json_config_path. If none is provided, uses the json_config_path attribute.

        :param rotation: True if you want to rotate display 180 degrees
        :type rotation: bool
        :param json_config_path: json file path where to save configuration, defaults to None
        :type json_config_path: str
        """
        self.img_is_new=True
        self.configuration["rotation"] = rotation

        if json_config_path:
            self.json_config_path = json_config_path

        self.__saveConfiguration()
    
    def __saveConfiguration(self):
        """Saves current configuration to JSON file at json_config_path, if exists
        """
        if self.json_config_path:
            with open(self.json_config_path, "w") as j:
                json.dump(self.configuration, j)
    
    async def setDisplayFromJSON(self, display_json_path):
        """Sets display dimensions, type and I2C wiring from JSON file.
        JSON file must have this structure:
        {
            "width": <width>,
            "height": <height>,
            "sda": <SDA pin (I2C)>,
            "scl": <SCL pin (I2C)>,
            "display_type": <int>   # use predefined values from this class:
                                        sh1106 display -> Omnia1BitDisplay.SH1106
                                        ssd1306 display -> Omnia1BitDisplay.SSD1306
        }

        :param display_json_path: JSON file path
        :type display_json_path: str
        """

        with open(display_json_path, "r") as j:
            tmp = json.load(j)

            self.setDimensions( (tmp["width"], tmp["height"]) )

            await self.setDisplay(tmp["sda"], tmp["scl"], tmp["display_type"])

    async def setDisplay(self, sda, scl, display_type):
        """Set display type and I2C pins

        :param sda: SDA pin (I2C)
        :type sda: int
        :param scl: SCL pin (I2C)
        :type scl: int
        :param display_type: use predefined values from this class:
                            sh1106 display -> Omnia1BitDisplay.SH1106
                            ssd1306 display -> Omnia1BitDisplay.SSD1306
        :type display_type: int
        """
        self.sda = sda
        self.scl = scl
        self.display_type = display_type

        await self.omniaProtocol.send([
                                self.sda,
                                self.scl,
                                self.width,
                                self.height,
                                self.display_type
                                ], OMT.ONE_BIT_DISPLAY)

    def startNotify(self):

        self.img_old = self.image
        self.resetImage()
        self.configuration["contrast"] = not self.configuration["contrast"]

    async def stopNotify(self):
        
        self.image = self.img_old
        self.configuration["contrast"] = not self.configuration["contrast"]
        
        await self.sendDisplay(True)

    async def sendDisplay(self, force_send=False):
        """Sends image to display. Avoids sending it if it didn't changed. You can send it anyway by setting force_send flag to True

        :param force_send: True if you want to force send image, defaults to False
        :type force_send: bool, optional
        """
        
        tmp_image = self.image  # tmp variable used in this method
        
        if "rotation" in self.configuration and self.configuration["rotation"]:  # if rotation is set
            tmp_image = self.image.rotate(180)

        if "contrast" in self.configuration and self.configuration["contrast"]:  # if contrast is set
            tmp_image = ImageOps.colorize(tmp_image, (255,255,255), (0,0,0))
        
        if self.img_is_new or force_send:
            self.img_is_new = False
            tmp_image = tmp_image.convert('1')  # 1-bit pixels, black and white, stored with one pixel per byte
            tmp_image = tmp_image.tobytes() # serialize image

            #self.log.debug("sending image")
            
            await self.omniaProtocol.send(tmp_image, OMT.ONE_BIT_IMAGE)

# ---------------------------------------------------- #

class OmniaTouchscreen:
    """Touchscreen utilities
    """
    def __init__(self, omniaProtocol, display_width, display_height):
        """Initialization

        :param omniaProtocol: low-level OmniaProtocol
        :type omniaProtocol: OmniaProtocol instance
        :param display_width: display's width
        :type display_width: int
        :param display_height: display's height
        :type display_height: int
        """

        ### OmniaProtocol ###
        self.omniaProtocol = omniaProtocol
        ### --- ###

        ### Coordinates ###
        self.x = 0
        self.y = 0
        ### --- ###

        ### Display ###
        self.width = display_width
        self.height = display_height
        ### --- ###

        ### Click callback ###
        self.__callback = None
        ### --- ###

        ### Debouncing timeout ###
        self.received_touch = time.time()
        self.DEBOUNCING_TIMEOUT = 300   # ms
        ### --- ###

        ### Log ###
        self.log = logging.getLogger(
            '[{}]: OmniaTouchscreen'.format(self.omniaProtocol.client_info["name"])
        )
        ### --- ###

    async def startReadingTouchscreen(self, callback):
        """Starts reading touchscreen from client

        :param callback: callback function. (x, y) tuple passed as argument
        :type callback: function object
        """

        self.__callback = callback

        # __preCallback is passed because coordinates need to be pre processed
        self.omniaProtocol.registerReceiveCallback(self.__preCallback, OMT.TOUCHSCREEN)

        await self.omniaProtocol.send([ 1 ], OMT.TOUCHSCREEN)   # tell client to start reading touchscreen

    async def stopReadingTouchscreen(self):
        """Stops reading touchscreen from client, deletes registered callback
        """

        self.__callback = None

        self.omniaProtocol.removeReceiveCallback(OMT.TOUCHSCREEN)

        await self.omniaProtocol.send([ 0 ], OMT.TOUCHSCREEN)   # tell client to stop reading touchscreen

    async def __preCallback(self, raw_coordinates):
        """Processes coordinates received from protocol

        :param raw_coordinates: received in this format: "x,y"
        :type raw_coordinates: str
        """
        raw_coordinates = raw_coordinates.decode()
        s_x = ''
        s_y = ''
        
        if len(raw_coordinates) > 0:
            if (time.time() - self.received_touch)*1000 > self.DEBOUNCING_TIMEOUT:
                self.received_touch = time.time()
                raw_coords = raw_coordinates.split(',')
                s_x = raw_coords[0]
                s_y = raw_coords[1]
                self.log.debug(f"Raw touch: x:{s_x}, y:{s_y}")
            
                if s_x.isdigit() and s_y.isdigit():
                    x = int(s_x)
                    y = int(s_y)

                    self.x = x
                    self.y = y

                    #self.x, self.y = self.scale_coords(x, y)

                    self.log.debug(f"Received: x:{self.x}, y:{self.y}")
                    
                    if self.__callback:     # call user's callback
                        self.__callback( (self.x, self.y) )
        
    def scale_coords(self, x, y):   # scale coordinates to screen dimensions
        scaled_x = abs( x - self.width)
        scaled_y = abs( y - self.height)

        return scaled_x, scaled_y

# ---------------------------------------------------- #

class OmniaILI9341Display(OmniaDisplay, OmniaTouchscreen):
    
    """Utilities for ILI9341 display. Extends OmniaDisplay and OmniaTouchscreen
    """
    def __init__(self, omniaProtocol, dimensions, image_mode="RGBA"):
        """Initialization

        :param omniaProtocol: low-level OmniaProtocol
        :type omniaProtocol: OmniaProtocol instance
        :param dimensions: width, length of the display
        :type dimensions: tuple or list
        :param image_mode: image mode, please refer to pillow modes (https://pillow.readthedocs.io/en/stable/handbook/concepts.html#concept-modes), defaults to "RGBA"
        :type image_mode: str, optional
        """
        OmniaDisplay.__init__(self, omniaProtocol, dimensions, image_mode=image_mode)

        OmniaTouchscreen.__init__(self, omniaProtocol, self.width, self.height)
        
        ### Log ###
        self.log = logging.getLogger(
            '[{}]: OmniaILI9341Display'.format(self.omniaProtocol.client_info["name"])
        )
        ### --- ###

    async def sendDisplay(self, image_format='jpeg'):
        """Send image display, encoding it with format

        :param image_format: image format encoding, defaults to 'jpeg'. Refer to pillow image formats (https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html)
        :type image_format: str, optional
        """
        f = io.BytesIO()    # temp I/O file object
        image = self.image.convert("RGB")   # convert image to RGB for ILI9341 display
        image.save(f, image_format)
        buf = f.getbuffer() # buffer from I/O file object

        await self.omniaProtocol.send(buf, OMT.RGBA_IMAGE)

        del buf     # delete buffer, so that temp I/O file object can be closed
        f.close()   # close temp I/O file object

