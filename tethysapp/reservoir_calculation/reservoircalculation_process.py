import os
import binascii
from pywps import Process, LiteralInput, LiteralOutput, ComplexInput, ComplexOutput, Format, FORMATS
from tethys_apps.tethysapp.reservoir_calculation.grassfunctions import RC

class reservoircalculationprocess(Process):

    """
    PyWPS process class for reservoircalculation.
    Define your WPS process here.
    The file name should NOT be changed.
    The process class name should be same with identifier. The default is lowercase app's name without space, you can modify it as you want(no space).
    """

    def __init__(self):
        inputs = [LiteralInput('point_x', 'Pour Point Longitude', data_type='float'),
                  LiteralInput('point_y', 'Pour Point Latitude', data_type='float'),
                  LiteralInput('water_level', 'Water level at pour point', data_type='float'),
                  ComplexInput('max_boundary', 'Maximum Reservior Boundary', supported_formats=[Format('application/gml+xml')])]
        outputs = [LiteralOutput('lake_volume', 'Reservoir volume in cubic meters', data_type='float'),
            ComplexOutput('lake_boundary', 'Reservoir boundary polygon', supported_formats=[Format('application/gml+xml')])]

        super(reservoircalculationprocess, self).__init__(
            self._handler,
            identifier='reservoircalculationprocess',
            title='Reservoir Calculation Service',
            abstract='Place a brief description of your process here',
            version='1.0',
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        # get input values
        xlon = request.inputs['point_x'][0].data
        ylat = request.inputs['point_y'][0].data
        water_level = request.inputs['water_level'][0].data
        boundary_geojson=request.inputs['max_boundary'][0].data
        prj = "native"
        string_length = 4
        jobid = binascii.hexlify(os.urandom(string_length))
        message = ""


        # Run RC()
        RC_dict = RC(jobid, boundary_geojson, xlon, ylat, water_level, prj)

        lake_GEOJSON = RC_dict["lake_GEOJSON"]
        lake_volume = RC_dict["lake_volume"]

        response.outputs['lake_boundary'].output_format = FORMATS.GML
        response.outputs['lake_boundary'].file = lake_GEOJSON
        response.outputs['lake_volume'].data = lake_volume

        return response