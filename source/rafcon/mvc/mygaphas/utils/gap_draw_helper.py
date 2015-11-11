from math import pi

from gtk.gdk import Color
from pango import SCALE, FontDescription
from cairo import ANTIALIAS_SUBPIXEL

from rafcon.mvc.mygaphas.utils.enums import SnappedSide
from rafcon.utils import constants
from rafcon.utils.geometry import deg2rad


def limit_value_string_length(value):
    """
    This method limits the string representation of the value to MAX_VALUE_LABEL_TEXT_LENGTH + 3 characters.
    :param value: Value to limit string representation
    :return: String holding the value with a maximum length of MAX_VALUE_LABEL_TEXT_LENGTH + 3
    """
    if isinstance(value, str) and len(value) > constants.MAX_VALUE_LABEL_TEXT_LENGTH:
        value = value[:constants.MAX_VALUE_LABEL_TEXT_LENGTH] + "..."
        final_string = " " + value + " "
    elif isinstance(value, (dict, list)) and len(str(value)) > constants.MAX_VALUE_LABEL_TEXT_LENGTH:
        value_text = str(value)[:constants.MAX_VALUE_LABEL_TEXT_LENGTH] + "..."
        final_string = " " + value_text + " "
    else:
        final_string = " " + str(value) + " "

    return final_string


def get_col_rgba(col, transparent=False, alpha=None):
    """
    This class converts a gtk.gdk.Color into its r, g, b parts and adds an alpha according to needs
    :param col: Color to extract r, g and b from
    :param transparent: Whether the color shoud be tranparent or not (used for selection in "data-flow-mode"
    :return: Red, Green, Blue and Alpha value (all betwenn 0.0 - 1.0)
    """
    r, g, b = col.red, col.green, col.blue
    r /= 65535.
    g /= 65535.
    b /= 65535.
    if transparent:
        a = .25
    else:
        a = 1.

    if alpha:
        a = alpha
    return r, g, b, a


def get_side_length_of_resize_handle(view, state_v):
    """Calculate the side length of a resize handle

    :param rafcon.mvc.mygaphas.view.ExtendedGtkView view: View
    :param rafcon.mvc.mygaphas.items.state.StateView state_v: StateView
    :return: side length
    :rtype: float
    """
    return state_v.port_side_size * view.get_zoom_factor() / 1.5


def draw_data_value_rect(cairo_context, color, value_size, name_size, pos, port_side):
    """
    This method draws the containing rect for the data port value, depending on the side and size of the label.
    :param context: Draw Context
    :param color: Background color of value part
    :param value_size: Size (width, height) of label holding the value
    :param name_size: Size (width, height) of label holding the name
    :param pos: Position of name label start point (upper left corner of label)
    :param port_side: Side on which the value part should be drawn
    :return: Rotation Angle (to rotate value accordingly), X-Position of value label start point, Y-Position
             of value label start point
    """
    c = cairo_context

    rot_angle = .0
    move_x = 0.
    move_y = 0.

    if port_side is SnappedSide.RIGHT:
        move_x = pos[0] + name_size[0]
        move_y = pos[1]

        c.rectangle(move_x, move_y, value_size[0], value_size[1])
    elif port_side is SnappedSide.BOTTOM:
        move_x = pos[0] - value_size[1]
        move_y = pos[1] + name_size[0]
        rot_angle = pi / 2.

        c.rectangle(move_x, move_y, value_size[1], value_size[0])
    elif port_side is SnappedSide.LEFT:
        move_x = pos[0] - value_size[0]
        move_y = pos[1]

        c.rectangle(move_x, move_y, value_size[0], value_size[1])
    elif port_side is SnappedSide.TOP:
        move_x = pos[0] - value_size[1]
        move_y = pos[1] - value_size[0]
        rot_angle = -pi / 2.

        c.rectangle(move_x, move_y, value_size[1], value_size[0])

    c.set_source_rgba(*color)
    c.fill_preserve()
    c.set_source_color(Color(constants.BLACK_COLOR))
    c.stroke()

    return rot_angle, move_x, move_y


def draw_connected_scoped_label(context, color, name_size, handle_pos, port_side, port_side_size,
                                draw_connection_to_port=False):
    """
    This method draws the label of a scoped variable connected to a data port. This is represented by drawing a bigger
    label where the top part is filled and the bottom part isn't.
    :param context: Draw Context
    :param color: Color to draw the label in (border and background fill color)
    :param name_size: Size of the name labels (scoped variable and port name) combined
    :param handle_pos: Position of port which label is connected to
    :param port_side: Side on which the label should be drawn
    :param port_side_size: Size of port (to have a relative size)
    :param draw_connection_to_port: Whether there should be a line connecting the label to the port
    :return: Rotation Angle (to rotate names accordingly), X-Position of name labels start point, Y-Position
             of name labels start point
    """
    c = context.cairo
    c.set_line_width(port_side_size * .03)

    c.set_source_color(Color(color))

    rot_angle = .0
    move_x = 0.
    move_y = 0.

    if port_side is SnappedSide.RIGHT:
        move_x = handle_pos.x + 2 * port_side_size
        move_y = handle_pos.y - name_size[1] / 2.

        c.move_to(move_x + name_size[0], move_y + name_size[1] / 2.)
        c.line_to(move_x + name_size[0], move_y)
        c.line_to(move_x, move_y)
        c.line_to(handle_pos.x + port_side_size, handle_pos.y)
        c.fill_preserve()
        c.stroke()
        if draw_connection_to_port:
            c.line_to(handle_pos.x + port_side_size / 2., handle_pos.y)
            c.line_to(handle_pos.x + port_side_size, handle_pos.y)
        else:
            c.move_to(handle_pos.x + port_side_size, handle_pos.y)
        c.line_to(move_x, move_y + name_size[1])
        c.line_to(move_x + name_size[0], move_y + name_size[1])
        c.line_to(move_x + name_size[0], move_y + name_size[1] / 2.)
    elif port_side is SnappedSide.BOTTOM:
        move_x = handle_pos.x + name_size[1] / 2.
        move_y = handle_pos.y + 2 * port_side_size
        rot_angle = pi / 2.

        c.move_to(move_x - name_size[1] / 2., move_y + name_size[0])
        c.line_to(move_x, move_y + name_size[0])
        c.line_to(move_x, move_y)
        c.line_to(handle_pos.x, move_y - port_side_size)
        c.fill_preserve()
        c.stroke()
        if draw_connection_to_port:
            c.line_to(handle_pos.x, handle_pos.y + port_side_size / 2.)
            c.line_to(handle_pos.x, move_y - port_side_size)
        else:
            c.move_to(handle_pos.x, move_y - port_side_size)
        c.line_to(move_x - name_size[1], move_y)
        c.line_to(move_x - name_size[1], move_y + name_size[0])
        c.line_to(move_x - name_size[1] / 2., move_y + name_size[0])
    elif port_side is SnappedSide.LEFT:
        move_x = handle_pos.x - 2 * port_side_size - name_size[0]
        move_y = handle_pos.y - name_size[1] / 2.

        c.move_to(move_x, move_y + name_size[1] / 2.)
        c.line_to(move_x, move_y)
        c.line_to(move_x + name_size[0], move_y)
        c.line_to(handle_pos.x - port_side_size, move_y + name_size[1] / 2.)
        c.fill_preserve()
        c.stroke()
        if draw_connection_to_port:
            c.line_to(handle_pos.x - port_side_size / 2., handle_pos.y)
            c.line_to(handle_pos.x - port_side_size, handle_pos.y)
        else:
            c.move_to(handle_pos.x - port_side_size, move_y + name_size[1] / 2.)
        c.line_to(move_x + name_size[0], move_y + name_size[1])
        c.line_to(move_x, move_y + name_size[1])
        c.line_to(move_x, move_y + name_size[1] / 2.)
    elif port_side is SnappedSide.TOP:
        move_x = handle_pos.x - name_size[1] / 2.
        move_y = handle_pos.y - 2 * port_side_size
        rot_angle = -pi / 2.

        c.move_to(move_x + name_size[1] / 2., move_y - name_size[0])
        c.line_to(move_x, move_y - name_size[0])
        c.line_to(move_x, move_y)
        c.line_to(handle_pos.x, move_y + port_side_size)
        c.fill_preserve()
        c.stroke()
        if draw_connection_to_port:
            c.line_to(handle_pos.x, handle_pos.y - port_side_size / 2.)
            c.line_to(handle_pos.x, move_y + port_side_size)
        else:
            c.move_to(handle_pos.x, move_y + port_side_size)
        c.line_to(move_x + name_size[1], move_y)
        c.line_to(move_x + name_size[1], move_y - name_size[0])
        c.line_to(move_x + name_size[1] / 2., move_y - name_size[0])
    c.stroke()

    return rot_angle, move_x, move_y


def draw_port_label(context, text, label_color, text_color, transparency, fill, label_position, port_side_length,
                    draw_connection_to_port=False, show_additional_value=False, additional_value=None,
                    only_extent_calculations=False):
    """
    Draws a normal label indicating the port name.
    :param context: Draw Context
    :param text: Text to display
    :param label_color: Color of the label (border and background if fill is set to True)
    :param text_color: Color of the text
    :param transparency: Transparency of the text
    :param fill: Whether the label should be filled or not
    :param label_position: Side on which the label should be drawn
    :param port_side_length: Side length of port
    :param draw_connection_to_port: Whether there should be a line connecting the label to the port
    :param show_additional_value: Whether to show an additional value (for data ports)
    :param additional_value: The additional value to be shown
    :param only_extent_calculations: Calculate only the extends and do not actually draw
    """
    c = context
    c.set_antialias(ANTIALIAS_SUBPIXEL)

    port_position = c.get_current_point()

    layout = c.create_layout()
    layout.set_text(text)

    font_name = constants.FONT_NAMES[0]
    font_size = port_side_length
    font = FontDescription(font_name + " " + str(font_size))
    layout.set_font_description(font)
    text_size = (layout.get_size()[0] / float(SCALE), layout.get_size()[1] / float(SCALE))

    # margin is the distance between the text and the border line
    margin = port_side_length / 4.
    # The text_size dimensions are rotated by 90 deg compared to the label, as the label is drawn upright
    width = text_size[1] + 2 * margin
    arrow_height = port_side_length
    height = arrow_height + text_size[0] + 2 * margin
    port_distance = port_side_length

    if label_position is SnappedSide.RIGHT:
        label_angle = deg2rad(-90)
        text_angle = 0
    elif label_position is SnappedSide.BOTTOM:
        label_angle = 0
        text_angle = deg2rad(-90)
    elif label_position is SnappedSide.LEFT:
        label_angle = deg2rad(90)
        text_angle = 0
    elif label_position is SnappedSide.TOP:
        label_angle = deg2rad(180)
        text_angle = deg2rad(90)

    # Draw (filled) outline of label
    c.move_to(*port_position)
    c.save()
    c.rotate(label_angle)
    draw_label_path(c, width, height, arrow_height, port_distance, draw_connection_to_port)
    c.restore()

    c.set_line_width(port_side_length * .03)
    c.set_source_rgba(*label_color)
    label_extents = c.stroke_extents()

    if only_extent_calculations:
        c.new_path()
    else:
        if fill:
            c.fill_preserve()
        c.stroke()

        # Move to the upper left corner of the desired text position
        c.save()
        c.move_to(*port_position)
        c.rotate(label_angle)
        c.rel_move_to(-text_size[1] / 2., text_size[0] + port_distance + arrow_height + margin)
        c.restore()

        # Show text in correct orientation
        c.save()
        c.rotate(text_angle)
        # Correction for labels positioned right: as the text is mirrored, the anchor point must be moved
        if label_position is SnappedSide.RIGHT:
            c.rel_move_to(-text_size[0], -text_size[1])
        c.set_source_rgba(*get_col_rgba(Color(text_color), transparency))
        c.update_layout(layout)
        c.show_layout(layout)
        c.restore()

    if show_additional_value:
        value_text = limit_value_string_length(additional_value)
        value_layout = c.create_layout()
        value_layout.set_text(value_text)
        value_layout.set_font_description(font)
        value_text_size = (value_layout.get_size()[0] / float(SCALE), text_size[1] / float(SCALE))

        # Move to the upper left corner of the additional value box
        c.save()
        c.move_to(*port_position)
        c.rotate(label_angle)
        c.rel_move_to(-width / 2., height + port_distance)
        # Draw rectangular path
        c.rel_line_to(width, 0)
        c.rel_line_to(0, value_text_size[0] + 2 * margin)
        c.rel_line_to(-width, 0)
        c.close_path()
        c.restore()

        value_extents = c.stroke_extents()

        if only_extent_calculations:
            c.new_path()
        else:
            # Draw filled outline
            c.set_source_rgba(*get_col_rgba(Color(constants.DATA_VALUE_BACKGROUND_COLOR)))
            c.fill_preserve()
            c.set_source_color(Color(constants.BLACK_COLOR))
            c.stroke()

            # Move to the upper left corner of the desired text position
            c.save()
            c.move_to(*port_position)
            c.rotate(label_angle)
            c.rel_move_to(-text_size[1] / 2., value_text_size[0] + margin + height + port_distance)
            c.restore()

            # Show text in correct orientation
            c.save()
            c.rotate(text_angle)
            # Correction for labels positioned right: as the text is mirrored, the anchor point must be moved
            if label_position is SnappedSide.RIGHT:
                c.rel_move_to(-value_text_size[0], -text_size[1])
            c.set_source_rgba(*get_col_rgba(Color(constants.SCOPED_VARIABLE_TEXT_COLOR)))
            c.update_layout(value_layout)
            c.show_layout(value_layout)
            c.restore()

        label_extents = min(label_extents[0], value_extents[0]), min(label_extents[1], value_extents[1]), \
                        max(label_extents[2], value_extents[2]), max(label_extents[3], value_extents[3])

    return label_extents


def draw_label_path(context, width, height, arrow_height, distance_to_port, draw_connection_to_port):
    """Draws the path for an upright label

    :param context: The Cairo context
    :param float width: Width of the label
    :param float height: Height of the label
    :param float distance_to_port: Distance to the port related to the label
    :param bool draw_connection_to_port: Whether to draw a line from the tip of the label to the port
    """
    c = context
    # The current point is the port position

    # If a connector is to be drawn, the first command is a line to the tip of the label
    if draw_connection_to_port:
        c.rel_line_to(0, distance_to_port)
    # Otherwise we first move the current point to the tip of the label
    else:
        c.rel_move_to(0, distance_to_port)

    # Line to upper left corner
    c.rel_line_to(-width / 2., arrow_height)
    # Line to lower left corner
    c.rel_line_to(0, height - arrow_height)
    # Line to lower right corner
    c.rel_line_to(width, 0)
    # Line to upper right corner
    c.rel_line_to(0, -(height - arrow_height))
    # Line to center top (tip of label)
    c.rel_line_to(-width / 2., -arrow_height)
    # Close path
    c.close_path()


def get_text_layout(cairo_context, text, size):
    c = cairo_context
    layout = c.create_layout()
    layout.set_text(text)

    font_name = constants.FONT_NAMES[0]

    font = FontDescription(font_name + " " + str(size))
    layout.set_font_description(font)

    return layout