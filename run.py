import argparse
import requests
from bs4 import BeautifulSoup
import googlemaps
from google.oauth2.service_account import Credentials
import gspread
import re
import json

# Setup for Google Sheets and Google Places API
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]
SERVICE_ACCOUNT_FILE = 'creds.json'
GOOGLE_MAPS_API_KEY = 'AIzaSyCj4KjlyV3p-FvY50vYYFl8HKtY-sU3OBE'

# Initialize clients
credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPE)
gs_client = gspread.authorize(credentials)
sheet = gs_client.open("P_3 code inst").sheet1
gmaps_client = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

def get_contact_info(website_url):
    print(f"Scraping website: {website_url}")
    emails, phones, additional_info = set(), set(), {}

    def scrape_page(url):
        print(f"Scraping page: {url}")
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract emails from "mailto:" links
            mailto_links = soup.find_all(href=re.compile(r'^mailto:'))
            for mailto in mailto_links:
                email = mailto.get('href').replace("mailto:", "").split('?')[0]  # Remove any query parameters
                emails.add(email)

            # Extract emails from text
            email_regex = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
            text_emails = set(email_regex.findall(soup.get_text()))
            emails.update(text_emails)

            # Extract phone numbers
            phone_regex = re.compile(r'\+\d{1,2}\s?\(?\d{3}\)?\s?\d{3}[-\s]?\d{4}')
            found_phones = phone_regex.findall(soup.get_text())
            phones.update(found_phones)

        except Exception as e:
            print(f"Error scraping {url}: {e}")

    # Initial scrape
    scrape_page(website_url)

    # Attempt to find and scrape additional pages that might contain contact information
    try:
        soup = BeautifulSoup(requests.get(website_url).text, 'html.parser')
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href and any(keyword in href for keyword in ['contact', 'about', 'kontakt']):
                full_url = requests.compat.urljoin(website_url, href)
                scrape_page(full_url)
    except Exception as e:
        print(f"Error finding additional contact info on {website_url}: {e}")

    return ', '.join(emails) if emails else "Not Available", \
           ', '.join(phones) if phones else "Not Available", \
           additional_info
          
def fetch_businesses(location, business_type):
    print(f"Fetching businesses for location: {location}, type: {business_type}")
    businesses = []

    try:
        places_result = gmaps_client.places_nearby(location=location, radius=1000, type=business_type)
        
        if 'results' in places_result and places_result['results']:
            for place in places_result['results'][:5]:  # Limit for testing
                name = place.get('name', 'Not Available')
                address = place.get('vicinity', 'Not Available')
                place_id = place.get('place_id', '')
                
                details_result = gmaps_client.place(place_id=place_id, fields=['website'])
                website = details_result.get('result', {}).get('website', 'Not Available')
                
                email, phone, additional_info = get_contact_info(website) if website != 'Not Available' else ('Not Available', 'Not Available', {})

                business_info = [name, address, email, phone, website, additional_info.get('description', ''), additional_info.get('addressRegion', ''), additional_info.get('starRating', '')]
                businesses.append(business_info)
                print(f"Fetched business info: {business_info}")
        else:
            print("No results found in the Google Places API response.")
    except Exception as e:
        print(f"Error fetching businesses: {e}")
    
    return businesses

def update_sheet(businesses):
    sheet.clear()
    sheet.append_row(["Business Name", "Address", "Email", "Phone", "Website", "Description", "Address Region", "Star Rating"])
    for business in businesses:
        try:
            sheet.append_row(business)
        except Exception as e:
            print(f"Error updating sheet for {business[0]}: {e}")

def main(location, business_type):
    businesses = fetch_businesses(location, business_type)
    update_sheet(businesses)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch and record business information from Google Places.")
    parser.add_argument("--location", help="Latitude,Longitude of the location", required=True)
    parser.add_argument("--type", help="Type of business", required=True)
    
    args = parser.parse_args()
    main(args.location, args.type)
