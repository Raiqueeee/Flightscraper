from scraper_sasta import SastaTicketScraper
from scraper_bookme import BookmeScraper
import logging
import re
import time
import csv
import pandas as pd
from datetime import datetime
import smtplib
from email.message import EmailMessage
import os

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("main")


def extract_numeric_price(price_text):
    if not price_text:
        return 0
    price_clean = re.sub(r'[^\d]', '', price_text)
    return int(price_clean) if price_clean.isdigit() else 0


def save_to_csv(flights, filename="flight_comparison.csv"):
    if not flights:
        print("⚠️ No flight data to save.")
        return
    headers = ["source", "airline", "departure", "arrival", "stops", "price", "numeric_price"]
    with open(filename, mode="w", newline='', encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        for flight in flights:
            writer.writerow(flight)
    print(f"✅ CSV file saved at: {filename}")


def save_to_excel(flights, filename="flight_comparison.xlsx"):
    if not flights:
        print("⚠️ No flight data to save.")
        return
    df = pd.DataFrame(flights)
    df.to_excel(filename, index=False)
    print(f"✅ Excel file saved at: {filename}")


def send_email_with_attachments(to_email, subject, body, file_paths, from_email, password):
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = to_email
        msg.set_content(body)

        for file_path in file_paths:
            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    file_data = f.read()
                    file_name = os.path.basename(file_path)
                    msg.add_attachment(file_data, maintype="application", subtype="octet-stream", filename=file_name)
            else:
                print(f"❌ File not found: {file_path}")

        with smtplib.SMTP("smtp.office365.com", 587) as smtp:
            smtp.starttls()
            smtp.login(from_email, password)
            smtp.send_message(msg)

        print("✅ Email sent successfully via Outlook!")

    except Exception as e:
        print(f"❌ Failed to send email: {e}")


def compare_prices(sasta_flights, bookme_flights):
    combined = []
    for flight in sasta_flights:
        flight["source"] = "SastaTicket"
        flight["numeric_price"] = extract_numeric_price(flight.get("price", ""))
        combined.append(flight)
    for flight in bookme_flights:
        flight["source"] = "Bookme"
        flight["stops"] = flight.get("stops", "N/A")
        flight["numeric_price"] = extract_numeric_price(flight.get("price", ""))
        combined.append(flight)
    combined.sort(key=lambda x: x["numeric_price"])
    return combined


def display_results(flights):
    if not flights:
        logger.warning("⚠️ No flights found from any source.")
        return

    logger.info("\n" + "=" * 90)
    logger.info("✅ FLIGHT COMPARISON RESULTS (Sorted by Price)")
    logger.info("=" * 90)

    for idx, flight in enumerate(flights, 1):
        source_icon = "🟢" if flight["source"] == "SastaTicket" else "🔵"
        logger.info(f"{idx:2d}. {source_icon} {flight['source']:12} | "
                    f"✈️ {flight['airline'][:25]:25} | "
                    f"🕔 {flight['departure']:8} → {flight['arrival']:8} | "
                    f"🛑 {flight.get('stops', 'N/A')[:12]:12} | "
                    f"💰 {flight['price']:>12}")

    logger.info("=" * 90)
    if flights:
        cheapest = flights[0]
        logger.info(f"💰 Cheapest flight: {cheapest['airline']} - {cheapest['price']} ({cheapest['source']})")



def main():
    origin = "LHE"
    destination = "KHI"
    date_mmddyyyy = "07/13/2025"

    logger.info("🚀 Starting Flight Price Comparison")
    logger.info(f"📍 Route: {origin} → {destination}")
    logger.info(f"📅 Date: {date_mmddyyyy}")
    logger.info("=" * 60)

    sasta_results = []
    bookme_results = []


    logger.info("🔍 Scraping SastaTicket.pk...")
    try:
        sasta = SastaTicketScraper()
        sasta_results = sasta.search_flights(origin, destination, date_mmddyyyy)
        logger.info(f"✅ Found {len(sasta_results)} flights on SastaTicket")
    except Exception as e:
        logger.error(f"❌ SastaTicket failed: {e}")

    time.sleep(2)

    
    logger.info("🔍 Scraping Bookme.pk...")
    try:
        day = int(date_mmddyyyy.split("/")[1])
        month = datetime.strptime(date_mmddyyyy, "%m/%d/%Y").strftime("%b")
        year = date_mmddyyyy.split("/")[-1]

        bookme = BookmeScraper()
        bookme_results = bookme.search_flights(origin, destination, day, month, year)
        logger.info(f"✅ Found {len(bookme_results)} flights on Bookme")
    except Exception as e:
        logger.error(f"❌ Bookme failed: {e}")

   
    logger.info("📊 Comparing flight prices...")
    all_flights = compare_prices(sasta_results, bookme_results)
    display_results(all_flights)

    if all_flights:
        prices = [f["numeric_price"] for f in all_flights if f["numeric_price"] > 0]
        if prices:
            logger.info(f"\n📈 Price range: PKR {min(prices):,} – PKR {max(prices):,}")
            logger.info(f"🎯 Cheapest: PKR {min(prices):,}")
        logger.info(f"🟢 SastaTicket: {len(sasta_results)} flights")
        logger.info(f"🔵 Bookme: {len(bookme_results)} flights")

        # Save and email files
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        excel_file = f"flight_comparison_{timestamp}.xlsx"
        save_to_excel(all_flights, excel_file)


    logger.info("✅ Flight comparison complete.\n")


if __name__ == "__main__":
    main()
