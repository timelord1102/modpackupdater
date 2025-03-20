import requests
import zipfile
import json
from tqdm import tqdm
import sys
import time

def comprehensive_search(url, modlist, update_version, mod_loader, reverse_search):
    modcount = 0
    updatable = 0
    failed = {}
    for mod in tqdm(modlist, desc="Checking mods"):
        found = False
        if mod['path'].split('.')[-1] == 'disabled':
            continue
        modcount += 1
        download_url = mod['downloads'][0].split('/')
        request = requests.get(url + download_url[4])
        modinfo = request.json()
        title = modinfo['title']
        if mod['path'].split('/')[0] == "mods" and mod_loader in modinfo['loaders'] and update_version in modinfo['game_versions']:
            request = requests.get(url + download_url[4] + '/version')
            modversions = request.json()
            if reverse_search:
                modversions = modversions[::-1]
            for version in tqdm(modversions, desc="Checking versions", leave=False):
                if update_version in version['game_versions'] and mod_loader in version['loaders']:
                    updatable += 1
                    found = True
                    break
        else:
            if update_version in modinfo['game_versions']:
                updatable += 1
                found = True
        if not found:
            if mod['path'].split('/')[0] not in failed:
                failed[mod['path'].split('/')[0]] = []
            failed[mod['path'].split('/')[0]].append(title)
    return modcount, updatable, failed

def fast_search(url, modlist, update_version, mod_loader):
    modcount = 0
    updatable = 0
    failed = {}
    for mod in tqdm(modlist, desc="Checking mods"):
        if mod['path'].split('.')[-1] == 'disabled':
            continue
        modcount += 1
        download_url = mod['downloads'][0].split('/')
        request = requests.get(url + download_url[4])
        modinfo = request.json()
        if update_version in modinfo['game_versions']:
            updatable += 1
        else:
            if mod['path'].split('/')[0] not in failed:
                failed[mod['path'].split('/')[0]] = []
            failed[mod['path'].split('/')[0]].append(modinfo['title'])
    return modcount, updatable, failed

color_codes = {
    "black": "\033[30m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
    "reset": "\033[0m",
    "orange": "\033[38;5;208m"
}

mod_loader = None
if len(sys.argv) < 3:
    print(color_codes["red"] + "Error: Not enough arguments." + color_codes["reset"])
    print("Usage: python main.py <modpack_file> <update_version> <mod_loader (optional)>")
    sys.exit(1)

if len(sys.argv) == 4 and sys.argv[3].lower() in ["fabric", "forge", "neoforge", "quilt"]:
    mod_loader = sys.argv[3].lower()
elif len(sys.argv) == 4:
    print("Invalid mod loader. Please use 'fabric', 'forge', 'neoforge', or 'quilt'.")
    exit(1)

url = "https://api.modrinth.com/v2/project/"

modpack_file = sys.argv[1]
update_version = sys.argv[2]

archive = zipfile.ZipFile(modpack_file, 'r')
moddata = archive.read('modrinth.index.json').decode('utf-8')

jsondata = json.loads(moddata)

reverse_search = jsondata['dependencies']['minecraft'] < update_version

modlist = jsondata['files']



if mod_loader:
    print(f"You are about to perform a full search. {color_codes['orange']}Makes double the API calls as fast search.{color_codes['reset']}")
    proceed = input("Do you wish to proceed? (Y/N): ")
    if proceed.lower() != "y":
        print("Exclude mod loader to perform a fast search.")
        exit(0)
    start_time = time.perf_counter()
    modcount, updatable, failed = comprehensive_search(url, modlist, update_version, mod_loader, reverse_search)
else:
    print(color_codes["orange"] + "WARNING" + color_codes["reset"] + " - Fast search does not check for mod loader compatibility.")
    start_time = time.perf_counter()
    modcount, updatable, failed = fast_search(url, modlist, update_version, mod_loader)
end_time = time.perf_counter()

print(f"{color_codes['blue']}Total mods: {color_codes['reset']} {modcount}")
print(f"{color_codes['green']}Updatable mods:{color_codes['reset']} {updatable}")
print(f"{color_codes['red']}Failed mods: {color_codes['reset']}{len(failed)}")
print(f"{color_codes['blue']}Update Ratio:{color_codes['reset']} {updatable/modcount*100:.2f}%")
export = input("Would you like to export the failed mods to a file? (Y/N): ")
if export.lower() == "y":
    with open('failed_mods.txt', 'w', encoding='utf-8') as f:
        for key in failed:
            f.write(f"{key.capitalize()}:\n")
            for mod in sorted(failed[key]):
                f.write(f"  {mod}\n")
print (f"{color_codes['blue']}Done!{color_codes['reset']} in {end_time-start_time:.2f} seconds.")
if not mod_loader:
    print("Please note that the fast search does not check for mod loader compatibility.")
    print("If you wish to perform a full search, please include the mod loader as an argument.")
