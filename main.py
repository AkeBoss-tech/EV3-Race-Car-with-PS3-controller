#!/usr/bin/env python3

import evdev
import ev3dev2.auto as ev3
import threading

def scale(val, src, dst):
    """
    Scale the given value from the scale of src to the scale of dst.

    val: float or int
    src: tuple
    dst: tuple

    example: print(scale(99, (0.0, 99.0), (-1.0, +1.0)))
    """
    return (float(val - src[0]) / (src[1] - src[0])) * (dst[1] - dst[0]) + dst[0]

def scale_stick(value):
    """
    This Function scales the sticks input value which is 0 to -255 to something 100 to -100
    """
    return scale(value,(0,255),(-100,100))

def scaleTurn(value):
    """
    Scales the turn input value and normalizes it.
    """
    newVal = value - 122
    newVal *= 2/3
    if newVal > -5 and newVal < 5:
        newVal = 0

    return normalizeTurn(newVal)

def withinRange(val, buffer, testVal):
    if val - buffer <= testVal <= val + buffer:
        return True
    return False



def normalizeTurn(degrees):
    if degrees >= maxTurn:
        return maxTurn
    elif degrees <= -1 * maxTurn:
        return -1 * maxTurn
    return degrees

print("Finding ps3 controller...")
devices = [evdev.InputDevice(fn) for fn in evdev.list_devices()]
for device in devices:
    if device.name == 'PLAYSTATION(R)3 Controller':
        print("Found the Controller")
        ps3dev = device.fn

# Initialize the controller
try:
    gamepad = evdev.InputDevice(ps3dev)
except:
    print("No Controller Connected")

# Initialize the Variables
speed = 0
turn = 0
steer_lock = False
running = True
precision = False
maxTurn = 55
stop = False

class MotorThread(threading.Thread): # This is the thread that will control the motors
    def __init__(self):
        # Initialize the motors
        try:
            self.motor1 = ev3.LargeMotor(ev3.OUTPUT_B)
            self.motor2 = ev3.LargeMotor(ev3.OUTPUT_C)
            self.steer = ev3.MediumMotor(ev3.OUTPUT_A)
            self.steer.position = 0
            self.steer.stop_action = "hold"
            self.steer.position_sp = 0
        except:
            raise RuntimeError("Motors not connected")
            
        threading.Thread.__init__(self)

    def run(self):
        # Turn the car on
        print("Engine running!")
        while running:
            self.motor1.run_direct(duty_cycle_sp=speed)
            self.motor2.run_direct(duty_cycle_sp=speed)
            
            if steer_lock:
                self.steer.stop()
            else:
                if precision:
                    self.steer.on(-1*turn/8)
                else:
                    self.steer.on(-1*turn/1.5)

            """target = self.steer.position_sp
            print(target)
            print(self.steer.position)
            accuracy = 5
            while True:
                if withinRange(target, accuracy, self.steer.position):
                    break
                elif self.steer.position > target:
                    self.steer.run_direct(duty_cycle_sp=0.2)
                elif self.steer.position < target:
                    self.steer.run_direct(duty_cycle_sp=-0.2)
            print("DONE")"""

        self.motor1.stop()
        self.motor2.stop()

# Start the thread
motor_thread = MotorThread()
motor_thread.setDaemon(True)
motor_thread.start()


for event in gamepad.read_loop():   # Event loop

    if event.type == 3:             # Analog Values
        if event.code == 1:         # Y axis on left stick
            speed = scale_stick(event.value)

    if event.type == 3:             # Analog Values
        if event.code == 3:         # X axis on right stick
            turn = scaleTurn(event.value)

    if event.type == 1 and event.code == 311:       # Digital Value R1
        if event.value == 1:    # Pressed  
            precision = True
        elif event.value == 0:  # Released
            precision = False
        print(precision)

    if event.type == 1 and event.code == 310:       # Digital Value L1
        if event.value == 1:    # Pressed
            steer_lock = True
        elif event.value == 0:  # Released
            steer_lock = False
        print(steer_lock)

    if event.type == 1 and event.code == 304 and event.value == 1:  # Digital value
        print("X button is pressed. Stopping.")
        stop = True
        # running = False
        # break

    if event.type == 1 and event.code == 307 and event.value == 1:  # Digital value
        if stop:
            running = False
            break
