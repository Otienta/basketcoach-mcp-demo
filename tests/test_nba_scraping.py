# tests/test_nba_scraping.py – VERSION FINALE (scraping léger comme TechCrunch)
import requests
from bs4 import BeautifulSoup

def test_nba_ranking():
    url = "https://www.basketball-reference.com/leagues/NBA_2026_standings.html"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, 'html.parser')
    table = soup.find('table', id='confs_standings_E')
    for row in table.find_all('tr')[:5]:
        cells = row.find_all('td')
        if cells:
            print(cells[0].get_text(strip=True), cells[2].get_text(), "-", cells[3].get_text())

if __name__ == "__main__":
    test_nba_ranking()