
def execute(self, inputs, outputs, gvm):
    self.logger.debug("Hello world")
    outputs["out"] = 10.0
    return 0
