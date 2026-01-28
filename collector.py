from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
import time
import os
import json
from datetime import datetime, timedelta

class WeightsCollector:
    def __init__(self, max_time_minutes=30, scroll_delay=3, cookies=None):
        self.max_time_minutes = max_time_minutes
        self.scroll_delay = scroll_delay
        self.all_ids = set()
        self.start_time = None
        self.driver = None
        self.scroll_count = 0
        self.cookies = cookies
        
    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        service = Service('/usr/bin/chromedriver')
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def take_screenshot(self, name):
        try:
            os.makedirs('screenshots', exist_ok=True)
            filename = f'screenshots/{name}.png'
            self.driver.save_screenshot(filename)
            print(f"📸 {filename}")
        except Exception as e:
            pass
    
    def load_cookies(self):
        """Загрузить cookies для авторизации"""
        try:
            if not self.cookies:
                print("⚠️ Cookies не указаны")
                return False
            
            print(f"\n🍪 Загрузка cookies...")
            
            # Сначала открываем weights.com чтобы установить домен
            self.driver.get("https://www.weights.com")
            time.sleep(3)
            
            # Парсим cookies
            # Формат может быть: "key1=value1; key2=value2" или JSON
            cookies_list = []
            
            # Пробуем как обычную строку cookies
            if self.cookies.startswith('{'):
                # Это JSON
                try:
                    cookies_dict = json.loads(self.cookies)
                    # Конвертируем в формат Selenium
                    for key, value in cookies_dict.items():
                        cookies_list.append({
                            'name': key,
                            'value': value,
                            'domain': '.weights.com'
                        })
                except:
                    pass
            else:
                # Это строка вида "key=value; key2=value2"
                pairs = self.cookies.split('; ')
                for pair in pairs:
                    if '=' in pair:
                        key, value = pair.split('=', 1)
                        cookies_list.append({
                            'name': key.strip(),
                            'value': value.strip(),
                            'domain': '.weights.com'
                        })
            
            print(f"   Найдено cookies: {len(cookies_list)}")
            
            # Добавляем каждый cookie
            for cookie in cookies_list:
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    print(f"   ⚠️ Не удалось добавить cookie {cookie.get('name')}: {e}")
            
            print("   ✅ Cookies загружены!")
            
            # Обновляем страницу чтобы применить cookies
            self.driver.refresh()
            time.sleep(3)
            
            self.take_screenshot("01_after_cookies")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Ошибка загрузки cookies: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def perform_search(self):
        """Поиск"""
        try:
            print(f"\n🔍 Переход на страницу моделей...")
            self.driver.get("https://www.weights.com/en/models")
            time.sleep(5)
            
            self.take_screenshot("02_models_page")
            
            print("   Ищу поле поиска...")
            
            search_selectors = [
                'input[type="search"]',
                'input[placeholder*="Search"]',
                'input[placeholder*="search"]',
                'input[name="search"]',
                'input[name="q"]',
            ]
            
            search_box = None
            for selector in search_selectors:
                try:
                    search_box = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if search_box.is_displayed():
                        print(f"   ✅ Поле поиска: {selector}")
                        break
                except:
                    continue
            
            if not search_box:
                print("   ❌ Поле поиска не найдено (возможно требуется авторизация)!")
                
                # Проверяем есть ли кнопка логина
                login_buttons = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Sign in') or contains(text(), 'Log in') or contains(text(), 'Login')]")
                if len(login_buttons) > 0:
                    print("   ⚠️ Найдена кнопка входа - cookies не сработали или истекли!")
                
                return False
            
            search_box.clear()
            time.sleep(1)
            search_box.send_keys("voice")
            time.sleep(2)
            search_box.send_keys(Keys.RETURN)
            
            print(f"   ⏳ Ожидание результатов (8 сек)...")
            time.sleep(8)
            
            # Прокручиваем
            for i in range(3):
                self.driver.execute_script("window.scrollBy(0, 500);")
                time.sleep(2)
            
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            self.take_screenshot("03_search_results")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Ошибка поиска: {e}")
            return False
    
    def open_first_model(self):
        """Открыть первый результат"""
        try:
            print(f"\n👆 Открываю первый результат...")
            
            model_links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/models/"]')
            print(f"   Найдено ссылок: {len(model_links)}")
            
            if len(model_links) == 0:
                print("   ❌ Результаты не найдены!")
                return False
            
            first_model = model_links[0]
            model_url = first_model.get_attribute('href')
            
            print(f"   Открываю: {model_url}")
            
            self.driver.execute_script("arguments[0].scrollIntoView(true);", first_model)
            time.sleep(1)
            self.driver.execute_script("arguments[0].click();", first_model)
            
            time.sleep(10)
            
            print(f"   ✅ Модель открыта: {self.driver.current_url}")
            self.take_screenshot("04_model_page")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            return False
        
    def get_elapsed_time(self):
        if not self.start_time:
            return 0
        return (datetime.now() - self.start_time).total_seconds()
    
    def get_remaining_time(self):
        elapsed = self.get_elapsed_time()
        total = self.max_time_minutes * 60
        remaining = total - elapsed
        return max(0, remaining)
    
    def format_time(self, seconds):
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}:{secs:02d}"
    
    def should_continue(self):
        elapsed = self.get_elapsed_time()
        max_seconds = self.max_time_minutes * 60
        return elapsed < max_seconds
    
    def collect_current_ids(self):
        """Собрать ID"""
        found_new = 0
        
        try:
            links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/models/"]')
            
            for link in links:
                try:
                    href = link.get_attribute('href')
                    if href and '/models/' in href:
                        parts = href.split('/models/')
                        if len(parts) > 1:
                            model_id = parts[1].split('/')[0].split('?')[0].split('#')[0]
                            if len(model_id) > 15 and model_id not in self.all_ids:
                                self.all_ids.add(model_id)
                                found_new += 1
                except:
                    continue
            
            images = self.driver.find_elements(By.TAG_NAME, 'img')
            for img in images:
                try:
                    src = img.get_attribute('src') or img.get_attribute('data-src')
                    if src and 'assets.weights.com' in src:
                        match = src.split('assets.weights.com/')
                        if len(match) > 1:
                            potential_id = match[1].split('/')[0]
                            if len(potential_id) > 15 and potential_id not in self.all_ids:
                                self.all_ids.add(potential_id)
                                found_new += 1
                except:
                    continue
            
            all_links = self.driver.find_elements(By.TAG_NAME, 'a')
            for link in all_links:
                try:
                    href = link.get_attribute('href')
                    if href and 'weights.com' in href:
                        import re
                        matches = re.findall(r'/([a-z0-9]{20,})', href)
                        for match in matches:
                            if match not in self.all_ids:
                                self.all_ids.add(match)
                                found_new += 1
                except:
                    continue
            
            if found_new > 0:
                print(f"   ✅ +{found_new} новых ID (всего: {len(self.all_ids)})")
                    
        except Exception as e:
            print(f"⚠️ Ошибка сбора: {e}")
        
        return found_new
    
    def scroll_page(self):
        """Скролл"""
        try:
            self.driver.execute_script("window.scrollBy(0, 800);")
            time.sleep(self.scroll_delay)
            
            current_pos = self.driver.execute_script("return window.pageYOffset;")
            max_height = self.driver.execute_script("return document.body.scrollHeight - window.innerHeight;")
            
            if current_pos >= max_height * 0.95:
                print("🔄 Конец страницы...")
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(2)
                return False
            
            return True
            
        except Exception as e:
            return False
    
    def run(self):
        self.start_time = datetime.now()
        end_time = self.start_time + timedelta(minutes=self.max_time_minutes)
        
        print("=" * 70)
        print("🎯 WEIGHTS.COM COLLECTOR v7.0 (COOKIES AUTH)")
        print("=" * 70)
        print(f"⏰ Таймер: {self.max_time_minutes} минут")
        print(f"🕐 Старт: {self.start_time.strftime('%H:%M:%S')}")
        print(f"🏁 Стоп:  {end_time.strftime('%H:%M:%S')}")
        print("=" * 70 + "\n")
        
        try:
            print("🔧 Настройка браузера...")
            self.setup_driver()
            
            self.take_screenshot("00_start")
            
            # Загружаем cookies
            if not self.load_cookies():
                print("❌ Не удалось загрузить cookies!")
                return self.all_ids
            
            # Поиск
            if not self.perform_search():
                print("⚠️ Поиск не удался (возможно cookies устарели)")
                return self.all_ids
            
            # Открыть модель
            if not self.open_first_model():
                print("❌ Не удалось открыть модель")
                return self.all_ids
            
            print("\n✅ Начинаю скролл и сбор...\n")
            
            self.scroll_count = 0
            last_report = time.time()
            report_interval = 30
            last_ids_count = 0
            
            while self.should_continue():
                self.collect_current_ids()
                self.scroll_page()
                self.scroll_count += 1
                
                current_time = time.time()
                if current_time - last_report >= report_interval:
                    elapsed = self.format_time(self.get_elapsed_time())
                    remaining = self.format_time(self.get_remaining_time())
                    new_ids = len(self.all_ids) - last_ids_count
                    last_ids_count = len(self.all_ids)
                    
                    print(f"📊 [{elapsed}] Прокруток: {self.scroll_count} | "
                          f"ID: {len(self.all_ids)} (+{new_ids}) | "
                          f"Осталось: {remaining}")
                    
                    last_report = current_time
                
                if self.scroll_count % 30 == 0:
                    self.take_screenshot(f"scroll_{self.scroll_count}")
            
            print("\n" + "=" * 70)
            print("⏰ АВТОСТОП")
            print("=" * 70)
            
            self.take_screenshot("99_final")
            
        except Exception as e:
            print(f"\n❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()
            
            try:
                self.take_screenshot("ERROR")
            except:
                pass
            
        finally:
            if self.driver:
                self.driver.quit()
            
            total_time = self.format_time(self.get_elapsed_time())
            print(f"\n✅ Завершено за {total_time}")
            print(f"📦 Собрано {len(self.all_ids)} ID\n")
        
        return self.all_ids

def save_results(ids):
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    os.makedirs('results', exist_ok=True)
    
    if len(ids) == 0:
        print("⚠️ ID не найдены.")
        with open('results/latest_ids.txt', 'w') as f:
            f.write('')
        with open('results/latest_links.txt', 'w') as f:
            f.write('')
        return
    
    ids_file = f'results/weights_ids_{timestamp}.txt'
    with open(ids_file, 'w') as f:
        for model_id in sorted(ids):
            f.write(model_id + '\n')
    
    links_file = f'results/weights_links_{timestamp}.txt'
    with open(links_file, 'w') as f:
        for model_id in sorted(ids):
            f.write(f'https://www.weights.com/download?modelId={model_id}\n')
    
    with open('results/latest_ids.txt', 'w') as f:
        for model_id in sorted(ids):
            f.write(model_id + '\n')
    
    with open('results/latest_links.txt', 'w') as f:
        for model_id in sorted(ids):
            f.write(f'https://www.weights.com/download?modelId={model_id}\n')
    
    print("💾 Сохранено:")
    print(f"   📄 {ids_file}")
    print(f"   🔗 {links_file}")

if __name__ == "__main__":
    MAX_TIME_MINUTES = int(os.getenv('MAX_TIME_MINUTES', '30'))
    SCROLL_DELAY = int(os.getenv('SCROLL_DELAY', '3'))
    COOKIES = os.getenv('WEIGHTS_COOKIES')
    
    collector = WeightsCollector(
        max_time_minutes=MAX_TIME_MINUTES,
        scroll_delay=SCROLL_DELAY,
        cookies=COOKIES
    )
    
    ids = collector.run()
    save_results(ids)
    
    print("\n" + "=" * 70)
    print(f"🎉 ЗАВЕРШЕНО! Собрано {len(ids)} ID")
    print("=" * 70 + "\n")
