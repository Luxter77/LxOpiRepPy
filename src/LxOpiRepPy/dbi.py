import dataclasses

@dataclasses.dataclass(order=True, frozen=True)
class QueryReturnValue:
    """Class containing server self.connection data"""
    querytime:  str
    query:      str
    head:       dataclasses.field(default_factory=list) # pylint: disable=E3701 # pylint is being silly again...
    ress:       dataclasses.field(default_factory=list) # pylint: disable=E3701
    ress_len:   int
    err_:       Exception

# TODO: add generic database template
# TODO: add spesific database type interfaces gated behind optional requirements
