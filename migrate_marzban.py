#!/usr/bin/env python3
import mysql.connector
import json
import uuid
import secrets
import getpass
import os
import datetime
import pytz  # Добавлен новый импорт

def generate_password(length=32):
    """Генерация случайного пароля для Trojan/Shadowsocks"""
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def get_db_config(label, prev_config=None):
    """Запрос параметров подключения к БД с подсказками из предыдущих значений"""
    if not prev_config:
        prev_config = {}
    
    print(f"\n===== {label} сервер =====")
    
    # Запрос хоста с подсказкой
    host_prompt = f"IP или хост"
    if 'host' in prev_config:
        host_prompt += f" [{prev_config['host']}]"
    host_prompt += ": "
    host = input(host_prompt) or prev_config.get('host', '')
    while not host:
        host = input("IP или хост не может быть пустым: ")
    
    # Запрос порта с подсказкой
    port_prompt = "Порт"
    default_port = prev_config.get('port', 3306)
    if default_port:
        port_prompt += f" [по умолчанию {default_port}]"
    port_prompt += ": "
    port = input(port_prompt) or default_port
    port = int(port) if port else 3306
    
    # Запрос пользователя с подсказкой
    user_prompt = "Пользователь MySQL"
    if 'user' in prev_config:
        user_prompt += f" [{prev_config['user']}]"
    user_prompt += ": "
    user = input(user_prompt) or prev_config.get('user', '')
    while not user:
        user = input("Пользователь MySQL не может быть пустым: ")
    
    # Пароль всегда запрашиваем новый
    password = getpass.getpass("Пароль MySQL: ")
    
    # Запрос базы данных с подсказкой
    db_prompt = "Имя базы данных (marzban)"
    default_db = prev_config.get('database', 'marzban')
    if default_db:
        db_prompt += f" [{default_db}]"
    db_prompt += ": "
    database = input(db_prompt) or default_db or 'marzban'
    
    return {
        'host': host,
        'port': port,
        'user': user,
        'password': password,
        'database': database
    }

def load_config():
    """Загрузка конфигурации из файла"""
    config_path = 'migrate_db_config.json'
    if not os.path.exists(config_path):
        return None
        
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Ошибка загрузки конфига: {e}")
        return None

def save_config(old_cfg, new_cfg):
    """Сохранение конфигурации в файл (без паролей)"""
    config_path = 'migrate_db_config.json'
    
    # Удаляем пароли перед сохранением
    safe_old = old_cfg.copy()
    safe_new = new_cfg.copy()
    safe_old.pop('password', None)
    safe_new.pop('password', None)
    
    config = {
        'old': safe_old,
        'new': safe_new
    }
    
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"\nКонфигурация сохранена в {config_path} (без паролей)")
    except Exception as e:
        print(f"Ошибка сохранения конфига: {e}")

def ensure_datetime(value, default=None, timezone='UTC'):
    """Конвертирует значение в DATETIME с учетом часового пояса"""
    if value is None or value == 0:
        return None

    # Обработка числового timestamp
    if isinstance(value, (int, float)):
        try:
            # Проверка диапазона
            if 0 < value <= 253402300799:  # Диапазон 1970-9999 год
                # Создаем UTC-дату
                utc_dt = datetime.datetime.utcfromtimestamp(value)
                
                # Конвертируем в нужный часовой пояс
                if timezone == 'Europe/Moscow':
                    msk_tz = pytz.timezone('Europe/Moscow')
                    utc_dt = pytz.utc.localize(utc_dt)
                    msk_dt = utc_dt.astimezone(msk_tz)
                    return msk_dt.strftime('%Y-%m-%d %H:%M:%S')
                return utc_dt.strftime('%Y-%m-%d %H:%M:%S')
        except (TypeError, ValueError):
            pass

    # Обработка строкового значения
    elif isinstance(value, str):
        try:
            # Парсим наивное время (без часового пояса)
            dt = datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            
            # Конвертируем в нужный часовой пояс
            if timezone == 'Europe/Moscow':
                msk_tz = pytz.timezone('Europe/Moscow')
                dt = msk_tz.localize(dt)
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            return value  # Возвращаем как есть для UTC
        except ValueError:
            pass

    return default

# Основной код скрипта
prev_config = load_config()

# Обработка старого сервера
print("\n" + "="*50)
if prev_config and 'old' in prev_config:
    print("Найдена сохраненная конфигурация для СТАРОГО сервера:")
    print(f"  Хост: {prev_config['old'].get('host', '')}")
    print(f"  Порт: {prev_config['old'].get('port', '')}")
    print(f"  Пользователь: {prev_config['old'].get('user', '')}")
    print(f"  База данных: {prev_config['old'].get('database', '')}")
    use_prev = input("\nИспользовать сохраненные параметры? (y/n): ").lower() == 'y'
    old_config = prev_config['old'] if use_prev else None
else:
    print("Сохраненной конфигурации для СТАРОГО сервера не найдено")
    old_config = None

old_config = get_db_config("Старый", old_config)

# Обработка нового сервера
print("\n" + "="*50)
if prev_config and 'new' in prev_config:
    print("Найдена сохраненная конфигурация для НОВОГО сервера:")
    print(f"  Хост: {prev_config['new'].get('host', '')}")
    print(f"  Порт: {prev_config['new'].get('port', '')}")
    print(f"  Пользователь: {prev_config['new'].get('user', '')}")
    print(f"  База данных: {prev_config['new'].get('database', '')}")
    use_prev = input("\nИспользовать сохраненные параметры? (y/n): ").lower() == 'y'
    new_config = prev_config['new'] if use_prev else None
else:
    print("Сохраненной конфигурации для НОВОГО сервера не найдено")
    new_config = None

new_config = get_db_config("Новый", new_config)

# Сохраняем новую конфигурацию (без паролей)
save_config(old_config, new_config)

# Запрос о временных зонах
print("\n" + "="*50)
print("Настройка временных зон:")
print("1. Старая БД: UTC (рекомендуется)")
print("2. Старая БД: Москва (UTC+3)")
old_db_tz = input("В какой временной зоне хранятся данные в СТАРОЙ базе? (1/2): ").strip()
old_db_tz = 'Europe/Moscow' if old_db_tz == '2' else 'UTC'

# Запрос о переносе сроков действия
print("\n" + "="*50)
transfer_expire = input("Переносить срок действия пользователей (expire)? (y/n): ").lower() == 'y'

print("\nНовая БД всегда использует UTC")
print("Все данные будут автоматически конвертированы")

# Далее идет код миграции...
try:
    # Подключение к старой базе
    old_conn = mysql.connector.connect(**old_config)
    old_cursor = old_conn.cursor(dictionary=True)
    
    # Выгрузка пользователей с их настройками VLESS
    query = """
    SELECT users.*, proxies.settings AS vless_settings 
    FROM users 
    LEFT JOIN proxies ON users.id = proxies.user_id
    """
    old_cursor.execute(query)
    users = old_cursor.fetchall()
    
    if not users:
        print("\n[!] В старой базе не найдено пользователей")
        exit()

    print(f"\nНайдено пользователей: {len(users)}")
    
    # Подготовка данных для вставки в новую базу
    new_users = []
    for user in users:
        # Парсинг VLESS настроек
        try:
            vless = json.loads(user['vless_settings'])
        except:
            vless = {"id": str(uuid.uuid4()), "flow": "xtls-rprx-vision"}
        
        # Генерация новых настроек
        proxy_settings = {
            "vless": {
                "id": vless.get("id", str(uuid.uuid4())),
                "flow": vless.get("flow", "xtls-rprx-vision")
            },
            "vmess": {"id": str(uuid.uuid4())},
            "trojan": {"password": generate_password()},
            "shadowsocks": {
                "method": "chacha20-ietf-poly1305",
                "password": generate_password()
            }
        }
        
        # Определяем текущее время UTC для значений по умолчанию
        now_utc = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        
        # Обработка временных полей с конвертацией временной зоны
        created_at = ensure_datetime(user.get('created_at'), now_utc, old_db_tz)
        
        # Обработка expire в зависимости от выбора пользователя
        if transfer_expire:
            expire = ensure_datetime(user.get('expire'), timezone=old_db_tz)
        else:
            expire = None
            
        sub_revoked_at = ensure_datetime(user.get('sub_revoked_at'), timezone=old_db_tz)
        sub_updated_at = ensure_datetime(user.get('sub_updated_at'), timezone=old_db_tz)
        online_at = ensure_datetime(user.get('online_at'), timezone=old_db_tz)
        edit_at = ensure_datetime(user.get('edit_at'), timezone=old_db_tz)
        last_status_change = ensure_datetime(user.get('last_status_change'), timezone=old_db_tz)
        
        # Формирование записи
        new_user = {
            'username': user['username'],
            'status': user['status'],
            'used_traffic': user['used_traffic'],
            'data_limit': user['data_limit'],
            'expire': expire,
            'created_at': created_at,
            'admin_id': user['admin_id'],
            'data_limit_reset_strategy': user['data_limit_reset_strategy'],
            'sub_revoked_at': sub_revoked_at,
            'note': user['note'],
            'sub_updated_at': sub_updated_at,
            'sub_last_user_agent': user['sub_last_user_agent'],
            'online_at': online_at,
            'edit_at': edit_at,
            'on_hold_timeout': user['on_hold_timeout'],
            'on_hold_expire_duration': user['on_hold_expire_duration'],
            'auto_delete_in_days': user['auto_delete_in_days'],
            'last_status_change': last_status_change,
            'proxy_settings': json.dumps(proxy_settings)
        }
        new_users.append(new_user)
    
    # Подключение к новой базе
    new_conn = mysql.connector.connect(**new_config)
    new_cursor = new_conn.cursor()
    
    # SQL для вставки
    columns = ", ".join(new_users[0].keys())
    placeholders = ", ".join(["%s"] * len(new_users[0]))
    insert_query = f"INSERT INTO users ({columns}) VALUES ({placeholders})"
    
    # Вставка данных
    for user in new_users:
        new_cursor.execute(insert_query, tuple(user.values()))
    
    new_conn.commit()
    print(f"\n[✓] Успешно перенесено {len(new_users)} пользователей")
    print(f"Конвертация времени выполнена из: {old_db_tz} -> UTC")
    print(f"Сроки действия перенесены: {'Да' if transfer_expire else 'Нет'}")
    
except mysql.connector.Error as err:
    print(f"\n[!] Ошибка MySQL: {err}")
    print(f"Код ошибки: {err.errno}")
    print(f"SQLSTATE: {err.sqlstate}")
    print(f"Сообщение: {err.msg}")
except Exception as e:
    print(f"\n[!] Ошибка: {e}")
    import traceback
    traceback.print_exc()
finally:
    if 'old_conn' in locals() and old_conn.is_connected():
        old_conn.close()
    if 'new_conn' in locals() and new_conn.is_connected():
        new_conn.close()
