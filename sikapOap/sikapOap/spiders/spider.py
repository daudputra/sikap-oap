
import json
import os
import scrapy
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException

class SikapOapSpider(scrapy.Spider):
    name = 'spider'
    allowed_domains = ['sikap-oap.papua.go.id']
    start_urls = ['https://sikap-oap.papua.go.id/perusahaan']

    def __init__(self):
        super(SikapOapSpider, self).__init__()
        self.error_links = []
        options = webdriver.ChromeOptions()
        # options.add_argument('--headless')  
        options.add_argument('--disable-gpu') 
        # options.add_argument('--window-size=1920,1080') 
        options.add_argument('--no-sandbox')  
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-popup-blocking')
        # options.add_argument('--start-maximized')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-notifications')

        service = ChromeService(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)

    def save_json(self, data, filename):
        with open(filename, 'w') as f:
            json.dump(data, f)


    def parse(self, response):
        self.driver.get(response.url)
        error_logs = []


        with open('list-links.txt', 'r') as file:
            detail_links = [line.strip() for line in file.readlines()]

        main_tab = self.driver.current_window_handle


        for link in detail_links:
            try:
                self.driver.execute_script(f"window.open('{link}', 'new_window')")
                    

                if main_tab is None:
                    main_tab = self.driver.current_window_handle


                if '404' in self.driver.title.lower():
                    self.logger.warning(f"Link rusak: {link}")
                    self.error_links.append(link)

                time.sleep(2) 
                for handle in self.driver.window_handles:
                    if handle != main_tab:
                        self.driver.switch_to.window(handle)
                        break

                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="panel"]/div[1]/section[2]/div/div/div/div[1]/div/div/div[2]/table/tbody'))
                )

                company_data = {}

                table_info = self.driver.find_elements(By.XPATH, '//*[@id="panel"]/div[1]/section[2]/div/div/div/div[1]/div/div/div[2]/table/tbody')
                for table in table_info:
                    company_name = table.find_element(By.XPATH, './tr[1]/td[3]/span').text
                    nomor_telepon = table.find_element(By.XPATH, './tr[2]/td[3]/span').text
                    email = table.find_element(By.XPATH, './tr[3]/td[3]/span').text
                    bidang = table.find_element(By.XPATH, './tr[4]/td[3]/span').text
                    alamat1 = table.find_element(By.XPATH, './tr[5]/td[3]/span').text
                    alamat2 = table.find_element(By.XPATH, './tr[6]/td[3]/span').text
                    alamat = ' '.join([alamat1, alamat2])
                    modal_dasar = table.find_element(By.XPATH, './tr[7]/td[3]/span').text
                    modal_ditempatkan = table.find_element(By.XPATH, './tr[7]/td[3]/span').text

                owner_data = []
                owner_rows = self.driver.find_elements(By.XPATH, '//*[@id="owner"]/tbody/tr')
                for row in owner_rows:
                    test_nama_pemilik = row.find_element(By.XPATH, './/td[1]').text
                    if test_nama_pemilik == 'No data available in table':
                        nama_pemilik = None
                        presentase = None
                        status = None
                        oap = None
                    else:
                        nama_pemilik = row.find_element(By.XPATH, './/td[1]/a').text if row.find_element(By.XPATH, './/td[1]/a') else None
                        presentase = row.find_element(By.XPATH, './/td/div/span').text if row.find_element(By.XPATH, './/td/div/span') else None
                        status = row.find_element(By.XPATH, './/td[3]/span').text if row.find_element(By.XPATH, './/td[3]/span') else None
                        oap = row.find_element(By.XPATH, './/td[4]/span').text if row.find_element(By.XPATH, './/td[4]/span') else None

                    owner_data.append({
                        'nama_pemilik': nama_pemilik,
                        'presentase': presentase,
                        'status': status,
                        'oap': oap
                    })

                company_data['daftar_pemilik'] = owner_data

                pengurus_data = []
                pengurus_rows = self.driver.find_elements(By.XPATH, '//*[@id="admin"]/tbody/tr')
                for row in pengurus_rows:
                    nama_pengurus = row.find_element(By.XPATH, './/td').text
                    if nama_pengurus == 'No data available in table':
                        nama_pengurus = None
                        jabatan = None
                        tanggal_menjabat = None
                        status_pengurus = None
                        oap_pengurus = None
                    else:
                        nama_pengurus = row.find_element(By.XPATH, './/td[1]/a').text if row.find_element(By.XPATH, './/td[1]/a') else None
                        jabatan = row.find_element(By.XPATH, './/td[2]').text if row.find_element(By.XPATH, './/td[2]') else None
                        tanggal_menjabat = row.find_element(By.XPATH, './/td[3]').text if row.find_element(By.XPATH, './/td[3]') else None
                        status_pengurus = row.find_element(By.XPATH, './/td[4]/span').text if row.find_element(By.XPATH, './/td[4]/span') else None
                        oap_pengurus = row.find_element(By.XPATH, './/td[5]/span').text if row.find_element(By.XPATH, './/td[5]/span') else None

                    pengurus_data.append({
                        'nama_pengurus': nama_pengurus,
                        'jabatan': jabatan,
                        'tanggal_menjabat': tanggal_menjabat,
                        'status': status_pengurus,
                        'oap': oap_pengurus
                    })

                company_data['daftar_pengurus'] = pengurus_data

                pengalaman_data = []
                pengalaman_rows = self.driver.find_elements(By.XPATH, '//*[@id="pengalaman"]/tbody/tr')
                for row in pengalaman_rows:
                    nama_pekerjaan = row.find_element(By.XPATH, './/td[1]').text if row.find_element(By.XPATH, './/td[1]') else None
                    if nama_pekerjaan == 'No data available in table':
                        nama_pekerjaan = None
                        nilai_pekerjaan = None
                        tanggal = None
                        lokasi = None
                    else:
                        nama_pekerjaan = row.find_element(By.XPATH, './/td[1]').text if row.find_element(By.XPATH, './/td[1]') else None
                        nilai_pekerjaan = row.find_element(By.XPATH, './/td[2]').text if row.find_element(By.XPATH, './/td[2]') else None
                        tanggal = row.find_element(By.XPATH, './/td[3]').text if row.find_element(By.XPATH, './/td[3]') else None
                        lokasi = row.find_element(By.XPATH, './/td[4]').text if row.find_element(By.XPATH, './/td[4]') else None

                    pengalaman_data.append({
                        'nama_pekerjaan': nama_pekerjaan,
                        'nilai_pekerjaan': nilai_pekerjaan,
                        'tanggal': tanggal,
                        'lokasi': lokasi
                    })
                company_data['data_pengalaman'] = pengalaman_data




                path_raw = 'data'
                dir_raw = os.path.join(path_raw)
                os.makedirs(dir_raw, exist_ok=True)
                filename = f'{company_name.replace(" ", "_").replace('.','_').replace('__', '_').lower()}.json'
                s3_file_path = f's3://ai-pipeline-statistics/data/data_raw/sikap-oap.papua/Data Perusahaan di Papua/json/{filename}'
                data = {
                    'link' : 'https://sikap-oap.papua.go.id/perusahaan',
                    'domain' : 'https://sikap-oap.papua.go.id',
                    'tag' : [
                        'https://sikap-oap.papua.go.id/perusahaan',
                        'perusahaan',
                        company_name
                        ],
                    'crawling_time' : datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'crawling_time_epoch' : int(datetime.now().timestamp()),
                    'path_data_raw' : s3_file_path,
                    'path_data_clean' : None,
                    'company_name': company_name,
                    'bidang': bidang,
                    'alamat': alamat,
                    'informasi_perusahaan': {
                        'nama_perusahaan': company_name,
                        'no_telp_perusahaan': nomor_telepon,
                        'email_perusahaan': email,
                        'kualifikasi_bidang_perusahaan': bidang,
                        'alamat': alamat,
                        'modal_dasar': modal_dasar,
                        'modal_ditempatkan': modal_ditempatkan
                    },
                    'daftar_pemilik': owner_data,
                    'daftar_pengurus': pengurus_data,
                    'data_pengalaman' : pengalaman_data
                }
                self.save_json(data, os.path.join(dir_raw, filename))

            except TimeoutException:
                error_logs.append({
                    'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "link": link,
                    "error_type": "TimeoutException",
                    "error_message": str(e)
                })
                self.save_json(error_logs, 'error_logs.json')
                self.logger.error(f"Timeout saat mengakses {link}. Melakukan retry.")
                continue
            except Exception as e:
                error_logs.append({
                    'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "link": link,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                })
                self.save_json(error_logs, 'error_logs.json')
                self.logger.error(f"Terjadi kesalahan saat mengakses {link}: {e}")
                continue


    def closed(self, reason):
        self.driver.quit()
        error_data = {'error_links': self.error_links}
        self.save_json(error_data, 'error_links.json')
