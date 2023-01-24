import gc
import cv2
import time
import json
import numpy
import requests
import threading
import pyautogui
import smtplib, ssl

from pynput import keyboard
from AppKit import NSWorkspace
from PIL import Image, ImageGrab
from email.mime.text import MIMEText
from Quartz import CGWindowListCopyWindowInfo, kCGNullWindowID, kCGWindowListOptionAll

# receiver
target_email = ""

# sender information
email = ""
password = ""
server = ""
port = 465

# send email
def sendEmail(message):
    msg = MIMEText(message)
    msg['Subject'] = "RokBot by M47Z"
    msg['From'] = email
    msg['To'] = target_email

    email_ctx = ssl.create_default_context()
    email_ctx.check_hostname = False
    email_ctx.set_ciphers('DEFAULT:!DH')
    email_ctx.verify_mode = ssl.CERT_NONE
    with smtplib.SMTP_SSL(server, port, context=email_ctx) as smtp:
        smtp.login(email, password)
        smtp.sendmail(email, target_email, msg.as_string())

# send message over discord webhook
def sendMessage(message, tag=False):
    # discord webhook url and user id to ping
    url = ""
    user_id = ""
    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        'content': "<@{}> -> {}".format( user_id, message ) if tag else "{}".format( message )
    }
    response = requests.post("{}?wait=true".format(url), headers=headers, data=json.dumps(data))
    return response.json().get('id')

# get message information
def getMessage(message_id):
    # discord webhook url
    url = ""
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.get("{}/messages/{}".format(url, message_id), headers=headers)
    return response.json()

# delete message
def deleteMessage(message_id):
    # discord webhook url
    url = ""
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.delete("{}/messages/{}".format(url, message_id), headers=headers)
    return response.status_code

# find image on another image
def subimg(haystack, needle, repeated=False):
    haystack_gray = cv2.cvtColor(haystack, cv2.COLOR_BGR2GRAY)
    needle_gray = cv2.cvtColor(needle, cv2.COLOR_BGR2GRAY)
        
    w, h = needle_gray.shape[::-1]

    res = cv2.matchTemplate(haystack_gray, needle_gray, cv2.TM_CCOEFF_NORMED)
    threshold = 0.88
    loc = numpy.where(res >= threshold)
    try:
        assert loc[0][0] > 0
        assert loc[1][0] > 0
        return (loc[1][0], loc[0][0])
    except:
        if repeated:
            return (-1, -1)
        else:
            return subimg(haystack, needle, True)

wnd_width = 1163
wnd_height = 900

# get capture from window
def getWndImg( window_name ):
    workspace = NSWorkspace.sharedWorkspace()
    active_app = workspace.activeApplication()['NSApplicationName']
    if active_app != "RiseOfKingdoms":
        time.sleep(0.25)
        return getWndImg( window_name )

    debug_screenshot = False
    window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionAll, kCGNullWindowID)
    for window in window_list:
        try:
            if window_name.lower() in str(window['kCGWindowName'].lower( )):
                x = int(window['kCGWindowBounds']['X'])
                y = int(window['kCGWindowBounds']['Y'])
                x2 = x + int(window['kCGWindowBounds']['Width'])
                y2 = y + int(window['kCGWindowBounds']['Height'])
                try:
                    img = ImageGrab.grab(bbox = (x, y, x2, y2))

                    if debug_screenshot:
                        img.save("screenshot.png")
                        exit()

                    img = numpy.array(img, dtype=numpy.uint8)
                    return img
                except:
                    time.sleep(0.25)
                    return getWndImg( window_name )
        except KeyError:
            pass
    else:
        raise Exception('Window %s not found.' % window_name)

# click on window
def clickWnd( window_name, target_x, target_y ):
    workspace = NSWorkspace.sharedWorkspace()
    active_app = workspace.activeApplication()['NSApplicationName']
    if active_app != "RiseOfKingdoms":
        time.sleep(0.25)
        return clickWnd( window_name, target_x, target_y )

    window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionAll, kCGNullWindowID)
    for window in window_list:
        try:
            if window_name.lower() in str(window['kCGWindowName'].lower( )):
                x = window['kCGWindowBounds']['X'] + target_x
                y = window['kCGWindowBounds']['Y'] + target_y
                pyautogui.click( x, y )
                time.sleep(0.5)
                return
        except KeyError:
            pass
    else:
        raise Exception('Window %s not found.' % window_name)

# exist image on another image
def existOnImage( image, image_path ):
    img = Image.open(image_path)
    img = numpy.array(img, dtype=numpy.uint8)

    img_x, img_y = subimg(image, img)
    if img_x < 0 or img_y < 0:
        return False

    return True

# get coords of image on another image
def getOnImage( image, image_path ):
    img = Image.open(image_path)
    img = numpy.array(img, dtype=numpy.uint8)

    return subimg(image, img)

# click on image on image
def clickOnImage( image, image_path, x = 0, y = 0 ):
    img = Image.open(image_path)
    img = numpy.array(img, dtype=numpy.uint8)

    (img_x, img_y) = subimg(image, img)
    if img_x < 0 or img_y < 0:
        return False

    if "help" in image_path and img_x < wnd_width / 2:
        return False

    clickWnd("RiseOfKingdoms", img_x + x, img_y + y)
    return True

# click on image on screen
def clickOnImageOnScreen( image_path, x = 0, y = 0 ):
    img = Image.open(image_path)
    img = numpy.array(img, dtype=numpy.uint8)

    screen = getWndImg("RiseOfKingdoms")
    (img_x, img_y) = subimg(screen, img)
    if img_x < 0 or img_y < 0:
        if "siege" in image_path:
            print("{} not found".format(image_path))
        return False
    
    clickWnd("RiseOfKingdoms", img_x + x, img_y + y)
    return True

# go to city hall
def goToCityHall():
    if not clickOnImageOnScreen("cityhall.png"):
        return
    
    time.sleep(2)

# help alliance
def helpAlliance(screen = None):
    if screen is None:
        screen = getWndImg("RiseOfKingdoms")
    
    if not clickOnImage(screen, "help.png", 10, 10):
        clickOnImage(screen, "help2.png")

# press on my scout camp
def pressMyScoutCamp():
    return clickOnImageOnScreen("scoutcamp.png", 10, 25) and clickOnImageOnScreen("scoutcamp_confirm.png")

# send available scouts
scouts_inf = 0
def sendAvailableScouts():
    global scouts_inf
    goToCityHall()

    scout_img = getWndImg("RiseOfKingdoms")

    # check if there is available scout (might not work if there is only one scout working)
    if not existOnImage( scout_img, "scoutcamp.png" ):
        return False

    print( "Sending available scouts..." )

    if not pressMyScoutCamp():
        return False

    i = 1
    while True:
        scout_img = getWndImg("RiseOfKingdoms")

        # check if scout is not available
        if not existOnImage( scout_img, "explore.png" ):
            print( "Scout not on screen" )
            clickWnd("RiseOfKingdoms", wnd_width * 0.85, 0.25 * wnd_height)
            clickWnd("RiseOfKingdoms", wnd_width * 0.05, 0.95 * wnd_height)
            break

        print("Sending Scout %d" % i)

        # press scout button
        clickOnImage( scout_img, "explore.png" )
        time.sleep(1.25)

        # find confirm button
        if not clickOnImageOnScreen("explore.png"):
            print ( "Confirm button not found" )

            goToCityHall()
            pressMyScoutCamp()
            continue

        # press send button
        if not clickOnImageOnScreen("send.png"):
            print ( "Send button not found" )

            goToCityHall()
            pressMyScoutCamp()
            continue

        goToCityHall()

        helpAlliance()

        if not pressMyScoutCamp():
            break

        i += 1

    if scouts_inf < 10:
        scouts_inf += i
    else:
        sendMessage("We have sent %d scouts" % scouts_inf)
        scouts_inf = 0

    return True

# check for game reconnection
def checkForGameReconnection(img):
    if not existOnImage(img, "confirm.png"):
        helpAlliance(img)
        return

    print( "Reconnecting..." )
    sendMessage("Game disconnected, attempting to reconnect")
    
    clickOnImage(img, "confirm.png")
    time.sleep(5)

    return checkForGameReconnection(getWndImg("RiseOfKingdoms"))

# pass captcha verification
running = True
remote_pause = False
def passCaptcha(img):
    global running, remote_pause
    print("A captcha has been detected!")
    sendMessage("A captcha has been detected!", True)
    sendEmail("A captcha has been detected. Please check the computer to continue.")

    print( "Pausing Script" )
    running = False
    remote_pause = True

    return

# press on my troop camp
def pressMyTroopCamp(img, camp_name):
    coords_x, coords_y = getOnImage(img, "{}.png".format(camp_name))
    if coords_x < 0 or coords_y < 0:
        return False

    clickWnd("RiseOfKingdoms", coords_x + 10, coords_y + 25)
    clickWnd("RiseOfKingdoms", coords_x + 10, coords_y + 25)
    
    confirm = clickOnImageOnScreen("{}_confirm.png".format(camp_name))
    if not confirm:
        return False
    
    time.sleep(0.25)
    return True

# train troops
def trainTroops():
    goToCityHall()

    troops_img = getWndImg("RiseOfKingdoms")

    if pressMyTroopCamp(troops_img, "archery"):
        if not clickOnImageOnScreen("train.png", 10, 5):
            print("Failed to train archery")
            sendMessage("Failed to train archery")
            clickWnd("RiseOfKingdoms", wnd_width * 0.85, 0.25 * wnd_height)
        else:
            print("We have trained archery")

        troops_img = getWndImg("RiseOfKingdoms")

    if pressMyTroopCamp(troops_img, "cavalry"):
        if not clickOnImageOnScreen("train.png", 10, 5):
            print("Failed to train cavalry")
            sendMessage("Failed to train cavalry")
            clickWnd("RiseOfKingdoms", wnd_width * 0.85, 0.25 * wnd_height)
        else:
            print("We have trained cavalry")
        
        troops_img = getWndImg("RiseOfKingdoms")

    if pressMyTroopCamp(troops_img, "infantry"):
        if not clickOnImageOnScreen("train.png", 10, 5):
            print("Failed to train infantry")
            sendMessage("Failed to train infantry")
            clickWnd("RiseOfKingdoms", wnd_width * 0.85, 0.25 * wnd_height)
        else:
            print("We have trained infantry")
        
        troops_img = getWndImg("RiseOfKingdoms")

    if pressMyTroopCamp(troops_img, "siege"):
        if not clickOnImageOnScreen("train.png", 10, 5):
            print("Failed to train siege")
            sendMessage("Failed to train siege")
            clickWnd("RiseOfKingdoms", wnd_width * 0.85, 0.25 * wnd_height)
        else:
            print("We have trained siege")
        
        troops_img = getWndImg("RiseOfKingdoms")

    return

# detect escape
def onPress(key):
    global running, remote_pause
    if key == keyboard.Key.esc:
        workspace = NSWorkspace.sharedWorkspace()
        active_app = workspace.activeApplication()['NSApplicationName']
        if active_app == "RiseOfKingdoms":
            print( "Pausing Script" if running else "Script Resumed" )
            running = not running
            remote_pause = False

# pause system
def pauseSystem():
    global running, remote_pause
    listener = keyboard.Listener(on_press=onPress)
    listener.start()

    og_message = sendMessage( "Bot Started!" )

    del_msg_id = 0

    paused = False
    while True:
        pause = getMessage( og_message ).get( 'reactions' ) != None

        if pause:
            if not running and not paused and remote_pause:
                running = True
                remote_pause = True
                paused = False
                
                if del_msg_id:
                    deleteMessage( del_msg_id )
                    del_msg_id = 0

                del_msg_id = sendMessage( "Script Resumed" )
                print( "Script Resumed" )
            elif running and not paused:
                running = False
                remote_pause = True
                paused = True
                
                if del_msg_id:
                    deleteMessage( del_msg_id )
                    del_msg_id = 0

                del_msg_id = sendMessage( "Script Paused" )
                print( "Pausing Script" )
        elif not running and paused:
            running = True
            remote_pause = True
            paused = False
            
            if del_msg_id:
                deleteMessage( del_msg_id )
                del_msg_id = 0

            del_msg_id = sendMessage( "Script Resumed" )
            print( "Script Resumed" )

        time.sleep(2.5)

# main loop
print ("Starting...")

threading.Thread(target=pauseSystem).start()

time.sleep(1)

i = 0
first_loop_pause = True
while True:
    if running:
        if not first_loop_pause:
            first_loop_pause = True

        img = getWndImg("RiseOfKingdoms")

        if existOnImage(img, "captcha.png"):
            passCaptcha(img)
        
        if not running:
            continue

        checkForGameReconnection(img)

        if not running:
            continue

        sendAvailableScouts()

        if not running:
            continue

        # trainTroops()
    else:
        if first_loop_pause:
            print( "Script Paused" )
            first_loop_pause = False
    
    if remote_pause:
        # avoid afk
        if i == 120:
            i = 0
            pyautogui.move(10, 0)
        elif i == 60:
            pyautogui.move(-10, 0)
        else:
            i += 1

    time.sleep(0.25)
    gc.collect()