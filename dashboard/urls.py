from django.urls import path
from dashboard import views

urlpatterns = [
    # ── FIXED PATHS first (must be before <str:channel_id>/) ─────
    path('', views.channels, name='channels'),
    path('create/', views.create_channel, name='create_channel'),
    path('delete/<str:channel_id>', views.delete_channel, name='delete_channel'),
    path('stats/', views.get_channel_statistics, name='channel_statistics'),
    path('api/channels/', views.ChannelList.as_view(), name='channel-list'),

    # EMBED (fixed paths)
    path('embed/channel/<str:channel_id>/', views.render_embed_code, name='render_embed_code'),
    path('embed/channel/<str:channel_id>/phChart/<str:start_date>/<str:end_date>/', views.render_ph_chart, name='render_ph_chart'),
    path('embed/channel/<str:channel_id>/humidityChart/<str:start_date>/<str:end_date>/', views.render_humidity_chart, name='render_humidity_chart'),
    path('embed/channel/<str:channel_id>/temperatureChart/<str:start_date>/<str:end_date>/', views.render_temperature_chart, name='render_temperature_chart'),
    path('embed/channel/<str:channel_id>/nitrogenChart/<str:start_date>/<str:end_date>/', views.render_nitrogen_chart, name='render_nitrogen_chart'),
    path('embed/channel/<str:channel_id>/phosphorousChart/<str:start_date>/<str:end_date>/', views.render_phosphorous_chart, name='render_phosphorous_chart'),
    path('embed/channel/<str:channel_id>/potassiumChart/<str:start_date>/<str:end_date>/', views.render_potassium_chart, name='render_potassium_chart'),
    path('embed/channel/<str:channel_id>/rainfallChart/<str:start_date>/<str:end_date>/', views.render_rainfall_chart, name='render_rainfall_chart'),

    # CHART DATA (fixed prefix paths)
    path('ph_data/<str:channel_id>/<str:start_date>/<str:end_date>/', views.getPHData, name='get_ph_data'),
    path('humidity_temperature/<str:channel_id>/<str:start_date>/<str:end_date>/', views.getHumidityTemperatureData, name='getHumidityTemperatureData'),
    path('NPK/<str:channel_id>/<str:start_date>/<str:end_date>/', views.getNPKData, name='getNPKData'),
    path('rainfall_data/<str:channel_id>/<str:start_date>/<str:end_date>/', views.getRainfallData, name='getRainfallData'),
    path('humidity_temperature/<str:channel_id>/all/', views.getHumidityTemperatureDataAll, name='getHumidityTemperatureDataAll'),
    path('ph_data/<str:channel_id>/all/', views.getPHDataAll, name='getPHDataAll'),
    path('NPK/<str:channel_id>/all/', views.getNPKDataAll, name='getNPKDataAll'),
    path('rainfall_data/<str:channel_id>/all/', views.getRainfallDataAll, name='getRainfallDataAll'),

    # ── CHANNEL-ID PATHS after all fixed paths ────────────────────
    path('<str:channel_id>/', views.view_channel_sensor, name='view_channel_sensor'),
    path('<str:channel_id>/edit', views.update_channel, name='edit_channel'),
    path('<str:channel_id>/get_dashboard_data/', views.getDashboardData, name="getDashboardData"),
    path('<str:channel_id>/share', views.share_channel, name="share_channel"),
    path('<str:channel_id>/share_chart/<str:chart_type>Chart/<str:start_date>/<str:end_date>/', views.share_chart, name="share_chart"),
    path('<str:channel_id>/share_chart/<str:chart_type>/live/', views.share_chart_live, name="share_chart_live"),
    path('embed/channel/<str:channel_id>/<str:chart_type>/live/', views.embed_live_chart, name='embed_live_chart'),
    path('<str:channel_id>/manage_sensor', views.manage_sensor, name="manage_sensor"),
    path('<str:channel_id>/edit_sensor/<str:sensor_type>/<str:sensor_id>/', views.edit_sensor, name="edit_sensor"),
    path('<str:channel_id>/add_sensor', views.add_sensor, name="add_sensor"),
    path('<str:channel_id>/unset_sensor', views.unset_sensor, name="unset_sensor"),
    path('<str:channel_id>/delete_sensor/<str:sensor_type>/', views.delete_sensor, name="delete_sensor"),
]
