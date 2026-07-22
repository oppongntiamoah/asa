from .blackstar import BlackstarParser
from .ic_securities import ICSecuritiesParser

PARSER_REGISTRY = {
    ICSecuritiesParser.broker_code: ICSecuritiesParser,
    BlackstarParser.broker_code: BlackstarParser,
    # "DATABANK": DatabankParser,  # post-MVP
}


def get_parser_class(broker_code: str):
    try:
        return PARSER_REGISTRY[broker_code]
    except KeyError:
        raise ValueError(f"No parser registered for broker '{broker_code}'")
