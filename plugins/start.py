#(©)CodeXBotz





import os
import asyncio
import sys
from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode, ChatMemberStatus
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, User
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, UserNotParticipant

from bot import Bot
from config import ADMINS, OWNER_ID, FORCE_MSG, START_MSG, CUSTOM_CAPTION, DISABLE_CHANNEL_BUTTON, PROTECT_CONTENT, DEL_TIMER, AUTO_DEL, DEL_MSG, USER_REPLY_TEXT
from helper_func import subscribed1, subscribed3, subscribed2, encode, decode, get_messages
from database.database import add_user, remove_all, del_user, full_userbase, present_user, is_admin
from plugins.trippy_xt import convert_time
from database.database import total_click, add_click, top_users, set_fsub, get_fsub

@Bot.on_message(filters.command('start') & filters.private & subscribed1 & subscribed2 & subscribed3)
async def start_command(client: Client, message: Message):
    id = message.from_user.id
    user_id = message.from_user.id
    if not await present_user(id):
        try:
            await add_user(id)
        except:
            pass
    text = message.text
    if len(text) > 7:
        try:
            base64_string = text.split(" ", 1)[1]
        except:
            return
        string = await decode(base64_string)
        argument = string.split("-")
        if len(argument) == 3:
            try:
                start = int(int(argument[1]) / abs(client.db_channel.id))
                end = int(int(argument[2]) / abs(client.db_channel.id))
            except:
                return
            if start <= end:
                ids = range(start, end + 1)
            else:
                ids = []
                i = start
                while True:
                    ids.append(i)
                    i -= 1
                    if i < end:
                        break
        elif len(argument) == 2:
            try:
                ids = [int(int(argument[1]) / abs(client.db_channel.id))]
            except:
                return
        temp_msg = await message.reply("Please wait...")
        last_message = None
        try:
            messages = await get_messages(client, ids)
        except:
            await message.reply_text("Something went wrong..!")
            return
        await temp_msg.delete()

        for idx, msg in enumerate(messages): 
            if bool(CUSTOM_CAPTION) & bool(msg.document):
                caption = CUSTOM_CAPTION.format(previouscaption="" if not msg.caption else msg.caption.html, filename=msg.document.file_name)
            else:
                caption = "" if not msg.caption else msg.caption.html

            if DISABLE_CHANNEL_BUTTON:
                reply_markup = msg.reply_markup
            else:
                reply_markup = None

            try:
                await add_click(user_id, base64_string)
                copied_msg = await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup, protect_content=PROTECT_CONTENT)
                await asyncio.sleep(0.1)
                asyncio.create_task(delete_message(copied_msg, DEL_TIMER))
                if idx == len(messages) - 1 and AUTO_DEL: 
                    last_message = copied_msg
            except FloodWait as e:
                await asyncio.sleep(e.x)
                copied_msg = await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup, protect_content=PROTECT_CONTENT)
                await asyncio.sleep(0.1)
                asyncio.create_task(delete_message(copied_msg, DEL_TIMER))
                if idx == len(messages) - 1 and AUTO_DEL:
                    last_message = copied_msg

        if AUTO_DEL and last_message:
            asyncio.create_task(auto_del_notification(client, last_message, DEL_TIMER))

        return
    else:
        reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("About Me", callback_data="about"),
                    InlineKeyboardButton("Close", callback_data="close")
                ]
            ]
        )
        await message.reply_text(
            text=START_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            quote=True
        )
        return


       


#=====================================================================================##

WAIT_MSG = """"<b>Processing ....</b>"""

REPLY_ERROR = """<code>Use this command as a reply to any telegram message with out any spaces.</code>"""

#=====================================================================================##

@Bot.on_message(filters.command('start') & filters.private)
async def not_joined(client: Bot, message: Message):
    buttons = [
        [
            InlineKeyboardButton(text="Join Channel", url=client.invitelink),
            InlineKeyboardButton(text="Join Channel", url=client.invitelink2),
        ]
    ]
    try:
        buttons.append(
            [
                InlineKeyboardButton(
                    text = 'Try Again',
                    url = f"https://t.me/{client.username}?start={message.command[1]}"
                )
            ]
        )
    except IndexError:
        pass
    
    


    await message.reply(
        text = FORCE_MSG.format(
                first = message.from_user.first_name,
                last = message.from_user.last_name,
                username = None if not message.from_user.username else '@' + message.from_user.username,
                mention = message.from_user.mention,
                id = message.from_user.id
            ),
        reply_markup = InlineKeyboardMarkup(buttons),
        quote = True,
        disable_web_page_preview = True
    )

@Bot.on_message(filters.command('users'))
async def get_users(client: Bot, message: Message):
    user_id = message.from_user.id
    is_user_admin = await is_admin(user_id)
    if not is_user_admin and user_id != OWNER_ID:       
        return   
    msg = await client.send_message(chat_id=message.chat.id, text=WAIT_MSG)
    users = await full_userbase()
    await msg.edit(f"{len(users)} users are using this bot")

@Bot.on_message(filters.command('changefsub'))
async def set_channels(client: Bot, message: Message):
    user_id = message.from_user.id
    is_user_admin = await is_admin(user_id)

    if not is_user_admin and user_id != OWNER_ID:
        await message.reply_text(USER_REPLY_TEXT)
        return

    if len(message.command) != 3:
        await message.reply_text("<b>Use like this sir:</b>\n<b>Ex:</b> /changefsub -100Xxxxxxx -100Xxxxxxx")
        return

    try:
        new_channel_id_1 = int(message.command[1])
        new_channel_id_2 = int(message.command[2])

        # Check if the bot is a participant of both channels
        member1 = await client.get_chat_member(chat_id=new_channel_id_1, user_id=client.me.id)
        member2 = await client.get_chat_member(chat_id=new_channel_id_2, user_id=client.me.id)

        if not member1 or not member2:
            await message.reply_text("admin toh dedo unkil :) ")
            return

        await set_fsub(new_channel_id_1, new_channel_id_2)

        channel_info = []

        channel1, channel2 = await get_fsub()

        for channel_id in [channel1, channel2]:
            try:
                chat = await client.get_chat(channel_id)
                channel_name = chat.title
                channel_info.append(f"<b>⚡ {channel_name} ({channel_id})</b>")
            except Exception as e:
                channel_info.append(f"<b>⚡ Unknown Channel ({channel_id})</b>")
        
        channels_text = "\n".join(channel_info)

        res = await message.reply_text(f"<b>Ruko bde bhaiya restart karne do 💦</b>")
        await asyncio.sleep(3)       
        await res.edit_text(f"<b>New Forcesub channels are:</b>\n{channels_text}")
        os.execl(sys.executable, sys.executable, *sys.argv)
        
    except ValueError:
        await message.reply_text("Channel IDs must be integers.")
    except Exception as e:
        await message.reply_text(f"An error occurred while processing your request.")




@Bot.on_message(filters.command('fsub'))
async def check_channels(client: Bot, message: Message):
    user_id = message.from_user.id
    is_user_admin = await is_admin(user_id)

    if not is_user_admin and user_id != OWNER_ID:
        await message.reply_text(USER_REPLY_TEXT)
        return

    channel_info = []
    
    channel1, channel2 = await get_fsub()

    for channel_id in [channel1, channel2]:
        try:
            chat = await client.get_chat(channel_id)
            channel_name = chat.title
            channel_info.append(f"<b>{channel_name}</b> ({channel_id})")
        except Exception as e:
            channel_info.append(f"<b>Unknown Channel ({channel_id})</b>")

    channels_text = "\n".join(channel_info)
    await message.reply_text(f"<b>Fsub Channels are:\n</b>\n{channels_text}")
   

@Bot.on_message(filters.command('info'))
async def info_command(client: Client, message: Message):   
    command_parts = message.text.split(" ", 1)
    user_id = message.from_user.id
    is_user_admin = await is_admin(user_id)
    if not is_user_admin and user_id != OWNER_ID:       
        return
    if len(command_parts) != 2:
        await message.reply("Invalid command format. Use /info (link or base64_string)")
        return    
  
    input_string = command_parts[1]
       
    if input_string.startswith("https://t.me/"):    
        base64_string = input_string.split("?start=")[-1]
    else:    
        base64_string = input_string
          
    total_count = await total_click(base64_string)
        
    info_text = f"✨ Total Click: {total_count}"
    
    await message.reply(info_text)

@Bot.on_message(filters.command('ranking'))
async def leaderboard_command(client: Client, message: Message):
    user_id = message.from_user.id
    is_user_admin = await is_admin(user_id)
    if not is_user_admin and user_id != OWNER_ID:       
        return
    try:      
        top_users_list = await top_users()

        if top_users_list:
            leaderboard_text = "Top 10 Users:\n\n"
            for index, (user_id, total_clicks) in enumerate(top_users_list, start=1):                
                user = await client.get_users(user_id)
                first_name = user.first_name
               
                link = f"<a href='tg://openmessage?user_id={user_id}'>{first_name}</a>"
                leaderboard_text += f"{index}. {link} - Total Clicks: {total_clicks}\n"
        else:
            leaderboard_text = "Failed to retrieve leaderboard."

        await message.reply_text(leaderboard_text)
    except Exception as e:
        await message.reply_text(f"An error occurred: {e}")
        

@Bot.on_message(filters.command('broadcast') & filters.private)
async def send_text(client: Bot, message: Message):
    user_id = message.from_user.id
    is_user_admin = await is_admin(user_id)
    if not is_user_admin and user_id != OWNER_ID:        
        return
    if message.reply_to_message:
        query = await full_userbase()
        broadcast_msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0
        
        pls_wait = await message.reply("<i>Broadcast ho rha till then FUCK OFF </i>")
        for chat_id in query:
            try:
                await broadcast_msg.copy(chat_id)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.x)
                await broadcast_msg.copy(chat_id)
                successful += 1
            except UserIsBlocked:
                await del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                await del_user(chat_id)
                deleted += 1
            except:
                unsuccessful += 1
                pass
            total += 1
        
        status = f"""<b><u>Broadcast Completed</u>

Total Users: <code>{total}</code>
Successful: <code>{successful}</code>
Blocked Users: <code>{blocked}</code>
Deleted Accounts: <code>{deleted}</code>
Unsuccessful: <code>{unsuccessful}</code></b>"""
        
        return await pls_wait.edit(status)

    else:
        msg = await message.reply(REPLY_ERROR)
        await asyncio.sleep(8)
        await msg.delete()



@Bot.on_message(filters.command('restart'))
async def restart_bot(b, m):
    user_id = m.from_user.id
    is_user_admin = await is_admin(user_id)
    if not is_user_admin and user_id != OWNER_ID:       
        return
    restarting_message = await m.reply_text(f"⚡️<b><i>Restarting....</i></b>", disable_notification=True)

    # Wait for 3 seconds
    await asyncio.sleep(3)

    # Update message after the delay
    await restarting_message.edit_text("✅ <b><i>Successfully Restarted</i></b>")

    # Restart the bot
    os.execl(sys.executable, sys.executable, *sys.argv)


#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def auto_del_notification(client, msg, delay_time):
    await msg.reply_text(DEL_MSG.format(time=convert_time(DEL_TIMER))) 
    await asyncio.sleep(delay_time)
    await msg.delete()
    

async def delete_message(msg, delay_time):
    await asyncio.sleep(delay_time)    
    await msg.delete()
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

