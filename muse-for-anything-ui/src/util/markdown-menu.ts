import { editorStateCtx, schemaCtx } from "@milkdown/core";
import { Ctx } from "@milkdown/ctx";
import { MarkType } from "@milkdown/prose/model";
import { EditorState } from "@milkdown/prose/state";
import { MenuConfigItem } from "@milkdown-lab/plugin-menu";


interface ToolbarIcon {
    label: string;
    svg: string;
}

/**
 * Inline SVG icons for the markdown toolbar buttons.
 *
 * Icons are taken from https://systemuicons.com, the same source the
 * `svg-icon` custom element uses, so the toolbar matches the rest of the UI.
 * They are inlined here (instead of using the icon font the menu plugin
 * defaults to) to avoid pulling an external font into a self-hosted
 * deployment.
 */
const TOOLBAR_ICONS: Record<string, ToolbarIcon> = {
    undo: {
        label: "undo",
        svg: '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" transform="translate(2 7)"><path d="m.5 6.5c3.33333333-4 6.33333333-6 9-6 2.6666667 0 5 1 7 3"/><path d="m.5 1.5v5h5"/></g></svg>',
    },
    redo: {
        label: "redo",
        svg: '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" transform="translate(2 7)"><path d="m16.5 6.5c-3.1700033-4-6.1700033-6-9-6-2.82999674 0-5.16333008 1-7 3"/><path d="m11.5 6.5h5v-5"/></g></svg>',
    },
    bold: {
        label: "bold",
        svg: '<span class="text-lg font-bold">B</span>',
    },
    italic: {
        label: "italic",
        svg: '<span class="text-lg italic">i</span>',
    },
    strikeThrough: {
        label: "strike through",
        svg: '<span class="text-lg" style="text-decoration: line-through">S</span>',
    },
    bulletList: {
        label: "bullet list",
        svg: '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd" transform="translate(4 5)"><g stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="m11.5 5.5h-7"/><path d="m11.5 9.5h-7"/><path d="m11.5 1.5h-7"/></g><path d="m1.49884033 2.5c.5 0 1-.5 1-1s-.5-1-1-1-.99884033.5-.99884033 1 .49884033 1 .99884033 1zm0 4c.5 0 1-.5 1-1s-.5-1-1-1-.99884033.5-.99884033 1 .49884033 1 .99884033 1zm0 4c.5 0 1-.5 1-1s-.5-1-1-1-.99884033.5-.99884033 1 .49884033 1 .99884033 1z" fill="currentColor"/></g></svg>',
    },
    orderedList: {
        label: "ordered list",
        svg: '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd" transform="translate(4 5)"><g stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="m11.5 5.5h-7"/><path d="m11.5 9.5h-7"/><path d="m11.5 1.5h-7"/></g><path d="m1.88 3v-2.172h-.037l-.68.459v-.617l.717-.488h.717v2.818z" fill="currentColor"/><path d="m.89941406 5.06835938c0-.57226563.45117188-.96289063 1.109375-.96289063.65234375 0 1.04101563.35351563 1.04101563.8359375 0 .33398437-.1484375.5546875-.59765625.9609375l-.5546875.50195313v.03710937h1.18554687v.55859375h-2.14257812v-.47851562l1.0078125-.91210938c.34765625-.31835938.40625-.43945312.40625-.60546875 0-.1953125-.13671875-.35742187-.3828125-.35742187-.26171875 0-.41601563.17773437-.41601563.421875zm.71289063 4.73046874v-.484375h.36132812c.23828125 0 .39257813-.13867187.39257813-.34179687 0-.19140625-.14648438-.33203125-.38867188-.33203125-.25390625 0-.40820312.13476562-.41992187.36328125h-.65234375c.00976562-.54101563.4375-.8984375 1.10742187-.8984375.66015625 0 1.02148438.34570313 1.01953125.765625 0 .33984375-.21875.56445313-.52734375.63671875v.03710938c.40625.05664062.640625.30859374.640625.67968752 0 .5039062-.48046875.8515625-1.15820312.8515625-.66992188 0-1.125-.3613281-1.15039063-.9160157h.68359375c.00976563.2167969.18554688.3515626.45703125.3515626.26171875 0 .43945313-.1425782.43945313-.3554688 0-.22265625-.16796875-.35742188-.44335938-.35742188z" fill="currentColor"/></g></svg>',
    },
    liftList: {
        label: "lift list",
        svg: '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" transform="translate(3 3)"><path d="m7.328 4.672v5.656h-5.656" transform="matrix(-.70710678 -.70710678 -.70710678 .70710678 12.985309 5.378691)"/><path d="m11.5 7.5h-11"/><path d="m14.5.5v14"/></g></svg>',
    },
    sinkList: {
        label: "sink list",
        svg: '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" transform="matrix(0 1 -1 0 17.5 3.5)"><path d="m11 4-4-4-4 4"/><path d="m7 0v11"/><path d="m0 14h14"/></g></svg>',
    },
    link: {
        label: "link",
        svg: '<svg xmlns="http://www.w3.org/2000/svg" width="21" height="21" viewBox="0 0 21 21"><g fill="none" fill-rule="evenodd" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M1.38757706,5.69087183 C0.839076291,5.14050909 0.5,4.38129902 0.5,3.54289344 C0.5,1.8623496 1.8623496,0.5 3.542893,0.5 L8.457107,0.5 C10.1376504,0.5 11.5,1.86235004 11.5,3.54289344 C11.5,5.22343727 10.1376504,6.5 8.457107,6.5 L6,6.5" transform="translate(3 6)"/><path d="M4.38757706,8.69087183 C3.83907629,8.14050909 3.5,7.38129902 3.5,6.54289344 C3.5,4.8623496 4.8623496,3.5 6.542893,3.5 L11.457107,3.5 C13.1376504,3.5 14.5,4.86235004 14.5,6.54289344 C14.5,8.22343727 13.1376504,9.5 11.457107,9.5 L9,9.5" transform="translate(3 6) rotate(-180 9 6.5)"/></g></svg>',
    },
    table: {
        label: "table",
        svg: '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" transform="translate(3 3)"><path d="m14.4978951 12.4978973-.0105089-9.99999996c-.0011648-1.10374784-.8962548-1.99789734-2-1.99789734h-9.99999995c-1.0543629 0-1.91816623.81587779-1.99451537 1.85073766l-.00548463.151365.0105133 10.00000004c.0011604 1.1037478.89625045 1.9978973 1.99999889 1.9978973h9.99999776c1.0543618 0 1.9181652-.8158778 1.9945143-1.8507377z"/><path d="m4.5 4.5v9.817"/><path d="m7-2v14" transform="matrix(0 1 -1 0 12.5 -2.5)"/></g></svg>',
    },
    quote: {
        label: "quote",
        svg: '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="m3.5 5.5h13.978"/><path d="m3.5 7.5h13.978"/><path d="m3.5 9.5h13.978"/><path d="m3.5 11.5h13.978"/><path d="m3.5 13.5h13.978"/><path d="m3.5 15.5h7"/></g></svg>',
    },
    code: {
        label: "code",
        svg: '<svg xmlns="http://www.w3.org/2000/svg" width="21" height="21" viewBox="0 0 21 21"><g fill="none" fill-rule="evenodd" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" transform="translate(2 3)"><line x1="10.5" x2="6.5" y1=".5" y2="14.5"/><polyline points="7.328 2.672 7.328 8.328 1.672 8.328" transform="rotate(135 4.5 5.5)"/><polyline points="15.328 6.672 15.328 12.328 9.672 12.328" transform="scale(1 -1) rotate(-45 -10.435 0)"/></g></svg>',
    },
};


/**
 * Render one toolbar icon as a DOM node the menu plugin can place in a button.
 *
 * The label is exposed as the accessible name of the button content.
 */
function icon(name: string): HTMLElement {
    const entry = TOOLBAR_ICONS[name];
    const span = document.createElement("span");
    span.classList.add("markdown-menu-icon");
    if (entry == null) {
        // an unmapped icon must not break the whole toolbar
        span.textContent = name;
        return span;
    }
    span.innerHTML = entry.svg;
    span.setAttribute("aria-label", entry.label);
    span.setAttribute("title", entry.label);
    return span;
}


/**
 * Return true if the current selection carries the given mark.
 *
 * An empty selection is tested against the marks stored for the next input,
 * a non-empty one against the whole selected range.
 */
function hasMark(state: EditorState, type: MarkType): boolean {
    if (type == null) {
        return false;
    }
    const { from, $from, to, empty } = state.selection;
    if (empty) {
        return Boolean(type.isInSet(state.storedMarks || $from.marks()));
    }
    return state.doc.rangeHasMark(from, to, type);
}


/** Return true if the mark named `markName` is active in the current selection. */
function markIsActive(ctx: Ctx, markName: string): boolean {
    const state = ctx.get(editorStateCtx);
    const schema = ctx.get(schemaCtx);
    return hasMark(state, schema.marks[markName]);
}


/** Return true if the schema has no mark named `markName`, so the button is unusable. */
function markIsMissing(ctx: Ctx, markName: string): boolean {
    return ctx.get(schemaCtx).marks[markName] == null;
}


/**
 * Toolbar layout for the markdown editor.
 *
 * Each inner array is one button group, rendered with a divider between
 * groups. Command keys are the ones exported by `@milkdown/preset-commonmark`
 * and `@milkdown/preset-gfm` in Milkdown 7.
 */
export const markdownMenuItems: MenuConfigItem[][] = [
    [
        {
            type: "select",
            text: "Heading",
            options: [
                { id: 1, content: "Large Heading" },
                { id: 2, content: "Medium Heading" },
                { id: 3, content: "Small Heading" },
                { id: 0, content: "Plain Text" },
            ],
            onSelect: (id) => {
                if (Number(id) === 0) {
                    return "TurnIntoText";
                }
                return ["WrapInHeading", Number(id)];
            },
        },
    ],
    [
        { type: "button", content: icon("undo"), key: "Undo" },
        { type: "button", content: icon("redo"), key: "Redo" },
    ],
    [
        {
            type: "button",
            content: icon("bold"),
            key: "ToggleStrong",
            active: (ctx) => markIsActive(ctx, "strong"),
            disabled: (ctx) => markIsMissing(ctx, "strong"),
        },
        {
            type: "button",
            content: icon("italic"),
            key: "ToggleEmphasis",
            active: (ctx) => markIsActive(ctx, "emphasis"),
            disabled: (ctx) => markIsMissing(ctx, "emphasis"),
        },
        {
            type: "button",
            content: icon("strikeThrough"),
            key: "ToggleStrikeThrough",
            active: (ctx) => markIsActive(ctx, "strike_through"),
            disabled: (ctx) => markIsMissing(ctx, "strike_through"),
        },
    ],
    [
        { type: "button", content: icon("bulletList"), key: "WrapInBulletList" },
        { type: "button", content: icon("orderedList"), key: "WrapInOrderedList" },
        { type: "button", content: icon("liftList"), key: "LiftListItem" },
        { type: "button", content: icon("sinkList"), key: "SinkListItem" },
    ],
    [
        {
            type: "button",
            content: icon("link"),
            key: "ToggleLink",
            active: (ctx) => markIsActive(ctx, "link"),
        },
        { type: "button", content: icon("table"), key: "InsertTable" },
        { type: "button", content: icon("quote"), key: "WrapInBlockquote" },
        { type: "button", content: icon("code"), key: "CreateCodeBlock" },
    ],
];
