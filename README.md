# music_video_processing
Automated title card generation and stitching of different music videos. This was done for the Online Gurupurnima event of Sunaada Art Foundation, Bengaluru.

## Requirements:
- An Excel file containing performer data in `.xls` or `.xlsx` format.
    - File should contain the following columns named exactly:
        * Name
        * Location
        * Composition
        * Raag
        * Taal
        * Description
    - File should be named `Performer Data.xlsx`
    - A sample file is available in this repo
- Each performer should name their file exactly like this:
    - name_location.mp4
    - Example: `Chirag Agarwal_London.mp4`
- You will have to install `Helvetica-Bold` font in your system. If not, use a similar looking font and update the script to use it.
- Place this script in the same location as the videos and run it
- It should create a `FINAL_VIDEO.mp4` if all goes well
