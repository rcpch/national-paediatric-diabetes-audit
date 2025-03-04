from project.constants import colors


ETHNICITIES = (
    ("A", "White - British"),
    ("B", "White - Irish"),
    ("C", "White - Any other White background"),
    ("D", "Mixed - White and Black Caribbean"),
    ("E", "Mixed - White and Black African"),
    ("F", "Mixed - White and Asian"),
    ("G", "Mixed - Any other mixed background"),
    ("H", "Asian - Indian or British Indian"),
    ("J", "Asian - Pakistani or British Pakistani"),
    ("K", "Asian - Bangladeshi or British Bangladeshi"),
    ("L", "Asian - Any other Asian background"),
    ("M", "Black - Caribbean"),
    ("N", "Black - African"),
    ("P", "Black - Any other Black background"),
    ("R", "Chinese"),
    ("S", "Other - Any other ethnic group"),
    ("Z", "Not Stated"),
    ("99", "Not known"),
)

# Define top-level ethnicity categories and their colors (RCPCH defined)
ETHNICITY_PARENT_COLOR_MAP = {
    "White": colors.RCPCH_LIGHT_BLUE,
    "Asian": colors.RCPCH_PINK,
    "Black": colors.RCPCH_MID_GREY,
    "Mixed": colors.RCPCH_YELLOW,
    "Other": colors.RCPCH_DARK_BLUE,
}

# Define ethnicity mapping to parents
ETHNICITY_CHILD_PARENT_MAP = {
    "Not known": "Other",
    "Any other mixed background": "Mixed",
    "African": "Black",
    "Pakistani or British Pakistani": "Asian",
    "Caribbean": "Black",
    "British, Mixed British": "White",
    "Any other White background": "White",
    "Any other Black background": "Black",
    "Mixed (White and Black Caribbean)": "Mixed",
    "Irish": "White",
    "Any other ethnic group": "Other",
    "Chinese": "Asian",
    "Any other Asian background": "Asian",
    "Mixed (White and Asian)": "Mixed",
    "Indian or British Indian": "Asian",
    "Not Stated": "Other",
    "Mixed (White and Black African)": "Mixed",
    "Bangladeshi or British Bangladeshi": "Asian",
}
