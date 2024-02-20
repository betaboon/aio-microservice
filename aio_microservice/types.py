from typing import Annotated

import annotated_types

Port = Annotated[int, annotated_types.Interval(ge=1, le=65535)]
