from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Zone:
    zone_id: str
    polygon: list[tuple[float, float]]


def point_in_polygon(x: float, y: float, polygon: list[tuple[float, float]]) -> bool:
    inside = False
    n = len(polygon)
    for i in range(n):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % n]
        intersects = ((y1 > y) != (y2 > y)) and (
            x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-9) + x1
        )
        if intersects:
            inside = not inside
    return inside


class ZoneAssigner:
    def __init__(self, zones: list[Zone]) -> None:
        self.zones = zones

    def assign(self, x_center: float, y_bottom: float) -> str | None:
        for zone in self.zones:
            if point_in_polygon(x_center, y_bottom, zone.polygon):
                return zone.zone_id
        return None


def default_zones(frame_width: int, frame_height: int) -> list[Zone]:
    w, h = frame_width, frame_height
    return [
        Zone("ENTRY", [(0, h * 0.8), (w * 0.2, h * 0.8), (w * 0.2, h), (0, h)]),
        Zone("FOH", [(w * 0.2, h * 0.6), (w * 0.8, h * 0.6), (w * 0.8, h), (w * 0.2, h)]),
        Zone("FRAGRANCE", [(w * 0.2, 0), (w * 0.4, 0), (w * 0.4, h * 0.6), (w * 0.2, h * 0.6)]),
        Zone("MAKEUP", [(w * 0.4, 0), (w * 0.8, 0), (w * 0.8, h * 0.6), (w * 0.4, h * 0.6)]),
        Zone("BILLING", [(w * 0.8, h * 0.6), (w, h * 0.6), (w, h), (w * 0.8, h)]),
    ]
