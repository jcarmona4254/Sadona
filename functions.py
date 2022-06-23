import discord

import constants as c

# for msg timer
import asyncio

# ui components
from discord.ui import Modal, InputText, Button, Select, View


def clean_text(msg, delimiter):
    if delimiter != '':
        msg = ''.join(msg.split())  # remove all whitespace within ()
        msg_li = msg.split(delimiter)  # create list out of (data) split by delimiter
        msg_li = list(dict.fromkeys(msg_li))  # remove duplicates
        msg = ', '.join(msg_li)  # list to string
    return msg


def parse_msg_data(message, descriptor):
    # descriptors -> t = title, d = description, # = tags, etc..

    msg_data = ''
    index = message.content.find(descriptor + '(')
    if index != -1:

        index += 2  # move index after '#('

        while index < len(message.content) and message.content[index] != ')':
            msg_data += message.content[index]
            index += 1

        if descriptor == '#':
            msg_data = clean_text(msg_data, ',')

    else:
        pass
        # debug: print(descriptor + ' descriptor nonexistent')
    return msg_data


# grabs author and provider fields if available then converts to tags -> sets embed footer
def apply_default_tags(message):
    e = message.embeds[0]
    author = None
    provider = None
    text = None

    counter = 0
    if e.author.name:
        author = e.author.name
        counter += 1
        text = author
    if e.provider.name:
        provider = e.provider.name
        counter += 1
        text = provider
    if counter > 1:
        text = author + ',' + provider
    elif counter == 1:
        text = ''.join(text.split())

    # add provider and author to tags
    if text:
        if e.footer.text:
            text = e.footer.text + ',' + text.lower()
            text = clean_text(text, ',')
            e.set_footer(text=text.lower())
        else:
            e.set_footer(text=text.lower())


def apply_descriptors(message):
    if message.embeds:

        # title
        title = parse_msg_data(message, 't')
        if title == '':
            title = message.embeds[0].title
        else:
            message.embeds[0].title = title

        # description
        descr = parse_msg_data(message, 'd')
        if descr == '':
            descr = message.embeds[0].description
        else:
            message.embeds[0].description = descr

        # tags
        tags = parse_msg_data(message, '#')
        if tags:
            message.embeds[0].set_footer(text=tags.lower(), icon_url=message.embeds[0].Empty)

    else:
        print('No embed to modify')
        return -1


def get_text_channels(guild):
    text_channels = []

    for channel in guild.text_channels:
        text_channels.append(channel)
    return text_channels


def get_channel_options(discord, text_channels):
    channel_options = []
    sorted_channels = []

    for channel in text_channels:
        sorted_channels.append([channel.name])

    for sorted_chan in sorted(sorted_channels):
        channel_options.append(discord.SelectOption(label=sorted_chan[0]))
    return channel_options


async def edit_modal(message, interaction):
    async def modal_callback(interaction):
        message.embeds[0].title = my_modal.children[0].value
        message.embeds[0].description = my_modal.children[1].value
        message.embeds[0].set_footer(text=clean_text(my_modal.children[2].value.lower(), ','),
                                     icon_url=message.embeds[0].Empty)
        await interaction.response.edit_message(embed=message.embeds[0])

    modal_e_title = InputText(label="Title", placeholder=message.embeds[0].title,
                              value=message.embeds[0].title)
    modal_e_descr = InputText(label="Description", style=discord.InputTextStyle.multiline,
                              value=message.embeds[0].description)
    modal_etags = InputText(label="Tags", placeholder=message.embeds[0].footer.text,
                            value=message.embeds[0].footer.text)
    my_modal = Modal(title='Edit Embed')
    my_modal.add_item(modal_e_title)
    my_modal.add_item(modal_e_descr)
    my_modal.add_item(modal_etags)

    my_modal.callback = modal_callback
    await interaction.response.send_modal(my_modal)


def build_edit_button(message):
    edit_button = Button(label='Edit Embed', style=discord.ButtonStyle.grey)

    async def edit_b_callback(interaction):
        await edit_modal(message, interaction)

    edit_button.callback = edit_b_callback
    return edit_button


def build_cancel_button():
    cancel_button = Button(label='Cancel', style=discord.ButtonStyle.red)

    async def cancel_b_callback(interaction):
        await interaction.response.edit_message(delete_after=0)

    cancel_button.callback = cancel_b_callback
    return cancel_button


def build_channel_select(message):
    text_channels = get_text_channels(message.guild)
    channel_options = get_channel_options(discord, text_channels)
    channel_select = Select(placeholder='Post to Selected Channel', options=channel_options)

    async def select_callback(interaction):
        await interaction.response.defer()

        for chan in text_channels:
            if chan.name == channel_select.values[0]:
                try:
                    await chan.send(embed=message.embeds[0])
                    await interaction.followup.send(content='Your embed was successfully posted in \''
                                                            + chan.name + '\'', ephemeral=True)
                    await interaction.delete_original_message()
                except Exception as e:
                    print(e)
                    await interaction.followup.send(e, ephemeral=True)

    channel_select.callback = select_callback
    return channel_select


async def build_view(ctx, components=None):
    if components is None:
        components = []
    view = View(timeout=None)
    for c in components:
        view.add_item(c)

    async def view_inter_callback(interaction):
        if interaction.user != ctx.author:
            await interaction.response.send_message("Interaction access is given solely to the "
                                                    "command author.",
                                                    ephemeral=True)
            return False
        return True

    view.interaction_check = view_inter_callback
    return view


async def msg_auto_removal(msg, timer):
    while timer >= 0:
        await asyncio.sleep(1)
        if timer == 0:
            try:
                await msg.delete_original_message()
            except:
                pass
                # debug: print('Auto-removal of msg failed. Likely already removed by user.')
        timer -= 1


async def check_permissions(ctx, message):
    member = await message.guild.fetch_member(ctx.interaction.user.id)
    # admin has rights by default
    if member.guild_permissions.administrator:
        return True
    for perm_role in c.PERMITTED_ROLES:
        for mem_role in member.roles:
            if mem_role.name == perm_role:
                return True
    return False
