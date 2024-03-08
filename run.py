import requests
from bs4 import BeautifulSoup
import googlemaps
from google.oauth2.service_account import Credentials
import gspread
import re
import json
import os

# Setup for Google Sheets and Google Places API
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

# Get credentials from environment variable
creds_raw = os.environ.get('CREDS', '{}')  
creds_dict = json.loads(creds_raw)  # Parse the JSON string into a Python dictionary

CREDENTIALS = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)  

# Initialize Google Sheets and Google Maps clients with the credentials
GS_CLIENT = gspread.authorize(CREDENTIALS)
SHEET = GS_CLIENT.open("P_3 code inst").sheet1  
GMAPS_CLIENT = googlemaps.Client(key=os.environ.get('GOOGLE_MAPS_API_KEY')) 

# REassign the GOOGLE_MAPS_API_KEY variable globally
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')

# validation functions for user input
def validate_location_input(location_input):
    """
    Validate the location input by querying Google Place API Find Place request.
    """
    find_place_url = 'https://maps.googleapis.com/maps/api/place/findplacefromtext/json'
    params = {
        'input': location_input,
        'inputtype': 'textquery',
        'fields': 'formatted_address',
        'key': GOOGLE_MAPS_API_KEY
    }
    response = requests.get(find_place_url, params=params).json()

    if response['status'] == 'OK':
        # Return the entire response for further verification by the user
        return response['candidates'][0]
    else:
        return None

        
def get_business_type_input():
    """
    Allow the user to select a business type from a predefined list of options.
    """
    business_types = ['Bar', 'Restaurant', 'Cafe', 'Hotel']
    print("Please select a business type by entering the corresponding number:")
    for i, business_type in enumerate(business_types, start=1):
        print(f"{i}. {business_type}")
    
    while True:
        selection = input("Enter number: \n").strip()
        if selection.isdigit() and 1 <= int(selection) <= len(business_types):
            return business_types[int(selection) - 1]
        else:
            print("Invalid selection. Please enter a number from the list.")

# Introduction and explanation of the tool
def introduction():
    print("Welcome to the Local Business Finder!")
    print("This tool allows you to search for local hospitality businesses information based on their location.")
    print("The search results will be updated in a Google Sheet provided in README.")
    print("Let's get started! Follow the prompts below:\n")


# function to scrape any relevant details or info from website
def get_contact_info(website_url):
    print(f"\nScraping new website: {website_url}")
    emails, phones, additional_info = set(), set(), {}
    description, addressRegion, starRating = '', '', ''
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

            # Extract additional information: description, region and rating
            scripts = soup.find_all('script', {'type': 'application/ld+json'})
            for script in scripts:
                data = json.loads(script.string)
                if 'description' in data:
                    additional_info['description'] = data['description']
                if 'address' in data:
                    additional_info['addressRegion'] = data['address'].get('addressRegion', '')
                if 'starRating' in data:
                    additional_info['starRating'] = data['starRating'].get('ratingValue', '')


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

    return ', '.join(emails) if emails else "Not Available", ', '.join(phones) if phones else "Not Available", {
        'description': description,
        'Region': addressRegion,
        'Rating': starRating
    }

# function to fetch businesses data from Google Places API
def fetch_businesses(location, business_type):
    query = f"{business_type} in {location}"
    print(f"Searching for: {query}\n")
    print(f"****** Start scraping ******\n")
    businesses = []
    search_result = GMAPS_CLIENT.places(query=query)

    if 'results' in search_result and search_result['results']:
        for place in search_result['results'][:5]: 
            name = place.get('name', 'Not Available')
            address = place.get('formatted_address', 'Not Available')
            place_id = place.get('place_id', '')
            details_result = GMAPS_CLIENT.place(place_id=place_id, fields=['website'])
            website = details_result.get('result', {}).get('website', 'Not Available')
            email, phone, additional_info = get_contact_info(website) if website != 'Not Available' else ('Not Available', 'Not Available', {})
            business_info = [name, address, email, phone, website, additional_info.get('description', ''), additional_info.get('addressRegion', ''), additional_info.get('starRating', '')]
            businesses.append(business_info)
    else:
        print("No results found for the specified query.")
    
    return businesses

# add info to Google Sheets
def update_sheet(businesses):
    SHEET.clear()
    SHEET.append_row(["Business Name", "Address", "Email", "Phone", "Website", "Description", "Address Region", "Star Rating"])
    print("\n***** Finished Scraping *****")
    for business in businesses:
        try:
            SHEET.append_row(business)
            # Check if email is not 'Not Available' and print the business name and phone number
            if business[2] != 'Not Available':
                print(f"Business Name: {business[0]}, Email: {business[2]}, Phone: {business[3]}")
        except Exception as e:
            print(f"Error updating sheet for {business[0]}: {e}")

# main function and user input
def main():
    introduction()
    while True:
        validated_location = None
        while not validated_location:
            location_input = input("Enter the location (e.g., 'Cork, Ireland'): ").strip()
            location_response = validate_location_input(location_input)
            if location_response:
                formatted_address = location_response['formatted_address']
                print(f"Found location: {formatted_address}")
                confirm = input("Is this the correct location? (yes/no): ").strip().lower()
                if confirm == 'yes':
                    validated_location = formatted_address
                else:
                    print("Please try entering the location again.\n")
            else:
                print("Invalid location. Please try again.\n")

        business_type = get_business_type_input()
        businesses = fetch_businesses(validated_location, business_type)
        update_sheet(businesses)
        print("\nThe search results have been updated to the Google Sheet titled 'P_3 code inst, you can find the link in the README.'.\n")

        another_search = input("Would you like to perform another search? (yes/no): ").strip().lower()
        if another_search != 'yes':
            print("Thank you for using the Local Business Finder. Goodbye!")
            break

if __name__ == "__main__":
    main()
    