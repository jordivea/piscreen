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

#Areas
LEFT, CENTER, RIGHT = 'left', 'center', 'right'

#Menu action
DELETE, SLIDESHOW, EXIT = 'delete', 'slideshow', 'exit'

WIDTH = int(config['display']['WIDTH'])
HEIGHT = int(config['display']['HEIGHT'])
EXIFTAG_ORIENTATION = 274

class piScreen():
    #visible menu
    visible_menu = False

    #areas
    click_areas = {}
    areas = {}

    #menu actions
    menu_click_areas = {}
    menu_areas = {}

    #images
    curr_id = 0
    images = []
    last_displayed = None
    last_slideshow = datetime.datetime.now()
    slideshow_interval = int(config['config']['slideshow_interval'])

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
        self.areas = self.get_areas()
        self.click_areas[LEFT] = pygame.Rect(self.areas[LEFT])
        self.click_areas[CENTER] = pygame.Rect(self.areas[CENTER])
        self.click_areas[RIGHT] = pygame.Rect(self.areas[RIGHT])

        #create menu areas (icons)
        self.menu_areas = self.get_menu_areas()
        self.menu_click_areas[DELETE] = pygame.Rect(self.menu_areas[DELETE][0])
        self.menu_click_areas[SLIDESHOW] = \
            pygame.Rect(self.menu_areas[SLIDESHOW][0])
        self.menu_click_areas[EXIT] = pygame.Rect(self.menu_areas[EXIT][0])


    def display_menu(self, force=False, highlight=None):
        """
        Display menu
        """
        #if self.visible_menu or not force:
        #    logger.debug("Menu is already visible")
        #    return

        logger.debug("Displaying menu")
        self.visible_menu = True

        x, y, w, h = self.areas[CENTER]
        menu_surface = pygame.Surface((w,h))
        menu_surface.set_alpha(128)
        menu_surface.fill((255,255,255))
        logger.debug("Adding white layer with transparency on top of current "\
                +"image")

        self.__screen.blit(menu_surface, (x,y))

        for action, menu_area in self.menu_areas.items():
            #if highlight is the given icon, change icon black to green
            if highlight == action:
                icon_path = menu_area[1][:-4]+"H"+menu_area[1][-4:]
            else:
                icon_path = menu_area[1]
            img = pygame.image.load(icon_path)
            self.__screen.blit(img, (menu_area[0][0],menu_area[0][1]))

        # update the display
        pygame.display.flip()

    def get_clicked_area(self):
        clicked_area = None
        menu_clicked_area = None

        pos = pygame.mouse.get_pos()
        logger.debug("mouse pos: {}".format(pos))
        for k, area in self.click_areas.items():
            if area.collidepoint(pos):
                clicked_area = k
                break

        if clicked_area == CENTER and self.visible_menu:
            for k, menu_area in self.menu_click_areas.items():
                if menu_area.collidepoint(pos):
                    menu_clicked_area = k
                    break

        return clicked_area, menu_clicked_area

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

    def onClick_center(self, action):
        '''
        Display center
        '''
        if self.visible_menu:
            #check clicked image
            logger.info("Menu action clicked: {}".format(action))
            if action == DELETE:
                self.menu_action_delete()
            elif action == SLIDESHOW:
                self.menu_action_slideshow()
            elif action == EXIT:
                self.menu_action_exit()
        else:
            self.display_menu()

    def menu_action_delete(self):
        """
        Deletes current image from directory
        """
        if len(self.images):
            logger.info("Deleting image file {}"\
                    .format(self.images[self.curr_id]))
            os.remove(self.images[self.curr_id])

            self.images.pop(self.curr_id)
            if self.curr_id >= len(self.images):
                self.curr_id = len(self.images)-1
        self.menu_hide(DELETE)

    def menu_action_slideshow(self):
        slideshow_interval_cfg = int(self.__settings['slideshow_interval'])

        if self.slideshow_interval != slideshow_interval_cfg:
            #slideshow value has been changed from the configured one
            self.slideshow_interval = slideshow_interval_cfg
        else:
            if not slideshow_interval_cfg:
                #slideshow interval disabled by config. Setting 30s slideshow
                self.slideshow_interval = 30
            else:
                self.slideshow_interval = 0

        logger.info("Slideshow interval set to: {}s"\
                .format(self.slideshow_interval))
        self.menu_hide(SLIDESHOW)

    def menu_action_exit(self):
        '''
        Perform menu action exit.
        Sets menu visible to false and displays again current image
        '''
        logger.info("Exiting menu")
        self.menu_hide(EXIT)

    def menu_hide(self, action):
        self.display_menu(highlight=action)
        time.sleep(2)
        self.visible_menu = False
        self.display_image()

    def get_image_rotation(self, img):
        rotation = 0
        if hasattr(img, '_getexif'):
            exifdata = img._getexif()
            if exifdata:
                #orientation ==1: landscape
                #orientation ==3: landscape upside down
                if exifdata[EXIFTAG_ORIENTATION] in (1, 3):
                    if int(self.__settings['orientation']) != \
                            exifdata[EXIFTAG_ORIENTATION]:
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
        else:
            # remove previous image from the screen
            self.__surface.fill((0, 0, 0))
            self.__screen.blit(self.__surface, (0, 0))
            pygame.display.flip()

        self.last_displayed = datetime.datetime.now()
        self.last_slideshow = datetime.datetime.now()

        if self.visible_menu:
            self.display_menu(True)

    def get_areas(self):
        """
        Get area tuples, (x, y, width, heigth)
        """
        w_lat = ceil(WIDTH/3)
        w_ctr = WIDTH - (2 * w_lat)

        if int(self.__settings['orientation']) == 1:
            logger.debug("Orientation: landscape (1)")
            areas = {LEFT: (0,0,w_lat,HEIGHT),
                     CENTER: (w_lat,0,w_ctr,HEIGHT),
                     RIGHT: (w_lat+w_ctr,0,w_lat,HEIGHT)}
        else: #orientation == 3, landscape, upside down
            logger.debug("Orientation: landscape upside down (3)")
            areas = {RIGHT: (0,0,w_lat,HEIGHT),
                     CENTER: (w_lat,0,w_ctr,HEIGHT),
                     LEFT: (w_lat+w_ctr,0,w_lat,HEIGHT)}
        return areas

    def get_menu_areas(self):
        x, _, w, _ = self.areas[CENTER]
        menu_areas = { DELETE: [], SLIDESHOW: [], EXIT: []}

        path = os.path.dirname(os.path.abspath(__file__)) + \
                '/../media/resources'

        if int(self.__settings['orientation']) == 1:
            orientation = 1
        else:
            orientation = 3

        img_rmve = "{}/menu_remove{}.png".format(path,orientation)    #80x96
        img_show = "{}/menu_slideshow{}.png".format(path,orientation) #80x80
        img_exit = "{}/menu_exit{}.png".format(path,orientation)      #80x80

        if int(self.__settings['orientation']) == 1:
            #remove image
            icon_x = x+(w/2)-40
            icon_y = 10
            menu_areas[DELETE] = [(icon_x, icon_y, 160, 96), img_rmve]

            #start slideshow
            icon_y = (HEIGHT/2)-32
            menu_areas[SLIDESHOW] = [(icon_x, icon_y, 160, 80), img_show]

            #leave menu
            icon_y = HEIGHT-90
            menu_areas[EXIT] = [(icon_x, icon_y, 160, 80), img_exit]
        else: #orientation == 3, landscape upside down
            #remove image
            icon_x = x+(w/2)-40
            icon_y = HEIGHT-106
            menu_areas[DELETE] = [(icon_x, icon_y, 160, 96), img_rmve]

            #start slideshow
            icon_y = (HEIGHT/2)-48
            menu_areas[SLIDESHOW] = [(icon_x, icon_y, 160, 80), img_show]

            #leave menu
            icon_y = 10
            menu_areas[EXIT] = [(icon_x, icon_y, 160, 80), img_exit]

        return menu_areas

    def run(self):
        not_quit = True
        refresh_interval = int(self.__settings['refresh_interval'])
        #slideshow_interval = int(self.__settings['slideshow_interval'])
        while not_quit:
            for event in pygame.event.get():

                if event.type == pygame.MOUSEBUTTONDOWN:
                    # FIXME: display during 2s the areas (left, right arrows
                    #        and dash lines separating areas)
                    #self.display_areas()

                    clicked_area, menu_clicked_area = self.get_clicked_area()
                    logger.info("MOUSEBUTTONDOWN detected on {} area"
                                 .format(clicked_area))
                    if clicked_area == LEFT:
                        self.onClick_left()
                    elif clicked_area == RIGHT:
                        self.onClick_right()
                    else:
                        self.onClick_center(menu_clicked_area)

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

            if self.slideshow_interval != 0 and len(self.images):
                if int((datetime.datetime.now() -
                    self.last_slideshow).total_seconds()) > \
                            self.slideshow_interval:
                    logger.debug("Slideshow: Display next image")
                    self.display_next_image()


if __name__ == '__main__':
    piscreen = piScreen()
    piscreen.run()
