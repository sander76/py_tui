import asyncio
import json
from asyncio import CancelledError
from functools import wraps
from logging import Handler
from xml.parsers.expat import ExpatError

from pygments.lexers.data import JsonLexer
from pygments.token import Token

from pttui.layout import output


def print_key_value_pair(key, value, scroll=True):
    output.text += "\n<green>{:<15}</green><orange>{}</orange>".format(
        key, value
    )
    if scroll:
        output.cursor_position = len(output.text)


def print_line(line, line_end=True, scroll=True):
    _line_end = ""
    if line_end:
        _line_end = "\n"
    output.text += "<orange>{}</orange>{}".format(line, _line_end)
    if scroll:
        output.cursor_position = len(output.text)


def print_dict(data: dict, scroll=True):
    text = json.dumps(data, indent=4)

    lex = JsonLexer()
    tokens = lex.get_tokens(text)
    out = []
    for tok in tokens:
        if tok[0] == Token.Text:
            out.append(tok[1])
        elif tok[0] == Token.Punctuation:
            out.append(tok[1])
        elif tok[0] == Token.Name.Tag:
            out.append("<green>{}</green>".format(tok[1]))
        elif tok[0] == Token.Literal.Number.Integer:
            out.append("<orange>{}</orange>".format(tok[1]))
        elif tok[0] == Token.Keyword.Constant:
            out.append("<red>{}</red>".format(tok[1]))
        elif tok[0] == Token.Literal.Number.Float:
            out.append("<yellow>{}</yellow>".format(tok[1]))
        else:
            out.append(tok[1])

    output.text += "\n{}".format("".join(out))

    if scroll:
        output.cursor_position = len(output.text)


def print_waiting_done(action):
    async def waiting():
        print_line(action, line_end=False)

        try:
            while True:
                await asyncio.sleep(0.5)
                print_line(".", line_end=False, scroll=False)
        except CancelledError:
            pass

    task = asyncio.ensure_future(waiting())

    async def _finished():
        print_line("done")
        # todo: make the wile loop not infinite as it might hang indefinitely
        task.cancel()
        while not task.cancelled:
            await asyncio.sleep(0.5)

    return _finished


def spinner(message):
    """Wraps a Waiting.... done spinner around a method"""

    def _spinner(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            done = print_waiting_done(message)
            res = await func(*args, **kwargs)
            await done()
            return res

        return wrapper

    return _spinner


class LogHandler(Handler):
    def emit(self, record):
        msg = self.format(record)
        try:
            print_line(msg)
        except ExpatError:
            pass
