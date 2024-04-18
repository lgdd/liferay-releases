import json
import requests
import subprocess
from tqdm import tqdm
from pathlib import Path
from bs4 import BeautifulSoup

def download_file(url, filename):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024
    with open(filename, 'wb') as file, tqdm(
        desc=filename.name,
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=block_size,
    ) as bar:
        for data in response.iter_content(block_size):
            bar.update(len(data))
            file.write(data)

def create_release(url):
  try:
    response = requests.get(url, timeout=5)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, 'html.parser')
    links = soup.find_all("a", href=True)

    for link in links:
      if "tomcat" in link["href"]:
        file_name = link["href"]
        absolute_url = url + "/" + file_name
        download_file(absolute_url, Path(file_name))
    subprocess.run(["gh", "release", "create", releaseKey, "$(ls *tomcat*)"])
    subprocess.run(["rm", "*tomcat*"])
  except requests.exceptions.Timeout:
    print("Timed out for {0}".format(url))

if __name__ == "__main__":
  releases = json.loads(requests.get("https://raw.githubusercontent.com/lgdd/liferay-product-info/main/releases.json").text)
  releases.reverse()
  for release in releases:
    url = release["url"]
    releaseKey = release["releaseKey"]
    try:
      subprocess.check_output(
        ["gh", "release", "view", releaseKey],
        stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
      error_message = e.output.decode("utf-8")
      if "release not found" in error_message:
        create_release(url)
      else:
        print(error_message)
        exit(1)