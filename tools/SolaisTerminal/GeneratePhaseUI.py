import re
import argparse
from dataclasses import dataclass
from typing import Optional, List

HEAD = """/* Auto generated by GeneratePhaseUI.py written by liuzikai */

#ifndef UI_PHASES_H
#define UI_PHASES_H

#include <QtWidgets/QScrollArea>
#include <QtWidgets/QGroupBox>
#include <QtWidgets/QCheckBox>
#include <QtWidgets/QLabel>
#include <QtWidgets/QDoubleSpinBox>
#include <QtWidgets/QComboBox>
#include <QtWidgets/QGridLayout>
#include <QtWidgets/QHBoxLayout>
#include <QtWidgets/QVBoxLayout>
#include "Parameters.pb.h"
#include "Parameters.h"

namespace meta {

class PhaseController {
public:
"""

TAIL = """

};

}

#endif  // UI_PHASES_H
"""


@dataclass
class Param:
    kind: str  # (Toggle)?(Int|Double)(Range)? or Enum<enum name>
    name: str
    label: str
    options: List[str] = ""


@dataclass
class Group:
    name: str
    params: List[Param]
    info_label: Optional[str] = None
    image: Optional[str] = None


def parse_groups(filename: str) -> [Group]:
    groups = {}
    enums = {}

    inside_message = None
    inside_enum = None
    current_group_name = None

    for line in open(filename, "r", encoding="utf-8"):

        line = line.strip()
        if line == "":
            continue

        if inside_message is None:
            if re.match(r"message +ParamSet +\{", line):
                inside_message = "ParamSet"
            elif re.match(r"message +Result +\{", line):
                inside_message = "Result"

        else:  # inside ParamSet or Result

            if inside_enum is not None:
                if line.startswith("}"):
                    inside_enum = None
                else:
                    if g := re.match(f"^(\S+?) *= *\d+ *;", line):
                        enums[inside_enum].append(g.group(1))
                    elif not line.startswith("//"):
                        raise ValueError(f'Unknown enum line "{line}"')

            else:  # not inside enum
                if g := re.match(r"^enum +(\S+?) *\{", line):
                    inside_enum = g.group(1)
                    enums[inside_enum] = []
                else:  # inside ParamSet or Result but not inside enum

                    if line.startswith("}"):
                        inside_message = None
                    else:
                        if g := re.match(f"^// *GROUP: *(\S+)$", line):
                            current_group_name = g.group(1)
                            if current_group_name not in groups.keys():
                                groups[current_group_name] = Group(name=current_group_name, params=[])
                        else:
                            if g := re.match(r"^(?:optional +)?(\S+?) +(\S+?) *= *\d+ *; *// *(.*) *", line):
                                kind = g.group(1)
                                if kind in enums.keys():
                                    # Add an enumeration parameter
                                    groups[current_group_name].params.append(
                                        Param(kind="Enum" + kind, name=g.group(2), label=g.group(3), options=enums[kind]))
                                elif kind == "string":
                                    # Result string
                                    assert inside_message == "Result", "string type appears outside the Result message"
                                    assert groups[current_group_name].info_label is None, \
                                        f'Duplicate info label for group "{current_group_name}"'
                                    groups[current_group_name].info_label = g.group(2)
                                elif kind == "Image":
                                    assert inside_message == "Result", "string type appears outside the Result message"
                                    assert groups[current_group_name].image is None, \
                                        f'Duplicate image for group "{current_group_name}"'
                                    groups[current_group_name].image = g.group(2)
                                else:
                                    # Process primitive types
                                    if kind == "int32" or kind == "int64":
                                        kind = "Int"
                                    elif kind == "double" or kind == "float":
                                        kind = "Double"
                                    groups[current_group_name].params.append(
                                        Param(kind=kind, name=g.group(2), label=g.group(3)))
                            else:
                                raise ValueError(f'Line "{line}" has incorrect structure')

    return groups.values()


print_line_prefix = ""


def print_line(s: str = ""):
    print(print_line_prefix, s, sep="")


def generate_ui_creation_code(groups: [Group]) -> [(str, str)]:
    global print_line_prefix

    variables = []  # member variables in (type, name) tuple
    reset_images_lines = []  # lines of code (without indentations) for resetImageLabels()

    print_line_prefix = "    "
    print_line("explicit PhaseController(QScrollArea *area, QVBoxLayout *areaLayout) {")

    print_line_prefix = "        "
    for group in groups:
        print_line(f"// GROUP {group.name}")

        # Group container
        group_obj = f"group{group.name}"
        variables.append(("QGroupBox*", group_obj))
        print_line(f'{group_obj} = new QGroupBox(area);')
        print_line(f'{group_obj}->setTitle(QString::fromUtf8("{group.name}"));')

        # Horizontal layout of the group container
        h_layout_obj = f'hLayout{group.name}'
        variables.append(("QHBoxLayout*", h_layout_obj))
        print_line(f'{h_layout_obj} = new QHBoxLayout({group_obj});')

        # Left-side container
        left_container_obj = f'leftContainer{group.name}'
        variables.append(("QWidget*", left_container_obj))
        print_line(f'{left_container_obj} = new QWidget({group_obj});')
        print_line(f'{h_layout_obj}->addWidget({left_container_obj});')

        # Grid layout for the left-side container
        g_layout_obj = f'gLayout{group.name}'
        variables.append(("QGridLayout*", g_layout_obj))
        print_line(f'{g_layout_obj} = new QGridLayout({left_container_obj});')
        print_line(f'{g_layout_obj}->setContentsMargins(0, 0, 0, 0);')

        # Add parameter widgets
        row_count = 0
        for param in group.params:

            type_str = param.kind

            # Add checkbox or label
            if type_str.startswith("Toggled"):
                type_str = type_str[len("Toggled"):]  # consume the prefix

                # Checkbox
                label_obj = f'{param.name}Check'
                variables.append(("QCheckBox*", label_obj))
                print_line(f'{label_obj} = new QCheckBox({left_container_obj});')

            else:
                # Label
                label_obj = f'{param.name}Label'
                variables.append(("QLabel*", label_obj))
                print_line(f'{label_obj} = new QLabel({left_container_obj});')

            print_line(f'{label_obj}->setText(QString::fromUtf8("{param.label}"));')
            print_line(f'{g_layout_obj}->addWidget({label_obj}, {row_count}, 0, 1, 1);')  # span column 0

            # Get data type
            if type_str.startswith("Enum"):
                combo_obj = f'{param.name}Combo'
                variables.append(("QComboBox*", combo_obj))
                print_line(f'{combo_obj} = new QComboBox({left_container_obj});')
                for option in param.options:
                    print_line(f'{combo_obj}->addItem(QString::fromUtf8("{option}"));')
                print_line(f'{g_layout_obj}->addWidget({combo_obj}, {row_count}, 1, 1, 2);')  # span column 1-2

            else:  # not Enum, numerical types
                if type_str.startswith("Int"):
                    decimal = "0"
                    type_str = type_str[len("Int"):]  # consume the prefix
                elif type_str.startswith("Double"):
                    decimal = "2"
                    type_str = type_str[len("Double"):]  # consume the prefix
                else:
                    raise ValueError(f'Unknown data type prefix in "{type_str}"')

                # Add one or two spin boxes
                if len(type_str) == 0:
                    # No keyword "Range", single spin box
                    spin_obj = f'{param.name}Spin'
                    variables.append(("QDoubleSpinBox*", spin_obj))
                    print_line(f'{spin_obj} = new QDoubleSpinBox({left_container_obj});')
                    print_line(f'{spin_obj}->setDecimals({decimal});')
                    print_line(f'{spin_obj}->setMaximum(9999);')
                    print_line(f'{g_layout_obj}->addWidget({spin_obj}, {row_count}, 1, 1, 1);')  # span column 1
                elif type_str == "Range":
                    # Two spin boxes
                    min_spin_obj = f'{param.name}MinSpin'
                    variables.append(("QDoubleSpinBox*", min_spin_obj))
                    print_line(f'{min_spin_obj} = new QDoubleSpinBox({left_container_obj});')
                    print_line(f'{min_spin_obj}->setDecimals({decimal});')
                    print_line(f'{min_spin_obj}->setMaximum(9999);')
                    print_line(f'{g_layout_obj}->addWidget({min_spin_obj}, {row_count}, 1, 1, 1);')  # span column 1
                    max_spin_obj = f'{param.name}MaxSpin'
                    variables.append(("QDoubleSpinBox*", max_spin_obj))
                    print_line(f'{max_spin_obj} = new QDoubleSpinBox({left_container_obj});')
                    print_line(f'{max_spin_obj}->setDecimals({decimal});')
                    print_line(f'{max_spin_obj}->setMaximum(9999);')
                    print_line(f'{g_layout_obj}->addWidget({max_spin_obj}, {row_count}, 2, 1, 1);')  # span column 2
                else:
                    raise ValueError(f'Unknown param type "{type_str}"')

            row_count += 1
            # Move to next param

        # Add vertical spacer
        v_spacer_obj = f'{group.name}VSpacer'
        variables.append(("QSpacerItem*", v_spacer_obj))
        print_line(f'{v_spacer_obj} = new QSpacerItem(229, 89, QSizePolicy::Minimum, QSizePolicy::Expanding);')
        print_line(f'{g_layout_obj}->addItem({v_spacer_obj}, {row_count}, 0, 1, 3);')  # span column 0 to 2
        row_count += 1

        # Add info label if required
        if group.info_label is not None:
            info_obj = f'{group.info_label}Label'
            variables.append(("QLabel*", info_obj))
            print_line(f'{info_obj} = new QLabel({left_container_obj});')
            print_line(f'{info_obj}->setText(QString::fromUtf8("{group.info_label}"));')
            print_line(f'{g_layout_obj}->addWidget({info_obj}, {row_count}, 0, 1, 3);')  # span column 0 to 2
            row_count += 1

        # Finish the left part
        # Add the horizontal spacer of the group
        h_spacer_obj = f'{group.name}HSpacer'
        variables.append(("QSpacerItem*", h_spacer_obj))
        print_line(f'{h_spacer_obj} = new QSpacerItem(446, 20, QSizePolicy::Expanding, QSizePolicy::Minimum);')
        print_line(f'{h_layout_obj}->addItem({h_spacer_obj});')

        # Add the image label if required
        if group.image is not None:
            image_obj = f'{group.image}Label'
            variables.append(("QLabel*", image_obj))
            print_line(f'{image_obj} = new QLabel({group_obj});')
            print_line(f'{image_obj}->setMinimumSize(QSize(0, 360));')
            print_line(f'{image_obj}->setMaximumSize(QSize(16777215, 360));')
            print_line(f'{image_obj}->setAlignment(Qt::AlignCenter);')
            reset_images_lines.append(f'{image_obj}->setText(QString::fromUtf8("{group.image}"));')
            print_line(f'{h_layout_obj}->addWidget({image_obj});')

        print_line(f'areaLayout->addWidget({group_obj});')
        print_line()
        # Move to next group

    print_line("resetImageLabels();")
    print_line_prefix = "    "
    print_line("}")
    print_line()

    print_line("void resetImageLabels() {")
    print_line_prefix = "        "
    for line in reset_images_lines:
        print_line(line)
    print_line_prefix = "    "
    print_line("}")
    print_line()

    return variables


def generate_apply_results_code(groups: [Group]) -> [(str, str)]:
    global print_line_prefix

    variables = []

    print_line_prefix = "    "
    print_line("void applyResults(const package::Result &results) {")

    print_line_prefix = "        "
    for group in groups:

        print_line(f"// GROUP {group.name}")

        # Set the info label
        if group.info_label is not None:
            info_obj = f'{group.info_label}Label'
            print_line('if (results.has_%s()) {' % group.info_label)
            print_line_prefix = "            "
            print_line(f'{info_obj}->setText(QString::fromStdString(results.{group.info_label}()));')
            print_line_prefix = "        "
            print_line('}')

        # Set the image label
        if group.image is not None:
            image_obj = f'{group.image}Label'
            qimage_obj = f'{group.image}Image'
            variables.append(("QImage", qimage_obj))
            print_line('if (results.has_%s()) {' % group.image)
            print_line_prefix = "            "
            print_line('if (!results.%s().data().empty()) {' % group.image)
            print_line_prefix = "                "
            print_line(f'{qimage_obj} = QImage::fromData((const uint8_t *) results.{group.image}().data().c_str(), results.{group.image}().data().size()).copy();')
            print_line(f'{image_obj}->setPixmap(QPixmap::fromImage({qimage_obj}));')
            print_line_prefix = "            "
            print_line('} else {')
            print_line_prefix = "                "
            print_line(f'{image_obj}->setText("Empty");')
            print_line_prefix = "            "
            print_line('}')
            print_line_prefix = "        "
            print_line('}')

    print_line_prefix = "    "
    print_line("}")
    print_line()

    return variables


def generate_apply_params_code(groups: [Group]) -> None:
    global print_line_prefix

    print_line_prefix = "    "
    print_line("void applyParamSet(const package::ParamSet &p) {")

    print_line_prefix = "        "
    for group in groups:
        print_line(f"// GROUP {group.name}")

        for param in group.params:

            type_str = param.kind

            # Add checkbox or label
            if type_str.startswith("Toggled"):
                type_str = type_str[len("Toggled"):]  # consume the prefix

                # Checkbox
                label_obj = f'{param.name}Check'
                print_line(f'{label_obj}->setChecked(p.{param.name}().enabled());')

            else:
                # Label
                label_obj = f'{param.name}Label'

            if type_str.startswith("Enum"):  # Enum
                combo_obj = f'{param.name}Combo'
                print_line(f'{combo_obj}->setCurrentIndex(p.{param.name}());')

            else:  # not Enum, numerical types
                if type_str.startswith("Int"):
                    type_str = type_str[len("Int"):]  # consume the prefix
                elif type_str.startswith("Double"):
                    type_str = type_str[len("Double"):]  # consume the prefix
                else:
                    raise ValueError(f'Unknown data type prefix in "{type_str}"')

                # Add one or two spin boxes
                if len(type_str) == 0:
                    # No keyword "Range", single spin box
                    spin_obj = f'{param.name}Spin'
                    print_line(f'{spin_obj}->setValue(p.{param.name}(){".val()" if label_obj.endswith("Check") else ""});')
                elif type_str == "Range":
                    # Two spin boxes
                    min_spin_obj = f'{param.name}MinSpin'
                    print_line(f'{min_spin_obj}->setValue(p.{param.name}().min());')
                    max_spin_obj = f'{param.name}MaxSpin'
                    print_line(f'{max_spin_obj}->setValue(p.{param.name}().max());')
                else:
                    raise ValueError(f'Unknown param type "{type_str}"')

            # Move to next param

        # Move to next group

    print_line_prefix = "    "
    print_line("}")
    print_line()


def generate_get_params_code(groups: [Group]) -> None:
    global print_line_prefix

    print_line_prefix = "    "
    print_line("package::ParamSet getParamSet() const {")

    print_line_prefix = "        "
    print_line("package::ParamSet p;")
    for group in groups:
        print_line(f"// GROUP {group.name}")

        for param in group.params:

            type_str = param.kind

            if type_str in ["Int", "Double"]:
                spin_obj = f'{param.name}Spin'
                print_line(f'p.set_{param.name}({spin_obj}->value());')
            elif type_str.startswith("Enum"):
                combo_obj = f'{param.name}Combo'
                print_line(f'p.set_{param.name}((package::ParamSet::{type_str[4:]}){combo_obj}->currentIndex());')
            elif type_str in ["ToggledInt", "ToggledDouble"]:
                check_obj = f'{param.name}Check'
                spin_obj = f'{param.name}Spin'
                print_line(f'p.set_allocated_{param.name}(alloc{type_str}({check_obj}->isChecked(), {spin_obj}->value()));')
            elif type_str == "DoubleRange":
                min_spin_obj = f'{param.name}MinSpin'
                max_spin_obj = f'{param.name}MaxSpin'
                print_line(f'p.set_allocated_{param.name}(allocDoubleRange({min_spin_obj}->value(), {max_spin_obj}->value()));')
            elif type_str == "ToggledDoubleRange":
                check_obj = f'{param.name}Check'
                min_spin_obj = f'{param.name}MinSpin'
                max_spin_obj = f'{param.name}MaxSpin'
                print_line(f'p.set_allocated_{param.name}(allocToggledDoubleRange({check_obj}->isChecked(), {min_spin_obj}->value(), {max_spin_obj}->value()));')
            else:
                raise ValueError(f'Unknown param type "{type_str}"')

            # Move to next param

        # Move to next group

    print_line("return p;")
    print_line_prefix = "    "
    print_line("}")
    print_line()


def generate_member_variables(pointers: [(str, str)]) -> None:
    global print_line_prefix
    print_line_prefix = "    "
    for kind, field in pointers:
        print_line(f'{kind} {field};')


def generate_all(proto_file: str) -> None:
    groups = parse_groups(proto_file)

    print(HEAD)
    variables = generate_ui_creation_code(groups)
    variables += generate_apply_results_code(groups)
    generate_apply_params_code(groups)
    generate_get_params_code(groups)
    print()
    print("private:")
    print()
    generate_member_variables(variables)
    print(TAIL)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("proto", help="Input proto file")
    args = parser.parse_args()
    generate_all(args.proto)
