import numpy
import curio

class Menu:
    def __init__(self, applications, omnia1BitDisplay, omniaPins, omniaController):

        ### Omnia libraries
        self.omnia1BitDisplay = omnia1BitDisplay
        self.omniaPins = omniaPins
        self.omniaController = omniaController
        ### --- ###

        self.n = int(self.omnia1BitDisplay.height/10) - 1

        self.applications = applications
        self.i = 0
        self.i_app = 0

        self.changed = True
        self.next_app = False
        self.close_app = False

        self.page = 1
    
    async def clickCallback(self, clickedBtn):
        if(clickedBtn == "SELECT"):
            self.i_app=self.i
            self.close_app = True
        
        elif(clickedBtn == "DOWN"):
            if(self.i==len(self.applications)-1):
                self.i=0
            else:
                self.i+=1

            self.page=int(self.i/self.n)+1
            self.changed=True
                
        elif(clickedBtn == "UP"):
            if(self.i==0):
                self.i=len(self.applications)-1
            else:
                self.i-=1

            self.page=int(self.i/self.n)+1
            self.changed=True

    async def run(self, firstApp=-1):

        self.omniaPins.registerInputCallback(self.clickCallback)

        self.changed = True

        if firstApp >= 0:
            self.applications[firstApp][1].run()
        
        pages=int(numpy.ceil(len(self.applications)/self.n))
        
        while not self.close_app :
            if (self.changed):
                self.omnia1BitDisplay.resetImage()
                self.omnia1BitDisplay.image_draw.text((45,0),"MENU "+str(self.page)+"\\"+str(pages), 255,self.omnia1BitDisplay.FONT_ARIAL_11)
                self.omnia1BitDisplay.image_draw.text((1,10+(self.i%self.n)*10),">", 255,self.omnia1BitDisplay.FONT_ARIAL_11)
                self.omnia1BitDisplay.image_draw.text((10,10),self.applications[self.n*(self.page-1)], 255,self.omnia1BitDisplay.FONT_ARIAL_11)
                for x in range(0,self.n-1):
                    if((self.page-1)*self.n+x+1<len(self.applications)):
                        self.omnia1BitDisplay.image_draw.text((10,10+(x+1)*10),self.applications[(self.page-1)*self.n+x+1], 255,self.omnia1BitDisplay.FONT_ARIAL_11)

                await self.omnia1BitDisplay.sendDisplay()
                self.changed=False
            
            await curio.sleep(0.1)

        self.close_app = False

        return self.i_app
