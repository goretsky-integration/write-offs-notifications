from enums import WriteOffType
from models import RGBColor

__all__ = ('WRITE_OFF_TYPE_TO_COLOR',)

WRITE_OFF_TYPE_TO_COLOR: dict[WriteOffType, RGBColor] = {
    WriteOffType.EXPIRE_AT_15_MINUTES: RGBColor(
        red=1.0,
        green=0.8274509804,
        blue=0.2901960784,
    ),
    WriteOffType.EXPIRE_AT_10_MINUTES: RGBColor(
        red=0.9529411765,
        green=0.5254901961,
        blue=0.01176470588,
    ),
    WriteOffType.EXPIRE_AT_5_MINUTES: RGBColor(
        red=0.9529411765,
        green=0.2862745098,
        blue=0.01176470588,
    ),
    WriteOffType.ALREADY_EXPIRED: RGBColor(
        red=1.0,
        green=0.2,
        blue=0.0,
    ),
}
