
from gtkmvc import ModelMT
from awesome_tool.statemachine.data_flow import DataFlow
from awesome_tool.utils.vividict import Vividict


class DataFlowModel(ModelMT):
    """This model class manages a DataFlow

    The model class is part of the MVC architecture. It holds the data to be shown (in this case a data flow).

    :param DataFlow data_flow: The data flow to be managed
     """

    data_flow = None

    __observables__ = ("data_flow",)

    def __init__(self, data_flow, parent, meta=None):
        """Constructor
        """

        ModelMT.__init__(self)  # pass columns as separate parameters
        
        assert isinstance(data_flow, DataFlow)
        self.parent = parent

        self.data_flow = data_flow

        if isinstance(meta, Vividict):
            self.meta = meta
        else:
            self.meta = Vividict()

        # this class is an observer of its own properties:
        self.register_observer(self)

    @ModelMT.observe("data_flow", before=True, after=True)
    def model_changed(self, model, name, info):
        if self.parent is not None:
            self.parent.model_changed(model, name, info)
