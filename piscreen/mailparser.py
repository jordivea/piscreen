from PIL import Image, ImageDraw, ImageFont
import configparser
import os
import logging
import time
import imaplib
import email
from email.header import decode_header
import tempfile
import textwrap

configfile = 'piscreen.cfg'
config = configparser.ConfigParser()
config.read(configfile)

logging.basicConfig(filename=config['log']['logfile'],
                    format='%(asctime)s %(module)s %(levelname)-8s %(message)s',
                    level=eval('logging.' + config['log']['level']),
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


class MailParser():

    def is_authorized(self, rcpt):
        for r in config['email']['authorized_recipients'].split(','):
            if r in rcpt:
                return True
        return False

    def create_img_from_txt(self, text):
        # create image from text and save in piscreen media directory
        txt = text.strip()

        img = Image.new('RGB', (480,320), color=(255,255,255))
        fnt = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeSansBoldOblique.ttf', 30)
        drw = ImageDraw.Draw(img)

        w, h = fnt.getsize(txt)
        if w < 460:
            #allow 10 pixel margin
            x = (480 - w)/2
            y = (300 - h)/2

            drw.text((x,y), txt, font=fnt, fill=(0,0,0))
        else:
            # wrap to 30 chars which is aprox 460 chars with current font
            # lines are aligned to the left, according to the longest line
            lines = textwrap.wrap(txt, width=30, replace_whitespace=False)
            x = (480 - len(max(lines, key=len))/2)
            max_width = 0
            y = 10
            rendered_lines = []
            for line in lines:
                w, h = fnt.getsize(line)
                max_width = max(max_width, w)
                rendered_lines.append((y, line))
                y += h

            rendered_x = (480 - max_width)/2
            for rendered_y, rendered_line in rendered_lines:
                drw.text((rendered_x, rendered_y), rendered_line, font=fnt,
                        fill=(0,0,0))

        filename = tempfile.NamedTemporaryFile(prefix="piscreen_", suffix=".jpg")
        filename = filename.name.split('/')[-1]
        filepath = os.path.join(config['config']['images_path'], filename)

        logger.info("New image {} created with text '{}'".format(filepath, txt))
        img.save(filepath)

    def read_inbox(self):
        # create an IMAP4 class with SSL
        imap = imaplib.IMAP4_SSL(config['email']['server'])
        # authenticate
        imap.login(config['email']['username'], config['email']['password'])

        status, msgs = imap.select("INBOX")
        logger.debug("Number of messages in inbox: {}".format(int(msgs[0])))

        if status != 'OK':
            logger.error("Error reading INBOX")
            return

        status, messages = imap.search(None, 'ALL')
        if status != 'OK':
            logger.error("No messages in INBOX")
            return

        for num in messages[0].split():
            # fetch the email message by ID
            res, msg = imap.fetch(num, "(RFC822)")
            if res != 'OK':
                logger.error("Error fetching message {}".format(int(num)))
                continue

            for response in msg:
                if isinstance(response, tuple):
                    # parse a bytes email into a message object
                    msg = email.message_from_bytes(response[1])

                    # decode email sender
                    sender, encoding = decode_header(msg.get("From"))[0]
                    if isinstance(sender, bytes):
                        sender = sender.decode(encoding)
                    logger.debug("Message from {}".format(sender))

                    if not self.is_authorized(sender):
                        logger.info("Message from unauthorized user {} marked for deletion".format(sender))
                        # Remove message from imap
                        imap.store(num, '+FLAGS', '\\Deleted')
                        continue

                    # decode the email subject
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        # if it's a bytes, decode to str
                        subject = subject.decode(encoding)

                    #TODO process subject.upper(): IMAGE/RECEIPE/ACTION
                    logger.debug("Message received from authorized sender '{}' and subject '{}'".format(sender, subject))

                    # if the email message is multipart
                    if msg.is_multipart():
                        logger.debug("Message multipart")
                        # iterate over email parts
                        for part in msg.walk():
                            # extract content type of email
                            content_type = part.get_content_type()
                            content_disposition = str(part.get("Content-Disposition"))
                            try:
                                # get the email body
                                body = part.get_payload(decode=True).decode()
                            except:
                                pass
                            if content_type == "text/plain" and "attachment" not in content_disposition:
                                # print text/plain emails and skip attachments
                                self.create_img_from_txt(body)
                            elif "attachment" in content_disposition:
                            #if "attachment" in content_disposition:
                                # download attachment
                                filename = part.get_filename()
                                if filename:
                                    filepath = os.path.join(config['config']['images_path'], filename)
                                    # download attachment and save it
                                    logger.info("Writing attachment to: {}".format(filepath))
                                    open(filepath, "wb").write(part.get_payload(decode=True))
                    else:
                        # extract content type of email
                        logger.debug("Message not multipart. Discarding")
                        content_type = msg.get_content_type()
                        # get the email body
                        body = msg.get_payload(decode=True).decode()
                        if content_type == "text/plain":
                            # print only text email parts
                             self.create_img_from_txt(body)

                    logger.debug("Message processed. Marking for deletion")
                    imap.store(num, '+FLAGS', '\\Deleted')

        # remove deleted messages, close the connection and logout
        imap.expunge()
        imap.close()
        imap.logout()

    def run(self):
        polling_interval = int(config['email']['polling_interval'])
        while True:
            logger.debug("Mail parser process started")
            self.read_inbox()
            logger.debug("Mail parser process stopped for {}s".format(polling_interval))
            time.sleep(polling_interval)

if __name__ == '__main__':
    mail = MailParser()
    mail.run()
