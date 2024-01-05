from urllib.parse import urlparse
import asyncio
import os
import random
import zipfile

class URLValidator:
    """
    A class to validate URLs with a replaceable part.
    """
    def __init__(self, base_url):
        """
        Initializes the URLValidator with a base URL.
        """
        self.base_url = base_url

    def is_valid_url(self, replacement):
        """
        Checks if the URL with the replacement is valid.
        """

        # Replace 'REPLACEMENT' in the base URL with the actual replacement value
        url_with_replacement = self.base_url.replace('REPLACEMENT', replacement)

        # Parse the URL and validate the scheme and netloc (domain)
        parsed_url = urlparse(url_with_replacement)
        return all([parsed_url.scheme, parsed_url.netloc])
    
class Downloader:
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15",
        # Add more user agents for diversity
    ]
    @staticmethod
    async def download_image(session, url, main_folder, chapter='', max_retries=3, delay=25):
        # Create the directory if it doesn't exist
        os.makedirs(f"{main_folder}/{chapter}", exist_ok=True)
        # Extracting image name from URL
        image_name = url.split('/')[-1]
        # Creating a path for the image
        path = os.path.join(main_folder + "/" + chapter + "/" + image_name)
        # Async powered by try/except
        attempts = 0
        while attempts < max_retries:
            try:
                await asyncio.sleep(delay)
                headers = {'User-Agent': random.choice(Downloader.user_agents)}
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        # Write the image to a file
                        with open(path, 'wb') as file:
                            file.write(await response.read())
                        print(f"Downloaded {main_folder}/{chapter}/{image_name}")
                        return
                    else:
                        raise Exception(f"Failed to download {main_folder}/{chapter}/{image_name}. Status: {response.status}")
                        attempts += 1
            except Exception as e:
                print(f"Attempt {attempts + 1} failed for {url}: {e}")
                attempts += 1
                if attempts < max_retries:
                    print(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
        raise Exception(f"Max retries reached for {url}")

class Makercbz:
    @staticmethod
    def create_cbz(main_folder, cbz_folder):
        # Initialize a dictionary to hold the file names for each subfolder
        subfolder_files = {}

        # Check if the base folder exists
        if os.path.exists(main_folder) and os.path.isdir(main_folder):
            # List all entries in the base folder
            entries = os.listdir(main_folder)
            # Filter out subfolders and sort them
            subfolders = [entry for entry in entries if entry.startswith('chapter-')]
            # Sorting the chapters numerically
            sorted_chapters = sorted(subfolders, key=lambda x: int(x.split('-')[1]))
        else:
            print(f"Error: destination folder '{main_folder}' does not exists")

        for chapter in sorted_chapters:
            chapter_path = os.path.join(main_folder, chapter)
            if os.path.isdir(chapter_path):
                # List files in the chapter folder
                chapter_files = os.listdir(chapter_path)
                # Sorting the files numerically (assuming filenames are numeric or have numeric prefixes)
                sorted_files = sorted(chapter_files, key=lambda x: int(''.join(filter(str.isdigit, x))))
                subfolder_files[chapter] = sorted_files
        for chapter, files in subfolder_files.items():
            # Create the path for the CBZ file
            cbz_file_path = os.path.join(cbz_folder, f"{chapter}.cbz")

            # Create a ZIP file
            with zipfile.ZipFile(cbz_file_path, 'w') as zipf:
                for file in files:
                    # Add each JPG file to the ZIP archive
                    zipf.write(os.path.join(main_folder, chapter, file), file)

