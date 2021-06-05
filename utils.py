import logging
import re
import requests

from hashlib import sha3_512

import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_secret(q, secret):
    """
    """
    return q == secret


def compare_bh_hashes(db_obj, hash_obj):
    """
    """
    if db_obj is None:
        logger.info("DB obj is none")
        return False

    db_hash, web_hash = db_obj["hash"], hash_obj["hash"]

    return db_hash != web_hash


def push_notification(bot, chat_id, text):
    """
    """
    bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")


def get_bayernheim_hash(bayernheim_link):
    mieten = requests.get(bayernheim_link)
    mieten_text = mieten.text

    hash_sha3_512 = sha3_512(mieten_text.encode("utf-8")).hexdigest()
    hash_obj = {"hash": hash_sha3_512}
    logger.info(f"Calculated hash: {hash_sha3_512}")
    return hash_obj


def get_bayernheim_text(bayernheim_link):
    """
    """
    return f"Changes in BayernHeim: {bayernheim_link}"


def get_immoscout_apartments(immo_search_url):
    """
    """
    apartments = []

    try:
        response_text = requests.post(immo_search_url)
        apartments_json = response_text.json()
        apartments = apartments_json["searchResponseModel"]["resultlist.resultlist"]["resultlistEntries"][0]["resultlistEntry"]
    except Exception as e:
        logger.warn("Could not read any listed appartement")
        apartments = []

    if not type(apartments) is list:
        apartments = [apartments]

    return apartments


def filter_unseen_apartments(apartments, seen_apartments):
    """
    """
    unseen_apartments = []

    for apartment in apartments:
        hash_obj = {"hash": apartment["@id"]}
        if not apartment["@id"] in seen_apartments:
            unseen_apartments.append(apartment)
            seen_apartments.append(hash_obj)

    return unseen_apartments


def process_unseen_apartments(unseen_apartments, bot, chat_id, immo_collection_name):
    """
    """
    # public_companies = ["GWG", "GEWOFAG"]
    for unseen_apartment in unseen_apartments:
        apartment = unseen_apartment["resultlist.realEstate"]
        text = get_immoscout_notification_text(apartment)

        # If you are interested only in public companies uncomment the next 2 line.
        # is_public = False

        # if 'realtorCompanyName' in apartment:
        #     company = apartment['realtorCompanyName'].upper()
        #     for c in public_companies:
        #         if company.find(c) != -1:
        #             is_public = True

        # if is_public:
        # push_notification(data)

        # If you are interested only in public companies comment out the next line.
        db.insert_to_database({"hash": apartment["@id"]}, collection_name=immo_collection_name)
        push_notification(bot, chat_id, text)


def get_immoscout_notification_text(apartment):
    """
    """
    title = re.sub("[^a-zA-Z0-9.\d\s]+", "", apartment["title"])
    address = re.sub(
        "[^a-zA-Z0-9.\d\s]+", "", apartment["address"]["description"]["text"]
    )
    size = apartment["livingSpace"]
    price_warm = "NONE"
    try:
        price_warm = apartment["calculatedPrice"]["value"]
    except Exception as e:
        try:
            price_warm = apartment["calculatedTotalRent"]["totalRent"]["value"]
        except Exception as e:
            logger.info(f"Error with Apartment: {str(apartment)} ")

    text = f"Apartment: {title} - Address: {address} - Size:{size} m2 - Price (warm): {price_warm} EUR -  - [https://www.immobilienscout24.de/expose/{apartment['@id']}](https://www.immobilienscout24.de/expose/{apartment['@id']})"
    return text
