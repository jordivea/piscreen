'''
#TODO: Add documentation
Purpose
version
license

'''
import pygame
import time
import glob
from PIL import Image
from math import ceil
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
WIDTH = int(config['display']['WIDTH'])
HEIGHT = int(config['display']['HEIGHT'])
EXIFTAG_ORIENTATION = 274

class piScreen():
    curr_id = 0
    click_areas = {}
    images = []
    last_displayed = None
    last_slideshow = datetime.datetime.now()

    def __init__(self):
        pygame.init()

        self.__settings = config['config']
        logger.debug("Setting display size: {}x{}".format(WIDTH, HEIGHT))
        self.__size = (WIDTH, HEIGHT)
        # When it is run on the piscreen device, display as fullscreen and
        # hide the cursor
        if os.uname()[1].lower() == 'piscreen':
            logger.info("Loading display configuration for piscreen device")
            self.__screen = pygame.display.set_mode(self.__size,
                                                    pygame.FULLSCREEN)
            pygame.mouse.set_visible(False)
        else:
            logger.info("Loading display configuration for not a piscreen "+\
                        "device")
            self.__screen = pygame.display.set_mode(self.__size)

        self.__surface = pygame.Surface(self.__size)
        self.__create_piscreen_click_areas()

        self.load_images()
        self.display_image()

    def find_images(self):
        imgs = []
        for ext in ('jpg', 'JPG'):
            imgs.extend(glob.glob(self.__settings['images_path']+'/*.'+ext))
            imgs.sort(key=os.path.getmtime)
        return imgs

    def load_images(self):
        '''Load all images in the local path, and create array'''
        reload_image = False

        logger.debug("Current loaded images: {}".format(len(self.images)))
        if len(self.images):
            imgs = self.find_images()
            logger.debug("Looking for new images")
            for i in imgs:
                if i not in self.images:
                    self.images.append(i)
                    logger.info("New image found: {}".format(i))
                    reload_image = True
        else:
            logger.debug("Loading initial images")
            self.images = self.find_images()
            reload_image = True

        logger.debug("Loaded {} images: {}".format(len(self.images),
                                                   self.images))

        if reload_image:
            if len(self.images):
                self.curr_id = len(self.images) -1
            self.display_image()
        else:
            self.last_displayed = datetime.datetime.now()

    def display_prev_image(self):
        logger.debug("Current id: {}".format(self.curr_id))
        if self.curr_id > 0:
            self.curr_id = self.curr_id -1
        elif self.curr_id == 0:
            self.curr_id = len(self.images) -1
        logger.debug("New current id: {}".format(self.curr_id))
        self.display_image()

    def display_next_image(self):
        logger.debug("Current id: {}".format(self.curr_id))
        if self.curr_id < len( self.images ) -1:
            self.curr_id = self.curr_id +1
        elif self.curr_id == len(self.images) -1:
            # last image, start the list from the begining
            self.curr_id = 0
        logger.debug("New current id: {}".format(self.curr_id))
        self.display_image()

    def __create_piscreen_click_areas(self):
        self.click_areas = {}
        # display size (WIDTH, HEIGHT)
        width_sides = 2 * ceil(WIDTH/5)
        width_center = WIDTH - (2 * width_sides)
        logger.debug("Click areas: LEFT:0,{0}; CENTER:{0},{1}; RIGHT:{1},{2}"
                     .format(width_sides, width_sides+width_center,
                             width_sides+width_center+width_sides))
        self.click_areas[LEFT] = pygame.Rect(0, 0, width_sides, HEIGHT)
        self.click_areas[CENTER] = pygame.Rect(width_sides, 0, width_center,
                                               HEIGHT)
        self.click_areas[RIGHT] = pygame.Rect(width_sides + width_center, 0,
                                              width_sides, HEIGHT)

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
        self.display_prev_image()

    def onClick_right(self):
        '''
        Load next image
        '''
        self.display_next_image()

    def onClick_center(self):
        '''
        Display center
        '''
        # TODO display menu
        pass

    def get_image_rotation(self, img):
        rotation = 0
        if hasattr(img, '_getexif'):
            exifdata = img._getexif()
            if exifdata:
                #default orientation ==3, raspberry pi is upside down, landscape
                if exifdata[EXIFTAG_ORIENTATION] == 1:
                    rotation = 180
                elif exifdata[EXIFTAG_ORIENTATION] == 6:
                    rotation = 90
                elif exifdata[EXIFTAG_ORIENTATION] == 8:
                    rotation = 270
        return rotation

    def display_image(self):
        if len(self.images):
            logger.debug("Display image {}:{}".format(self.curr_id,
                self.images[self.curr_id]))

            img_path = self.images[self.curr_id]
            img = Image.open(img_path)
            img_save = False

            rotation = self.get_image_rotation(img)
            if rotation:
                img = img.rotate(rotation, expand=True)
                img_save = True

            if img.size[1] > HEIGHT:
               # scale image
                hpercent = (HEIGHT / float(img.size[1]))
                wsize = int((float(img.size[0]) * float(hpercent)))
                img = img.resize((wsize, HEIGHT), Image.ANTIALIAS)
                img_save = True
                logger.debug("Image resized: {}".format(img_path))
            else:
                wsize = img.size[0]

            if img_save: img.save(img_path)

            w_offset = 0
            if wsize < WIDTH:
                w_offset = int((WIDTH - wsize) / 2)

            img = pygame.image.load(img_path)

            # remove previous image from the screen
            self.__surface.fill((0, 0, 0))
            self.__screen.blit(self.__surface, (0, 0))
            pygame.display.flip()

            self.__screen.blit(img, (w_offset, 0))
            # update the display
            pygame.display.flip()

        self.last_displayed = datetime.datetime.now()
        self.last_slideshow = datetime.datetime.now()

    def display_areas(self):
        #FIXME currently not working. Lines are not erased
        width_sides = 2 * ceil(WIDTH/5)
        width_center = WIDTH - (2 * width_sides)

        color = ( 255, 0, 0 )
        pygame.draw.line(self.__screen, color, (width_sides, 0),
                         (width_sides, HEIGHT))
        pygame.draw.line(self.__screen, color, (width_sides+width_center, 0),
                         (width_sides+width_center, HEIGHT))
        pygame.display.update()

        pygame.display.flip()
        time.sleep(5)
        self.display_image()

    def run(self):
        not_quit = True
        refresh_interval = int(self.__settings['refresh_interval'])
        slideshow_interval = int(self.__settings['slideshow_interval'])
        while not_quit:
            for event in pygame.event.get():

                if event.type == pygame.MOUSEBUTTONDOWN:
                    # FIXME: display during 2s the areas (left, right arrows
                    #        and dash lines separating areas)
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
                if int((datetime.datetime.now() -
                    self.last_displayed).total_seconds()) > refresh_interval:
                    self.load_images()

            if slideshow_interval != 0 and len(self.images):
                if int((datetime.datetime.now() -
                    self.last_slideshow).total_seconds()) > slideshow_interval:
                    logger.debug("Slideshow: Display next image")
                    self.display_next_image()


if __name__ == '__main__':
    piscreen = piScreen()
    piscreen.run()
