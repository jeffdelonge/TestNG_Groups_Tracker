# TestNG Groups Manager

A Python tool for tracking group membership in a TestNG project using @Test annotations with groups.

Still needs functionality extended to track groups defined in a testng.xml file.


## Getting Started

### Prerequisites

Requires Python 3


## Usage

The groups manager serves two purposes: test case group membership tracking and test case group membership management.

For group membership tracking, the groups manager searches files in a TestNG project for `@Test` annotations and writes its findings to a CSV file.

By providing an input CSV file, you can use the groups manager to modify the `@Test` annotations in files in your TestNG project.


### Running

***Group membership tracking:***

```
$ python3 groups_tracker.py
```

This will create a file called `test_case_data.csv` containing data for each @Test annotation in the project at `search_root`.

This will also create files `group_membership_histogram.txt` and `group_membership_lists.txt` containing group membership information.

You can optionally provide the following arguments:
*   `--search_root SEARCH_ROOT`
        Absolute path to the directory from which to start searching for test cases. (Default: "{your home directory}/tve_ott_cms/test")

*   `--out_csv_name OUT_CSV_NAME`
        Name for the CSV output file containing data about test cases.

*   `--search_filename_prefix SEARCH_FILENAME_PREFIX`
        When generating the output CSV, only check files starting with `SEARCH_FILENAME_PREFIX`. (Default: "TC")

*   `--search_filename_suffix SEARCH_FILENAME_SUFFIX`
        Only check files ending with `SEARCH_FILENAME_SUFFIX`. (Default: ".java")


***Group membership management:***

With a CSV file containing data about test cases, `test_case_data.csv`:
```
$ python3 groups_tracker.py --in_csv_name test_case_data.csv
```

This will read the data in the CSV file and update files in your TestNG project to reflect any changes to groups/annotations made in the CSV file.

After updating files in your TestNG project, this will search the TestNG project as detailed in ***Group membership tracking*** to keep the CSV
file up to date.
