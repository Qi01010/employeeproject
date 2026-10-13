from .geofence import (ATTENDANCE_RADIUS_METERS, ATTENDANCE_CENTER_LATITUDE,
                       ATTENDANCE_CENTER_LONGITUDE)

def attendance_config(request):
    return {'attendance_radius': ATTENDANCE_RADIUS_METERS,
            'attendance_center_latitude': ATTENDANCE_CENTER_LATITUDE,
            'attendance_center_longitude': ATTENDANCE_CENTER_LONGITUDE}
