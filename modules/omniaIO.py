import json
import logging

### Omnia libraries ###
from core.omniaMessageTypes      import OmniaMessageTypes as OMT
### --- ###

class OmniaPins:
    """Utilities to handle Input, Output, PWM, NeoPixel pins
    """

    ### Pin modes ###
    INPUT_MODE = "in"
    OUTPUT_MODE = "out"
    NEOPIXEL_MODE = "neopixel"
    PWM_MODE = "pwm"

    def __init__(self, omniaProtocol, pinout={}):
        """Initializes instance.
        Pinout structure:
            KEYS:   "in" -> Input pins
                    "out" -> Output pins
                    "neopixel" -> Neeopixel pins
                    "pwm" -> PWM pins
            
            Inside those keys you must declare each pin as follows:
                "<pin-name>": {
                                "number": <pin-number>
                                }

            NOTE: Pin names and numbers cannot be repeated.
        
        Example pinout structure:
            "in":{
                "UP": {
                    "number": 12
                },
                "DOWN": {
                    "number": 13
                }
            },
            "out": {
                "LED": {
                    "number": 16
                }
            },
            "neopixel":{
                "NEO1": {
                    "number":15
                }
            }

        :param omniaProtocol: low-level OmniaProtocol
        :type omniaProtocol: OmniaProtocol instance
        :param pinout: pinout dictionary, defaults to {}
        :type pinout: dict, optional
        """

        ### OmniaProtocol ###
        self.omniaProtocol = omniaProtocol
        ### --- ###

        ### Pinout ###
        self.pinout = pinout
        self.pin_modes = [self.INPUT_MODE, self.OUTPUT_MODE, self.NEOPIXEL_MODE, self.PWM_MODE]
        ### --- ###

        ### Callback ###
        self.__old_callback = None  # callback memory
        self.__callback = None      # callback of the user

        self.__high_pins = {}     # pins state (received and decoded from omniaProtocol)
        ### --- ###

        ### Log ###
        self.log = logging.getLogger(
            '[{}]: OmniaPins'.format(self.omniaProtocol.client_info["name"])
        )
        ### --- ###
    
    async def loadPinoutFromJSON(self, pinout_json_path):
        """Loads pinout setup from JSON and sends INPUT pins to client

        :param pinout_json_path: JSON file path
        :type pinout_json_path: str
        """

        with open(pinout_json_path, "r") as j:
            tmp = json.load(j)

            for pin_mode in self.pin_modes:     # load only valid pin modes (for safe)
                if pin_mode in tmp:
                    self.pinout.update({ pin_mode: tmp[pin_mode] })
        
        await self.sendInPins()
    
    async def sendInPins(self):
        """Set client INPUT pins from pinout configuration
        """
        for pin in self.pinout[self.INPUT_MODE]:
            await self.sendInPin(self.pinout[self.INPUT_MODE][pin]['number'])
    
    async def sendInPin(self, pin):
        """Set client INPUT pin

        :param pin: pin number
        :type pin: int
        """
        await self.omniaProtocol.send([ pin ], OMT.INPUT_PIN)
    
    def setPin(self, pin_number, pin_name, pin_mode):
        """Sets pin to pin_mode and send it to client if pin_mode="in". Checks if pin is not already configured.

        :param pin_number: pin number
        :type pin_number: int
        :param pin_name: pin name
        :type pin_name: str
        :param pin_mode: pin mode, must be one among these: "in", "out", "neopixel", "pwm"
        :type pin_mode: str
        """

        if not pin_mode in self.pin_modes:
            #raise ValueError("{} mode is not valid".format(pin_mode))
            self.log.error("{} mode is not valid".format(pin_mode))
            return
        
        pin_already_configured = False      # checked at the end of for
        pin_mode_already_configured = ""    # needed to log / raise error

        for p_mode in self.pinout:    # for every pin_mode in pinout
            
            for pin in self.pinout[p_mode]:   # for every pin in this pin mode
                
                if pin_number == self.pinout[p_mode][pin]["number"]:    # check if pin number alredy exists
                    #raise ValueError("A pin with number {} is already configured in '{}' mode".format(pin_number, p_mode))
                    self.log.error("A pin with number {} is already configured in '{}' mode".format(pin_number, p_mode))
                    pin_already_configured = True   # raise flag
                    break
                
                elif pin_name == pin: # check if pin name alredy exists
                    #raise ValueError("A pin with name '{}' is already configured in '{}' mode".format(pin_name, p_mode))
                    self.log.error("A pin with name '{}' is already configured in '{}' mode".format(pin_name, p_mode))
                    pin_already_configured = True   # raise flag
                    break
                
        if not pin_already_configured:  # new pin can be registered
            if pin_mode in self.pinout:
                self.pinout[pin_mode].update({ pin_name : { "number": pin_number }})
            else:
                self.pinout[pin_mode] = { pin_name : { "number": pin_number }}
            
            if pin_mode == self.INPUT_MODE:
                self.sendInPin(pin_number)
    
    async def removePin(self, pin_name):
        """Remove pin from pinout, pin_name is used for identification.
        If pin is an input, send remove message to client

        :param pin_name: pin name
        :type pin_name: str
        """

        removed = False

        for p_mode in self.pinout:    # for every pin_mode in pinout
            for p_name in self.pinout[p_mode]: # for every pin in this pin mode
                if p_name == pin_name:
                    p = self.pinout[p_mode].pop(pin_name)
                    
                    await self.omniaProtocol.send([ p["number"] ], OMT.REMOVE_INPUT_PIN)

                    removed = True
                    self.log.info("Pin '{}' removed from '{}' mode".format(pin_name, p_mode))
                    break
        
        if not removed:
            #raise ValueError("Pin with name '{}' not found".format(pin_name))
            self.log.error("Pin with name '{}' not found".format(pin_name))
    
    async def setOutPin(self, pin_name, value):
        """Sets client OUTPUT pin. Checks if pin is in "out" mode, otherwise raise an error

        :param pin_name: OUTPUT pin name
        :type pin_name: str
        :param value: pin value (True or False)
        :type value: bool
        """
        if pin_name in self.pinout[self.OUTPUT_MODE]:
            pin_number = self.pinout[self.OUTPUT_MODE][pin_name]["number"]

            await self.omniaProtocol.send([ pin_number, int(not value) ], OMT.OUTPUT_PIN) # value is negated to control ESP8266 pins properly
        
        else:
            #raise ValueError("Pin '{}' is not registered as 'out' mode".format(pin_name))
            self.log.error("Pin '{}' is not registered as 'out' mode".format(pin_name))
    
    async def setPwmPin(self, pin_name, frequency, duty):
        """Set client PWM pin. Checks if pin is in "pwm" mode, otherwise raise an error

        :param pin_name: PWM pin name
        :type pin_name: str
        :param frequency: PWM frequency
        :type frequency: int
        :param duty: PWM duty cycle
        :type duty: int
        """

        if pin_name in self.pinout[self.PWM_MODE]:
            pin_number = self.pinout[self.PWM_MODE][pin_name]["number"]

            await self.omniaProtocol.send([ pin_number, frequency, duty ], OMT.PWM_PIN)
        
        else:
            #raise ValueError("Pin '{}' is not registered as 'pwm' mode".format(pin_name))
            self.log.error("Pin '{}' is not registered as 'pwm' mode".format(pin_name))
    
    async def setNeopixelPin(self, pin_name, rgb, notify=False):
        """Sets client Neopixel pin. Checks if pin is in "neopixel" mode, otherwise raise an error

        :param pin_name: NeoPixel pin name
        :type pin_name: str
        :param rgb: red, green, blue values (from 0 to 255)
        :type rgb: list or tuple
        """

        if pin_name in self.pinout[self.NEOPIXEL_MODE]:
            pin_number = self.pinout[self.NEOPIXEL_MODE][pin_name]["number"]

            red = rgb[0]
            green = rgb[1]
            blue = rgb[2]

            await self.omniaProtocol.send([ pin_number, red, green, blue ], OMT.NEOPIXEL_PIN)
        
        else:
            #raise ValueError("Pin '{}' is not registered as 'neopixel' mode".format(pin_name))
            self.log.error("Pin '{}' is not registered as 'neopixel' mode".format(pin_name))

    def registerInputCallback(self, callback):
        """Registers callback. Saves current callback, that can be restored using restoreInputCallback().
        Registers callback to omniaProtocol.

        :param callback: callback function
        :type callback: function object
        :param recv_type: type of the message expected to be received, use types from OmniaMessageTypes
        :type recv_type: str
        """
        self.__old_callback = self.__callback
        self.__callback = callback

        # register '__receivedHighPins(data)' because data received from omniaProtocol
        # need to be processed before being passed to the user's callback
        self.omniaProtocol.registerReceiveCallback(self.__receivedHighPins, OMT.INPUT_PIN)    # register class callback to omniaProtocol
    
    def restoreInputCallback(self):
        """Restores callback to the one saved by registerInputCallback()
        """
        self.__callback = self.__old_callback
    
    async def __receivedHighPins(self, data):
        """Set clicked buttons to '1' and do callback only for the "last" clicked button. (improvement needed)

        :param data: sum of all the values corresponding to each HIGH pin,
                     each value is calculated as 1 << (pin number)
        :type data: bytes
        """
        data = int(data)

        high_pin = None

        for pin in self.pinout["in"]:
            if(data & 1<<self.pinout["in"][pin]["number"]):
                self.__high_pins[pin] = 1     # record all clicked buttons of the last receive in case it's needed to know them 
                high_pin = pin    # record the last clicked button
            else:
                self.__high_pins[pin] = 0
        
        if high_pin:
            self.log.debug("clicked {!r}".format(high_pin))
            if self.__callback:
                await self.__callback(high_pin)   # call user's callback

# ---------------------------------------------------- #

class OmniaADC:
    """Utility to read ADC values from clients
    """

    def __init__(self, omniaProtocol):
        """Initialization

        :param omniaProtocol: low-level OmniaProtocol
        :type omniaProtocol: OmniaProtocol instance
        """

        ### OmniaProtocol ###
        self.omniaProtocol = omniaProtocol
        ### --- ###

        ### Callback ###
        self.__callback = None
        ### --- ###

        ### Log ###
        self.log = logging.getLogger(
            '[{}]: OmniaADC'.format(self.omniaProtocol.client_info["name"])
        )
        ### --- ###
    
    async def startRecv(self, pin_number, callback):
        """Start reading ADC values from pin_number client pin.
        Registers callback to omniaProtocol

        :param pin_number: pin number from which to read ADC values
        :type pin_number: int
        :param callback: callback function, called when ADC value is received
        :type callback: function
        """
        self.__callback = callback

        # register '__received(data)' because data received from omniaProtocol
        # need to be processed before being passed to the user's callback
        self.omniaProtocol.registerReceiveCallback(self.__received, OMT.READ_ADC)    # register class callback to omniaProtocol

        await self.omniaProtocol.send([ 1, pin_number ], OMT.READ_ADC)
    
    async def stopRecv(self):
        """Stop receiving ADC from client. Restores previous omniaProtocol callback
        """
        await self.omniaProtocol.send([ 0 ], OMT.READ_ADC)
        
        self.omniaProtocol.restoreReceiveCallback(OMT.READ_ADC)
    
    def __received(self, data):
        data = int(data)
        self.__callback(data)   # user's callback

# ---------------------------------------------------- #

class OmniaI2C:
    """Utility to read I2C values from clients
    """

    def __init__(self, omniaProtocol):
        """Initialization

        :param omniaProtocol: low-level OmniaProtocol
        :type omniaProtocol: OmniaProtocol instance
        """

        ### OmniaProtocol ###
        self.omniaProtocol = omniaProtocol
        ### --- ###

        ### Callback ###
        self.__callback = None
        ### --- ###

        ### Log ###
        self.log = logging.getLogger(
            '[{}]: OmniaI2C'.format(self.omniaProtocol.client_info["name"])
        )
        ### --- ###
    
    async def setI2C(self, sda, scl):
        """Set I2C SDA and SCL on client

        :param sda: SDA pin (I2C)
        :type sda: int
        :param scl: SCL pin (I2C)
        :type scl: int
        """
        self.log.debug("setting I2C")
        
        await self.omniaProtocol.send([ sda, scl ], OMT.SET_I2C)

    async def startRecv(self, i2c_address, read_length, callback):
        """Start reading I2C values from pin_number client pin.
        Registers callback to omniaProtocol.

        :param i2c_address: I2C address from which you want to read data
        :type i2c_address: int
        :param read_length: how much data you want to read (in bytes)
        :type read_length: int
        :param callback: callback function, called when I2C value is received
        :type callback: function object
        """

        self.log.debug("start receiving I2C")

        self.__callback = callback

        self.omniaProtocol.registerReceiveCallback(self.__callback, OMT.READ_I2C)    # register user's callback to omniaProtocol

        await self.omniaProtocol.send([ 1, i2c_address, read_length ], OMT.READ_I2C)
    
    async def stopRecv(self):
        """Stop receiving I2C from client. Restores previous omniaProtocol callback.
        """

        await self.omniaProtocol.send([ 0 ], OMT.READ_I2C)
        
        self.omniaProtocol.restoreReceiveCallback(OMT.READ_I2C)

        self.log.debug("stop receiving I2C")