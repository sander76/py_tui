import asyncio
from asyncio import Future
from collections import Counter
from typing import List

from prompt_toolkit.application import get_app
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import HSplit, Window
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import Label, TextArea, HorizontalLine

from pttui.async_widgets import AsyncButton
from pttui.layout import set_current_sidebar


class SideBarItem:
    """An item in the sidebar"""

    def __init__(self, key_binding, handler, container):
        self.binding = key_binding
        self.handler = handler
        self.container = container

    def __pt_container__(self):
        return self.container


class SideBarItemButton(SideBarItem):
    """A button in the sidebar."""

    def __init__(
        self, text, handler, key_binding=None, append_key_to_text=True
    ):
        if append_key_to_text and key_binding:
            text = "{} [{}]".format(text, key_binding)
        super().__init__(key_binding, handler, AsyncButton(text, handler))


class SideBarItemLabel(SideBarItem):
    """A label"""

    def __init__(self, text, style=""):
        super().__init__(None, None, Label(text, style=style))


class SideBarItemTextEntry(SideBarItem):
    style = Style.from_dict({"control": "bg:#88ff88"})

    def __init__(self, label=None, key=None):
        self.key = key

        super().__init__(
            None, None, TextArea(multiline=False, style="class:text_entry")
        )


class SideBarItemLine(SideBarItem):
    """Draw a horizontal line."""
    def __init__(self):
        super().__init__(None, None, HorizontalLine())


class SideBarItemSpace(SideBarItem):
    """Draw an empty line."""
    def __init__(self):
        super().__init__(None, None, Window(height=1))


class SideBar:
    """A basic sidebar container"""

    @staticmethod
    def make_async_binding(handler):
        def _(event):
            asyncio.get_event_loop().create_task(handler(event))

        return _

    @staticmethod
    def add_title(title):
        yield SideBarItemLabel(title)
        yield SideBarItemLine()

    def __init__(
        self, context, items: List[SideBarItem], parent_container, title=None
    ):
        self._items = items
        assert items is not None
        # assert len(items) > 0
        self.context = context
        self._key_bindings = KeyBindings()
        self._key_bindings.add("up")(self.go_up)
        self._key_bindings.add("down")(self.go_down)
        self._make_bindings()
        self._title = title
        self._container = None
        self.build()
        self.parent_container = parent_container
        self.app = get_app()

    def __call__(self):
        #todo: await a future.
        self.show()

    def _build(self):
        if self._title:
            for _itm in SideBar.add_title(self._title):
                yield _itm
        for _itm in self._items:
            yield _itm

    def build(self):
        """Build the sidebar with its items."""
        self._container = HSplit(
            tuple(self._build()), key_bindings=self._key_bindings, width=25
        )

    def add_item(self, item: SideBarItem):
        assert isinstance(item, SideBarItem)
        self._items.append(item)
        self.build()

    def add_items(self, items: List[SideBarItem], clear=False):
        if clear:
            self._items = items
        else:
            self._items.extend(items)
        self.build()

    @staticmethod
    def is_focusable(container):
        try:
            return container.content.focusable()
        except AttributeError:
            return False

    @property
    def has_focusable_items(self):
        for itm in self._container.children:
            if SideBar.is_focusable(itm):
                return True
        return False

    def get_current(self, event):
        return self._container.children.index(event.app.layout.current_window)

    def go_up(self, event):
        def get_previous_focusable(previous_idx):
            if previous_idx < 0:
                return get_previous_focusable(
                    len(self._container.children) - 1
                )

            if SideBar.is_focusable(self._container.children[previous_idx]):
                return self._container.children[previous_idx]
            return get_previous_focusable(previous_idx - 1)

        current = self.get_current(event)
        previous_focusable = get_previous_focusable(current - 1)
        event.app.layout.focus(previous_focusable)

    def go_down(self, event):
        def get_next_focusable(next_idx):
            if next_idx == len(self._container.children):
                return get_next_focusable(0)
            if SideBar.is_focusable(self._container.children[next_idx]):
                return self._container.children[next_idx]
            return get_next_focusable(next_idx + 1)

        current = self.get_current(event)
        next_focusable = get_next_focusable(current + 1)
        event.app.layout.focus(next_focusable)

    def _validate_bindings(self):
        """Validate keybinding on duplicates."""
        c = Counter((item.binding for item in self._items if item.binding))
        for key, value in c.items():
            if value > 1:
                raise AssertionError(
                    "Key binding -%s- is defined more than once" % key
                )

    def _make_bindings(self):
        self._validate_bindings()

        for item in self._items:
            if item.binding:
                self._key_bindings.add(item.binding)(
                    SideBar.make_async_binding(item.handler)
                )

    def show(self):
        set_current_sidebar(self)

    def __pt_container__(self):
        return self._container


class SideBarYesNo(SideBar):
    """A menu item which asks the user for yes/no input."""

    def __init__(self, context, parent_container, label=None, title=None):
        children = [SideBarItemSpace()]
        if label:
            children.append(SideBarItemLabel(text=label))
            children.append(SideBarItemSpace())

        children.append(SideBarItemButton("YES [y]", self._yes, "y"))
        children.append(SideBarItemButton("NO [n]", self._no, "n"))
        super().__init__(context, children, parent_container, title=title)

        self.future = Future()

    async def _yes(self, *args):
        self.future.set_result(True)
        self.parent_container.show()

    async def _no(self, *args):
        self.future.set_result(False)
        self.parent_container.show()


class SideBarSelectableList(SideBar):
    """A menu sidebar with selectable items."""

    def __init__(
        self, context, items: List[dict], parent_container, title=None
    ):
        children = []
        for item in items:
            children.append(SideBarItemButton(item["text"], self.select(item)))
        children.append(SideBarItemLine())
        children.append(
            SideBarItemButton(
                "Cancel", self.cancel, "c", append_key_to_text=True
            )
        )
        super().__init__(context, children, parent_container, title=title)

        self.future = Future()

    async def cancel(self, *args):
        self.future.set_result(None)
        self.parent_container.show()

    def select(self, item):
        async def selected(*args):
            self.future.set_result(item)
            self.parent_container.show()

        return selected


class SideBarForm(SideBar):
    """A menu sidebar as a form with ok and cancel option"""

    def __init__(
        self, context, items: List[SideBarItem], parent_container, title=None
    ):

        items.append(
            SideBarItemButton("OK", self.ok, "o", append_key_to_text=True)
        )

        super().__init__(context, items, parent_container, title=title)

        self.future = Future()
        self.data = {}

    async def ok(self, *args):
        for item in self._items:
            if isinstance(item, SideBarItemTextEntry) and item.key:
                self.data[item.key] = item.container.text
        self.future.set_result(self.data)

        self.parent_container.show()

    async def cancel(self, *args):
        self.future.set_result(None)

        self.parent_container.show()
