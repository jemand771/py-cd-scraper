import json

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
        

    f = open(outfile, "w")
    json.dump(data, f)
    f.close()