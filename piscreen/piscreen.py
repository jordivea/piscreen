'''
#TODO: Add documentation
Purpose
version
license

'''
import pygame
import time
import glob
#import shutil
from PIL import Image
import configparser
import os
import logging
import datetime

configfile = os.path.splitext(os.path.realpath(__file__))[0] + '.cfg'
config = configparser.ConfigParser()
config.read(configfile)

logging.basicConfig(filename=config['log']['logfile'],
                    format='%(asctime)s %(module)s %(levelname)-8s %(message)s',
                    level=eval('logging.' + config['log']['level']),
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

LEFT, CENTER, RIGHT = 'left', 'center', 'right'


class piScreen():
    curr_id = 0
    click_areas = {}
    images = []
    last_displayed = None

    def __init__(self):
        pygame.init()

        self.__size = (480, 320)
        if lower(os.uname()[1]) == 'piscreen':
            logger.info("Loading display configuration for piscreen device")
            self.__screen = pygame.display.set_mode(self.__size, pygame.FULLSCREEN)
            pygame.mouse.set_visible(False)
        else:
            logger.info("Loading display configuration for debugging purposes")
            self.__screen = pygame.display.set_mode(self.__size)

        self.__surface = pygame.Surface(self.__size)
        self.__create_piscreen_click_areas()
        self.__settings = config['config']
        self.load_images()
        self.display_image()


    def load_images(self):
        '''Load all images in the local path, and create array'''
        reload_image = False

        logger.debug("Current loaded images: {}".format(len(self.images)))
        if len(self.images) > 0:
            imgs = glob.glob(self.__settings['images_path']+'/*.jpg')
            logger.debug("Reloading {} images: {}".format(len(imgs), imgs))
            for i in imgs:
                if i not in self.images:
                    self.images.append(i)
                    logger.info("New image found: {}".format(i))
                    reload_image = True
        else:
            logger.debug("Loading initial images")
            self.images = glob.glob(self.__settings['images_path']+'/*.jpg')
            self.images.sort(key=os.path.getmtime)
            reload_image = True

        logger.debug("Loaded {} images: {}".format(len(self.images), self.images))

        if len(self.images) > 0:
            self.curr_id = len(self.images) - 1

        if reload_image:
            self.display_image()
        else:
            self.last_displayed = datetime.datetime.now()


    def display_prev_image(self):
        logger.debug("Current id: {}".format(self.curr_id))
        if self.curr_id > 0:
            self.curr_id = self.curr_id - 1
        self.display_image()
        logger.debug("Current id: {}".format(self.curr_id))

    def display_next_image(self):
        logger.debug("Current id: {}".format(self.curr_id))
        if self.curr_id < len( self.images ) -1:
            self.curr_id = self.curr_id +1
        self.display_image()
        logger.debug("Current id: {}".format(self.curr_id))

    def __create_piscreen_click_areas(self):
        self.click_areas = {}
        # display size (480, 320)
        self.click_areas[LEFT] = pygame.Rect(0, 0, 200, 320)
        self.click_areas[CENTER] = pygame.Rect(200, 0, 80, 320)
        self.click_areas[RIGHT] = pygame.Rect(280, 0, 200, 320)


    def get_clicked_area(self):
        result = None
        pos = pygame.mouse.get_pos()
        logger.debug("mouse pos: {}".format(pos))
        for k, area in self.click_areas.items():
            if area.collidepoint(pos):
                result = k
                break
        return result

    def onClick_left(self):
        '''
        Load previous image
        '''
        # TODO display left arrow for 2s
        self.display_prev_image()

    def onClick_right(self):
        '''
        Load next image
        '''
        # TODO display right arrow for 2s
        self.display_next_image()

    def onClick_center(self):
        '''
        Display center
        '''
        # TODO display right arrow for 2s
        pass

    def display_image(self):
        if len(self.images):
            # scale image
            baseheight = 320
            img_path = self.images[self.curr_id]

            img = Image.open(img_path)
            hpercent = (baseheight / float(img.size[1]))
            wsize = int((float(img.size[0]) * float(hpercent)))
            img = img.resize((wsize, baseheight), Image.ANTIALIAS)
            img.save(img_path)

            w_offset = 0
            if wsize < 480:
                w_offset = int((480 - wsize) / 2)
            img = pygame.image.load(img_path)

            # remove previous image from the screen
            self.__surface.fill((0, 0, 0))
            self.__screen.blit(self.__surface, (0, 0))
            pygame.display.flip()

            self.__screen.blit(img, (w_offset, 0))
            pygame.display.flip()  # update the display

        self.last_displayed = datetime.datetime.now()


    def display_areas(self):
        color = ( 255, 0, 0 )
        pygame.draw.line(self.__screen, color, (200, 0), (200, 320))
        pygame.draw.line(self.__screen, color, (280, 0), (280, 320))
        pygame.display.update()

        pygame.display.flip()
        time.sleep(5)
        self.display_image()

    def run(self):
        not_quit = True
        refresh_interval = int(self.__settings['refresh_interval'])
        while not_quit:
            for event in pygame.event.get():

                if event.type == pygame.MOUSEBUTTONDOWN:
                    # display during 2s the areas (left, right arrows and dash lines separating areas)
                    #self.display_areas()

                    clicked_area = self.get_clicked_area()
                    logger.info("MOUSEBUTTONDOWN detected on {} area"
                                 .format(clicked_area))
                    if clicked_area == LEFT:
                        self.onClick_left()
                    elif clicked_area == RIGHT:
                        self.onClick_right()
                    else:
                        self.onClick_center()

                elif event.type == pygame.QUIT:
                    logger.info("Quitting")
                    not_quit = False
                elif event.type == pygame.KEYDOWN and \
                        event.key == pygame.K_ESCAPE:
                    logger.info("ESC key pressed. Quitting")
                    not_quit = False

            if refresh_interval != 0:
                if int((datetime.datetime.now() - self.last_displayed).total_seconds()) > \
                        refresh_interval:
                    self.load_images()

# landscape, portrait
#ORIENTATION_PREFERRED = 'landscape'
#
#
#ORIENTATION_180 = 3
#ORIENTATION_270 = 6
#ORIENTATION_090 = 8
#
# def get_random_image()
#    pass
#
# def get_rotation_angle(filename)
#    #Check if file exists
#    img = Image.open(filename)
#    img_exif = dict(img._getexif().items())
#    img_orientation =  img_exif['orientation']
#
#    if ORIENTATION_PREFERRED = 'landscape':
#        if img_orientation == ORIENTATION_180:
#            angle = 180
#        elif img_orientation == ORIENTATION_270 or \
#             img_orientation == ORIENTATION_090:
#            angle = -1
#
#    return angle


if __name__ == '__main__':
    piscreen = piScreen()
    piscreen.run()
