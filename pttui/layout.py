import logging

from prompt_toolkit import HTML
from prompt_toolkit.application import get_app
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.formatted_text import (
    to_formatted_text,
    fragment_list_to_text,
)
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import (
    BufferControl,
    Window,
    VSplit,
    DynamicContainer,
    HSplit,
    FormattedTextControl,
    Dimension,
    Layout,
)
from prompt_toolkit.layout.processors import Processor, Transformation
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import MenuContainer, TextArea

from pttui.helpers import get_following

LOGGER = logging.getLogger(__name__)


class FormatText(Processor):
    def apply_transformation(self, ti):
        try:
            fragments = to_formatted_text(
                HTML(fragment_list_to_text(ti.fragments))
            )
            return Transformation(fragments)
        except Exception:
            return Transformation(ti.fragments)


# todo: make textbuffer fixed length (for example: len = max(10000))

_output_window = TextArea(
    complete_while_typing=False,
    scrollbar=True,
    focus_on_click=True,
    line_numbers=True,
    input_processors=[FormatText()],
)
output = _output_window.buffer

kb = KeyBindings()


@kb.add("c-q")
def _(event):
    event.app.exit()


_current_menu = None


def set_current_sidebar(menu):
    global _current_menu
    _current_menu = menu
    if menu.has_focusable_items:
        get_app().layout.focus(menu)


def get_current_sidebar():
    return _current_menu


# ui_style = {"text_entry": "bg:#aaaaaa #888888", "status_bar": "bg:#aaaaaa"}
ui_style = Style.from_dict({"status": "reverse", "shadow": "bg:#440044"})



status = {"general": "Press CTRL-Q to quit"}


def set_status(key, value):
    """Add a status to the status bar."""
    status[key] = value
    status_bar.text = HTML(get_status())


def get_status():
    return " | ".join((val for val in status.values()))


status_bar = FormattedTextControl(
    HTML(get_status()), show_cursor=False, style="class:status"
)


def get_layout(entry_point, top_menu_items):
    set_current_sidebar(entry_point)
    menu = DynamicContainer(get_current_sidebar)

    # windows that are focused by pressing tab keys.

    main_focus = [menu, _output_window]

    following = get_following(main_focus)

    def next_main_window(event):
        next_idx = following(1)
        event.app.layout.focus(main_focus[next_idx])

    def previous_main_window(event):
        next_idx = following(-1)
        event.app.layout.focus(main_focus[next_idx])

    key_binding = KeyBindings()
    kb.add("tab")(next_main_window)
    kb.add("s-tab")(previous_main_window)

    root_container = HSplit(
        [
            VSplit(
                [menu, Window(width=1, char="|"), _output_window],
                height=Dimension(),
            ),
            Window(
                content=status_bar,
                width=Dimension(),
                height=1,
                style="class:status_bar",
            ),
        ]
    )
    if top_menu_items:
        root_container = MenuContainer(
            body=root_container, menu_items=top_menu_items
        )
        main_focus.append(root_container.window)

    layout = Layout(root_container, focused_element=entry_point)
    return layout
