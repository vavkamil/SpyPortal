#!/usr/bin/env python3

# Credits to https://github.com/hacefresko/EvilPortal

import os
import re
import json
import signal
import sqlite3
import threading
from scapy.all import *
from datetime import datetime


def check_if_root():
    # Check for root priviledges
    if os.getuid() != 0:
        print("[x] Please, run program as root!\n")
        quit()


def banner():
    banner = "\n"
    banner += "  ___         _         ___      _  __  __ \n"
    banner += " | _ \_ _ ___| |__  ___/ __|_ _ (_)/ _|/ _|\n"
    banner += " |  _/ '_/ _ \ '_ \/ -_)__ \ ' \| |  _|  _/\n"
    banner += " |_| |_| \___/_.__/\___|___/_||_|_|_| |_|  \n"
    banner += "    802.11 Probe Requests Sniffer ~ v0.1   \n"

    return banner


def sqlite_connect():
    con = sqlite3.connect("output_probe_data.db")
    cur = con.cursor()
    return con, cur


def show_interfaces():
    interfaces_list = []

    for dirpath, interfaces, filenames in os.walk("/sys/class/net"):
        for interface in interfaces:
            if re.match(r"wl\w+", interface):

                # Directory /sys/class/net/<interface>/type contains
                # the mode in which the interface is operating:
                #   1   -> managed
                #   803 -> monitor
                #

                interface_mode = check_interface_mode(interface)

                interfaces_list.append(
                    {"name": interface, "mode": interface_mode, "channel": 0}
                )

    available_interfaces = ""

    i = 1
    for interface in interfaces_list:
        available_interfaces += "[{}] -> {} ({})\n".format(
            i, interface["name"], interface["mode"]
        )
        i = i + 1

    return interfaces_list, available_interfaces


def check_interface_mode(interface):
    f = open("/sys/class/net/" + interface + "/type", "r")
    interface_type = f.read().rstrip()
    f.close()

    if interface_type == "803":
        interface_mode = "monitor"
    else:
        interface_mode = "managed"

    return interface_mode


def enable_monitor_mode(interface):
    print("[i] Configuring network interface ...")

    os.system("ifconfig " + interface + " down")
    os.system("iw " + interface + " set type monitor")
    os.system("ifconfig " + interface + " up")

    # Set channel to 1 for later scanning
    os.system("iw " + interface + " set channel 1")

    # Check if interface is indeed in monitor mode
    if check_interface_mode(interface) != "monitor":
        print('[x] Newtork interface couldn"t be put in monitor mode!\n')
        return -1

    print("[i] Monitor mode configured succesfuly\n")

    return 0


def sigint_handler(sig, frame):
    print("\n\n[x] SIGINT: Exiting...")

    quit()


def change_channel(interface):
    t = threading.currentThread()
    # We assign stop=False as an attribute of the current thread. This is used to stop the loop from other thread
    channel = 0
    while not getattr(t, "stop", False):
        channel = channel + 1
        if channel > 13:
            channel = 1
        # self.interfaces[nInterface]["channel"] = channel

        # print(channel)
        os.system("iw " + interface + " set channel " + str(channel))
        time.sleep(0.5)

    # os.system("iw " + interface + " set channel 1")
    # self.interfaces[nInterface]["channel"] = 1


def sniffProbeReq(interface):
    probeRequests = []

    # stop is defined as global for the sigint handler to be able to get it
    global stop
    stop = False

    def sigint_handler_probe(sig, frame):
        global stop
        stop = True
        signal.signal(signal.SIGINT, sigint_handler)
        print("quit")

    signal.signal(signal.SIGINT, sigint_handler_probe)

    changeChThread = threading.Thread(target=change_channel, args=(interface,))
    changeChThread.start()

    print("\n[i] Listening for Probe Request (Ctrl+C to stop)\n")

    template = "{0:17} | {1:7} | {2:17} | {3:32} | {4:50}"
    print(template.format("DATETIME", "CHANNEL", "CLIENT", "SSID", "VENDOR"))  # header
    print(
        "------------------|---------|-------------------|----------------------------------|--------------------------------------------------"
    )



    def sniff_client_probes(pkt):
        # Protocol 802.11, type management, subtype probe request
        if pkt.haslayer(Dot11) and pkt[Dot11].type == 0 and pkt[Dot11].subtype == 4:
            client = pkt[Dot11].addr2.upper()
            vendor = check_mac_vendor(client)
            ssid = pkt.info.decode("UTF-8")
            try:
                channel = pkt[Dot11].channel
            except:
                channel = "?"

            newProbeRequest = {"client": client, "ssid": ssid}
            if ssid and newProbeRequest not in probeRequests:
                probeRequests.append(newProbeRequest)
                # print("[%3s] %11s %17s -> %-32.32s" % (str(len(probeRequests)), channel, client, ssid))

                # datetime object containing current date and time
                now = datetime.now()

                # yy-mm-dd H:M:S
                dt_string = now.strftime("%y-%m-%d %H:%M:%S")

                con, cur = sqlite_connect()
                cur.execute(
                    f"INSERT INTO probe_requests (datetime, channel, client, ssid, vendor) VALUES (?, ?, ?, ?, ?)",
                    [dt_string, channel, client, ssid, vendor],
                )
                con.commit()
                con.close()

                print(template.format(dt_string, channel, client, ssid, vendor))
                # print(pkt[Dot11].show())

    sniffer = AsyncSniffer(iface=interface, prn=sniff_client_probes)
    sniffer.start()

    while not stop:
        pass

    changeChThread.stop = True
    sniffer.stop()



def check_mac_vendor(client):
    vendor = "?"
    macaddress = []
    with open("macaddress.io-db.json", "r") as f:
        for line in f:
            macaddress.append(json.loads(line))

    for mac in macaddress:
        if client[:8] == mac["oui"]:
            vendor = mac["companyName"]

    return vendor


def main():
    print(banner())
    signal.signal(signal.SIGINT, sigint_handler)
    check_if_root()

    (interfaces_list, available_interfaces) = show_interfaces()

    # Select network interface
    if len(interfaces_list) == 0:
        print("[x] No network interface detected!\n")
        quit()

    elif len(interfaces_list) >= 1:
        ok = -1
        while ok != 0:
            print("[i] Available network interfaces:\n")
            print(available_interfaces)
            i_interface = int(input("[?] Select network interface > ")) - 1
            print()
            if i_interface < 0 or i_interface >= len(interfaces_list):
                print("[x] Input value out of bounds!\n")
            else:
                if interfaces_list[i_interface]["mode"] != "monitor":
                    ok = enable_monitor_mode(interfaces_list[i_interface]["name"])
                else:
                    ok = 0

    print("[i] Network interface in use: " + interfaces_list[i_interface]["name"])

    probeRequest = sniffProbeReq(interfaces_list[i_interface]["name"])


# main routine
if __name__ == "__main__":
    main()
