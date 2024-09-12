// tailwind.config.js
module.exports = {
  content: [
    "./project/npda/templates/**/*.html",
    "./static/**/*.js",
    "./static/**/*.jsx",
    "./static/**/*.ts",
    "./static/**/*.tsx",
  ],
  theme: {
    extend: {},
  },
  plugins: [require("daisyui")],
  darkMode: "media",
  theme: {
    backgroundColor: (theme) => ({
      ...theme("colors"),
      rcpch_lightest_grey: "#f3f3f3",
    }),
    extend: {
      fontFamily: {
        montserrat: ["Montserrat", "regular"],
        arial: ["Arial", "sans-serif"],
      },
      maxWidth: {
        custom: "33.7rem", // Replace '30rem' with the exact width you want
      },
      colors: {
        rcpch_lightest_grey: "#f3f3f3",

        rcpch_dark_blue: "#0d0d58",
        rcpch_strong_blue: "#3366cc",
        /* 51,102,204 */
        rcpch_strong_blue_light_tint1: "#668cd9",
        rcpch_strong_blue_light_tint2: "#99b3e6",
        rcpch_strong_blue_light_tint3: "#ccd9f2",
        rcpch_strong_blue_dark_tint: "#405a97",

        /* 45,49,109 */
        rcpch_light_blue: "#11a7f2",
        rcpch_light_blue_tint1: "#4dbdf5",
        rcpch_light_blue_tint2: "#88d3f9",
        rcpch_light_blue_tint3: "#cfe9fc",
        rcpch_light_blue_dark_tint: "#0082bc",
        /* 17,167,242 */

        rcpch_pink: "#e00087",
        /* 224,0,135 */
        rcpch_pink_light_tint1: "#e840a5",
        rcpch_pink_light_tint2: "#ef80c3",
        rcpch_pink_light_tint3: "#f7bfe1",
        rcpch_pink_dark_tint: "#ab1368",

        /* monochrome */
        rcpch_white: "#ffffff",
        rcpch_light_grey: "#d9d9d9",
        /* 217,217,217 */
        rcpch_mid_grey: "#b3b3b3",
        /* 179,179,179 */
        rcpch_dark_grey: "#808080",
        /* 128,128,128 */
        rcpch_charcoal: "#4d4d4d",
        /* 77,77,77 */
        rcpch_charcoal_dark: "#191919",
        rcpch_black: "#000000",

        /* secondary colours */
        rcpch_red: "#e60700",
        rcpch_red_light_tint1: "#ec4540",
        rcpch_red_light_tint2: "#f38380",
        rcpch_red_light_tint3: "#f9c1bf",
        rcpch_red_dark_tint: "#b11d23",

        rcpch_orange: "#ff8000",
        rcpch_orange_light_tint1: "#ffa040",
        rcpch_orange_light_tint2: "#ffc080",
        rcpch_orange_light_tint3: "#ffdfbf",
        rcpch_orange_dark_tint: "#bf6914",

        rcpch_yellow: "#ffd200",
        rcpch_yellow_light_tint1: "#ffdd40",
        rcpch_yellow_light_tint2: "#ffe980",
        rcpch_yellow_light_tint3: "#fff4bf",
        rcpch_yellow_dark_tint: "#c5a000",

        rcpch_strong_green: "#66cc33",
        rcpch_strong_green_light_tint1: "#8cd966",
        rcpch_strong_green_light_tint2: "#b3e699",
        rcpch_strong_green_light_tint3: "#d9f2cc",
        rcpch_strong_green_dark_tint: "#53861b",

        rcpch_aqua_green: "#00bdaa",
        rcpch_aqua_green_light_tint1: "#40ecbf",
        rcpch_aqua_green_light_tint2: "#80ded4",
        rcpch_aqua_green_light_tint3: "#bfeeea",
        rcpch_aqua_green_dark_tint: "#2e888d",

        rcpch_purple: "#7159aa",
        rcpch_purple_light_tint1: "#ae4cbf",
        rcpch_purple_light_tint2: "#c987d4",
        rcpch_purple_light_tint3: "#e4c3ea",
        rcpch_purple_dark_tint: "#66296c",

        /* old colours */
        rcpch_gold: "#c2a712",
        rcpch_vivid_green: "#c8d400",
        rcpch_dark_red: "#9a0500",
      },
    },
  },
  variants: {
    extend: {
      backgroundColor: ["active"],
    },
  },
};
