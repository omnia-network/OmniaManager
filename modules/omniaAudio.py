class OmniaAudio:
    """Utility to play audio on clients
    """

    def __init__(self, omniaProtocol):
        """Initialization

        :param omniaProtocol: low-level OmniaProtocol
        :type omniaProtocol: OmniaProtocol instance
        """

        ### OmniaProtocol ###
        self.omniaProtocol = omniaProtocol
        ### --- ###

    async def startAudio(self, framerate, channels, sampwidth, chunk_size):
        """Start client's audio player

        :param framerate: audio's framerate
        :type framerate: int
        :param channels: audio's channels
        :type channels: int
        :param sampwidth: audio's sample width
        :type sampwidth: int
        :param chunk_size: audio's chunk size
        :type chunk_size: int
        """
        
        await self.omniaProtocol.send([
            1, 
            framerate, 
            channels, 
            sampwidth, 
            chunk_size
                ], OMT.SET_AUDIO)
    
    async def stopAudio(self, notify=True):
        """Stops audio player
        """
        
        await self.omniaProtocol.send([
            0
            ], OMT.SET_AUDIO)
    
    async def sendAudio(self, samples):
        """Sends audio chunk to client

        :param samples: audio chunk
        :type samples: bytes
        """
        await self.omniaProtocol.send( samples, OMT.AUDIO_CHUNK)