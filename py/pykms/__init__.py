from .pykms import *
from enum import Enum
import os
import struct

#
# Common RGB colours
#

red = RGB(255, 0, 0)
green = RGB(0, 255, 0)
blue = RGB(0, 0, 255)
yellow = RGB(255, 255, 0)
purple = RGB(255, 0, 255)
white = RGB(255, 255, 255)
cyan = RGB(0, 255, 255)

#
# DrmObject API extensions
#

def __obj_set_prop(self, prop, value):
    if self.card.has_atomic:
        areq = AtomicReq(self.card)
        areq.add(self, prop, value)
        if areq.commit_sync() != 0:
            print("commit failed")
    else:
        if self.set_prop_value(prop, value) != 0:
            print("setting property failed")

def __obj_set_props(self, map):
    if self.card.has_atomic:
        areq = AtomicReq(self.card)

        for key, value in map.items():
            areq.add(self, key, value)

        if areq.commit_sync() != 0:
            print("commit failed")
    else:
        for propid,propval in map.items():
            if self.set_prop_value(propid, propval) != 0:
                print("setting property failed")

DrmObject.set_prop = __obj_set_prop
DrmObject.set_props = __obj_set_props

#
# Card API extensions
#

def __card_disable_planes(self):
    areq = AtomicReq(self)

    for p in self.planes:
        areq.add(p, "FB_ID", 0)
        areq.add(p, "CRTC_ID", 0)

    if areq.commit_sync() != 0:
        print("disabling planes failed")

Card.disable_planes = __card_disable_planes

class DrmEventType(Enum):
    VBLANK = 0x01
    FLIP_COMPLETE = 0x02

# struct drm_event {
#   __u32 type;
#   __u32 length;
#};
#

_drm_ev = struct.Struct("II")

#struct drm_event_vblank {
#   struct drm_event base;
#   __u64 user_data;
#   __u32 tv_sec;
#   __u32 tv_usec;
#   __u32 sequence;
#   __u32 reserved;
#};

_drm_ev_vbl = struct.Struct("QIIII") # Note: doesn't contain drm_event

class DrmEvent:
    def __init__(self, type, seq, time, data):
        self.type = type
        self.seq = seq
        self.time = time
        self.data = data

# Return DrmEvents. Note: blocks if there's nothing to read
def __card_read_events(self):
    buf = os.read(self.fd, _drm_ev_vbl.size * 20)

    if len(buf) == 0:
        return

    if len(buf) < _drm_ev.size:
        raise RuntimeError("Partial DRM event")

    idx = 0

    while idx < len(buf):
        ev_tuple = _drm_ev.unpack_from(buf, idx)

        type = DrmEventType(ev_tuple[0])

        if type != DrmEventType.VBLANK and type != DrmEventType.FLIP_COMPLETE:
            raise RuntimeError("Illegal DRM event type")

        vbl_tuple = _drm_ev_vbl.unpack_from(buf, idx + _drm_ev.size)

        seq = vbl_tuple[3]
        time = vbl_tuple[1] + vbl_tuple[2] / 1000000.0;
        udata = pykms.__ob_unpack_helper(vbl_tuple[0])

        yield DrmEvent(type, seq, time, udata)

        idx += ev_tuple[1]

Card.read_events = __card_read_events
