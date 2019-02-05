from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import sqlite3, matplotlib
from wordcloud import WordCloud
from PIL import Image
matplotlib.use('Agg')

ign_list = ['Tic-Tac-Four' 'Connect Four\n\n', 'Tic-Tac-Toe\n\n', 'Rock-Paper-Scissors\n\n', 
            'Russian Roulette\n\n', 'Checkers\n\n', 'Pool Checkers\n\n']


# DATABASE OPERATIONS
# Read messages from database
def read_db(cid, uid):
    conn = sqlite3.connect('messages.db')
    c = conn.cursor()
    try:
        c.execute("SELECT messages FROM '{}' WHERE uid = '{}'".format(cid, uid))
        data = c.fetchall()
        conn.close()
        return data
    except:
        conn.close()
        data = '[]'
        return data

# Write messages to database
def write_db(cid, msg, id):
    if all(i not in msg for i in ign_list):
        conn = sqlite3.connect('messages.db')
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS '{}'" 
                  "(messages TEXT NOT NULL DEFAULT '', uid INTEGER UNIQUE PRIMARY KEY)".format(cid))
        c.execute("INSERT OR IGNORE INTO '{}' (messages, uid) VALUES ('', ?)".format(cid), (id,))
        c.execute("UPDATE '{}' SET messages = messages || ' ' || ? WHERE uid LIKE ?".format(cid), (msg, id,))
        conn.commit()
        conn.close()


# COMMAND HANDLERS
# Greeting message
def start(bot, update):
    update.message.reply_text('Add me to groups, and I\'ll collect the messages required for generating a word cloud! '
                              'Use /help for more info')

def help(bot, update):
    update.message.reply_text('This bot can only collect messages from the time it\'s been added to the group.\n'
                              '/generate - Generates a wordcloud from requesting user\'s history\n'
                              '/reset_hist - DELETES all message history of the requesting user\n'
                              '/request - Request a feature to be added\n\nKeep generating for '
                              'different colors and positions!')

# Generate a word cloud image
def gen(bot, update):
    cid = str(update.message.chat_id)
    uid = int(update.message.from_user.id)
    words = str(read_db(cid, uid))
    if words == '[]':
        update.message.reply_text('Please send messages before generating!')
    else:
        words = words.replace('\'', '')
        words = words.replace('\\n', ' ')
        words = words.replace(',', '')
        words = words.lower()
        wordcloud = WordCloud(background_color='white').generate(words)
        image = wordcloud.to_image()
        image.save('wc.png', 'PNG')
        bot.sendPhoto(cid, photo=open('wc.png', 'rb'), 
                      reply_to_message_id=update.message.message_id, 
                      caption='Word Cloud for %s'%(update.message.from_user.first_name))

# Delete user chat history    
def delmsg(bot, update):
    cid = str(update.message.chat_id)
    uid = int(update.message.from_user.id)
    conn = sqlite3.connect('messages.db')
    c = conn.cursor()
    c.execute("DELETE FROM '{}' WHERE uid = ?".format(cid), (uid,))
    conn.commit()
    conn.close()
    update.message.reply_text('History deleted!')

# Request a feature
def req(bot, update, args):
    rmesg = " ".join(args)
    if rmesg == "":
        update.message.reply_text('Please type /request followed by your suggestion')
    else:
        bot.sendMessage(chat_id='', text='Feature requested: %s' %rmesg) 
        conn = sqlite3.connect('features.db')
        conn.execute("INSERT INTO features VALUES (?)", (rmesg,))
        conn.commit()
        conn.close()


# MESSAGE HANDLERS
# Save an incoming message
def save_msg(bot, update):
    cid = str(update.message.chat_id)
    msg = str(update.message.text)
    uid = int(update.message.from_user.id)
    write_db(cid, msg, uid)


# TELEGRAM WRAPPER
def main():
    updater = Updater('')
    dp = updater.dispatcher
    # Command Handlers
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('help', help))
    dp.add_handler(CommandHandler('generate', gen))
    dp.add_handler(CommandHandler('reset_hist', delmsg))
    dp.add_handler(CommandHandler('request', req, pass_args=True))
    # Messages
    dp.add_handler(MessageHandler(Filters.text, save_msg))

    # Start the Bot
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
