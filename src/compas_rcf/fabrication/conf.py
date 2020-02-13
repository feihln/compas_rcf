from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import confuse

from compas_rcf.abb.helpers import zone_dict


class ZoneDataTemplate(confuse.Template):
    def __init__(self, default=confuse.REQUIRED):
        super(ZoneDataTemplate, self).__init__(default=default)

    def convert(self, value, view):
        if isinstance(value, (int, float)):
            if not -1 >= value >= 2000:  # arbitrary max value
                self.fail(u"ZoneData needs to be from -1 to 2000", view)
            return value
        if value.upper() not in zone_dict.keys():
            self.fail(
                u"ZoneData must match one of {0}".format(", ".join(zone_dict.keys())),
                view,
            )
        return zone_dict[value.upper()]


abb_rcf_conf_template = {
    # Two following is set by command line arguments
    "debug": confuse.TypeTemplate(bool, default=False),
    "verbose": confuse.TypeTemplate(bool, default=False),
    # is_target_real is set either by command line argument, during run or in conf file
    "target": confuse.TypeTemplate(str, default=None),
    "wobjs": {"picking_wobj_name": str, "placing_wobj_name": str},
    "tool": {
        "tool_name": str,
        "io_needles_pin": str,
        "grip_state": int,
        "release_state": int,
        "wait_before_io": confuse.Number(default=2),
        "wait_after_io": confuse.Number(default=0.5),
    },
    "speed_values": {
        "speed_override": confuse.Number(default=100),
        "speed_max_tcp": float,
        "accel": float,
        "accel_ramp": confuse.Number(default=100),
    },
    "safe_joint_positions": {
        "start": confuse.Sequence([float] * 6),
        "end": confuse.Sequence([float] * 6),
    },
    "movement": {
        "offset_distance": float,
        "speed_placing": float,
        "speed_picking": float,
        "speed_travel": float,
        "zone_travel": ZoneDataTemplate(),
        "zone_pick": ZoneDataTemplate(),
        "zone_place": ZoneDataTemplate(),
    },
}


def get_numerical_zone_value(zone_data):
    """Take input and return numerical zone data.

    Parameters
    ----------
    zone_value : str, float or int
        Either zone data in mm or one of RAPID's defined variable names for zone data

    Returns
    -------
    float or int
        zone data in mm
    """
    return zone_dict[zone_data.upper()]


fabrication_conf = confuse.LazyConfig("FabricationRunner", __name__)