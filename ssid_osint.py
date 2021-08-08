#!/usr/bin/env python3

import json
import argparse
import requests
from requests.auth import HTTPBasicAuth

wigle_api_url = "https://api.wigle.net/api/v2"
wigle_api_name = ""
wigle_api_token = ""


def banner():
    banner = "\n"
    banner += "  ___ ___ ___ ___     ___  ___ ___ _  _ _____ \n"
    banner += " / __/ __|_ _|   \   / _ \/ __|_ _| \| |_   _|\n"
    banner += " \__ \__ \| || |) | | (_) \__ \| || .` | | |  \n"
    banner += " |___/___/___|___/   \___/|___/___|_|\_| |_|  \n"

    return banner


def parse_args():
    parser = argparse.ArgumentParser(
        description="xx",
        epilog="Have a nice day :)",
    )
    parser.add_argument("-ssid", dest="ssid", help="Enter the ESSID", required=True)
    parser.add_argument("-city", dest="city", help="Enter the City")
    parser.add_argument("-country", dest="country", help="Enter the Country")

    return parser.parse_args()


def search_ssid(ssid, boundingbox):

    if boundingbox:
        lat1, lat2, long1, long2 = boundingbox
        url = f"{wigle_api_url}/network/search?onlymine=false&freenet=false&paynet=false&latrange1={lat1}&latrange2={lat2}&longrange1={long1}&longrange2={long2}&ssid={ssid}"
    else:
        url = f"{wigle_api_url}/network/search?onlymine=false&freenet=false&paynet=false&ssid={ssid}"

    r = requests.get(
        url,
        auth=HTTPBasicAuth(wigle_api_name, wigle_api_token),
    )
    json_obj = json.loads(json.dumps(r.json()))
    return json_obj


def check_mac_vendor(bssid):
    vendor = "?"
    macaddress = []
    with open("macaddress.io-db.json", "r") as f:
        for line in f:
            macaddress.append(json.loads(line))

    for mac in macaddress:
        if bssid[:8] == mac["oui"]:
            vendor = mac["companyName"]

    return vendor


def parse_ssid_data(ssid_obj):
    i = 0
    ssid_dict = {}

    for res in ssid_obj:
        ssid_dict[i] = {}
        ssid_dict[i]["latitude"] = res["trilat"]
        ssid_dict[i]["longitude"] = res["trilong"]
        ssid_dict[i]["essid"] = res["ssid"]
        ssid_dict[i]["bssid"] = res["netid"]
        ssid_dict[i]["vendor"] = check_mac_vendor(res["netid"])
        ssid_dict[i]["channel"] = res["channel"]
        ssid_dict[i]["encryption"] = res["encryption"]
        ssid_dict[i]["country"] = res["country"]
        ssid_dict[i]["city"] = res["city"]
        ssid_dict[i]["date"] = res["lastupdt"]
        ssid_dict[i]["postalcode"] = res["postalcode"]

        i = i + 1

    return ssid_dict


def search_city(city):
    r = requests.get(
        f"{wigle_api_url}/network/geocode?addresscode={city}",
        auth=HTTPBasicAuth(wigle_api_name, wigle_api_token),
    )
    json_obj = json.loads(json.dumps(r.json()))

    i = 1
    for res in json_obj["results"]:
        print(f"\t[{i}] -> {res['display_name']}")

    i_city = int(input("\n[i] Select city from the list > ")) - 1
    print("\n")
    boundingbox = json_obj["results"][i_city]["boundingbox"]
    return boundingbox


def main(args):

    boundingbox = ""
    if args.city and not args.country:
        print(f"[i] Searching city: {args.city}\n")
        boundingbox = search_city(args.city)

    print(f"[i] Searching ESSID: {args.ssid}\n")
    ssid_obj = search_ssid(args.ssid, boundingbox)

    if ssid_obj["totalResults"] == 0:
        exit("[i] SSID not found\n")
    elif ssid_obj["totalResults"] > 10:
        exit("[i] Found more than ten results, please specify country & city\n")

    ssid_dict = {}
    ssid_dict = parse_ssid_data(ssid_obj["results"])

    print(f"[i] Found {len(ssid_dict)} results\n")
    for i in ssid_dict:
        print(
            f"\t[i] {ssid_dict[i].get('essid')} -> {ssid_dict[i].get('encryption')} ({ssid_dict[i].get('channel')}) -> {ssid_dict[i]['bssid']} -> {ssid_dict[i]['vendor']}"
        )
        print(
            f"\t[i] {ssid_dict[i].get('city')} ({ssid_dict[i].get('postalcode')}) -> {ssid_dict[i].get('country')} -> https://www.google.com/maps/search/?api=1&query={ssid_dict[i].get('latitude')},{ssid_dict[i].get('longitude')}"
        )
        print(f"\t[i] {ssid_dict[i].get('date')}\n")


# main routine
if __name__ == "__main__":
    print(banner())
    args = parse_args()
    main(args)
