class CocoBbox:
    """Class that represents a COCO-style bounding box.
    
    COCO bounding box is a quadruplet of integers [l, t, w, h]
    with values being left, top, width, height in pixels.
    """
    def __init__(self, left: int, top: int, width: int, height: int):
        self.left = int(left)
        self.top = int(top)
        self.width = int(width)
        self.height = int(height)
    
    @property
    def right(self) -> int:
        return self.left + self.width
    
    @property
    def bottom(self) -> int:
        return self.top + self.height
    
    def __iter__(self):
        yield self.left
        yield self.top
        yield self.width
        yield self.height
    
    def __repr__(self):
        return f"CocoBbox({self.left}, {self.top}, {self.width}, {self.height})"
    
    @staticmethod
    def from_json(json) -> "CocoBbox":
        """Parses the COCO bbox from a JSON list, e.g. [1,2,3,4]"""
        assert type(json) == list
        assert len(json) == 4
        return CocoBbox(*[
            int(i) for i in json
        ])

    def dilate(self, amount: int) -> "CocoBbox":
        """Enlarges the bbox in all directions by the given amount"""
        return CocoBbox(
            left=self.left - amount,
            top=self.top - amount,
            width=self.width + 2 * amount,
            height=self.height + 2 * amount
        )
    
    def intersect_with(self, other: "CocoBbox") -> "CocoBbox":
        """Intersects the bbox with another one and returns the result.
        Returns a 0-sized bbox if the two bboxes do not overlap."""
        left = max(self.left, other.left)
        right = min(self.right, other.right)
        width = max(0, right - left)

        top = max(self.top, other.top)
        bottom = min(self.bottom, other.bottom)
        height = max(0, bottom - top)

        return CocoBbox(
            left=left,
            top=top,
            width=width,
            height=height
        )

    def union_with(self, other: "CocoBbox") -> "CocoBbox":
        """Unions the bbox with another one and returns the result."""
        left = min(self.left, other.left)
        right = max(self.right, other.right)

        top = min(self.top, other.top)
        bottom = max(self.bottom, other.bottom)

        return CocoBbox(
            left=left,
            top=top,
            width=right - left,
            height=bottom - top
        )

