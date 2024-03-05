# Local Business Finder

## Table of Contents

- [Introduction](#introduction)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Deployment](#deployment)
- [Configuration](#configuration)
- [Usage](#usage)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)
- [Contact](#contact)

## Introduction

The Local Business Finder is a Python-based application designed to leverage Google Places API and web scraping techniques to help users discover businesses in their desired locations. This tool is particularly useful for identifying contact information, business types, and additional details to support local economies and provide accessible information.

## Key Features

- **Business Search**: Users can search for businesses by type and location.
- **Data Scraping**: Extracts contact information and additional details from business websites.
- **Google Sheets Integration**: Automatically updates a Google Sheet with search results for easy access and analysis.
- **User Interaction**: Simple command-line interface for inputting search criteria and receiving prompts.

## Technology Stack

- Python
- BeautifulSoup for web scraping
- Google Maps and Places API for business information
- gspread for Google Sheets integration
- Heroku for deployment

## Deployment

This application is deployed on Heroku. Follow these steps for deployment:

1. Fork or clone this repository.
2. Create a new Heroku app.
3. Set up Config Vars in Heroku: `CREDS`, `GOOGLE_MAPS_API_KEY`, and `PORT`.
4. Connect your GitHub repository to Heroku and enable automatic deploys.
5. Deploy the main branch.

Refer to Heroku's official documentation for detailed steps.

## Configuration

When you create the app, you will need to add two buildpacks from the _Settings_ tab. The ordering is as follows:

1. `heroku/python`
2. `heroku/nodejs`

You must then create a _Config Var_ called `PORT`. Set this to `8000`

If you have credentials, such as in the Love Sandwiches project, you must create another _Config Var_ called `CREDS` and paste the JSON into the value field.

Connect your GitHub repository and deploy as normal.

Ensure the following environment variables are configured in your deployment environment:

- `GOOGLE_MAPS_API_KEY`: Your API key for Google Maps and Places.
- `CREDS`: A JSON string of your Google service account credentials for accessing Google Sheets.
- `PORT`: The port number on which your application will run, typically `8000` for local development.

## Usage

After deployment, access the application via the command line and follow the interactive prompts:

1. Input the desired location (e.g., "Cork, Ireland").
2. Choose a business type from the provided options.
3. Review the fetched business information updated in the specified Google Sheet.

Google Sheet Link: [Local Business Finder Results](https://docs.google.com/spreadsheets/d/1SGr8HLTg4N9j9foBEQx93-e1qJEULERhQS-CKm7BSRo/edit?usp=sharing)

## Testing

This application has undergone multiple testing phases:

- Local testing for functionality and bug fixes.
- Heroku deployment testing to ensure proper environment variable configuration.
- Continuous integration testing for upcoming features like Google geolocation API integration.
- We have added checks through the CLI to ensure the correct data is being fetched
- Correct deployment should have the following output
  ![Application Running Correctly](assets/images/app_running.png)

## Contributing

Contributions are always welcome. Please open an issue to discuss proposed changes or submit a pull request.

## License

This project is for use by testing by Code Institute evaluators, it is not meant for personal use or commercial gain. We do not accept any responsibility for the misuse of the code.

## Acknowledgments

- Google Places API for providing extensive business data.
- BeautifulSoup for enabling efficient web scraping.
- The Code Institute for guidance and resources on project deployment.
- To fully understand these API tools and the necessary code and format needed to use them, we mostly referenced Stack Overflow and Google Places, namely the below, so some overlapping may occur for layout and code structure for email/number references:
  [^1]: [Google Maps Address Validation Overview](https://developers.google.com/maps/documentation/address-validation/overview)
  [^2]: [Scrape right phone numbers using Beautiful Soup in Python - Stack Overflow](https://stackoverflow.com/questions/55957937/scrape-right-phone-numbers-using-beautiful-soup-in-python)
  [^3]: [Scraping email addresses Beautiful Soup - Stack Overflow](https://stackoverflow.com/questions/71166959/scraping-email-addresses-beautiful-soup)
  [^4]: [BeautifulSoup: How to extract email from a website - Stack Overflow](https://stackoverflow.com/questions/57944130/beautifulsoup-how-to-extract-email-from-a-website)

## Contact

For inquiries or contributions, please contact [your-email@example.com](mailto:richard@theworkwall.com).
