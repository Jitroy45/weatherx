import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
import requests
import json
from telegram.ext import JobQueue

TELEGRAM_BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
OPENWEATHERMAP_API_KEY = 'YOUR_OPENWEATHERMAP_API_KEY'


def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Current Weather", callback_data='current_weather')],
        [InlineKeyboardButton("Forecast", callback_data='forecast')],
        [InlineKeyboardButton("Set Location", callback_data='set_location')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Welcome to Aesthetic Weather Bot! Use the buttons below:', reply_markup=reply_markup)

def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    
    if query.data == 'current_weather':
        weather(query, context)
    elif query.data == 'forecast':
        forecast(query, context)
    elif query.data == 'set_location':
        query.edit_message_text('Please use /setlocation <city> to set your location.')

def check_weather(context: CallbackContext) -> None:
    job = context.job
    location = job.context['location']
    chat_id = job.context['chat_id']
    
    weather_data = get_weather(location)
    if weather_data.get('cod') != 200:
        context.bot.send_message(chat_id, text='Failed to get weather data.')
        return

    weather_desc = weather_data['weather'][0]['description']
    if 'rain' in weather_desc:
        context.bot.send_message(chat_id, text='It\'s going to rain today! ☔')

def set_alert(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    location = context.user_data.get('location')
    if not location:
        update.message.reply_text('Please set your location using /setlocation <city>.')
        return

    context.job_queue.run_repeating(check_weather, interval=3600, first=0, context={'chat_id': chat_id, 'location': location})
    update.message.reply_text('Weather alerts have been set!')


def set_location(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    location = ' '.join(context.args)
    context.user_data['location'] = location
    update.message.reply_text(f'Set location to {location}. Use /weather to get the current weather.')


def get_weather(location: str) -> dict:
    url = f'http://api.openweathermap.org/data/2.5/weather?q={location}&appid={OPENWEATHERMAP_API_KEY}&units=metric'
    response = requests.get(url)
    return response.json()


def weather(update: Update, context: CallbackContext) -> None:
    location = context.user_data.get('location')
    if not location:
        update.message.reply_text('Please set your location using /setlocation <city>.')
        return

    weather_data = get_weather(location)
    if weather_data.get('cod') != 200:
        update.message.reply_text('Failed to get weather data. Please check your location and try again.')
        return

    weather_desc = weather_data['weather'][0]['description']
    temp = weather_data['main']['temp']
    humidity = weather_data['main']['humidity']
    wind_speed = weather_data['wind']['speed']
    icon = weather_data['weather'][0]['icon']

    weather_icons = {
        "01d": "☀️", "01n": "🌙",
        "02d": "🌤️", "02n": "☁️",
        "03d": "🌥️", "03n": "☁️",
        "04d": "☁️", "04n": "☁️",
        "09d": "🌧️", "09n": "🌧️",
        "10d": "🌦️", "10n": "🌧️",
        "11d": "⛈️", "11n": "⛈️",
        "13d": "❄️", "13n": "❄️",
        "50d": "🌫️", "50n": "🌫️"
    }
    
    weather_icon = weather_icons.get(icon, "🌈")
    
    weather_message = (
        f"Weather in *{location}*:\n"
        f"{weather_icon} *{weather_desc.capitalize()}*\n"
        f"🌡️ *Temperature*: {temp}°C\n"
        f"💧 *Humidity*: {humidity}%\n"
        f"💨 *Wind Speed*: {wind_speed} m/s"
    )

    update.message.reply_text(weather_message, parse_mode='Markdown')



def forecast(update: Update, context: CallbackContext) -> None:
    location = context.user_data.get('location')
    if not location:
        update.message.reply_text('Please set your location using /setlocation <city>.')
        return

    url = f'http://api.openweathermap.org/data/2.5/forecast?q={location}&appid={OPENWEATHERMAP_API_KEY}&units=metric'
    response = requests.get(url)
    forecast_data = response.json()

    if forecast_data.get('cod') != '200':
        update.message.reply_text('Failed to get forecast data. Please check your location and try again.')
        return

    forecast_message = f"Weather forecast for *{location}*:\n"
    for item in forecast_data['list'][:8]:
        time = item['dt_txt']
        desc = item['weather'][0]['description']
        temp = item['main']['temp']
        forecast_message += f"`{time}`: *{desc.capitalize()}*, {temp}°C\n"

    update.message.reply_text(forecast_message, parse_mode='Markdown')
  
def main() -> None:
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('setlocation', set_location))
    dispatcher.add_handler(CommandHandler('weather', weather))
    dispatcher.add_handler(CommandHandler('forecast', forecast))
    dispatcher.add_handler(CommandHandler('alert', set_alert))
    dispatcher.add_handler(CallbackQueryHandler(button))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()


