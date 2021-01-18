import logging
import struct
import curio
import time

### Omnia libraries ###
from core.omniaMessageTypes      import OmniaMessageTypes
### --- ###

class OmniaProtocol(OmniaMessageTypes):
    """OmniaProtocol is the low lewel class, that handles the communication with the client.
        
        It gets the socket object and converts it into a pair of StreamReader and StreamWriter objects.
    """

     #*****VERSION*****#
    __version__ = "0.5.1"

    def getVersion(self):
        return self.__version__
    
    def __init__(self, socket, client_info):
        """Initialize OmniaProtocol class

        :param socket: opened socket with client
        :type socket: socket.socket
        :param client_info: info of the client that instantiated the class:
                            
                            a. if instanciated by User class
                            {
                                "name": "user_name",
                                "uid": "user id",    # RFID or BLE
                                "type": "user"
                            }
                            
                            b. if instanciated by Device class
                            {
                                "name": "device_name",
                                "class": "device_type"
                                "type": "device"
                            }
                            
        :type client_info: dict
        """

        ### Client data ###
        '''
        if instanciated by User class
        {
            "name": "user_name",
            "uid": "user id",    # RFID or BLE
            "type": "user"
        }
        '''
        '''
        if instanciated by Device class
        {
            "name": "device_name",
            "class": "device_type"
            "type": "device"
        }
        '''
        self.client_info = client_info
        self.client_type = self.client_info["type"]
        ### --- ###

        ### Tasks ###
        self.taskGroup = curio.TaskGroup()
        ### --- ###

        ### Network I/O ###
        self.socket = socket
        self.alive = True   # set to False when resuming
        ### --- ###
        
        ### Latency ###
        self.l_time = 0.0   # time before sending latency message
        self.latency = 0.0
        self.tot_latency = 0.0  # sum of latency iterations
        self.latency_iterations = 10    # number of iterations
        self.n_latency_sent = 0        # number of latency messages sent
        self.__final_latency_callback = None
        ### --- ###

        ### Callbacks ###
        self.__receive_callbacks = {}
        self.__old_receive_callbacks = {}
        ### --- ###

        ### Tasks ###
        self.recv_task = None
        self.tasks = [] # tasks created by the user
        ### --- ###

        ### Log ###
        self.log = logging.getLogger(
            '[{}]: OmniaProtocol'.format(self.client_info["name"])
        )
        ### --- ###
    
    ### RECEIVE ###

    async def recv(self):
        """Receiving Task
        """
        self.log.debug("RECV TASK STARTED")
        while True:
            #self.log.debug("receiving data")
            
            if self.alive:  # check if protocol is not resuming
                
                try:
                    data = await self.socket.readline()
                    data = bytearray(data).replace(b'\n',b'')   # remove end-line character
                    
                    if len(data) > 0:
                        recv_type = chr(data[0])    # get message type
                        data = data[1:]     # remove message type from data
                        
                        self.log.debug(f"received (type: '{recv_type}'): {data}")
                        
                        if recv_type in self.__receive_callbacks:    # if received message is of this type is expected
                            #self.log.debug(f"calling callback: {self.__receive_callbacks[recv_type]}")
                            await self.__receive_callbacks[recv_type](data)
                        else:
                            self.log.warning("Received message of type '{}' not expected".format(recv_type))
                        
                        '''for r in self.__receive_callbacks:
                            await self.__receive_callbacks[r](data)'''
                except:
                    pass
            
            else:
                break
    
        self.log.debug("recv finished")

    def registerReceiveCallback(self, callback, recv_type):
        """Registers callback, called when message of type 'recv_type' is received.
        Stores the previous callback, that can be restored by calling restoreReceiveCallback()

        :param callback: callback function
        :type callback: function object
        :param recv_type: type of the message expected to be received, use types from OmniaMessageTypes
        :type recv_type: str
        """
        if recv_type in self.__receive_callbacks:
            self.__old_receive_callbacks[recv_type] = self.__receive_callbacks[recv_type]
        
        self.__receive_callbacks[recv_type] = callback

        self.log.debug(f"Registering callback: {callback} of type '{recv_type}'")
    
    def removeReceiveCallback(self, recv_type):
        """Removes the received callback with this recv_type

        :param recv_type: type of the message expected to be received, use types from OmniaMessageTypes
        :type recv_type: str
        """
        if recv_type in self.__old_receive_callbacks:
            self.__old_receive_callbacks[recv_type].pop(recv_type)
        
        if recv_type in self.__receive_callbacks:
            cb = self.__receive_callbacks.pop(recv_type)
            self.log.debug(f"Removing callback: {cb} of type '{recv_type}'")
    
    def restoreReceiveCallback(self, recv_type):
        """Restores receive callback to the one saved by registerReceiveCallback()

        :param recv_type: type of the message expected to be received, use types from OmniaMessageTypes
        :type recv_type: str
        """
        if recv_type in self.__old_receive_callbacks:
            self.__receive_callbacks[recv_type] = self.__old_receive_callbacks[recv_type]

    ### END RECEIVE ###

    ### SEND ###

    async def send(self, message, msg_type):
        """Send message to client using the StreamWriter and call the writer.drain() coro.
        If message is a list, convert it to string with '-' separator between elements, then encode.

        :param message: message to be sent
        :type message: list or bytes
        :param msg_type: type of the message to be sent, use values from OmniaMessageTypes class 
        :type msg_type: str
        """
        if self.alive:   # check if protocol is not resuming
            try:
                message = self.__prepareMsg(message, msg_type)
                message = self.__addMsgLength(message)

                await self.socket.write(message)
            except:
                pass
    
    def __prepareMsg(self, msg, msg_type):
        """Prepare the message to be sent:
            1. if message is a list, convert it to string with '-' separator between elements.
            2. add encoded msg_type in front
            3. add lenght of the entire msg_type+message in front 

        :param msg: message to be sent, could be either a list or bytes, depending on the msg_type
        :type msg: list or bytes
        :param msg_type: type of the message to be sent, use values from OmniaMessageTypes class 
        :type msg_type: str
        :return: encoded message with its length on front
        :rtype: bytes
        """

        if type(msg) == list:
            msg = '-'.join(map(str, msg)) # msg string format "<param1>-<param2>-..."
            msg = msg.encode()  # encode message to byte string
        
        b_msg_type = msg_type.encode()  # encode message type to byte string
        
        to_send = b_msg_type + msg 

        #self.log.debug("sending message: {}".format(to_send))

        return to_send

    def __addMsgLength(self, msg):
        """Calculate lenght of msg and pack it at the beginning

        :param msg: message to be sent
        :type msg: bytes 
        :return: message packed with its lenght
        :rtype: bytes
        """

        msg = struct.pack('>I', len(msg)) + msg     # prefix each message with a 4-byte length (network byte order)
        return msg
    
    ### END SEND ###

    ### LOOP ###

    async def begin(self, loop):
        """Start the receive task and run loop continuously

        :param loop: continuous loop to be awaited
        :type loop: coroutine
        """

        # create receive task
        self.recv_task = await self.taskGroup.spawn(self.recv)

        await self.calculateLatency()

        loop_task = await self.addTask(loop)

        await loop_task.join()

    async def addTask(self, task, wait_for_execution=False):
        """Create new task using curio.spawn().

        :param task: coroutine to be scheduled
        :type task: Coroutine
        :param wait_for_execution: True if you want to wait for task execution and get the result, defaults to False
        :type wait_for_execution: bool, optional
        :return: scheduled task if wait_for_execution is False, task's result if wait_for_execution is True
        :rtype: curio.Task or task's result
        """
        t = await self.taskGroup.spawn(task)    # spawn task in taskGroup

        self.tasks.append(t)    # keep task, could be used later

        if wait_for_execution:
            return await t.join()
        else:
            return t
    
    ### END LOOP ###

    async def resumeSocket(self, new_socket, recalc_latency=True):
        """Close old socket, restart recv_task and recalculate latency if recalc_latency is True

        :param new_socket: new curio opened socket
        :type new_socket: curio.Socket
        :param recalc_latency: False if you want to skip latency calculation, defaults to True
        :type recalc_latency: bool, optional
        """
        self.alive = False
        
        await self.recv_task.cancel()

        await self.socket.flush()
        await self.socket.close()

        self.socket = new_socket

        self.alive = True

        # create receive task
        self.recv_task = await self.taskGroup.spawn(self.recv)

        await self.calculateLatency()   # recalculate latency

        self.log.debug("resumed")
    
    ### LATENCY ###

    async def __latencyCallback(self, response):
        """Calculate latency (in ms) by averaging all latency readings

        :param response: latency message from protocol
        :type response: str
        """

        if response != '':
            self.tot_latency += (time.time() - float(response)) / 2     # server to client message latency
            
            if self.n_latency_sent == self.latency_iterations:  # reached desired number of sent messages 

                self.latency = (self.tot_latency / self.n_latency_sent) * 1000  # latency (in ms)

                self.n_latency_sent = 0

                self.log.debug("latency: {} ms".format(self.latency))

                self.removeReceiveCallback(self.LATENCY)    # latency callback not needed anymore

                # if there's a registered callback, call it with the result
                if self.__final_latency_callback:
                    self.__final_latency_callback(self.latency)
            else:
                await self.__sendLatencyMessage()

    async def __sendLatencyMessage(self):
        """Send message to calculate latency 
        """
        self.l_time = time.time()

        await self.send( str(self.l_time).encode(), self.LATENCY)

        self.n_latency_sent += 1   # store how many messages are sent

    async def calculateLatency(self, iterations=10, callback=None):
        """Calculate latency (in ms)

        :param iterations: number of iterations to calculate latency, defaults to 10
        :type iterations: int, optional
        :param callback: callback function, latency (float) is passed, defaults to None
        :type callback: function object, optional
        """

        self.latency_iterations = iterations
        self.__final_latency_callback = callback
        self.log.debug("calculating latency...")

        self.registerReceiveCallback(self.__latencyCallback, self.LATENCY) 

        await self.__sendLatencyMessage()

    def getLatency(self):
        """Get last calculated latency (in ms)

        :return: latency
        :rtype: float
        """
        if self.latency > 0.0:
            return self.latency
        else:
            self.log.error("Latency was never calculated")
    
    ### END LATENCY ###
