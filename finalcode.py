import os
import time
import random
import requests
import logging
import shutil
import hashlib
import re
import datetime
from datetime import datetime
from urllib.parse import urljoin, parse_qs, urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    StaleElementReferenceException, 
    NoSuchElementException, 
    TimeoutException,
    ElementClickInterceptedException
)

class NSEReportsDownloader:
    """NSE Reports Downloader Class"""
    
    def __init__(self, download_folder=None, chromedriver_path=None):
        # Check if paths are provided
        if download_folder is None or chromedriver_path is None:
            raise ValueError("Both download_folder and chromedriver_path must be provided")
        self.enable_email_notifications = False
        self.recipient_email = None
        # Constants
        self.PAGE_URL = "https://www.nseindia.com/all-reports"
        self.BASE_URL = "https://www.nseindia.com"
        self.DOWNLOAD_FOLDER = download_folder
        self.CHROMEDRIVER_PATH = chromedriver_path
        
        # Create logs directory
        self.LOGS_FOLDER = os.path.join(download_folder, 'logs')
        os.makedirs(self.LOGS_FOLDER, exist_ok=True)
        
        # Setup logging with both file and console handlers
        self.logger = logging.getLogger('NSEDownloader')
        self.logger.setLevel(logging.INFO)

        # Create file handler
        log_file = os.path.join(self.LOGS_FOLDER, f'nse_downloads_{datetime.now().strftime("%Y%m%d")}.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)

        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Create formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add the handlers to the logger
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

        # Get today's date in various formats used by NSE
        today = datetime.now()
        self.TODAY_DATE = today.strftime('%d%m%Y')  # DDMMYYYY
        self.TODAY_DATE_ALT = today.strftime('%d-%m-%Y')  # DD-MM-YYYY
        self.TODAY_DATE_SHORT = today.strftime('%d%b%Y').upper()  # DDMMMYYYY
        self.DATE_FOLDER_FORMAT = today.strftime('%Y-%m-%d')  # YYYY-MM-DD for folder names
        
        # File patterns to specifically look for
        self.FILE_PATTERNS = [
            "C_VAR1_", "APS_CL","APPSEC", "MF_VAR", "series_change", "shortselling",
            "price_band", "BhavCopy", "MA", "AUB", "cat_turnover", "CMVOLT", "C_STT",
            "eq_band_changes", "top10nifty50", "SLB_ELG_SEC","CM", "series"
        ]
        
        # Specific report patterns that need special handling
        self.REPORT_PATTERNS = {
            'series_change': {
                'button_text': ['Series', 'Change', 'Report'],
                'url_pattern': 'series_change',
                'section_id': 'cr_equity_daily_Current'
            },
            'shortselling': {
                'button_text': ['Short', 'Selling'],
                'url_pattern': 'shortselling',
                'section_id': 'cr_equity_daily_Current'
            }
        }
        
        # Specific sections to check
        self.SPECIFIC_SECTIONS = [
            '//*[@id="cr_equity_daily_Current"]/div/div[1]',
            '//div[contains(@class, "reportsDownload")]',
            '//div[contains(@class, "row col-12")]',
            '//div[contains(@class, "col-lg-4 col-md-4 col-sm-6 my-2")]',
            '//div[contains(@class, "tab-pane")]',
            '//div[contains(@class, "reportSelection")]',
            '//div[contains(@id, "equityArchives")]'
        ]
        
        # File categories
        self.FILE_TYPES = {
            "csv": ["csv"],
            "pdf": ["pdf"],
            "xls": ["xls", "xlsx"],
            "zip": ["zip"],
            "dat": ["dat"],
            "dbf": ["dbf"],
            "txt": ["txt"],
            "doc": ["doc", "docx"]
        }
        
        # Create download directory structure
        self.setup_directories()

    def setup_directories(self):
        """Create necessary directories for downloads and organization"""
        os.makedirs(self.DOWNLOAD_FOLDER, exist_ok=True)
        # Create category folders with date subfolders
        for folder in self.FILE_TYPES.keys():
            date_folder = os.path.join(self.DOWNLOAD_FOLDER, folder, self.DATE_FOLDER_FORMAT)
            os.makedirs(date_folder, exist_ok=True)

    def get_file_hash(self, file_path):
        """Calculate MD5 hash of a file"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def handle_duplicate_file(self, file_path):
        """Handle duplicate files by comparing content and timestamps"""
        if not os.path.exists(file_path):
            return False
            
        try:
            os.remove(file_path)
            self.logger.info(f"Deleted duplicate file: {os.path.basename(file_path)}")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting duplicate file: {str(e)}")
            return False

    def setup_driver(self):
        """Configure and return ChromeDriver instance with enhanced options"""
        options = Options()
        prefs = {
            "download.default_directory": os.path.abspath(self.DOWNLOAD_FOLDER),
            "download.prompt_for_download": False,
            "safebrowsing.enabled": True,
            "profile.default_content_settings.popups": 0,
            "plugins.always_open_pdf_externally": True,
            "download.extensions_to_open": "doc,docx",
            "download.default_mime_handlers": {
                "application/msword": {"action": 1},
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document": {"action": 1}
            }
        }
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--use-gl=swiftshader")
        options.add_argument("--headless=new")
        options.add_experimental_option("prefs", prefs)
        options.add_argument("--disable-extensions")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        service = Service(self.CHROMEDRIVER_PATH)
        return webdriver.Chrome(service=service, options=options)

    def wait_for_page_load(self, driver):
        """Enhanced page load waiting mechanism"""
        try:
            wait = WebDriverWait(driver, 30)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "container-fluid")))
            
            spinners = driver.find_elements(By.CLASS_NAME, "loading-spinner")
            if spinners:
                wait.until(EC.invisibility_of_elements_located((By.CLASS_NAME, "loading-spinner")))
            
            time.sleep(5)
            
        except Exception as e:
            self.logger.error(f"Error waiting for page load: {str(e)}")

    def interact_with_dynamic_elements(self, driver):
        """Handle dynamic elements that might need interaction"""
        try:
            current_elements = driver.find_elements(By.XPATH, 
                "//button[contains(text(), 'Current') or contains(text(), 'Today')]")
            for elem in current_elements:
                try:
                    driver.execute_script("arguments[0].click();", elem)
                    time.sleep(2)
                except:
                    continue

            expand_elements = driver.find_elements(By.XPATH, 
                "//button[contains(@class, 'collapse') or contains(@data-toggle, 'collapse')]")
            for elem in expand_elements:
                try:
                    driver.execute_script("arguments[0].click();", elem)
                    time.sleep(1)
                except:
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error interacting with dynamic elements: {str(e)}")

    def is_today_report(self, url):
        """Check if the URL corresponds to today's report"""
        if not url:
            return False
            
        url_lower = url.lower()
        
        if any(date in url_lower for date in [
            self.TODAY_DATE.lower(),
            self.TODAY_DATE_ALT.lower(),
            self.TODAY_DATE_SHORT.lower()
        ]):
            return True
            
        try:
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            
            for param_values in query_params.values():
                for value in param_values:
                    if any(date.lower() in value.lower() for date in [
                        self.TODAY_DATE,
                        self.TODAY_DATE_ALT,
                        self.TODAY_DATE_SHORT
                    ]):
                        return True
        except:
            pass
        
        return False

    def _extract_section_links(self, section, all_links):
        """Helper method to extract links from a section"""
        try:
            links = section.find_elements(By.TAG_NAME, "a")
            for link in links:
                try:
                    href = link.get_attribute("href")
                    data_link = link.get_attribute("data-link")
                    
                    if href and self.is_today_report(href):
                        all_links.add(href)
                    if data_link and self.is_today_report(data_link):
                        all_links.add(data_link)
                except:
                    continue

            buttons = section.find_elements(By.TAG_NAME, "button")
            for button in buttons:
                try:
                    if any(text.lower() in button.text.lower() for text in ['download', 'get', 'report']):
                        data_link = button.get_attribute("data-link")
                        onclick = button.get_attribute("onclick")
                        
                        if data_link and self.is_today_report(data_link):
                            all_links.add(data_link)
                        if onclick and 'download' in onclick.lower():
                            url_match = re.search(r"['\"](https?://[^'\"]+)['\"]", onclick)
                            if url_match and self.is_today_report(url_match.group(1)):
                                all_links.add(url_match.group(1))
                except:
                    continue
        except Exception as e:
            self.logger.debug(f"Error extracting section links: {str(e)}")

    def _handle_specific_report(self, driver, pattern, all_links):
        """Handle specific report types that need special interaction"""
        try:
            sections = driver.find_elements(By.ID, pattern['section_id'])
            for section in sections:
                try:
                    elements = section.find_elements(By.XPATH, 
                        f".//*[{' or '.join(f"contains(text(), '{text}')" for text in pattern['button_text'])}]")
                    
                    for elem in elements:
                        try:
                            driver.execute_script("arguments[0].scrollIntoView(true);", elem)
                            time.sleep(1)
                            elem.click()
                            time.sleep(2)
                            
                            download_elements = section.find_elements(By.XPATH, 
                                f".//*[contains(@href, '{pattern['url_pattern']}') or contains(@data-link, '{pattern['url_pattern']}')]")
                            
                            for download_elem in download_elements:
                                href = download_elem.get_attribute("href")
                                data_link = download_elem.get_attribute("data-link")
                                
                                if href and self.is_today_report(href):
                                    all_links.add(href)
                                if data_link and self.is_today_report(data_link):
                                    all_links.add(data_link)
                                    
                        except Exception as e:
                            self.logger.debug(f"Error interacting with element: {str(e)}")
                            continue
                            
                except Exception as e:
                    self.logger.debug(f"Error processing section: {str(e)}")
                    continue
                    
        except Exception as e:
            self.logger.debug(f"Error handling specific report pattern: {str(e)}")

    def extract_links(self, driver):
        """Extract today's download links from the page"""
        all_links = set()
        wait = WebDriverWait(driver, 10)
        
        for xpath in self.SPECIFIC_SECTIONS:
            try:
                sections = wait.until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
                for section in sections:
                    try:
                        if 'collapse' in section.get_attribute('class', ''):
                            driver.execute_script("arguments[0].classList.remove('collapse')", section)
                            time.sleep(1)
                        
                        self._extract_section_links(section, all_links)
                    except Exception as e:
                        self.logger.debug(f"Error processing section: {str(e)}")
                        continue
            except Exception as e:
                self.logger.debug(f"Error with xpath {xpath}: {str(e)}")

        for report_type, pattern in self.REPORT_PATTERNS.items():
            try:
                self._handle_specific_report(driver, pattern, all_links)
            except Exception as e:
                self.logger.debug(f"Error handling {report_type}: {str(e)}")

        for pattern in self.FILE_PATTERNS:
            try:
                elements = driver.find_elements(By.XPATH, 
                    f"//*[contains(@href, '{pattern}') or contains(@data-link, '{pattern}')]")
                for elem in elements:
                    href = elem.get_attribute("href")
                    data_link = elem.get_attribute("data-link")
                    
                    if href and self.is_today_report(href):
                        all_links.add(href)
                    if data_link and self.is_today_report(data_link):
                        all_links.add(data_link)
            except Exception as e:
                self.logger.debug(f"Error with pattern {pattern}: {str(e)}")

        try:
            doc_elements = driver.find_elements(By.XPATH, 
                "//*[contains(@href, '.doc') or contains(@data-link, '.doc')]")
            for elem in doc_elements:
                href = elem.get_attribute("href")
                data_link = elem.get_attribute("data-link")
                
                if href:
                    all_links.add(href)
                if data_link:
                    all_links.add(data_link)
        except Exception as e:
            self.logger.debug(f"Error searching for document files: {str(e)}")

        self.logger.info(f"Total unique links found: {len(all_links)}")
        return all_links

    def download_file(self, url, session, cookies, max_retries=3):
        """Download a single file with enhanced retry mechanism"""
        filename = url.split('/')[-1]
        file_path = os.path.join(self.DOWNLOAD_FOLDER, filename)
        
        if os.path.exists(file_path):
            self.handle_duplicate_file(file_path)
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.nseindia.com/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache'
        }
        
        if url.lower().endswith(('.doc', '.docx')):
            headers.update({
                'Accept': 'application/msword, application/vnd.openxmlformats-officedocument.wordprocessingml.document, */*'
            })
        
        if 'series_change' in url.lower():
            headers.update({
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json, text/javascript, */*; q=0.01'
            })
        
        for attempt in range(max_retries):
            try:
                urls_to_try = [
                    url,
                    url.replace('nsearchives.nseindia.com', 'archives.nseindia.com'),
                    url.replace('archives.nseindia.com', 'nsearchives.nseindia.com')
                ]
                
                for try_url in urls_to_try:
                    try:
                        response = session.get(try_url, headers=headers, cookies=cookies, stream=True, timeout=60)
                        
                        if response.status_code == 200:
                            content_disposition = response.headers.get('Content-Disposition')
                            if content_disposition:
                                try:
                                    filename_match = re.search(r'filename=["\'](.*)["\']', content_disposition)
                                    if filename_match:
                                        filename = filename_match.group(1)
                                        file_path = os.path.join(self.DOWNLOAD_FOLDER, filename)
                                except:
                                    pass
                            
                            with open(file_path, 'wb') as f:
                                for chunk in response.iter_content(chunk_size=8192):
                                    if chunk:
                                        f.write(chunk)
                            self.logger.info(f"Successfully downloaded {filename}")
                            return True
                    except requests.exceptions.RequestException as e:
                        self.logger.debug(f"Error trying URL {try_url}: {str(e)}")
                        continue
                
                self.logger.warning(f"Download attempt {attempt + 1} failed for {filename}")
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(2, 5))
                    
            except Exception as e:
                self.logger.error(f"Error downloading {filename} (Attempt {attempt + 1}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(2, 5))
                continue
        
        return False

    def organize_files(self):
        """Organize downloaded files into type-specific folders with date subfolders"""
        self.logger.info("Organizing downloaded files into date-wise folders...")
        
        for file in os.listdir(self.DOWNLOAD_FOLDER):
            file_path = os.path.join(self.DOWNLOAD_FOLDER, file)
            
            if os.path.isfile(file_path):
                file_ext = file.split(".")[-1].lower()
                
                for folder, extensions in self.FILE_TYPES.items():
                    if file_ext in extensions:
                        date_folder = os.path.join(self.DOWNLOAD_FOLDER, folder, self.DATE_FOLDER_FORMAT)
                        new_path = os.path.join(date_folder, file)
                        
                        if os.path.exists(new_path):
                            self.handle_duplicate_file(new_path)
                        
                        try:
                            shutil.move(file_path, new_path)
                            self.logger.info(f"Moved {file} to {folder}/{self.DATE_FOLDER_FORMAT}/")
                        except Exception as e:
                            self.logger.error(f"Error moving file {file}: {str(e)}")
                        break

    def validate_downloaded_files(self):
        """Validate all downloaded files"""
        self.logger.info("Starting file validation process...")
        validation_results = {
            'total_files': 0,
            'valid_files': 0,
            'invalid_files': [],
            'missing_files': [],
            'corrupt_files': []
        }

        MIN_FILE_SIZE = 100

        try:
            for folder_name, extensions in self.FILE_TYPES.items():
                folder_path = os.path.join(self.DOWNLOAD_FOLDER, folder_name)
                date_folder_path = os.path.join(folder_path, self.DATE_FOLDER_FORMAT)
                
                if not os.path.exists(date_folder_path):
                    self.logger.warning(f"Date directory not found: {date_folder_path}")
                    continue

                for filename in os.listdir(date_folder_path):
                    file_path = os.path.join(date_folder_path, filename)
                    validation_results['total_files'] += 1

                    try:
                        if not os.path.exists(file_path):
                            validation_results['missing_files'].append(filename)
                            self.logger.error(f"File missing: {filename}")
                            continue

                        file_size = os.path.getsize(file_path)
                        if file_size < MIN_FILE_SIZE:
                            validation_results['invalid_files'].append(f"{filename} (Size: {file_size} bytes)")
                            self.logger.warning(f"File too small: {filename} ({file_size} bytes)")
                            continue

                        file_ext = filename.split('.')[-1].lower()
                        if file_ext not in extensions:
                            validation_results['invalid_files'].append(f"{filename} (Invalid extension)")
                            self.logger.warning(f"Invalid file extension: {filename}")
                            continue

                        try:
                            if file_ext in ['csv', 'txt']:
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    first_line = f.readline()
                                    if not first_line:
                                        raise ValueError("Empty file")

                            elif file_ext in ['pdf', 'zip', 'xls', 'xlsx', 'doc', 'docx']:
                                with open(file_path, 'rb') as f:
                                    magic_numbers = {
                                        'pdf': b'%PDF',
                                        'zip': b'PK\x03\x04',
                                        'xls': b'\xD0\xCF\x11\xE0',
                                        'xlsx': b'PK\x03\x04',
                                        'doc': b'\xD0\xCF\x11\xE0',
                                        'docx': b'PK\x03\x04'
                                    }
                                    file_start = f.read(4)
                                    
                                    if file_ext in magic_numbers:
                                        expected_magic = magic_numbers[file_ext]
                                        if not file_start.startswith(expected_magic):
                                            if file_ext in ['doc', 'docx', 'xls', 'xlsx']:
                                                if not (file_start.startswith(b'\xD0\xCF\x11\xE0') or 
                                                        file_start.startswith(b'PK\x03\x04')):
                                                    raise ValueError(f"Invalid {file_ext} file format")
                                            else:
                                                raise ValueError(f"Invalid {file_ext} file format")

                            validation_results['valid_files'] += 1
                            self.logger.info(f"File validated successfully: {filename}")

                        except Exception as e:
                            validation_results['corrupt_files'].append(filename)
                            self.logger.error(f"File corruption detected in {filename}: {str(e)}")

                    except Exception as e:
                        self.logger.error(f"Error validating {filename}: {str(e)}")
                        validation_results['invalid_files'].append(filename)

            self.logger.info("\nValidation Summary:")
            self.logger.info(f"Total files processed: {validation_results['total_files']}")
            self.logger.info(f"Valid files: {validation_results['valid_files']}")
            self.logger.info(f"Invalid files: {len(validation_results['invalid_files'])}")
            self.logger.info(f"Missing files: {len(validation_results['missing_files'])}")
            self.logger.info(f"Corrupt files: {len(validation_results['corrupt_files'])}")

            if validation_results['invalid_files']:
                self.logger.warning("Invalid files:")
                for file in validation_results['invalid_files']:
                    self.logger.warning(f"- {file}")

            if validation_results['corrupt_files']:
                self.logger.warning("Corrupt files:")
                for file in validation_results['corrupt_files']:
                    self.logger.warning(f"- {file}")

            if validation_results['missing_files']:
                self.logger.warning("Missing files:")
                for file in validation_results['missing_files']:
                    self.logger.warning(f"- {file}")

            return validation_results

        except Exception as e:
            self.logger.error(f"Error during validation process: {str(e)}")
            return validation_results
        
    def download_reports(self):
        """Main method to download and organize today's NSE reports"""
        driver = None
        session = requests.Session()
        successful_downloads = 0
        
        try:
            self.logger.info(f"Starting download process for reports dated {self.TODAY_DATE_ALT}...")
            
            driver = self.setup_driver()
            driver.get(self.PAGE_URL)
            
            self.wait_for_page_load(driver)
            self.interact_with_dynamic_elements(driver)
            
            cookies = {cookie['name']: cookie['value'] for cookie in driver.get_cookies()}
            download_links = self.extract_links(driver)
            
            if not download_links:
                self.logger.warning("No downloadable links found for today's reports!")
                return
            
            self.logger.info(f"Found {len(download_links)} files to download for today")
            
            for link in download_links:
                if link and isinstance(link, str):
                    if self.download_file(link, session, cookies):
                        successful_downloads += 1
            
            self.organize_files()
            validation_results = self.validate_downloaded_files()
            
            self.logger.info(f"Download process completed. Successfully downloaded {successful_downloads} out of {len(download_links)} files.")
            self.logger.info(f"Valid files after validation: {validation_results['valid_files']}")
            
            if self.enable_email_notifications and self.recipient_email:
                email_subject = f"NSE Reports Download Summary - {self.TODAY_DATE_ALT}"
                email_message = (
                    f"Download Summary for {self.TODAY_DATE_ALT}:\n"
                    f"Total files attempted: {len(download_links)}\n"
                    f"Successful downloads: {successful_downloads}\n"
                    f"Valid files: {validation_results['valid_files']}\n"
                    f"Invalid files: {len(validation_results['invalid_files'])}\n"
                    f"Corrupt files: {len(validation_results['corrupt_files'])}"
                )
                
                
        except Exception as e:
            self.logger.error(f"Error during download process: {str(e)}")
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass

if __name__ == "__main__":
    DOWNLOAD_FOLDER = r"C:\Users\sande\OneDrive\Desktop\scrapper\Scheduled_Downloads"
    CHROMEDRIVER_PATH = r"C:\Users\sande\OneDrive\Desktop\scrapper\chromedriver.exe"
    
    downloader = NSEReportsDownloader(
        download_folder=DOWNLOAD_FOLDER,
        chromedriver_path=CHROMEDRIVER_PATH
    )
    downloader.download_reports()