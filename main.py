import cpuinfo
import pyopencl as cl
import psutil
import math
import requests
import re
from bs4 import BeautifulSoup

cpu_name = cpuinfo.get_cpu_info()['brand_raw']
print(f"CPU: {cpu_name}")

def get_gpu_info():
    platforms = cl.get_platforms()
    devices = []
    for p in platforms:
        devices.extend(p.get_devices())
    return list(set(d.name.strip() for d in devices))

gpus = get_gpu_info()
brands = ['nvidia', 'amd', 'intel']

select_gpus = [gpu for gpu in gpus if any(brand in gpu.lower() for brand in brands)]
gpu_name = select_gpus[0] if select_gpus else None
if gpu_name:
    gpu_name = re.sub(r'^(NVIDIA|AMD|Intel)\s*', '', gpu_name, flags=re.IGNORECASE).strip()
print(f"GPU: {gpu_name}")

mem = psutil.virtual_memory()
uram = round(mem.total / (1024**3), 2)
ram = 2**math.ceil(math.log2(uram))
print(f"RAM: {ram} GB")

url = input("Enter Steam link:")
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
cookies = {
    "birthtime": "568022401",
    "mature_content": "1"
}

def get_gpu_name(url):
    res = requests.get(url, headers=headers, cookies=cookies)
    soup = BeautifulSoup(res.text, 'html.parser')

    min_reqs = soup.find('div', class_='game_area_sys_req_leftCol')
    if min_reqs:
        nested_list = min_reqs.find('ul', class_='bb_ul')
        if nested_list:
            items = nested_list.find_all('li')
            for li in items:
                if "Graphics:" in li.get_text():
                    scr_gpu = li.get_text().replace("Graphics:", "").strip()
                    return scr_gpu

    return "Not found"

def get_cpu_name(url):
    res = requests.get(url, headers=headers, cookies=cookies)
    soup = BeautifulSoup(res.text, 'html.parser')

    min_reqs = soup.find('div', class_='game_area_sys_req_leftCol')
    if min_reqs:
        nested_list = min_reqs.find('ul', class_='bb_ul')
        if nested_list:
            items = nested_list.find_all('li')
            for li in items:
                if "Processor:" in li.get_text():
                    scr_cpu = li.get_text().replace("Processor:", "").strip()
                    return scr_cpu

    return "Not found"

def get_ram_name(url):
    res = requests.get(url, headers=headers, cookies=cookies)
    soup = BeautifulSoup(res.text, 'html.parser')

    min_reqs = soup.find('div', class_='game_area_sys_req_leftCol')
    if min_reqs:
        nested_list = min_reqs.find('ul', class_='bb_ul')
        if nested_list:
            items = nested_list.find_all('li')
            for li in items:
                if "Memory:" in li.get_text():
                    scr_ram = li.get_text().replace("Memory:", "").strip()
                    return scr_ram

    return "Not found"


def clean_name(str):
    if "®" in str or "™" in str:
        str = str.replace("®", "").replace("™", "")
    if "(R)" in str or "(TM)" in str:
        str = str.replace("(R)", "").replace("(TM)", "")
    str = re.sub(r'\s*@\s*\d+(\.\d+)?\s*GHz.*', '', str, flags=re.IGNORECASE)

    if " or " in str:
        str = str.split(" or ", 1)[0]
    str = re.split(r'\s*/\s*', str, maxsplit=1)[0]
    if " w/ " in str:
        str = str.split(" w/ ", 1)[0]
    str = re.sub(r'(?<!\bGeForce\s)\b(GTX|RTX)\b', r'GeForce \1', str)
    str = re.sub(r'\bIntel\s+(?!Core\b)(i\d)', r'Intel Core \1', str, flags=re.IGNORECASE)

    return str.rstrip()

def trim_vram(gpu_name):
    pattern = r'\s?\(?\d+\s?GB\)?.*'
    clean_name = re.sub(pattern, '', gpu_name, flags=re.IGNORECASE)
    return clean_name.rstrip()

def trim_at_ram(str):
    target = " RAM"

    if target in str:
        return str.split(target, 1)[0]

    return str.rstrip()

scr_ram = trim_at_ram(get_ram_name(url))
scr_cpu_name = clean_name(get_cpu_name(url))
scr_gpu_name = clean_name(get_gpu_name(url))
scr_gpu_name = re.sub(r'^(NVIDIA|AMD|Intel)\s*', '', scr_gpu_name, flags=re.IGNORECASE).strip()
print(f"Steam Minimum GPU Requirement: {scr_gpu_name}")
print(f"Steam Minimum CPU Requirement: {scr_cpu_name}")
print(f"Steam Minimum RAM Requirement: {scr_ram}")

def get_cpu_rating(cpu_name):
    formatted_name = cpu_name.replace(" ", "+")
    url = f"https://www.cpubenchmark.net/cpu.php?cpu={formatted_name}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            label = soup.find(string="Single Thread Rating")

            if label:
                parent_div = label.find_parent('div')
                score_div = parent_div.find_next_sibling('div')
                if score_div:
                    score = score_div.text.strip().replace(",", "")
                    return int(score)
    except Exception as e:
        print(f"Error: {e}")
    return None

scr_cpu_score = get_cpu_rating(scr_cpu_name)
cpu_score = get_cpu_rating(clean_name(cpu_name))

def get_gpu_rating(gpu_name):
    formatted_name = gpu_name.replace(" ", "+")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        list_response = requests.get("https://www.videocardbenchmark.net/gpu_list.php", headers=headers)
        if list_response.status_code != 200:
            return None

        list_soup = BeautifulSoup(list_response.text, 'html.parser')
        gpu_link = None
        for a in list_soup.find_all('a', href=True):
            href = a['href']
            if f'gpu={formatted_name}&id=' in href:
                gpu_link = href.split('#')[0]
                if gpu_link.startswith('video_lookup.php?'):
                    gpu_link = gpu_link.replace('video_lookup.php?', 'gpu.php?')
                break

        if not gpu_link:
            return None

        url = f"https://www.videocardbenchmark.net/{gpu_link}"
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            right_desc = soup.find('div', class_='right-desc')
            if right_desc:
                icon_div = right_desc.find('div', class_='speedicon')
                if icon_div:
                    score_span = icon_div.find_next_sibling('span')
                    if score_span:
                        return int(score_span.text.strip().replace(",", ""))
    except Exception as e:
        print(f"Error: {e}")
    return None

gpu_score = get_gpu_rating(gpu_name)
scr_gpu_score = get_gpu_rating(trim_vram(scr_gpu_name))
scr_ram = int("".join(re.findall(r'\d+', scr_ram)))

if gpu_score < scr_gpu_score:
    print("GPU: Not Compatible ❌")
elif gpu_score >= scr_gpu_score:
    print("GPU: Compatible ✅")

if cpu_score < scr_cpu_score:
    print("CPU: Not Compatible ❌")
elif cpu_score >= scr_cpu_score:
    print("CPU: Compatible ✅")

if ram < scr_ram:
    print("Enough RAM not available ❌")
elif ram >= scr_ram:
    print("Enough RAM is available ✅")