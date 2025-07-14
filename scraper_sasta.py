from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("scraper_sasta")


class SastaTicketScraper:
    def __init__(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.wait = WebDriverWait(self.driver, 30)

    def close(self):
        self.driver.quit()
        logger.info("🔒 Scraper closed")

    def search_flights(self, origin, destination, date_mmddyyyy):
        try:
            logger.info("🚀 Chrome launched (non-headless)")
            self.driver.get("https://www.sastaticket.pk/")
            time.sleep(3)

            # From input
            from_input = self.wait.until(EC.element_to_be_clickable((By.ID, "rc_select_0")))
            self.driver.execute_script("arguments[0].click();", from_input)
            from_input.send_keys(origin)
            time.sleep(1)
            from_input.send_keys(Keys.ARROW_DOWN + Keys.ENTER)

            # To input
            to_input = self.wait.until(EC.element_to_be_clickable((By.ID, "rc_select_1")))
            self.driver.execute_script("arguments[0].click();", to_input)
            to_input.send_keys(destination)
            time.sleep(1)
            to_input.send_keys(Keys.ARROW_DOWN + Keys.ENTER)

            # Date
            date_obj = datetime.strptime(date_mmddyyyy, "%m/%d/%Y")
            date_for_data_test = date_obj.strftime("search-fields-date-picker-depart-%a %b %d %Y")

            date_input = self.wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "input[data-test='search-fields-date-picker-departing']")))
            self.driver.execute_script("arguments[0].click();", date_input)
            time.sleep(2)

            day_button = self.wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, f"div[data-test='{date_for_data_test}']")))
            self.driver.execute_script("arguments[0].click();", day_button)
            time.sleep(1)

            # Click Search Flights button
            search_btn = self.wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "button[data-test='search-fields-search-button']")))
            self.driver.execute_script("arguments[0].scrollIntoView(true);", search_btn)
            time.sleep(1)
            self.driver.execute_script("arguments[0].click();", search_btn)
            logger.info("✅ Search Flights button clicked.")

            # Wait for flights
            logger.info("🔍 Waiting for flights...")
            self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div[data-test='search-flight-card-container']")))
            time.sleep(2)

            # SCROLL TO LOAD MORE FLIGHTS
            flights_seen = set()
            results = []
            scroll_pause_time = 2
            screen_height = self.driver.execute_script("return window.innerHeight;")
            scroll_position = 0

            while len(flights_seen) < 5:
                self.driver.execute_script(f"window.scrollTo(0, {scroll_position + screen_height});")
                time.sleep(scroll_pause_time)
                scroll_position += screen_height

                flights = self.driver.find_elements(By.CSS_SELECTOR, "div[data-test='search-flight-card-container']")
                for flight in flights:
                    try:
                        airline = flight.find_element(By.CSS_SELECTOR, "span.text-sm.font-secondary").text.strip()
                        dep_time = flight.find_element(By.CSS_SELECTOR, "span[data-test='search-flight-card-start-time']").text.strip()
                        arr_time = flight.find_element(By.CSS_SELECTOR, "span[data-test='search-flight-card-end-time']").text.strip()
                        stops = flight.find_element(By.CSS_SELECTOR, "span[data-test='search-flight-card-stop-text']").text.strip()
                        price = flight.find_element(By.CSS_SELECTOR, "button[data-test='search-flight-card-price-button-main']").text.strip()

                        flight_id = f"{airline}-{dep_time}-{arr_time}-{price}"
                        if flight_id not in flights_seen:
                            flights_seen.add(flight_id)
                            results.append({
                                "airline": airline,
                                "departure": dep_time,
                                "arrival": arr_time,
                                "stops": stops,
                                "price": price
                            })
                    except Exception as fe:
                        continue

                if scroll_position > 4000:  # Avoid scrolling too much
                    break

            logger.info(f"✅ {len(results)} flights scraped")
            return results

        except Exception as e:
            logger.error(f"❌ Scraping error: {e}")
            return []

        finally:
            self.close()


# ✈️ Example usage
if __name__ == "__main__":
    logger.info("SastaTicket Scraper Started")
    logger.info("📍 LHE → ISB")
    logger.info("📅 Date: 07/15/2025")

    scraper = SastaTicketScraper()
    flights = scraper.search_flights("LHE", "ISB", "07/15/2025")

    if not flights:
        logger.info("❌ No flights found.")
    else:
        logger.info("✅ Flights found:")
        for idx, f in enumerate(flights, 1):
            logger.info(f"{idx}. ✈️ {f['airline']} | 🕔 {f['departure']} → {f['arrival']} | 🛑 {f['stops']} | 💰 {f['price']}")
