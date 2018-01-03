from pywps import Process

class reservoircalculation(Process):

    """
    PyWPS process class for reservoircalculation.
    Define your WPS process here.
    The file name should NOT be changed.
    The process class name should be same with identifier. The default is lowercase app's name without space, you can modify it as you want(no space).
    """

    def __init__(self):
        inputs = []
        outputs = []

        super(reservoircalculation, self).__init__(
            self._handler,
            identifier='reservoircalculation',
            title='Name a title for your process here',
            abstract='Place a brief description of your process here',
            version='0.1',
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        return response