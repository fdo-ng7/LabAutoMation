#!/usr/bin/env python
import json
# with open('ndc-config.json', 'r') as outfile:
#     json.dump(data, outfile)
#
# import json

with open('./ndc-config.json') as json_file:
    data = json.load(json_file)

print data['physical']['vcenter']['username']
print data['physical']['vcenter']['ip']
