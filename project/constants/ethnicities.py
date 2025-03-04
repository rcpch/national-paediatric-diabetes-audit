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
    "White": {
        "color": colors.RCPCH_LIGHT_BLUE,
        "categories": [
            "White - British",
            "White - Irish",
            "White - Any other White background",
        ],
    },
    "Mixed": {
        "color": colors.RCPCH_YELLOW,
        "categories": [
            "Mixed - White and Black Caribbean",
            "Mixed - White and Black African",
            "Mixed - White and Asian",
            "Mixed - Any other mixed background",
        ],
    },
    "Asian": {
        "color": colors.RCPCH_PINK,
        "categories": [
            "Asian - Indian or British Indian",
            "Asian - Pakistani or British Pakistani",
            "Asian - Bangladeshi or British Bangladeshi",
            "Asian - Any other Asian background",
            "Chinese",
        ],
    },
    "Black": {
        "color": colors.RCPCH_MID_GREY,
        "categories": [
            "Black - Caribbean",
            "Black - African",
            "Black - Any other Black background",
        ],
    },
    "Other": {
        "color": colors.RCPCH_DARK_BLUE,
        "categories": ["Other - Any other ethnic group", "Not Stated", "Not known"],
    },
}
