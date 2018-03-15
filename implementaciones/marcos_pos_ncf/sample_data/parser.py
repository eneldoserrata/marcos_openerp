import re

model = "account.journal"

xml_out = open("fix.xml", "w")
xml_in = open("account.journal.t.xml", "r")


#fix account.journal
if model == "account.journal":
    for line in xml_in:
        if "<field name='id'>" in line:
            continue
        elif "__export__." in line:
            new_line = line.replace("__export__.", "")
            if "/id" in new_line:
                value = new_line[45:-9]
                if len(value):
                    new_line = new_line.replace(value, "")
                    new_line = new_line.replace("/id'>", "' ref='%s'" % value)
                    new_line = new_line.replace("</field>", "/>")
                else:
                    continue
            xml_out.write(new_line)
        elif "<field name='type'>" in line:
            new_line = line.lower()
            if "bank and checks" in new_line:
                new_line = new_line.replace("bank and checks", "bank")
            if "sale refund" in new_line:
                new_line = new_line.replace("sale refund", "sale_refund")
            xml_out.write(new_line)
        else:
            xml_out.write(line)



#fix account.account
if model == "account.acoount.template":
    for line in xml_in:
        if "<field name='id'>" in line:
            continue
        elif "__export__." in line:
            new_line = line.replace("__export__.", "eym_")
            fix1 = re.findall("(_[1-1])'", new_line)
            fix2 = re.findall("(_[1-1])<", new_line)
            if len(fix1):
                new_line = new_line.replace("_1'", "'")
            if len(fix2):
                new_line = new_line.replace("_1<", "<")

            if "<field name='parent_id/id'>" in new_line:
                value = new_line[43:-9]
                if len(value):
                    new_line = new_line.replace(value, "")
                    new_line = new_line.replace("/id'>", "' ref='%s'" % value)
                    new_line = new_line.replace("</field>", "/>")
                else:
                    continue
            xml_out.write(new_line)

        elif "<field name='user_type/id'>" in line:
            value = line[43:-9]
            new_line = line.replace(value, "")
            new_line = new_line.replace("/id'>", "' ref='%s'" % value)
            new_line = new_line.replace("account.", "")
            new_line = new_line.replace("</field>", "/>")
            xml_out.write(new_line)
        elif "<field name='type'>" in line:
            new_line = line.lower()
            if "regular" in new_line:
                new_line = new_line.replace("regular", "other")
            xml_out.write(new_line)
        elif "<field name='code'>" in line:
            new_line = line.replace("-", "")
            xml_out.write(new_line)
        else:
            xml_out.write(line)

#fix ir.sequence
if model == "ir.sequence":
    for line in xml_in:
        if "ir.sequence" in line:
            new_line = line.replace("__export__.", "")
            xml_out.write(new_line)
        elif "<field name='id'>" in line:
            continue
        elif "<field name='padding'>" in line:
            value = re.findall("\d+", line).pop()
            new_line = line.replace("<field name='padding'>%s</field>" % value,
                                    "<field name='padding' eval='%s'/>" % value)
            xml_out.write(new_line)
        else:
            xml_out.write(line)


xml_in.close()
xml_out.close()