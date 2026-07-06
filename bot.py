import discord
from discord import Intents
import logging
from database import Message, Attachment, EditedMessage, DeletedMessage, get_db_session, init_db

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

class MessageLoggerBot(discord.Client):
    def __init__(self):
        intents = Intents.default()
        intents.message_content = True  
        intents.messages = True
        intents.guilds = True
        intents.members = True
        super().__init__(intents=intents)

    async def on_ready(self):
        logger.info(f'Bot logged in as {self.user}')

    async def on_message(self, message):
        if message.author.bot: 
            return
        if message.type != discord.MessageType.default:
            return

        with get_db_session() as db:
            try:
                mentioned_users = [str(m.id) for m in message.mentions]
                mentioned_roles = [str(r.id) for r in message.role_mentions]

                reply_to_message_id = None
                reply_to_author = None
                if message.reference and message.reference.message_id:
                    try:
                        referenced_msg = await message.channel.fetch_message(message.reference.message_id)
                        reply_to_message_id = str(referenced_msg.id)
                        reply_to_author = str(referenced_msg.author)
                    except:
                        reply_to_message_id = str(message.reference.message_id)

                msg_record = Message(
                    message_id=str(message.id),
                    channel_id=str(message.channel.id),
                    channel_name=getattr(message.channel, 'name', None),
                    guild_id=str(message.guild.id) if message.guild else None,
                    guild_name=message.guild.name if message.guild else None,
                    author_id=str(message.author.id),
                    author_name=message.author.name,
                    author_discriminator=message.author.discriminator if hasattr(message.author, 'discriminator') else '0',
                    author_nickname=message.author.nick if hasattr(message.author, 'nick') else None,
                    content=message.content,
                    timestamp=message.created_at,
                    is_bot=message.author.bot,
                    mentions=mentioned_users, # Managed automatically as native JSON primitives now
                    mentioned_roles=mentioned_roles,
                    has_attachments=len(message.attachments) > 0,
                    has_embed=len(message.embeds) > 0,
                    reply_to_message_id=reply_to_message_id,
                    reply_to_author=reply_to_author
                )
                db.add(msg_record)

                for attachment in message.attachments:
                    db.add(Attachment(
                        message_id=str(message.id),
                        attachment_id=str(attachment.id),
                        filename=attachment.filename,
                        content_type=attachment.content_type,
                        url=attachment.url,
                        size=attachment.size,
                        proxy_url=attachment.proxy_url
                    ))
                db.commit()
            except Exception as e:
                logger.error(f'Error logging message: {e}')
                db.rollback()

    async def on_message_edit(self, before, after):
        if before.content == after.content or after.type != discord.MessageType.default:
            return

        with get_db_session() as db:
            try:
                msg_record = db.query(Message).filter_by(message_id=str(after.id)).first()
                if msg_record:
                    msg_record.content = after.content
                    msg_record.edited_timestamp = discord.utils.utcnow()

                    db.add(EditedMessage(
                        message_id=str(after.id),
                        old_content=before.content,
                        new_content=after.content,
                        edited_at=discord.utils.utcnow()
                    ))
                    db.commit()
            except Exception as e:
                logger.error(f'Error logging edit: {e}')
                db.rollback()

    async def on_message_delete(self, message):
        if message.type != discord.MessageType.default:
            return

        with get_db_session() as db:
            try:
                msg_record = db.query(Message).filter_by(message_id=str(message.id)).first()
                deleted_record = DeletedMessage(
                    message_id=str(message.id),
                    channel_id=str(message.channel.id),
                    channel_name=getattr(message.channel, 'name', None),
                    guild_id=str(message.guild.id) if message.guild else None,
                    guild_name=message.guild.name if message.guild else None,
                    author_id=str(message.author.id),
                    author_name=message.author.name,
                    author_discriminator=message.author.discriminator if hasattr(message.author, 'discriminator') else '0',
                    content=message.content,
                    original_timestamp=message.created_at,
                    has_attachments=len(message.attachments) > 0,
                    reply_to_message_id=msg_record.reply_to_message_id if msg_record else None
                )
                db.add(deleted_record)
                if msg_record:
                    msg_record.content = "[MESSAGE DELETED]"
                db.commit()
            except Exception as e:
                logger.error(f'Error logging deletion: {e}')
                db.rollback()

def run_bot(token: str):
    init_db()
    bot = MessageLoggerBot()
    bot.run(token)

if __name__ == '__main__':
    import os
    from dotenv import load_dotenv
    load_dotenv()
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    if not DISCORD_TOKEN:
        exit(1)
    run_bot(DISCORD_TOKEN)
