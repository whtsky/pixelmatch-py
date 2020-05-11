from typing import List, MutableSequence, Optional, Sequence, Tuple, Union

# note: this shouldn't be necessary, but apparently is
Number = Union[int, float]
ImageSequence = Sequence[Number]
MutableImageSequence = MutableSequence[Number]
RGBTuple = Union[Tuple[Number, Number, Number], List[Number]]
