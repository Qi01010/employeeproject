import math

ATTENDANCE_RADIUS_METERS = 200
MAX_ACCURACY_METERS = 100

# จุดคงที่จากหมุด Google Maps ที่ผู้ใช้ส่งมา (คณะวิทยาศาสตร์ฯ มรภ.กำแพงเพชร)
ATTENDANCE_CENTER_LATITUDE = 16.4511111111
ATTENDANCE_CENTER_LONGITUDE = 99.5133611111


def parse_position(data):
    values = []
    for key in ('latitude', 'longitude', 'accuracy'):
        raw = data.get(key)
        if isinstance(raw, bool) or not isinstance(raw, (str, int, float)):
            raise ValueError('กรุณาส่งตำแหน่ง GPS และค่าความแม่นยำให้ครบ')
        try:
            value = float(raw)
        except (ValueError, TypeError, OverflowError):
            raise ValueError('ข้อมูลตำแหน่ง GPS ไม่ถูกต้อง')
        if not math.isfinite(value):
            raise ValueError('ข้อมูลตำแหน่ง GPS ไม่ถูกต้อง')
        values.append(value)
    lat, lng, accuracy = values
    if not -90 <= lat <= 90 or not -180 <= lng <= 180 or accuracy < 0:
        raise ValueError('ข้อมูลตำแหน่ง GPS ไม่ถูกต้อง')
    if accuracy > MAX_ACCURACY_METERS:
        raise ValueError('ตำแหน่งคลาดเคลื่อนเกิน 100 เมตร กรุณาลองใหม่ในจุดที่รับสัญญาณได้ดี')
    return lat, lng, accuracy


def distance_meters(lat1, lng1, lat2, lng2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371000 * 2 * math.asin(math.sqrt(min(1.0, max(0.0, a))))


