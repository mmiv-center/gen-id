# gen-id

A simple program to generate an identifier based on a regular expression.
Such identifiers can be used in research projects as de-identified IDs. If 
this program is used in such a manner one needs to keep a mapping file of
the ID (hash-ed) and the generated ID.

Note: There are better ways to generate an ID. Probably the easiest
is to generate the ID based on a time stamp + random + counter method 
similar to DICOM UIDs. Those IDs can be generated at a high rate,
they don't repeat even if they are generated on different systems independently 
from each other but they are very long.

The method used in this example is suitable if the generated ID should
be very short, follow a predictable, human-friendly pattern and not 
come in a sequence.

### Usage

```
Usage:
  Generate a random UID based on a given pattern (regular expression). Pattern can
  be made unique given an exclusion list of already existing pattern provided as a text file
  with one line per existing ID. Here an example call generating an id based on
  three digit numbers:
  > gen-id.py -r 'PROJ_01_[0-9]{3}'

If an exclusion file is provided with -e (--exclusion_file)
the program will attempt to create an id that is not in the file. This
might fail! In this case an error message is created and the exit code
of the program is != 0.
  > gen-id.py -r 'PROJ_[0-9]{3}' -e exclusion_list.txt

If the -a (--auto_add) option is used the generated ID will be added to the
exclusion file automatically.
  > touch exclusion_list.txt
  > gen-id.py -r 'PROJ_[0-9]{3}' -e exclusion_list.txt -a
  > gen-id.py -r 'PROJ_[0-9]{3}' -e exclusion_list.txt -a
  > gen-id.py -r 'PROJ_[0-9]{3}' -e exclusion_list.txt -a
  > cat exclusion_list.txt
Further examples that show-case pattern that work:
  > gen-id.py -r 'PROJ_(a|[0-9][a-z][A-Z])_[0-9][0-9][0-9][a-z]'
  > ./gen-id.py -r 'PROJ_(a|[0-9][a-z][A-Z])_[0-9][0-9][0-9][a-z]_\d{8}_.'

Warning: Some normal pattern will not work as expected. Don't use '*' and '+'
         because they will result in IDs of unknown (=1) length.
```