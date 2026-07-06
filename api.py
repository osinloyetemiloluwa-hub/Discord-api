Python




import threading
import asyncio
from bot import MessageLoggerBot

# ... (Keep all your existing Flask routes and setup here) ...

def run_discord_bot():
    """Function to run the Discord Bot inside a background thread"""
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    if not DISCORD_TOKEN:
        logger.error('DISCORD_TOKEN not found! Background bot cannot start.')
        return

    # Create a fresh async event loop for this background thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    bot = MessageLoggerBot()
    logger.info("Initializing Discord Bot in background thread...")
    
    try:
        loop.run_until_complete(bot.start(DISCORD_TOKEN))
    except Exception as e:
        logger.error(f"Discord Bot encountered an error: {e}")

# Initialize database
init_db()
logger.info('Database initialized')

# Start the Discord Bot thread immediately when Gunicorn loads this file
bot_thread = threading.Thread(target=run_discord_bot, daemon=True)
bot_thread.start()
logger.info('Background Discord bot thread successfully spawned.')


if __name__ == '__main__':
    # This block is used for local running (python api.py)
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    logger.info(f'Starting Discord Logger API locally on port {port}')
    app.run(host='0.0.0.0', port=port, debug=debug)
