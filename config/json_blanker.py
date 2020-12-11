import json
import sys


def blank_json(input_object):
    if type(input_object) is list:
        output_list = []
        for item in input_object:
            output_list.append(blank_json(item))

        return output_list
    
    elif type(input_object) is dict:
        output_dict = {}
        for (key, val) in input_object.items():
            output_dict[key] = blank_json(val)
        
        return output_dict

    else:
        if type(input_object) is str:
            return ""
        elif type(input_object) is int:
            return 0
        elif type(input_object) is bool:
            return False
        elif type(input_object) is None:
            return None


if len(sys.argv) == 1:
    print("No files specified")
    sys.exit()

for arg in sys.argv[1:]:
    with open("./config/" + arg, "r") as f:
        raw = json.load(f)
    
    blanked = blank_json(raw)
    
    with open("./config/template_" + arg, "w") as f:
        json.dump(blanked, f, indent=4)