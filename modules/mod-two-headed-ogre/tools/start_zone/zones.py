"""Zone of a position, read from the server data (maps/*.map area grids and dbc/AreaTable.dbc).

The world database leaves creature.zoneId at 0, so the start zone generator finds Blade's Edge
creatures from their coordinates instead.
"""

import os
import struct

SIZE_OF_GRIDS = 533.33333


class Zones:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self._grids = {}
        self._parent = {}
        with open(os.path.join(data_dir, "dbc", "AreaTable.dbc"), "rb") as handle:
            data = handle.read()
        _, count, fields, record_size, _ = struct.unpack_from("<4sIIII", data)
        for i in range(count):
            area_id, _map_id, zone_id = struct.unpack_from("<III", data, 20 + i * record_size)
            self._parent[area_id] = zone_id

    def _grid(self, map_id, gx, gy):
        key = (map_id, gx, gy)
        if key not in self._grids:
            path = os.path.join(self.data_dir, "maps", "%03d%02d%02d.map" % (map_id, gx, gy))
            area = None
            if os.path.exists(path):
                with open(path, "rb") as handle:
                    data = handle.read()
                offset = struct.unpack_from("<11I", data)[3]                  # areaMapOffset
                _fourcc, flags, grid_area = struct.unpack_from("<IHH", data, offset)
                area = grid_area if flags & 1 else struct.unpack_from("<256H", data, offset + 8)
            self._grids[key] = area
        return self._grids[key]

    def area_at(self, map_id, x, y):
        fx = 32 - x / SIZE_OF_GRIDS
        fy = 32 - y / SIZE_OF_GRIDS
        area = self._grid(map_id, int(fx), int(fy))
        if area is None or isinstance(area, int):
            return area
        return area[(int(16 * fx) & 15) * 16 + (int(16 * fy) & 15)]

    def zone_at(self, map_id, x, y):
        area = self.area_at(map_id, x, y)
        if not area:
            return 0
        return self._parent.get(area) or area
