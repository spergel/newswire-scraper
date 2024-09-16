from bs4 import BeautifulSoup
import re



def getindividualarticle(soup):
    release = soup.find("section", class_="release-body container") 
    for paragraph in release.find_all("p"):
        if paragraph.find('b') is None:
            paragraph = paragraph.get_text()
            paragraph = re.sub(r'\s+', ' ', paragraph).strip()
            print(paragraph)
        else:
            getcompanies(paragraph)
    
    if release:
        legend = release.find("span", class_="legendSpanClass")
        location = release.find("span", class_="xn-location")
        chron = release.find("span", class_="xn-chron")
        source = release.find("a")
        ticker = release.find("a", class_="ticket-symbol")
        print(legend)
        print(location.get_text(strip=True))
        print(chron.get_text(strip=True))
        print(source.get_text(strip=True))
        if ticker:
            print(ticker.get_text(strip=True))
    else:
        print("Legend span not found")
    print(paras)
def getcompanies(paragraph):
    is_bold = paragraph.find('b') is not None
    first_word_bold = paragraph.find('b') and paragraph.find('b').text.strip().startswith('About')

    if is_bold and first_word_bold:
        # Extract company name (everything bolded after "About")
        company_name = paragraph.find('b').text.strip().split('About ', 1)[1]
        
        # Extract description (everything that is not bolded)
        description = ''.join(child.string for child in paragraph.children if child.name != 'b')
        
        # Clean up the description
        description = re.sub(r'\s+', ' ', description).strip()
        print(f"Company Name: {company_name}")
        print(f"Description: {description.strip()}")
    else:
        print("The paragraph doesn't meet the required format.")

if __name__ == "__main__":
    with open("prnewswire.html", "r", encoding="utf-8") as r:  # Ensure correct file encoding
        soup = BeautifulSoup(r, 'html.parser')
    getindividualarticle(soup)
