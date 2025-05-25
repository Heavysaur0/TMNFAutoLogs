import requests
from bs4 import BeautifulSoup
# -> pip install beautifulsoup4 requests

def get_tmnf_map_info(uid):
    url = f"https://www.xaseco.org/uidfinder.php?uid={uid}"
    response = requests.get(url)
    
    if response.status_code != 200:
        raise Exception(f"Request failed with status code {response.status_code}")
    
    soup = BeautifulSoup(response.text, 'html.parser')

    table = soup.find('table', {'id': 'uidfinder'})
    if not table:
        raise Exception("UID not found or table structure changed.")

    rows = table.find_all('tr')
    
    error_span = rows[4].find('span', class_='error')
    if error_span:
        raise Exception(f"UID lookup error: {error_span.text.strip()}")

    if len(rows) < 7:
        raise Exception("Unexpected number of rows. UID may be invalid or structure changed.")

    try:
        map_info = {
            'name': rows[4].find_all('td')[1].text.strip(),
            'section':    rows[4].find_all('td')[3].text.strip(),
            'author':     rows[5].find_all('td')[1].text.strip(),
            'environment':rows[5].find_all('td')[3].text.strip(),
            'type':       rows[6].find_all('td')[1].text.strip(),
            'mood':       rows[6].find_all('td')[3].text.strip()
        }
        return map_info
    except (IndexError, AttributeError):
        raise IndexError("Failed to parse table content correctly.")


if __name__ == '__main__':
    A01_track_uid = "BeySZdnfuSh4nHY5xztiXLmlrXe"
    uid = A01_track_uid
    try:
        info = get_tmnf_map_info(uid)
        for key, value in info.items():
            print(f"{key}: {value}")
    except Exception as e:
        print("Error:", e)








# "BeySZdnfuSh4nHY5xztiXLmlrXe"