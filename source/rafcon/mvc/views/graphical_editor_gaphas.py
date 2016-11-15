import gtk
import gobject

from gtkmvc import View

from gaphas import tool
from gaphas import painter

from rafcon.mvc.mygaphas.view import ExtendedGtkView
from rafcon.mvc.mygaphas.tools import HoverItemTool, ConnectionCreationTool, ConnectionModificationTool, \
    RemoveItemTool, MoveItemTool, MultiSelectionTool, RightClickTool, MoveHandleTool
from rafcon.mvc.mygaphas.painter import StateCornerHandlePainter, NameCornerHandlePainter

from rafcon.mvc.config import global_gui_config
from rafcon.utils import log

logger = log.get_logger(__name__)


class GraphicalEditorView(View, gobject.GObject):
    top = 'main_frame'

    def __init__(self):
        """View holding the graphical editor

        The purpose of the view is only to hold the graphical editor. The class ob the actual editor with the OpenGL
        functionality is GraphicalEditor
        """
        gobject.GObject.__init__(self)
        View.__init__(self)

        self.v_box = gtk.VBox()
        self.scroller = gtk.ScrolledWindow()
        self.scroller.set_name('graphical_editor_scroller')
        self.editor = ExtendedGtkView()
        self.editor.modify_bg(gtk.STATE_NORMAL, global_gui_config.gtk_colors['INPUT_BACKGROUND'])
        self.editor.tool = tool.ToolChain(self.editor). \
            append(HoverItemTool()). \
            append(MoveHandleTool()). \
            append(ConnectionCreationTool()). \
            append(ConnectionModificationTool()). \
            append(tool.PanTool()). \
            append(tool.ZoomTool()). \
            append(MoveItemTool(self)). \
            append(MultiSelectionTool(self)). \
            append(RemoveItemTool(self)). \
            append(RightClickTool(self))
        self.editor.painter = painter.PainterChain(). \
            append(painter.ItemPainter()). \
            append(StateCornerHandlePainter()). \
            append(NameCornerHandlePainter()). \
            append(painter.FocusedItemPainter()). \
            append(painter.ToolPainter())
        self.scroller.add(self.editor)
        self.v_box.pack_end(self.scroller)

        self['main_frame'] = self.v_box

    def setup_canvas(self, canvas, zoom):
        self.editor.canvas = canvas
        self.editor.zoom(zoom)
        self.editor.set_size_request(0, 0)


gobject.type_register(GraphicalEditorView)
gobject.signal_new('remove_state_from_state_machine', GraphicalEditorView, gobject.SIGNAL_RUN_FIRST, None,
                   ())
gobject.signal_new('meta_data_changed', GraphicalEditorView, gobject.SIGNAL_RUN_FIRST, None,
                   (gobject.TYPE_PYOBJECT, gobject.TYPE_STRING, gobject.TYPE_BOOLEAN,))
