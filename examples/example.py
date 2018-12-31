import asyncio
import logging

from prompt_toolkit import Application
from prompt_toolkit.eventloop import use_asyncio_event_loop
from prompt_toolkit.layout import Layout
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import MenuContainer, MenuItem

from pttui.command_sidebar import (
    SideBarYesNo,
    SideBarItemButton,
    SideBar,
    SideBarItemLabel,
    SideBarSelectableList,
    SideBarForm,
    SideBarItemTextEntry,
    SideBarItemSpace,
)
from pttui.printers import (
    print_line,
    print_key_value_pair,
    print_dict,
    LogHandler,
    spinner,
)
from pttui.helpers import Context

from pttui.layout import set_status, get_layout, output

from pttui.layout import kb, ui_style

use_asyncio_event_loop()

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
#
_handler = LogHandler()
logger.addHandler(_handler)
# #
LOGGER = logging.getLogger(__name__)


class SceneMenu(SideBar):
    def __init__(self, context, parent_container=None):
        items = [
            SideBarItemLabel("Scenes"),
            SideBarItemButton("Activate scene", self.activate, "a"),
            SideBarItemButton("print dict", self.print_dict, "p"),
        ]
        super().__init__(context, items, parent_container, "Scenes")

    async def activate(self, *args):
        print_line("activate scene")

    async def print_dict(self, *args):
        a = {"test": 1, "test1": {"a": True}}
        print_dict(a)


class ShadeMenu(SideBar):
    def __init__(self, context, parent_container=None):
        items = []
        items.append(SideBarItemLabel("Shade actions"))
        items.append(SideBarItemButton("start [s]", self.start_timer, "s"))
        items.append(SideBarItemButton("open [o]", self.open, "o"))
        items.append(SideBarItemButton("delete [d]", self.delete, "d"))
        items.append(SideBarItemButton("get list [g]", self.get_list, "g"))
        items.append(SideBarItemLabel("Info:"))
        items.append(SideBarItemButton("info [i]", self.info, "i"))
        items.append(SideBarItemButton("user", self.user, "u"))
        items.append(SideBarItemButton("print dict", self.print_dict, "p"))
        items.append(SideBarItemButton("print line", self.print_line, "n"))
        items.append(SideBarItemButton("log message", self.do_log, "l"))
        items.append(SideBarItemButton("test menu", self.test_menu, "t"))
        items.append(SideBarItemButton("add scene", self.add_scene, "a"))
        items.append(SideBarItemButton("select text",self.select_text,"x"))
        super().__init__(context, items, parent_container, "SHADE MENU")

    @spinner("Adding item")
    async def add_scene(self, *args):
        scene_menu.add_item(SideBarItemLabel("new label"))
        await asyncio.sleep(3)

    async def select_text(self,*args):
        output.cursor_position=0
        output.start_selection()
        output.cursor_position=100

    async def test_menu(self, *args):
        test = SideBar(None, [SideBarItemSpace()], None)
        test.show()

    async def do_log(self, *args):
        LOGGER.debug("this is in the log. %s", "test")

    async def print_line(self, *args):
        print_line("a line")

    async def print_dict(self, *args):
        a = {
            "test": 1,
            "test1": {"a": True, "nested": "string"},
            "b": 1.45,
            "atest": "string output",
        }
        print_dict(a)

    async def open(self, *args):
        print_line("opening")
        await asyncio.sleep(1)
        print_line("finished opening")

    async def start_timer(self, *args):
        print_line("starting timer")
        loop = 0
        while loop < 30:
            loop += 1
            set_status(
                "loop", "<green>loop:</green><orange>{}</orange>".format(loop)
            )
            await asyncio.sleep(1)
            print_line("looping")
        print_line("finished")

    async def delete(self, *args):
        yes_no = SideBarYesNo(
            None, self, label="Are you sure ?", title="DELETE"
        )
        yes_no.show()
        # await the result to be sure to return to this method and proceed
        # depending on the result.
        result = await yes_no.future
        print_key_value_pair("return value: ", result)

    async def get_list(self, *args):
        items = [{"text": "item 1"}, {"text": "item 2"}, {"text": "item 3"}]
        select_items = SideBarSelectableList(
            None, items, self, title="Select an item."
        )
        select_items.show()
        selected = await select_items.future

        print_key_value_pair("selected item: ", selected)

    async def info(self, *args):
        print_key_value_pair("info", "here")

    async def user(self, *args):
        user = UserInput(self)
        user.show()
        data = await user.future
        print_key_value_pair("input", data)


class UserInput(SideBarForm):
    def __init__(self, parent_container):
        items = [
            SideBarItemLabel("ip address:"),
            SideBarItemTextEntry(key="ip_address"),
            SideBarItemSpace(),
        ]
        super().__init__(None, items, parent_container, title="Enter hub data")


loop = asyncio.get_event_loop()

context = Context()

shade_menu = ShadeMenu(context)
context.shade_menu = shade_menu

scene_menu = SceneMenu(context)
context.scene_menu = scene_menu

test_menu = SideBar(context, [], None)

menu_items = [
    MenuItem(
        "file",
        children=[
            MenuItem("shades", shade_menu.show),
            MenuItem("scenes", scene_menu.show),
        ],
    )
]

layout = get_layout(shade_menu, menu_items)

app = Application(
    layout=layout,
    full_screen=True,
    key_bindings=kb,
    style=ui_style,
)

loop.run_until_complete(app.run_async().to_asyncio_future())
