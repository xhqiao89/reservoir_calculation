from tethys_sdk.base import TethysAppBase, url_map_maker


class ReservoirCalculation(TethysAppBase):
    """
    Tethys app class for Reservoir Calculation App.
    """

    name = 'Reservoir Calculation for Dominican Republic'
    index = 'reservoir_calculation:home'
    icon = 'reservoir_calculation/images/reservoiricon.png'
    package = 'reservoir_calculation'
    root_url = 'reservoir-calculation'
    color = '#33c1ff'
    description = 'This app allows you to calculate the reservoir boudary and volume with a designed pour point and water level in Dominican Republic country. '
    tags = ''
    enable_feedback = False
    feedback_emails = []

    def url_maps(self):
        """
        Add controllers
        """
        UrlMap = url_map_maker(self.root_url)

        url_maps = (
            UrlMap(
                name='home',
                url='reservoir-calculation',
                controller='reservoir_calculation.controllers.home'
            ),
            UrlMap(name='run',
                   url='reservoir-calculation/run',
                   controller='reservoir_calculation.controllers.run_rc')
        )

        return url_maps
