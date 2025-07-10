# Airalo eSIM Order Testing

This package tests proper handling when placing eSIM orders via the Airalo API.

## Steps Executed

1. Test the current API token, if any, to see if it is still valid  
2. If not valid, obtain a new API token  
3. Place an order for 6 new eSIMs, with package ID `"merhaba-7days-1gb"`  
4. List the created eSIMs of the day  
5. Validate the eSIM list so that it has the correct quantity and the correct package slug  

## Package Contents

The package contains 2 files:

1. **`api_access.json`**  
   JSON file that contains API credentials and other input data needed for the test:
   - `"client_id"`: Client ID for API  
   - `"client_secret"`: Client secret for API  
   - `"timeout"`: Timeout for API request, normally 10 seconds  
   - `"token_url"`: URL for API request to obtain a fresh token  
   - `"balance_url"`: URL for API request to test the current token  
   - `"esim_order_url"`: URL for API request to order new eSIMs  
   - `"esim_list_url"`: URL for API request to list created eSIMs  
   - `"pkg_id"`: Package ID for the ordered eSIMs  
   - `"qty"`: Number of eSIMs to be ordered  
   - `"created_at"`: The date of the eSIM order  
   - `"client_token"`: Token for API requests. If not a valid token, the token test will fail and a new token will be fetched.

2. **`process_esims.py`**  
   Python script that executes the testing steps outlined above. Input is fetched from the `api_access.json` file, placed in the same directory
   as the script itself.
