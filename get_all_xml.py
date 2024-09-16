import requests
import gzip
import xml.etree.ElementTree as ET
import os
from datetime import datetime, timedelta
import sys
import csv
def process_sitemap(url, folder):
    response = requests.get(url)
    if response.status_code == 200:
        try:
            # Try to decompress as gzip
            content = gzip.decompress(response.content)
        except (EOFError, gzip.BadGzipFile):
            # If decompression fails, assume it's plain XML
            content = response.content
        
        # Try to parse the content as XML
        try:
            root = ET.fromstring(content)
        except ET.ParseError:
            print(f"Failed to parse XML from {url}")
            return

        namespace = {
            'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9',
            'image': 'http://www.google.com/schemas/sitemap-image/1.1'
        }
        
        # Save the XML content
        xml_filename = url.split('/')[-1].replace('.gz', '')
        with open(os.path.join(folder, xml_filename), 'wb') as f:
            f.write(content)
        print(f"Downloaded XML: {xml_filename}")
        
        # Create a list of HTML files with metadata
        html_files = []
        for url_element in root.findall('.//ns:url', namespace):
            loc = url_element.find('ns:loc', namespace)
            if loc is not None and loc.text.endswith('.html'):
                lastmod = url_element.find('ns:lastmod', namespace)
                lastmod = lastmod.text if lastmod is not None else ''
                changefreq = url_element.find('ns:changefreq', namespace)
                changefreq = changefreq.text if changefreq is not None else ''
                priority = url_element.find('ns:priority', namespace)
                priority = priority.text if priority is not None else ''
                image = url_element.find('image:image', namespace)
                image_url = image.find('image:loc', namespace).text if image is not None else ''
                html_files.append([loc.text, lastmod, changefreq, priority, image_url])
        
        # Save the list of HTML files to a CSV
        csv_filename = f"html_list_{xml_filename.replace('.xml', '.csv')}"
        with open(os.path.join(folder, csv_filename), 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['URL', 'Last Modified', 'Change Frequency', 'Priority', 'Image URL'])
            writer.writerows(html_files)
        print(f"Created HTML CSV list: {csv_filename}")
    else:
        print(f"Failed to download sitemap: {url}")


def main(website_name):
    if website_name == "prnewswire":
        start_date = datetime(2011, 1, 1)
        end_date = datetime.now()
        current_date = start_date
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        while current_date <= end_date:
            year = current_date.year
            month = current_date.month
            print(month)
            month_text = months[month - 1]
            
            url = f"https://www.prnewswire.com/Sitemap_Index_{month_text}_{year}.xml.gz"
            folder_name = f"prnewswire_sitemaps_{year}"
            
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)
            
            print(f"Processing: {url}")
            process_sitemap(url, folder_name)
            
            current_date += timedelta(days=32)
            current_date = current_date.replace(day=1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python get_xml.py <website name>  | Websites supported are prnewswire, businesswire, candawire")
        sys.exit(1)
    
    website_name = sys.argv[1]
    
    main(website_name)
