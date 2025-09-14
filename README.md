# Discord Mod Mail Bot

A Discord bot that allows users to send direct messages to create support tickets. Staff can respond to tickets in a designated support channel, and messages are automatically forwarded between users and staff.

## Features

- **Direct Message Support**: Users can DM the bot to create support tickets
- **Automatic Ticket Creation**: Creates tickets in a designated support channel
- **Message Forwarding**: Forwards messages between users and staff
- **SQLite Database**: Stores ticket and message history
- **Docker Support**: Easy deployment with Docker and Docker Compose
- **Staff Commands**: Commands to manage and close tickets

## Prerequisites

- Python 3.12+
- Discord Bot Token
- Discord Server with appropriate permissions

## Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd discord-mod-mail
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy the environment template and fill in your values:

```bash
cp .env.template .env
```

Edit `.env` file with your configuration:

```env
DISCORD_TOKEN=your_discord_bot_token_here
SUPPORT_TICKET_PARENT=your_support_channel_id_here
DATABASE_PATH=./data/modmail.db
BOT_PREFIX=!
```

### 4. Discord Bot Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to the "Bot" section
4. Create a bot and copy the token
5. Enable the following intents:
   - Message Content Intent
   - Server Members Intent (if needed)
6. Invite the bot to your server with the following permissions:
   - Send Messages
   - Read Message History
   - Manage Messages
   - Embed Links
   - Read Messages

### 5. Run the Bot

#### Development Mode

```bash
# Using Makefile (recommended)
make run

# Or directly
python bot.py
```

#### Production Mode with Docker

```bash
# Using Makefile (recommended)
make up

# Or directly
docker-compose up -d
```

## Makefile Commands

The project includes a Makefile for easy development and deployment:

```bash
# Setup and installation
make setup      # Set up the project
make install    # Install dependencies
make dev        # Complete development setup

# Development
make run        # Run the bot
make test       # Run tests
make lint       # Run linting
make format     # Format code

# Docker
make build      # Build Docker image
make up         # Start with Docker Compose
make down       # Stop the bot
make logs       # View logs
make restart    # Quick restart

# Maintenance
make clean      # Clean up files
make status     # Check bot status
```

## Usage

### For Users

1. Send a direct message to the bot
2. The bot will create a support ticket in the designated channel
3. Staff will respond in the support channel
4. Continue the conversation by replying to the bot's messages

### For Staff

- **View Active Tickets**: `!tickets` - Lists all active tickets
- **Close Ticket**: `!close [user_id]` - Closes a ticket (current channel or by user ID)
- **Add User to Ticket**: `!adduser <@user|user_id>` - Adds a user to the current ticket
- **Remove User from Ticket**: `!removeuser <@user|user_id>` - Removes a user from the current ticket
- **Ticket Information**: `!ticketinfo` - Shows information about the current ticket
- **Respond to Tickets**: Reply to messages in the support channel to respond to users

## Database Schema

The bot uses SQLite to store:

- **Tickets**: User ID, Channel ID, Creation time, Active status
- **Ticket Users**: Multiple users per ticket (many-to-many relationship)
- **Messages**: Message content, User ID, Direction (user/staff), Timestamps

## Docker Deployment

The bot is containerized for easy deployment:

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the bot
docker-compose down
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DISCORD_TOKEN` | Discord bot token | Yes |
| `SUPPORT_TICKET_PARENT` | Channel ID for support tickets | Yes |
| `DATABASE_PATH` | Path to SQLite database | No (default: ./data/modmail.db) |
| `BOT_PREFIX` | Command prefix | No (default: !) |

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for more information.
