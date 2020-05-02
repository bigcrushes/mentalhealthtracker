import logging
import telegram
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater
from telegram.ext import MessageHandler, Filters
import math
import random
from telegram.ext import JobQueue
import datetime
import pytz
from telegram.ext import CommandHandler
from telegram.ext import ConversationHandler

#logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

#keyboards and bot setup
bot = telegram.Bot( [TOKEN] )
menu_keyboard = [['Yes'], ['No']]
menu_markup = ReplyKeyboardMarkup(menu_keyboard, one_time_keyboard=True, resize_keyboard=True)
timezone_keyboard = [['+12'],['+11'],['+10'],['+9'],['+8'],['+7'],['+6'],['+5'],['+4'],['+3'],['+2'],['+1'],['+0'],['-1'],['-2'],['-3'],['-4'],['-5'],['-6'],['-7'],['-8'],['-9'],['-10'],['-11'],['-12'],['-13'],['-14']]
timezone_markup = ReplyKeyboardMarkup(timezone_keyboard, one_time_keyboard=True, resize_keyboard=True)

updater = Updater(token= [TOKEN], use_context=True)
dispatcher = updater.dispatcher
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome to HealthyBot! A bot dedicated to try and make sure you keep healthy! You automatically start of with a pet that you can read to or feed to level up! Do so using the coins you earn by checking in and carrying out healthy daily habits! Type /commands to see the commands you can use!")
    if 'petExp' not in context.user_data:
        context.user_data['petExp'] = 0
    if 'coins' not in context.user_data:
        context.user_data['coins'] = 0
    if 'petname' not in context.user_data:
        context.user_data['petname'] = "Mr. No Name"
    if 'timezone' not in context.user_data:
        context.user_data['timezone'] = "+0"
    if 'badDays' not in context.user_data:
        context.user_data['badDays'] = 0


def commands(update, context):
    update.message.reply_text("/bank - Checks number of coins you have\n"
                              "/cancel - Cancel any command you are in the middle of\n"
                              "/commands - Shows list of commands\n"
                              "/checkin - Daily check-in on whether you carried out healthy living habits!\n"
                              "/helpline - Link to Befrienders Worldwide. Seek help if you need someone to talk to.\n"
                              "/petcheck - Checks the progress of your pet\n"
                              "/petfeed - Feed your pet! Costs 100 coins.\n"
                              "/petname - Change your pets name!\n"
                              "/petread - Read to your pet! Costs 300 coins.\n"
                              "/timezone - Change your timezone (default is GMT+0)\n"
                             )

def helpline(update, context):
    update.message.reply_text('Seek help if you need it! Find someone to talk to! https://www.befrienders.org/')

def reminder(context):
    job = context.job
    context.bot.send_message(job.context, text="It's been 24 hours since your last check-in! Remember to check in for today!")

def cancel(update, context):
    update.message.reply_text('Command cancelled', reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def checkInSleep(update, context):
    #get timezone adjusted time
    timeZone = "Etc/GMT" + context.user_data['timezone']

    if 'lastcheckin' not in context.user_data:
        update.message.reply_text('Did you sleep at least 7 hours last night?', reply_markup=menu_markup)
        return SLEEP
    elif context.user_data['lastcheckin'] == datetime.datetime.now(pytz.timezone(timeZone)).date():
        update.message.reply_text("You've already checked in today! Please check in again tomorrow!")
        return ConversationHandler.END
    else:
        update.message.reply_text('Did you sleep at least 7 hours last night?', reply_markup=menu_markup)
        return SLEEP

def checkInEat(update, context):
    #save sleep data
    text = update.message.text
    context.user_data['sleep'] = text
    #ask if at least 2 meals
    update.message.reply_text('Did you eat at least 2 meals yesterday?', reply_markup=menu_markup)
    return EAT

def checkInExercise(update, context):
    #save sleep data
    text = update.message.text
    context.user_data['eat'] = text
    #ask exercise
    update.message.reply_text('Did you exercise yesterday?', reply_markup=menu_markup)
    return EXERCISE

def checkInOverall(update, context):
    #save exercise data
    text = update.message.text
    context.user_data['exercise'] = text
    #ask overall
    update.message.reply_text('Overall, do you feel today was a bad day?', reply_markup=menu_markup)
    return OVERALL

def endCheckIn(update,context):
    timeZone = "Etc/GMT" + context.user_data['timezone']
    #save overall data
    text = update.message.text
    context.user_data['overall'] = text

    #Count score
    user_data = context.user_data
    score = 100
    if user_data['eat'] == 'Yes':
        score+=300
    if user_data['sleep'] == 'Yes':
        score+=300
    if user_data['exercise'] == 'Yes':
        score+=150
    if user_data['overall'] == 'No':
        score+=100

    #add coins
    if 'coins' in user_data:
        user_data['coins'] += score
    else:
        user_data['coins'] = score

    #clear all checkin data
    user_data['sleep'] = None
    user_data['eat'] = None
    user_data['exercise'] = None

    #set last check in date to now
    user_data['lastcheckin'] = datetime.datetime.now(pytz.timezone(timeZone)).date()


    #end conversation

    update.message.reply_text("Thank you for checking in! Here's your {} coins! Have a good day!".format(score))

    #have a counter for bad days
    if user_data['overall'] == 'Yes':
        user_data['badDays'] +=1

    #check bad days counter
    if user_data['badDays'] == 7:
        update.message.reply_text("You seem to be having a rough week! Maybe try talking about your problems with a friend or use /helpline to find your nearest available helpline! Stay strong and stay happy!")

    #set new timer to remind next check in
    if 'job' in context.chat_data:
        old_job = context.chat_data['job']
        old_job.schedule_removal()

    new_job = context.job_queue.run_once(reminder, 86400, context=update.message.chat_id)
    context.chat_data['job'] = new_job

    if score < 200:
        update.message.reply_text('Remember to take care of yourself!')
    return ConversationHandler.END

def checkBank(update,context):
    update.message.reply_text("You have {} coins!".format(context.user_data['coins']))


def checkPet(update,context): #check progress of pet
    bot.sendSticker(chat_id=update.message.chat_id, sticker='CAACAgUAAxkBAAICg15_MnUgv_0jS6VYZRq70C4VYo9tAAJLAAN3MrICOUCcm5EhcKwYBA')
    update.message.reply_text("Your pet {} is level {}! Only {} more XP to the next level!".format(context.user_data['petname'], math.ceil(context.user_data['petExp']/200), 200-(context.user_data['petExp']%200)))

def readToPet(update,context):
    if context.user_data['coins'] < 300:
        update.message.reply_text("You don't have enough coins for this!")
    else:
        xpgain = random.randint(70,100)
        context.user_data['petExp'] += xpgain
        context.user_data['coins'] -= 300
        update.message.reply_text("Your pet {} earned {} XP! You have {} coins left!".format(context.user_data['petname'],xpgain, context.user_data['coins']))

def petName(update, context):
    update.message.reply_text("Please give a name for your pet!")
    return PETNAME

def getPetName(update, context):
    text = update.message.text
    context.user_data['petname'] = text
    update.message.reply_text("Your pet is now named {}! Thank you!".format(context.user_data['petname']))
    return ConversationHandler.END

def feedPet(update,context):
    if context.user_data['coins'] < 100:
        update.message.reply_text("You don't have enough coins for this!")
    else:
        xpgain = random.randint(15,25)
        context.user_data['petExp'] += xpgain
        context.user_data['coins'] -= 100
        update.message.reply_text("Your pet {} earned {} XP! You have {} coins left!".format(context.user_data['petname'],xpgain, context.user_data['coins']))

def timezone(update,context):
    update.message.reply_text('With reference to GMT, what is your timezone?', reply_markup=timezone_markup)
    return TIMEZONE

def getTimezone(update,context):
    text = update.message.text
    if text != "+12" and text != "+11" and text != "+10" and text != "+9" and text != "+8" and text != "+7" and text != "+6" and text != "+5" and text != "+4" and text != "+3" and text != "+2" and text != "+1" and text != "+0" and text != "-1" and text != "-2" and text != "-3" and text != "-4" and text != "-5" and text != "-6" and text != "-7" and text != "-8" and text != "-10" and text != "-11" and text != "-12" and text != "-13" and text != "-14":
        update.message.reply_text("You did not enter a timezone!")
        return ConversationHandler.END
    else:
        context.user_data['timezone'] = text
        update.message.reply_text("Your timezone has been changed! Thank you!")
        return ConversationHandler.END

EAT,SLEEP,PETNAME,TIMEZONE,EXERCISE,OVERALL = range(6)
def main():
    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    coin_handler = CommandHandler('bank', checkBank)
    dispatcher.add_handler(coin_handler)

    pet_handler = CommandHandler('petcheck', checkPet)
    dispatcher.add_handler(pet_handler)

    readpet_handler = CommandHandler('petread', readToPet)
    dispatcher.add_handler(readpet_handler)

    commands_handler = CommandHandler('commands', commands)
    dispatcher.add_handler(commands_handler)

    feedpet_handler = CommandHandler('petfeed', feedPet)
    dispatcher.add_handler(feedpet_handler)

    helpline_handler = CommandHandler('helpline', helpline)
    dispatcher.add_handler(helpline_handler)

    #get pet name
    conv2_handler = ConversationHandler(
        entry_points=[CommandHandler('petname', petName)],

        states={
            PETNAME: [MessageHandler(Filters.text, getPetName)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dispatcher.add_handler(conv2_handler)

    #checkin tracker
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('checkin', checkInSleep)],

        states={
            SLEEP: [MessageHandler(Filters.regex('^(Yes|No)$'), checkInEat)],

            EAT: [MessageHandler(Filters.regex('^(Yes|No)$'), checkInExercise)],

            EXERCISE: [MessageHandler(Filters.regex('^(Yes|No)$'), checkInOverall)],

            OVERALL: [MessageHandler(Filters.regex('^(Yes|No)$'), endCheckIn)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dispatcher.add_handler(conv_handler)

    #timezone convo handler
    conv3_handler = ConversationHandler(
        entry_points=[CommandHandler('timezone', timezone)],

        states={
            TIMEZONE: [MessageHandler(Filters.text, getTimezone)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dispatcher.add_handler(conv3_handler)


    updater.start_polling()

if __name__ == '__main__':
    main()
