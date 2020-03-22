#!/usr/bin/env python3

#
# Some interesting observations: We could notice if we cannot generate
# another key. Right now we just give up after 20 independent tries.
# This would happen if we exhaust all choices we could have
# done in the tree. This would indicate that we need to keep a shuffle list at each
# step of the generation. We need to be able to backtrack in this list and if we
# reach the end of the shuffle list we know there are no other ways to generate a key.
#
# For now we just make sure that there are always enough keys based on the number of
# characters used.
#

import getopt
import sys
import sre_parse
import random
import os
from sre_constants import *


def usage():
    print("Usage:")
    print("  Generate a random UID based on a given pattern (regular expression). Pattern can")
    print("  be made unique given an exclusion list of already existing pattern provided as a text file")
    print("  with one line per existing ID. Here an example call generating an id based on")
    print("  three digit numbers:")
    print("  > gen-id.py -r 'PROJ_01_[0-9]{3}'")
    print("")
    print("If an exclusion file is provided with -e (--exclusion_file)")
    print("the program will attempt to create an id that is not in the file. This")
    print("might fail! In this case an error message is created and the exit code")
    print("of the program is != 0.")
    print("  > gen-id.py -r 'PROJ_[0-9]{3}' -e exclusion_list.txt")
    print("")
    print("If the -a (--auto_add) option is used the generated ID will be added to the")
    print("exclusion file automatically.")
    print("  > touch exclusion_list.txt")
    print("  > gen-id.py -r 'PROJ_[0-9]{3}' -e exclusion_list.txt -a")
    print("  > gen-id.py -r 'PROJ_[0-9]{3}' -e exclusion_list.txt -a")
    print("  > gen-id.py -r 'PROJ_[0-9]{3}' -e exclusion_list.txt -a")
    print("  > cat exclusion_list.txt")
    print("Further examples that show-case pattern that work:")
    print("  > gen-id.py -r 'PROJ_(a|[0-9][a-z][A-Z])_[0-9][0-9][0-9][a-z]'")
    print(
        "  > ./gen-id.py -r 'PROJ_(a|[0-9][a-z][A-Z])_\1[0-9][0-9][0-9][a-z]_\d{8}_.'")
    print("")
    print("Warning: Some normal pattern will not work as expected. Don't use '*' and '+'")
    print("         because they will result in IDs of unknown (=1) length.")
    print("")


# keep a list of groups so we can reference them later
reference_list = []


def generator(ast):
    # gets an abstract syntax tree and generates a single example random key from it
    # we can get random choices with random.randint(a,b) for example
    txt = ""
    for x in range(0, len(ast)):
        if ast[x][0] == LITERAL:
            txt = txt + chr(ast[x][1])
        elif ast[x][0] == IN:
            txt = txt + generator(ast[x][1])
        elif ast[x][0] == RANGE:
            # return one character from that range
            min_char = ast[x][1][0]
            max_char = ast[x][1][1]
            txt = txt + chr(random.randint(min_char, max_char))
        elif ast[x][0] == MAX_REPEAT:
            # do this a couple of times
            mr = ast[x][1]
            for y in range(0, mr[0]):
                txt = txt + generator(mr[2])
        elif ast[x][0] == SUBPATTERN:
            mr = ast[x][1]
            # we will not remember that sub-pattern this is!!!
            patnum = mr[1]
            # we can do this if mr[3][1] is a branch, but it could be IN as well
            # for single characters, in that case we should random choice here
            tt = ""
            if mr[3][0][0] == BRANCH:
                tt = generator(mr[3])
            elif mr[3][0][0] == IN:
                mr = mr[3][0][1]
                choice = random.randint(0, len(mr)-1)
                tt = generator([mr[choice]])
            reference_list.append(tt)
            txt = txt + tt
        elif ast[x][0] == BRANCH:
            # depends on the number of branches, run one of them
            mr = ast[x][1][1]
            choice = random.randint(0, len(mr)-1)
            txt = txt + generator(mr[choice])
        elif ast[x][0] == GROUPREF:
            if (ast[x][1]-1) not in list(range(0, len(reference_list))):
                print("Error: unknown reference %d!" % (ast[x][1]))
                sys.exit(-1)
            # here the index starts with 1!
            txt = txt + reference_list[ast[x][1] - 1]
        elif ast[x][0] == CATEGORY:
            if ast[x][1] == CATEGORY_DIGIT:
                txt = txt + \
                    random.choice(("0", "1", "2", "3", "4",
                                   "5", "6", "7", "8", "9"))
            elif ast[x][1] == CATEGORY_SPACE:
                txt = txt + \
                    random.choice((" ", "\t"))
            else:
                print("Error: unknown category %s" % (ast[x][1]))
                sys.exit(-1)
        elif ast[x][0] == NEGATE:
            print("Error: we do not support negated character lists!")
            sys.exit(-1)
        elif ast[x][0] == ANY:
            all_digit_list = list(
                map(chr, list(range(ord("0"), ord("9") + 1))))
            all_lchar_list = list(
                map(chr, list(range(ord("a"), ord("z") + 1))))
            all_uchar_list = list(
                map(chr, list(range(ord("A"), ord("Z") + 1))))
            all_list = all_digit_list + all_lchar_list + all_uchar_list
            txt = txt + \
                random.choice(all_list)
        else:
            print("Unknown regular expression term type %s" % (ast[x][0]))
            print("")
            print("Warning: We don't want to support some unspecified things")
            print("         like repeat and repeat_one. We would not know")
            print("         how many times an item should be repeated.")
    return txt


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hm:r:e:a", [
                                   "help", "method=", "regexp=", "exclusion="])
    except getopt.GetoptError as err:
        # print help information and exit:
        print(str(err))  # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    method = "random-id"
    regexp_string = ""
    exclusion_file = ""
    verbose = False
    # automatically add the new ID to the exclusion file
    auto_add = False
    for o, a in opts:
        if o in ("-a", "--auto-add"):
            auto_add = True
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-m", "--method"):
            method = a
        elif o in ("-r", "--regexp"):
            regexp_string = a.strip('\'')
        elif o in ("-e", "--exclusion_file"):
            exclusion_file = a
        else:
            assert False, "unhandled option"
    # now check that we support the method
    if method != "random-id":
        print("only method random-id is currently supported")
        usage()
        sys.exit(-1)
    if regexp_string == "":
        print("Regular expression string is required, use the -r option.")
        print("")
        usage()
        sys.exit(-1)
    exclusions = []
    if os.path.isfile(exclusion_file):
        with open(exclusion_file, 'r') as f:
            exclusions = f.readlines()
    else:
        if auto_add:
            print("Error: auto_add is only allowed if an exclusion file has")
            print("been provided and the file exists. We will ignore this option now.")
            auto_add = False

    # we have to start the program with a good random seed
    seed_bytes = 128
    random.seed(os.urandom(seed_bytes))

    ast = sre_parse.parse(regexp_string)
    gen_string = generator(ast)
    tries = 0
    while gen_string in exclusions:
        gen_string = generator(ast)
        tries = tries + 1
        if tries > 20:
            print(
                "Error: no unique key found based on the exclusion file %s after %d tries." % (exclusion_file,
                                                                                               tries))
            # check if the return value is 0!
            sys.exit(-1)

    if auto_add:
        with open(exclusion_file, 'a') as f:
            f.write(gen_string + '\n')
    print(gen_string)


if __name__ == '__main__':
    main()
