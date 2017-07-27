import pygame
import time
import glob
import random
import shutil
from PIL import Image
import configparser
import os
import logging
import datetime
from common import dbconnector

configfile = os.path.splitext(os.path.realpath(__file__))[0] + '.cfg'
config = configparser.ConfigParser()
config.read(configfile)

logging.basicConfig(filename=config['log']['logfile'],
                    level=eval('logging.' + config['log']['level']))
logger = logging.getLogger(__name__)

LEFT = 'left'
RIGHT = 'right'


class piScreen():
    curr_id = 0
    click_areas = {}
    last_displayed = None

    def __init__(self):
        pygame.init()
        pygame.mouse.set_visible(False)
        self.__size = (480, 320)
        self.__screen = pygame.display.set_mode(self.__size, pygame.FULLSCREEN)
        self.__surface = pygame.Surface(self.__size)
        self.__create_piscreen_click_areas()
        self.__settings = config['config']
        self.dbconn = dbconnector.dbConnector(configfile)
        self.load_new_image()
        self.display_image()
        logger.debug("configfile: " + configfile)

    def copy_file(self, filename, image_id):
        shutil.copyfile(filename, self.__settings['local_image_path'])
        self.curr_id = image_id

    def load_new_image(self):
        files = glob.glob(self.__settings['remote_image_pattern'])
        filename = random.choice(files)

        cmd = 'INSERT INTO piscreen_images(filename) VALUES("%s")' % filename

        self.dbconn.open()
        row_id = self.dbconn.insert_row(cmd)

        if row_id is not None:
            self.copy_file(filename, row_id)

        cmd = 'DELETE FROM piscreen_images WHERE ID < ('\
              'SELECT MIN(foo.mid) FROM ( '\
              'SELECT id as mid FROM piscreen_images ORDER BY id DESC LIMIT {} '\
              ') as foo);'.format(self.__settings['image_history_max'])
        self.dbconn.execute_stmt(cmd)

        self.dbconn.close()

    def load_prev_image(self):
        cmd = 'SELECT id, filename FROM piscreen_images WHERE id < %d '\
            'ORDER BY id DESC LIMIT 1' % self.curr_id

        self.dbconn.open()
        row = self.dbconn.get_row(cmd)
        self.dbconn.close()
        if row is not None:
            self.copy_file(row[1], row[0])

    def load_next_image(self):
        cmd = 'SELECT id, filename FROM piscreen_images WHERE id > %d '\
            'ORDER BY id ASC LIMIT 1' % self.curr_id

        self.dbconn.open()
        row = self.dbconn.get_row(cmd)
        self.dbconn.close()
        if row is not None:
            self.copy_file(row[1], row[0])
        else:
            self.load_new_image()

    def __create_piscreen_click_areas(self):
        self.click_areas = {}
        # display size (480, 320)
        self.click_areas[LEFT] = pygame.Rect(0, 0, 240, 320)
        self.click_areas[RIGHT] = pygame.Rect(240, 0, 240, 320)

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
        # TODO display left arrow
        self.load_prev_image()
        self.display_image()

    def onClick_right(self):
        '''
        Load next image
        '''
        # TODO display right arrow
        self.load_next_image()
        self.display_image()

    def display_image(self):
        # scale image
        baseheight = 320
        img = Image.open(self.__settings['local_image_path'])
        hpercent = (baseheight / float(img.size[1]))
        wsize = int((float(img.size[0]) * float(hpercent)))
        img = img.resize((wsize, baseheight), Image.ANTIALIAS)
        img.save(self.__settings['local_image_path'])

        w_offset = 0
        if wsize < 480:
            w_offset = int((480 - wsize) / 2)
        img = pygame.image.load(self.__settings['local_image_path'])

        # remove previous image from the screen
        self.__surface.fill((0, 0, 0))
        self.__screen.blit(self.__surface, (0, 0))
        pygame.display.flip()

        self.__screen.blit(img, (w_offset, 0))
        pygame.display.flip()  # update the display

        self.last_displayed = datetime.datetime.now()

    def run(self):
        not_quit = True
        refresh_interval = int(self.__settings['refresh_interval'])
        while not_quit:
            for event in pygame.event.get():

                if event.type == pygame.MOUSEBUTTONDOWN:
                    clicked_area = self.get_clicked_area()
                    logger.debug("MOUSEBUTTONDOWN detected: {}"
                                 .format(clicked_area))
                    if clicked_area == LEFT:
                        self.onClick_left()
                    elif clicked_area == RIGHT:
                        self.onClick_right()

                elif event.type == pygame.QUIT:
                    not_quit = False

            if refresh_interval != 0:
                if int((datetime.datetime.now() - self.last_displayed).total_seconds()) < \
                        refresh_interval:
                    self.load_new_image()
                    self.display_image()

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
