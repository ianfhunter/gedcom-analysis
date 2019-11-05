from gedcom.element.individual import IndividualElement
from gedcom.parser import Parser
import gedcom.tags as tags
import datetime



def get_main_person(ged):
    root_child_elements = ged.get_root_child_elements()

    you = None

    # Get Root Person
    for element in root_child_elements:
        if isinstance(element, IndividualElement):
            (first, last) = element.get_name()
            return element

def get_name(elem):
    return " ".join(elem.get_name())

def get_ancestry(ged, individiual, recurse=0, verbose=False):

    def print_fmt(level, person, style=0):

        if style == 0:
            pre_seperator="|"
            seperator = "_"
            post_seperator=" "
        elif style == 1:
            pre_seperator="|"
            seperator = "-"
            post_seperator="> "

        name = get_name(person)

        pre_string = ""
        if level:
            pre_string = pre_seperator
        pre_string += seperator*level
        if level:
            pre_string = pre_string + post_seperator

        print(pre_string + name)

    if verbose:
        print_fmt(recurse, individiual)

    parents = ged.get_parents(individiual, "ALL")

    if len(parents) == 0:
        return []
    elif len(parents) == 1:
        p = [get_ancestry(ged, parents[0], recurse=recurse+1, verbose=verbose)]
    else:
        assert(len(parents) == 2)
        p1 = get_ancestry(ged, parents[0], recurse=recurse+1, verbose=verbose)
        p2 = get_ancestry(ged, parents[1], recurse=recurse+1, verbose=verbose)
        p = [p1, p2]

    return {
        "name": get_name(individiual),
        "parents": p,
        "ref": individiual

    }

def centuries(ged, tree, recurse={}):

    e = tree["ref"]
    y = e.get_birth_year()
    century = y // 100 + 1
    recurse[century] = recurse.get(century, 0) + 1

    parents = tree["parents"]
    for p in parents:
        if p == []:
            continue
        recurse = centuries(ged, p, recurse)

    return recurse



def generations(ged, tree, recurse=0, recurse_dict={}):

    e = tree["ref"]

    parents = tree["parents"]

    recurse_dict[recurse] = recurse_dict.get(recurse, 0) + 1

    for p in parents:
        if p == []:
            continue
        _, recurse_dict = generations(ged, p, recurse+1, recurse_dict)

    if recurse == 0:
        return recurse_dict

    return recurse, recurse_dict


def brick_walls(ged, tree):

    e = tree["ref"]

    parents = tree["parents"]

    pc = 0
    for p in parents:
        if p == []:
            continue
        brick_walls(ged, p)
        pc += 1

    if pc == 0:
        print("- " + get_name(e))


def loose_cousins(ged, tree, child=None):

    e = tree["ref"]

    # print("Me:", get_name(e), "child:", child)

    exclusion = set([e])

    f = ged.get_families(e)
    if f != []:
        c = set()
        for sibling in ged.get_family_members(f[0]):
            c.add(sibling)

        for sp in ged.get_family_members(f[0], members_type="PARENTS"):
            exclusion.add(sp)

        if child:
            exclusion.add(child)

        # for cc in c:
        #     print("Have:", cc)
        # for e in exclusion:
        #     print("exclude:", e)

        f = c.difference(exclusion)
        for x in f:
            age = x.get_death_year() - x.get_birth_year()

            suitable_for_search = False

            if age < 0:
                # No need to search for descendants of those who died young
                suitable_for_search = True
            if age > 18:
                # Let's assume that our ancestors were all good and married at 18
                suitable_for_search = True

            if suitable_for_search:
                if len(ged.get_families(x)) == 0:
                    # You have two families or more if you get married.
                    # This call by default check for families where you are a spouse, rather than a child.
                    b = x.get_birth_year() if x.get_birth_year() != -1 else "?"
                    d = x.get_death_year() if x.get_death_year() != -1 else "?"
                    print(" * {} ({}, {})".format(get_name(x),b, d) )


    parents = tree["parents"]

    pc = 0
    for p in parents:
        if p == []:
            continue
        loose_cousins(ged, p, e)
        pc += 1


def established_missing_info(ged, tree):
    e = tree["ref"]

    parents = tree["parents"]
   
    if e.get_birth_year() == -1:
        print("Unknown Birth Year for", get_name(e))
    if e.get_death_year() == -1:
        if datetime.datetime.now().year - e.get_birth_year() > 100:
             print("Unknown Death Year for", get_name(e))
    pc = 0
    for p in parents:
        if p == []:
            continue
        established_missing_info(ged, p)

def missing_on_census(ged, tree):
    e = tree["ref"]

    c = e.get_census_data()
    if c != []:
        print(c)
    parents = tree["parents"]
   
    for p in parents:
        if p == []:
            continue
        missing_on_census(ged, p)
        
        
def stats(ged, tree):

    print("==== Centuries ====")
    c = centuries(ged, tree)

    for cen in c:
        print("{}th century: {} people".format(cen, c[cen]))

    print("==== Generations ====")

    g = generations(ged, tree)
    for gen in g:
        have = g[gen]
        want = 2**(gen)
        print("{}/{} in Generation {} - {:.1f}%".format(have, want, gen, 100*have/want))

    print("==== Brick Walls ====")

    brick_walls(ged, tree)

    print("==== Loose Branches ====")

    loose_cousins(ged, tree)

    print("==== Missing Info on Established People ====")
    established_missing_info(ged, tree)

    #print("==== Missing on Census ====")
    #missing_on_census(ged, tree)

    print("==== End Report ====")

if __name__ == "__main__":
    file_path = '/home/ian/Windows/Ged/test.ged'
    ged = Parser()
    ged.parse_file(file_path, False)

    me = get_main_person(ged)
    tree = get_ancestry(ged, me, verbose=False)

    stats(ged, tree)
