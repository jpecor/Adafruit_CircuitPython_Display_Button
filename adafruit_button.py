# The MIT License (MIT)
#
# Copyright (c) 2019 Limor Fried for Adafruit Industries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""
`adafruit_button`
================================================================================

UI Buttons for displayio


* Author(s): Limor Fried

Implementation Notes
--------------------

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

from micropython import const
import displayio
from adafruit_display_text.label import Label
from adafruit_display_shapes.rect import Rect
from adafruit_display_shapes.roundrect import RoundRect

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_Display_Button.git"


def _check_color(color):
    # if a tuple is supplied, convert it to a RGB number
    if isinstance(color, tuple):
        r, g, b = color
        return int((r << 16) + (g << 8) + (b & 0xff))
    return color


class Button():
    # pylint: disable=too-many-instance-attributes, too-many-locals
    """Helper class for creating UI buttons for ``displayio``.

    :param x: The x position of the button.
    :param y: The y position of the button.
    :param width: The width of the button in pixels.
    :param height: The height of the button in pixels.
    :param name: The name of the button.
    :param style: The style of the button. Can be RECT, ROUNDRECT, SHADOWRECT, SHADOWROUNDRECT.
                  Defaults to RECT.
    :param fill_color: The color to fill the button. Defaults to 0xFFFFFF.
    :param outline_color: The color of the outline of the button.
    :param label: The text that appears inside the button. Defaults to not displaying the label.
    :param label_font: The button label font.
    :param label_color: The color of the button label text. Defaults to 0x0.
    :param selected_fill: Inverts the fill color.
    :param selected_outline: Inverts the outline color.
    :param selected_label: Inverts the label color.

    """
    RECT = const(0)
    ROUNDRECT = const(1)
    SHADOWRECT = const(2)
    SHADOWROUNDRECT = const(3)

    def __init__(self, *, x, y, width, height, name=None, style=RECT,
                 fill_color=0xFFFFFF, outline_color=0x0,
                 label=None, label_font=None, label_color=0x0,
                 selected_fill=None, selected_outline=None,
                 selected_label=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self._font = label_font
        self._selected = False
        self.group = displayio.Group()
        self.name = name
        self._label = label
        self.body = self.fill = self.shadow = None

        self.fill_color = _check_color(fill_color)
        self.outline_color = _check_color(outline_color)
        self._label_color = label_color
        self._label_font = label_font
        # Selecting inverts the button colors!
        self.selected_fill = _check_color(selected_fill)
        self.selected_outline = _check_color(selected_outline)
        self.selected_label = _check_color(selected_label)

        if self.selected_fill is None and fill_color is not None:
            self.selected_fill = (~self.fill_color) & 0xFFFFFF
        if self.selected_outline is None and outline_color is not None:
            self.selected_outline = (~self.outline_color) & 0xFFFFFF

        if outline_color or fill_color:
            if style == Button.RECT:
                self.body = Rect(x, y, width, height,
                                 fill=self.fill_color, outline=self.outline_color)
            elif style == Button.ROUNDRECT:
                self.body = RoundRect(x, y, width, height, r=10,
                                      fill=self.fill_color, outline=self.outline_color)
            elif style == Button.SHADOWRECT:
                self.shadow = Rect(x + 2, y + 2, width - 2, height - 2,
                                   fill=outline_color)
                self.body = Rect(x, y, width - 2, height - 2,
                                 fill=self.fill_color, outline=self.outline_color)
            elif style == Button.SHADOWROUNDRECT:
                self.shadow = RoundRect(x + 2, y + 2, width - 2, height - 2, r=10,
                                        fill=self.outline_color)
                self.body = RoundRect(x, y, width - 2, height - 2, r=10,
                                      fill=self.fill_color, outline=self.outline_color)
            if self.shadow:
                self.group.append(self.shadow)
            self.group.append(self.body)

        self.label = label

        # else: # ok just a bounding box
        # self.bodyshape = displayio.Shape(width, height)
        # self.group.append(self.bodyshape)

    @property
    def label(self):
        """The text label of the button"""
        return self._label.text

    @label.setter
    def label(self, newtext):
        if self._label and self.group and (self.group[-1] == self._label):
            self.group.pop()

        self._label = None
        if not newtext or (self._label_color is None):  # no new text
            return     # nothing to do!

        if not self._label_font:
            raise RuntimeError("Please provide label font")
        self._label = Label(self._label_font, text=newtext)
        dims = self._label.bounding_box
        if dims[2] >= self.width or dims[3] >= self.height:
            raise RuntimeError("Button not large enough for label")
        self._label.x = self.x + (self.width - dims[2]) // 2
        self._label.y = self.y + self.height // 2
        self._label.color = self._label_color
        self.group.append(self._label)

        if (self.selected_label is None) and (self._label_color is not None):
            self.selected_label = (~self._label_color) & 0xFFFFFF


    @property
    def selected(self):
        """Selected inverts the colors."""
        return self._selected

    @selected.setter
    def selected(self, value):
        if value == self._selected:
            return   # bail now, nothing more to do
        self._selected = value
        if self._selected:
            new_fill = self.selected_fill
            new_out = self.selected_outline
            new_label = self.selected_label
        else:
            new_fill = self.fill_color
            new_out = self.outline_color
            new_label = self._label_color
        # update all relevant colros!
        if self.body is not None:
            self.body.fill = new_fill
            self.body.outline = new_out
        if self._label is not None:
            self._label.color = new_label

    def contains(self, point):
        """Used to determine if a point is contained within a button. For example,
        ``button.contains(touch)`` where ``touch`` is the touch point on the screen will allow for
        determining that a button has been touched.
        """
        return (self.x <= point[0] <= self.x + self.width) and (self.y <= point[1] <=
                                                                self.y + self.height)
