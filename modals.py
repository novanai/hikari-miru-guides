import os
import typing

import dotenv
import hikari
import miru
from dataclasses import dataclass
from hikari import ButtonStyle, Intents, MessageFlag, TextInputStyle


dotenv.load_dotenv()

INTENTS = Intents.ALL_MESSAGES | Intents.MESSAGE_CONTENT

bot = hikari.GatewayBot(
    os.environ["BOT_TOKEN"],
    intents=INTENTS,
)
miru.install(bot)


@dataclass
class Embed:
    title: typing.Union[str, None] = None
    description: typing.Union[str, None] = None
    thumbnail_url: typing.Union[str, None] = None


class EmbedEditor(miru.Modal):
    def __init__(self, embed: Embed) -> None:
        super().__init__("Embed Editor")

        items = [
            miru.TextInput(
                label="Title",
                value=embed.title,
                custom_id="title",
            ),
            miru.TextInput(
                label="Description",
                value=embed.description,
                custom_id="description",
                style=TextInputStyle.PARAGRAPH,
            ),
            miru.TextInput(
                label="Thumbnail URL",
                value=embed.thumbnail_url,
                custom_id="thumbnail_url",
            ),
        ]

        for item in items:
            self.add_item(item)

    async def callback(self, ctx: miru.ModalContext) -> None:
        await ctx.defer()


@dataclass
class Webhook:
    url: typing.Union[str, None] = None
    username: typing.Union[str, None] = None
    avatar_url: typing.Union[str, None] = None

    @property
    def id(self) -> typing.Union[int, None]:
        if not self.url:
            return None

        return int(self.url.split("webhooks/")[1].split("/")[0])

    @property
    def token(self) -> typing.Union[str, None]:
        if not self.url:
            return None

        return self.url.split("/")[-1]


class WebhookEditor(miru.Modal):
    def __init__(self, webhook: Webhook) -> None:
        super().__init__("Webhook Editor")

        items = [
            miru.TextInput(
                label="Webhook URL",
                value=webhook.url,
                custom_id="url",
            ),
            miru.TextInput(
                label="Username",
                value=webhook.username,
                custom_id="username",
            ),
            miru.TextInput(
                label="Avatar URL",
                value=webhook.avatar_url,
                custom_id="avatar_url",
            ),
        ]

        for item in items:
            self.add_item(item)

    async def callback(self, ctx: miru.ModalContext) -> None:
        await ctx.defer()


class MainView(miru.View):
    def __init__(self, author: hikari.User) -> None:
        self.author = author

        self.embed = Embed()
        self.webhook = Webhook()

        super().__init__(timeout=240)

    @miru.button(label="Edit Embed", style=ButtonStyle.SECONDARY)
    async def edit_embed(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        view = EmbedEditor(self.embed)
        await ctx.respond_with_modal(view)
        await view.wait()

        for item in view.children:
            item = typing.cast(miru.TextInput, item)

            setattr(self.embed, item.custom_id, item.value)

    @miru.button(label="Edit Webhook", style=ButtonStyle.SECONDARY)
    async def edit_webhook(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        view = WebhookEditor(self.webhook)
        await ctx.respond_with_modal(view)
        await view.wait()

        for item in view.children:
            item = typing.cast(miru.TextInput, item)

            setattr(self.webhook, item.custom_id, item.value)

    @miru.button(label="Preview Embed", style=hikari.ButtonStyle.PRIMARY)
    async def preview_embed(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        embed = hikari.Embed(title=self.embed.title, description=self.embed.description)
        embed.set_thumbnail(self.embed.thumbnail_url)

        await ctx.respond(embed, flags=MessageFlag.EPHEMERAL)

    @miru.button(label="Post Webhook", style=hikari.ButtonStyle.SUCCESS)
    async def post_webhook(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        if not (self.webhook.id and self.webhook.token):
            await ctx.respond(
                "Please supply a valid webhook URL!", flags=MessageFlag.EPHEMERAL
            )
            return

        embed = hikari.Embed(title=self.embed.title, description=self.embed.description)
        embed.set_thumbnail(self.embed.thumbnail_url)

        msg = await self.bot.rest.execute_webhook(
            self.webhook.id,
            self.webhook.token,
            username=self.webhook.username or hikari.UNDEFINED,
            avatar_url=self.webhook.avatar_url or hikari.UNDEFINED,
            embed=embed,
        )
        await ctx.edit_response(
            f"Posted to <#{msg.channel_id}>!",
            components=[],
            flags=MessageFlag.EPHEMERAL,
        )

    async def view_check(self, ctx: miru.ViewContext) -> bool:
        if ctx.user.id != self.author.id:
            await ctx.respond(
                "You can't use these buttons!", flags=MessageFlag.EPHEMERAL
            )
            return False

        return True

    async def on_timeout(self) -> None:
        assert self.message is not None
        await self.message.edit("Timed out!", components=[])


@bot.listen()
async def on_message(event: hikari.MessageCreateEvent) -> None:
    if not event.is_human or not event.content or not event.content == "miru":
        return

    view = MainView(event.author)

    msg = await event.message.respond(components=view)

    await view.start(msg)


bot.run()
