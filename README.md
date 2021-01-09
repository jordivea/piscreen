# piscreen

Python application to display images in a 480x320 display

Screen is divided in left/center/right areas
Left/Right -> navigation
Center -> Menu

Menu:
- Images (default)
- Receipes


Images:
- Loads images from local directory
- Background process checks gmail and saves it in directory. New image, triggers a flag to load instantly


Gmail process:
- Loads emails only from a given recipient (config file)
- Email subject
    - IMAGE: attachment
    - TEXT: creates an image with the text
    - RECEIPE: loads receipe in text file md4 

Schedule
- Step 1: load image from local directory, navigation
- Step 2: gmail process - IMAGE
- Step 3: gmail process - TEXT
- Step 4: receipes menu


