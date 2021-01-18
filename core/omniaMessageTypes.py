class OmniaMessageTypes:
    
    ### Images ###
    ONE_BIT_IMAGE = 'S'
    RGBA_IMAGE = 'd'
    ### --- ###

    ### Displays ###
    ONE_BIT_DISPLAY = 'D'
    TOUCHSCREEN = 't'
    ### --- ###

    ### Video ###
    START_STOP_VIDEO_STREAM = 'V'
    VIDEO_FRAME = 'v'
    ### --- ###

    ### Audio ###
    SET_AUDIO = 'A'
    AUDIO_CHUNK = 'a'
    ### --- ###

    ### IO pins ###
    INPUT_PIN = 'I'
    REMOVE_INPUT_PIN = 'R'
    OUTPUT_PIN = 'O'
    PWM_PIN = 'P'
    NEOPIXEL_PIN = 'N'

    READ_ADC = 'e'
    SET_I2C = 'i'
    READ_I2C = 'c'
    ### --- ###

    ### Connectivity ###
    READ_BLE = 'b'
    SET_NFC = 'n'
    READ_NFC = 'f'
    ### --- ###

    ### Latency ###
    LATENCY = 'l'
    ### --- ###