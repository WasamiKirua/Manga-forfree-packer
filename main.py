import asyncio
import aiohttp
import os
from playwright.async_api import async_playwright
from selectolax.parser import HTMLParser
from utilities import URLValidator, Downloader, Makercbz

async def process_chapter(chapter_link, main_folder):
    async with async_playwright() as p, aiohttp.ClientSession() as session:

        # Launch the browser
        browser = await p.chromium.launch()
        # Open a new page
        page = await browser.new_page()
        # Navigate to the chapter link
        await page.goto(chapter_link)

        # Get the page content
        content = await page.content()

        # Parse the HTML content
        parser = HTMLParser(content)

        # Extract src attributes of img elements inside div with class 'page-break'
        img_srcs = []
        for div in parser.css('div.page-break'):
            for img in div.css('img'):
                src = img.attrs.get('src')
                if src:
                    img_srcs.append(src)
        # Destination folder's name
        chapter_name = chapter_link.split('/')[-2]
        # Iterate img_srcs list and download imgs to the related folder
        await asyncio.gather(*(Downloader.download_image(session, src, main_folder, chapter=chapter_name) for src in img_srcs))

        print(f"Processed chapter: {chapter_link} with {len(img_srcs)} images.")

        # Close the browser
        await browser.close()

async def process_chapter_raw(chapter_link, main_folder):
    async with async_playwright() as p, aiohttp.ClientSession() as session:

        # Launch the browser
        browser = await p.chromium.launch()
        # Open a new page
        page = await browser.new_page()
        # Navigate to the chapter link
        await page.goto(chapter_link)

        # Get the page content
        content = await page.content()

        # Parse the HTML content
        parser = HTMLParser(content)

        # Extract src attributes of img elements inside div with class 'page-break'
        img_srcs_raw = []
        for div in parser.css('div.page-break'):
            for img in div.css('img'):
                src = img.attrs.get('src')
                if src:
                    img_srcs_raw.append(src)
        # Destination folder's name
        chapter_name = chapter_link.split('/')[-2]
        # Iterate img_srcs list and download imgs to the related folder
        await asyncio.gather(*(Downloader.download_image(session, src, main_folder, chapter=chapter_name) for src in img_srcs_raw))

        print(f"Processed chapter: {chapter_link} with {len(img_srcs_raw)} images.")

        # Close the browser
        await browser.close()

async def fetch_chapters(url):
    async with async_playwright() as p:
        # Launch the browser (Chromium, Firefox, or WebKit)
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Go to the webpage
        await page.goto(url)

        # Get the page content
        content = await page.content()

        # Parse the HTML
        tree = HTMLParser(content)

        # Find all the "li" elements with class "wp-manga-chapter"
        global chapters_list
        chapters_list = []
        chapters = tree.css('li.wp-manga-chapter')

        # Extract and print the text and link of each chapter
        for chapter in chapters:
            link = chapter.css_first('a').attributes.get('href')
            title = chapter.css_first('a').text()
            if "raw" not in title:
                chapters_list.append(link)
                #print(f"Title: {title}, Link: {link}")

        # Close the browser
        await browser.close()

        return chapters_list

async def fetch_chapters_raw(url):
    async with async_playwright() as p:
        # Launch the browser (Chromium, Firefox, or WebKit)
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Go to the webpage
        await page.goto(url)

        # Get the page content
        content = await page.content()

        # Parse the HTML
        tree = HTMLParser(content)

        # Find all the "li" elements with class "wp-manga-chapter"
        global chapters_list_raw
        chapters_list_raw = []
        chapters = tree.css('li.wp-manga-chapter')

        # Extract and print the text and link of each chapter
        for chapter in chapters:
            link = chapter.css_first('a').attributes.get('href')
            title = chapter.css_first('a').text()
            if "raw" in title:
                print(f"Appending: {link} to chapters_list_raw")
                chapters_list_raw.append(link)
                #print(f"Title: {title}, Link: {link}")

        # Close the browser
        await browser.close()

        return chapters_list_raw

async def main():
    url_input = input("Enter the Mangaforfree URL: ")

    # Validate URL
    url_replacement = url_input.split('/')[-2]
    base_url = "https://mangaforfree.net/manga/REPLACEMENT/"
    url_validator = URLValidator(base_url)
    is_valid = url_validator.is_valid_url(url_replacement)
    
    # Run fetchers
    if is_valid:
        # Set vars to build main folder's name
        folder_first = url_replacement.split('-')[-2]
        folder_last = url_replacement.split('-')[-1]
        main_folder = f"{folder_first.title()}{folder_last.title()}"
        raw_choice = input(f"Do you want the RAW version? y/n ")

        if raw_choice.lower() == 'y':
            # Create main folder with uppercase
            os.makedirs(f"{main_folder}_RAW/chapters", exist_ok=True)
            os.makedirs(f"{main_folder}_RAW/CBZ_files", exist_ok=True)
            chapters_list_raw = await fetch_chapters_raw(url_input)
            for chapter_link in reversed(chapters_list_raw):
                # Add safe wait
                await asyncio.sleep(delay=5)
                await process_chapter_raw(chapter_link, main_folder=f"{main_folder}_RAW/chapters")
            Makercbz.create_cbz(f"{main_folder}_RAW/chapters", cbz_folder=f"{main_folder}_RAW/CBZ_files")

        elif raw_choice.lower() == 'n':
            # Create main folder with uppercase
            os.makedirs(f"{main_folder}/chapters", exist_ok=True)
            os.makedirs(f"{main_folder}/CBZ_files", exist_ok=True)
            chapters_list = await fetch_chapters(url_input)
            for chapter_link in reversed(chapters_list):
                # Add safe wait
                await asyncio.sleep(delay=5)
                await process_chapter(chapter_link, main_folder=f"{main_folder}/chapters")
            Makercbz.create_cbz(f"{main_folder}/chapters", cbz_folder=f"{main_folder}/CBZ_files")
        else:
            print("Error: answer with 'y' or 'n'")
    else:
        print("Error: the input URL is not valid! ")

# Run the main async function
asyncio.run(main())
