# commands
from discord.ext import commands

# custom functions
from functions import *

if __name__ == '__main__':

    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)
    msg_command_name = 'Embed'


    @bot.event
    async def on_ready():
        print(f"Bot loaded with {int(bot.latency * 100)} ping")


    @bot.slash_command(name="bulletin_board", description="Send bulletin-board reaction message.")
    async def setup(ctx):
        response = await ctx.respond(c.ROLE_REACTION_MSG)
        msg = await response.original_message()
        await msg.add_reaction('\U0001F4F0')

    @bot.event
    async def on_raw_reaction_add(payload):
        channel = await bot.fetch_channel(payload.channel_id)
        msg = await channel.fetch_message(payload.message_id)

        message_id = payload.message_id
        m = payload.member

        if payload.emoji.name == '📰':
            if msg.content == c.ROLE_REACTION_MSG:
                guild = bot.get_guild(payload.guild_id)
                role = discord.utils.get(guild.roles, name='Bulletin')
                await m.add_roles(role)
        else:
            pass


    @bot.event
    async def on_raw_reaction_remove(payload):
        channel = await bot.fetch_channel(payload.channel_id)
        msg = await channel.fetch_message(payload.message_id)
        message_id = payload.message_id
        guild = bot.get_guild(payload.guild_id)
        m = await guild.fetch_member(payload.user_id)

        if payload.emoji.name == '📰':
            if msg.content == c.ROLE_REACTION_MSG:
                role = discord.utils.get(guild.roles, name='Bulletin')
                await m.remove_roles(role)
        else:
            pass

    @bot.message_command(name=msg_command_name)
    async def embed(ctx, message: discord.Message):
        if not await check_permissions(ctx, message):
            await ctx.respond(content="Sorry, you don't have permissions.",
                              ephemeral=True)
            return

        if not message.embeds:
            await ctx.respond(content="No embed found in message. Add a url that includes an embed or create your own "
                                      "embed. (Creating your own Embed is not available at the moment.)",
                              ephemeral=True)
        else:

            em = message.embeds[0]
            em.colour = c.EMBED_COLOR
            apply_descriptors(message)
            apply_default_tags(message)
            edit_button = build_edit_button(message)
            cancel_button = build_cancel_button()
            channel_select = build_channel_select(message)
            view = await build_view(ctx, [edit_button, cancel_button, channel_select])
            response = await ctx.respond(embed=em, ephemeral=False, view=view)
            await msg_auto_removal(response, 300)  # auto-remove response after 5 minutes


    bot.run(c.TOKEN)
