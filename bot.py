#! /usr/bin/python
import random
import discord
import sys
__version__ = "0.2.8"

piazza_schedule_link = "<https://piazza.com/class/kszba47ze8v47t?cid=8>"

lastQueue = ""  # Keep track of the last output from queue to prevent students spamming !S when it hasn't updated

def isTA(usr: discord.Member):
    roles:list[discord.Role] = usr.roles

    # Exception
    special_roles = {"ex-ta"}
    for x in roles:
        if x.permissions.kick_members or x.name.lower() in special_roles:
            return True
    return False


def sanitizeString(s):
    needToEscape = ["*", "`", "~", "_", ">", "|", ":", "/", "."]  # Characters that need to have an excape character placed in front of them
    # Update: We can actually just escape all of those.
    # needToRemove = []  # Characters that need to be replaced with a space
    for char in needToEscape:
        s = s.replace(char, "\\" + char)
    # for char in needToRemove:
    #     s = s.replace(char, " ")
    while "  " in s:  # Remove double spaces
        s = s.replace("  ", " ")
    return s


# Gets the username if they have one, otherwise their Discord name
def getDisplayName(user):
    nickname = user.nick
    username = sanitizeString(user.name)
    if nickname:
        return sanitizeString(nickname)
    else:
        return username


def printQ(q):
    st = "Students in the queue:\n"
    for x, ele in enumerate(q):
        studentDisplayName = getDisplayName(ele)
        st += "{}. {}\n".format(x + 1, studentDisplayName)
    return st


client = discord.Client()
id_to_list = {}  # string->List dictionary


# Set the bot's Discord status to "Watching ..."
async def setBotStatus(message: str):
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=message))
    print("Set bot status to 'Watching {}'".format(message))


# Open or close office hours with appropriate bot messages, channel settings, and bot status
# isOpen is the new office hours status
# sender is the person who sent the command
# channel is the channel the command was sent in
async def setOfficeHoursOpenStatus(isOpen: bool, sender, channel):
    # From https://stackoverflow.com/questions/63402412/how-to-check-a-permission-value-of-a-text-channel-discord-py
    wasOpen: bool = channel.overwrites_for(channel.guild.default_role).send_messages  # Was office hours previously open before calling this function?
    if wasOpen == None:
        # Wow, this was an annoying "intended feature" to find. If the boolean is somehow "None" then it doesn't have an explicitly allowed or denied permission
        # https://discordpy.readthedocs.io/en/latest/api.html#discord.PermissionOverwrite
        wasOpen = True  # We'll consider it as open if it isn't explicitly closed

    if isOpen == wasOpen:  # No change to make
        await channel.send("Hey there, {}! You might not have noticed this, but office hours are already {}.".format(sender.mention, ["closed", "open"][isOpen]))
        return

    else:
        if isOpen:
            await channel.set_permissions(channel.guild.default_role, send_messages=True)
            await channel.send("**Office Hours are now OPEN!**")
            await setBotStatus("Office Hours Open!")
        else:
            # Closing Office Hours
            # The queue is actually cleared right with the `!C` command
            await channel.set_permissions(channel.guild.default_role, send_messages=False)
            await channel.send("**Office Hours are now CLOSED!**\nYou can view the Office Hours schedule on Piazza here: {}\nA TA can open office hours with `!O`\nOnce office hours are open, you'll be able to send `!E` in this channel to join the queue.".format(piazza_schedule_link))
            await setBotStatus("Office Hours Closed!")


async def updateStatusToQueueLength(waitingStudentsCount: int):
    studentsPlural = "student" if waitingStudentsCount == 1 else "students"
    await setBotStatus("{} {} in queue".format(waitingStudentsCount, studentsPlural))


@client.event
async def on_ready():  # onready is called after all guilds are added to client
    print('Bot logged in as {0.user}'.format(client))
    await setBotStatus("Netflix until you send an open/close command in a valid channel")


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
                    msg = "{} you were already in the queue!".format(name)
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
                    await updateStatusToQueueLength(len(queue))
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
                    await updateStatusToQueueLength(len(queue))
                else:
                    msg = "{}, according to my records, you were already not in the queue.".format(name)
                    await message.channel.send(msg)
            else:
                # leave called before any enqueues
                # print("edge case")
                msg = "{}, according to my records, you were already not in the queue.".format(name)
                await message.channel.send(msg)

        if message.content.startswith('!p') or message.content.startswith('!P'):
            msg = "Here's the Office Hours schedule on Piazza. {}".format(piazza_schedule_link)
            await message.channel.send(msg)

        #               dequeue: TA only
        if (message.content.lower().startswith('!d')) and isTA(message.author):
            ta = message.author.mention
            taName = getDisplayName(message.author)
            actionString = "Please join the `general` voice channel and wait for {taName} to pull you into a private voice channel."
            if message.content.lower().startswith('!dm'):
                actionString = "Please wait for {taName} to send you a direct message."
            if thisid in id_to_list:
                queue = id_to_list[thisid]
                if len(queue) > 0:
                    stu = queue.pop(0)
                    msg = "{}, you are next! {} is available to help you now!\n{}".format(stu.mention, ta, actionString.format(taName=taName))
                    await message.channel.send(msg)
                    await updateStatusToQueueLength(len(queue))
                else:
                    # no one in queue
                    msg = "Good job TAs! The Queue is empty!"
                    await message.channel.send(msg)
            else:
                # called before anyone enqueued
                msg = "Good job TAs! The Queue is empty!"
                await message.channel.send(msg)

        #           Close office hours: TA only
        if (message.content.startswith('!c') or message.content.startswith('!C')) and isTA(message.author):
            await setOfficeHoursOpenStatus(False, message.author, message.channel)
            id_to_list[thisid] = []  # Clear the queue
            # msg = "Cleared the queue."
            # await message.channel.send(msg)

        if (message.content.startswith('!o') or message.content.startswith('!O')) and isTA(message.author):
            await setOfficeHoursOpenStatus(True, message.author, message.channel)

        #              show queue
        if message.content.startswith('!s') or message.content.startswith('!S'):
            if thisid in id_to_list:
                queue = id_to_list[thisid]
                currentQueue = printQ(queue)
                global lastQueue
                if queue:
                    if lastQueue == currentQueue:
                        # Queue hasn't changed
                        if isTA(message.author):  # But this is a TA, so we'll send it anyway
                            msg = "Hey {studentMention}, the queue hasn't updated since the last time it was checked, but since you're a TA, I'll be nice :smiley_cat:\n{currentQueue}".format(studentMention=message.author.mention, currentQueue=currentQueue)
                        else:  # Not a TA and queue hasn't changed
                            msg = "Hey {studentMention}, the queue hasn't updated since the last time it was checked. Please be patient.".format(studentMention=message.author.mention)
                    else:
                        msg = currentQueue
                        lastQueue = currentQueue

                    await message.channel.send(msg)
                else:
                    lastQueue = ""
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
                  "`!H` to view this **help** menu\n" \
                  "__Commands For TAs__\n" \
                  "`!D` or `!DM` to **dequeue** the next student\n" \
                  "`!O` to **open** office hours\n" \
                  "`!C` to **close** office hours and empty the queue\n" \
                  "__About__ discord-office-hours v. {ver}\n" \
                  "Commands are not case sensitive, and only the beginning of your message is checked.".format(
                ver=__version__)
            await message.channel.send(msg)

    # Allow these in any channel now

    # Only for TAs or Ex-TA
    if isTA(message.author):
        msgLower = message.content.lower()
        if message.content.lower().startswith('!panik'):
                await message.channel.send(
                    "https://media.discordapp.net/attachments/542843013559353344/692393206205251744/PANIK.gif")

        # A better way by Nicholas:
        negativeWords = ["bad", "not good", "terrible", "awful", "no good", "wrong", "incorrect", "not correct"]
        positiveWords = ["good", "awesome", "nice", "cool", "correct", "right", "fantastic", "great", "outstanding", "amazing"]
        negativeResponses = ["Hisssss", "Grrrrr", ":pouting_cat:", ":scream_cat:"]
        positiveResponses = ["Purr", "Purrrrr", "Meow", ":cat:", ":heart_eyes_cat:", ":smiley_cat:", ":smile_cat:"]

        # A TA is talking about the bot
        if any(word in msgLower for word in ["gandalf", "bot"]):
            if any(word in msgLower for word in negativeWords):  # It's negative:
                await message.channel.send(random.choice(negativeResponses))
            elif any(word in msgLower for word in positiveWords):  # It's positive
                await message.channel.send(random.choice(positiveResponses))


if __name__ == "__main__":
    mytoken = sys.argv[1]
    client.run(mytoken)  # TODO: system env to run from a bat script to keep my token safe online
