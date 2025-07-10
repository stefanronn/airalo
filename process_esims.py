import requests
import json
import sys
import os
import urllib.parse as ul
from datetime import date
from requests.exceptions import RequestException

"""
This script processes esims from Airalo, including obtaining a new token, if necessary
"""

accessfname = "api_access.json"     # File with API access info in JSON format

os.chdir(sys.path[0])            # Set current directory to script directory


def readaccess(accessfname):
    """
    Reads access information data from a JSON file.

    Reads access information data from a JSON file.
    Input: Access info file name
    Return: Dictionary with API access information, or exception
    """
    try:
        with open(accessfname, 'r') as f:
            return json.load(f)
    except Exception as e:
        return e    
    

def test_token(accessinfo):
    """Returns True when the stored token is still valid, else False"""

    url   = accessinfo["balance_url"]
    token = accessinfo["client_token"]
    timeout = accessinfo["timeout"]
    headers = {"Authorization": f"Bearer {token}"}

    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
    except requests.Timeout:
        print("Balance check timed out.", file=sys.stderr)
        return False
    except requests.ConnectionError as exc:
        print(f"Connection error: {exc}", file=sys.stderr)
        return False
    except requests.RequestException as exc:           # catch-all for the rest
        print(f"Request failed: {exc}", file=sys.stderr)
        return False

    if resp.status_code == 200:
        print("Token from access info file is valid.")
        return True

    if resp.status_code in (401, 403):
        print("Token is invalid or expired.")
        return False

    # Any other HTTP status → log as much detail as we can extract
    try:
        msg = resp.json().get("message", resp.text)
    except ValueError:                                 # not JSON
        msg = resp.text
    snippet = msg[:200] + ("…" if len(msg) > 200 else "")
    print(f"Unexpected status {resp.status_code}: {snippet}")
    return False
    

def get_token(accessinfo):
    """Fetch a fresh token"""

    url = accessinfo["token_url"]
    timeout = accessinfo["timeout"]

    multipart = {
        "client_id":     (None, accessinfo["client_id"]),
        "client_secret": (None, accessinfo["client_secret"]),
        "grant_type":    (None, "client_credentials"),
    }

    headers = {"Accept": "application/json"}

    try:
        resp = requests.post(url, files=multipart, headers=headers, timeout=timeout)
    except requests.Timeout:
        print("Token request timed out.")
        return None
    except requests.ConnectionError as exc:
        print(f"Connection error: {exc}")
        return None
    except requests.RequestException as exc:
        print(f"Request failed: {exc}")
        return None

    if resp.status_code in (401, 403):
        try:
            msg = resp.json().get("message", resp.text)
        except ValueError:
            msg = resp.text
        print(f"Authentication failed ({resp.status_code}): {msg}")
        return None

    if not resp.ok:      # any non-2xx apart from 401/403
        try:
            msg = resp.json().get("message", resp.text)
        except ValueError:
            msg = resp.text
        print(f"{resp.status_code}: {msg}")
        return None

    try:
        return resp.json()["data"]["access_token"]
    except (ValueError, KeyError) as exc:   # JSON error or missing key
        snippet = resp.text[:200] + ("…" if len(resp.text) > 200 else "")
        print(f"Malformed token response: {exc} - body starts with: {snippet}")
        return None

    

def post_esim_order(accessinfo, token):
    """Posts an order for new esims"""

    url = accessinfo["esim_order_url"]
    pkg_id = accessinfo["pkg_id"]
    qty = accessinfo["qty"]
    timeout = accessinfo["timeout"]


    multipart = {
        "package_id": (None, pkg_id),
        "quantity":   (None, str(qty)),  
        "type":       (None, "sim"),      
        "description":(None, f"{qty} x {pkg_id}"),
    }

    headers = {
        "Accept":        "application/json",
        "Authorization": f"Bearer {token}",
    }

    try:
        resp = requests.post(url, files=multipart, headers=headers, timeout=timeout)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"Order failed: {exc}")
        return False

    # print(resp.json().get("data", []))
    return True


def get_esim_list(accessinfo, token):
    """gets a list of created esims"""

    url = accessinfo["esim_list_url"]
    created_at = accessinfo["created_at"]
    timeout = accessinfo["timeout"]

    default_qs = {
        "limit": "100",      # max records pere page
        "page":  "1",
        "filter[created_at]": created_at + " - " + created_at,
        "include": "order",
    }

    url       = f"{url}?{ul.urlencode(default_qs, doseq=True)}"
    headers   = {
        "Accept":        "application/json",
        "Authorization": f"Bearer {token}",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()       # raises on 4xx / 5xx
    except RequestException as exc:
        print(f"Network error getting eSIM list: {exc}")
        return None
    except ValueError as exc:           # .json() failed
        print(f"Invalid JSON in eSIM list response ({resp.status_code}): {resp.text}")
        return None

    return resp.json().get("data") or []


def validate_esim_list(accessinfo, esims):
    """Validates a list of esims"""

    if len(esims) == accessinfo["qty"]:
        print("Correct count:", len(esims))
    else:
        print("Wrong count:", len(esims))
        return False

    for sim in esims:
        slug = sim.get("package_id") or (sim.get("simable") or {}).get("package_id")
        if slug != accessinfo["pkg_id"]:
            return False

    print("Correct package slugs:", accessinfo["pkg_id"])
    return True




def main():
    
    accessinfo = readaccess(accessfname)
    if isinstance(accessinfo, Exception):
        print("Problems reading access info:", str(accessinfo))
        return
    
    validtoken = test_token(accessinfo)

    if validtoken:
        token = accessinfo["client_token"]
    else:
        token = get_token(accessinfo)
        print("Token:", token)

    esims_created = post_esim_order(accessinfo, token)
    if not esims_created:
        print("Esims order failed")
        return

    esims = get_esim_list(accessinfo, token)
    if not esims:
        print("Esims listing failed")
        return
   
    correct_esims = validate_esim_list(accessinfo, esims)

    if not correct_esims:
        print("Esims not validated")
        return
    else:
        print("Success!")

    return


if __name__ == "__main__":
    main()

