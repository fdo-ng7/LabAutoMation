#!/usr/bin/env python

# Learning how to use regex
# ideal output - https://*:443
import re
url = "https://10.159.81.251:443/guestFile?id=69&token=5206064a-951e-37d3-c6e1-941c53da11b569"
print url
url = re.sub(r"^http[s]?:\/\/(?:[0-9]|[.])+", "https://*", url)
print re.findall('http[s]?: // \*:', url)


print url


#^http[s]?: \/\/(?: [0 - 9] | [$-_@. & +])+
