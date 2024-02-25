# Import necessary libraries
import argparse
import requests
from bs4 import BeautifulSoup
import googlemaps
from google.oauth2.service_account import Credentials
import gspread

# Setup Google Sheets and Google Places
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]
SERVICE_ACCOUNT_FILE = 'creds.json'
GOOGLE_MAPS_API_KEY = 'AIzaSyCj4KjlyV3p-FvY50vYYFl8HKtY-sU3OBE'

# Authorize Google Sheets client
credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPE)
gs_client = gspread.authorize(credentials)
sheet = gs_client.open("P_3 code inst").sheet1

# Authorize Google Maps client
gmaps_client = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

def get_website_email(website_url):
    """Attempt to scrape the website for an email address."""
    print(f"Attempting to scrape website: {website_url}")
    email = "Not Available"
    try:
        response = requests.get(website_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        email_tags = soup.find_all('a', href=True)
        for tag in email_tags:
            if 'mailto:' in tag['href']:
                email = tag['href'].split(':')[1]
                print(f"Email found: {email}")
                break
    except Exception as e:
        print(f"Error scraping website: {e}")
    return email

def fetch_businesses(location, business_type):
    print(f"Fetching businesses for location: {location}, type: {business_type}")
    businesses = []
    try:
        places_result = gmaps_client.places_nearby(location=location, radius=1000, type=business_type)
        print(f"Google Places API Response: {places_result}")  # Log the raw API response

        if not places_result.get('results'):
            print("No results found in the Google Places API response.")
            return businesses

        for place in places_result['results'][:10]:  # Limit for testing
            business_info = {
                'name': place.get('name', 'Not Available'),
                'address': place.get('vicinity', 'Not Available'),
                'phone': 'Not Available',
                'email': 'Not Available',
                'website': 'Not Available'
            }

            # Fetch additional details for phone and website
            place_id = place.get("place_id", "")
            if place_id:
                details = gmaps_client.place(place_id=place_id, fields=['formatted_phone_number', 'website'])
                result = details.get("result", {})
                business_info['phone'] = result.get('formatted_phone_number', 'Not Available')
                business_info['website'] = result.get('website', 'Not Available')
                if business_info['website'] != 'Not Available':
                    business_info['email'] = get_website_email(business_info['website'])
            
            print(f"Fetched business info: {business_info}")
            businesses.append([business_info['name'], business_info['address'], business_info['phone'], business_info['email']])
    except Exception as e:
        print(f"Error fetching businesses: {e}")
    return businesses


def update_sheet(businesses):
    """Update the Google Sheet with the fetched business information."""
    print("Updating Google Sheet...")
    sheet.clear()  # Clear existing content
    sheet.append_row(["Business Name", "Address", "Phone Number", "Email"])  # Header
    for business in businesses:
        sheet.append_row(business)
    print("Sheet updated successfully.")

def main(location, business_type):
    """Main function to fetch businesses and update sheet."""
    businesses = fetch_businesses(location, business_type)
    update_sheet(businesses)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch and record business information.")
    parser.add_argument("--location", help="Latitude,Longitude of the location", required=True)
    parser.add_argument("--type", help="Type of business", required=True)
    
    args = parser.parse_args()
    main(args.location, args.type)