#! /usr/bin/python
import random
import discord
import sys

__version__ = "0.2.1"


def isTA(usr: discord.Member):
    roles = usr.roles
    for x in roles:
        if x.name.upper() == "CSE 116 TA":
            return True
    return False


def sanitizeString(s):
    needToEscape = ["*", "`", "~", "_", ">", "|",
                    ":"]  # Characters that need to have an excape character placed in front of them
    needToRemove = ["\\", "/", "."]  # Characters that need to be replaced with a space
    for char in needToEscape:
        s = s.replace(char, "\\" + char)
    for char in needToRemove:
        s = s.replace(char, " ")
    while "  " in s:  # Remove double spaces
        s = s.replace("  ", " ")
    return s


def printQ(q):
    st = "Students in the queue:\n"
    for x, ele in enumerate(q):
        nickname = ele.nick
        username = sanitizeString(ele.name)  # Sanitize input to prevent formatting
        if nickname:
            nickname = sanitizeString(nickname)
            st += "{}. {}\n".format(x + 1, nickname)
        else:
            st += "{}. {}\n".format(x + 1, username)
    return st


client = discord.Client()
id_to_list = {}  # string->List dictionary


@client.event
async def on_ready():  # onready is called after all guilds are added to client
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    global id_to_list
    thisid = str(message.guild.id)
    if message.author == client.user:
        return  # prevents infinite loops of reading own message

    if message.channel.name == "office-hours-queue":  # only want messages in OH

        #               enqueue
        if message.content.startswith('!e') or message.content.startswith('!E'):
            stu = message.author
            name = stu.mention
            if thisid in id_to_list:
                queue = id_to_list[thisid]
                if stu in queue:
                    queue.remove(stu)
                    queue.append(stu)
                    msg = "{} you were already in the list! You have been moved to the back.".format(name)
                    await message.channel.send(msg)
                else:
                    if len(queue) == 0:
                        msg = "{} you have been successfully added to the queue, and you are first in line!".format(
                            name)
                        queue.append(stu)
                        await message.channel.send(msg)
                    else:
                        queue.append(stu)
                        msg = "{} you have been successfully added to the queue in position: {}".format(name,
                                                                                                        len(queue))
                        await message.channel.send(msg)
            else:
                queue = [stu]
                id_to_list[thisid] = queue
                msg = "{} you have been successfully added to the queue, and you are next!".format(name)
                await message.channel.send(msg)

        #               leave queue
        if message.content.startswith('!l') or message.content.startswith('!L'):
            stu = message.author
            name = stu.mention
            if thisid in id_to_list:
                queue = id_to_list[thisid]
                if stu in queue:
                    queue.remove(stu)
                    msg = "{} you have successfully removed yourself from the queue.".format(name)
                    await message.channel.send(msg)
                else:
                    msg = "{}, according to my records, you were already not in the queue.".format(name)
                    await message.channel.send(msg)
            else:
                # leave called before any enqueues
                print("edge case")
                msg = "{}, according to my records, you were already not in the queue.".format(name)
                await message.channel.send(msg)

        if message.content.startswith('!p') or message.content.startswith('!P'):
            msg = "Here's the Office Hours schedule on Piazza. https://piazza.com/class/kk305idk4vd72?cid=6"
            await message.channel.send(msg)

        if message.content.startswith('!g') or message.content.startswith('!G'):    # output github repo link
            msg = "https://github.com/0xJonR/discord-office-hours"
            await message.channel.send(msg)

        #               dequeue: TA only
        if (message.content.startswith('!d') or message.content.startswith('!D')) and isTA(message.author):
            ta = message.author.mention
            if thisid in id_to_list:
                queue = id_to_list[thisid]
                if len(queue) > 0:
                    stu = queue.pop(0)
                    msg = "{}, you are next! {} is available to help you now!".format(stu.mention, ta)
                    await message.channel.send(msg)
                else:
                    # no one in queue
                    msg = "Good job TAs! The Queue is empty!"
                    await message.channel.send(msg)
            else:
                # called before anyone enqueued
                msg = "Good job TAs! The Queue is empty!"
                await message.channel.send(msg)

        #           Clear queue: TA only
        if (message.content.startswith('!c') or message.content.startswith('!C')) and isTA(message.author):
            id_to_list[thisid] = []
            msg = "Cleared the queue."
            await message.channel.send(msg)

        #              show queue
        if message.content.startswith('!s') or message.content.startswith('!S'):
            if thisid in id_to_list:
                queue = id_to_list[thisid]
                if queue:
                    # printQ
                    msg = printQ(queue)
                    await message.channel.send(msg)
                else:
                    msg = "The queue is empty right now."
                    await message.channel.send(msg)
            else:
                msg = "The queue is empty right now."
                id_to_list[thisid] = []
                await message.channel.send(msg)

        # help
        if message.content.startswith('!h') or message.content.startswith('!H'):
            msg = "__Commands For Students__\n" \
                  "`!E` to **enter** the queue\n" \
                  "`!S` to **show** the queue\n" \
                  "`!L` to **leave** the queue\n" \
                  "`!P` to view the office hours schedule on **Piazza**\n" \
                  "`!G` to view the Github Repo\n" \
                  "`!H` to view this **help** menu\n" \
                  "__Commands For TAs__\n" \
                  "`!D` to **dequeue** the next student\n" \
                  "`!C` to **clear** the queue\n" \
                  "__About__ discord-office-hours v. {ver}\n" \
                  "Commands are not case sensitive, and only the beginning of your message is checked.".format(
                ver=__version__)
            await message.channel.send(msg)


    else:  # Not in office hours channel
        if isTA(message.author):  # Other fun stuff for only TAs because we don't want to spam the server
            taMessage = message.content.lower()
            if taMessage.startswith('!panik'):
                    await message.channel.send(
                        "https://media.discordapp.net/attachments/542843013559353344/692393206205251744/PANIK.gif")

            if taMessage.startswith("!pet"):
                possibilities = ["Purr", "Purrrrr", "Meow", "😹"]
                await message.channel.send(random.choice(possibilities))

            if "bad" in taMessage and "gandalf" in taMessage or "bot" in taMessage:
                await message.channel.send("Hisssss")

            # From Rin:
            if "good" in taMessage and "gandalf" in taMessage or "bot" in taMessage:
                possibilities = ["Purr", "Purrrrr", "Meow"]
                await message.channel.send(random.choice(possibilities))

            # if "good" in message.content.lower() and "bot" in message.content.lower():
            #     possibilities = ["Purr", "Purrrrr", "Meow"]
            #     await message.channel.send(random.choice(possibilities))

if __name__ == "__main__":
    mytoken = sys.argv[1]
    client.run(mytoken)  # TODO: system env to run from a bat script to keep my token safe online
    main()
