import requests
import gzip
import os
from datetime import datetime, timedelta
import sys
import pandas as pd
from lxml import etree
import re

class SitemapProcessor:
    def __init__(self, website_name):
        self.website_name = website_name
        self.config = self.get_website_config()
        self.all_data = pd.DataFrame(columns=['URL', 'Last Modified', 'Change Frequency', 'Priority'])

    def get_website_config(self):
        configs = {
            "prnewswire": {
                "start_date": datetime(2011, 1, 1),
                "url_template": "https://www.prnewswire.com/Sitemap_Index_{month_text}_{year}.xml.gz",
                "folder_template": "prnewswire_sitemaps",
            },
            "canadawire": {
                "start_date": datetime(2014, 1, 1),
                "url_template": "https://www.newswire.ca/Sitemap_Index_{month_text}_{year}.xml.gz",
                "folder_template": "canadawire_sitemaps",
            },
            "businesswire": {
                "start_date": datetime(2020, 11, 1),
                "url_template": "https://www.businesswire.com/smaps/smaps-bw/{year}-{month:02d}-{day:02d}.xml.gz",
                "folder_template": "businesswire_sitemaps",
            },
        }
        return configs.get(self.website_name)

    def download_and_parse_xml(self, url):
        response = requests.get(url)
        if response.status_code == 200:
            try:
                content = gzip.decompress(response.content)
            except (EOFError, gzip.BadGzipFile):
                content = response.content
            
            try:
                # Try parsing with lxml's XMLParser
                parser = etree.XMLParser(recover=True)
                root = etree.fromstring(content, parser=parser)
                return root, content
            except etree.XMLSyntaxError as e:
                print(f"Failed to parse XML from {url}")
                print(f"Parse error: {e}")
                print(f"Content (first 200 characters): {content[:200]}")
                
                # Attempt to extract URLs using regex as a fallback
                urls = re.findall(b'<loc>(.*?)</loc>', content)
                if urls:
                    print(f"Extracted {len(urls)} URLs using regex")
                    dummy_root = etree.Element('urlset')
                    for url in urls:
                        url_elem = etree.SubElement(dummy_root, 'url')
                        loc_elem = etree.SubElement(url_elem, 'loc')
                        loc_elem.text = url.decode('utf-8')
                    return dummy_root, content
        else:
            print(f"Failed to download sitemap: {url}")
        return None, response.content

    def process_sitemap(self, url):
        root, _ = self.download_and_parse_xml(url)
        if root is None:
            return pd.DataFrame(columns=['URL', 'Last Modified', 'Change Frequency', 'Priority'])

        namespace = {
            'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'
        }

        sitemap_data = []
        for url_element in root.xpath('.//ns:url', namespaces=namespace):
            loc = url_element.xpath('./ns:loc', namespaces=namespace)
            if loc:
                lastmod = url_element.xpath('./ns:lastmod', namespaces=namespace)
                lastmod = lastmod[0].text if lastmod else ''
                changefreq = url_element.xpath('./ns:changefreq', namespaces=namespace)
                changefreq = changefreq[0].text if changefreq else ''
                priority = url_element.xpath('./ns:priority', namespaces=namespace)
                priority = priority[0].text if priority else ''
                
                sitemap_data.append([loc[0].text, lastmod, changefreq, priority])
        
        return pd.DataFrame(sitemap_data, columns=['URL', 'Last Modified', 'Change Frequency', 'Priority'])

    def save_csv(self, data, filename):
        data.to_csv(filename, index=False, encoding='utf-8')
        print(f"Created CSV: {filename}")

    def process_sitemaps(self):
        end_date = datetime.now()
        current_date = self.config['start_date']
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        
        if not os.path.exists(self.config['folder_template']):
            os.makedirs(self.config['folder_template'])
        annual_data = pd.DataFrame(columns=['URL', 'Last Modified', 'Change Frequency', 'Priority'])
        while current_date <= end_date:
            year = current_date.year
            month = current_date.month
            month_text = months[month - 1]
            
            if self.website_name == "businesswire":
                month_start = current_date.replace(day=1)
                month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                for day in range(1, month_end.day + 1):
                    url = self.config['url_template'].format(year=year, month=month, day=day)
                    print(f"Processing: {url}")
                    annual_data = pd.concat([annual_data, self.process_sitemap(url)], ignore_index=True)
                print(len(annual_data))
            else:
                url = self.config['url_template'].format(month_text=month_text, year=year)
                print(f"Processing: {url}")
                annual_data = pd.concat([annual_data, self.process_sitemap(url)], ignore_index=True)
                print(len(annual_data))
            
            if month == 12 or (current_date.year == end_date.year and current_date.month == end_date.month):
                filename = os.path.join(self.config['folder_template'], f"annual_sitemap_{year}.csv")
                self.save_csv(annual_data, filename)
                self.all_data = pd.concat([self.all_data, annual_data], ignore_index=True)
                annual_data = pd.DataFrame(columns=['URL', 'Last Modified', 'Change Frequency', 'Priority'])
            
            current_date += timedelta(days=32)
            current_date = current_date.replace(day=1)

        # Save full report
        full_filename = os.path.join(self.config['folder_template'], f"full_sitemap_{self.website_name}.csv")
        self.save_csv(self.all_data, full_filename)

def main(website_name):
    processor = SitemapProcessor(website_name)
    processor.process_sitemaps()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python get_xml.py <website name>")
        print("Websites supported are: prnewswire, businesswire, canadawire")
        sys.exit(1)
    
    website_name = sys.argv[1].lower()
    
    if website_name not in ["prnewswire", "businesswire", "canadawire"]:
        print("Unsupported website. Please choose from: prnewswire, businesswire, canadawire")
        sys.exit(1)
    
    main(website_name)