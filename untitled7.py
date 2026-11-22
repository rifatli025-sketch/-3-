
import telebot
import sqlite3
import random

bot = telebot.TeleBot("ТВОЙ_ТОКЕН")

conn = sqlite3.connect("movies.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS movies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    genre TEXT,
    year INTEGER,
    rating REAL
)
""")
conn.commit()


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "🎬 Добро пожаловать в MovieBot!\n\n"
        "Я помогу тебе хранить любимые фильмы.\n\n"
        "/add - добавить фильм\n"
        "/list - список фильмов\n"
        "/search - найти фильм\n"
        "/delete - удалить фильм\n"
        "/random - случайный фильм\n"
        "/stats - статистика"
    )


@bot.message_handler(commands=['add'])
def add_movie(message):
    msg = bot.send_message(message.chat.id, "Напиши название фильма:")
    bot.register_next_step_handler(msg, get_genre)


def get_genre(message):
    name = message.text.strip()
    if not name:
        bot.send_message(message.chat.id, "Название не может быть пустым!")
        return

    msg = bot.send_message(message.chat.id, "Напиши жанр фильма:")
    bot.register_next_step_handler(msg, get_year, name)


def get_year(message, name):
    genre = message.text.strip()
    if not genre:
        bot.send_message(message.chat.id, "Жанр не может быть пустым!")
        return

    msg = bot.send_message(message.chat.id, "Напиши год выпуска:")
    bot.register_next_step_handler(msg, get_rating, name, genre)


def get_rating(message, name, genre):
    try:
        year = int(message.text)
        if year < 1888 or year > 2100:
            raise ValueError
    except ValueError:
        bot.send_message(message.chat.id, "Введи корректный год!")
        return

    msg = bot.send_message(message.chat.id, "Оцени фильм от 1 до 10:")
    bot.register_next_step_handler(msg, save_movie, name, genre, year)


def save_movie(message, name, genre, year):
    try:
        rating = float(message.text.replace(",", "."))
        if not 1 <= rating <= 10:
            raise ValueError
    except ValueError:
        bot.send_message(message.chat.id, "Рейтинг должен быть от 1 до 10!")
        return

    cursor.execute(
        "INSERT INTO movies (name, genre, year, rating) VALUES (?, ?, ?, ?)",
        (name, genre, year, rating)
    )
    conn.commit()

    bot.send_message(message.chat.id, "✅ Фильм успешно добавлен!")


@bot.message_handler(commands=['list'])
def show_movies(message):
    cursor.execute("SELECT * FROM movies ORDER BY id DESC")
    movies = cursor.fetchall()

    if not movies:
        bot.send_message(message.chat.id, "Список фильмов пока пуст!")
        return

    result = "🎬 ТВОЯ КОЛЛЕКЦИЯ ФИЛЬМОВ:\n\n"

    for movie in movies:
        result += (
            f"🆔 ID: {movie[0]}\n"
            f"🎥 Название: {movie[1]}\n"
            f"🎭 Жанр: {movie[2]}\n"
            f"📅 Год: {movie[3]}\n"
            f"⭐ Рейтинг: {movie[4]}/10\n\n"
        )

    bot.send_message(message.chat.id, result)


@bot.message_handler(commands=['search'])
def search_movie(message):
    msg = bot.send_message(message.chat.id, "Какой фильм ищем?")
    bot.register_next_step_handler(msg, find_movie)


def find_movie(message):
    cursor.execute(
        "SELECT * FROM movies WHERE name LIKE ?",
        ("%" + message.text.strip() + "%",)
    )
    movies = cursor.fetchall()

    if movies:
        for movie in movies:
            bot.send_message(
                message.chat.id,
                f"🎬 {movie[1]}\n"
                f"🎭 Жанр: {movie[2]}\n"
                f"📅 Год: {movie[3]}\n"
                f"⭐ Рейтинг: {movie[4]}/10\n"
                f"🆔 ID: {movie[0]}"
            )
    else:
        bot.send_message(message.chat.id, "Фильм не найден!")


@bot.message_handler(commands=['delete'])
def delete_movie(message):
    msg = bot.send_message(message.chat.id, "Введи ID фильма:")
    bot.register_next_step_handler(msg, remove_movie)


def remove_movie(message):
    try:
        movie_id = int(message.text)
    except ValueError:
        bot.send_message(message.chat.id, "ID должен быть числом!")
        return

    cursor.execute("DELETE FROM movies WHERE id = ?", (movie_id,))
    conn.commit()

    if cursor.rowcount > 0:
        bot.send_message(message.chat.id, "🗑 Фильм удалён!")
    else:
        bot.send_message(message.chat.id, "Фильм с таким ID не найден!")


@bot.message_handler(commands=['random'])
def random_movie(message):
    cursor.execute("SELECT name, genre, year, rating FROM movies")
    movies = cursor.fetchall()

    if movies:
        movie = random.choice(movies)
        bot.send_message(
            message.chat.id,
            f"🎲 Случайный фильм:\n\n"
            f"🎬 {movie[0]}\n"
            f"🎭 Жанр: {movie[1]}\n"
            f"📅 Год: {movie[2]}\n"
            f"⭐ Рейтинг: {movie[3]}/10"
        )
    else:
        bot.send_message(message.chat.id, "В базе пока нет фильмов!")


@bot.message_handler(commands=['stats'])
def statistics(message):
    cursor.execute("SELECT COUNT(*) FROM movies")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT AVG(rating) FROM movies")
    average = cursor.fetchone()[0]

    cursor.execute("""
        SELECT genre, COUNT(*)
        FROM movies
        GROUP BY genre
        ORDER BY COUNT(*) DESC
    """)
    genres = cursor.fetchall()

    result = f"📊 СТАТИСТИКА\n\n🎬 Всего фильмов: {total}\n"

    if average is not None:
        result += f"⭐ Средний рейтинг: {average:.1f}/10\n"

    result += "\n🎭 Фильмы по жанрам:\n"

    for genre, count in genres:
        result += f"• {genre}: {count}\n"

    bot.send_message(message.chat.id, result)


bot.infinity_polling()
