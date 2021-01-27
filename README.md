# Final Fantasy XIV Lodestone Parser

## What?
This code will do the following:

1. Parse a lodestone profile.
2. Download non-cosmetic icons.
3. Extract average level.
4. Store worn-item ids and item level in JSON
5. Convert icons as Guetzli compressed JPG files
6. Upload icons to BASE_URL/images/CLASS/ folder
7. Upload json to BASE_URL/datafiles/CLASS_itemids.json

## Why?
I wanted a way to automatically extract data from my Lodestone profile to my personal website.

## How?
1. Clone the repository.
2. Install necessary python package with: *python -m pip install beautifulsoup4 pyguetzli pysftp python-dotenv*
3. Add the following parameters to a .env file:
   1. LODESTONE_URL - full path  to your lodestone profile
   2. SFTP_HOST - your SFTP host
   3. SFTP_USER - your SFTP username
   4. SFTP_PASS - your SFTP password
   5. BASE_PATH - the base path of your SFTP login from root (/) for example *MYSITE.COM* willl use */your_account_root/MYSITE.COM/* for all relevant interactions
4. Run the code.