import argparse
import glob
import os
import csv
from contextlib import redirect_stdout
import sys
import re
import operator
import ast


CSV_FIELD_NAMES = ['Filename', 'Groups', 'Annotation', 'Associated Function', 'Line Number', 'Package', 'Absolute Path']


def main():
    global FLAGS
    FLAGS = set_up_args()

    if FLAGS.in_csv_name:
        file_changes = process_csv(FLAGS.in_csv_name, FLAGS.force_changes)

        if file_changes:
            print('Updating {} and statistics files to reflect these changes...'.format(FLAGS.in_csv_name))
            search_and_report(FLAGS.search_root, FLAGS.in_csv_name)
    else:
        search_and_report(FLAGS.search_root, FLAGS.out_csv_name)


def set_up_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--search_root',
        type=str,
        default=os.path.expanduser('~/tve_ott_cms/test'),
        help='Absolute path to the directory from which to start searching for test cases.'
    )
    parser.add_argument(
        '--search_filename_prefix',
        type=str,
        default='TC',
        help='When generating the output CSV, only check files starting with the SEARCH_FILENAME_PREFIX. (Default "TC")'
    )
    parser.add_argument(
        '--search_filename_suffix',
        type=str,
        default='.java',
        help='When generating the output CSV, only check files ending with SEARCH_FILENAME_SUFFIX. (Default ".java")'
    )
    parser.add_argument(
        '--out_csv_name',
        type=str,
        default='test_case_data.csv',
        help='Name for the CSV output file containing data about test cases.'
    )
    parser.add_argument(
        '--in_csv_name',
        type=str,
        help='Name of a CSV input file containing data about test cases.'
    )
    parser.add_argument(
        '--force_changes',
        action='store_true',
        default=False,
        help='Adding flag --force_changes will force updates to files even if they have been modified '+
                'more recently than the input CSV file.'
    )

    return parser.parse_args()


def search_and_report(search_root, out_csv_name):
    data_list = search_directory(search_root)

    generate_reports(data_list, out_csv_name)


def generate_reports(data_list, out_csv_name):
    print('Generating reports...')
    statistics_dict = {
        'counts': {
            'test_case_files': 0,
            'test_cases': 0
        },
        'group_counts': {},
        'groups_membership': {}
    }

    print('Writing data to {}'.format(out_csv_name))
    with open(out_csv_name, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=CSV_FIELD_NAMES)
        writer.writeheader()
        for annotation_data_item in data_list:
            update_group_statistics(annotation_data_item, statistics_dict['group_counts'], statistics_dict['groups_membership'])
            writer.writerow(annotation_data_item)

    print('Writing group membership histogram to group_membership_histogram.txt')
    with open('group_membership_histogram.txt', 'w') as f:
        with redirect_stdout(f):
            print_values_value_sorted(statistics_dict['group_counts'])

    print('Writing group membership lists to group_membership_lists.txt')
    with open('group_membership_lists.txt', 'w') as f:
        with redirect_stdout(f):
            sorted_hist = sorted(statistics_dict['group_counts'].items(), key=operator.itemgetter(1))
            for group_name, group_count in sorted_hist:
                group_membership_list = statistics_dict['groups_membership'][group_name]
                print('{}: {}'.format(group_name, group_count))
                for test_string in group_membership_list:
                    print('\t{}'.format(test_string))
                print()


def search_directory(search_root):
    print('Searching {} and subdirectories for files like "{}*{}" ...'.format(search_root, FLAGS.search_filename_prefix, FLAGS.search_filename_suffix))
    data_list = []

    search_start_path = os.path.abspath(search_root)
    search_string = '{}/**'.format(search_start_path)
    for absolute_path in glob.iglob(search_string, recursive=True):
        if os.path.isfile(absolute_path):
            for annotation_data_item in process_file(absolute_path):
                data_list.append(annotation_data_item)

    return data_list


def process_file(absolute_path):
    annotation_data_items = []

    filename = os.path.basename(absolute_path)
    if filename.startswith(FLAGS.search_filename_prefix) and filename.endswith(FLAGS.search_filename_suffix):
        with open(absolute_path, 'r') as f:
            annotations = []
            test_method = False
            for line_number, line in enumerate(f, start=1):
                line = line.strip()
                if line[:7] == 'package':
                    package_name = line[8:-1]
                elif line[:5] == '@Test':
                    test_method = True
                    annotations.append([line_number, line])
                elif test_method:
                    if line[0] != '@':
                        test_method = False
                        annotations[-1].append(line)

            if not annotations:
                print('Did not find any test annotations in {}'.format(absolute_path))
                return []

            for annotation in annotations:
                try:
                    groups = get_groups(annotation[1])
                except ValueError as e:
                    print(e)
                    groups = ['UNKNOWN']
                function_name = get_function_name(annotation[2])

                # CSV Fields: Filename, Groups, Annotation, Associated Function, Line Number, Package, Absolute Path
                data_item = [filename, groups, annotation[1], function_name, annotation[0], package_name, absolute_path]
                annotation_data_items.append(dict(zip(CSV_FIELD_NAMES, data_item)))

    return annotation_data_items


def update_group_statistics(source_data_dict, group_counts_dict, group_membership_dict):
    """
    group_counts_dict = {
        '{group name}': int({number of test cases in group})
    }

    group_membership_dict = {
        '{group name}': [
            '{filename}:{test function line number} {test function name}'
        ]
    }
    """
    for group in source_data_dict['Groups']:
        increment_count(group, group_counts_dict)
        if group not in group_membership_dict:
            group_membership_dict[group] = []
        test_string = '{}:{} {}'.format(source_data_dict['Filename'], source_data_dict['Line Number']+1, source_data_dict['Associated Function'])
        group_membership_dict[group].append(test_string)


def print_values_value_sorted(count_dict):
    sorted_dict = sorted(count_dict.items(), key=operator.itemgetter(1))
    for item in sorted_dict:
        print('{0:30}\t{1:5d}'.format(item[0], item[1]))


def print_values_key_sorted(count_dict):
    for key in sorted(count_dict):
        print('{0:5d}\t{1:40}'.format(count_dict[key], key))


def process_csv(in_csv_name, force_changes):
    print('Reading data from {} ...'.format(in_csv_name))
    with open(in_csv_name, 'r') as csvfile:
        data = list(csv.DictReader(csvfile))

    csv_modified_time = os.path.getmtime(in_csv_name)
    file_changes = False

    print('Checking files for test annotation differences...')
    for row in data:
        absolute_path = row['Absolute Path']
        filename = row['Filename']

        file_modified_time = os.path.getmtime(absolute_path)
        if file_modified_time > csv_modified_time and not force_changes:
            print('WARNING: File {} was modified more recently than your input CSV file. I will not make changes to {}'.format(filename, absolute_path))
            print('Include flag --force_changes to suppress this warning.')
        else:
            file_changes = True if process_annotation(row) else file_changes

    if not file_changes:
        print('No files changed')

    return file_changes


def process_annotation(csv_row):
    filename = csv_row['Filename']
    absolute_path = csv_row['Absolute Path']
    csv_annotation = csv_row['Annotation']
    annotation_line_number = int(csv_row['Line Number'])
    csv_groups = ast.literal_eval(csv_row['Groups'])

    with open(absolute_path, 'r') as f:
        file_contents = f.readlines()
        modified = False
        found = False

        file_annotation = file_contents[annotation_line_number-1]
        if file_annotation.strip()[:5] == '@Test':
            found = True
            if csv_annotation != file_annotation.strip():
                modified = True
                file_contents[annotation_line_number-1] = match_whitespace(file_annotation, csv_annotation)
                print('Writing new annotation to line {} of {}:\n{}\n'.format(annotation_line_number, absolute_path, csv_annotation))
            elif csv_groups != get_groups(file_annotation):
                modified = True
                file_contents[annotation_line_number-1] = replace_groups(file_annotation, csv_groups)
                print('Writing new groups to line {} of {}:\n{}\n'.format(annotation_line_number, absolute_path, file_contents[annotation_line_number-1]))

        # If we found and changed a test annotation, write the modified annotation to the file. Otherwise, don't try to write the file.
        if modified:
            write_file(file_contents, absolute_path)
        elif not found:
            print('Incorrect annotation line number for file {}'.format(filename))
            print('Expected @Test annotation at line {}'.format(annotation_line_number))
            print('Try regenerating the CSV file to update the annotation line numbers.')
            print('This will overwrite any changes you have made to the CSV file.')
        return modified


def match_whitespace(source_annotation, target_annotation):
    leading_whitespace = source_annotation[:source_annotation.find('@')]
    trailing_whitespace = source_annotation[source_annotation.find('\n'):]
    return leading_whitespace + target_annotation + trailing_whitespace


def replace_groups(source_annotation, groups):
    if groups_brackets_in(source_annotation):
        start_index = source_annotation.find('{')
        end_index = source_annotation.find('}')
        return source_annotation[:start_index+1] + ', '.join('"{}"'.format(group) for group in groups) + source_annotation[end_index:]

    groups_expression = groups_quotes_in(source_annotation)
    if groups_expression:
        before_groups, after_groups = source_annotation.split(groups_expression)
        return before_groups + 'groups = {' + ', '.join('"{}"'.format(group) for group in groups) + '}' + after_groups


def write_file(contents, absolute_path):
    with open(absolute_path, 'w') as f:
        for line in contents:
            f.write(line)


def groups_brackets_in(test_annotation):
    # Search for a substring like 'groups = {"group_name"}'
    m = re.search('groups( )*=( )*{(.)*}', test_annotation)
    if m == None:
        return False
    return True


def groups_quotes_in(test_annotation):
    # Search for a substring like 'groups = "group_name"'
    m = re.search('groups( )*=( )*"[^),]*"', test_annotation)
    if m == None:
        return False
    return m.group()


def get_groups(test_annotation):
    # Search for a substring like 'groups = {"group_name"}'
    m = re.search('groups( )*=( )*{(.)*}', test_annotation)
    if m != None:
        result = m.group()
        groups_string = result[result.find('{')+1 : result.rfind('}')]
        groups = [group_name.strip().replace('"', '') for group_name in groups_string.split(',')]
        return groups

    # Search for a substring like 'groups = "group_name"'
    m = re.search('groups( )*=( )*"[^),]*"', test_annotation)
    if m != None:
        result = m.group()
        groups = [result[result.find('"')+1 : result.rfind('"')].replace('"', '')]
        return groups

    raise ValueError('Failed to extract groups annotation from: %s', test_annotation)


def get_function_name(function_line):
    # Extract substring "functionName" from function_line string like "public void functionName() {\n"
    end_index = function_line.find('(')
    start_index = function_line[:end_index].rfind(' ')
    return function_line[start_index+1:end_index]


def increment_count(key, count_dict):
    if key in count_dict:
        count_dict[key] += 1
    else:
        count_dict[key] = 1


if __name__ == '__main__':
    main()
