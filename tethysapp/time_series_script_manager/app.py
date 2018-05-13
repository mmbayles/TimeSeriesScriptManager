from tethys_sdk.base import TethysAppBase, url_map_maker


class TimeSeriesScriptManager(TethysAppBase):
    """
    Tethys app class for Time Series Manager.
    """

    name = 'Time Series Script Manager'
    index = 'time_series_script_manager:home'
    icon = 'time_series_script_manager/images/file.png'
    package = 'time_series_script_manager'
    root_url = 'time-series-script-manager'
    color = '#A78EB8'
    description = 'This application is designed to launch Python scripts using Google Colaboratory'
    tags = 'Time Series, CUAHSI, HydroShare'
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
                url='time-series-script-manager',
                controller='time_series_script_manager.controllers.home'
            ),
            UrlMap(
                name='parse_data',
                url='parse_data',
                controller='time_series_script_manager.controllers.parse_data'
            ),
            UrlMap(
                name='upload_google',
                url='upload_google',
                controller='time_series_script_manager.controllers.upload_google'
            ),
            UrlMap(
                name='view_script',
                url='view_script',
                controller='time_series_script_manager.controllers.view_script'
            ),
        )

        return url_maps
