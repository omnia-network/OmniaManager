import curio
import numpy

class Devices:

    def __init__(self, username, omnia1BitDisplay, omniaPins, omniaController):
        self.username = username

        ### Omnia libraries
        self.omnia1BitDisplay = omnia1BitDisplay
        self.omniaPins = omniaPins
        self.omniaController = omniaController
        ### --- ###

        self.changed = True
        self.close_app = False
        
        self.n = int(self.omnia1BitDisplay.height/10) - 1

        self.devices = []
        self.i = 0

        self.changed = True
        self.next_app = False
        self.close_app = False

        self.page = 1

    async def clickCallback(self, clickedBtn):

        self.changed = True

        if(clickedBtn == "SELECT"):
            if (self.i == len(self.devices)):
                self.close_app = True
            else:
                device = self.devices[self.i]
                #print(device.name)
                if device.getStreamingUser() == self.username:
                    await device.resetStreamingUser()
                elif device.getStreamingUser() == '':
                    devType = device.getDeviceType()
                    iot_function = self.omniaController.getIOTFunction(self.username, devType)
                    device.setStreamingUser(self.username)
                    iot_function.handleStreaming(device)
                    await device.runIOTFunction(iot_function)

        elif(clickedBtn == "DOWN"):
            if(self.i == len(self.devices)):    # go down until "MENU"
                self.i = 0
            else:
                self.i += 1

            self.page = int(self.i/self.n) + 1
                
        elif(clickedBtn == "UP"):
            if(self.i == 0):
                self.i = len(self.devices)  # go to "MENU"
            else:
                self.i -= 1

            self.page = int(self.i/self.n) + 1


    async def run(self):

        self.omniaPins.registerInputCallback(self.clickCallback)

        self.changed = True		

        while not self.close_app:
            self.devices = await self.omniaController.listNearDevices(self.username)
            pages = int(numpy.ceil(len(self.devices) / self.n))
            if pages == 0: pages = 1
            
            if self.changed:
                self.omnia1BitDisplay.resetImage()
                self.omnia1BitDisplay.image_draw.text((45,0),"DEVICES "+str(self.page)+"\\"+str(pages), 255,self.omnia1BitDisplay.FONT_ARIAL_11)
                self.omnia1BitDisplay.image_draw.text((1,10+(self.i%self.n)*10),">", 255,self.omnia1BitDisplay.FONT_ARIAL_11)
                # self.omnia1BitDisplay.image_draw.text((10,10),self.devices[self.n*(self.page-1)], 255,self.omnia1BitDisplay.FONT_ARIAL_11)
                for x in range(0,self.n-1):
                    if((self.page-1)*self.n+x < len(self.devices)):
                        dev = self.devices[(self.page-1)*self.n+x]
                        self.omnia1BitDisplay.image_draw.text((10,10+(x)*10), dev.name, 255,self.omnia1BitDisplay.FONT_ARIAL_11)
                        if dev.stream:
                            self.omnia1BitDisplay.image_draw.text((80,10+ 10*x),"<->", 255, self.omnia1BitDisplay.FONT_ARIAL_11)
                
                if self.page == pages:
                    self.omnia1BitDisplay.image_draw.text((10, 10 + len(self.devices) % self.n * 10), "MENU", 255, self.omnia1BitDisplay.FONT_ARIAL_11)

                await self.omnia1BitDisplay.sendDisplay()
                self.changed=False
    
            await curio.sleep(0.1)

        self.close_app = False
        return -1


