from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("scraper_bookme")


class BookmeScraper:
    def __init__(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.wait = WebDriverWait(self.driver, 30)

    def close(self):
        try:
            self.driver.quit()
            logger.info("🔒 Scraper closed")
        except:
            pass

    def type_airport_field(self, outer_id, inner_id, code):
        outer_input = self.wait.until(EC.element_to_be_clickable((By.ID, outer_id)))
        self.driver.execute_script("arguments[0].click();", outer_input)
        time.sleep(1)

        inner_input = self.wait.until(EC.visibility_of_element_located((By.ID, inner_id)))
        inner_input.clear()

        for char in code:
            inner_input.send_keys(char)
            time.sleep(0.2)

        time.sleep(2)
        inner_input.send_keys(Keys.ARROW_DOWN)
        time.sleep(1)
        inner_input.send_keys(Keys.ENTER)

    def pick_date(self, day: int, month: str, year: str):
        logger.info(f"📅 Selecting date: {day} {month} {year}")

        date_input = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[placeholder='Departure Date']")))
        self.driver.execute_script("arguments[0].click();", date_input)
        time.sleep(1)

        # Select month
        month_btn = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, f"//div[contains(@class,'dp__month_year_select') and text()='{month}']")))
        month_btn.click()
        time.sleep(1)
        month_option = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, f"//div[contains(@class,'dp__overlay_cell') and text()='{month}']")))
        month_option.click()
        time.sleep(1)

        # Select year
        year_btn = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, f"//div[contains(@class,'dp__month_year_select') and text()='{year}']")))
        year_btn.click()
        time.sleep(1)
        year_option = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, f"//div[contains(@class,'dp__overlay_cell') and text()='{year}']")))
        year_option.click()
        time.sleep(1)

        # Select day
        day_elem = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, f"//div[contains(@class,'day') and text()='{day}']")))
        day_elem.click()
        time.sleep(1)

    def search_flights(self, origin, destination, day, month, year):
        try:
            self.driver.get("https://bookme.pk/flights")
            logger.info("🚀 Navigated to Bookme")

            self.wait.until(EC.element_to_be_clickable((By.ID, "0"))).click()
            time.sleep(1)

            self.type_airport_field("from", "from0", origin)
            self.type_airport_field("to", "to0", destination)

            self.pick_date(day, month, year)

            
            search_btn = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit'].btn-primary")))
            self.driver.execute_script("arguments[0].click();", search_btn)
            logger.info("🔍 Search button clicked. Waiting for results...")

            # ✅ WAIT until at least 3 flight cards are found
            self.wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "div.flight-card")) >= 3)
            logger.info("✅ 3+ flight cards loaded.")
            time.sleep(2)  

            
            logger.info("🔄 Scrolling to load more flights...")
            flights_seen = set()
            results = []
            scroll_pause_time = 2
            screen_height = self.driver.execute_script("return window.innerHeight;")
            scroll_position = 0

            while len(flights_seen) < 5:
                self.driver.execute_script(f"window.scrollTo(0, {scroll_position + screen_height});")
                time.sleep(scroll_pause_time)
                scroll_position += screen_height

                flights = self.driver.find_elements(By.CSS_SELECTOR, "div.flight-card")
                for flight in flights:
                    try:
                        airline = flight.find_element(By.CSS_SELECTOR, ".airline-name").text.strip()
                        dep_time = flight.find_elements(By.CSS_SELECTOR, "h5.text-dark")[0].text.strip()
                        arr_time = flight.find_elements(By.CSS_SELECTOR, "h5.text-dark")[1].text.strip()
                        price = flight.find_element(By.CSS_SELECTOR, "h3.text-primary").text.strip()

                        flight_id = f"{airline}-{dep_time}-{arr_time}-{price}"
                        if flight_id not in flights_seen:
                            flights_seen.add(flight_id)
                            results.append({
                                "airline": airline,
                                "departure": dep_time,
                                "arrival": arr_time,
                                "price": price
                            })
                    except Exception:
                        continue

                if scroll_position > 4000:
                    break

            logger.info(f"✅ {len(results)} flights scraped")
            return results

        except Exception as e:
            logger.error(f"❌ Scraping error: {e}")
            return []

        finally:
            self.close()


# ✈️ Run Example
if __name__ == "__main__":
    logger.info("📍 Bookme Flight Scraper Started")
    logger.info("🛫 From: LHE → 🛬 To: KHI | 📅 Date: 15 Jul 2025")

    scraper = BookmeScraper()
    flights = scraper.search_flights("LHE", "KHI", day=15, month="Jul", year="2025")

    if not flights:
        logger.info("❌ No flights found.")
    else:
        logger.info("✅ Flights found:")
        for idx, f in enumerate(flights, 1):
            logger.info(f"{idx}. ✈️ {f['airline']} | 🕔 {f['departure']} → {f['arrival']} | 💰 {f['price']}")
