import curio

class Settings:
    def __init__(self, username, omnia1BitDisplay, omniaPins, omniaController):
        self.username = username

        ### Omnia libraries
        self.omnia1BitDisplay = omnia1BitDisplay
        self.omniaPins = omniaPins
        self.omniaController = omniaController
        ### --- ###
        
        self.contrast = False
        self.rotation = True
        self.i = 0
        self.changed = True
        self.close_app = False
    
    async def clickCallback(self, clickedBtn):
        if(clickedBtn == "SELECT"):
            if(self.i==2):
                self.close_app=True
            elif(self.i==1):
                self.rotation = not self.rotation
                self.omnia1BitDisplay.setRotation(self.rotation)
                self.changed=True
            elif(self.i==0):
                self.contrast = not self.contrast
                self.omnia1BitDisplay.setContrast(self.contrast)
                self.changed=True
        
        elif(clickedBtn == "DOWN"):
            if(self.i==2):
                self.i=0
            else:
                self.i+=1

            self.changed=True
            
        elif(clickedBtn == "UP"):
            if(self.i==0):
                self.i=2
            else:
                self.i-=1
            
            self.changed=True

    async def run(self):

        self.omniaPins.registerInputCallback(self.clickCallback)

        self.changed=True
        self.close_app=False
        
        while not self.close_app:
            if (self.changed):
                self.changed=False
                self.omnia1BitDisplay.resetImage()

                self.omnia1BitDisplay.image_draw.text( (35,0), "SETTINGS ", 255, self.omnia1BitDisplay.FONT_ARIAL_11)
                self.omnia1BitDisplay.image_draw.text( (10,10), "CONTRAST ", 255, self.omnia1BitDisplay.FONT_ARIAL_11)
                self.omnia1BitDisplay.image_draw.text( (10,20), "ROTATION ", 255, self.omnia1BitDisplay.FONT_ARIAL_11)
                self.omnia1BitDisplay.image_draw.text( (10,30), "MENU ", 255, self.omnia1BitDisplay.FONT_ARIAL_11)
                self.omnia1BitDisplay.image_draw.text( (1,10+self.i*10), ">", 255, self.omnia1BitDisplay.FONT_ARIAL_11)
                
                await self.omnia1BitDisplay.sendDisplay()
            
            await curio.sleep(0.1)

        self.close_app = False

        return -1



