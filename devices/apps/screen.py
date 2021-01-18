# install opencv: https://stackoverflow.com/a/60201245/5094892
# run python3: LD_PRELOAD=/usr/lib/arm-linux-gnueabihf/libatomic.so.1 python3
import cv2
from PIL import Image
import io
import curio

### Omnia libraries ###
from modules.omniaDisplay           import OmniaILI9341Display, OmniaTouchscreen, OmniaDisplay
### --- ###

class Screen():
    def __init__(self, username, omniaController):
        self.device = 0
        self.username = username
        self.omniaController = omniaController

        self.omniaProtocol = None

        self.omniaDisplay = None
        self.omniaTouchscreen = None

        self.width = 540
        self.height = 1170

        self.fps = 30

        self.time_sleep = 1/self.fps
        
        self.vidcap = cv2.VideoCapture('devices/resources/video/gaber.mp4')
        self.success = None
        self.image = None
        self.count = 0
        
        ## touch
        self.x = 0
        self.y = 0

    def getNotificationMessage(self, deviceName, username=None):

        msg = []

        msg.append([(10, 35), deviceName.replace("_", " ").upper()])
        msg_status = "START STREAM?"
        
        msg.append([(10,50), msg_status])

        return msg
    
    async def handleStreaming(self, device):
        if self.device != device:
            if self.device != 0:
                await self.stop()
            
            old_device = self.device
            self.__setDevice(device)
            if old_device != 0:
                await old_device.resetStreamingUser()
    
    def __setDevice(self, device):
        self.device = device
        self.omniaProtocol = self.device.omniaProtocol

        #self.omniaDisplay = OmniaILI9341Display(self.omniaProtocol, (self.width,self.height))
        self.omniaDisplay = OmniaDisplay(self.omniaProtocol, (self.width, self.height))
        self.omniaTouchscreen = OmniaTouchscreen(self.omniaProtocol, self.width, self.height)

    def touchCallback(self, xy_coordinates):

        self.x = xy_coordinates[0]
        self.y = xy_coordinates[1]

    async def start(self):
        await self.omniaTouchscreen.startReadingTouchscreen(self.touchCallback)

        self.success, self.image = self.vidcap.read()
        self.count = 0

        await self.omniaDisplay.startVideoStream()
    
    async def stop(self):
        await self.omniaDisplay.stopVideoStream()
        await self.omniaTouchscreen.stopReadingTouchscreen()

    async def run(self):        

        if self.device:

            if self.success:
                if self.y < 150:
                    im=Image.fromarray(self.image)
                    #im=im.rotate(90, expand=True)
                    im=im.convert("RGB")
                    im=im.resize((self.width,self.height))

                    await self.omniaDisplay.sendVideoFrame(im)

                    for _ in range(2):
                        self.success, self.image = self.vidcap.read()
                        self.count += 1
                else:
                    await self.omniaDisplay.sendVideoFrame()    # send empty array
            else:
                await self.omniaDisplay.stopVideoStream()
