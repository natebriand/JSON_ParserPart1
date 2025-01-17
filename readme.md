JSON PARSER PROGRAM - README
Author: Nate Briand

Instructions:
The following folder for which the program is contained in already has
various test files to be used. Inside 'input.folder' contains 10 test files
with valid JSON strings, that will be tested using pythons file read, and
outputted to the corresponding output file in 'output_folder'. If you wish to
test certain strings simply select a text file, paste your JSON string, and
then run the Scanner.py file.

Assumptions:
Extensive error checking has been implemented within the program but there are
a few assumptions.
- literals such as false, true, and null, will be expected to be inputted
in correct python syntax, which is un-capitalized versions of the word.
- the JSON string will not be tokenized until it follows typical and correct
JSON syntax. It will return errors until the string is fixed.
- the only number recognized at the moment is Integers. such as '4' or '45'.
any floating point, scientific notation, etc, number will not be recognized
and an error will be thrown.