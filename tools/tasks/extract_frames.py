
from pdf2image import convert_from_path

RESOLUTION = 200
THREAD_COUNT = 4

def extract_frames(pdf_file, output_folder, start = None, end = None):

    images = convert_from_path(pdf_file, first_page=start, last_page=end, dpi=RESOLUTION, thread_count=THREAD_COUNT)

    for index, image in enumerate(images):
        
        image.save(f"{output_folder}/{index + 1:03}.png", "PNG")
