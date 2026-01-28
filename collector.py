from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
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
        self.scroll_count = 0  # ← ИСПРАВЛЕНО: инициализация счётчика
        
    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")  # ← ИСПРАВЛЕНО: новый headless
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        # Используем системный chromedriver
        service = Service('/usr/bin/chromedriver')  # ← ИСПРАВЛЕНО: путь к системному драйверу
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
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
        found_new = 0
        
        try:
            # Ждём загрузки контента
            time.sleep(1)
            
            # Собираем ссылки на модели
            links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/models/"]')
            
            for link in links:
                try:
                    href = link.get_attribute('href')
                    if href and '/models/' in href:
                        parts = href.split('/models/')
                        if len(parts) > 1:
                            model_id = parts[1].split('/')[0].split('?')[0]
                            if len(model_id) > 15 and model_id not in self.all_ids:
                                self.all_ids.add(model_id)
                                found_new += 1
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"⚠️ Ошибка сбора: {e}")
        
        return found_new
    
    def scroll_page(self):
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
        print("🎯 WEIGHTS.COM AUTO COLLECTOR v3.1")
        print("=" * 70)
        print(f"⏰ Таймер: {self.max_time_minutes} минут ({self.max_time_minutes * 60} секунд)")
        print(f"🕐 Старт: {self.start_time.strftime('%H:%M:%S')}")
        print(f"🏁 Стоп:  {end_time.strftime('%H:%M:%S')}")
        print(f"⏱️  Задержка между скроллами: {self.scroll_delay} сек")
        print("=" * 70 + "\n")
        
        try:
            print("🔧 Настройка браузера...")
            self.setup_driver()
            
            print("🌐 Загрузка weights.com...")
            self.driver.get("https://weights.com")
            time.sleep(5)
            print("✅ Страница загружена\n")
            
            self.scroll_count = 0  # ← ИСПРАВЛЕНО: инициализация здесь тоже
            last_report = time.time()
            report_interval = 30
            
            while self.should_continue():
                # Сбор ID
                self.collect_current_ids()
                
                # Прокрутка
                self.scroll_page()
                self.scroll_count += 1
                
                # Периодический отчёт
                current_time = time.time()
                if current_time - last_report >= report_interval:
                    elapsed = self.format_time(self.get_elapsed_time())
                    remaining = self.format_time(self.get_remaining_time())
                    
                    print(f"📊 [{elapsed}] Прокруток: {self.scroll_count} | "
                          f"ID: {len(self.all_ids)} | "
                          f"Осталось: {remaining}")
                    
                    last_report = current_time
            
            print("\n" + "=" * 70)
            print("⏰ ВРЕМЯ ВЫШЛО - АВТОСТОП")
            print("=" * 70)
            
        except Exception as e:
            print(f"\n❌ Критическая ошибка: {e}")
            import traceback
            traceback.print_exc()
            
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
    
    # ID с временной меткой
    ids_file = f'results/weights_ids_{timestamp}.txt'
    with open(ids_file, 'w') as f:
        for model_id in sorted(ids):
            f.write(model_id + '\n')
    
    # Ссылки с временной меткой
    links_file = f'results/weights_links_{timestamp}.txt'
    with open(links_file, 'w') as f:
        for model_id in sorted(ids):
            f.write(f'https://www.weights.com/download?modelId={model_id}\n')
    
    # Последние результаты (перезапись)
    with open('results/latest_ids.txt', 'w') as f:
        for model_id in sorted(ids):
            f.write(model_id + '\n')
    
    with open('results/latest_links.txt', 'w') as f:
        for model_id in sorted(ids):
            f.write(f'https://www.weights.com/download?modelId={model_id}\n')
    
    print("💾 Результаты сохранены:")
    print(f"   📄 {ids_file}")
    print(f"   🔗 {links_file}")
    print(f"   📄 results/latest_ids.txt")
    print(f"   🔗 results/latest_links.txt")

if __name__ == "__main__":
    MAX_TIME_MINUTES = int(os.getenv('MAX_TIME_MINUTES', '30'))
    SCROLL_DELAY = int(os.getenv('SCROLL_DELAY', '3'))
    
    print("\n🔧 КОНФИГУРАЦИЯ:")
    print(f"   ⏰ Таймер автостопа: {MAX_TIME_MINUTES} минут")
    print(f"   ⏱️  Задержка скролла: {SCROLL_DELAY} секунд")
    print(f"   💾 Папка результатов: ./results/\n")
    
    collector = WeightsCollector(
        max_time_minutes=MAX_TIME_MINUTES,
        scroll_delay=SCROLL_DELAY
    )
    
    ids = collector.run()
    save_results(ids)
    
    print("\n" + "=" * 70)
    print(f"🎉 ЗАВЕРШЕНО! Собрано {len(ids)} ID")
    print("=" * 70 + "\n")
