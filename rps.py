import os
import random

import dotenv
import hikari
import miru
from hikari import ButtonStyle, Intents, MessageFlag

dotenv.load_dotenv()

INTENTS = Intents.ALL_MESSAGES | Intents.MESSAGE_CONTENT


bot = hikari.GatewayBot(
    os.environ["BOT_TOKEN"],
    intents=INTENTS,
)
miru.install(bot)

EMOJI: dict[str, str] = {
    "r": "🪨",
    "p": "📄",
    "s": "✂️",
}


class RPSView(miru.View):
    def __init__(self, user: hikari.User) -> None:
        self.user = user
        self.user_wins = 0

        super().__init__(timeout=30)

    @miru.button(emoji="🪨", style=ButtonStyle.SECONDARY, custom_id="r")
    async def rock(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        await self.play(button.custom_id, ctx)

    @miru.button(emoji="📄", style=ButtonStyle.SUCCESS, custom_id="p")
    async def paper(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        await self.play(button.custom_id, ctx)

    @miru.button(emoji="✂️", style=ButtonStyle.PRIMARY, custom_id="s")
    async def scissors(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        await self.play(button.custom_id, ctx)

    @miru.button(
        label="End game",
        emoji="✖️",
        style=ButtonStyle.DANGER,
    )
    async def stop_game(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        self.stop()

    async def play(self, user: str, ctx: miru.ViewContext) -> None:
        bot = random.choice(["r", "p", "s"])

        text = f"{EMOJI[user]} vs {EMOJI[bot]}"

        if user == bot:
            await ctx.respond(f"{text} - Draw!", flags=MessageFlag.EPHEMERAL)

        elif (
            (user == "r" and bot == "s")
            or (user == "p" and bot == "r")
            or (user == "s" and bot == "p")
        ):
            await ctx.respond(f"{text} - You win!", flags=MessageFlag.EPHEMERAL)
            self.user_wins += 1

        else:
            await ctx.respond(f"{text} - You lose!", flags=MessageFlag.EPHEMERAL)

    async def view_check(self, ctx: miru.ViewContext) -> bool:
        if ctx.user.id != self.user.id:
            await ctx.respond("This isn't your game!", flags=MessageFlag.EPHEMERAL)
            return False

        return True


@bot.listen()
async def on_message(event: hikari.MessageCreateEvent) -> None:
    if not event.is_human or not event.content or not event.content == "rps":
        return

    view = RPSView(event.author)

    msg = await event.message.respond("Rock, Paper, Scissors!", components=view)

    await view.start(msg)
    await view.wait()

    await msg.edit(f"You won {view.user_wins} times!", components=[])


bot.run()
