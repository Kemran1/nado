import os

from flask import Flask, render_template, request, redirect, url_for, jsonify
import mysql.connector
from datetime import datetime, time, timedelta
import re
from werkzeug.exceptions import BadRequest

app = Flask(__name__, template_folder=os.path.dirname(os.path.abspath(__file__)))

# Конфигурация базы данных
db_config = {
    'user': 'kemran',
    'password': '555555Kk!',
    'host': '90.156.168.176',
    'database': 'student',
    'raise_on_warnings': True
}


def get_db_connection():
    return mysql.connector.connect(**db_config)


# Главная страница с формой
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Получаем данные из формы
        date_str = request.form.get('date')
        time_str = request.form.get('time')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')

        # Валидация данных
        errors = []

        try:
            appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            min_date = datetime(2025, 6, 15).date()
            max_date = datetime(2025, 8, 15).date()

            if not (min_date <= appointment_date <= max_date):
                errors.append("Дата должна быть между 15 июня 2025 и 15 августа 2025")
        except (ValueError, TypeError):
            errors.append("Неверный формат даты")

        try:
            appointment_time = datetime.strptime(time_str, '%H:%M').time()
            start_time = time(8, 0)
            end_time = time(16, 0)

            if not (start_time <= appointment_time <= end_time):
                errors.append("Время должно быть между 08:00 и 16:00")

            if appointment_time.minute not in (0, 30):
                errors.append("Время должно быть с шагом 30 минут")
        except (ValueError, TypeError):
            errors.append("Неверный формат времени")

        if not full_name or not re.match(r'^[а-яА-ЯёЁa-zA-Z\s\-]+$', full_name):
            errors.append("ФИО должно содержать только буквы и не может быть пустым")

        if not phone or not re.match(r'^\+7 \(\d{3}\) \d{3}-\d{2}-\d{2}$', phone):
            errors.append("Неверный формат телефона")

        if errors:
            return render_template('form.html', errors=errors, form_data=request.form)

        # Сохраняем в базу данных
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Проверяем, не занято ли уже это время
            cursor.execute(
                "SELECT id FROM student.appointments WHERE appointment_date = %s AND appointment_time = %s",
                (appointment_date, appointment_time.strftime('%H:%M:%S'))
            )
            if cursor.fetchone():
                errors.append("Выбранное время уже занято, пожалуйста, выберите другое")
                return render_template('form.html', errors=errors, form_data=request.form)

            # Добавляем запись
            cursor.execute(
                "INSERT INTO student.appointments (appointment_date, appointment_time, full_name, phone_number) "
                "VALUES (%s, %s, %s, %s)",
                (appointment_date, appointment_time.strftime('%H:%M:%S'), full_name, phone))

            conn.commit()
            return redirect(url_for('success'))
        except mysql.connector.Error as err:
            return render_template('form.html', errors=[f"Ошибка базы данных: {err}"], form_data=request.form)
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    return render_template('form.html')


# Страница успешной отправки
@app.route('/success')
def success():
    return render_template('success.html')


# API для получения занятых временных слотов
@app.route('/api/taken_times')
def get_taken_times():
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({'error': 'Date parameter is required'}), 400

    try:
        appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT appointment_time FROM student.appointments WHERE appointment_date = %s",
            (appointment_date,)
        )

        taken_times = []
        for row in cursor:
            # Обрабатываем как timedelta
            if isinstance(row['appointment_time'], timedelta):
                total_seconds = row['appointment_time'].total_seconds()
                hours = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)
                taken_times.append(f"{hours:02d}:{minutes:02d}")
            # Или как строку (если уже в формате HH:MM)
            elif isinstance(row['appointment_time'], str):
                taken_times.append(row['appointment_time'][:5])
            # Или как time
            elif hasattr(row['appointment_time'], 'strftime'):
                taken_times.append(row['appointment_time'].strftime('%H:%M'))

        return jsonify({'taken_times': taken_times})
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


if __name__ == '__main__':
    app.run(debug=True)