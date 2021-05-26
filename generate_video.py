#!/usr/bin/env python
import os
from moviepy.editor import *
import subprocess
import pandas as pd
import multiprocessing as mp
import time
import shutil

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
VIDEO_SIZE = (1920, 1080)
WIDTH, HEIGHT = VIDEO_SIZE
TITLE_CARD_DURATION = 5 # seconds
FPS = 30
ALL_VIDEOS_TXT_FILE = 'all_videos.txt'
PERFORMER_DATA = None
TITLE_CARDS_FOLDER = 'title_cards'
CONVERTED_VIDEOS_FOLDER = 'converted_videos'

def create_single_title_card(performer_data):
    """
    Create a single title card for the performer.
    This is to be run using multiprocessing.

    :param list performer_data: list of doct data objects of the performers
    """
    name = performer_data['Name']
    location = performer_data['Location']
    title_card_path = '%s/%s_%s_titlecard.mp4' % (TITLE_CARDS_FOLDER, name.lower(), location.lower())

    # Return if the title card was already created
    if os.path.exists(title_card_path):
        print('Title card %s was already created. Skipping creating again.' % title_card_path)
        return

    print("Creating Title Card for %s" % name)

    # Name
    name_clip = TextClip(name.title(), color='white', font=FONT, fontsize=85)
    name_clip = name_clip.set_position(("center", HEIGHT/6))

    # Location
    location_clip = TextClip('(%s)' % location.title(), color='white', font=FONT, fontsize=60)
    location_clip = location_clip.set_position(("center", HEIGHT/6 + 90))

    # Description
    # Divide the description into lines of 9 words each
    desc = performer_data['Description'].split()
    descriptions = []
    words_per_line = 9
    pos = HEIGHT/3 + 40
    for i in range(0, len(desc), words_per_line):
        d = TextClip(' '.join(desc[i:i+words_per_line]), color='white', font=FONT, fontsize=45)
        d = d.set_position(("center", pos))
        pos += 60
        descriptions.append(d)

    # Composition name
    composition = TextClip(performer_data['Composition'].title(), color='white', font=FONT, fontsize=80)
    composition = composition.set_position(("center", HEIGHT/2 + 80))

    # Raag
    raag = TextClip('Raag %s' % performer_data['Raag'].title(), color='white', font=FONT, fontsize=70)
    raag = raag.set_position(("center", HEIGHT/2 + 190))

    # Taal
    taal = TextClip('(%s)' % performer_data['Taal'].title(), color='white', font=FONT, fontsize=60)
    taal = taal.set_position(("center", HEIGHT/2 + 280))

    # Composite all text clips to make a video
    cvc_title = CompositeVideoClip([name_clip, location_clip] + descriptions + [composition, raag, taal], size=VIDEO_SIZE)
    cvc_title = cvc_title.set_duration(TITLE_CARD_DURATION).set_fps(FPS)

    cvc_title.write_videofile(title_card_path,
                              codec='libx264',
                              fps=FPS)

def create_title_cards():
    """
    Create title cards for the performers.
    """
    # Create a new folder named 'title_cards'
    try:
        os.mkdir(TITLE_CARDS_FOLDER)
    except FileExistsError:
        pass

    pool = mp.Pool(mp.cpu_count())
    pool.map(create_single_title_card, PERFORMER_DATA)

def convert_portrait_to_landscape(video):
    """
    Note: Not being used currently but keeping for future in case we need it.
    Convert the given portrait video to landscape

    :param str video: Name of the video to be converted
    """
    cmd = 'ffmpeg -y -i {video} -vf "scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:-1:-1:color=black" {video}'
    cmd = cmd.split()
    cmd[5] = cmd[5].format(width=WIDTH, height=HEIGHT)
    cmd[3] = video
    filename, ext = os.path.splitext(video)
    cmd[-1] = '%s_landscape%s' % (filename, ext)

    print('Converting video %s from portrait to landscape\ncmd = %s' % (video, cmd))
    subprocess.call(cmd)

def ensure_videos_exist():
    """
    Ensure that all performer videos exist in the current folder.
    """
    all_videos = get_final_videos(title_cards=False)
    missing_videos = [v for v in all_videos if not os.path.exists(v)]
    if missing_videos:
        msg = 'The following videos were not found. Please make sure they are named correctly:\n%s'
        raise ValueError(msg % '\n'.join(missing_videos))

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

def get_final_videos(title_cards=True, converted=False):
    """
    Return the list of all videos and title cards in the correct order
    
    :param bool title_cards: Add the title cards to the list if True
    :param bool converted: Add the suffix "_converted" to filenames if True
    """
    all_videos = []
    for peformer in PERFORMER_DATA:
        video = '%s_%s.mp4' % (peformer['Name'], peformer['Location'])
        filename, ext = os.path.splitext(video)
        title_card = '%s/%s_titlecard%s' % (TITLE_CARDS_FOLDER, filename, ext)
        if converted:
            video = '%s/%s_converted%s' % (CONVERTED_VIDEOS_FOLDER, filename, ext)
            video = video.lower()
            title_card = '%s/%s_titlecard_converted%s' % (CONVERTED_VIDEOS_FOLDER, filename, ext)
        if title_cards:
            all_videos.append(title_card.lower())
        all_videos.append(video)

    return all_videos

def convert_single_video(filename):
    """
    Convert a single video to have standard audio codec/sample rate

    :param str filename: Name of the file to be converted
    """
    basename = os.path.basename(filename)
    video_path = '%s/%s_converted.mp4' % (CONVERTED_VIDEOS_FOLDER, os.path.splitext(basename)[0].lower())

    # Return if the video was already converted
    if os.path.exists(video_path):
        print('Video %s was already converted. Skipping converting again.' % video_path)
        return

    cmd = "ffmpeg -y -i \"{filename}\" -f lavfi -i anullsrc -c:v copy -video_track_timescale 30k -c:a aac -ac 6 -ar 48000 -shortest {filename}_converted.mp4"
    cmd = cmd.split()
    cmd[3] = filename
    cmd[-1] = video_path
    print("Converting video %s to compatible format\ncmd = %s" % (filename, cmd))
    subprocess.call(cmd)

def convert_videos():
    """
    Convert all performer videos and title cards to standard format
    """
    # Create a new folder named 'converted_videos'
    try:
        os.mkdir(CONVERTED_VIDEOS_FOLDER)
    except FileExistsError:
        pass

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
    shutil.rmtree(CONVERTED_VIDEOS_FOLDER)
    os.remove(ALL_VIDEOS_TXT_FILE)
    print('Cleaned up')

if __name__ == '__main__':
    start = time.time()
    PERFORMER_DATA = read_data_from_file(r'Performer Data.xlsx')

    # Ensure the videos are present
    ensure_videos_exist()
    print('All videos exist on disk')

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
