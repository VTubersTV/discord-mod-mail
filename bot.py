import discord
from discord.ext import commands
import sqlite3
import os
import asyncio
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True
intents.guilds = True

bot = commands.Bot(command_prefix=os.getenv('BOT_PREFIX', '!'), intents=intents)

class ModMailDatabase:
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize the database with required tables"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create tickets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')

        # Create ticket_users table for multiple users per ticket
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ticket_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ticket_id) REFERENCES tickets (id),
                UNIQUE(ticket_id, user_id)
            )
        ''')

        # Create messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                is_from_user BOOLEAN NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ticket_id) REFERENCES tickets (id)
            )
        ''')

        conn.commit()
        conn.close()

    def create_ticket(self, user_id, channel_id):
        """Create a new support ticket"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO tickets (user_id, channel_id)
            VALUES (?, ?)
        ''', (user_id, channel_id))

        ticket_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return ticket_id

    def get_active_ticket(self, user_id):
        """Get the active ticket for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, channel_id FROM tickets
            WHERE user_id = ? AND is_active = 1
            ORDER BY created_at DESC
            LIMIT 1
        ''', (user_id,))

        result = cursor.fetchone()
        conn.close()

        return result

    def close_ticket(self, user_id):
        """Close the active ticket for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE tickets SET is_active = 0
            WHERE user_id = ? AND is_active = 1
        ''', (user_id,))

        conn.commit()
        conn.close()

    def update_ticket_channel(self, ticket_id, new_channel_id):
        """Update the channel ID for a ticket"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE tickets SET channel_id = ?
            WHERE id = ?
        ''', (new_channel_id, ticket_id))

        conn.commit()
        conn.close()

    def cleanup_invalid_tickets(self, support_category_id):
        """Close tickets that have invalid channel IDs (e.g., category IDs)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE tickets SET is_active = 0
            WHERE channel_id = ? AND is_active = 1
        ''', (support_category_id,))

        conn.commit()
        conn.close()

    def add_message(self, ticket_id, message_id, user_id, content, is_from_user):
        """Add a message to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO messages (ticket_id, message_id, user_id, content, is_from_user)
            VALUES (?, ?, ?, ?, ?)
        ''', (ticket_id, message_id, user_id, content, is_from_user))

        conn.commit()
        conn.close()

    def add_user_to_ticket(self, ticket_id, user_id):
        """Add a user to a ticket"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO ticket_users (ticket_id, user_id)
                VALUES (?, ?)
            ''', (ticket_id, user_id))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # User already in ticket
            return False
        finally:
            conn.close()

    def remove_user_from_ticket(self, ticket_id, user_id):
        """Remove a user from a ticket"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            DELETE FROM ticket_users
            WHERE ticket_id = ? AND user_id = ?
        ''', (ticket_id, user_id))

        conn.commit()
        conn.close()

    def get_ticket_users(self, ticket_id):
        """Get all users in a ticket"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT user_id FROM ticket_users
            WHERE ticket_id = ?
        ''', (ticket_id,))

        users = [row[0] for row in cursor.fetchall()]
        conn.close()

        return users

    def get_ticket_by_channel(self, channel_id):
        """Get ticket by channel ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, user_id FROM tickets
            WHERE channel_id = ? AND is_active = 1
            ORDER BY created_at DESC
            LIMIT 1
        ''', (channel_id,))

        result = cursor.fetchone()
        conn.close()

        return result

# Initialize database
db = ModMailDatabase(os.getenv('DATABASE_PATH', './data/modmail.db'))

def process_attachments(message):
    """Process message attachments and return formatted content"""
    if not message.attachments:
        return "", []

    attachment_text = ""
    files = []

    for attachment in message.attachments:
        # Check if it's an image
        if attachment.content_type and attachment.content_type.startswith('image/'):
            attachment_text += f"\n📷 **Image:** {attachment.filename}\n"
        else:
            attachment_text += f"\n📎 **File:** {attachment.filename}\n"

        files.append(attachment)

    return attachment_text, files

def create_embed_with_attachments(title, description, color, message, files=None):
    """Create an embed with attachment support"""
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.now(timezone.utc)
    )

    # Add attachment information if present
    if message.attachments:
        attachment_text, _ = process_attachments(message)
        if attachment_text:
            embed.add_field(name="Attachments", value=attachment_text, inline=False)

    return embed

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} guilds')

    # Clean up any invalid tickets (tickets with category IDs instead of channel IDs)
    support_category_id = int(os.getenv('SUPPORT_TICKET_PARENT'))
    db.cleanup_invalid_tickets(support_category_id)
    print("Cleaned up invalid tickets from database")

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # Handle DM messages
    if isinstance(message.channel, discord.DMChannel):
        await handle_dm_message(message)
    # Handle messages in support channels (any channel in the support category)
    elif (isinstance(message.channel, discord.TextChannel) and
          message.channel.category and
          message.channel.category.id == int(os.getenv('SUPPORT_TICKET_PARENT'))):
        await handle_support_channel_message(message)

    # Process commands
    await bot.process_commands(message)

async def handle_dm_message(message):
    """Handle direct messages from users"""
    user_id = message.author.id

    # Check if user has an active ticket
    ticket = db.get_active_ticket(user_id)

    if not ticket:
        # Create new ticket
        support_category_id = int(os.getenv('SUPPORT_TICKET_PARENT'))
        support_category = bot.get_channel(support_category_id)

        if not support_category or not isinstance(support_category, discord.CategoryChannel):
            await message.author.send("Error: Support category not found or invalid.")
            return

        # Create a new text channel for this ticket
        ticket_channel = await support_category.create_text_channel(
            name=f"ticket-{message.author.id}",
            topic=f"Support ticket for {message.author.mention} ({message.author.id})"
        )

        ticket_id = db.create_ticket(user_id, ticket_channel.id)

        # Add the original user to the ticket
        db.add_user_to_ticket(ticket_id, user_id)

        # Send initial message to support channel
        embed = create_embed_with_attachments(
            title="New Support Ticket",
            description=f"User: {message.author.mention} ({message.author.id})",
            color=0x00ff00,
            message=message
        )
        embed.add_field(name="Message", value=message.content or "*No text content*", inline=False)
        embed.set_footer(text=f"Ticket ID: {ticket_id}")

        # Send message with attachments if any
        if message.attachments:
            files = [await attachment.to_file() for attachment in message.attachments]
            sent_message = await ticket_channel.send(embed=embed, files=files)
        else:
            sent_message = await ticket_channel.send(embed=embed)

        # Store message in database
        db.add_message(ticket_id, sent_message.id, user_id, message.content, True)

        # Send confirmation to user
        await message.author.send("Your support ticket has been created! A staff member will respond soon.")
    else:
        # Forward message to support channel
        ticket_id, support_channel_id = ticket
        support_channel = bot.get_channel(support_channel_id)

        # Check if the stored channel is valid and is a text channel
        if support_channel and isinstance(support_channel, discord.TextChannel):
            embed = create_embed_with_attachments(
                title="Message from User",
                description=f"User: {message.author.mention} ({message.author.id})",
                color=0x0099ff,
                message=message
            )
            embed.add_field(name="Message", value=message.content or "*No text content*", inline=False)
            embed.set_footer(text=f"Ticket ID: {ticket_id}")

            # Send message with attachments if any
            if message.attachments:
                files = [await attachment.to_file() for attachment in message.attachments]
                sent_message = await support_channel.send(embed=embed, files=files)
            else:
                sent_message = await support_channel.send(embed=embed)

            # Store message in database
            db.add_message(ticket_id, sent_message.id, user_id, message.content, True)
        else:
            # If the stored channel is invalid (e.g., it's a category), create a new ticket
            await message.author.send("Your previous ticket channel is no longer available. Creating a new ticket...")

            # Create new ticket
            support_category_id = int(os.getenv('SUPPORT_TICKET_PARENT'))
            support_category = bot.get_channel(support_category_id)

            if not support_category or not isinstance(support_category, discord.CategoryChannel):
                await message.author.send("Error: Support category not found or invalid.")
                return

            # Create a new text channel for this ticket
            ticket_channel = await support_category.create_text_channel(
                name=f"ticket-{message.author.id}",
                topic=f"Support ticket for {message.author.mention} ({message.author.id})"
            )

            # Update the ticket with the new channel ID
            db.update_ticket_channel(ticket_id, ticket_channel.id)

            # Send initial message to support channel
            embed = create_embed_with_attachments(
                title="New Support Ticket (Recreated)",
                description=f"User: {message.author.mention} ({message.author.id})",
                color=0x00ff00,
                message=message
            )
            embed.add_field(name="Message", value=message.content or "*No text content*", inline=False)
            embed.set_footer(text=f"Ticket ID: {ticket_id}")

            # Send message with attachments if any
            if message.attachments:
                files = [await attachment.to_file() for attachment in message.attachments]
                sent_message = await ticket_channel.send(embed=embed, files=files)
            else:
                sent_message = await ticket_channel.send(embed=embed)

            # Store message in database
            db.add_message(ticket_id, sent_message.id, user_id, message.content, True)

            # Send confirmation to user
            await message.author.send("Your support ticket has been recreated! A staff member will respond soon.")

async def handle_support_channel_message(message):
    """Handle messages in the support channel"""
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # Get ticket information from the channel
    ticket = db.get_ticket_by_channel(message.channel.id)

    if not ticket:
        return  # Not a ticket channel

    ticket_id, user_id = ticket

    # Check if this is a reply to a ticket message
    if message.reference and message.reference.message_id:
        # Get the referenced message
        try:
            referenced_message = await message.channel.fetch_message(message.reference.message_id)

            # Extract ticket ID from the embed footer
            if referenced_message.embeds:
                embed = referenced_message.embeds[0]
                if embed.footer and embed.footer.text and 'Ticket ID:' in embed.footer.text:
                    ticket_id = int(embed.footer.text.split(': ')[1])

                    # Get all users in this ticket
                    ticket_users = db.get_ticket_users(ticket_id)

                    # Send message to all users in the ticket
                    for user_id in ticket_users:
                        try:
                            user = await bot.fetch_user(user_id)
                            embed = create_embed_with_attachments(
                                title="Staff Response",
                                description=message.content or "*No text content*",
                                color=0xff9900,
                                message=message
                            )
                            embed.set_footer(text="Reply to this message to continue the conversation")

                            try:
                                # Send message with attachments if any
                                if message.attachments:
                                    files = [await attachment.to_file() for attachment in message.attachments]
                                    await user.send(embed=embed, files=files)
                                else:
                                    await user.send(embed=embed)
                            except discord.Forbidden:
                                print(f"Could not send message to user {user_id}")
                        except discord.NotFound:
                            print(f"User {user_id} not found")
                        except Exception as e:
                            print(f"Error fetching user {user_id}: {e}")

                    # Store message in database for the first user (original ticket creator)
                    if ticket_users:
                        db.add_message(ticket_id, message.id, ticket_users[0], message.content, False)
        except Exception as e:
            print(f"Error handling support channel message reply: {e}")
    else:
        # Handle regular messages in ticket channels
        try:
            # Get all users in this ticket
            ticket_users = db.get_ticket_users(ticket_id)

            # Send message to all users in the ticket
            for user_id in ticket_users:
                try:
                    user = await bot.fetch_user(user_id)
                    embed = create_embed_with_attachments(
                        title="Staff Response",
                        description=message.content or "*No text content*",
                        color=0xff9900,
                        message=message
                    )
                    embed.set_footer(text="Reply to this message to continue the conversation")

                    try:
                        # Send message with attachments if any
                        if message.attachments:
                            files = [await attachment.to_file() for attachment in message.attachments]
                            await user.send(embed=embed, files=files)
                        else:
                            await user.send(embed=embed)
                    except discord.Forbidden:
                        print(f"Could not send message to user {user_id}")
                except discord.NotFound:
                    print(f"User {user_id} not found")
                except Exception as e:
                    print(f"Error fetching user {user_id}: {e}")

            # Store message in database for the first user (original ticket creator)
            if ticket_users:
                db.add_message(ticket_id, message.id, ticket_users[0], message.content, False)
        except Exception as e:
            print(f"Error handling support channel message: {e}")

@bot.command(name='close')
@commands.has_permissions(manage_messages=True)
async def close_ticket(ctx, user_id: int = None):
    """Close a support ticket and notify all users"""
    if user_id:
        # Get the ticket
        ticket = db.get_active_ticket(user_id)
        if ticket:
            ticket_id, _ = ticket
            # Get all users in the ticket
            ticket_users = db.get_ticket_users(ticket_id)

            # Close the ticket
            db.close_ticket(user_id)

            # Notify all users
            for uid in ticket_users:
                try:
                    user = await bot.fetch_user(uid)
                    embed = discord.Embed(
                        title="Support Ticket Closed",
                        description="Your support ticket has been closed by staff.",
                        color=0xff0000,
                        timestamp=datetime.now(timezone.utc)
                    )
                    await user.send(embed=embed)
                except discord.NotFound:
                    print(f"User {uid} not found for close notification")
                except discord.Forbidden:
                    print(f"Could not send close notification to user {uid}")
                except Exception as e:
                    print(f"Error fetching user {uid} for close notification: {e}")

            await ctx.send(f"Ticket for user {user_id} has been closed and all users have been notified.")
        else:
            await ctx.send(f"No active ticket found for user {user_id}.")
    else:
        # Try to close ticket in current channel
        ticket = db.get_ticket_by_channel(ctx.channel.id)
        if ticket:
            ticket_id, original_user_id = ticket
            # Get all users in the ticket
            ticket_users = db.get_ticket_users(ticket_id)

            # Close the ticket
            db.close_ticket(original_user_id)

            # Notify all users
            for uid in ticket_users:
                try:
                    user = await bot.fetch_user(uid)
                    embed = discord.Embed(
                        title="Support Ticket Closed",
                        description="Your support ticket has been closed by staff.",
                        color=0xff0000,
                        timestamp=datetime.now(timezone.utc)
                    )
                    await user.send(embed=embed)
                except discord.NotFound:
                    print(f"User {uid} not found for close notification")
                except discord.Forbidden:
                    print(f"Could not send close notification to user {uid}")
                except Exception as e:
                    print(f"Error fetching user {uid} for close notification: {e}")

            await ctx.send("This ticket has been closed and all users have been notified.")
        else:
            await ctx.send("No active ticket found in this channel. Please provide a user ID.")

@bot.command(name='tickets')
@commands.has_permissions(manage_messages=True)
async def list_tickets(ctx):
    """List all active tickets"""
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT user_id, channel_id, created_at FROM tickets
        WHERE is_active = 1
        ORDER BY created_at DESC
    ''')

    tickets = cursor.fetchall()
    conn.close()

    if not tickets:
        await ctx.send("No active tickets found.")
        return

    embed = discord.Embed(title="Active Tickets", color=0x00ff00)

    for ticket in tickets:
        user_id, channel_id, created_at = ticket
        try:
            user = await bot.fetch_user(user_id)
            username = user.display_name
        except discord.NotFound:
            username = f"Unknown User ({user_id})"
        except Exception as e:
            print(f"Error fetching user {user_id}: {e}")
            username = f"Unknown User ({user_id})"

        embed.add_field(
            name=f"User: {username}",
            value=f"User ID: {user_id}\nCreated: {created_at}",
            inline=False
        )

    await ctx.send(embed=embed)

@bot.command(name='adduser')
@commands.has_permissions(manage_messages=True)
async def add_user_to_ticket(ctx, user: discord.Member = None):
    """Add a user to the current support ticket"""
    if not user:
        await ctx.send("Please mention a user or provide their ID to add them to the ticket.")
        return

    # Get ticket for current channel
    ticket = db.get_ticket_by_channel(ctx.channel.id)
    if not ticket:
        await ctx.send("No active ticket found in this channel.")
        return

    ticket_id, _ = ticket

    # Add user to ticket
    success = db.add_user_to_ticket(ticket_id, user.id)

    if success:
        await ctx.send(f"✅ Added {user.mention} to the ticket.")

        # Notify the user
        try:
            embed = discord.Embed(
                title="Added to Support Ticket",
                description="You have been added to a support ticket. You will now receive all messages from staff.",
                color=0x00ff00,
                timestamp=datetime.now(timezone.utc)
            )
            await user.send(embed=embed)
        except discord.Forbidden:
            print(f"Could not send notification to user {user.id}")
    else:
        await ctx.send(f"❌ {user.mention} is already in this ticket.")

@bot.command(name='removeuser')
@commands.has_permissions(manage_messages=True)
async def remove_user_from_ticket(ctx, user: discord.Member = None):
    """Remove a user from the current support ticket"""
    if not user:
        await ctx.send("Please mention a user or provide their ID to remove them from the ticket.")
        return

    # Get ticket for current channel
    ticket = db.get_ticket_by_channel(ctx.channel.id)
    if not ticket:
        await ctx.send("No active ticket found in this channel.")
        return

    ticket_id, original_user_id = ticket

    # Don't allow removing the original ticket creator
    if user.id == original_user_id:
        await ctx.send("❌ Cannot remove the original ticket creator.")
        return

    # Remove user from ticket
    db.remove_user_from_ticket(ticket_id, user.id)

    await ctx.send(f"✅ Removed {user.mention} from the ticket.")

    # Notify the user
    try:
        embed = discord.Embed(
            title="Removed from Support Ticket",
            description="You have been removed from the support ticket and will no longer receive messages from staff.",
            color=0xff9900,
            timestamp=datetime.now(timezone.utc)
        )
        await user.send(embed=embed)
    except discord.Forbidden:
        print(f"Could not send notification to user {user.id}")

@bot.command(name='ticketinfo')
@commands.has_permissions(manage_messages=True)
async def ticket_info(ctx):
    """Show information about the current ticket"""
    ticket = db.get_ticket_by_channel(ctx.channel.id)
    if not ticket:
        await ctx.send("No active ticket found in this channel.")
        return

    ticket_id, original_user_id = ticket
    ticket_users = db.get_ticket_users(ticket_id)

    embed = discord.Embed(
        title="Ticket Information",
        color=0x0099ff,
        timestamp=datetime.now(timezone.utc)
    )

    # Add original user
    try:
        original_user = await bot.fetch_user(original_user_id)
        original_username = original_user.display_name
    except discord.NotFound:
        original_username = f"Unknown User ({original_user_id})"
    except Exception as e:
        print(f"Error fetching user {original_user_id}: {e}")
        original_username = f"Unknown User ({original_user_id})"

    embed.add_field(name="Original User", value=f"{original_username} ({original_user_id})", inline=False)

    # Add all users in ticket
    users_text = []
    for user_id in ticket_users:
        try:
            user = await bot.fetch_user(user_id)
            username = user.display_name
        except discord.NotFound:
            username = f"Unknown User ({user_id})"
        except Exception as e:
            print(f"Error fetching user {user_id}: {e}")
            username = f"Unknown User ({user_id})"
        users_text.append(f"• {username} ({user_id})")

    embed.add_field(name="Users in Ticket", value="\n".join(users_text) if users_text else "No users", inline=False)
    embed.set_footer(text=f"Ticket ID: {ticket_id}")

    await ctx.send(embed=embed)

if __name__ == "__main__":
    # Check if required environment variables are set
    if not os.getenv('DISCORD_TOKEN'):
        print("Error: DISCORD_TOKEN not found in environment variables")
        exit(1)

    if not os.getenv('SUPPORT_TICKET_PARENT'):
        print("Error: SUPPORT_TICKET_PARENT not found in environment variables")
        exit(1)

    # Run the bot
    bot.run(os.getenv('DISCORD_TOKEN'))
