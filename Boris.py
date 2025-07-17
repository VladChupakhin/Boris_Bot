import requests
from typing import Dict, Optional, Any
import json
from pathlib import Path
from datetime import datetime, date, timedelta

ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT_DIR / 'application.json'

with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config: Dict[str, str] = json.load(f)

# Constants
PYRUS_AUTH_URL = 'https://accounts.pyrus.com/api/v4'
PYRUS_API_URL = 'https://api.pyrus.com/v4'
FORM_ID = 469817
BOT_LOGIN: str = config["login"]
BOT_KEY: str = config["security_key"]
MY_ID = 1223545  # мой айдшник в пайрус

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
        token: str = response.json().get("access_token")
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
            return date_str  # просто дату
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
        tasks_data: Dict[str, Any] = response.json()
        tasks: list[Any] = tasks_data.get("tasks", [])
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

    # Не распределено на Бориса - разница
    report["not_assigned_to_boris"] = report["eligible_tasks"] - report["boris_assigned"]

    return report

def create_task_with_comment(headers: Dict[str, str], report_name: str, report_body: str) -> Optional[Dict[str, Any]]:
    """Создает задачу в Pyrus с заданным отчетом и возвращает тело созданной задачи."""
    task_data: Dict[str, Any] = {
        "form_id": FORM_ID,
        "author": {"id": MY_ID},
        "fields": [
            {
                "id": 10,
                "type": "person",
                "name": "Ответственный",
                "value": {"id": MY_ID}
            },
            {
                "id": 1,
                "value": f"[Отчет работа Бориса] [{report_name}]"
            },
            {
                "id": 2,
                "value": report_body
            },
            {
                "id": 16,
                "value": {"choice_id": 1}
            },
            {
                "id": 15,
                "value": {"choice_id": 1}
            },
            {
                "id": 434,
                "value": {"choice_id": 1}
            },
            {
                "id": 805,
                "value": {"choice_id": 1}
            },
            {
                "id": 766,
                "value": {"choice_id": 1}
            }
        ]
    }

    try:
        response = requests.post(
            f"{PYRUS_API_URL}/tasks",
            headers=headers,
            json=task_data,
            timeout=10
        )
        response.raise_for_status()
        task: Dict[str, Any] = response.json()
        return task
    except Exception as e:
        print(f"Ошибка при создании задачи: {str(e)}")
        return None

def main() -> None:
    headers = get_auth_headers()
    if not headers:
        print("Не удалось получить заголовки авторизации. Выход.")
        return

    print("\n=== Ввод параметров отчета ===")
    print("Введите период для анализа:")
    date_from_str = get_valid_date("Дата начала периода")
    date_to_str = get_valid_date("Дата окончания периода")

    # строки в объекты date
    date_from = datetime.strptime(date_from_str, "%Y-%m-%d").date()
    date_to = datetime.strptime(date_to_str, "%Y-%m-%d").date()

    # один день к date_to
    date_to_plus_one = date_to + timedelta(days=1)

    # завтрашняя дата
    date_too = date.today() + timedelta(days=1)

    # даты в строки для API
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
    print(f"#Всего задач в телеграм {report['total_tasks']}")
    print(f"#Задач подходящих под условия (Базовый договор, Cloud, CloudPro, CloudEnterprise) {report['eligible_tasks']}")
    print(f"#Из них распределилось на Бориса только {report['boris_assigned']}")
    print(f"!Не распределено задач на Бориса - {report['not_assigned_to_boris']}")
    print(f"#Операторы отметили что он не участвовал в {report['not_participated']}")
    print(f"#Без проверки можно сделать вывод, что Борис пообщался полноценно в {report['full_conversation']} задачах")
    
    print(f"#Решил задач/Предложил точное решение - {report['solved_tasks']}")
    print(f"#Помог клиенту/Операторам, подсказал в решении - {report['helped_tasks']}")
    print(f"#Ответил не правильно/навыки не подошли - {report['wrong_answers']}")
    print(f"#Не участвовал по мнению оператора - {report['not_participated']}")

    # итоговая аналитика
    total_tasks = report['total_tasks']
    boris_assigned = report['boris_assigned']
    full_conversation = report['full_conversation']
    solved_tasks = report['solved_tasks']
    wrong_answers = report['wrong_answers']
    not_participated = report['not_participated']
    eligible_tasks = report['eligible_tasks']
    not_assigned_to_boris = report['not_assigned_to_boris']
    helped_tasks = report['helped_tasks']

    boris_assigned_percentage = (boris_assigned / total_tasks) * 100 if total_tasks else 0
    full_conversation_percentage = (full_conversation / boris_assigned) * 100 if boris_assigned else 0
    effectiveness_percentage = (solved_tasks / full_conversation) * 100 if full_conversation else 0
    effectiveness_of_all = (solved_tasks / total_tasks) * 100 if total_tasks else 0
    wrong_answers_percentage = (wrong_answers / full_conversation) * 100 if full_conversation else 0
    not_participated_percentage = (not_participated / boris_assigned) * 100 if boris_assigned else 0
    not_assigned_to_boris_percentage = (not_assigned_to_boris / eligible_tasks) * 100 if eligible_tasks else 0

    # BODY отчета
    report_body = f"""
    Общие данные
    #Всего задач в телеграм {total_tasks}
    #Задач подходящих под условия (Базовый договор, Cloud, CloudPro, CloudEnterprise) {eligible_tasks}
    #Из них распределилось на Бориса только {boris_assigned}
    !Не распределено задач на Бориса - {not_assigned_to_boris}
    #Операторы отметили что он не участвовал {not_participated}
    #Без проверки можно сделать вывод, что Борис пообщался полноценно в {full_conversation} задачах
    
    #Решил задач/Предложил точное решение - {solved_tasks}
    #Помог клиенту/Операторам, подсказал в решении - {helped_tasks}
    #Ответил не правильно/навыки не подошли - {wrong_answers}
    #Не участвовал по мнению оператора - {not_participated}

    🧾 Итоговая аналитика:

    Борису передано {boris_assigned_percentage:.1f}% от всех задач ({boris_assigned} из {total_tasks})
    Из переданных задач он полноценно участвовал в {full_conversation} задачах ({full_conversation_percentage:.1f}% от полученных)
    Эффективность в полезных задачах — {effectiveness_percentage:.1f}% ({solved_tasks} из {full_conversation}), что составляет {effectiveness_of_all:.1f}% от всех задач
    В {wrong_answers} задачах дал ошибочные или нерелевантные ответы ({wrong_answers_percentage:.1f}% среди задач с участием)
    По мнению операторов, не участвовал в {not_participated} задаче — это {not_participated_percentage:.1f}% от полученных
    Остались без назначения {not_assigned_to_boris} задачи — это {not_assigned_to_boris_percentage:.1f}% от подходящих
    """

    # NAME отчета
    report_name = f"{date_from_str}-{date_to_str}"

    # CREATE TASK
    task = create_task_with_comment(headers, report_name, report_body)

    if task:
        task_id: int = task['task']['id']
        print("\n=== Задача успешно создана ===")
        print(f"ID задачи: {task_id}")
        print(f"Ссылка на задачу: https://pyrus.com/t#id{task_id}")
        print(f"Текст задачи: {task['task']['text']}")
    else:
        print("Не удалось создать задачу.")


if __name__ == "__main__":
    main()