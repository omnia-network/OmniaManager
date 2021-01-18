import time
import curio
import logging
from numpy.random 			import randint

class NotifyService:
    def __init__(self, username, omnia1BitDisplay, omniaPins, omniaController):

        self.username = username

        ### Omnia libraries
        self.omnia1BitDisplay = omnia1BitDisplay
        self.omniaPins = omniaPins
        self.omniaController = omniaController
        ### --- ###

        ### Devices ###
        self.recentDevices = []
        #self.nearDeavices=[]
        self.device = 0
        ### --- ###

        ### Flags ###
        self.stop = False
        self.accepted = False
        ### --- ###

        ### Log ###
        self.log = logging.getLogger(
            '[{}]: NotifyService'.format(self.username)
        )
        ### --- ###

    async def clickButtonCallback(self, clickedBtn):
        self.log.debug("clicked " + clickedBtn)
        if(clickedBtn == "SELECT"):
            self.stop = True
            self.accepted = True
        
        elif(clickedBtn == "DOWN"):
            self.stop = True
                
        elif(clickedBtn == "UP"):
            self.stop = True

    async def run(self):

        self.log.debug("started")

        while True:
            devs = await self.omniaController.listNearDevices(self.username)
            
            for dev in devs: 
                if (not dev in self.recentDevices) and dev.getStreamingUser() == "" and not dev.canStreamLater(self.username):
                    dev.setStreamingUser(self.username)
                    self.device=dev

            for dev in self.recentDevices:
                if(not (dev in devs)):
                    self.recentDevices.remove(dev)

            if(self.device):
                self.omnia1BitDisplay.startNotify()
                self.omniaPins.registerInputCallback(self.clickButtonCallback)

                self.log.debug("new notification for "+self.username)

                color = list(randint(0,32,3))
                await self.omniaPins.setNeopixelPin("NEO1", color)
                self.omnia1BitDisplay.image_draw.text((40,0), "NOTIFY", 255, self.omnia1BitDisplay.FONT_ARIAL_11)
                self.omnia1BitDisplay.image_draw.text((10,20), "FOUND", 255, self.omnia1BitDisplay.FONT_ARIAL_11)

                devType = self.device.getDeviceType()

                iot_function = self.omniaController.getIOTFunction(self.username, devType)
                
                notifMsg = iot_function.getNotificationMessage(self.device.getName())
                
                for line in notifMsg:
                    self.omnia1BitDisplay.image_draw.text(line[0], line[1], 255, self.omnia1BitDisplay.FONT_ARIAL_11)

                await self.omnia1BitDisplay.sendDisplay()

                self.stop = False
                self.accepted = False
                startTime = time.time()

                while(not self.stop):
                    if time.time() - startTime > 30:
                        self.stop = True
                    
                    await asyncio.sleep(0.1)

                if self.accepted:
                    await iot_function.handleStreaming(self.device)
                    await self.device.runIOTFunction(iot_function)
                else:
                    await self.device.resetStreamingUser()

                await self.omniaPins.setNeopixelPin("NEO1", [0, 0, 0])
                
                await self.omnia1BitDisplay.stopNotify()
                self.omniaPins.restoreInputCallback()
                
                self.device = 0
            
            await curio.sleep(0.1)
            
    def getUsedDevices(self):
        return self.recentDevices

