from seleniumbase import *
from supabase import create_client, Client
import sys
import csv
import time
from threading import Thread, Event

from concurrent.futures import (
    ProcessPoolExecutor,
    ThreadPoolExecutor,
    wait,
    FIRST_EXCEPTION,
)

sys.argv.append("-n") 


SUPABASE_URL = "https://yegmcsxgxkbqbjdmsvfm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InllZ21jc3hneGticWJqZG1zdmZtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MTk2NzI3NzIsImV4cCI6MjAzNTI0ODc3Mn0.79Czw_E8h4Bm3iV22Ja6R66-l-rTHfucnuWPeWAFuAY"
SUPABASE_TABLE_NAME = "ck_proxy_gd"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def load_data(start_data, end_data):

    proxy = []
    with open("proxy.csv") as csv_proxy_file:
        proxy = list(csv.reader(csv_proxy_file, delimiter=":"))

    line_count = 0

    proxy = proxy[int(start_data) : int(end_data)]

    return {"proxy": proxy}

def check_ip(sb):
    sb.uc_open_with_reconnect("https://iphub.info/",10)
    sb.sleep(2)

    td_hostname = sb.is_element_present("td#hostname")
    if td_hostname:
        hostname = sb.get_text("td#hostname")
        country = sb.get_text("td > span#countryName")
        type_proxy = sb.get_text('td > span#type')
        print(f"{hostname} , {type_proxy}", file=sys.__stderr__)

        if "Good IP" in type_proxy:
            return {"status": True, "hostname": hostname, "country": country,"type": type_proxy}
        else:
            return {"status": False, "hostname": is_hostname, "country": country,"type": type_proxy}
    else:
        return {"status": False, "data": ""}

def insert_supabase(proxy, hostname, country, type, good):
    try:
        response = (
            supabase.table(SUPABASE_TABLE_NAME)
            .insert({"proxy": proxy, "hostname": hostname, "country": country, "type": type, "good": good})
            .execute()
        )
    except Exception as e:
        if "duplicate key" in e.message:
            pass
        else:
            print(f"{e}")


def run_bot(data_proxy, index, job_number):
    proxy_ip = data_proxy[0]
    proxy_port = data_proxy[1]

    proxy = f"socks5://{proxy_ip}:{proxy_port}"

    with SB(undetectable=True, xvfb=True, proxy=proxy) as sb:
        sb.maximize_window()
        try:
            is_good = check_ip(sb)

            if is_good["status"]:
                hostname = is_good["hostname"]
                country = is_good["country"]
                type_proxy = is_good["type"]

                insert_supabase(proxy, hostname, country, type_proxy, true)
        except Exception as e:
            print(f"[Index #{index}] - TERJADI ERROR SAAT RUN :{e}")
            sb.driver.quit()

def main():

    if len(sys.argv) < 3:
        print('Params require "node run.js 0 5"')
        os._exit(1)

    get_job_number = True

    start_data = int(sys.argv[1])
    end_data = int(sys.argv[2])

    job_number = 0

    if get_job_number:
        job_number = int(sys.argv[3])

    workers = 1

    if not start_data and not end_data:
        print('Params require "node run.js 0 5"')
        os._exit(1)

    data = load_data(start_data, end_data)
    data_proxy = data["proxy"]

    event = Event()

    start_time = time.time()

    futures = []

    line_count = 0

    with ThreadPoolExecutor(max_workers=workers) as executor:
        for index in range(start_data + 1, end_data + 1):
            futures.append(
                executor.submit(
                    run_bot,
                    data_proxy[line_count],
                    index,
                    job_number,
                )
            )
            line_count += 1

    wait(futures, return_when=FIRST_EXCEPTION)

    end_time = time.time()
    # print("FINISH IN: ", end_time - start_time)
    hours, rem = divmod(end_time - start_time, 3600)
    minutes, seconds = divmod(rem, 60)
    print("FINISH IN {:0>2}:{:0>2}:{:05.2f}".format(int(hours), int(minutes), seconds))


main()
