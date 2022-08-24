import { defaultValueCtx, Editor, editorViewOptionsCtx, rootCtx } from "@milkdown/core";
import { clipboard } from "@milkdown/plugin-clipboard";
import { cursor } from "@milkdown/plugin-cursor";
import { emoji } from "@milkdown/plugin-emoji";
import { history } from "@milkdown/plugin-history";
import { indent } from "@milkdown/plugin-indent";
import { listener, listenerCtx } from "@milkdown/plugin-listener";
import { math } from "@milkdown/plugin-math";
import { menu, menuPlugin } from "@milkdown/plugin-menu";
import { prism } from "@milkdown/plugin-prism";
import { tooltip } from "@milkdown/plugin-tooltip";
import { gfm } from "@milkdown/preset-gfm";
import { setBlockType, wrapIn } from "@milkdown/prose/commands";
import { redo, undo } from "@milkdown/prose/history";
import { MarkType } from "@milkdown/prose/model";
import { liftListItem, sinkListItem } from "@milkdown/prose/schema-list";
import { EditorState, TextSelection } from "@milkdown/prose/state";
import { replaceAll } from "@milkdown/utils";
import { autoinject, bindable, bindingMode, child, TaskQueue } from "aurelia-framework";
import { MarkdownTheme } from "util/markdown-theme";


// function copied from @milkdown/plugin-menu
const hasMark = (state: EditorState, type: MarkType): boolean => {
    if (!type) {
        return false;
    }
    const { from, $from, to, empty } = state.selection;
    if (empty) {
        return Boolean(type.isInSet(state.storedMarks || $from.marks()));
    }
    return state.doc.rangeHasMark(from, to, type);
};

@autoinject()
export class Markdown {
    @bindable editable: boolean = false;
    @bindable({ defaultBindingMode: bindingMode.toView }) markdownIn: string | null;
    @bindable({ defaultBindingMode: bindingMode.fromView }) markdownOut: string;

    @child(".markdown-container") markdownElement: HTMLDivElement;

    private queue: TaskQueue;
    private editor: Editor | null = null;

    private editorSetupDeferred = false;

    constructor(queue: TaskQueue) {
        this.queue = queue;
    }

    markdownElementChanged(newElement: HTMLDivElement) {
        if (newElement == null) {
            return;
        }

        if (this.markdownIn || this.editable) {
            // setting up the markdown editor takes some time so it is handled in an async task
            this.queue.queueTask(() => this.setupEditor(newElement));
        } else {
            this.editorSetupDeferred = true;
        }
    }

    setupEditor(newElement: HTMLDivElement) {
        Editor.make()
            .config((ctx) => {
                ctx.set(rootCtx, newElement);
                ctx.set(editorViewOptionsCtx, { editable: () => this.editable ?? false });
                ctx.set(defaultValueCtx, this.markdownIn ?? "");
                ctx.get(listenerCtx).markdownUpdated((ctx, markdown) => {
                    if (this.editable) {
                        this.queue.queueMicroTask(() => this.markdownOut = markdown);
                    }
                });
            })
            .use(MarkdownTheme)
            .use(gfm)
            .use(listener)
            .use(prism)
            .use(math)
            .use(clipboard)
            .use(history)
            .use(cursor)
            .use(emoji)
            .use(indent)
            .use(tooltip)
            //.use(slash) // enable again when readonly view issues are solved
            .use(menu.configure(menuPlugin, {
                config: [
                    [
                        {
                            type: "select",
                            text: "Heading",
                            options: [
                                { id: "1", text: "Large Heading" },
                                { id: "2", text: "Medium Heading" },
                                { id: "3", text: "Small Heading" },
                                { id: "0", text: "Plain Text" },
                            ],
                            disabled: (view) => {
                                const { state } = view;
                                const setToHeading = (level: number) => setBlockType(state.schema.nodes.heading, { level })(state);
                                return (
                                    !(view.state.selection instanceof TextSelection) ||
                                    !(setToHeading(1) || setToHeading(2) || setToHeading(3))
                                );
                            },
                            onSelect: (id) => (Number(id) ? ["TurnIntoHeading", Number(id)] : ["TurnIntoText", null]),
                        },
                    ],
                    [
                        {
                            type: "button",
                            icon: "undo",
                            key: "Undo",
                            disabled: (view) => {
                                return !undo(view.state);
                            },
                        },
                        {
                            type: "button",
                            icon: "redo",
                            key: "Redo",
                            disabled: (view) => {
                                return !redo(view.state);
                            },
                        },
                    ],
                    [
                        {
                            type: "button",
                            icon: "bold",
                            key: "ToggleBold",
                            active: (view) => hasMark(view.state, view.state.schema.marks.strong),
                            disabled: (view) => !view.state.schema.marks.strong,
                        },
                        {
                            type: "button",
                            icon: "italic",
                            key: "ToggleItalic",
                            active: (view) => hasMark(view.state, view.state.schema.marks.em),
                            disabled: (view) => !view.state.schema.marks.em,
                        },
                        {
                            type: "button",
                            icon: "strikeThrough",
                            key: "ToggleStrikeThrough",
                            active: (view) => hasMark(view.state, view.state.schema.marks.strike_through),
                            disabled: (view) => !view.state.schema.marks.strike_through,
                        },
                    ],
                    [
                        {
                            type: "button",
                            icon: "bulletList",
                            key: "WrapInBulletList",
                            disabled: (view) => {
                                const { state } = view;
                                return !wrapIn(state.schema.nodes.bullet_list)(state);
                            },
                        },
                        {
                            type: "button",
                            icon: "orderedList",
                            key: "WrapInOrderedList",
                            disabled: (view) => {
                                const { state } = view;
                                return !wrapIn(state.schema.nodes.ordered_list)(state);
                            },
                        },
                        {
                            type: "button",
                            icon: "taskList",
                            key: "TurnIntoTaskList",
                            disabled: (view) => {
                                const { state } = view;
                                return !wrapIn(state.schema.nodes.task_list_item)(state);
                            },
                        },
                        {
                            type: "button",
                            icon: "liftList",
                            key: "LiftListItem",
                            disabled: (view) => {
                                const { state } = view;
                                return !liftListItem(state.schema.nodes.list_item)(state);
                            },
                        },
                        {
                            type: "button",
                            icon: "sinkList",
                            key: "SinkListItem",
                            disabled: (view) => {
                                const { state } = view;
                                return !sinkListItem(state.schema.nodes.list_item)(state);
                            },
                        },
                    ],
                    [
                        {
                            type: "button",
                            icon: "link",
                            key: "ToggleLink",
                            active: (view) => hasMark(view.state, view.state.schema.marks.link),
                        },
                        {
                            type: "button",
                            icon: "table",
                            key: "InsertTable",
                        },
                        {
                            type: "button",
                            icon: "quote",
                            key: "WrapInBlockquote",
                        },
                        {
                            type: "button",
                            icon: "code",
                            key: "TurnIntoCodeFence",
                        },
                    ],
                ],
            }))
            .create()
            .then(editor => this.editor = editor);
    }

    markdownInChanged(newMarkdown: string | null) {
        if (this.editorSetupDeferred) {
            this.editorSetupDeferred = false;
            this.queue.queueTask(() => {
                this.setupEditor(this.markdownElement);
                this.markdownInChanged(newMarkdown);
            });
        }
        this.queue.queueTask(() => {
            const markdown = newMarkdown ?? "";
            this.editor?.action(replaceAll(markdown, true));
        });
    }

    // TODO
    // editableChanged

}
