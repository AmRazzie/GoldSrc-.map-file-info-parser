import re
import csv
from pathlib import Path


MAP_FOLDER = "maps"
OUTPUT_FOLDER = "output"


CHAPTERS = {

    "Black Mesa Inbound":
    ["c0a0","c0a0a","c0a0b","c0a0c","c0a0d","c0a0e"],

    "Anomalous Materials":
    ["c1a0","c1a0a","c1a0b","c1a0c","c1a0d","c1a0e"],

    "Unforeseen Consequences":
    ["c1a1","c1a1a","c1a1b","c1a1c","c1a1d","c1a1f"],

    "Office Complex":
    ["c1a2","c1a2a","c1a2b","c1a2c","c1a2d"],

    "We've Got Hostiles":
    ["c1a3","c1a3a","c1a3b","c1a3c","c1a3d"],

    "Blast Pit":
    ["c1a4","c1a4b","c1a4d","c1a4e","c1a4f","c1a4g","c1a4i","c1a4j","c1a4k"],

    "Power Up":
    ["c2a1","c2a1a","c2a1b"],

    "On A Rail":
    ["c2a2","c2a2a","c2a2b1","c2a2b2","c2a2c","c2a2d","c2a2e","c2a2f","c2a2g","c2a2h"],

    "Apprehension":
    ["c2a3","c2a3a","c2a3b","c2a3c","c2a3d","c2a3e"],

    "Residue Processing":
    ["c2a4","c2a4a","c2a4b","c2a4c","c2a4d","c2a4e"],

    "Questionable Ethics":
    ["c2a4f","c2a4g"],

    "Surface Tension":
    ["c2a5","c2a5a","c2a5b","c2a5c","c2a5d","c2a5e","c2a5f","c2a5g","c2a5w","c2a5x"],

    "Forget About Freeman":
    ["c3a1","c3a1a","c3a1b"],

    "Lambda Core":
    ["c3a2","c3a2a","c3a2b","c3a2c","c3a2d","c3a2e","c3a2f"],

    "Xen":
    ["c4a1","c4a1a","c4a1b","c4a1c","c4a1d","c4a1e","c4a1f"],

    "Gonarch's Lair":
    ["c4a2","c4a2a","c4a2b"],

    "Interloper":
    ["c4a3"],

    "Endgame":
    ["c5a1"]
}



def find_maps():

    return sorted(
        Path(MAP_FOLDER).glob("*.map"),
        key=lambda x:x.name.lower()
    )



def choose_files(files):

    while True:

        print("""
Choose file scope:

1. All files
2. File range
3. Specific files
4. Chapter
5. Quit
""")

        c=input("Choice: ")


        if c=="1":
            return files


        if c=="2":

            print(
                f"Available range: 1-{len(files)}"
            )

            a,b=map(
                int,
                input("Range: ").split("-")
            )

            return files[a-1:b]



        if c=="3":

            names=input(
                "Files: "
            ).split(",")

            return [
                f for f in files
                if f.stem in names
            ]



        if c=="4":

            names=list(CHAPTERS)

            for i,n in enumerate(names,1):
                print(f"{i}. {n}")

            print("0. Back")

            x=input("Chapter: ")

            if x=="0":
                continue

            return [
                f for f in files
                if f.stem in CHAPTERS[
                    names[int(x)-1]
                ]
            ]



        if c=="5":
            return "QUIT"




def extract_entities(text):

    entities=[]


    for m in re.finditer(
        r'"classname"\s+"[^"]+"',
        text
    ):

        start=text.rfind(
            "{",
            0,
            m.start()
        )


        if start < 0:
            continue


        depth=0
        end=None


        for i in range(
            start,
            len(text)
        ):

            if text[i]=="{":
                depth+=1

            elif text[i]=="}":

                depth-=1

                if depth==0:
                    end=i+1
                    break


        if end:

            block=text[start:end]

            if block not in entities:
                entities.append(block)


    return entities



def get_keys(block):

    return dict(
        re.findall(
            r'"([^"]+)"\s+"([^"]*)"',
            block
        )
    )

# ==========================
# COORDINATES
# ==========================

def get_brush_bounds(block):

    points = re.findall(
        r'\(\s*(-?\d+(?:\.\d+)?)\s+'
        r'(-?\d+(?:\.\d+)?)\s+'
        r'(-?\d+(?:\.\d+)?)\s*\)',
        block
    )


    if not points:
        return None, False


    xs=[]
    ys=[]
    zs=[]


    # Normal axis-aligned brushes
    for i in range(0, len(points), 3):

        if i+2 >= len(points):
            break


        p1=tuple(map(float, points[i]))
        p2=tuple(map(float, points[i+1]))
        p3=tuple(map(float, points[i+2]))


        if p1[0] == p2[0] == p3[0]:
            xs.append(p1[0])


        if p1[1] == p2[1] == p3[1]:
            ys.append(p1[1])


        if p1[2] == p2[2] == p3[2]:
            zs.append(p1[2])



    # Rotated brush fallback
    if not xs or not ys or not zs:

        return None, True



    return (

        (
            int(min(xs)),
            int(min(ys)),
            int(min(zs)),

            int(max(xs)),
            int(max(ys)),
            int(max(zs))
        ),

        False
    )




def get_origin(keys):

    if "origin" not in keys:
        return None


    try:

        x,y,z=map(
            float,
            keys["origin"].split()
        )


        return (
            int(x),
            int(y),
            int(z),
            int(x),
            int(y),
            int(z)
        )


    except:

        return None




def get_coordinates(block,keys):

    coords, rotated = get_brush_bounds(block)


    if rotated:

        return "INV", True


    if coords:

        return coords, False



    origin=get_origin(keys)


    if origin:

        return origin, False



    return None, False




# ==========================
# SCAN
# ==========================

def scan(files, classname):

    results=[]


    for file in files:

        text=file.read_text(
            encoding="utf-8",
            errors="ignore"
        )


        for entity in extract_entities(text):

            keys=get_keys(entity)


            if keys.get(
                "classname",
                ""
            ).lower() != classname.lower():

                continue



            coords, rotated = get_coordinates(
                entity,
                keys
            )



            if rotated:

                print(
                    "WARNING: Rotated coordinates:",
                    file.stem,
                    keys.get("targetname",""),
                    keys.get("map","")
                )



            if coords == "INV":

                x1=y1=z1=x2=y2=z2 = \
                    "INV"



            elif coords:

                x1,y1,z1,x2,y2,z2=coords



            else:

                x1=y1=z1=x2=y2=z2=""



            row={

                "filename":
                    file.stem,

                "classname":
                    keys.get(
                        "classname",
                        ""
                    ),

                "x1":x1,
                "y1":y1,
                "z1":z1,

                "x2":x2,
                "y2":y2,
                "z2":z2,

                "coordinates":
                    f"{x1} {y1} {z1} {x2} {y2} {z2}"
            }


            row.update(keys)

            results.append(row)


    return results




# ==========================
# OUTPUT
# ==========================

def ensure_output():

    Path(
        OUTPUT_FOLDER
    ).mkdir(
        exist_ok=True
    )



def output_name(default):

    x=input(
        f"Output filename [{default}]: "
    ).strip()

    return x or default



def write_file(name,text):

    ensure_output()


    path=Path(
        OUTPUT_FOLDER
    ) / name


    path.write_text(
        text,
        encoding="utf-8"
    )


    print(
        "Created:",
        path
    )




def save_csv(data):

    hidden={
        "x1",
        "y1",
        "z1",
        "x2",
        "y2",
        "z2"
    }


    fields=set()


    for row in data:

        for k in row:

            if k not in hidden:
                fields.add(k)



    with open(
        Path(OUTPUT_FOLDER) /
        output_name("export.csv"),
        "w",
        newline="",
        encoding="utf-8"
    ) as f:


        writer=csv.DictWriter(
            f,
            fieldnames=sorted(fields)
        )


        writer.writeheader()


        for row in data:

            writer.writerow(
                {
                    k:v
                    for k,v in row.items()
                    if k in fields
                }
            )




def save_keys(data):

    hidden={
        "x1",
        "y1",
        "z1",
        "x2",
        "y2",
        "z2"
    }


    out=[]


    for row in data:

        for k,v in row.items():

            if k not in hidden:

                out.append(
                    f"{k}: {v}"
                )


        out.append("")


    write_file(
        output_name("keys.txt"),
        "\n".join(out)
    )




def custom_template(data):

    print("""
Available placeholders:

filename
classname

targetname
target
killtarget

map
landmark

coordinates
""")


    template=input(
        "Template: "
    )


    out=[]


    for row in data:

        line=template


        for k,v in row.items():

            line=line.replace(
                "{"+k+"}",
                str(v)
            )

            line=line.replace(
                k,
                str(v)
            )


        out.append(line)



    write_file(
        output_name("custom.txt"),
        "\n\n".join(out)
    )




# ==========================
# BXT
# ==========================

def bxt_trigger(data):

    out=[]


    for r in data:

        out.append(
            f"bxt_triggers_add "
            f"{r['x1']} "
            f"{r['y1']} "
            f"{r['z1']} "
            f"{r['x2']} "
            f"{r['y2']} "
            f"{r['z2']}; "
            f"bxt_triggers_setcommand "
            f"\"{r.get('filename','')}/"
            f"{r.get('map','')}\""
        )


    write_file(
        output_name("bxt_triggers.cfg"),
        "\n\n".join(out)
    )




def bxt_split(data):

    out=[]


    for r in data:

        out.append(
            f"bxt_splits_add_trigger "
            f"{r['x1']} "
            f"{r['y1']} "
            f"{r['z1']} "
            f"{r['x2']} "
            f"{r['y2']} "
            f"{r['z2']} "
            f"{r.get('filename','')} "
            f"{r.get('map','')}"
        )


    write_file(
        output_name("bxt_splits.cfg"),
        "\n".join(out)
    )




# ==========================
# MAIN
# ==========================

def run():

    files=find_maps()


    print(
        "Found",
        len(files),
        "map files."
    )


    while True:

        selected=choose_files(files)


        if selected=="QUIT":

            print("Finished.")
            break



        while True:

            classname=input(
                "\nEnter classname (back=files): "
            )


            if classname=="back":

                break



            data=scan(
                selected,
                classname
            )


            print(
                "Found",
                len(data),
                "entities."
            )


            while True:

                print("""
Output:

1. CSV
2. Keys
3. Custom Template
4. BXT Trigger
5. BXT Split
6. Back to classname
7. Back to files
8. Quit
""")


                c=input("Choice: ")



                if c=="1":
                    save_csv(data)

                elif c=="2":
                    save_keys(data)

                elif c=="3":
                    custom_template(data)

                elif c=="4":
                    bxt_trigger(data)

                elif c=="5":
                    bxt_split(data)

                elif c=="6":
                    break

                elif c=="7":
                    selected=None
                    break

                elif c=="8":
                    return



                print(
                    "\nCOMPLETE\n"
                    "Exported:",
                    len(data),
                    "entities\n"
                )



            if selected is None:
                break




if __name__=="__main__":

    run()