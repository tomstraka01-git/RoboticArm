import math
from dataclasses import dataclass
from typing import Optional


@dataclass
class Position:
    x: float
    y: float
    z: float


class RobotKinematics:
    """
    Forward and Inverse Kinematics for a 4-DOF robotic arm + gripper.

    Arm segment lengths (mm) can be overridden in the constructor.

    Usage:
        from kinematics import RobotKinematics, Position

        kin = RobotKinematics()

        # Inverse kinematics
        angles = kin.solve_ik(x=100, y=0, z=80, phi_deg=90)
        if angles:
            base, shoulder, elbow, wrist = angles

        # Forward kinematics
        pos = kin.solve_fk(base=90, shoulder=90, elbow=90, wrist=90)
        print(pos.x, pos.y, pos.z)
    """

    def __init__(
        self,
        H0: float = 50.0,
        L1: float = 105.0,
        L2: float = 100.0,
        L3: float = 35.0,
        Lg: float = 60.0,
    ):
        """
        H0  - base height offset (mm)
        L1  - shoulder-to-elbow length (mm)
        L2  - elbow-to-wrist length (mm)
        L3  - wrist-to-gripper-base length (mm)
        Lg  - gripper length (mm)
        """
        self.H0 = H0
        self.L1 = L1
        self.L2 = L2
        self.L3 = L3
        self.Lg = Lg

    def solve_fk(
        self,
        base: float,
        shoulder: float,
        elbow: float,
        wrist: float,
    ) -> Position:
        """
        Forward Kinematics: servo angles (degrees, 0-180) -> gripper position.

        The angles are offset by 90 internally to match the physical neutral
        position (same convention as the C++ code).

        Returns a Position(x, y, z) in mm.
        """
        t0 = math.radians(base - 90)
        t1 = math.radians(shoulder - 90)
        t2 = math.radians(elbow - 90)
        t3 = math.radians(wrist - 90)
        phi = t1 + t2 + t3

        r = (
            self.L1 * math.cos(t1)
            + self.L2 * math.cos(t1 + t2)
            + (self.L3 + self.Lg) * math.cos(phi)
        )
        z = (
            self.H0
            + self.L1 * math.sin(t1)
            + self.L2 * math.sin(t1 + t2)
            + (self.L3 + self.Lg) * math.sin(phi)
        )

        return Position(
            x=r * math.cos(t0),
            y=r * math.sin(t0),
            z=z,
        )

    def solve_ik(
        self,
        x: float,
        y: float,
        z: float,
        phi_deg: float = 0.0,
    ) -> Optional[tuple[int, int, int, int]]:
        """
        Inverse Kinematics: gripper position -> servo angles (degrees, 0-180).

        phi_deg - gripper pitch angle in degrees.
                  0   = horizontal
                  -90 = pointing straight down

        Returns (base, shoulder, elbow, wrist) as integer servo angles (0-180),
        or None if the target position is unreachable.
        """
        phi = math.radians(phi_deg - 90.0)

        theta0 = math.atan2(y, x)

        r  = math.sqrt(x**2 + y**2) - self.L3 * math.cos(phi)
        zw = z - self.H0 - self.L3 * math.sin(phi)

        r  -= self.Lg * math.cos(phi)
        zw -= self.Lg * math.sin(phi)

        dist = math.sqrt(r**2 + zw**2)
        if dist > (self.L1 + self.L2) or dist < abs(self.L1 - self.L2):
            return None  # unreachable

        cos_theta2 = (r**2 + zw**2 - self.L1**2 - self.L2**2) / (
            2.0 * self.L1 * self.L2
        )
        cos_theta2 = max(-1.0, min(1.0, cos_theta2))  # clamp for acos safety
        theta2 = math.acos(cos_theta2)

        k1 = self.L1 + self.L2 * math.cos(theta2)
        k2 = self.L2 * math.sin(theta2)
        theta1 = math.atan2(zw, r) - math.atan2(k2, k1)

        theta3 = -(theta1 + theta2) + phi

        # Convert to degrees and apply servo offsets
        base     = self._clamp(int(math.degrees(theta0) + 90))
        shoulder = self._clamp(int(math.degrees(theta1) + 90))
        elbow    = self._clamp(int(math.degrees(theta2) - 90))
        wrist    = self._clamp(int(math.degrees(theta3) + 90))

        return base, shoulder, elbow, wrist

    @staticmethod
    def _clamp(angle: int, lo: int = 0, hi: int = 180) -> int:
        return max(lo, min(hi, angle))