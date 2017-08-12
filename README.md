# TestNG Groups Manager

A Python tool for tracking and managing test case group membership in a TestNG project using `@Test` annotations with groups.

Still needs functionality extended for the following:
* Track groups defined in a `testng.xml` file
* Use regular expressions to handle multi line `@Test` annotations
* Use regular expressions to handle any parsing where they could improve reliability


## Getting Started

### Prerequisites

Requires Python 3


## Usage

The groups manager serves two purposes: test case group membership tracking and test case group membership management.

For group membership tracking, the groups manager searches files in a TestNG project for `@Test` annotations, writes
its findings to a CSV file, and outputs a few text files containing information about group membership.

By providing an input CSV file, you can use the groups manager to modify the `@Test` annotations in files in your TestNG project.


## Running

### Group membership tracking

```
$ python3 groups_manager.py
```

This will create a file called `test_case_data.csv` containing data for each `@Test` annotation in the project at `search_root`.

This will also create files `group_membership_histogram.txt` and `group_membership_lists.txt` containing group membership information.

You can optionally provide the following arguments:
*   `--search_root SEARCH_ROOT`
        Absolute path to the directory from which to start searching for test cases.
        Defaults to "{your home directory}/tve_ott_cms/test"

*   `--out_csv_name OUT_CSV_NAME`
        Name for the output CSV file containing data about test cases.
        Defaults to "test_case_data.csv"

*   `--search_filename_prefix SEARCH_FILENAME_PREFIX`
        When generating the output CSV, only check files starting with `SEARCH_FILENAME_PREFIX`.
        Defaults to "TC"

*   `--search_filename_suffix SEARCH_FILENAME_SUFFIX`
        Only check files ending with `SEARCH_FILENAME_SUFFIX`.
        Defaults to ".java"


### Group membership management

With a CSV file containing data about test cases, `test_case_data.csv`:
```
$ python3 groups_manager.py --in_csv_name test_case_data.csv
```

This will read the data in `test_case_data.csv` and update files in your TestNG project to reflect any changes you made to groups
or annotations in the input CSV file.

If a file in your TestNG project was modified more recently than the input CSV file, that file will not be changed. You can use
flag `--force_changes` to override this behavior.

If the groups manager makes changes to any files in your TestNG project, it will then search the TestNG project as detailed in
[Group membership tracking](#group-membership-tracking) and overwrite all entries in the CSV file to keep the CSV file up to date.
Note that you should provide any of the optional arguments you provided when originally generating the reports, as this CSV update
step will need all of these arguments to keep the CSV update consistent with the original CSV creation.

You can optionally provide the following arguments:
*   `--in_csv_name IN_CSV_NAME`
        Name of a CSV input file containing data about test cases.
        No default value.

*   `--force_changes`
        Force updates to files even if they have been modified more recently than the input CSV file.
