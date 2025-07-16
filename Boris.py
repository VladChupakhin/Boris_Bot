import requests
from typing import Dict, Optional
import json
from pathlib import Path
from datetime import datetime, date, timedelta

ROOT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = ROOT_DIR / 'application.json'

with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config = json.load(f)

#Constants
PYRUS_AUTH_URL = 'https://accounts.pyrus.com/api/v4'
PYRUS_API_URL = 'https://api.pyrus.com/v4'
FORM_ID = 469817
BOT_LOGIN = config["login"]
BOT_KEY = config["security_key"]

def get_auth_headers() -> Optional[Dict[str, str]]:
    """Получение токена авторизации"""
    try:
        print("Пытаемся авторизоваться...")
        response = requests.post(
            f"{PYRUS_AUTH_URL}/auth",
            json={"login": BOT_LOGIN, "security_key": BOT_KEY},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        response.raise_for_status()
        print("Авторизация успешна!")
        token = response.json().get("access_token")
        if not token:
            print("Ошибка: токен не получен!")
            return None
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    except Exception as e:
        print(f"Ошибка авторизации: {str(e)}")
        return None

def get_valid_date(prompt: str) -> str:
    """Запрашивает дату с проверкой формата"""
    while True:
        date_str = input(prompt + " (YYYY-MM-DD): ")
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return date_str  #просто дату
        except ValueError:
            print("Ошибка формата! Используйте YYYY-MM-DD")

def get_tasks_count(headers: Dict[str, str], params: Dict[str, str]) -> int:
    """Получение количества задач по заданным параметрам"""
    try:
        response = requests.get(
            f"{PYRUS_API_URL}/forms/{FORM_ID}/register",
            headers=headers,
            params=params,
            timeout=10
        )
        response.raise_for_status()
        tasks_data = response.json()
        tasks = tasks_data.get("tasks", [])
        return len(tasks)
    except Exception as e:
        print(f"Ошибка при выполнении запроса: {str(e)}")
        return 0

def generate_report(headers: Dict[str, str], date_params: Dict[str, str]) -> Dict[str, int]:
    """Генерация отчета с использованием введенных дат"""
    report: Dict[str, int] = {}
    
    # Всего задач в телеграм
    params_total = {
        "field_ids": "",
        "fld434": "5",
        "include_archived": "y",
        **date_params
    }
    report["total_tasks"] = get_tasks_count(headers, params_total)
    
    # Задач подходящих под условия
    params_eligible = {
        "field_ids": "",  
        "fld434": "5",
        "fld650": "76365689,76365693,80222870,77549497,77549500",
        "fld651": "76365689,76365693,80222870,77549497,77549500",
        "include_archived": "y",
        **date_params
    }
    report["eligible_tasks"] = get_tasks_count(headers, params_eligible)
    
    # Распределилось на Бориса
    params_boris = {
        "field_ids": "",  
        "fld434": "5",
        "fld805": "2,3,4,5",
        "include_archived": "y",
        **date_params
    }
    report["boris_assigned"] = get_tasks_count(headers, params_boris)
    
    # Операторы отметили что он не участвовал
    params_not_participated = {
        "field_ids": "",  
        "fld434": "5",
        "fld805": "2,3,4,5",
        "fld822": "4",
        "include_archived": "y",
        **date_params
    }
    report["not_participated"] = get_tasks_count(headers, params_not_participated)
    
    # Борис пообщался полноценно
    params_full_conversation = {
        "field_ids": "",  
        "fld434": "5",
        "fld805": "2,3,4,5",
        "fld822": "1,2,3",
        "include_archived": "y",
        **date_params
    }
    report["full_conversation"] = get_tasks_count(headers, params_full_conversation)
    
    # Решил задач/Предложил точное решение
    params_solved = {
        "field_ids": "",  
        "fld434": "5",
        "fld805": "2,3,4,5",
        "fld822": "1",
        "include_archived": "y",
        **date_params
    }
    report["solved_tasks"] = get_tasks_count(headers, params_solved)
    
    # Помог клиенту/Операторам
    params_helped = {
        "field_ids": "",  
        "fld434": "5",
        "fld805": "2,3,4,5",
        "fld822": "2",
        "include_archived": "y",
        **date_params
    }
    report["helped_tasks"] = get_tasks_count(headers, params_helped)
    
    # Ответил не правильно
    params_wrong_answer = {
        "field_ids": "",  
        "fld434": "5",
        "fld805": "2,3,4,5",
        "fld822": "3",
        "include_archived": "y",
        **date_params
    }
    report["wrong_answers"] = get_tasks_count(headers, params_wrong_answer)
    
    return report

def main() -> None:
    headers = get_auth_headers()
    if not headers:
        print("Не удалось получить заголовки авторизации. Выход.")
        return
    
    print("\n=== Ввод параметров отчета ===")
    print("Введите период для анализа:")
    date_from_str = get_valid_date("Дата начала периода")
    date_to_str = get_valid_date("Дата окончания периода")

    #строки в объекты date
    date_from = datetime.strptime(date_from_str, "%Y-%m-%d").date()
    date_to = datetime.strptime(date_to_str, "%Y-%m-%d").date()

    #один день к date_to
    date_to_plus_one = date_to + timedelta(days=1)

    #завтрашняя дату
    date_too = date.today() + timedelta(days=1)

    #даты в строки для API
    date_from_str = date_from.strftime("%Y-%m-%d")
    date_to_plus_one_str = date_to_plus_one.strftime("%Y-%m-%d")
    date_too_str = date_too.strftime("%Y-%m-%d")


    date_params = {
        "created_after": f"{date_from_str}T00:00:00Z",
        "created_before": f"{date_to_plus_one_str}T00:00:00Z",
        "closed_before": f"{date_too_str}T23:59:59Z"
    }
    
    report = generate_report(headers, date_params)
    
    print("\n=== Результаты отчета ===")
    print(f"Всего задач в телеграм: {report['total_tasks']}")
    print(f"Задач подходящих под условия: {report['eligible_tasks']}")
    print(f"Распределилось на Бориса: {report['boris_assigned']}")
    print(f"Операторы отметили что он не участвовал: {report['not_participated']}")
    print(f"Борис пообщался полноценно: {report['full_conversation']}")
    print(f"Решил задач/Предложил точное решение: {report['solved_tasks']}")
    print(f"Помог клиенту/Операторам: {report['helped_tasks']}")
    print(f"Ответил не правильно: {report['wrong_answers']}")

if __name__ == "__main__":
    main()