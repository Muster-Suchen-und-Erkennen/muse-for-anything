import { css, injectGlobal } from "@emotion/css";
import { ThemeBorder, ThemeColor, themeFactory, ThemeFont, ThemeGlobal, ThemeIcon, ThemeScrollbar, ThemeShadow, ThemeSize } from "@milkdown/core";
import { injectProsemirrorView, useAllPresetRenderer } from "@milkdown/theme-pack-helper";


interface IconMapping {
    [prop: string]: {
        label: string,
        icon: string,
    }
}

const iconMapping: IconMapping = {
    help: {
        label: "help",
        icon: '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><circle cx="10.5" cy="10.5" r="8"/><circle cx="10.5" cy="10.5" r="4"/><path d="m13.5 7.5 2.5-2.5"/><path d="m13.5 13.5 2.5 2.5"/><path d="m7.5 13.5-2.5 2.5"/><path d="m7.5 7.5-2.5-2.5"/></g></svg>',
    },
    diagram: {
        label: "diagram",
        icon: '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" transform="translate(2 2)"><path d="m5.5.5h6v5h-6z"/><path d="m10.5 11.5h6v5h-6z"/><path d="m.5 11.5h6v5h-6z"/><path d="m3.498 11.5v-3h10v3"/><path d="m8.5 8.5v-3"/></g></svg>',
    },
    h1: {
        label: "h1",
        icon: '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="m13.5 5.5-2 10"/><path d="m9.5 5.5-2 10"/><path d="m6.5 8.5h9"/><path d="m5.5 12.5h9"/></g></svg>',
    },
    h2: {
        label: "h2",
        icon: '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="m13.5 5.5-2 10"/><path d="m9.5 5.5-2 10"/><path d="m6.5 8.5h9"/><path d="m5.5 12.5h9"/></g></svg>',
    },
    h3: {
        label: "h3",
        icon: '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="m13.5 5.5-2 10"/><path d="m9.5 5.5-2 10"/><path d="m6.5 8.5h9"/><path d="m5.5 12.5h9"/></g></svg>',
    },
    loading: {
        label: "loading",
        icon: '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="m10.5 3.5v2"/><path d="m15.5 5.5-1.5 1.5"/><path d="m5.5 5.5 1.5 1.5"/><path d="m10.5 17.5v-2"/><path d="m15.5 15.5-1.5-1.5"/><path d="m5.5 15.5 1.5-1.5"/><path d="m3.5 10.5h2"/><path d="m15.5 10.5h2"/></g></svg>',
    },
    quote: {
        label: "quote",
        icon: '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="m3.5 5.5h13.978"/><path d="m3.5 7.5h13.978"/><path d="m3.5 9.5h13.978"/><path d="m3.5 11.5h13.978"/><path d="m3.5 13.5h13.978"/><path d="m3.5 15.5h7"/></g></svg>',
    },
    code: {
        label: "code",
        icon: '<svg xmlns="http://www.w3.org/2000/svg" width="21" height="21" viewBox="0 0 21 21"><g fill="none" fill-rule="evenodd" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" transform="translate(2 3)"><line x1="10.5" x2="6.5" y1=".5" y2="14.5"/><polyline points="7.328 2.672 7.328 8.328 1.672 8.328" transform="rotate(135 4.5 5.5)"/><polyline points="15.328 6.672 15.328 12.328 9.672 12.328" transform="scale(1 -1) rotate(-45 -10.435 0)"/></g></svg>',
    },
    table: {
        label: "table",
        icon: '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" transform="translate(3 3)"><path d="m14.4978951 12.4978973-.0105089-9.99999996c-.0011648-1.10374784-.8962548-1.99789734-2-1.99789734h-9.99999995c-1.0543629 0-1.91816623.81587779-1.99451537 1.85073766l-.00548463.151365.0105133 10.00000004c.0011604 1.1037478.89625045 1.9978973 1.99999889 1.9978973h9.99999776c1.0543618 0 1.9181652-.8158778 1.9945143-1.8507377z"/><path d="m4.5 4.5v9.817"/><path d="m7-2v14" transform="matrix(0 1 -1 0 12.5 -2.5)"/></g></svg>',
    },
    divider: {
        label: "divider",
        icon: '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="m3 10.5h15"></path></svg>',
    },
    image: {
        label: "image",
        icon: '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd" transform="translate(3 3)"><g stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="m2.5.5h10c1.1045695 0 2 .8954305 2 2v10c0 1.1045695-.8954305 2-2 2h-10c-1.1045695 0-2-.8954305-2-2v-10c0-1.1045695.8954305-2 2-2z"/><path d="m14.5 10.5-3-3-3 2.985"/><path d="m12.5 14.5-9-9-3 3"/></g><circle cx="11" cy="4" fill="currentColor" r="1"/></g></svg>',
    },
    brokenImage: {
        label: "broken image",
        icon: '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd" transform="translate(3 3)"><g stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="m2.5.5h10c1.1045695 0 2 .8954305 2 2v10c0 1.1045695-.8954305 2-2 2h-10c-1.1045695 0-2-.8954305-2-2v-10c0-1.1045695.8954305-2 2-2z"/><path d="m14.5 10.5-3-3-3 2.985"/><path d="m12.5 14.5-9-9-3 3"/></g><circle cx="11" cy="4" fill="currentColor" r="1"/></g></svg>',
    },
    bulletList: {
        label: "bullet list",
        icon: '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd" transform="translate(4 5)"><g stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="m11.5 5.5h-7"/><path d="m11.5 9.5h-7"/><path d="m11.5 1.5h-7"/></g><path d="m1.49884033 2.5c.5 0 1-.5 1-1s-.5-1-1-1-.99884033.5-.99884033 1 .49884033 1 .99884033 1zm0 4c.5 0 1-.5 1-1s-.5-1-1-1-.99884033.5-.99884033 1 .49884033 1 .99884033 1zm0 4c.5 0 1-.5 1-1s-.5-1-1-1-.99884033.5-.99884033 1 .49884033 1 .99884033 1z" fill="currentColor"/></g></svg>',
    },
    orderedList: {
        label: "ordered list",
        icon: '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd" transform="translate(4 5)"><g stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="m11.5 5.5h-7"/><path d="m11.5 9.5h-7"/><path d="m11.5 1.5h-7"/></g><path d="m1.88 3v-2.172h-.037l-.68.459v-.617l.717-.488h.717v2.818z" fill="currentColor"/><path d="m.89941406 5.06835938c0-.57226563.45117188-.96289063 1.109375-.96289063.65234375 0 1.04101563.35351563 1.04101563.8359375 0 .33398437-.1484375.5546875-.59765625.9609375l-.5546875.50195313v.03710937h1.18554687v.55859375h-2.14257812v-.47851562l1.0078125-.91210938c.34765625-.31835938.40625-.43945312.40625-.60546875 0-.1953125-.13671875-.35742187-.3828125-.35742187-.26171875 0-.41601563.17773437-.41601563.421875zm.71289063 4.73046874v-.484375h.36132812c.23828125 0 .39257813-.13867187.39257813-.34179687 0-.19140625-.14648438-.33203125-.38867188-.33203125-.25390625 0-.40820312.13476562-.41992187.36328125h-.65234375c.00976562-.54101563.4375-.8984375 1.10742187-.8984375.66015625 0 1.02148438.34570313 1.01953125.765625 0 .33984375-.21875.56445313-.52734375.63671875v.03710938c.40625.05664062.640625.30859374.640625.67968752 0 .5039062-.48046875.8515625-1.15820312.8515625-.66992188 0-1.125-.3613281-1.15039063-.9160157h.68359375c.00976563.2167969.18554688.3515626.45703125.3515626.26171875 0 .43945313-.1425782.43945313-.3554688 0-.22265625-.16796875-.35742188-.44335938-.35742188z" fill="currentColor"/></g></svg>',
    },
    taskList: {
        label: "task list",
        icon: '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><path d="m2.5.5h10c1.1045695 0 2 .8954305 2 2v10c0 1.1045695-.8954305 2-2 2h-10c-1.1045695 0-2-.8954305-2-2v-10c0-1.1045695.8954305-2 2-2z" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" transform="translate(3 3)"/></svg>',
    },
    bold: {
        label: "bold",
        icon: '<span class="text-lg font-bold">B</span>',
    },
    italic: {
        label: "italic",
        icon: '<span class="text-lg italic">i</span>',
    },
    inlineCode: {
        label: "inline code",
        icon: '<svg xmlns="http://www.w3.org/2000/svg" width="21" height="21" viewBox="0 0 21 21"><g fill="none" fill-rule="evenodd" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" transform="translate(2 3)"><line x1="10.5" x2="6.5" y1=".5" y2="14.5"/><polyline points="7.328 2.672 7.328 8.328 1.672 8.328" transform="rotate(135 4.5 5.5)"/><polyline points="15.328 6.672 15.328 12.328 9.672 12.328" transform="scale(1 -1) rotate(-45 -10.435 0)"/></g></svg>',
    },
    strikeThrough: {
        label: "strike through",
        icon: '<span class="text-lg" style="text-decoration: line-through">S</span>',
    },
    link: {
        label: "link",
        icon: '<svg xmlns="http://www.w3.org/2000/svg" width="21" height="21" viewBox="0 0 21 21"><g fill="none" fill-rule="evenodd" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M1.38757706,5.69087183 C0.839076291,5.14050909 0.5,4.38129902 0.5,3.54289344 C0.5,1.8623496 1.8623496,0.5 3.542893,0.5 L8.457107,0.5 C10.1376504,0.5 11.5,1.86235004 11.5,3.54289344 C11.5,5.22343727 10.1376504,6.5 8.457107,6.5 L6,6.5" transform="translate(3 6)"/><path d="M4.38757706,8.69087183 C3.83907629,8.14050909 3.5,7.38129902 3.5,6.54289344 C3.5,4.8623496 4.8623496,3.5 6.542893,3.5 L11.457107,3.5 C13.1376504,3.5 14.5,4.86235004 14.5,6.54289344 C14.5,8.22343727 13.1376504,9.5 11.457107,9.5 L9,9.5" transform="translate(3 6) rotate(-180 9 6.5)"/></g></svg>',
    },
    leftArrow: {
        label: "left arrow",
        icon: '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><path d="m4.5 8.5-4-4 4-4" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" transform="translate(7 6)"/></svg>',
    },
    rightArrow: {
        label: "right arrow",
        icon: '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><path d="m.5 8.5 4-4-4-4" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" transform="translate(9 6)"/></svg>',
    },
    upArrow: {
        label: "up arrow",
        icon: '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><path d="m.5 4.5 4-4 4 4" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" transform="translate(6 8)"/></svg>',
    },
    downArrow: {
        label: "down arrow",
        icon: '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><path d="m8.5.5-4 4-4-4" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" transform="translate(6 8)"/></svg>',
    },
    alignLeft: {
        label: "align left",
        icon: '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="m4.5 6.5h12"/><path d="m4.498 10.5h5.997"/><path d="m4.5 14.5h9.995"/></g></svg>',
    },
    alignRight: {
        label: "align right",
        icon: '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="m4.5 6.5h12"/><path d="m10.498 10.5h5.997"/><path d="m6.5 14.5h9.995"/></g></svg>',
    },
    alignCenter: {
        label: "align center",
        icon: '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="m4.5 6.5h12"/><path d="m7.498 10.5h5.997"/><path d="m5.5 14.5h9.995"/></g></svg>',
    },
    delete: {
        label: "delete",
        icon: '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" transform="translate(3 2)"><path d="m2.5 2.5h10v12c0 1.1045695-.8954305 2-2 2h-6c-1.1045695 0-2-.8954305-2-2zm5-2c1.0543618 0 1.91816512.81587779 1.99451426 1.85073766l.00548574.14926234h-4c0-1.1045695.8954305-2 2-2z"/><path d="m.5 2.5h14"/><path d="m5.5 5.5v8"/><path d="m9.5 5.5v8"/></g></svg>',
    },
    select: {
        label: "select",
        icon: '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><path d="m5 4h1c.55228475 0 1 .44771525 1 1v1c0 .55228475-.44771525 1-1 1h-1c-.55228475 0-1-.44771525-1-1v-1c0-.55228475.44771525-1 1-1zm0-4h1c.55228475 0 1 .44771525 1 1v1c0 .55228475-.44771525 1-1 1h-1c-.55228475 0-1-.44771525-1-1v-1c0-.55228475.44771525-1 1-1zm4 4h1c.5522847 0 1 .44771525 1 1v1c0 .55228475-.4477153 1-1 1h-1c-.55228475 0-1-.44771525-1-1v-1c0-.55228475.44771525-1 1-1zm0-4h1c.5522847 0 1 .44771525 1 1v1c0 .55228475-.4477153 1-1 1h-1c-.55228475 0-1-.44771525-1-1v-1c0-.55228475.44771525-1 1-1zm0 8h1c.5522847 0 1 .44771525 1 1v1c0 .5522847-.4477153 1-1 1h-1c-.55228475 0-1-.4477153-1-1v-1c0-.55228475.44771525-1 1-1zm-4 0h1c.55228475 0 1 .44771525 1 1v1c0 .5522847-.44771525 1-1 1h-1c-.55228475 0-1-.4477153-1-1v-1c0-.55228475.44771525-1 1-1zm-4-4h1c.55228475 0 1 .44771525 1 1v1c0 .55228475-.44771525 1-1 1h-1c-.55228475 0-1-.44771525-1-1v-1c0-.55228475.44771525-1 1-1zm0-4h1c.55228475 0 1 .44771525 1 1v1c0 .55228475-.44771525 1-1 1h-1c-.55228475 0-1-.44771525-1-1v-1c0-.55228475.44771525-1 1-1zm0 8h1c.55228475 0 1 .44771525 1 1v1c0 .5522847-.44771525 1-1 1h-1c-.55228475 0-1-.4477153-1-1v-1c0-.55228475.44771525-1 1-1z" fill="currentColor" fill-rule="evenodd" transform="translate(5 5)"/></svg>',
    },
    unchecked: {
        label: "unchecked",
        icon: '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><path d="m2.5.5h10c1.1045695 0 2 .8954305 2 2v10c0 1.1045695-.8954305 2-2 2h-10c-1.1045695 0-2-.8954305-2-2v-10c0-1.1045695.8954305-2 2-2z" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" transform="translate(3 3)"/></svg>',
    },
    checked: {
        label: "checked",
        icon: '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" transform="translate(3 3)"><path d="m2.5.5h10c1.1045695 0 2 .8954305 2 2v10c0 1.1045695-.8954305 2-2 2h-10c-1.1045695 0-2-.8954305-2-2v-10c0-1.1045695.8954305-2 2-2z"/><path d="m4.5 7.5 2 2 4-4"/></g></svg>',
    },
    undo: {
        label: "undo",
        icon: '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" transform="translate(2 7)"><path d="m.5 6.5c3.33333333-4 6.33333333-6 9-6 2.6666667 0 5 1 7 3"/><path d="m.5 1.5v5h5"/></g></svg>',
    },
    redo: {
        label: "redo",
        icon: '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" transform="translate(2 7)"><path d="m16.5 6.5c-3.1700033-4-6.1700033-6-9-6-2.82999674 0-5.16333008 1-7 3"/><path d="m11.5 6.5h5v-5"/></g></svg>',
    },
    liftList: {
        label: "lift list",
        icon: '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" transform="translate(3 3)"><path d="m7.328 4.672v5.656h-5.656" transform="matrix(-.70710678 -.70710678 -.70710678 .70710678 12.985309 5.378691)"/><path d="m11.5 7.5h-11"/><path d="m14.5.5v14"/></g></svg>',
    },
    sinkList: {
        label: "sink list",
        icon: '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" transform="matrix(0 1 -1 0 17.5 3.5)"><path d="m11 4-4-4-4 4"/><path d="m7 0v11"/><path d="m0 14h14"/></g></svg>',
    },
};

const colorMap = {
    "primary": "--primary-color",
    "secondary": "--primary-color",
    "neutral": "--text-color",
    "solid": "--text-color",
    "shadow": "--background-color",
    "line": "--text-alt-color",
    "border": "--border-color",
    "surface": "--background-alt-color",
    "background": "--background-color",
};

export const MarkdownTheme = themeFactory((emotion, manager) => {
    const mainElement = document.querySelector("body main") ?? document.querySelector("body .main") ?? document.querySelector("body");
    const documentStyles = (mainElement as any)?.computedStyleMap();
    // eslint-disable-next-line complexity
    manager.set(ThemeColor, ([key, opacity]) => {
        const cssVar = colorMap[key] ?? "--text";
        let color: string = documentStyles.get(cssVar)
            .toString()
            .trim();
        if (color === "white") {
            color = "#ffffff";
        }
        if (color === "black") {
            color = "#000000";
        }
        if (color.startsWith("#")) {
            color = color.substring(1);
        }
        let rgb: number[] | null = null;
        let defaultOpacity = 1;
        if (color.startsWith("rgba")) {
            const values = color.substring(5, color.length - 1).split(/\s*,\s*/);
            defaultOpacity = parseFloat(values.pop() ?? "1");
            rgb = values.map((value => parseInt(value, 10)));
        } else if (color.startsWith("rgb")) {
            const values = color.substring(4, color.length - 1).split(/\s*,\s*/);
            rgb = values.map((value => parseInt(value, 10)));
        } else {
            const splitColor: string[] = [];
            if (color.length === 3) {
                splitColor.push(color.charAt(0) + color.charAt(0));
                splitColor.push(color.charAt(1) + color.charAt(1));
                splitColor.push(color.charAt(2) + color.charAt(2));
            }
            if (color.length === 6) {
                splitColor.push(color.substring(0, 2));
                splitColor.push(color.substring(2, 4));
                splitColor.push(color.substring(4, 6));
            }
            rgb = splitColor.map((value) => parseInt(value, 16));
        }
        if (!rgb || rgb.length !== 3) {
            return;
        }

        return `rgba(${rgb?.join(", ")}, ${(opacity || 1) * defaultOpacity})`;
    });
    manager.set(ThemeSize, (key) => {
        if (key === "radius") {
            return "0.125rem";
        }
        return "1px";
    });
    manager.set(ThemeIcon, (iconId) => {
        const target = iconMapping[iconId] ?? null;
        const div = document.createElement("div");
        div.classList.add("p-1");
        div.innerHTML = target.icon;

        return {
            dom: div,
            label: target?.label ?? iconId,
        };
    });

    manager.set(ThemeScrollbar, ([direction = "y", type = "normal"] = ["y", "normal"] as never) => {
        return css``;
    });

    manager.set(ThemeFont, (key) => {
        if (key === "typography") {
            return "var(--font)";
        }

        return "var(--font-mono)";
    });

    manager.set(ThemeShadow, (key) => {
        return ""; // TODO
    });

    manager.set(ThemeBorder, (direction) => {
        const width = manager.get(ThemeSize, "lineWidth");
        if (!direction) {
            return `border: ${width} solid var(--text-alt-color);`;
        }
        return `${`border-${direction}`}: ${width} solid var(--text-alt-color);`;
    });

    manager.set(ThemeGlobal, () => {
        const background = manager.get(ThemeColor, ["background", 0.5]);
        const secondary = manager.get(ThemeColor, ["secondary"]);
        const table = css`
            /* copy from https://github.com/ProseMirror/prosemirror-tables/blob/master/style/tables.css */
            .tableWrapper {
                overflow-x: auto;
                margin: 0;
                width: 100%;
                * {
                    margin: 0;
                    box-sizing: border-box;
                    font-size: 1em;
                }
            }
            table {
                border-collapse: collapse;
                table-layout: fixed;
                width: 100%;
                overflow: auto;
                border-radius: ${manager.get(ThemeSize, "radius")};
                p {
                    line-height: unset;
                }
            }
            tr {
                ${manager.get(ThemeBorder, "bottom")};
            }
            td,
            th {
                padding: 0 1em;
                vertical-align: top;
                box-sizing: border-box;
                position: relative;
                min-width: 100px;
                ${manager.get(ThemeBorder, undefined)};
                text-align: left;
                line-height: 3;
                height: 3em;
            }
            th {
                background-color: ${background};
                font-weight: 400;
            }
            .column-resize-handle {
                position: absolute;
                right: -2px;
                top: 0;
                bottom: 0;
                z-index: 20;
                pointer-events: none;
                background-color: ${secondary};
                width: ${manager.get(ThemeSize, "lineWidth")};
            }
            .resize-cursor {
                cursor: ew-resize;
                cursor: col-resize;
            }
            .selectedCell {
                &::after {
                    z-index: 2;
                    position: absolute;
                    content: '';
                    left: 0;
                    right: 0;
                    top: 0;
                    bottom: 0;
                    background-color: ${secondary};
                    opacity: 0.5;
                    pointer-events: none;
                }
                & ::selection {
                    color: unset;
                    background: transparent;
                }
            }
        `;

        injectProsemirrorView(emotion);

        injectGlobal`
            .milkdown {
                .material-icons-outlined {
                    font-size: 1.5em;
                }
                position: relative;
                margin-left: auto;
                margin-right: auto;
                box-sizing: border-box;
                ${manager.get(ThemeShadow, undefined)}
                ${manager.get(ThemeScrollbar, undefined)}
                .editor {
                    outline: none;
                    ${table};
                }
            }
        `;
    });

    useAllPresetRenderer(manager, emotion);
});

