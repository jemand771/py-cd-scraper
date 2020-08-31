import json


ROOM_ERROR = "unknown room. an error might have occured. please contact @jemand771 about this"
PREPEND_TITLES = False

unknown_dozent = list()

def repair(infile, outfile):

    f = open(infile)
    data = json.load(f)
    f.close()

    
    del_fields = []
    # no one needs these fields since they're equivalent to their non-s-counterparts
    # description is also sent in remarks
    del_fields += ["sroom", "sinstructor", "description"]
    # fields are not used further down the pipeline. deleted to reduce complexicty
    # @me: comment out these lines if i happen to need any of the data i delete
    del_fields += ["allDay", "color", "editable"]

    print("deleting fields:", del_fields)
    for lesson in data:
        for field in del_fields:
            del lesson[field]

    # re-format start and end time to be time only. create a new field "date" for the day
    for lesson in data:
        
        date = lesson["start"].split(" ")[0]
        if date != lesson["start"].split(" ")[0]:
            print("parsing error! start and end date do not match!", lesson)
            continue
        lesson["date"] = date
        
        for f in ("start", "end"):
            lesson[f] = lesson[f].split(" ")[1]

    # re-label rooms because prof. lehnguth doesn't know how to use cd
    for lesson in data:

        if not room_valid(lesson["room"]):
            lesson["room"], lesson["remarks"] = room_and_remarks_from_remarks(lesson["remarks"])

    # lookup for instructors
    for lesson in data:
        lesson["instructor"] = dozent_translate(lesson["instructor"])
    
    for dozent in unknown_dozent:
        print("unknown instructor", dozent)

    f = open(outfile, "w")
    json.dump(data, f)
    f.close()


def room_and_remarks_from_remarks(remarks):

    fernstudium_tags = ["Fernlehre", "Fernstudium"]
    room = ROOM_ERROR
    sp = remarks.replace("(", "").replace(")", "").split(" ")
    if len(sp) < 2 or not room_valid(sp[0]):
        if any([x in remarks for x in fernstudium_tags]):
            for x in fernstudium_tags:
                remarks = remarks.replace(x, "")
            return "zuhause :)", remarks
        print("unable to parse room from remarks:", remarks)
        return room, remarks
    room = sp[0]
    remarks = " ".join(sp[1:])

    return room, remarks


def dozent_translate(name):

    f = open("config/dozent.json")
    data = json.load(f)
    f.close()

    for dozent in data:
        for alias in dozent["alias"]:
            if alias == name:
                if PREPEND_TITLES:
                    return dozent["title"] + " " + dozent["name"]
                return dozent["name"]
    if not name in unknown_dozent:
        unknown_dozent.append(name)
    return "unknown (" + name + ")"


# TODO make this configurable
def room_valid(room):

    # special room names that do not conform with a schema
    if room in ("AULA", "Z_TI1"):
        return True
    
    # check for standard room format
    # last 3 digits have to be a room number
    try:
        _ = int(room[-3:])
    except ValueError:
        return False
    # everything before those 3 digits has to be a valid identifier
    if room[:-3] not in ("VR", "SR", "PC", "L"):
        return False

    # should be fine
    return True