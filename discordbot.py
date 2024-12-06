from discord.ext import commands
import sqlite3
import random
import discord
from datetime import datetime
import math
import multiprocessing
import time

intents = discord.Intents.default()
intents.members = True
client = commands.Bot(command_prefix=";", intents=intents)
db = sqlite3.connect('discordbot.db')
cursor = db.cursor()
client.remove_command("help")


def stock_fluctuate():
    print("Fluctuating")
    while True:
        databases = sqlite3.connect('discordbot.db')
        cursors = databases.cursor()
        cursors.execute('CREATE TABLE IF NOT EXISTS stock(name, amount, percent)')
        floatval = random.uniform(-0.02, 0.02)
        cursors.execute('SELECT amount FROM stock WHERE name = ?', ("DiscordBots",))
        result = cursors.fetchone()
        result = float(result[0]) * (1 + round(floatval, 3))
        print(floatval)
        print(result)
        percentage = str(round(floatval, 3) * 100)[0:5]
        if percentage.startswith("-"):
            percentage = percentage
        else:
            percentage = "+" + percentage
        if round(result) <= 1:
            result = 1
        cursors.execute('UPDATE stock SET amount = ?, percent = ? WHERE name = ?', (round(result), percentage, "DiscordBots"))
        databases.commit()
        databases.close()
        time.sleep(60)


def bot_main():


    def make_account(id):
        print("Made account with id ", id)
        cursor.execute('INSERT INTO main(id, money) VALUES(?,?)', (id, 5000))
        db.commit()
        return 5000


    @client.command()
    async def buystock(ctx, name, amount):
        account = get_account(ctx.author.id)
        if name.lower() == "discordbots":
            name = "DiscordBots"
        cursor.execute('SELECT amount FROM stock WHERE name = ?', (name,))
        cost = cursor.fetchone()[0]
        totalcost = int(amount)*int(cost)
        if int(totalcost) > int(account):
            await ctx.send(f"You can not afford that much stock, the transaction would "
                           f"cost ${totalcost} but you only have ${account}")
        else:
            newaccount = account-totalcost
            await ctx.send(f"You bought {amount} shares in {name} for ${totalcost}\n"
                           f"New total: ${newaccount}")
            if name == "DiscordBots":
                cursor.execute('SELECT DiscordBots FROM main WHERE id = ?', (ctx.author.id,))
            count = cursor.fetchone()
            print(count)
            if count[0]:
                oldtotal = count[0].split(" ")[0]
                oldcost = count[0].split(" ")[1]
                oldcost = int(oldcost)
                oldtotal = int(oldtotal)
                oldcost += totalcost
                oldtotal += int(amount)
                newstring = f"{oldtotal} {oldcost}"
            else:
                newstring = f"{amount} {totalcost}"
            if name == "DiscordBots":
                cursor.execute('UPDATE main SET money = ?, DiscordBots = ? WHERE id = ?',
                               (newaccount, newstring, ctx.author.id,))
                db.commit()


    @client.command()
    async def stock(ctx, name):
        embed = discord.Embed(title="Simulated Stock Market")
        if name.lower() == "discordbots":
            databases = sqlite3.connect('discordbot.db')
            cursors = databases.cursor()
            cursors.execute('SELECT * FROM stock WHERE name = ?', ("DiscordBots",))
            result = cursors.fetchone()
            embed.description = f"DiscordBots:\n**${result[1]}** {result[2]}%"
            await ctx.send(embed=embed)
            databases.close()


    @client.command()
    async def makestock(ctx, name, value):
        if ctx.author.id == 803766890023354438:
            databases = sqlite3.connect('discordbot.db')
            cursors = databases.cursor()
            cursors.execute('CREATE TABLE IF NOT EXISTS stock(name, amount, percent)')
            cursors.execute('INSERT INTO stock(amount, name) VALUES(?, ?)', (value, name,))
            databases.commit()
            databases.close()


    def get_account(id):
        cursor.execute('SELECT money FROM main WHERE id = ?', (id,))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return make_account(id)


    @client.command()
    async def sellstock(ctx, name, amount):
        if name.lower() == "discordbots":
            cursor.execute('SELECT DiscordBots FROM main WHERE id = ?', (ctx.author.id,))
            result = cursor.fetchone()
            if not result[0]:
                await ctx.send(f"You have no shares for DiscordBots")
            else:
                stock = int(result[0].split(" ")[0])
                if int(amount) <= stock:
                    cursor.execute('SELECT amount FROM stock WHERE name = ?', ("DiscordBots",))
                    cost = cursor.fetchone()[0]
                    cost = int(cost)
                    moneygained = int(cost)*int(amount)
                    account = get_account(ctx.author.id)
                    stock -= int(amount)
                    cursor.execute('UPDATE main SET money = ?, DiscordBots = ? WHERE id = ?',
                                   (int(account)+int(moneygained),
                                    f"{stock} {result[0].split(' ')[1]}",
                                    ctx.author.id,))
                    await ctx.send(f"Sold {amount} shares for DiscordBots for ${moneygained}\n"
                                   f"New Total: ${int(account)+int(moneygained)}")
                else:
                    await ctx.send("You do not own that many shares for DiscordBots")


    @client.command(aliases=['i', 'inv'])
    async def inventory(ctx):
        embed = discord.Embed(title=f"{ctx.author.display_name}'s Inventory")
        cursor.execute('SELECT DiscordBots FROM main WHERE id = ?', (ctx.author.id,))
        result = cursor.fetchone()
        if not result[0]:
            result[0] = "0 0"
        embed.description = f"DiscordBots\n{result[0].split(' ')[0]} Shares\n" \
                            f"${result[0].split(' ')[1]} Spent"
        await ctx.send(embed=embed)


    @client.command()
    async def howmany(ctx, role: discord.Role):
        count = 0
        members = ""
        guild = ctx.message.guild
        for member in guild.members:
            if role in member.roles:
                count += 1
                members += " " + member.display_name
        await ctx.send(str(count) + " people have this role")
        await ctx.send(members)


    @client.command()
    async def daily(ctx):
        time = datetime.now()
        account = get_account(ctx.author.id)
        cursor.execute('SELECT daily FROM main WHERE id = ?', (ctx.author.id,))
        result = cursor.fetchone()
        embed = discord.Embed(color=0xff99ff, title="Daily Reward", description="You got $1000 as a daily reward"
                                                                                "\nDon't spend it all in one place"
                                                                                f"\nNew Total: ${account+1000}")
        if result[0]:
            oldtime = datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S.%f')
            difference = time-oldtime
            if difference.total_seconds() >= 86400:
                await ctx.send(embed=embed)
                account += 1000
                cursor.execute('UPDATE main SET money = ?, daily = ? WHERE id = ?', (account, time, ctx.author.id,))
                db.commit()
            else:
                seconds = round(86400 - difference.total_seconds())
                embed.title = "Command on Cooldown"
                embed.description = f"Please wait another {math.floor(math.floor(seconds/60)/60)%60}h " \
                                    f"{math.floor(seconds/60)%60}m {seconds%60}s"
                await ctx.send(embed=embed)
        else:
            await ctx.send(embed=embed)
            account += 1000
            cursor.execute('UPDATE main SET money = ?, daily = ? WHERE id = ?', (account, time, ctx.author.id,))
            db.commit()


    @client.command(aliases=['top'])
    async def rich(ctx):
        count = 0
        dictionary = {1: ":first_place:", 2: ":second_place:", 3: ":third_place:", 4: ":four:", 5: ":five:"}
        embed = discord.Embed(title="Richest Users", description="", color=0x99ff99)
        cursor.execute('SELECT * FROM main ORDER BY money DESC LIMIT 5')
        result = cursor.fetchall()
        for user in result:
            count += 1
            defined = client.get_user(user[0])
            embed.description = embed.description + dictionary[count] + " " + defined.name + "#" + \
                                str(defined.discriminator) + ": **$" + str(user[1]) + "**\n"
        await ctx.send(embed=embed)


    @client.command()
    async def nick(ctx, *, name):
        if ctx.author.id == 803766890023354438:
            await ctx.message.delete()
            user = client.get_guild(ctx.guild.id).get_member(803995408891117568)
            await user.edit(nick=name)


    @client.command()
    async def help(ctx, command=None):
        if command == None:
            embed = discord.Embed(title="Help Command", color=0xFFC0CB)
            embed.add_field(name=";blackjack (amount)", value="Play a game of blackjack with a bot, lonely")
            embed.add_field(name=";balance", value="Check out your balance for the currency commands")
            embed.add_field(name=";rich", value="Get the top 5 richest players!")
            embed.add_field(name=";daily", value="Get $1000 daily")
        elif command.lower() == "blackjack" or command.lower() == "bj":
            embed = discord.Embed(title="Blackjack Command",
                                  description="EX: ;blackjack 100\nGambles the specified amount to play a simple game of blackjack with a bot",
                                  color=0xFFC0CB)
        elif command.lower() == "bal" or command.lower() == "balance":
            embed = discord.Embed(title="Balance Command",
                                  description="EX: ;balance\nGets the balance of yourself or an optional user",
                                  color=0xFFC0CB)
        elif command.lower() == "daily":
            embed = discord.Embed(title="Daily Command",
                                  description="EX: ;daily\nGet $100 daily, this resets every 24h since you ran the command",
                                  color=0xFFC0CB)
        await ctx.send(embed=embed)


    @client.event
    async def on_ready():
        message = await client.get_guild(803675559552483419).get_channel(813477675502796830).fetch_message(813478929087856660)
        await message.delete()
        print("Ready!")
        cursor.execute('CREATE TABLE IF NOT EXISTS main(id, money, daily, weekly, DiscordBots)')
        db.commit()
        await client.change_presence(activity=discord.Game(";help"))



    def deal(id=None):
        card = random.randint(1, 13)
        if card == 1:
            final = "A"
        elif card == 11:
            final = "J"
        elif card == 12:
            final = "Q"
        elif card == 13:
            final = "K"
        else:
            final = card
        if card > 10:
            card = 10
        if card == 1:
            card = 11
        return [final, card]


    @client.command(aliases=['bal'])
    async def balance(ctx, user=None):
        if not user:
            author = ctx.author
        else:
            author = await client.get_user(user.split("<@!")[1].split(">")[0])
        embed = discord.Embed(title=f"{author.name}'s Balance", description="$" + str(get_account(author.id)),
                              color=0x99ff99)
        await ctx.send(embed=embed)


    @client.after_invoke
    async def database(ctx):
        global db, cursor
        db.commit()
        db.close()
        db = sqlite3.connect('discordbot.db')
        cursor = db.cursor()


    @client.command()
    async def sql(ctx, *, args):
        if ctx.author.id == 803766890023354438:
            cursor.execute(args)
            result = cursor.fetchall()
            if result:
                print(result)
                await ctx.send(result)
            else:
                await ctx.send("Done")


    @client.command(aliases=['bj'])
    async def blackjack(ctx, amount=None):
        if amount:
            result = get_account(ctx.author.id)
            if amount == "all" or amount == "a":
                amount = result
            if int(amount) <= result:
                amount = str(amount)
                aces, totalaces = 0, 0
                embed = discord.Embed(title=f"{ctx.author.display_name}'s Blackjack Game $" + amount, color=0xc1c0ff)
                author = ctx.author.id
                pcard1 = deal()
                pcard2 = deal()
                playertotal = pcard1[1] + pcard2[1]
                cards = f"{str(pcard1[0])} {str(pcard2[0])}"
                embed.add_field(name="Your Hand", value=f"**{str(pcard1[0])} {str(pcard2[0])}**\nTotal: {str(playertotal)}",
                                inline=False)
                card1 = deal()
                card2 = deal()
                total = card1[1] + card2[1]
                dcards = f"{str(card1[0])} {str(card2[0])}"
                embed.add_field(name="Dealer's Hand", value=f"**{str(card1[0])} ?**\nTotal: ?", inline=False)
                message = await ctx.send(embed=embed)
                await message.add_reaction("🇭")
                await message.add_reaction("🇸")

                def check(reaction, user):
                    return reaction.message.id == message.id and str(reaction.emoji) == '🇭' and user.id == ctx.author.id or \
                           reaction.message == message and str(reaction.emoji) == "🇸" and user.id == ctx.author.id

                wait = await client.wait_for('reaction_add', check=check)
                if wait[0].emoji == "🇸":
                    while total < 17:
                        aces, totalaces = 0, 0
                        if "A" in dcards:
                            for character in dcards:
                                if character == "A":
                                    totalaces += 1
                            if aces < totalaces:
                                aces += 1
                                total -= 10
                                totalaces = 0
                        card3 = deal()
                        total += card3[1]
                        dcards += f" {card3[0]}"
                    embed.set_field_at(1, name="Dealer's Hand",
                                       value=f"**{dcards}**\nTotal: {str(total)}", inline=False)
                    await message.remove_reaction(wait[0], ctx.author)
                    if int(playertotal) < int(total):
                        if int(total) < 22:
                            embed.title = "You lost"
                            embed.set_field_at(0, name="~~Your Hand~~",
                                               value=f"~~**{cards}**~~\n~~Total: {str(playertotal)}~~")
                            cursor.execute('UPDATE main SET money = ? WHERE id = ?',
                                           (result - int(amount), ctx.author.id,))
                        elif int(total) >= 22:
                            embed.title = "You won $" + amount
                            embed.set_field_at(1, name="~~Dealer's Hand~~",
                                               value=f"~~**{dcards}**~~\n~~Total: {str(total)}~~", inline=False)
                            cursor.execute('UPDATE main SET money = ? WHERE id = ?', (result + int(amount), ctx.author.id,))
                        db.commit()
                    elif int(total) < int(playertotal):
                        embed.title = "You won $" + amount
                        embed.set_field_at(1, name="~~Dealer's Hand~~",
                                           value=f"~~**{dcards}**~~\n~~Total: {str(total)}~~", inline=False)
                        cursor.execute('UPDATE main SET money = ? WHERE id = ?', (result + int(amount), ctx.author.id,))
                        db.commit()
                    elif int(total) == int(playertotal):
                        embed.title = 'Tied :/'
                    await message.edit(embed=embed)
                elif wait[0].emoji == "🇭":
                    overkill = False
                    while not overkill:
                        if wait[0].emoji == "🇭":
                            await message.remove_reaction(wait[0], ctx.author)
                            card3 = deal()
                            playertotal += card3[1]
                            cards += f" {str(card3[0])}"
                            if playertotal <= 21:
                                embed.set_field_at(0, name="Your Hand",
                                                   value=f"**{cards}**\nTotal: {str(playertotal)}")
                            else:
                                if "A" in cards:
                                    for character in cards:
                                        if character == "A":
                                            totalaces += 1
                                    if aces < totalaces:
                                        aces += 1
                                        playertotal -= 10
                                        totalaces = 0
                                        embed.set_field_at(0, name="Your Hand",
                                                           value=f"**{cards}**\nTotal: {str(playertotal)}")
                                if playertotal >= 21:
                                    overkill = True
                                    embed.set_field_at(0, name="~~Your Hand~~",
                                                       value=f"~~**{cards}**~~\n~~Total: {str(playertotal)}~~")
                                    embed.title = "You lost $" + amount
                                    embed.set_field_at(1, name="Dealer's Hand",
                                                       value=f"**{dcards}**\nTotal: {str(total)}",
                                                       inline=False)
                                    cursor.execute('UPDATE main SET money = ? WHERE id = ?',
                                                   (result - int(amount), ctx.author.id,))
                                    db.commit()
                            await message.edit(embed=embed)
                            wait = await client.wait_for('reaction_add', check=check)
                        elif wait[0].emoji == "🇸":
                            totalaces, aces = 0, 0
                            overkill = True
                            while total < 17:
                                if "A" in dcards:
                                    for character in dcards:
                                        if character == "A":
                                            totalaces += 1
                                    if aces < totalaces:
                                        aces += 1
                                        total -= 10
                                        totalaces = 0
                                card3 = deal()
                                total += card3[1]
                                dcards += f" {card3[0]}"
                            embed.set_field_at(1, name="Dealer's Hand",
                                               value=f"**{dcards}**\nTotal: {str(total)}", inline=False)
                            await message.remove_reaction(wait[0], ctx.author)
                            if int(playertotal) < int(total):
                                if int(total) < 22:
                                    embed.title = "You lost $" + amount
                                    embed.set_field_at(0, name="~~Your Hand~~",
                                                       value=f"~~**{cards}**~~\n~~Total: {str(playertotal)}~~")
                                    cursor.execute('UPDATE main SET money = ? WHERE id = ?',
                                                   (result - int(amount), ctx.author.id,))
                                if int(total) >= 22:
                                    embed.title = "You won $" + amount
                                    embed.set_field_at(1, name="~~Dealer's Hand~~",
                                                       value=f"~~**{dcards}**~~\n~~Total: {str(total)}~~",
                                                       inline=False)
                                    cursor.execute('UPDATE main SET money = ? WHERE id = ?',
                                                   (result + int(amount), ctx.author.id,))
                                db.commit()
                            elif int(total) < int(playertotal):
                                embed.title = "You won $" + amount
                                embed.set_field_at(1, name="~~Dealer's Hand~~",
                                                   value=f"~~**{dcards}**~~\n~~Total: {str(total)}~~",
                                                   inline=False)
                                cursor.execute('UPDATE main SET money = ? WHERE id = ?',
                                               (result + int(amount), ctx.author.id,))
                                db.commit()
                            elif int(total) == int(playertotal):
                                embed.title = 'Tied :/'
                            await message.edit(embed=embed)
            else:
                await ctx.send("That is more money than you have, you only have $" + str(result))
        else:
            await ctx.send("Please specify an amount")


    client.run("token")


if __name__ == '__main__':
    thread = multiprocessing.Process(target=stock_fluctuate)
    thread2 = multiprocessing.Process(target=bot_main)
    thread.start()
    thread2.start()
