import asyncio

from prompt_toolkit.application import get_app
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import FormattedTextControl, Window, WindowAlign
from prompt_toolkit.mouse_events import MouseEventType


class AsyncButton:
    """An async implementation of a clickable item."""

    def __init__(self, text, handler=None, width=12, finished_callback=None):
        assert isinstance(width, int)
        self.loop = asyncio.get_event_loop()
        if handler:
            if not asyncio.iscoroutinefunction(handler):
                raise Exception("handler is not a coroutine function.")

        self._call_back = finished_callback

        self.text = text
        self.handler = handler
        self.width = width
        self.control = FormattedTextControl(
            self._get_text_fragments,
            key_bindings=self._get_key_bindings(),
            focusable=True,
        )

        def get_style():
            if get_app().layout.has_focus(self):
                return "class:button.focused"
            else:
                return "class:button"

        self.window = Window(
            self.control,
            align=WindowAlign.LEFT,
            height=1,
            width=width,
            style=get_style,
            dont_extend_width=True,
            dont_extend_height=True,
        )

    async def async_handler(self, event):
        await self.handler(event)

    def _get_key_bindings(self):
        """ Key bindings for the Button. """
        kb = KeyBindings()

        @kb.add(" ")
        @kb.add("enter")
        def _(event):
            if self.handler:
                _task = self.loop.create_task(self.async_handler(event))
                if self._call_back:
                    _task.add_done_callback(self._call_back)

        return kb

    def _get_text_fragments(self):
        text = "  -{}".format(self.text)

        def handler(mouse_event):
            if mouse_event.event_type == MouseEventType.MOUSE_UP:
                self.handler()

        return [
            ("[SetCursorPosition]", ""),
            ("class:button.text", text, handler),
        ]

    def __pt_container__(self):
        return self.window
