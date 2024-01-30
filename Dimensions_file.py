from typing import NamedTuple, Literal

INCH_IN_CM = 2.54


class Length:
    """Class for handling lengths in pixels and cm"""

    # length_px : Dimensions_pixel = (0,0)
    # length_cm : Dimensions_cm = (0.,0.)
    def __init__(self, length_in: float, unit: Literal["px", "cm"], dpi: int) -> None:
        self._dpi = dpi
        self._px_to_cm_factor = INCH_IN_CM / self._dpi
        if unit == "px":
            self.px = round(length_in)
        elif unit == "cm":
            self.cm = length_in
        else:
            raise ValueError(f"Unknown unit {unit}")

    @property
    def cm(self) -> float:
        return self.px * self._px_to_cm_factor

    @cm.setter
    def cm(self, length_cm: float) -> None:
        self.px = round(length_cm / self._px_to_cm_factor)

    @property
    def dpi(self) -> int:
        return self._dpi


class Dimensions_px(NamedTuple):
    width: int
    height: int


class Dimensions_cm(NamedTuple):
    width: float
    height: float


class Dimensions:
    """Class for handling dimensions in pixels and cm"""

    def __init__(
        self, width: float, height: float, unit: Literal["px", "cm"], dpi: int
    ) -> None:
        self._dpi = dpi
        self._px_to_cm_factor = INCH_IN_CM / self._dpi
        self.instanciated_as = unit  # for debugging only
        if unit == "px":
            self.dim_px = Dimensions_px(width, height)
        elif unit == "cm":
            self.dim_cm = Dimensions_cm(width, height)
        else:
            raise ValueError(f"Unknown unit {unit}")

    # Alternative constructor to allow for passing in Length objects
    @classmethod
    def from_length(cls, width: Length, height: Length) -> None:
        assert width.dpi == height.dpi, "DPI mismatch"
        return cls(width=width.cm, height=height.cm, unit="cm", dpi=width.dpi)

    @property
    def dpi(self) -> int:
        return self._dpi

    @property
    def dim_px(self) -> Dimensions_px:
        return self._dim_px

    @dim_px.setter
    def dim_px(self, dim_px: Dimensions_px) -> None:
        self._dim_px = dim_px

    @property
    def dim_cm(self) -> Dimensions_cm:
        return Dimensions_cm(
            self.dim_px.width * self._px_to_cm_factor,
            self.dim_px.height * self._px_to_cm_factor,
        )

    @dim_cm.setter
    def dim_cm(self, dim_cm: Dimensions_cm) -> None:
        self.dim_px = Dimensions_px(
            round(dim_cm.width / self._px_to_cm_factor),
            round(dim_cm.height / self._px_to_cm_factor),
        )

    @property
    def width_px(self) -> int:
        return self.dim_px.width

    @property
    def width_cm(self) -> int:
        return self.dim_cm.width

    @property
    def height_px(self) -> int:
        return self.dim_px.height

    @property
    def height_cm(self) -> int:
        return self.dim_cm.height

    def add(self, other: "Dimensions") -> "Dimensions":
        assert self._dpi == other._dpi, "DPI mismatch"
        return Dimensions(
            self.width_cm + other.width_cm,
            self.height_cm + other.height_cm,
            unit="cm",
            dpi=self._dpi,
        )

    def scale(self, factor: float) -> "Dimensions":
        return Dimensions(
            self.width_cm * factor, self.height_cm * factor, unit="cm", dpi=self._dpi
        )


class Position(Dimensions):
    # Alternative syntax for the Dimensions class for storing positions
    @property
    def x_px(self):
        return super().width_px

    @property
    def y_px(self):
        return super().height_px

    @property
    def x_cm(self):
        return super().width_cm

    @property
    def y_cm(self):
        return super().height_cm

    @property
    def xy_px(self):
        return super().dim_px

    @property
    def xy_cm(self):
        return super().dim_cm


if __name__ == "__main__":
    from book_poster_creator import main

    main()
