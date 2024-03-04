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
CREDENTIALS = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPE)
GS_CLIENT = gspread.authorize(CREDENTIALS)
SHEET = GS_CLIENT.open("P_3 code inst").sheet1
GMAPS_CLIENT = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

def validate_coordinates(input_str):
    try:
        lat, lng = map(float, input_str.split(","))
        if lat < -90 or lat > 90 or lng < -180 or lng > 180:
            raise ValueError("Coordinates out of range.")
        return input_str
    except ValueError as e:
        print(f"Invalid coordinates: {e}")
        return None

def validate_business_type(value):
    if not value:
        raise argparse.ArgumentTypeError("Business type must not be empty.")
    return value

def get_contact_info(website_url):
    print(f"Scraping website: {website_url}")
    emails, phones, additional_info = set(), set(), {}
    mailto_found = False

    def scrape_page(url):
        nonlocal mailto_found
        print(f"Scraping page: {url}")
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract "mailto:" emails first
            mailto_links = soup.find_all('a', href=re.compile(r'^mailto:'))
            for mailto in mailto_links:
                email = mailto['href'].replace("mailto:", "").split('?')[0]
                emails.add(email)
                mailto_found = True

            if not mailto_found:
                # Extract text-based emails only if no "mailto:" email is found
                text_emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', soup.get_text())
                emails.update(text_emails)

            # Extract phone numbers
            possible_phones = re.findall(r'\b(?:\+?\d{1,3}\s*(?:\(0?\d{1,3}\))?|\(0?\d{1,3}\)\s*)?(?:(?:\d\s*){6,}\d)\b', soup.get_text())
            phones.update(possible_phones)


        except Exception as e:
            print(f"Error scraping {url}: {e}")

    scrape_page(website_url)

    # Attempt to find and scrape additional contact pages
    try:
        soup = BeautifulSoup(requests.get(website_url).text, 'html.parser')
        for link in soup.find_all('a', href=True):
            href = link['href']
            if any(keyword in href.lower() for keyword in ['contact', 'about', 'kontakt']):
                full_url = requests.compat.urljoin(website_url, href)
                scrape_page(full_url)
    except Exception as e:
        print(f"Error finding additional contact info on {website_url}: {e}")

    return ', '.join(emails) if emails else "Not Available", ', '.join(phones) if phones else "Not Available", additional_info


def fetch_businesses(location, business_type):
    print(f"Fetching businesses for location: {location}, type: {business_type}")
    businesses = []

    try:
        places_result = GMAPS_CLIENT.places_nearby(location=location, radius=1000, type=business_type)
        
        if 'results' in places_result and places_result['results']:
            for place in places_result['results'][:5]:  # Limit for testing
                name = place.get('name', 'Not Available')
                address = place.get('vicinity', 'Not Available')
                place_id = place.get('place_id', '')
                
                details_result = GMAPS_CLIENT.place(place_id=place_id, fields=['website'])
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
    SHEET.clear()
    SHEET.append_row(["Business Name", "Address", "Email", "Phone", "Website", "Description", "Address Region", "Star Rating"])
    for business in businesses:
        try:
            SHEET.append_row(business)
        except Exception as e:
            print(f"Error updating sheet for {business[0]}: {e}")

def main():
    while True:
        location_input = input("Enter the coordinates (latitude,longitude): ")
        location = validate_coordinates(location_input)
        if location:
            break
        else:
            print("Please enter valid coordinates.")

    business_type = input("Enter the business type: ").strip()
    if business_type:
        businesses = fetch_businesses(location, business_type)
        update_sheet(businesses)
    else:
        print("Business type cannot be empty.")

if __name__ == "__main__":
    main()