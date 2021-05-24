#!/usr/bin/python3
import os
from moviepy.editor import *
import subprocess
import pandas as pd
import multiprocessing as mp
import time

__doc__ = """
Requirements:
- Excel file containing performer data in .xls or .xlsx format.
    - File should contain the following columns named exactly:
        * Name
        * Location
        * Composition
        * Raag
        * Taal
    - File should be named "Performer Data.xlsx"
- Each performer should name their file exactly like this:
    - <name>_<location>
    - example: Chirag Agarwal_London.mp4
- Place this script in the same location as the videos and run it
- It should create a FINAL_VIDEO.mp4 if all goes well
"""

__author__ = "Chirag Agarwal, London, 24/05/2021"

FONT = 'Helvetica-Bold'
PERFORMER_NAME = 'Chirag Agarwal'
PERFORMER_LOCATION = 'London'
COMPOSITION = 'Jago Mohan Pyare'
RAAG = 'Bhairav'
TAAL = 'Teental'
VIDEO_SIZE = (1920, 1080)
WIDTH, HEIGHT = VIDEO_SIZE
TITLE_CARD_DURATION = 5 # seconds
FPS = 30
ALL_VIDEOS_TXT_FILE = 'all_videos.txt'
PERFORMER_DATA = None

def create_single_title_card(performer_data):
    """
    Create a single title card for the performer.
    This is to be run using multiprocessing.

    :param list performer_data: list of doct data objects of the performers
    """
    name = performer_data['Name']
    location = performer_data['Location']
    print("Creating Title Card for %s" % name)

    # Name
    name_clip = TextClip(name, color='white', font=FONT, fontsize=85)
    name_clip = name_clip.set_position(("center", HEIGHT/6))

    # Location
    location_clip = TextClip('(%s)' % location, color='white', font=FONT, fontsize=60)
    location_clip = location_clip.set_position(("center", HEIGHT/6 + 90))

    # Composition name
    composition = TextClip(performer_data['Composition'], color='white', font=FONT, fontsize=80)
    composition = composition.set_position(("center", HEIGHT/3 + 40))

    # Raag
    raag = TextClip('Raag %s' % performer_data['Raag'], color='white', font=FONT, fontsize=70)
    raag = raag.set_position(("center", HEIGHT/3 + 140))

    # Taal
    taal = TextClip('(%s)' % performer_data['Taal'], color='white', font=FONT, fontsize=60)
    taal = taal.set_position(("center", HEIGHT/2 + 50))

    # Composite all text clips to make a 5 second video
    cvc_title = CompositeVideoClip([name_clip, location_clip, composition, raag, taal], size=VIDEO_SIZE)
    cvc_title = cvc_title.set_duration(TITLE_CARD_DURATION).set_fps(FPS)

    cvc_title.write_videofile('%s_%s_titlecard.mp4' % (name.lower(), location.lower()),
                              codec='libx264',
                              fps=FPS)

def create_title_cards():
    """
    Create title cards for the performers.
    """
    pool = mp.Pool(mp.cpu_count())
    pool.map(create_single_title_card, PERFORMER_DATA)

def stitch_videos():
    """
    Stitch the videos together using ffmpeg
    """
    all_videos = get_final_videos(converted=True)
    create_video_list_file(all_videos)
    cmd = 'ffmpeg -y -f concat -safe 0 -i {all_videos_file} -c copy FINAL_VIDEO.mp4'
    cmd = cmd.split()
    cmd[-4] = ALL_VIDEOS_TXT_FILE

    print('Stitching final video together!\ncmd = %s' % cmd)
    subprocess.call(cmd)

def create_video_list_file(all_videos):
    """
    Create a txt file containing a list of all the videos in order

    :param list all_videos: list of all videos to be converted
    """
    all_videos = ["file '%s'" % v for v in all_videos]
    with open(ALL_VIDEOS_TXT_FILE, 'w') as f:
        f.write('\n'.join(all_videos))

def get_final_videos(converted=False):
    """
    Return the list of all videos and title cards in the correct order

    :param bool converted: Add the suffix "_converted" to filenames if True
    """
    all_videos = []
    for peformer in PERFORMER_DATA:
        video = '%s_%s.mp4' % (peformer['Name'], peformer['Location'])
        filename, ext = os.path.splitext(video)
        title_card = '%s_titlecard%s%s' % (filename, '_converted' if converted else '', ext)
        if converted:
            video = '%s_converted%s' % (filename, ext)
            video = video.lower()
        all_videos.extend([title_card.lower(), video])

    return all_videos

def convert_single_video(filename):
    """
    Convert a single video to have standard audio codec/sample rate

    :param str filename: Name of the file to be converted
    """
    cmd = "ffmpeg -y -i \"{filename}\" -f lavfi -i anullsrc -c:v copy -video_track_timescale 30k -c:a aac -ac 6 -ar 48000 -shortest {filename}_converted.mp4"
    cmd = cmd.split()
    cmd[3] = filename
    cmd[-1] = '%s_converted.mp4' % os.path.splitext(filename)[0].lower()
    print("Converting video %s to compatible format\ncmd = %s" % (filename, cmd))
    subprocess.call(cmd)

def convert_videos():
    """
    Convert all performer videos and title cards to standard format
    """
    all_videos = get_final_videos()

    pool = mp.Pool(mp.cpu_count())
    pool.map(convert_single_video, all_videos)

def read_data_from_file(filename):
    """
    Read the performer data from the excel file.
    Return the data as list of dict objects

    :param str filename: Name of the file to be read
    """
    df = pd.read_excel(filename, engine='openpyxl')
    return df.to_dict(orient='records')

def cleanup():
    """
    Delete all the temp converted files
    """
    all_videos = get_final_videos(converted=True)
    for v in all_videos:
        os.remove(v)
    os.remove(ALL_VIDEOS_TXT_FILE)
    print('Cleaned up')

if __name__ == '__main__':
    start = time.time()
    PERFORMER_DATA = read_data_from_file(r'Performer Data.xlsx')

    # Create title cards
    create_title_cards()
    print('All cards created in %f seconds!' % (time.time() - start))

    # Convert all videos to compatible format
    convert_videos()
    print('All videos converted in %f seconds!' % (time.time() - start))

    # Stitch the videos into one final video
    stitch_videos()
    print('Final video is ready! FINAL_VIDEO.mp4')

    # Cleanup
    cleanup()

    print('Total time taken = %f seconds' % (time.time() - start))
