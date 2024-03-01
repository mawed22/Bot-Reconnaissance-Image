from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
import base64
import requests
from gtts import gTTS
from dotenv import load_dotenv
import os
import io

load_dotenv()

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Accessing variables
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


# Create 'Images' directory if it doesn't exist
if not os.path.exists('Images'):
    os.makedirs('Images')

# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Function to handle photo messages
def photo(update, context):
    # Save the photo
    photo_file = update.message.photo[-1].get_file()
    file_path = f'Images/{photo_file.file_id}.jpg'
    photo_file.download(file_path)

    # Encode and send the photo to OpenAI API
    base64_image = encode_image(file_path)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    payload = {
        "model": "gpt-4-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Dis moi si l'image contient un fruit ou un légume, et donne les propriétés nutritives de ce fruit ou légume. Soit bref et précis"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 300
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    if response.status_code == 200:
        # Process the response
        data = response.json()
        #content = data['choices'][0]['message']['content']
        #update.message.reply_text(str(content))  # Format the response for readability
        description = data['choices'][0]['message']['content']

        # Vérification si la description correspond à un fruit ou un légume
        if "fruit" in description or "vegetable" in description or "légume" in description:
            update.message.reply_text(description)
            # Convertir le texte en audio
            tts = gTTS(description, lang='fr')
            audio_io = io.BytesIO()
            tts.write_to_fp(audio_io)
            audio_io.seek(0)
            # Envoyer l'audio à l'utilisateur
            context.bot.send_audio(chat_id=update.effective_chat.id, audio=audio_io, title="Description Audio Fruit/Légume")

        else:
            description = "L'image ne semble pas être celle d'un fruit ou d'un légume. Je ne traite que les images de fruits ou légumes."
            update.message.reply_text(description)
            # Convertir le texte en audio
            tts = gTTS(description, lang='fr')
            audio_io = io.BytesIO()
            tts.write_to_fp(audio_io)
            audio_io.seek(0)
            # Envoyer l'audio à l'utilisateur
            context.bot.send_audio(chat_id=update.effective_chat.id, audio=audio_io, title="Description Audio")
    else:
        update.message.reply_text("L'image est en train d'être analysée.")

# Define a few command handlers
def start(update, context):
    """Send a message when the command /start is issued."""
    update.message.reply_text('Salut 🙂! Je suis FruitVeggieBot, envoye-moi une image de ton fruit🍏ou légume🥕 mystérieux et je me transformerai en détective culinaire pour te révéler ses secrets nutritionnels.')

def help(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Envoye-moi une image de fruit ou de légume et je te donnerai des informations dessus !')

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def handle_text(update, context):
    """Répondre aux messages textuels qui ne sont pas des commandes."""
    update.message.reply_text("Salut 🙂! Je ne traite que des images de fruits ou de légumes. Veuillez m'envoyer une image de fruit ou de légume pour analyse.")

def main():
    """Start the bot."""
    updater = Updater(TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # On different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))

    # on non-command i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))

    # On non-command i.e. photo - echo the photo on Telegram
    dp.add_handler(MessageHandler(Filters.photo, photo))

    # Log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
