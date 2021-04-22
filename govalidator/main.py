from govalidator import Govalidator
from govalidator import Goextractor
from govalidator import Gogenerator
from govalidator import Gotemplate
from govalidator import logs
from govalidator import exits

import os
import inspect
from argparse import ArgumentParser


def parse_args():
    """
    Handle command-line arguments with argparse.ArgumentParser
    Return list of arguments, largely for use in `parse_arguments`.
    """

    # Initialize
    parser = ArgumentParser(prog='Govalidate')
    # Specify the vladfile to be something other than vladfile.py

    subparsers = parser.add_subparsers(help='sub-command help', dest="subcommand")

    parser_validate = subparsers.add_parser('validate', help='Validate a file')

    parser_validate.add_argument(
        dest="template",
        help="Python template to use for validation",
    )

    parser_validate.add_argument(
        dest="source",
        help="File to validate",
    )

    parser_validate.add_argument(
        dest="type",
        choices=['spreadsheet', 'tabular'],
        help="Type of file to validate : spreadsheet of tabular",
        default="spreadsheet"
    )

    parser_validate.add_argument(
        "-s",
        "--sheet",
        dest="sheet",
        default=0,
        help="Sheet to validate",
    )

    parser_validate.add_argument(
        "-d",
        "--delimiter",
        dest="delimiter",
        help="Delimiter for tabular files : Default to ','",
        default=","
    )

    parser_generate = subparsers.add_parser('generate', help='Generate an xlsx file')

    parser_generate.add_argument(
        dest="template",
        help="Python template to use for validation",
    )

    parser_generate.add_argument(
        dest="output",
        help="Output file name",
    )

    parser_extract = subparsers.add_parser('extract', help='Extract a template file')

    parser_extract.add_argument(
        dest="source",
        help="File to validate",
    )

    parser_extract.add_argument(
        dest="output",
        help="Output file name",
    )

    parser_extract.add_argument(
        "-s",
        "--sheet",
        dest="sheet",
        default=0,
        help="Sheet to extract",
    )

    return parser.parse_args()


def is_valid_template(tup):
    """
    Takes (name, object) tuple, returns True if it's a public Gotemplate subclass.
    """
    name, item = tup
    return bool(
        inspect.isclass(item) and issubclass(item, Gotemplate) and hasattr(item, "validators") and not name.startswith("_")
    )


def load_template_file(path):
    """
    Load template file and get the custom class (subclass of Gotemplate)
    """

    directory, template = os.path.split(path)
    file = template.split(".")[0]
    mod = __import__(file)
    custom_class = None

    filtered_classes = dict(filter(is_valid_template, vars(mod).items()))
    # Get the first one
    if filtered_classes:
        custom_class = filtered_classes.values()[0]
    return custom_class


def main():
    arguments = parse_args()
    logger = logs.logger
    if arguments.subcommand not in ["validate", "generate", "extract"]:
        logger.error(
            "Unknown command"
        )
        exits.NOINPUT

    if arguments.subcommand == "extract":
        Goextractor(source=arguments.source, output=arguments.output, sheet=arguments.sheet).extract()
        return exits.OK

    custom_template_class = load_template_file(arguments.template)
    if not custom_template_class:
        logger.error(
            "Could not find a subclass of Gotemplate in the provided file."
        )
        return exits.UNAVAILABLE

    if arguments.subcommand == "validate":
        all_passed = True

        passed = Govalidator(
            validators=custom_template_class.validators,
            source=arguments.source,
            type=arguments.type,
            separator=arguments.separator
        ).validate()
        all_passed = all_passed and passed
        return exits.OK if all_passed else exits.DATAERR

    else:
        Gogenerator(
            validators=custom_template_class.validators,
            output=arguments.output,
        ).generate()
        return exits.OK


def run(name):
    if name == "__main__":
        exit(main())


run(__name__)