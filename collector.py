from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
from datetime import datetime, timedelta

class WeightsCollector:
    def __init__(self, max_time_minutes=30, scroll_delay=3):
        self.max_time_minutes = max_time_minutes
        self.scroll_delay = scroll_delay
        self.all_ids = set()
        self.start_time = None
        self.driver = None
        self.scroll_count = 0
        
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
    
    def perform_initial_search(self):
        """Выполнить начальный поиск"""
        try:
            print(f"\n🔍 Выполняю поиск голосовых моделей...")
            
            # Ждём поле поиска
            search_selectors = [
                'input[type="search"]',
                'input[placeholder*="Search"]',
                'input[placeholder*="search"]',
                'input[name="search"]',
                'input[name="q"]',
                '.search-input',
                '#search'
            ]
            
            search_box = None
            for selector in search_selectors:
                try:
                    search_box = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if search_box:
                        print(f"✅ Найдено поле поиска: {selector}")
                        break
                except:
                    continue
            
            if not search_box:
                # Пробуем найти любой input
                inputs = self.driver.find_elements(By.TAG_NAME, 'input')
                for inp in inputs:
                    input_type = inp.get_attribute('type')
                    if input_type in ['search', 'text', None]:
                        search_box = inp
                        print(f"✅ Найден input: type={input_type}")
                        break
            
            if not search_box:
                print("❌ Поле поиска не найдено!")
                self.take_screenshot("search_not_found")
                return False
            
            # Вводим запрос "voice"
            search_box.clear()
            time.sleep(0.5)
            search_box.send_keys("voice")
            time.sleep(1)
            search_box.send_keys(Keys.RETURN)
            
            print(f"⏳ Ожидание результатов поиска...")
            time.sleep(5)
            
            self.take_screenshot("01_search_results")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка поиска: {e}")
            self.take_screenshot("search_error")
            return False
    
    def open_first_model(self):
        """Открыть первый результат поиска"""
        try:
            print(f"\n👆 Открываю первый результат...")
            
            # Ищем ссылки на модели
            model_links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/models/"]')
            
            print(f"   Найдено ссылок на модели: {len(model_links)}")
            
            if len(model_links) == 0:
                print("❌ Результаты поиска не найдены!")
                self.take_screenshot("no_results")
                return False
            
            # Кликаем на первую модель
            first_model = model_links[0]
            model_url = first_model.get_attribute('href')
            
            print(f"   Открываю: {model_url}")
            
            first_model.click()
            
            print(f"⏳ Ожидание загрузки страницы модели...")
            time.sleep(5)
            
            print(f"✅ Страница модели открыта: {self.driver.current_url}")
            self.take_screenshot("02_model_page")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка открытия модели: {e}")
            self.take_screenshot("model_open_error")
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
        """Собрать ID со страницы"""
        found_new = 0
        
        try:
            # Метод 1: Ссылки на модели
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
            
            # Метод 2: Изображения от weights.com
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
            
            # Метод 3: Все длинные ID в ссылках
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
        """Скролл страницы"""
        try:
            current_pos = self.driver.execute_script("return window.pageYOffset;")
            max_height = self.driver.execute_script("return document.body.scrollHeight - window.innerHeight;")
            
            # Скролл вниз
            self.driver.execute_script("window.scrollBy(0, 600);")
            time.sleep(self.scroll_delay)
            
            new_pos = self.driver.execute_script("return window.pageYOffset;")
            
            # Если достигли конца - прокрутка вверх
            if new_pos >= max_height * 0.95:
                print("🔄 Конец страницы, прокрутка вверх...")
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(2)
                return False
            
            return True
            
        except Exception as e:
            print(f"⚠️ Ошибка прокрутки: {e}")
            return False
    
    def run(self):
        self.start_time = datetime.now()
        end_time = self.start_time + timedelta(minutes=self.max_time_minutes)
        
        print("=" * 70)
        print("🎯 WEIGHTS.COM VOICE MODELS COLLECTOR v3.5")
        print("=" * 70)
        print(f"⏰ Таймер: {self.max_time_minutes} минут")
        print(f"🕐 Старт: {self.start_time.strftime('%H:%M:%S')}")
        print(f"🏁 Стоп:  {end_time.strftime('%H:%M:%S')}")
        print(f"⏱️  Задержка скролла: {self.scroll_delay} сек")
        print("=" * 70 + "\n")
        
        try:
            print("🔧 Настройка браузера...")
            self.setup_driver()
            
            print("🌐 Загрузка weights.com...")
            self.driver.get("https://www.weights.com/en/models")
            
            print(f"   URL: {self.driver.current_url}")
            print(f"   Title: {self.driver.title}")
            
            print("⏳ Ожидание загрузки (10 сек)...")
            time.sleep(10)
            
            self.take_screenshot("00_homepage")
            
            # Шаг 1: Поиск "1"
            if not self.perform_initial_search():
                print("❌ Не удалось выполнить поиск")
                return self.all_ids
            
            # Шаг 2: Открыть первый результат
            if not self.open_first_model():
                print("❌ Не удалось открыть модель")
                return self.all_ids
            
            print("\n✅ Начинаю бесконечный скролл и сбор ID...\n")
            
            self.scroll_count = 0
            last_report = time.time()
            report_interval = 30
            last_ids_count = 0
            
            # Бесконечный скролл до конца таймера
            while self.should_continue():
                # Сбор ID
                self.collect_current_ids()
                
                # Скролл
                self.scroll_page()
                self.scroll_count += 1
                
                # Периодический отчёт
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
                    
                # Скриншот каждые 50 прокруток
                if self.scroll_count % 50 == 0:
                    self.take_screenshot(f"scroll_{self.scroll_count}")
            
            print("\n" + "=" * 70)
            print("⏰ ВРЕМЯ ВЫШЛО - АВТОСТОП")
            print("=" * 70)
            
            self.take_screenshot("99_final")
            
        except Exception as e:
            print(f"\n❌ Критическая ошибка: {e}")
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
            print(f"\n✅ Сбор завершён за {total_time}")
            print(f"📦 Собрано {len(self.all_ids)} уникальных ID")
            print(f"🔄 Выполнено прокруток: {self.scroll_count}\n")
        
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
    
    print("💾 Результаты сохранены:")
    print(f"   📄 {ids_file}")
    print(f"   🔗 {links_file}")

if __name__ == "__main__":
    MAX_TIME_MINUTES = int(os.getenv('MAX_TIME_MINUTES', '30'))
    SCROLL_DELAY = int(os.getenv('SCROLL_DELAY', '3'))
    
    print("\n🔧 КОНФИГУРАЦИЯ:")
    print(f"   ⏰ Таймер: {MAX_TIME_MINUTES} минут")
    print(f"   ⏱️  Задержка: {SCROLL_DELAY} секунд\n")
    
    collector = WeightsCollector(
        max_time_minutes=MAX_TIME_MINUTES,
        scroll_delay=SCROLL_DELAY
    )
    
    ids = collector.run()
    save_results(ids)
    
    print("\n" + "=" * 70)
    print(f"🎉 ЗАВЕРШЕНО! Собрано {len(ids)} ID голосовых моделей")
    print("=" * 70 + "\n")
