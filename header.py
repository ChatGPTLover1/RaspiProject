import RPi.GPIO as GPIO
import time
def LED_blink_ON(pin):
    while 1:
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(1)
        GPIO.output(pin, GPIO.LOW)
        time.sleep(1)

def LED_blink_OFF(pin):
    GPIO.output(pin, GPIO.LOW)
    GPIO.cleanup()